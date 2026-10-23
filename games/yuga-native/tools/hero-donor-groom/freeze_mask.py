"""Freeze a conservative face selection; classification awaits actual-view review."""
import argparse,array,hashlib,json,struct,sys
from pathlib import Path
import bpy

SHA='0c9fe46baa0a2f6e5f9cdb9386aad1405f9f22470a729c2538142576981f5c0b'
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def digest_faces(mesh,ids):
 h=hashlib.sha256()
 for i in ids:
  f=mesh.polygons[i];h.update(struct.pack('<4I',i,*f.vertices))
  for li in f.loop_indices:h.update(struct.pack('<2f',*mesh.uv_layers.active.data[li].uv))
 return h.hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args(sys.argv[sys.argv.index('--')+1:]);assert sha(a.source)==SHA;a.output.mkdir(parents=True,exist_ok=False)
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(a.source.resolve()));o=next(x for x in bpy.data.objects if x.type=='MESH');m=o.data;uv=m.uv_layers.active.data;bsdf=next(n for n in m.materials[0].node_tree.nodes if n.type=='BSDF_PRINCIPLED');im=bsdf.inputs['Base Color'].links[0].from_node.image;pixels=array.array('f',[0.])*len(im.pixels);im.pixels.foreach_get(pixels);w,h=im.size
 def rgb(u,v):
  i=(max(0,min(h-1,int(v*h)))*w+max(0,min(w-1,int(u*w))))*4;return tuple(pixels[i:i+3])
 def envelope(v):return -.115<v.x<.115 and .01<v.y<.115 and .18<v.z<.415
 def hair(c):
  r,g,b=c;return .2126*r+.7152*g+.0722*b<.16 and b<=r*1.6+.008 and max(c)-min(c)<.13
 selected=[];rows=[];mixed=[]
 for f in m.polygons:
  if not all(envelope(m.vertices[i].co) for i in f.vertices):continue
  colors=[rgb(*uv[li].uv) for li in f.loop_indices];flags=[hair(c) for c in colors]
  if all(flags):
   selected.append(f.index);rows.append({'id':f.index,'vertices':list(f.vertices),'xyz':[list(m.vertices[i].co) for i in f.vertices],'uv':[list(uv[li].uv) for li in f.loop_indices],'rgb':colors})
  elif any(flags):mixed.append(f.index)
 chosen=set(selected);protected=[i for i in range(len(m.polygons)) if i not in chosen]
 r={'schema_version':1,'source_sha256':SHA,'script_sha256':sha(__file__),'blender':bpy.app.version_string,'status':'UNVALIDATED conservative semantic-selection proposal; no removal allowed until actual-view review','selected_face_ids':selected,'protected_face_ids':protected,'mixed_corner_faces_explicitly_PROTECTED':mixed,'selected_count':len(selected),'protected_count':len(protected),'mixed_protected_count':len(mixed),'all_original_faces':len(m.polygons),'mask_source_space':{'x':[-.115,.115],'y':[.01,.115],'z':[.18,.415],'corner_rule':'Every vertex inside envelope; every original albedo UV corner luminance<.16, B<=R*1.6+.008, chroma<.13. Spatial context is rear nape; actual-view reviewer must confirm semantics.'},'selected_faces_uv_digest':digest_faces(m,selected),'protected_faces_uv_digest':digest_faces(m,protected),'positions_sha256':hashlib.sha256(b''.join(struct.pack('<3f',*v.co) for v in m.vertices)).hexdigest(),'images':[{'name':i.name,'sha256':hashlib.sha256(bytes(i.packed_file.data)).hexdigest()} for i in bpy.data.images if i.packed_file],'input_unchanged':sha(a.source)==SHA,'body_deleted':False,'runtime_promoted':False}
 (a.output/'mask.json').write_text(json.dumps(r,indent=2)+'\n');(a.output/'selected-face-corner-proof.json').write_text(json.dumps(rows,separators=(',',':'))+'\n');print(json.dumps({k:v for k,v in r.items() if k not in ['selected_face_ids','protected_face_ids','mixed_corner_faces_explicitly_PROTECTED']},indent=2))
if __name__=='__main__':main()
