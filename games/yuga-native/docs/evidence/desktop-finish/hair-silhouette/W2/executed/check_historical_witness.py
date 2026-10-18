"""Recover the recorded head rigid frame and test four retained recoil patches.

The full historical matrix tape is unavailable. This is deliberately a patch
replay, separate from the fresh complete-body 37-pose current-parent replay.
"""
import argparse,json
from pathlib import Path
import numpy as np
from build_candidate import PROJECT,GLB,sha
from check_contacts import narrow

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--manifest',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();assert not a.output.exists()
 path=PROJECT/'docs/evidence/visual-rounds/round3/role10/r7-action-witness.json';w=json.loads(path.read_text());m=json.loads(a.manifest.read_text());old=GLB(PROJECT/'art/visual-rounds/groom/principal-groom-v1/rama-hero.glb');p=old.doc['meshes'][2]['primitives'][0];oldv=old.array(p['attributes']['POSITION'])
 first=[];second=[];counter=[]
 for row in w['witnesses']:
  source=np.array(row['source_positions']);assert np.max(abs(oldv[row['candidate_hair_vertex_ids']]-source))<1e-12
  target=np.array(row['witness']['witness_hair_triangle']);first.extend(source);second.extend(target)
  test=narrow.compare(target[None],np.array(row['witness']['witness_other_triangle'])[None],band=.01);assert test['crossings']>0
  counter.append({'region':row['region'],'old_contact_counterexample':test})
 first,second=np.array(first),np.array(second);x=first-first.mean(0);y=second-second.mean(0);u,s,v=np.linalg.svd(x.T@y);r=v.T@np.diag([1,1,np.linalg.det(v.T@u.T)])@u.T;t=second.mean(0)-r@first.mean(0)
 residual=float(np.linalg.norm(first@r.T+t-second,axis=1).max());assert residual<2e-6 and abs(np.linalg.det(r)-1)<1e-9
 rows=[]
 for level,row in m['levels'].items():
  g=GLB(row['output']);assert sha(g.path)==row['output_sha256'];p=g.doc['meshes'][2]['primitives'][0];vtx=g.array(p['attributes']['POSITION']);tri=g.array(p['indices']).reshape(-1,3)
  joints=g.array(p['attributes']['JOINTS_0']);weights=g.array(p['attributes']['WEIGHTS_0']);assert np.all(joints[:,0]==104) and np.all(weights[:,0]==1) and np.all(weights[:,1:]==0)
  posed=(vtx@r.T+t)[tri]
  comparisons={c['region']:narrow.compare(posed,np.array(c['witness']['witness_other_triangle'])[None],band=.025) for c in w['witnesses']}
  rows.append({'level':level,'comparisons':comparisons,'passed':all(c['crossings']==0 and c['guaranteed_lower_bound_m']>.0002 for c in comparisons.values())})
 result={'passed':all(c['passed'] for c in rows),'scope':'Four retained actual measured-step-recoil contact patches only, with unit-scale rigid head frame recovered from twelve exact original source/recorded point correspondences. Full historical body pose is unavailable; this does not qualify that entire historical pose. Fresh37-pose full-collar replay is separate.','manifest_sha256':sha(a.manifest),'checker_sha256':sha(__file__),'witness_sha256':sha(path),'rigid_rotation':r.tolist(),'rigid_translation':t.tolist(),'maximum_rigid_frame_residual_m':residual,'counterexamples':counter,'rows':rows}
 a.output.write_text(json.dumps(result,indent=2)+'\n');print('passed',result['passed'],'rigid_residual_m',residual,[(x['level'],{k:round(v['guaranteed_lower_bound_m']*1000,3) for k,v in x['comparisons'].items()}) for x in rows]);raise SystemExit(0 if result['passed'] else 1)
if __name__=='__main__':main()
