"""Conservative original-byte GLB patch of a texture/spatially masked hair region.

Reuses Blender's glTF import and mesh math. No topology, UV, image, material,
primitive or skin changes. Original GLB is immutable; this writes a candidate.
"""
import argparse,array,hashlib,json,math,struct,sys,time
from collections import defaultdict
from pathlib import Path
import bpy
from mathutils import Vector

SOURCE_SHA='0c9fe46baa0a2f6e5f9cdb9386aad1405f9f22470a729c2538142576981f5c0b'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def key(p):return tuple(round(float(c)*1e7) for c in p)
def smoothstep(lo,hi,x):
 t=max(0.,min(1.,(x-lo)/(hi-lo)));return t*t*(3-2*t)
def glb(raw):
 magic,version,size=struct.unpack_from('<III',raw);assert magic==0x46546c67 and version==2 and size==len(raw)
 off=12;doc=None;binary=None
 while off<len(raw):
  n,t=struct.unpack_from('<II',raw,off);off+=8
  if t==0x4e4f534a:doc=json.loads(raw[off:off+n])
  elif t==0x004e4942:binary=off
  off+=n
 assert doc is not None and binary is not None
 return doc,binary
def acc(doc,binary,index):
 a=doc['accessors'][index];v=doc['bufferViews'][a['bufferView']];assert a['componentType']==5126 and a['type']=='VEC3'
 return binary+v.get('byteOffset',0)+a.get('byteOffset',0),v.get('byteStride',12),a['count']
def main():
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);start=time.monotonic();assert sha(a.source)==SOURCE_SHA
 a.output.mkdir(parents=True,exist_ok=False);raw=a.source.read_bytes();doc,binary=glb(raw);primitive=doc['meshes'][0]['primitives'][0];assert len(doc['meshes'])==1 and len(doc['meshes'][0]['primitives'])==1
 po,ps,count=acc(doc,binary,primitive['attributes']['POSITION']);no,ns,ncount=acc(doc,binary,primitive['attributes']['NORMAL']);assert count==ncount
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(a.source.resolve()));obj=next(o for o in bpy.context.scene.objects if o.type=='MESH');mesh=obj.data;mesh.calc_loop_triangles();assert len(mesh.vertices)==count
 points={};members=defaultdict(list)
 for v in mesh.vertices:points.setdefault(key(v.co),v.co.copy());members[key(v.co)].append(v.index)
 neighbors=defaultdict(set)
 for edge in mesh.edges:
  x,y=(key(mesh.vertices[i].co) for i in edge.vertices)
  if x!=y:neighbors[x].add(y);neighbors[y].add(x)
 material=mesh.materials[0];bsdf=next(n for n in material.node_tree.nodes if n.type=='BSDF_PRINCIPLED');image=bsdf.inputs['Base Color'].links[0].from_node.image;pixels=array.array('f',[0.])*(len(image.pixels));image.pixels.foreach_get(pixels);w,h=image.size
 vertex_hair=defaultdict(list);uv=mesh.uv_layers.active.data
 for loop in mesh.loops:
  u,v=uv[loop.index].uv;ix=max(0,min(w-1,int(u*w)));iy=max(0,min(h-1,int(v*h)));i=(iy*w+ix)*4;r,g,b=pixels[i:i+3];lum=.2126*r+.7152*g+.0722*b
  hair=(1-smoothstep(.07,.16,lum)) if b<=r*1.6+.008 and max(r,g,b)-min(r,g,b)<.13 else 0.
  vertex_hair[key(mesh.vertices[loop.vertex_index].co)].append(hair)
 weights={}
 for k,co in points.items():
  x,y,z=co
  spatial=smoothstep(.25,.275,z)*(1-smoothstep(.39,.415,z))*smoothstep(.045,.065,y)*(1-smoothstep(.105,.13,y))*smoothstep(-.115,-.09,x)*(1-smoothstep(.07,.095,x))
  samples=vertex_hair[k]
  # Require every corner at a coincident position to classify as dark hair.
  texture=min(samples) if samples else 0.
  weight=spatial*texture
  if weight>1e-6:weights[k]=weight
 assert weights,'Empty mask'
 original={k:p.copy() for k,p in points.items()};current={k:p.copy() for k,p in points.items()}
 for iteration in range(3):
  for coefficient in (.28,-.29):
   updates={}
   for k,weight in weights.items():
    linked=neighbors[k]
    if len(linked)<3:continue
    average=sum((current[n] for n in linked),Vector())/len(linked);pnew=current[k]+coefficient*weight*(average-current[k]);delta=pnew-original[k]
    if delta.length>.0025:delta*=.0025/delta.length;pnew=original[k]+delta
    updates[k]=pnew
   current.update(updates)
 changed={k for k in weights if (current[k]-original[k]).length>1e-10}
 normals=defaultdict(Vector)
 for tri in mesh.loop_triangles:
  ks=[key(mesh.vertices[i].co) for i in tri.vertices];p0,p1,p2=(current[k] for k in ks);normal=(p1-p0).cross(p2-p0)
  for k in set(ks)&changed:normals[k]=normals[k]+normal
 output=bytearray(raw);allowed=[];mapped=0;deltas=[];norm_angles=[];changed_vertex_ids=[]
 for i in range(count):
  gx,gy,gz=struct.unpack_from('<3f',raw,po+i*ps);k=key((gx,-gz,gy));assert k in original,('Unmapped glTF vertex',i,k);mapped+=1
  if k not in changed:continue
  pnew=current[k];struct.pack_into('<3f',output,po+i*ps,pnew.x,pnew.z,-pnew.y);allowed.append([po+i*ps,12]);deltas.append((pnew-original[k]).length);changed_vertex_ids.append(i)
  nx,ny,nz=struct.unpack_from('<3f',raw,no+i*ns);oldnormal=Vector((nx,-nz,ny));newnormal=normals[k]
  if newnormal.length>1e-12:
   newnormal.normalize();blended=oldnormal.lerp(newnormal,.7).normalized();angle=oldnormal.angle(blended,0.);norm_angles.append(math.degrees(angle));struct.pack_into('<3f',output,no+i*ns,blended.x,blended.z,-blended.y);allowed.append([no+i*ns,12])
 covered=bytearray(len(raw))
 for off,n in allowed:covered[off:off+n]=b'\x01'*n
 changes=[i for i,(x,y) in enumerate(zip(raw,output)) if x!=y];assert all(covered[i] for i in changes)
 candidate=a.output/'rama-hair-micro-cleanup.glb';candidate.write_bytes(output)
 assert sha(a.source)==SOURCE_SHA
 # Diagnostic measures only: average neighbor residual in the selected region.
 def residual(coords):return sum((coords[k]-sum((coords[n] for n in neighbors[k]),Vector())/len(neighbors[k])).length for k in weights if neighbors[k])/len(weights)
 report={'schema_version':1,'scope':'Topology-preserving surgical candidate; not hair silhouette/rig/runtime acceptance.','source_sha256':SOURCE_SHA,'candidate_sha256':sha(candidate),'source_bytes':len(raw),'candidate_bytes':len(output),'script_sha256':sha(__file__),'blender':bpy.app.version_string,'algorithm':'Three Taubin pairs lambda0.28/mu-0.29 on exact-position groups, dark rear-hair texture/spatial mask, displacement cap0.0025sourceunits','mask_bounds':{'x':[-.115,.095],'y':[.045,.13],'z':[.25,.415]},'mask_texture':'Every coincident vertex corner: dark/low-chroma/nonblue albedo; smooth luminance ramp0.07..0.16','source_height':max(v.co.z for v in mesh.vertices)-min(v.co.z for v in mesh.vertices),'positions_mapped':mapped,'position_groups':len(points),'selected_position_groups':len(weights),'moved_position_groups':len(changed),'moved_original_vertices':len(changed_vertex_ids),'max_displacement':max(deltas),'mean_displacement':sum(deltas)/len(deltas),'normal_change_max_degrees':max(norm_angles),'neighbor_residual_before':residual(original),'neighbor_residual_after':residual(current),'byte_differences':len(changes),'allowed_byte_ranges':allowed,'changed_vertex_ids':changed_vertex_ids,'preservation':{'input_unchanged':sha(a.source)==SOURCE_SHA,'topology_and_indices_unchanged':True,'uv_accessor_bytes_unchanged':True,'embedded_images_exact_bytes_unchanged':True,'materials_and_nodes_json_exact_bytes_unchanged':True,'all_vertices_outside_mask_exact_positions_normals_unchanged':True},'runtime_promoted':False,'artistic_acceptance':'pending matched actual renders','elapsed_seconds':time.monotonic()-start}
 (a.output/'candidate.json').write_text(json.dumps(report,indent=2)+'\n');(a.output/'changed-vertices.json').write_text(json.dumps({'indices':changed_vertex_ids})+'\n');print('YUGA_CLEANUP_CANDIDATE='+json.dumps({k:v for k,v in report.items() if k not in {'allowed_byte_ranges','changed_vertex_ids'}},separators=(',',':')))
if __name__=='__main__':main()
