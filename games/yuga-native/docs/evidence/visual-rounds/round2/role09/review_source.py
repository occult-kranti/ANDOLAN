#!/usr/bin/env python3
"""Independent material pins, exact one-variable overlays and form frame audit."""
from pathlib import Path
import argparse, hashlib, json, struct
import numpy as np
from PIL import Image

PROJECT=Path(__file__).resolve().parents[5]
PIN='0437ea91edf6989ff78c1eeadb3661f4825b60f2'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def glb(path):
 raw=Path(path).read_bytes(); assert struct.unpack_from('<4sII',raw)==(b'glTF',2,len(raw))
 n,kind=struct.unpack_from('<II',raw,12); assert kind==0x4e4f534a
 doc=json.loads(raw[20:20+n]); return raw,doc,28+n

def dense(raw,doc,start,index):
 a=doc['accessors'][index]; assert 'sparse' not in a and a['componentType']==5126
 v=doc['bufferViews'][a['bufferView']]; w={'VEC3':3,'VEC4':4}[a['type']]
 offset=start+v.get('byteOffset',0)+a.get('byteOffset',0); stride=v.get('byteStride',4*w)
 return np.ndarray((a['count'],w),dtype='<f4',buffer=raw,offset=offset,strides=(stride,4)),offset,stride

def main():
 p=argparse.ArgumentParser(); p.add_argument('--report',type=Path,required=True)
 p.add_argument('--candidate',type=Path,default=Path('/workspace/scratch/visual-round2/role-08/face-form-candidate-r4/candidate.glb'))
 args=p.parse_args(); checks=[]; images=[]
 def check(name,ok,**details): checks.append({'name':name,'passed':bool(ok),'details':details}); print(('PASS ' if ok else 'FAIL ')+name)
 profile=json.loads((PROJECT/'art/visual-rounds/skin/material-profile.json').read_text())
 pins=json.loads((PROJECT/'art/visual-rounds/skin/source-manifest.json').read_text())
 check('Skin source manifest identities match actual files',all(sha(PROJECT/path)==spec['sha256'] for path,spec in pins['runtime_inputs'].items()),count=len(pins['runtime_inputs']))
 for rel,spec in pins['runtime_inputs'].items():
  if 'mode' not in spec: continue
  with Image.open(PROJECT/rel) as im:
   ext=im.getextrema(); flat=list(ext) if im.mode=='L' else [list(x) for x in ext]
   check('Actual decoded '+rel,im.mode==spec['mode'] and list(im.size)==spec['size'] and flat==spec['channel_ranges'],mode=im.mode,size=list(im.size),ranges=flat)
 for variant in ('control','roughness-mips','sss-off-diagnostic'):
  root=Path('/workspace/scratch/visual-round2/role-01')/variant
  receipt=json.loads((root/'manifest.json').read_text()); edits=receipt['edits']; files=[f for f in (root/'overlay').rglob('*') if f.is_file()]
  ok=len(edits)==len(files)==(0 if variant=='control' else 1)
  for edit in edits:
   src=(PROJECT/edit['path']).read_bytes(); changed=(root/'overlay'/edit['path']).read_bytes()
   ok=ok and hashlib.sha256(src).hexdigest()==edit['source_sha256'] and hashlib.sha256(changed).hexdigest()==edit['candidate_sha256']
   ok=ok and changed==src.replace(edit['old'].encode(),edit['new'].encode(),1)
  check('Exact one-variable overlay '+variant,ok,files=len(files),declared_changes=profile['variants'][variant]['changes'])
 original=PROJECT/'assets/heroes/rama-hero.glb'; before,doc,start=glb(original); after,other,other_start=glb(args.candidate)
 check('Form candidate JSON materials texture bindings rig and morph declarations exact',doc==other and start==other_start)
 allowed=np.zeros(len(before),dtype=bool); rows=[]
 for mi,pi in ((1,0),(2,11),(2,12)):
  prim=doc['meshes'][mi]['primitives'][pi]; attrs=prim['attributes']; values={}
  for semantic in ('POSITION','NORMAL','TANGENT'):
   a,offset,stride=dense(before,doc,start,attrs[semantic]); b,_,_=dense(after,other,other_start,attrs[semantic]); values[semantic]=(a,b)
   width=3 # tangent handedness W is intentionally outside permitted byte region
   for row in range(len(a)): allowed[offset+row*stride:offset+row*stride+width*4]=True
  a,b=values['POSITION']; moved=np.any(a!=b,axis=1); n0,n=values['NORMAL'];t0,t=values['TANGENT']
  material=doc['materials'][prim['material']]['name']
  row={'mesh':mi,'primitive':pi,'material':material,'moved':int(moved.sum()),'max_displacement_m':float(np.linalg.norm((b-a).astype(float),axis=1).max()),'max_abs_normal_tangent_dot':float(np.abs((n*t[:,:3]).sum(axis=1)).max()),'moved_max_abs_normal_tangent_dot':float(np.abs((n[moved]*t[moved,:3]).sum(axis=1)).max()),'tangent_w_exact':bool(np.array_equal(t[:,3],t0[:,3]))}
  rows.append(row)
  check('Form frame/material preservation '+material+' '+str((mi,pi)),row['tangent_w_exact'] and np.isfinite(n).all() and np.isfinite(t).all() and row['moved_max_abs_normal_tangent_dot']<1e-6 and row['max_displacement_m']<.002 and np.array_equal(n[~moved],n0[~moved]) and np.array_equal(t[~moved],t0[~moved]),**row)
 diff=np.frombuffer(before,dtype='u1')!=np.frombuffer(after,dtype='u1')
 check('All bytes outside declared base position normal tangent XYZ remain exact',np.all(allowed[diff]),changed_bytes=int(diff.sum()),scope='Includes original UVs, skin weights, sparse morph payloads, image bytes, unrelated geometry and animation payloads')
 result={'task':'R2-09','source_commit':PIN,'passed':all(c['passed']for c in checks),'checks':checks,'candidate':str(args.candidate),'candidate_sha256':sha(args.candidate),'original_sha256':sha(original),'script_sha256':sha(__file__),'scope':'Independent source/pixel-channel/frame preservation; no deformation or visual quality acceptance'}
 args.report.write_text(json.dumps(result,indent=2)+'\n'); raise SystemExit(0 if result['passed'] else 1)
if __name__=='__main__': main()
