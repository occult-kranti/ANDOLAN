"""Finite secondary displacement stress on admitted source materials only."""
import gzip,json,sys,time
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE));from check_candidate import ROOT,GLB,sha,PINS,candidate,transform,contacts,skin
out=HERE/'secondary-stress-r5.json';assert not out.exists();began=time.monotonic();folder=HERE/'candidate-r5';manifest=json.loads((folder/'source-manifest.json').read_text())
tape=ROOT/'docs/evidence/desktop-finish/hair-silhouette/W2/smooth-parent-pose-r1.json';fresh=json.loads(tape.read_text());assert sha(tape)=='e5b321f65f1faca587a871edab37deb557f0aca0ba2bf31bb8fa8f89508dff4f'
draw=ROOT/'docs/evidence/desktop-finish/S3/W3/native-r5.json.gz';old=json.loads(gzip.decompress(draw.read_bytes()))
kinds={'Cobalt handwoven silk':'cloth','Cobalt lotus brocade':'cloth','Worked warm gold':'cloth','Swept black hair':'hair'};runtime=ROOT/'scripts/rama_secondary_motion.gd';text=runtime.read_text();assert 'const CLOTH_LIMIT := .075'in text and 'const HAIR_LIMIT := .018'in text;assert 'const MATERIAL_KINDS := {"Cobalt handwoven silk":"cloth", "Cobalt lotus brocade":"cloth", "Worked warm gold":"cloth", "Swept black hair":"hair"}'in text
rows=[]
for level,pin in PINS.items():
 name='rama-hero'+(''if level=='near'else'-'+level)+'.glb';g=GLB(ROOT/'art/hero-finish/s4-diadem-smooth/candidate-r2'/name);assert sha(g.path)==pin;names=[g.doc['nodes'][j]['name']for j in g.doc['skins'][0]['joints']];ib=g.array(g.doc['skins'][0]['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1).astype(float)
 parts={}
 for mi,pi,p in g.primitives():
  a=p['attributes'];v=g.array(a['POSITION']);j=g.array(a['JOINTS_0']);w=g.array(a['WEIGHTS_0']);tri=g.array(p['indices']).reshape(-1,3);material=g.doc['materials'][p['material']]['name']
  if mi==2 and pi in[2,5,6]:tri=tri[~np.all((np.sum(np.where(j==50,w,0),axis=1)>.999999)[tri],axis=1)]
  key=f'mesh{mi}/primitive{pi}/'+material;parts[key]={'v':v,'j':j,'w':w,'tri':tri,'kind':kinds.get(material),'alpha2':np.clip(g.array(a['COLOR_0'],normalized=True)[:,3],0,1)**2}
 v,t=candidate(GLB(folder/Path(manifest['levels'][level]['path']).name));samples=[(s['id'],np.array([s['bone_global_poses'][n]for n in names]))for s in fresh['samples']if s['id']in['rest','measured_step_recoil','piercing_dawn_release','dawn_volley_recoil']];samples.append((old['samples'][62]['id'],np.array(old['samples'][62]['bone_globals'])))
 for label,poses in samples:
  base={n:skin(p['v'],p['j'],p['w'],poses@ib)for n,p in parts.items()};moved=transform(v,poses[49])
  for axis in [np.array([1.,0,0]),np.array([0.,1,0]),np.array([0.,0,1]),np.ones(3)/np.sqrt(3)]:
   for sign in[-1,1]:
    posed={}
    for name,p in parts.items():
     offset=axis*sign*(.075 if p['kind']=='cloth'else-.018 if p['kind']=='hair'else 0.);posed[name]=base[name]+p['alpha2'][:,None]*offset
    check=contacts(moved,t,parts,posed);fail={k:c['crossings']for k,c in check.items()if c['crossings']};rows.append({'level':level,'pose':label,'cloth_offset':(axis*sign*.075).tolist(),'hair_offset':(-axis*sign*.018).tolist(),'contacts':check,'passed':not fail});print(level,label,fail,flush=True)
report={'schema':1,'complete':True,'passed':all(r['passed']for r in rows),'checker_sha256':sha(__file__),'secondary_script_sha256':sha(runtime),'candidate_manifest_sha256':sha(folder/'source-manifest.json'),'source_pins':PINS,'rows':rows,'elapsed_s':time.monotonic()-began,'scope':'Five source pose witnesses×8opposing cardinal/diagonal max-offset fixtures×3LODs. Only actual admitted materials get alpha-squared offsets. Skin/neck/bones stay skinned/static; newarmouralpha0. Stress extremes are not an observed continuous motion claim.'};out.write_text(json.dumps(report,indent=2)+'\n');print('complete',report['passed'],report['elapsed_s'])
