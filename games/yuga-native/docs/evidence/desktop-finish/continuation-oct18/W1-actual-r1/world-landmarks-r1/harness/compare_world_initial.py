from pathlib import Path
import json,hashlib
from PIL import Image,ImageChops
import numpy as np
W=Path(__file__).parent.parent
A=json.loads((W/'world-baseline-actual-r1/capture.json').read_text());B=json.loads((W/'world-candidate-actual-r1/capture.json').read_text())
def differences(a,b,path=''):
 if type(a)!=type(b):return [{'path':path,'baseline':a,'candidate':b}]
 if isinstance(a,dict):
  z=[]
  for k in sorted(a.keys()|b.keys()):
   if k not in a or k not in b:z.append({'path':path+'/'+k,'baseline':a.get(k),'candidate':b.get(k)})
   else:z+=differences(a[k],b[k],path+'/'+k)
  return z
 if isinstance(a,list):
  if len(a)!=len(b):return [{'path':path,'lengths':[len(a),len(b)]}]
  z=[]
  for i,(x,y) in enumerate(zip(a,b)):z+=differences(x,y,path+'/'+str(i))
  return z
 return [] if a==b else [{'path':path,'baseline':a,'candidate':b}]
a=A['shots'][0];b=B['shots'][0]
admitted={'/process_frame','/physics_frame','/drawn_frame','/pose_signal_counters/process_frame','/pose_signal_counters/physics_frame','/pose_signal_counters/drawn_frame','/frontage/branch','/sha256'}
d= differences(a,b);unexpected=[r for r in d if r['path'] not in admitted]
p=Image.open(W/'world-baseline-actual-r1'/a['file']).convert('RGBA');q=Image.open(W/'world-candidate-actual-r1'/b['file']).convert('RGBA');x=np.array(p);y=np.array(q)
assert p.size==q.size
changed=np.any(x!=y,axis=2);where=np.argwhere(changed);bbox=[int(where[:,1].min()),int(where[:,0].min()),int(where[:,1].max())+1,int(where[:,0].max())+1] if len(where) else None
r={'reports_complete':A['complete'] and B['complete'],'checks_pass':all(c['passed'] for r in [A,B] for c in r['checks']),'admitted_difference_paths':sorted(admitted),'all_shot_differences':d,'unexpected_shot_differences':unexpected,'pixel_check':{'mode':'RGBA all four channels; independent RGB bbox','size':p.size,'different_pixels':int(changed.sum()),'max_channel_delta':int(np.abs(x.astype(int)-y.astype(int)).max()),'all_channel_bbox':bbox,'rgb_bbox':ImageChops.difference(p.convert('RGB'),q.convert('RGB')).getbbox()},'resource_census':{r['branch']:{k:v for k,v in r['production_admission'].items() if k!='projected'} for r in [A,B]},'projection_exact':A['production_admission']['projected']==B['production_admission']['projected']}
r['passed']=r['reports_complete'] and r['checks_pass'] and not unexpected and r['pixel_check']['different_pixels']==0 and r['projection_exact']
(W/'world-comparison-r1.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items() if k not in ['all_shot_differences','unexpected_shot_differences']}));print('unexpected',len(unexpected));raise SystemExit(0 if r['passed'] else 1)
