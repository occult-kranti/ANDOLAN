from pathlib import Path
import json,hashlib,numpy as np
from PIL import Image
B=Path('/tmp/yuga-title-floor-normal-r1');a=json.loads((B/'render-baseline-r1/capture.json').read_text());b=json.loads((B/'render-candidate-r1/capture.json').read_text())
def diff(a,b,p=''):
 if type(a)!=type(b):return [{'path':p,'a':a,'b':b}]
 if isinstance(a,dict):return sum((diff(a.get(k),b.get(k),p+'/'+k)for k in sorted(set(a)|set(b))),[])
 if isinstance(a,list):
  if len(a)!=len(b):return [{'path':p,'lengths':[len(a),len(b)]}]
  return sum((diff(x,y,p+'/'+str(i))for i,(x,y)in enumerate(zip(a,b))),[])
 return []if a==b else [{'path':p,'a':a,'b':b}]
rows=[]
for x,y in zip(a['shots'],b['shots']):
 assert x['id']==y['id'];pa=B/'render-baseline-r1'/(x['id']+'.png');pb=B/'render-candidate-r1'/(y['id']+'.png');aa=np.array(Image.open(pa)).astype(np.int16);bb=np.array(Image.open(pb)).astype(np.int16);d=np.abs(aa-bb)
 changes=diff(x,y);ignored={'/sha256','/file','/frame','/physics_frame','/render_frame'};important=[z for z in changes if z['path']not in ignored]
 rows.append({'id':x['id'],'same_recorded_controls':not important,'metadata_differences':changes,'unignored_differences':important,'pixel_difference':{'changed_pixels':int(np.any(d,axis=-1).sum()),'max_channel_delta':int(d.max()),'mean_absolute_channel_delta':float(d.mean())},'baseline_sha256':hashlib.sha256(pa.read_bytes()).hexdigest(),'candidate_sha256':hashlib.sha256(pb.read_bytes()).hexdigest()})
r={'same_recorded_controls':all(x['same_recorded_controls']for x in rows),'rows':rows};(B/'actual-comparison-r1.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'same_recorded_controls':r['same_recorded_controls'],'differences':[{ 'id':x['id'],'paths':[z['path']for z in x['unignored_differences']]}for x in rows]}))
