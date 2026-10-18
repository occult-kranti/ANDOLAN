"""Full-triangle source candidate contacts; distinct from native/raster acceptance."""
import argparse, hashlib, importlib.util, json
from pathlib import Path
import numpy as np
from build_candidate import PROJECT, GLB, PINS, sha

p=PROJECT/'docs/evidence/visual-rounds/round3/role10/geometry_probe.py'
spec=importlib.util.spec_from_file_location('narrow_phase',p);narrow=importlib.util.module_from_spec(spec);spec.loader.exec_module(narrow)


def part(g,mi,pi,selection=None):
 primitive=g.doc['meshes'][mi]['primitives'][pi]
 v=g.array(primitive['attributes']['POSITION']).astype(float);t=g.array(primitive['indices']).reshape(-1,3)
 if selection is not None:t=t[selection(v,t)]
 used,index=np.unique(t,return_inverse=True)
 c=g.array(primitive['attributes']['COLOR_0'],True)[used,3] if 'COLOR_0' in primitive['attributes'] else np.zeros(len(used))
 return {'v':v[used],'tri':index.reshape(-1,3),'j':g.array(primitive['attributes']['JOINTS_0'])[used],
         'w':g.array(primitive['attributes']['WEIGHTS_0'])[used],'alpha':c}


def posed(piece,transforms,offset=None):
 v=np.c_[piece['v'],np.ones(len(piece['v']))];result=np.zeros((len(v),3))
 for slot in range(4):result+=np.einsum('nij,nj->ni',transforms[piece['j'][:,slot]],v)[:,:3]*piece['w'][:,slot,None]
 if offset is not None:result+=offset*piece['alpha'][:,None]**2
 return result[piece['tri']]


def setup(manifest,level):
 row=manifest['levels'][level];g=GLB(row['output']);old=GLB(row['source'])
 assert sha(g.path)==row['output_sha256'] and sha(old.path)==PINS[level]
 hp=g.doc['meshes'][2]['primitives'][0];v=g.array(hp['attributes']['POSITION']).astype(float);t=g.array(hp['indices']).reshape(-1,3)
 new=part(g,2,0,lambda v,t:np.arange(len(t))>=row['retained_triangles'])
 lower=part(g,2,0,lambda v,t:(np.arange(len(t))>=row['retained_triangles']) & np.any(v[t,1]<1.71,axis=1))
 inv=g.array(g.doc['skins'][0]['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1).astype(float)
 names=[g.doc['nodes'][i]['name'] for i in g.doc['skins'][0]['joints']]
 assert names[104]=='head' and len(names)==164
 return row,g,old,new,lower,v[t],inv,names


def main():
 ap=argparse.ArgumentParser();ap.add_argument('--manifest',type=Path,required=True);ap.add_argument('--output',type=Path,required=True)
 ap.add_argument('--mode',choices=['rest','poses','stress'],required=True);ap.add_argument('--poses',type=Path)
 ap.add_argument('--level',choices=['near','mid','far','all'],default='all');ap.add_argument('--start',type=int,default=0);ap.add_argument('--count',type=int,default=37)
 a=ap.parse_args();assert not a.output.exists();m=json.loads(a.manifest.read_text());checks=[]
 result={'scope':'Stored source triangles; actual captured baseline matrices replayed offline. No candidate import/raster/general motion claim.',
  'mode':a.mode,'manifest_sha256':sha(a.manifest),'checker_sha256':sha(__file__),'triangle_dependency_sha256':sha(p),'selfcheck':narrow.selfcheck(),'rows':checks}
 levels=['near','mid','far'] if a.level=='all' else [a.level]
 tape=json.loads(a.poses.read_text()) if a.poses else None
 if tape:
  assert tape['passed'] and tape['source_pins']['res://assets/heroes/rama-hero.glb']==PINS['near']
  result['actual_pose_tape_sha256']=sha(a.poses)
 for level in levels:
  row,g,old,new,lower,allhair,inv,names=setup(m,level)
  if a.mode=='rest':
   skin=[]
   for mi,mesh in enumerate(old.doc['meshes']):
    for pi,pr in enumerate(mesh['primitives']):
     material=old.doc['materials'][pr['material']]['name']
     if material not in ['Rama warm skin','Natural lips','Warm sclera','Deep brown iris','Pupil']:continue
     vv=old.array(pr['attributes']['POSITION']);tt=old.array(pr['indices']).reshape(-1,3)
     tt=tt[np.any(vv[tt,1]>1.65,axis=1)]
     if len(tt):skin.append(vv[tt])
   gen=posed(new,np.repeat(np.eye(4)[None],164,axis=0))
   comparisons={'full_head_skin_and_features':narrow.compare(gen,np.concatenate(skin),band=.008)}
   for label,model in [('acceptedSmoothR2',old),('historicalBand',GLB(PROJECT/'art/visual-rounds/groom/principal-groom-v1'/g.path.name))]:
    gold=model.doc['meshes'][2]['primitives'][2];gv=model.array(gold['attributes']['POSITION']);gt=model.array(gold['indices']).reshape(-1,3)
    headgold=gv[gt[np.any(gv[gt,1]>1.75,axis=1)]]
    crown_manifest=json.loads((PROJECT/'art/hero-finish/s4-diadem-smooth/candidate-r2/source-manifest.json').read_text())
    crown_row=crown_manifest['levels'][level]
    assert sha(model.path)==(crown_row['source_sha256'] if label=='historicalBand' else crown_row['sha256'])
    ids=np.array(crown_row['selected_vertex_ids']);rail=gv[gt[np.all(np.isin(gt,ids),axis=1)]]
    assert len(rail)==crown_row['selected_triangles']
    comparisons[label+'_headgold_vs_generated']=narrow.compare(gen,headgold,band=.008)
    comparisons[label+'_lowerrail_vs_complete_hair']=narrow.compare(allhair,rail,band=.008)
    result[label+'_crown_'+level+'_sha256']=sha(model.path)
   checks.append({'level':level,'comparisons':comparisons,'passed':all(x['crossings']==0 and x['guaranteed_lower_bound_m']>.0002 for x in comparisons.values())})
   print(level,{k:(v['crossings'],v['guaranteed_lower_bound_m']) for k,v in comparisons.items()},flush=True)
  else:
   assert tape is not None
   collars={label:part(old,2,pi,lambda v,t:np.any(v[t,1]>1.40,axis=1)&np.any(v[t,1]<1.72,axis=1)&np.all(abs(v[t,0])<.30,axis=1)) for label,pi in [('gold',2),('silk',3),('brocade',4),('neck',11)]}
   samples=tape['samples'][a.start:a.start+a.count]
   if a.mode=='stress':samples=[s for s in samples if s['id'] in ['rest','piercing_dawn_windup','measured_step_release','measured_step_recoil']]
   for sample in samples:
    poses=np.array([sample['bone_global_poses'][name] for name in names]);transforms=poses@inv
    offsets=[('nominal',None,None)] if a.mode=='poses' else [(str(axis.tolist())+'*'+str(sign),axis*sign*.018,-axis*sign*.075) for axis in [np.array([1.,0,0]),np.array([0.,1,0]),np.array([0.,0,1]),np.ones(3)/np.sqrt(3)] for sign in [-1,1]]
    for label,ho,co in offsets:
     hair=posed(lower,transforms,ho)
     comparisons={name:narrow.compare(hair,posed(piece,transforms,co),band=.010) for name,piece in collars.items()}
     passed=all(v['crossings']==0 and v['guaranteed_lower_bound_m']>.0002 for v in comparisons.values())
     checks.append({'level':level,'pose':sample['id'],'offset':label,'comparisons':comparisons,'passed':passed})
     print(level,sample['id'],label,{k:(v['crossings'],round(v['guaranteed_lower_bound_m']*1000,3)) for k,v in comparisons.items()},flush=True)
     a.output.write_text(json.dumps({**result,'passed':all(r['passed'] for r in checks),'complete':False},indent=2)+'\n')
 result.update(passed=all(r['passed'] for r in checks),complete=True)
 a.output.write_text(json.dumps(result,indent=2)+'\n')
 raise SystemExit(0 if result['passed'] else 1)

if __name__=='__main__':main()
