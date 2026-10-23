#!/usr/bin/env python3
"""Adversarial UV-interior samples against frozen source mask, no mesh edits."""
import argparse,hashlib,io,json,struct
from pathlib import Path
from PIL import Image

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def parse_glb(raw):
 n,t=struct.unpack_from('<II',raw,12);assert t==0x4e4f534a
 return json.loads(raw[20:20+n]),20+n+8
def qualifies(c):
 r,g,b=c;return .2126*r+.7152*g+.0722*b<.16 and b<=r*1.6+.008 and max(c)-min(c)<.13
def main():
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--proof',type=Path,required=True);p.add_argument('--report',type=Path,required=True);a=p.parse_args();assert sha(a.source)=='0c9fe46baa0a2f6e5f9cdb9386aad1405f9f22470a729c2538142576981f5c0b';raw=a.source.read_bytes();doc,binary=parse_glb(raw);material=doc['materials'][0];texture=doc['textures'][material['pbrMetallicRoughness']['baseColorTexture']['index']];image_index=texture.get('source',texture.get('extensions',{}).get('EXT_texture_webp',{}).get('source'));assert image_index is not None;view=doc['bufferViews'][doc['images'][image_index]['bufferView']];offset=binary+view.get('byteOffset',0);im=Image.open(io.BytesIO(raw[offset:offset+view['byteLength']])).convert('RGB');rows=json.loads(a.proof.read_text());failed=[];corners_match=True;sample_count=0
 def sample(uv):
  x=max(0,min(im.width-1,int(uv[0]*im.width)));y=max(0,min(im.height-1,int(uv[1]*im.height)));return tuple(c/255 for c in im.getpixel((x,im.height-1-y)))
 for row in rows:
  uv=row['uv'];colors=[sample(v) for v in uv];corners_match=corners_match and all(abs(q-r)<2e-7 for original,actual in zip(row['rgb'],colors) for q,r in zip(original,actual));bad=[]
  # Includes all edge midpoints and centroid, then a fixed barycentric grid.
  barycentrics=[(.5,.5,0),(.5,0,.5),(0,.5,.5),(1/3,1/3,1/3)]
  barycentrics.extend((i/8,j/8,1-(i+j)/8) for i in range(9) for j in range(9-i))
  for weights in barycentrics:
   point=[sum(weights[k]*uv[k][axis] for k in range(3)) for axis in range(2)];rgb=sample(point);sample_count+=1
   if not qualifies(rgb):bad.append({'barycentric':weights,'uv':point,'rgb':rgb})
  if bad:failed.append({'face_id':row['id'],'xyz':row['xyz'],'uv':uv,'corner_rgb':colors,'failed_samples':bad})
 report={'schema_version':1,'scope':'Adversarial sampling can disqualify a mask; passing samples cannot prove hair semantics. No deletion or fitted donor.','source_sha256':sha(a.source),'proof_sha256':sha(a.proof),'script_sha256':sha(__file__),'all_bpy_corner_values_match_decoded_image':corners_match,'selected_faces':len(rows),'samples':sample_count,'faces_failing_interior_or_edge_color_rule':len(failed),'failed_face_ids':[r['face_id'] for r in failed],'first_failure_witnesses':failed[:20],'all_selected_samples_eligible':corners_match and not failed,'semantic_mask_validated':False}
 a.report.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['first_failure_witnesses','failed_face_ids']},indent=2))
if __name__=='__main__':main()
