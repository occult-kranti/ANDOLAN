"""Additional exact named-bone R2 pose tape: all five ability stages,3sourceLODs."""
import argparse,json,sys,time
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE));from check_candidate import ROOT,GLB,sha,PINS,candidate,transform,collider_parts,contacts,skin
TAPE=ROOT/'docs/evidence/desktop-finish/hair-silhouette/W2/smooth-parent-pose-r1.json'
PIN='e5b321f65f1faca587a871edab37deb557f0aca0ba2bf31bb8fa8f89508dff4f'
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--candidate',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args();assert not args.output.exists();began=time.monotonic()
 assert sha(TAPE)==PIN;tape=json.loads(TAPE.read_text());assert tape['passed']and len(tape['samples'])==37 and tape['source_pins']['res://assets/heroes/rama-hero.glb']==PINS['near']
 manifest=json.loads((args.candidate/'source-manifest.json').read_text());rows=[]
 for level,pin in PINS.items():
  name='rama-hero'+(''if level=='near'else'-'+level)+'.glb';g=GLB(ROOT/'art/hero-finish/s4-diadem-smooth/candidate-r2'/name);assert sha(g.path)==pin
  names=[g.doc['nodes'][j]['name']for j in g.doc['skins'][0]['joints']];assert len(names)==164 and names[49]=='shoulder01.L';ib=g.array(g.doc['skins'][0]['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1).astype(float)
  for i,name in enumerate(names):assert np.max(abs(np.array(tape['bone_global_rests'][name])-np.linalg.inv(ib[i])))<2e-6,(level,name)
  parts={k:v for k,v in collider_parts(g).items()if not k.startswith('Existing left cap / ')}
  for mi,pi,p in g.primitives():
   if mi==2 and pi in[0,2,3,4,5,6,11]:continue
   a=p['attributes'];parts[f'mesh{mi}/primitive{pi}/'+g.doc['materials'][p['material']]['name']]={'v':g.array(a['POSITION']),'tri':g.array(p['indices']).reshape(-1,3),'j':g.array(a['JOINTS_0']),'w':g.array(a['WEIGHTS_0'])}
  source=args.candidate/Path(manifest['levels'][level]['path']).name;assert sha(source)==manifest['levels'][level]['sha256'];v,t=candidate(GLB(source))
  for sample in tape['samples']:
   poses=np.array([sample['bone_global_poses'][name]for name in names]);posed={n:skin(p['v'],p['j'],p['w'],poses@ib)for n,p in parts.items()};moved=transform(v,poses[49]);check=contacts(moved,t,parts,posed)
   rows.append({'level':level,'pose':sample['id'],'contacts':check,'passed':all(c['crossings']==0 for c in check.values())});print(level,sample['id'],{k:c['crossings']for k,c in check.items()if c['crossings']},flush=True)
 result={'schema':1,'complete':True,'passed':all(r['passed']for r in rows),'checker_sha256':sha(__file__),'shared_checker_sha256':sha(HERE/'check_candidate.py'),'candidate_manifest_sha256':sha(args.candidate/'source-manifest.json'),'tape_sha256':PIN,'source_pins':PINS,'pose_source_pins':tape['source_pins'],'levels':3,'rows':rows,'elapsed_s':time.monotonic()-began,'scope':'Exact named-bone captured direct-API poses, all18 source primitive groups minus superseded leftcap. Neutral face surface and nominal shader offsets; no nocked-arrow transform in this tape. Actual imported render/continuous collision/secondary stress are separate.'}
 args.output.write_text(json.dumps(result,indent=2)+'\n');print('complete',result['passed'],result['elapsed_s'])
if __name__=='__main__':main()
