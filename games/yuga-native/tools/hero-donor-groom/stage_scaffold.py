"""Stage an unfitted rigless CC0 donor region and editable reduction seed.

No generated-source face is removed, no donor fitting is attempted, and no GLB
is exported. The reduced seed is not authored quad retopology or an art pass.
"""
import argparse,hashlib,json,struct,sys
from pathlib import Path
import bmesh,bpy
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from freeze_mask import digest_faces

SOURCE_SHA='0c9fe46baa0a2f6e5f9cdb9386aad1405f9f22470a729c2538142576981f5c0b'
DONOR_SHA='ef018941de8f8b53b3bf4808139601e15ae5c398c7fb23f26a221f1e1a0c6adc'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def positions(m):return hashlib.sha256(b''.join(struct.pack('<3f',*v.co) for v in m.vertices)).hexdigest()
def topology(m):
 bm=bmesh.new();bm.from_mesh(m);r={'vertices':len(bm.verts),'edges':len(bm.edges),'faces':len(bm.faces),'boundary_edges':sum(e.is_boundary for e in bm.edges),'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges)};bm.free();return r
def main():
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--donor',type=Path,required=True);p.add_argument('--inventory',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);assert sha(a.source)==SOURCE_SHA and sha(a.donor)==DONOR_SHA;a.output.mkdir(parents=True,exist_ok=False);inventory=json.loads(a.inventory.read_text());selection=inventory['donor_components'][1];assert selection['component']==1 and selection['vertices']==12762 and selection['faces']==25528
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(a.source.resolve()));source=next(o for o in bpy.data.objects if o.type=='MESH');source.name='GENERATED ORIGINAL reference DO NOT DELETE';source.hide_select=True;original_positions=positions(source.data);source['source_sha256']=SOURCE_SHA;source['omission_mask_status']='REJECTED; no faces removed';source['candidate']=False
 original_source_uv_digest=digest_faces(source.data,range(len(source.data.polygons)));original_ids=source.data.attributes.new('original_source_face_id','INT','FACE');original_ids.data.foreach_set('value',list(range(len(source.data.polygons))));labels=source.data.attributes.new('artist_semantic_label','INT','FACE');labels.data.foreach_set('value',[0]*len(source.data.polygons));source['semantic_label_legend']='0UNKNOWN 1HAIR 2CLOTH 3SKIN 4HARDWARE 5UNCERTAIN; all start UNKNOWN; no deletion permission'
 with bpy.data.libraries.load(str(a.donor.resolve()),link=False) as (available,data):
  assert 'Unified swept hair sculpture' in available.objects;data.objects=['Unified swept hair sculpture']
 donor=data.objects[0];mesh=donor.data;face_ids=selection['face_ids'];vertex_ids=sorted({i for f in face_ids for i in mesh.polygons[f].vertices});lookup={old:new for new,old in enumerate(vertex_ids)};assert len(vertex_ids)==12762;assert hashlib.sha256(json.dumps(vertex_ids).encode()).hexdigest()==selection['vertex_ids_sha256']
 selected_mesh=bpy.data.meshes.new('Exact pre-C1 rear-nape component1');selected_mesh.from_pydata([mesh.vertices[i].co.copy() for i in vertex_ids],[],[[lookup[i] for i in mesh.polygons[f].vertices] for f in face_ids]);selected_mesh.update();selected_mesh.materials.append(mesh.materials[0]);uv=selected_mesh.uv_layers.new(name='UVMap');normals=[]
 for old_face,new_face in zip(face_ids,selected_mesh.polygons):
  previous=mesh.polygons[old_face];new_face.use_smooth=True
  for old_li,new_li in zip(previous.loop_indices,new_face.loop_indices):uv.data[new_li].uv=mesh.uv_layers.active.data[old_li].uv;normals.append(mesh.corner_normals[old_li].vector.copy())
 selected_mesh.normals_split_custom_set(normals)
 fids=selected_mesh.attributes.new('original_donor_face_id','INT','FACE');fids.data.foreach_set('value',face_ids);vids=selected_mesh.attributes.new('original_donor_vertex_id','INT','POINT');vids.data.foreach_set('value',vertex_ids)
 high=bpy.data.objects.new('DONOR exact rear-nape UNFITTED reference',selected_mesh);bpy.context.scene.collection.objects.link(high);high['donor_sha256']=DONOR_SHA;high['source_object']='Unified swept hair sculpture';high['component']=1;high['fitted']=False;high['rigless']=True;high['license']='CC0-1.0 project-authored hair; art/hero-rama/NOTICE.md';high.hide_set(True);high.hide_render=True
 # Verify selected dense geometry and UVs preserve the source, before reduction.
 exact_positions=all(tuple(selected_mesh.vertices[j].co)==tuple(mesh.vertices[i].co) for j,i in enumerate(vertex_ids));exact_uv=all(tuple(selected_mesh.uv_layers.active.data[new_li].uv)==tuple(mesh.uv_layers.active.data[old_li].uv) for old_face,new_face in zip(face_ids,selected_mesh.polygons) for old_li,new_li in zip(mesh.polygons[old_face].loop_indices,new_face.loop_indices));print('EXACT_SOURCE_POSITIONS',exact_positions,'EXACT_SOURCE_UV',exact_uv);assert exact_positions and exact_uv
 cage=high.copy();cage.data=high.data.copy();cage.name='EDITABLE reduction SEED UNFITTED not quad-retopo';bpy.context.scene.collection.objects.link(cage);cage.hide_set(False);cage.hide_render=True
 for attribute in list(cage.data.attributes):
  if attribute.name.startswith('original_donor_'):cage.data.attributes.remove(attribute)
 bpy.ops.object.select_all(action='DESELECT');cage.select_set(True);bpy.context.view_layer.objects.active=cage;reduction=cage.modifiers.new('One bounded donor-only collapse seed','DECIMATE');reduction.ratio=.02;bpy.ops.object.modifier_apply(modifier=reduction.name);cage['derivation']='One donor-only DECIMATE ratio .02; not hand-authored quad cage or accepted new silhouette';cage['fitted']=False;cage['candidate']=False
 # Measured donor-only anchor suggestions: no target/source alignment invented.
 seeds={'left-root':(-.055,.105,1.79),'right-root':(.045,.105,1.77),'left-long-end':(-.06,.13,1.49),'right-short-end':(.06,.135,1.54),'left-mid-turn':(-.025,.15,1.65),'right-mid-turn':(.035,.15,1.69)};anchors=[]
 for name,seed in seeds.items():
  i=min(vertex_ids,key=lambda j:(mesh.vertices[j].co-Vector(seed)).length_squared);xyz=list(mesh.vertices[i].co);empty=bpy.data.objects.new('DONOR measured anchor '+name,None);empty.empty_display_type='PLAIN_AXES';empty.empty_display_size=.012;empty.location=xyz;bpy.context.scene.collection.objects.link(empty);anchors.append({'name':name,'donor_original_vertex_id':i,'xyz':xyz,'seed_query':seed,'role':'Measured donor-only suggestion, not generated-source attachment or accepted flow design'})
 images=[{'name':node.image.name,'packed_sha256':hashlib.sha256(bytes(node.image.packed_file.data)).hexdigest()} for node in mesh.materials[0].node_tree.nodes if node.type=='TEX_IMAGE' and node.image and node.image.packed_file]
 bpy.data.objects.remove(donor,do_unlink=True);bpy.data.orphans_purge(do_recursive=True);assert positions(source.data)==original_positions;assert len(source.data.polygons)==96660;assert digest_faces(source.data,range(len(source.data.polygons)))==original_source_uv_digest
 bpy.context.scene['status']='UNFITTED authoring intake; generated omission mask rejected';bpy.context.scene['no_runtime_candidate']=True;scene_path=a.output/'unfitted-donor-scaffold.blend';bpy.ops.wm.save_as_mainfile(filepath=str(scene_path.resolve()))
 report={'schema_version':1,'scope':'Actual editable rigless donor-only authoring scaffold; no source removal, no fitting, no replacement candidate, no render, no export.','source_sha256':SOURCE_SHA,'donor_sha256':DONOR_SHA,'inventory_sha256':sha(a.inventory),'script_sha256':sha(__file__),'source_original_faces_uv_digest':original_source_uv_digest,'source_original_positions_sha256':original_positions,'semantic_template':{'face_id_attribute':'original_source_face_id','label_attribute':'artist_semantic_label','legend':{'0':'UNKNOWN','1':'HAIR','2':'CLOTH','3':'SKIN','4':'HARDWARE','5':'UNCERTAIN'},'all_labels_initially_unknown':True},'source_original_vertices':len(source.data.vertices),'source_original_faces':len(source.data.polygons),'source_positions_unchanged':positions(source.data)==original_positions,'source_generated_file_unchanged':sha(a.source)==SOURCE_SHA,'donor_file_unchanged':sha(a.donor)==DONOR_SHA,'donor_original_object':'Unified swept hair sculpture','donor_component':1,'donor_original_face_ids':face_ids,'donor_original_vertex_ids':vertex_ids,'donor_source_positions_exact':exact_positions,'donor_source_uv_exact':exact_uv,'donor_positions_sha256':positions(selected_mesh),'donor_mesh_faces_uv_digest':digest_faces(selected_mesh,range(len(selected_mesh.polygons))),'donor_topology':topology(selected_mesh),'donor_images':images,'editable_seed_positions_sha256':positions(cage.data),'editable_seed_topology':topology(cage.data),'editable_seed_method':'Applied donor-only collapse ratio .02; no new gesture/cage control-point edits, no quad retopology claim.','rig_objects_in_scene':sum(o.type=='ARMATURE' for o in bpy.context.scene.objects),'measured_donor_anchor_suggestions':anchors,'target_landmarks':'NOT AUTHORED: semantic body/cape/neck boundary must be approved before fitting.','scene':{'path':str(scene_path),'bytes':scene_path.stat().st_size,'sha256':sha(scene_path)},'source_removal':False,'donor_fitted':False,'candidate_created':False,'runtime_promoted':False,'positive_completion':True}
 assert report['rig_objects_in_scene']==0
 (a.output/'scaffold.json').write_text(json.dumps(report,indent=2)+'\n');print('YUGA_DONOR_SCAFFOLD='+json.dumps({k:v for k,v in report.items() if k not in ['donor_original_face_ids','donor_original_vertex_ids']},separators=(',',':')))
if __name__=='__main__':main()
