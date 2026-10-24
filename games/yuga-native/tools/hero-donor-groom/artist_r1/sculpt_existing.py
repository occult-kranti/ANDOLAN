"""One non-destructive lower-hair sculpt of the approved Rama geometry.

Reuses existing closed hair instead of cutting the rejected generated source.
The retained lattice has artist-chosen unequal left/right sweep controls.
No source faces, body positions, materials, images, rig or action are replaced.
"""
import argparse,hashlib,json,math,struct,sys,time
from pathlib import Path
import bpy
from mathutils import Vector

SOURCE_SHA='db4b2ec7a14cad72299d462c1265374f615d5e9d8b8852c4669e1f960f78245e'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def smooth(a,b,x):
 t=max(0.,min(1.,(x-a)/(b-a)));return t*t*(3-2*t)
def aim(o,p):o.rotation_euler=(Vector(p)-o.location).to_track_quat('-Z','Y').to_euler()
def light(name,at,power,size,target):
 d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;o=bpy.data.objects.new(name,d);bpy.context.scene.collection.objects.link(o);o.location=at;aim(o,target);return o
def positions(mesh,ids):return hashlib.sha256(b''.join(struct.pack('<3f',*mesh.vertices[i].co) for i in ids)).hexdigest()
def uv_digest(mesh):return hashlib.sha256(b''.join(struct.pack('<2f',*item.uv) for item in mesh.uv_layers.active.data)).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);assert sha(a.source)==SOURCE_SHA;a.output.mkdir(parents=True,exist_ok=False);start=time.monotonic();bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(a.source.resolve()));scene=bpy.context.scene
 for o in bpy.data.objects:
  if o.type=='ARMATURE':o.data.pose_position='REST'
 baseline=bpy.data.objects['RamaHero'];baseline.name='APPROVED BASELINE Rama';candidate=baseline.copy();candidate.data=baseline.data.copy();candidate.name='W3 posterior-hair sculpt CANDIDATE';scene.collection.objects.link(candidate);baseline.hide_render=True
 mesh=candidate.data;hair_materials={i for i,m in enumerate(mesh.materials) if m.name=='Swept black hair'};assert len(hair_materials)==1;hair_faces=[f.index for f in mesh.polygons if f.material_index in hair_materials];hair_vertices={v for f in mesh.polygons if f.material_index in hair_materials for v in f.vertices};nonhair_vertices={v for f in mesh.polygons if f.material_index not in hair_materials for v in f.vertices};assert hair_vertices.isdisjoint(nonhair_vertices)
 group=candidate.vertex_groups.new(name='W3 exact posterior hair selection');selected=[];weights={}
 for i in sorted(hair_vertices):
  co=mesh.vertices[i].co;weight=smooth(.018,.065,co.y)*(1-smooth(1.72,1.79,co.z))
  if weight>1e-7:group.add([i],weight,'REPLACE');selected.append(i);weights[i]=weight
 assert selected
 # Six directly selected sculpt stations. The left family turns out/in/out;
 # the right has a shorter raised ending and an opposing central turn.
 # These edit the existing surface via a retained cage, not new hair primitives.
 controls_left=[[-.008,0,.020],[-.032,.010,.008],[.018,.020,0],[-.024,.002,0],[0,0,0],[0,0,0]]
 controls_right=[[.025,.002,.055],[.038,.005,.030],[-.012,.012,.008],[.012,-.006,0],[0,0,0],[0,0,0]]
 lattice=bpy.data.lattices.new('W3 directly edited asymmetric lower-hair cage');lattice.points_u=4;lattice.points_v=3;lattice.points_w=6;lattice.interpolation_type_u='KEY_CARDINAL';lattice.interpolation_type_v='KEY_CARDINAL';lattice.interpolation_type_w='KEY_CARDINAL';cage=bpy.data.objects.new('EDITABLE lower-hair sculpt cage',lattice);scene.collection.objects.link(cage);cage.location=(0,.09,1.655);cage.scale=(.30,.24,.39);control_record=[]
 for k in range(6):
  for j in range(3):
   for i in range(4):
    point=lattice.points[(k*3+j)*4+i];x=i/3;mix=smooth(.2,.8,x);delta=Vector(controls_left[k]).lerp(Vector(controls_right[k]),mix);old=point.co_deform.copy();point.co_deform=old+Vector([delta[axis]/cage.scale[axis] for axis in range(3)]);control_record.append({'uvw':[i,j,k],'basis':list(old),'sculpt':list(point.co_deform),'world_delta':list(delta)})
 modifier=candidate.modifiers.new('W3 asymmetric posterior sculpt; crown and body protected','LATTICE');modifier.object=cage;modifier.vertex_group=group.name
 # Evaluate real lattice result in REST, with same source rig for both variants.
 deps=bpy.context.evaluated_depsgraph_get();bpy.context.view_layer.update();before=baseline.evaluated_get(deps).to_mesh();after=candidate.evaluated_get(deps).to_mesh();changed=[];protected_max=0.;selected_max=0.;selected_set=set(selected)
 assert len(before.vertices)==len(after.vertices)==len(mesh.vertices)
 for i,(v,w) in enumerate(zip(before.vertices,after.vertices)):
  distance=(v.co-w.co).length
  if i in selected_set:
   selected_max=max(selected_max,distance)
   if distance>1e-8:changed.append(i)
  else:protected_max=max(protected_max,distance)
 assert protected_max<1e-7 and selected_max>.01 and selected_max<.10
 baseline.evaluated_get(deps).to_mesh_clear();candidate.evaluated_get(deps).to_mesh_clear()
 protected=sorted(set(range(len(mesh.vertices)))-selected_set);assert positions(baseline.data,protected)==positions(mesh,protected);assert uv_digest(baseline.data)==uv_digest(mesh)
 # Fixed close-up studio. Clay override is identical for source and candidate.
 clay=bpy.data.materials.new('Neutral clay comparison ONLY');clay.use_nodes=True;bsdf=clay.node_tree.nodes.get('Principled BSDF');bsdf.inputs['Base Color'].default_value=(.38,.40,.43,1);bsdf.inputs['Roughness'].default_value=.62;scene.view_layers[0].material_override=clay
 scene.world=bpy.data.worlds.new('Fixed sculpt review world');scene.world.color=(.065,.065,.065);scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.055,.065,.085,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.32
 target=Vector((0,.035,1.67));light('Fixed large key',(-2,-3,3.4),520,2.5,target);light('Fixed fill',(2,-1,2.5),240,2.2,target);light('Fixed rear rim',(-1,2.5,3.0),520,2.0,target)
 camera_data=bpy.data.cameras.new('Fixed close source/candidate camera');camera=bpy.data.objects.new('Fixed close source/candidate camera',camera_data);scene.collection.objects.link(camera);scene.camera=camera;camera_data.type='ORTHO';camera_data.ortho_scale=.65;camera_data.lens=70
 scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=32;scene.cycles.use_denoising=False;scene.cycles.seed=0;scene.cycles.use_animated_seed=False;scene.render.threads_mode='FIXED';scene.render.threads=2;scene.render.resolution_x=640;scene.render.resolution_y=800;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.render.film_transparent=False
 candidate['source_sha256']=SOURCE_SHA;candidate['art_status']='UNREVIEWED four-view sculpt; not runtime';candidate['no_generated_source_cut']=True;cage['artist_controls']='Two unequal posterior flow families; six fixed sculpt stations, crown/body unselected';cage.hide_render=True
 scene_path=a.output/'approved-rama-hair-sculpt.blend';bpy.ops.wm.save_as_mainfile(filepath=str(scene_path.resolve()))
 frames=[]
 for view,offset in [('front',(1.2,-3,.3)),('profile',(3,0,.25)),('rear',(-1.2,3,.3)),('oblique',(-2.5,2.5,.2))]:
  camera.location=target+Vector(offset);aim(camera,target)
  for variant in ['baseline','candidate']:
   baseline.hide_render=variant!='baseline';candidate.hide_render=variant!='candidate';path=a.output/(view+'-'+variant+'.png');scene.render.filepath=str(path.resolve());begin=time.monotonic();bpy.ops.render.render(write_still=True);frames.append({'path':path.name,'view':view,'variant':variant,'camera_offset':offset,'sha256':sha(path),'bytes':path.stat().st_size,'seconds':time.monotonic()-begin})
 images=[{'name':i.name,'sha256':hashlib.sha256(bytes(i.packed_file.data)).hexdigest()} for i in bpy.data.images if i.packed_file]
 report={'schema_version':1,'scope':'Actual non-destructive lower-posterior sculpt of approved Rama source; no generated-source cut, retinted clone or runtime promotion.','source_path':str(a.source),'source_sha256':SOURCE_SHA,'script_sha256':sha(__file__),'blender':bpy.app.version_string,'source_vertices':len(mesh.vertices),'source_faces':len(mesh.polygons),'hair_faces':hair_faces,'selected_vertex_ids':selected,'selected_weights':weights,'protected_vertex_count':len(protected),'changed_evaluated_vertices':len(changed),'max_selected_displacement_metres':selected_max,'max_protected_displacement_metres':protected_max,'protected_basis_positions_exact':positions(baseline.data,protected)==positions(mesh,protected),'uv_exact':uv_digest(baseline.data)==uv_digest(mesh),'source_file_unchanged':sha(a.source)==SOURCE_SHA,'material_names':[m.name for m in mesh.materials],'image_hashes':images,'editable_cage':{'dimensions':[4,3,6],'location':list(cage.location),'scale':list(cage.scale),'controls':control_record,'left_stations_world_delta':controls_left,'right_stations_world_delta':controls_right},'scene':{'path':str(scene_path),'bytes':scene_path.stat().st_size,'sha256':sha(scene_path)},'render':{'renderer':'Cycles CPU','threads':2,'samples':32,'seed':0,'denoising':False,'resolution':[640,800],'target':list(target),'ortho_scale':.65,'clay_override_only':True},'frames':frames,'positive_completion':len(frames)==8,'runtime_promoted':False,'artistic_decision':'pending actual four-view comparison','elapsed_seconds':time.monotonic()-start}
 (a.output/'receipt.json').write_text(json.dumps(report,indent=2)+'\n');print('W3_HAIR_SCULPT='+json.dumps({k:v for k,v in report.items() if k not in ['hair_faces','selected_vertex_ids','selected_weights','editable_cage','image_hashes']},separators=(',',':')))
if __name__=='__main__':main()
