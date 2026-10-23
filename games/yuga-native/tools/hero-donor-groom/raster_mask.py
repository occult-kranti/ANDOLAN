#!/usr/bin/env python3
"""Conservative complete UV triangle/texel overlap plus one-texel filter guard.

No discrete point sampling substitutes for triangle interiors: 2D SAT includes
every texel square touched by each UV triangle. All eight neighboring texels
are included conservatively for base-level bilinear filtering. Eligibility
remains a color diagnostic, never semantic truth or removal permission.
"""
import argparse,hashlib,io,json,math,struct,time
from collections import defaultdict
from pathlib import Path
import numpy as np
from PIL import Image

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def qualifies(rgb):
 r,g,b=rgb;return .2126*r+.7152*g+.0722*b<.16 and b<=r*1.6+.008 and max(rgb)-min(rgb)<.13
def components(rows,ids):
 chosen=set(ids);edges=defaultdict(list)
 for row in rows:
  if row['id'] not in chosen:continue
  p=[tuple(v) for v in row['xyz']]
  for a,b in [(0,1),(1,2),(2,0)]:edges[tuple(sorted((p[a],p[b])))].append(row['id'])
 adjacency=defaultdict(set)
 for faces in edges.values():
  for f in faces:adjacency[f].update(set(faces)-{f})
 remaining=set(chosen);groups=[];lookup={r['id']:r for r in rows}
 while remaining:
  todo=[remaining.pop()];group=[]
  while todo:
   f=todo.pop();group.append(f)
   for other in adjacency[f]:
    if other in remaining:remaining.remove(other);todo.append(other)
  points=[p for f in group for p in lookup[f]['xyz']]
  groups.append({'faces':len(group),'face_ids':sorted(group),'bounds_min':[min(p[i] for p in points) for i in range(3)],'bounds_max':[max(p[i] for p in points) for i in range(3)]})
 return sorted(groups,key=lambda row:-row['faces']),sum(len(faces)==1 for faces in edges.values())
def main():
 p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--proof',type=Path,required=True);p.add_argument('--coarse-adversary',type=Path,required=True);p.add_argument('--report',type=Path,required=True);a=p.parse_args();start=time.monotonic();assert sha(a.source)=='0c9fe46baa0a2f6e5f9cdb9386aad1405f9f22470a729c2538142576981f5c0b';raw=a.source.read_bytes();n,t=struct.unpack_from('<II',raw,12);d=json.loads(raw[20:20+n]);binary=20+n+8;texture=d['textures'][d['materials'][0]['pbrMetallicRoughness']['baseColorTexture']['index']];index=texture.get('source',texture.get('extensions',{}).get('EXT_texture_webp',{}).get('source'));v=d['bufferViews'][d['images'][index]['bufferView']];o=binary+v.get('byteOffset',0);image=np.asarray(Image.open(io.BytesIO(raw[o:o+v['byteLength']])).convert('RGB'))/255.;height,width,_=image.shape;rows=json.loads(a.proof.read_text());failed=[];safe=[];total_covered=0;total_guard=0;witnesses=[]
 for row in rows:
  tri=np.array(row['uv'],dtype=float)*np.array([width,height]);lo=np.floor(tri.min(axis=0)).astype(int)-1;hi=np.floor(tri.max(axis=0)).astype(int);assert int(np.prod(hi-lo+1))<1100000
  xx,yy=np.meshgrid(np.arange(lo[0],hi[0]+1),np.arange(lo[1],hi[1]+1));centers=np.column_stack([xx.ravel()+.5,yy.ravel()+.5]);keep=(centers[:,0]+.5>=tri[:,0].min()-1e-10)&(centers[:,0]-.5<=tri[:,0].max()+1e-10)&(centers[:,1]+.5>=tri[:,1].min()-1e-10)&(centers[:,1]-.5<=tri[:,1].max()+1e-10)
  signed=np.cross(tri[1]-tri[0],tri[2]-tri[0]);orientation=1 if signed>=0 else -1
  for i in range(3):
   edge=tri[(i+1)%3]-tri[i];relative=centers-tri[i];distance=orientation*(edge[0]*relative[:,1]-edge[1]*relative[:,0]);radius=.5*(abs(edge[0])+abs(edge[1]));keep &= distance>=-radius-1e-10
  # Explicit x/y interval projections above include exact boundary touches.
  cells=np.column_stack([xx.ravel()[keep],yy.ravel()[keep]]);assert len(cells)>0
  guarded=set((int(x+dx),int(y+dy)) for x,y in cells for dx in (-1,0,1) for dy in (-1,0,1));total_covered+=len(cells);total_guard+=len(guarded);bad=[]
  for x,y in guarded:
   rgb=tuple(float(q) for q in image[height-1-(y%height),x%width])
   if not qualifies(rgb):bad.append({'texel_xy_lower_left':[x%width,y%height],'rgb':rgb})
  if bad:
   failed.append(row['id'])
   if len(witnesses)<20:witnesses.append({'face_id':row['id'],'xyz':row['xyz'],'uv':row['uv'],'covered_texels':len(cells),'filter_guard_texels':len(guarded),'failing_texels':len(bad),'first_bad_texel':bad[0]})
  else:safe.append(row['id'])
 coarse=json.loads(a.coarse_adversary.read_text());assert set(coarse['failed_face_ids']).issubset(failed)
 groups,boundaries=components(rows,safe);report={'schema_version':1,'scope':'Full covered base-level UV texel overlap + one-texel bilinear guard eligibility only; no hair semantics/removal permission, no fitting.','source_sha256':sha(a.source),'proof_sha256':sha(a.proof),'script_sha256':sha(__file__),'image_size':[width,height],'method':'Convex triangle/square separating-axis intersection, every intersecting texel square retained including edge touches; 3x3 texel filter support, repeat-wrap; all covered/guard texels must satisfy original rule. No finite point-only replacement.','selected_faces':len(rows),'sum_covered_texel_tests':total_covered,'sum_filter_guard_texel_tests':total_guard,'unsafe_face_count':len(failed),'unsafe_face_ids':failed,'safe_face_count':len(safe),'diagnostic_safe_face_ids':safe,'safe_components':groups,'safe_component_count':len(groups),'safe_boundary_edges':boundaries,'largest_safe_component_faces':groups[0]['faces'] if groups else 0,'largest_safe_component_fraction':groups[0]['faces']/len(safe) if safe else 0,'all_coarse_failures_caught':True,'first_failure_witnesses':witnesses,'semantic_mask_validated':False,'source_omission_allowed':False,'elapsed_seconds':time.monotonic()-start}
 a.report.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['unsafe_face_ids','diagnostic_safe_face_ids','safe_components','first_failure_witnesses']},indent=2))
if __name__=='__main__':main()
