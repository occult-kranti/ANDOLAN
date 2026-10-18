"""Incremental bridge attachment invariance and declared collar stress. No native claim."""
import argparse,json
from pathlib import Path
import numpy as np
from check_candidate import setup,piece,posed,narrow
from check_draw_contacts import compare_with_bounds
from build_candidate import PROJECT,sha

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--manifest',type=Path,required=True);ap.add_argument('--poses',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--level',choices=['near','mid','far'],required=True);a=ap.parse_args();assert not a.output.exists()
 m=json.loads(a.manifest.read_text());row=m['levels'][a.level];old,g,v,t,new=setup(row);tape=json.loads(a.poses.read_text());assert tape['passed'] and len(tape['samples'])==37
 names=[g.doc['nodes'][i]['name']for i in g.doc['skins'][0]['joints']];ib=g.array(g.doc['skins'][0]['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1)
 checks=[]
 def check(name,okay,**facts):checks.append(dict(name=name,passed=bool(okay),**facts))
 hp=old.doc['meshes'][2]['primitives'][0];ov=old.array(hp['attributes']['POSITION']);ot=old.array(hp['indices']).reshape(-1,3);alpha=old.array(hp['attributes']['COLOR_0'],True)[:,3];j=old.array(hp['attributes']['JOINTS_0']);w=old.array(hp['attributes']['WEIGHTS_0']);anchored=(alpha==0)&np.all(j==[104,0,0,0],axis=1)&np.all(w==[1,0,0,0],axis=1)
 ret=json.loads((PROJECT/'art/hero-finish/hair-silhouette-r1/candidate-r4/groom-manifest.json').read_text())['levels'][a.level]['retained_triangles']
 triangles=v[t[row['preserved_triangles']:]]
 for label,mask in [('knot',(np.arange(len(ot))<ret)&np.all(ov[ot,1]>1.854,axis=1)),('crown',(np.arange(len(ot))>=ret)&np.any(ov[ot,1]>1.80,axis=1))]:
  fixed=mask&np.all(anchored[ot],axis=1);contact=narrow.compare(triangles,ov[ot[fixed]],band=.012);check('attachment overlaps fully anchored head104 '+label,contact['crossings']>0,comparison=contact,anchored_target_triangles=int(fixed.sum()))
 collars={label:piece(old,2,pi,lambda v,t:np.any(v[t,1]>1.40,axis=1)&np.any(v[t,1]<1.72,axis=1)&(v[t,0].min(axis=1)<.30)&(v[t,0].max(axis=1)>-.30))for label,pi in [('gold',2),('silk',3),('brocade',4),('neck',11)]}
 samples=[s for s in tape['samples']if s['id']in ['rest','piercing_dawn_windup','measured_step_release','measured_step_recoil']];assert len(samples)==4
 for sample in samples:
  tr=np.array([sample['bone_global_poses'][name]for name in names])@ib
  for axis in [np.array([1.,0,0]),np.array([0.,1,0]),np.array([0.,0,1]),np.ones(3)/np.sqrt(3)]:
   for sign in [-1,1]:
    hair=posed(new,tr,axis*sign*.018);contacts={name:compare_with_bounds(hair,posed(part,tr,None if name=='neck'else-axis*sign*.075),band=.010)for name,part in collars.items()};check(sample['id']+' '+str((axis*sign).tolist()),all(c['crossings']==0 and c['guaranteed_lower_bound_m']>.0002 for c in contacts.values()),comparisons=contacts)
 result=dict(scope='R5 new triangles only. Existing captured baseline matrices replayed offline; 18mm hair and opposing 75mm cloth displacement scaled by actual alpha squared. Neck stays static under the runtime shader contract. No native continuity or raster acceptance.',manifest_sha256=sha(a.manifest),pose_tape_sha256=sha(a.poses),checker_sha256=sha(__file__),secondary_owner_sha256=sha(PROJECT/'scripts/rama_secondary_motion.gd'),level=a.level,checks=checks,passed=all(c['passed']for c in checks),complete=True);a.output.write_text(json.dumps(result,indent=2)+'\n');print(a.level,result['passed'],len(checks),[c['name']for c in checks if not c['passed']]);raise SystemExit(0 if result['passed']else 1)
if __name__=='__main__':main()
