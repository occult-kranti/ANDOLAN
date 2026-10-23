"""Audit a copied glTF mesh in Blender; never mutate/export the input."""
import argparse,hashlib,json,math,sys,time
from collections import Counter,defaultdict
from pathlib import Path
import bpy,bmesh

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def components(bm):
 unseen=set(v.index for v in bm.verts);out=[]
 while unseen:
  seed=unseen.pop();stack=[seed];group=[seed]
  while stack:
   i=stack.pop()
   for e in bm.verts[i].link_edges:
    j=e.other_vert(bm.verts[i]).index
    if j in unseen:unseen.remove(j);stack.append(j);group.append(j)
  out.append(group)
 return sorted(out,key=len,reverse=True)
def stats(bm):
 bm.verts.ensure_lookup_table();bm.verts.index_update();bm.edges.index_update();bm.faces.index_update()
 cs=components(bm)
 return {'vertices':len(bm.verts),'edges':len(bm.edges),'faces':len(bm.faces),'components':len(cs),'component_vertices_largest':list(map(len,cs[:24])),'boundary_edges':sum(e.is_boundary for e in bm.edges),'wire_edges':sum(e.is_wire for e in bm.edges),'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),'degenerate_faces_1e_14':sum(f.calc_area()<1e-14 for f in bm.faces),'euler_characteristic':len(bm.verts)-len(bm.edges)+len(bm.faces),'finite_geometry':all(math.isfinite(c) for v in bm.verts for c in v.co)}
def exact_union(mesh):
 keys={};ids=[]
 for v in mesh.vertices:
  k=tuple(v.co);ids.append(keys.setdefault(k,len(keys)))
 edges=Counter();adj=defaultdict(set)
 for face in mesh.polygons:
  vs=[ids[i] for i in face.vertices]
  for i,a in enumerate(vs):
   b=vs[(i+1)%len(vs)];edges[tuple(sorted((a,b)))]+=1;adj[a].add(b);adj[b].add(a)
 unseen=set(keys.values());cs=[]
 while unseen:
  stack=[unseen.pop()];n=0
  while stack:
   k=stack.pop();n+=1
   for other in adj[k]:
    if other in unseen:unseen.remove(other);stack.append(other)
  cs.append(n)
 return {'method':'Exact float coordinate identity union; every original face retained; no weld/cleanup operation','unique_positions':len(keys),'faces':len(mesh.polygons),'undirected_edges':len(edges),'boundary_edges_incidence1':sum(n==1 for n in edges.values()),'nonmanifold_edges_incidence_gt2':sum(n>2 for n in edges.values()),'components':len(cs),'component_positions_largest':sorted(cs,reverse=True)[:24]}
def main():
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);start=time.monotonic()
 expected='0c9fe46baa0a2f6e5f9cdb9386aad1405f9f22470a729c2538142576981f5c0b'
 assert sha(a.source)==expected,'Unexpected input'
 a.output.mkdir(parents=True,exist_ok=False);bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(a.source.resolve()));obj=next(o for o in bpy.context.scene.objects if o.type=='MESH');mesh=obj.data
 bm=bmesh.new();bm.from_mesh(mesh);before=stats(bm);weld=bm.copy();bmesh.ops.remove_doubles(weld,verts=list(weld.verts),dist=1e-7);after=stats(weld)
 bins=defaultdict(list)
 for v in weld.verts:
  x,y,z=v.co
  if abs(x)<.16 and y>.025 and .15<z<.49:bins['rear_hair_envelope'].append(v.index)
  if abs(x)<.10 and y<0 and z>.30:bins['front_face_envelope'].append(v.index)
 subset={k:{'vertices':len(ids),'bounds_min':[min(weld.verts[i].co[j] for i in ids) for j in range(3)],'bounds_max':[max(weld.verts[i].co[j] for i in ids) for j in range(3)]} for k,ids in bins.items()}
 images=[{'name':im.name,'width':im.size[0],'height':im.size[1],'packed_bytes':len(im.packed_file.data) if im.packed_file else 0,'packed_sha256':hashlib.sha256(im.packed_file.data).hexdigest() if im.packed_file else None} for im in bpy.data.images]
 cs=components(weld)
 small=[]
 for c in cs[1:]:
  points=[weld.verts[i].co for i in c];small.append({'vertices':len(c),'min':[min(v[j] for v in points) for j in range(3)],'max':[max(v[j] for v in points) for j in range(3)]})
 report={'schema_version':1,'source':str(a.source),'source_sha256':expected,'script_sha256':sha(__file__),'blender':bpy.app.version_string,'scope':'Read-only source geometry and exact-position weld diagnostic; no derivative acceptance.','raw_import':before,'exact_coordinate_union':exact_union(mesh),'positional_weld_diagnostic':after,'diagnostic_warning':'Blender remove_doubles removes duplicate faces; resulting boundary counts do not describe source holes. See exact_coordinate_union for authoritative retained-face source connectivity.','weld_distance':1e-7,'small_components':small,'region_envelopes':subset,'uv_layers':len(mesh.uv_layers),'images':images,'elapsed_seconds':time.monotonic()-start,'input_unchanged':sha(a.source)==expected}
 (a.output/'audit.json').write_text(json.dumps(report,indent=2)+'\n');print('YUGA_SOURCE_AUDIT='+json.dumps(report,separators=(',',':')));bm.free();weld.free()
if __name__=='__main__':main()
