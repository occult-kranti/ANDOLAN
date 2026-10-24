"""Isolated CC0 MPFB rear-guide fit. No canonical write, GLB export or skin acceptance."""
import argparse,hashlib,json,sys,gzip,math,time
from pathlib import Path
import bpy
from mathutils import Matrix,Vector
ROOT=Path('/workspace/ANDOLAN')
sys.path.insert(0,str(ROOT/'games/yuga-native/tools/hero-donor-groom/artist_r1'))
from sculpt_existing import sha,aim,positions,uv_digest

SOURCE_SHA='93aedaef061dc14618a0fcfad33c3df816fa755e8093381cbdfd0fd4c34527f5'
ANCESTOR_SHA='30b44c964664a5326dc89576748e63649fa10d5cfe30878ff3aa103e5cdd53f6'
CANONICAL_SHA='db4b2ec7a14cad72299d462c1265374f615d5e9d8b8852c4669e1f960f78245e'

def digest(rows):return hashlib.sha256(json.dumps(rows,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def raw_positions(data):return [tuple(v.vector) for v in data.attributes['position'].data]
def main():
 p=argparse.ArgumentParser();p.add_argument('--donor',type=Path,required=True);p.add_argument('--ancestor',type=Path,required=True);p.add_argument('--region-receipt',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);assert sha(a.donor)==SOURCE_SHA and sha(a.ancestor)==ANCESTOR_SHA;canonical=ROOT/'games/yuga-native/assets/heroes/rama-hero.glb';assert sha(canonical)==CANONICAL_SHA;a.output.mkdir(parents=True,exist_ok=False);start=time.monotonic();bpy.ops.wm.open_mainfile(filepath=str(a.ancestor));scene=bpy.context.scene;baseline=bpy.data.objects['APPROVED BASELINE Rama'];mesh=baseline.data;ids=list(range(len(mesh.vertices)));before_pos=positions(mesh,ids);before_uv=uv_digest(mesh)
 # This working scene alone drops old experimental objects; saved source stays exact.
 for name in ['W3 posterior-hair sculpt CANDIDATE','EDITABLE lower-hair sculpt cage']:
  old=bpy.data.objects.get(name)
  if old is not None:bpy.data.objects.remove(old,do_unlink=True)
 for obj in scene.objects:
  if obj.type=='ARMATURE':obj.data.pose_position='REST'
 candidate=baseline.copy();candidate.data=baseline.data.copy();candidate.name='MPFB nape preview Rama';scene.collection.objects.link(candidate);candidate.hide_render=False;baseline.hide_render=True
 region=json.loads(gzip.decompress(a.region_receipt.read_bytes()));clump_ids=set(v for c in region['clumps'] for v in c['source_vertex_ids']);hair_mats={i for i,m in enumerate(mesh.materials) if m.name=='Swept black hair'};masked_faces=[p.index for p in mesh.polygons if set(p.vertices)<=clump_ids];mixed=[p.index for p in mesh.polygons if set(p.vertices)&clump_ids and not set(p.vertices)<=clump_ids];assert masked_faces and not mixed;assert all(mesh.polygons[i].material_index in hair_mats for i in masked_faces)
 group=candidate.vertex_groups.new(name='AUTHORING ONLY old nine nape clumps');group.add(sorted(clump_ids),1.,'REPLACE');mask=candidate.modifiers.new('Preview mask only: original nape','MASK');mask.vertex_group=group.name;mask.invert_vertex_group=True;mask.threshold=.5
 with bpy.data.libraries.load(str(a.donor),link=False) as (available,loaded):loaded.objects=['Human','straight_hair_to_shoulder']
 human,donor=loaded.objects;assert human and donor
 for obj in loaded.objects:
  if obj.name not in scene.objects:scene.collection.objects.link(obj)
 donor.name='MPFB CC0 fitted rear guides';donor.data=donor.data.copy();human.name='HIDDEN source Human for MPFB curve surface';human.hide_render=True;human.hide_viewport=False;donor.hide_render=False
 points=raw_positions(donor.data);roots=[points[c.first_point_index] for c in donor.data.curves];keep=[i for i,r in enumerate(roots) if r[1]>=-.015 and r[2]>=1.51];assert len(keep)>=20
 selector=donor.data.attributes.new('YUGA_rear_guides','BOOLEAN','CURVE');keep_set=set(keep)
 for i,item in enumerate(selector.data):item.value=i in keep_set
 nodegroup=bpy.data.node_groups.new('AUTHORING rear guide selection','GeometryNodeTree');nodegroup.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry');nodegroup.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry');nodes=nodegroup.nodes;links=nodegroup.links;inp=nodes.new('NodeGroupInput');out=nodes.new('NodeGroupOutput');attr=nodes.new('GeometryNodeInputNamedAttribute');attr.data_type='BOOLEAN';attr.inputs['Name'].default_value=selector.name;invert=nodes.new('FunctionNodeBooleanMath');invert.operation='NOT';delete=nodes.new('GeometryNodeDeleteGeometry');delete.domain='CURVE';links.new(inp.outputs['Geometry'],delete.inputs['Geometry']);links.new(attr.outputs['Attribute'],invert.inputs[0]);links.new(invert.outputs[0],delete.inputs['Selection']);links.new(delete.outputs['Geometry'],out.inputs['Geometry']);select_mod=donor.modifiers.new('AUTHORING rear subset before interpolation','NODES');select_mod.node_group=nodegroup;bpy.context.view_layer.objects.active=donor
 while list(donor.modifiers).index(select_mod)>0:bpy.ops.object.modifier_move_up(modifier=select_mod.name)
 donor_lo=min(v.co.z for v in human.data.vertices);donor_hi=max(v.co.z for v in human.data.vertices);scale=1.85/(donor_hi-donor_lo);shift=(0.,.033,-donor_lo*scale);fit=bpy.data.objects.new('EDITABLE measured donor-to-Rama fit',None);scene.collection.objects.link(fit);fit.matrix_world=Matrix.Translation(Vector(shift))@Matrix.Diagonal((scale,scale,scale,1.));human.parent=fit;human.matrix_parent_inverse=Matrix.Identity(4)
 # Parent to the source surface as upstream intended; no source rig is imported.
 donor.parent=human;donor.matrix_parent_inverse=Matrix.Identity(4);donor.matrix_basis=Matrix.Identity(4)
 scene.view_layers[0].material_override=None;scene.view_settings.exposure=-.7
 for name,energy in [('Fixed large key',260),('Fixed fill',120),('Fixed rear rim',320)]:bpy.data.objects[name].data.energy=energy
 scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=32;scene.cycles.use_denoising=False;scene.render.threads_mode='FIXED';scene.render.threads=2;scene.render.resolution_x=640;scene.render.resolution_y=800;scene.render.resolution_percentage=100;scene.cycles.seed=0
 target=Vector((0,.035,1.67));cameras={}
 for view,offset in [('profile',(3,0,.25)),('rear',(-1.2,3,.3))]:
  data=scene.camera.data.copy();camera=bpy.data.objects.new('MPFB locked '+view,data);scene.collection.objects.link(camera);camera.location=target+Vector(offset);data.type='ORTHO';data.ortho_scale=.65;aim(camera,target);cameras[view]=camera
 scene.camera=cameras['rear'];assert positions(mesh,ids)==before_pos and positions(candidate.data,ids)==before_pos and uv_digest(mesh)==before_uv and uv_digest(candidate.data)==before_uv;assert raw_positions(donor.data)==points
 missing_images=[{'name':im.name,'filepath':im.filepath} for im in bpy.data.images if im.source=='FILE' and im.packed_file is None and not Path(bpy.path.abspath(im.filepath)).exists()];assert not missing_images,missing_images
 scene_path=a.output/'rama-mpfb-rear-guide-study.blend';bpy.ops.wm.save_as_mainfile(filepath=str(scene_path));report={'schema_version':1,'stage':'source-fitted-render-pending','scope':'Isolated static donor-curves preview; no GLB, skin/23-clip, LOD or canonical acceptance','source_sha256':CANONICAL_SHA,'donor_sha256':SOURCE_SHA,'donor_object':'straight_hair_to_shoulder','donor_author':'Tomáš Klecer','asset_license':'CC0-1.0','ancestor_sha256':ANCESTOR_SHA,'region_receipt_sha256':sha(a.region_receipt),'script_sha256':sha(__file__),'source_curve_count':len(roots),'selected_curve_ids':keep,'selected_curve_count':len(keep),'source_root_positions':roots,'guide_points_digest':digest(points),'source_guide_points_unchanged':True,'donor_human_height_m':donor_hi-donor_lo,'fit':{'uniform_scale':scale,'translation':shift,'method':'Uniform donor Human height to existing 1.85 m authored Rama anatomy; explicit +33 mm rear offset; editable non-destructive parent transform'},'masked_original_nape_vertices':len(clump_ids),'masked_original_nape_vertex_ids':sorted(clump_ids),'masked_original_faces':masked_faces,'masked_faces_all_named_hair':True,'mixed_protected_faces':mixed,'body_crown_source_mesh_positions_exact':True,'body_crown_uv_exact':True,'source_mesh_topology_unchanged_mask_not_applied':True,'canonical_source_unchanged':sha(canonical)==CANONICAL_SHA,'source_rig_and_actions_not_modified':True,'source_rig_bones':[{'name':b.name,'parent':b.parent.name if b.parent else None,'rest':[list(row) for row in b.matrix_local]} for obj in scene.objects if obj.type=='ARMATURE' for b in obj.data.bones],'source_blender_version':'4.4 header; read in Blender '+bpy.app.version_string,'scene':{'path':str(scene_path),'bytes':scene_path.stat().st_size,'sha256':sha(scene_path)},'render':{'threads':2,'samples':32,'resolution':[640,800],'exposure':-.7,'material_override':None,'views':['profile','rear'],'variants':['baseline','candidate']},'missing_external_images':missing_images,'frames':[],'canonical_promoted':False,'runtime_promoted':False,'elapsed_seconds':time.monotonic()-start};(a.output/'source-receipt.json').write_text(json.dumps(report,indent=2)+'\n');print('MPFB_FIT='+json.dumps({k:v for k,v in report.items() if k not in ['source_root_positions','masked_original_nape_vertex_ids','masked_original_faces','source_rig_bones']},separators=(',',':')))
if __name__=='__main__':main()
