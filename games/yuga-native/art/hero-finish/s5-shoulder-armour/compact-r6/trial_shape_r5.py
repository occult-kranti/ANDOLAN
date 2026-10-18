"""Compare ordinary rigid49 cap / rigid50 lame against whole50; no runtime writer."""
import gzip,json,sys,time
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE));from check_candidate import ROOT,GLB,sha,PINS,candidate,transform,collider_parts,contacts,skin
out=HERE/'compact-shape-r5-trial.json';assert not out.exists();began=time.monotonic()
source=ROOT/'art/hero-finish/s4-diadem-smooth/candidate-r2/rama-hero.glb';assert sha(source)==PINS['near'];g=GLB(source);ib=g.array(g.doc['skins'][0]['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1).astype(float);names=[g.doc['nodes'][j]['name']for j in g.doc['skins'][0]['joints']]
manifest=json.loads((HERE/'candidate-r5/source-manifest.json').read_text());cg=GLB(HERE/'candidate-r5/shoulder-armour-near.glb');v,t=candidate(cg);world=transform(v,np.linalg.inv(ib[49]));bindings=np.full(len(v),49);groups=[];vo=to=0
for material in range(3):
 for part in manifest['levels']['near']['components']:
  if part['material']!=material:continue
  if part['name']in['First overlapping deltoid lame','Rolled gold border 2']:bindings[vo:vo+part['vertices']]=50
  groups.append((part['name'],to,to+part['triangles']));vo+=part['vertices'];to+=part['triangles']
assert vo==len(v)and to==len(t)
parts={k:p for k,p in collider_parts(g).items()if not k.startswith('Existing left cap / ')}
tape=ROOT/'docs/evidence/desktop-finish/hair-silhouette/W2/smooth-parent-pose-r1.json';fresh=json.loads(tape.read_text());samples=[(s['id'],np.array([s['bone_global_poses'][n]for n in names]))for s in fresh['samples']]
draw=ROOT/'docs/evidence/desktop-finish/S3/W3/native-r5.json.gz';old=json.loads(gzip.decompress(draw.read_bytes()));samples +=[(s['id'],np.array(s['bone_globals']))for i,s in enumerate(old['samples'])if i in [0,38,62,104,146,198,259,320,347]]
rows=[]
for label,poses in samples:
 posed={n:skin(p['v'],p['j'],p['w'],poses@ib)for n,p in parts.items()}
 for mode in ['all49']:
  bs=np.full(len(v),49);moved=np.zeros_like(v,dtype=float)
  for bone in np.unique(bs):mask=bs==bone;moved[mask]=transform(world[mask],poses[bone]@ib[bone])
  check=contacts(moved,t,parts,posed);fail={k:c['crossings']for k,c in check.items()if c['crossings']};groups_failed={}
  if fail:
   for name,a,b in groups:
    one=contacts(moved,t[a:b],parts,posed);x={k:c['crossings']for k,c in one.items()if c['crossings']}
    if x:groups_failed[name]=x
  rows.append({'pose':label,'mode':mode,'contacts':check,'components':groups_failed,'passed':not bool(fail)});print(label,mode,groups_failed,flush=True)
result={'schema':1,'complete':True,'checker_sha256':sha(__file__),'candidate_sha256':sha(cg.path),'source_sha256':sha(source),'tapes':{str(tape):sha(tape),str(draw):sha(draw)},'samples':len(samples),'rows':rows,'elapsed_s':time.monotonic()-began,'scope':'Ordinary existing bone rigid bindings proposed; no new geometry/bones/controller. Seven relevant body/material groups minus oldcap, not full18 final check.'};out.write_text(json.dumps(result,indent=2)+'\n');print('complete',result['elapsed_s'])
