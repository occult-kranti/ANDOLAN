"""Reuse Rama's existing rig/actions through Blender nearest-face skin transfer.

This produces an isolated deformation candidate, not an accepted game hero.
The existing shoulder skinning trial establishes the closest-surface/four-weight
principle; Blender's Data Transfer modifier supplies polygon interpolation here.
No accepted asset or source image is modified.
"""
import argparse, hashlib, json, math, statistics, sys, time
from pathlib import Path
import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[4]
DONOR = ROOT/'games/yuga-native/assets/heroes/rama-hero.glb'
ORIGINAL = ROOT/'games/yuga-native/art/production-stage-oct23/hero-source/rama-generated.glb'
ORIGINAL_SHA = '0c9fe46baa0a2f6e5f9cdb9386aad1405f9f22470a729c2538142576981f5c0b'

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bounds(objects, evaluated=False):
 dg=bpy.context.evaluated_depsgraph_get();points=[]
 for o in objects:
  if evaluated:
   eo=o.evaluated_get(dg);me=eo.to_mesh();points.extend(eo.matrix_world@v.co for v in me.vertices);eo.to_mesh_clear()
  else:points.extend(o.matrix_world@v.co for v in o.data.vertices)
 return {'low':[min(v[i] for v in points) for i in range(3)],'high':[max(v[i] for v in points) for i in range(3)]}
def quant(values,p):
 s=sorted(values);return s[min(len(s)-1,int((len(s)-1)*p))]
def pose_positions(mesh):
 dg=bpy.context.evaluated_depsgraph_get();eo=mesh.evaluated_get(dg);me=eo.to_mesh()
 out=[eo.matrix_world@v.co for v in me.vertices];eo.to_mesh_clear();return out

def main():
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,default=ORIGINAL);p.add_argument('--output',type=Path,required=True);p.add_argument('--export',action='store_true');p.add_argument('--anatomy-gated',action='store_true')
 a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);a.source=a.source.resolve();a.output=a.output.resolve();a.output.mkdir(parents=True,exist_ok=False)
 if sha(ORIGINAL)!=ORIGINAL_SHA:raise RuntimeError('Canonical original input changed')
 script_hash=sha(__file__);started=time.monotonic();bpy.ops.wm.read_factory_settings(use_empty=True)
 bpy.ops.import_scene.gltf(filepath=str(DONOR));scene=bpy.context.scene
 rigs=[o for o in scene.objects if o.type=='ARMATURE'];assert len(rigs)==1;rig=rigs[0]
 donor_meshes=[o for o in scene.objects if o.type=='MESH' and o.name in {'RamaHero','RamaFace'}]
 assert len(donor_meshes)==2
 actions=list(bpy.data.actions)
 if rig.animation_data:
  rig.animation_data.action=None
  for track in rig.animation_data.nla_tracks:track.mute=True
 for bone in rig.pose.bones:bone.matrix_basis=Matrix.Identity(4)
 rig.data.pose_position='REST';scene.frame_set(0);bpy.context.view_layer.update()
 donor_bounds=bounds(donor_meshes)
 # Join a disposable donor geometry copy, preserving its real vertex-group names.
 copies=[]
 for o in donor_meshes:
  c=o.copy();c.data=o.data.copy();scene.collection.objects.link(c);c.name='Transfer donor '+o.name
  for mod in list(c.modifiers):c.modifiers.remove(mod)
  c.parent=None;c.matrix_world=o.matrix_world.copy();copies.append(c)
 bpy.ops.object.select_all(action='DESELECT')
 for c in copies:c.select_set(True)
 bpy.context.view_layer.objects.active=copies[0];bpy.ops.object.join();surface=bpy.context.object;surface.name='Existing Rama rest-weight surface'
 surface.data.calc_loop_triangles();verts=[surface.matrix_world@v.co for v in surface.data.vertices];tris=[tuple(t.vertices) for t in surface.data.loop_triangles]
 tree=BVHTree.FromPolygons(verts,tris,all_triangles=True)
 before=set(scene.objects);bpy.ops.import_scene.gltf(filepath=str(a.source));new=[o for o in scene.objects if o not in before];targets=[o for o in new if o.type=='MESH'];assert len(targets)==1
 target=targets[0];target.name='Rama generated skin-transfer candidate';source_bounds=bounds([target])
 source_h=source_bounds['high'][2]-source_bounds['low'][2];donor_h=donor_bounds['high'][2]-donor_bounds['low'][2]
 scale=donor_h/source_h
 sx=(source_bounds['high'][0]+source_bounds['low'][0])*.5
 sy=(source_bounds['high'][1]+source_bounds['low'][1])*.5
 mapping=Matrix.Translation(Vector((-sx*scale,-sy*scale,donor_bounds['low'][2]-source_bounds['low'][2]*scale)))@Matrix.Scale(scale,4)
 transform=mapping@target.matrix_world
 for v in target.data.vertices:v.co=transform@v.co
 target.parent=None;target.matrix_world=Matrix.Identity(4);target.data.update()
 original_positions=[v.co.copy() for v in target.data.vertices]
 distances=[]
 for v in target.data.vertices:
  nearest=tree.find_nearest(v.co)
  if nearest[0] is None:raise RuntimeError('No donor surface')
  distances.append(nearest[3])
 for group in surface.vertex_groups:target.vertex_groups.new(name=group.name)
 mod=target.modifiers.new('Existing nearest-face vertex weights','DATA_TRANSFER');mod.object=surface;mod.use_vert_data=True;mod.data_types_verts={'VGROUP_WEIGHTS'};mod.vert_mapping='POLYINTERP_NEAREST';mod.layers_vgroup_select_src='ALL';mod.layers_vgroup_select_dst='NAME';mod.mix_mode='REPLACE';mod.mix_factor=1.0
 bpy.ops.object.select_all(action='DESELECT');target.select_set(True);bpy.context.view_layer.objects.active=target;bpy.ops.object.modifier_apply(modifier=mod.name)
 # glTF uses bounded four-influence rows. Retain the strongest donor contributions.
 anatomy=None
 if a.anatomy_gated:
  sys.path.insert(0,str(Path(__file__).resolve().parent))
  import anatomy_gate
  anatomy=anatomy_gate.apply(target,surface,rig)
 dropped=[];unweighted=[];max_influences=0;norm_errors=[]
 for v in target.data.vertices:
  weights=sorted([(g.group,g.weight) for g in v.groups if g.weight>1e-8],key=lambda x:(-x[1],x[0]));keep=weights[:4];total=sum(x[1] for x in keep)
  if total<=0:unweighted.append(v.index);continue
  dropped.append(sum(x[1] for x in weights[4:]));max_influences=max(max_influences,len(keep))
  for group,_ in weights:target.vertex_groups[group].remove([v.index])
  for group,weight in keep:target.vertex_groups[group].add([v.index],weight/total,'REPLACE')
  norm_errors.append(abs(sum(g.weight for g in v.groups)-1))
 if unweighted:raise RuntimeError(f'{len(unweighted)} vertices lack donor weights')
 arm=target.modifiers.new('Reused Rama armature','ARMATURE');arm.object=rig;arm.use_vertex_groups=True
 # glTF expects the mesh under its armature; retain identity world transforms.
 target.parent=rig;target.matrix_parent_inverse=rig.matrix_world.inverted();target.matrix_world=Matrix.Identity(4)
 rig.data.pose_position='POSE';bpy.context.view_layer.update()
 # Keep original donor hidden and out of selected export. Source mesh remains intact.
 for o in list(scene.objects):
  if o not in {target,rig}:o.hide_render=True;o.hide_set(True)
 surface.hide_render=True;surface.hide_set(True)
 scene.render.fps=30
 samples=[]
 rest_positions=None
 for action_name,frames in [('REST',[0]),('idle',[0,24,48,72,96]),('fire',[0,8,12,20]),('run',[0,5,10,15,20]),('cast1',[0,12,24])]:
  if action_name=='REST':
   rig.animation_data.action=None
   for bone in rig.pose.bones:bone.matrix_basis=Matrix.Identity(4)
  else:
   action=next(x for x in actions if x.name.startswith(action_name+'_'))
   rig.animation_data.action=action
  for frame in frames:
   scene.frame_set(frame);bpy.context.view_layer.update();positions=pose_positions(target)
   assert all(math.isfinite(c) for v in positions for c in v)
   if rest_positions is None:rest_positions=positions
   movement=[(v-r).length for v,r in zip(positions,rest_positions)]
   # Record existing edges' relative stretches; large ratios expose bad transfer.
   ratios=[]
   for e in target.data.edges:
    ia,ib=e.vertices;old=(rest_positions[ia]-rest_positions[ib]).length
    if old>1e-7:ratios.append((positions[ia]-positions[ib]).length/old)
   samples.append({'action':action_name,'frame':frame,'finite':True,'bounds':bounds([target],True),'max_displacement_m':max(movement),'p95_displacement_m':quant(movement,.95),'edge_ratio':{'min':min(ratios),'p95':quant(ratios,.95),'p99':quant(ratios,.99),'max':max(ratios)}})
 rig.animation_data.action=next(x for x in actions if x.name.startswith('idle_'));scene.frame_set(0);bpy.context.view_layer.update()
 outblend=a.output/'skin-transfer.blend';bpy.ops.wm.save_as_mainfile(filepath=str(outblend),compress=True)
 export=None
 if a.export:
  bpy.ops.object.select_all(action='DESELECT');target.hide_set(False);rig.hide_set(False);target.select_set(True);rig.select_set(True);bpy.context.view_layer.objects.active=rig
  path=a.output/'rama-skin-transfer.glb'
  bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_range=False,export_skins=True,export_def_bones=False,export_all_influences=False)
  export={'path':str(path),'sha256':sha(path),'bytes':path.stat().st_size}
 report={'schema_version':1,'scope':'Isolated nearest-face/four-weight reuse candidate; actual deformation and contact review required; no runtime or quality acceptance.','inputs':{'donor':{'path':str(DONOR.relative_to(ROOT)),'sha256':sha(DONOR)},'generated':{'path':str(a.source),'sha256':sha(a.source)}},'method':{'reused_tool':'Blender Data Transfer POLYINTERP_NEAREST plus strongest-four normalization','related_existing_code':'art/hero-finish/s5-shoulder-armour/articulated-r5/skinning_trials.py','existing_code_sha256':sha(ROOT/'games/yuga-native/art/hero-finish/s5-shoulder-armour/articulated-r5/skinning_trials.py'),'coordinate_mapping':[list(row) for row in mapping],'uniform_scale':scale,'donor_rest_bounds':donor_bounds,'generated_input_bounds':source_bounds},'target':{'vertices':len(target.data.vertices),'bones':len(rig.data.bones),'action_names':[x.name for x in actions],'unweighted_vertices':len(unweighted),'max_influences':max_influences,'maximum_normalization_error':max(norm_errors),'maximum_dropped_weight':max(dropped),'nearest_donor_distance_m':{'median':quant(distances,.5),'p95':quant(distances,.95),'max':max(distances)},'geometry_exact_after_fit':all((v.co-original_positions[v.index]).length<1e-8 for v in target.data.vertices)},'samples':samples,'saved_scene':{'path':str(outblend),'bytes':outblend.stat().st_size,'sha256':sha(outblend)},'export':export,'elapsed_seconds':time.monotonic()-started,'runtime_promoted':False,'quality_accepted':False}
 report['script_sha256']=script_hash
 report['anatomy_gate']=anatomy
 (a.output/'transfer.json').write_text(json.dumps(report,indent=2)+'\n');print('RIG_TRANSFER_MECHANICS_PASS',json.dumps(report['target']),flush=True)
if __name__=='__main__':main()
