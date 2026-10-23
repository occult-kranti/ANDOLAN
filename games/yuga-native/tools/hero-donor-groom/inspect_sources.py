"""Read-only source-specific donor component and generated hair-region inventory."""
import argparse,array,hashlib,json,sys
from pathlib import Path
from collections import defaultdict
import bpy

SOURCE_SHA='0c9fe46baa0a2f6e5f9cdb9386aad1405f9f22470a729c2538142576981f5c0b'
DONOR_SHA='ef018941de8f8b53b3bf4808139601e15ae5c398c7fb23f26a221f1e1a0c6adc'
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def bounds(points):return {'min':[min(p[i] for p in points) for i in range(3)],'max':[max(p[i] for p in points) for i in range(3)]}
def main():
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--donor',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);assert sha(a.source)==SOURCE_SHA and sha(a.donor)==DONOR_SHA
 a.output.mkdir(exist_ok=False,parents=True);bpy.ops.wm.open_mainfile(filepath=str(a.donor.resolve()));obj=bpy.data.objects['Unified swept hair sculpture'];mesh=obj.data;adj=defaultdict(set)
 for e in mesh.edges:
  v,w=e.vertices;adj[v].add(w);adj[w].add(v)
 remaining=set(range(len(mesh.vertices)));components=[]
 while remaining:
  todo=[remaining.pop()];ids=[]
  while todo:
   v=todo.pop();ids.append(v)
   for w in adj[v]:
    if w in remaining:remaining.remove(w);todo.append(w)
  ids.sort();components.append(ids)
 components.sort(key=lambda x:(-len(x),x[0]));donor=[]
 for i,ids in enumerate(components):
  chosen=set(ids);faces=[p.index for p in mesh.polygons if p.vertices[0] in chosen];points=[mesh.vertices[j].co for j in ids]
  donor.append({'component':i,'vertices':len(ids),'faces':len(faces),'bounds':bounds(points),'vertex_ids_sha256':hashlib.sha256(json.dumps(ids).encode()).hexdigest(),'face_ids':faces})
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(a.source.resolve()));obj=next(o for o in bpy.data.objects if o.type=='MESH');mesh=obj.data;uv=mesh.uv_layers.active.data;bsdf=next(n for n in mesh.materials[0].node_tree.nodes if n.type=='BSDF_PRINCIPLED');im=bsdf.inputs['Base Color'].links[0].from_node.image;pix=array.array('f',[0.])*len(im.pixels);im.pixels.foreach_get(pix);w,h=im.size
 def sample(u,v):
  x=max(0,min(w-1,int(u*w)));y=max(0,min(h-1,int(v*h)));offset=(y*w+x)*4;return tuple(pix[offset:offset+3])
 candidates=[];bins=defaultdict(list)
 for face in mesh.polygons:
  co=face.center
  if -.13<co.x<.13 and co.y>.01 and .13<co.z<.45:
   colors=[sample(*uv[li].uv) for li in face.loop_indices];lums=[.2126*r+.7152*g+.0722*b for r,g,b in colors];nonblue=all(b<=r*1.6+.008 for r,g,b in colors);lowchroma=all(max(c)-min(c)<.13 for c in colors)
   row={'face':face.index,'centroid':list(co),'lum_min':min(lums),'lum_max':max(lums),'nonblue':nonblue,'lowchroma':lowchroma}
   candidates.append(row);bins[round(co.z/.025)*.025].append(row)
 summary=[]
 for z,rows in sorted(bins.items()):
  dark=[r for r in rows if r['lum_max']<.16 and r['nonblue'] and r['lowchroma']];summary.append({'z_bin':z,'faces_in_rear_envelope':len(rows),'allcorner_dark_nonblue_faces':len(dark),'dark_bounds':bounds([r['centroid'] for r in dark]) if dark else None})
 report={'schema_version':1,'source_sha256':SOURCE_SHA,'donor_sha256':DONOR_SHA,'script_sha256':sha(__file__),'blender':bpy.app.version_string,'donor_components':donor,'generated_rear_bins':summary,'source_unchanged':sha(a.source)==SOURCE_SHA,'donor_unchanged':sha(a.donor)==DONOR_SHA,'semantic_mask_validated':False}
 (a.output/'inventory.json').write_text(json.dumps(report,indent=2)+'\n');(a.output/'rear-face-colors.json').write_text(json.dumps(candidates)+'\n');print('DONOR_COMPONENTS='+json.dumps([{k:v for k,v in row.items() if k!='face_ids'} for row in donor],indent=2));print('GENERATED_BINS='+json.dumps(summary,indent=2))
if __name__=='__main__':main()
