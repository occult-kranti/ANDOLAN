"""Carry the approved-hair sculpt through a sparse original-byte GLB patch.

All nonpermitted binary ranges remain exact. JSON semantics may change only
at measured POSITION/NORMAL/TANGENT accessor bounds. Skin/UV/action data remain exact.
"""
import argparse,hashlib,json,math,struct,sys
from pathlib import Path
import bpy
import numpy as np

SOURCE_SHA='db4b2ec7a14cad72299d462c1265374f615d5e9d8b8852c4669e1f960f78245e'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def parse(raw):
 assert struct.unpack_from('<III',raw)==(0x46546c67,2,len(raw));offset=12;doc=None;binary=None
 while offset<len(raw):
  n,t=struct.unpack_from('<II',raw,offset);offset+=8
  if t==0x4e4f534a:doc=json.loads(raw[offset:offset+n])
  if t==0x004e4942:binary=offset
  offset+=n
 assert doc is not None and binary is not None;return doc,binary
def attribute(doc,binary,index):
 a=doc['accessors'][index];v=doc['bufferViews'][a['bufferView']];assert a['type']=='VEC3' and a['componentType']==5126
 return binary+v.get('byteOffset',0)+a.get('byteOffset',0),v.get('byteStride',12),a['count']
def main():
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--scene',type=Path,required=True);p.add_argument('--sculpt-report',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);r=json.loads(a.sculpt_report.read_text());assert sha(a.source)==SOURCE_SHA;assert sha(a.scene)==r['scene']['sha256'];a.output.mkdir(parents=True,exist_ok=False);raw=a.source.read_bytes();doc,binary=parse(raw);hair={i for i,m in enumerate(doc['materials']) if m.get('name')=='Swept black hair'};primitives=[p for mesh in doc['meshes'] for p in mesh['primitives'] if p.get('material') in hair];assert len(primitives)==1;primitive=primitives[0];po,ps,count=attribute(doc,binary,primitive['attributes']['POSITION']);no,ns,nn=attribute(doc,binary,primitive['attributes']['NORMAL']);assert count==nn
 bpy.ops.wm.open_mainfile(filepath=str(a.scene.resolve()));baseline=bpy.data.objects['APPROVED BASELINE Rama'];candidate=bpy.data.objects['W3 posterior-hair sculpt CANDIDATE'];mesh=baseline.data;hair_mats={i for i,m in enumerate(mesh.materials) if m.name=='Swept black hair'};hair_ids=sorted({v for p in mesh.polygons if p.material_index in hair_mats for v in p.vertices});assert len(hair_ids)==count
 deps=bpy.context.evaluated_depsgraph_get();bpy.context.view_layer.update();baseline_evaluated=baseline.evaluated_get(deps);before=baseline_evaluated.to_mesh();evaluated=candidate.evaluated_get(deps);after=evaluated.to_mesh(preserve_all_data_layers=True,depsgraph=deps);assert len(after.vertices)==len(mesh.vertices);after.calc_tangents(uvmap=after.uv_layers.active.name)
 # Source accessor order must be proven, never guessed from approximate nearest-neighbor positions.
 max_mapping=0.;converted=[];imported=[]
 for i,vertex_id in enumerate(hair_ids):
  gx,gy,gz=struct.unpack_from('<3f',raw,po+i*ps);co=mesh.vertices[vertex_id].co;distance=math.dist((gx,-gz,gy),co);max_mapping=max(max_mapping,distance);converted.append((gx,-gz,gy));imported.append(tuple(co))
 # Skin REST reconstruction has sub-micron float32 round-trip residuals.
 # Confirm every ordered position within a declared float32 budget, AND every
 # ordered UV below. No nearest-neighbor map or fitted affine is used. Carry
 # only DELTAS through the known axis rotation onto untouched raw basis values.
 coordinate_scale=max(1.,max(abs(v) for p in converted for v in p));roundtrip_budget=16*float(np.finfo(np.float32).eps)*coordinate_scale;assert max_mapping<roundtrip_budget;linear=np.eye(3);inverse=np.eye(3)
 uv_accessor=doc['accessors'][primitive['attributes']['TEXCOORD_0']];uv_view=doc['bufferViews'][uv_accessor['bufferView']];uo=binary+uv_view.get('byteOffset',0)+uv_accessor.get('byteOffset',0);us=uv_view.get('byteStride',8);assert uv_accessor['count']==count and uv_accessor['componentType']==5126;vertex_uv={};hair_id_set=set(hair_ids);selected_id_set=set(r['selected_vertex_ids'])
 for loop in mesh.loops:
  if loop.vertex_index in hair_id_set:vertex_uv.setdefault(loop.vertex_index,tuple(mesh.uv_layers.active.data[loop.index].uv))
 max_uv_residual=0.
 for i,vertex_id in enumerate(hair_ids):
  u,v=struct.unpack_from('<2f',raw,uo+i*us);max_uv_residual=max(max_uv_residual,math.dist((u,1-v),vertex_uv[vertex_id]))
 assert max_uv_residual<1e-7,('Hair accessor UV order differs',max_uv_residual)
 normals={};tangents={};ta=doc['accessors'][primitive['attributes']['TANGENT']];tv=doc['bufferViews'][ta['bufferView']];to=binary+tv.get('byteOffset',0)+ta.get('byteOffset',0);ts=tv.get('byteStride',16);assert ta['type']=='VEC4' and ta['componentType']==5126 and ta['count']==count
 for face in after.polygons:
  if face.material_index not in hair_mats:continue
  for li in face.loop_indices:
   vertex_id=after.loops[li].vertex_index;n=after.corner_normals[li].vector.copy()
   if vertex_id in normals:assert (normals[vertex_id]-n).length<2e-5
   else:normals[vertex_id]=n
   tangents.setdefault(vertex_id,(after.loops[li].tangent.copy(),after.loops[li].bitangent_sign))
 patch=bytearray(raw);allowed=bytearray(len(raw));delta=[];max_delta=0.
 for i,vertex_id in enumerate(hair_ids):
  old=before.vertices[vertex_id].co;new=after.vertices[vertex_id].co;distance=(old-new).length
  if distance<=1e-8:continue
  assert vertex_id in selected_id_set;assert .018<mesh.vertices[vertex_id].co.y and mesh.vertices[vertex_id].co.z<1.79;assert distance<.1;normal=normals[vertex_id].normalized();old_glb=struct.unpack_from('<3f',raw,po+i*ps);move=new-old;position=(old_glb[0]+move.x,old_glb[1]+move.z,old_glb[2]-move.y);normal_glb=(normal.x,normal.z,-normal.y);tangent,sign=tangents[vertex_id];tangent=(tangent-normal*tangent.dot(normal)).normalized();tangent_glb=(tangent.x,tangent.z,-tangent.y,-sign);assert all(math.isfinite(q) for q in (*position,*normal_glb,*tangent_glb));struct.pack_into('<3f',patch,po+i*ps,*position);struct.pack_into('<3f',patch,no+i*ns,*normal_glb);struct.pack_into('<4f',patch,to+i*ts,*tangent_glb)
  for off,size in [(po+i*ps,12),(no+i*ns,12),(to+i*ts,16)]:allowed[off:off+size]=b'\1'*size
  delta.append({'hair_accessor_vertex':i,'blender_vertex':vertex_id,'position':list(struct.unpack_from('<3f',patch,po+i*ps)),'normal':list(struct.unpack_from('<3f',patch,no+i*ns)),'tangent':list(struct.unpack_from('<4f',patch,to+i*ts))});max_delta=max(max_delta,distance)
 evaluated.to_mesh_clear();baseline_evaluated.to_mesh_clear();assert delta;differences=sum(x!=y for x,y in zip(raw,patch));assert all(allowed[i] for i,(x,y) in enumerate(zip(raw,patch)) if x!=y);assert parse(patch)[0]==doc
 position_index=primitive['attributes']['POSITION'];old_bounds={key:list(doc['accessors'][position_index][key]) for key in ['min','max']};updated_bounds={}
 for semantic,offset,stride,components in [('POSITION',po,ps,3),('NORMAL',no,ns,3),('TANGENT',to,ts,4)]:
  index=primitive['attributes'][semantic];accessor=doc['accessors'][index];points=[struct.unpack_from('<'+'f'*components,patch,offset+i*stride) for i in range(count)];prior={key:list(accessor[key]) for key in ['min','max'] if key in accessor};bounds={}
  for key,fn in [('min',min),('max',max)]:
   if key in accessor:accessor[key]=[fn(p[j] for p in points) for j in range(components)];bounds[key]=list(accessor[key])
  updated_bounds[semantic]={'accessor':index,'before':prior,'after':bounds}
 minimum=doc['accessors'][position_index]['min'];maximum=doc['accessors'][position_index]['max'];encoded=json.dumps(doc,separators=(',',':'),ensure_ascii=False).encode();encoded+=b' '*((-len(encoded))%4);payload=patch[binary:];container=struct.pack('<III',0x46546c67,2,28+len(encoded)+len(payload))+struct.pack('<II',len(encoded),0x4e4f534a)+encoded+struct.pack('<II',len(payload),0x004e4942)+payload;target=a.output/'rama-hair-sculpt-isolated.glb';target.write_bytes(container);assert parse(container)[0]==doc
 proof={'schema_version':1,'scope':'Hair-only POSITION/NORMAL/TANGENT delta plus measured bounds of every modified accessor; no native pose/LOD/final art acceptance.','source_sha256':SOURCE_SHA,'scene_sha256':sha(a.scene),'sculpt_report_sha256':sha(a.sculpt_report),'script_sha256':sha(__file__),'candidate':{'path':str(target),'bytes':len(container),'sha256':sha(target)},'source_bytes':len(raw),'hair_accessor_vertices':count,'changed_vertices':len(delta),'changed_binary_bytes':differences,'max_displacement_metres':max_delta,'max_import_order_position_residual':max_mapping,'float32_skin_rest_roundtrip_budget':roundtrip_budget,'max_ordered_uv_residual':max_uv_residual,'coordinate_method':'Every ordered source UV and position crosschecked; no nearest-neighbor/fitted map. Evaluated candidate-minus-evaluated baseline sculpt deltas rotate from Blender axes onto original raw basis values, retaining source float32 skin REST basis.','all_other_binary_bytes_exact':True,'position_accessor':position_index,'position_bounds_before':old_bounds,'position_bounds_after':{'min':minimum,'max':maximum},'json_semantics_unchanged_except_modified_accessor_bounds':True,'modified_accessor_bounds':updated_bounds,'tangent_handedness':'Negate Blender bitangent_sign because glTF UV V is 1 minus Blender UV V','raw_json_bytes_exact':False,'preserved':['triangle/index accessors','all UV/color-alpha arrays','all embedded image bytes','all material references/properties','JOINTS/WEIGHTS accessors','inverse bind matrices','skin joints/nodes','all animation metadata and sampler bytes','all nonhair POSITION/NORMAL/TANGENT bytes','all untouched hair POSITION/NORMAL/TANGENT bytes'],'delta':delta,'source_file_unchanged':sha(a.source)==SOURCE_SHA,'runtime_promoted':False,'artistic_scope':'W1 conditional go as bounded editable improvement; broad parallel panels remain.','native_reimport_pose_lod_and_textured_seam_checks':'pending; neighboring protected normals/tangents remain original','positive_completion':True}
 (a.output/'patch-proof.json').write_text(json.dumps(proof,indent=2)+'\n');print(json.dumps({k:v for k,v in proof.items() if k!='delta'},indent=2))
if __name__=='__main__':main()
