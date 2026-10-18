from pathlib import Path
import json,hashlib
import numpy as np
from PIL import Image
B=Path('/tmp/yuga-paving-pair-r1')
a=json.loads((B/'render-baseline-r1/capture.json').read_text());b=json.loads((B/'render-candidate-r1/capture.json').read_text())
def diff(a,b,p=''):
 if type(a)!=type(b):return [{'path':p,'a':a,'b':b}]
 if isinstance(a,dict):
  out=[]
  for k in sorted(set(a)|set(b)):
   if k not in a or k not in b:out.append({'path':p+'/'+k,'a':a.get(k),'b':b.get(k)})
   else:out+=diff(a[k],b[k],p+'/'+k)
  return out
 if isinstance(a,list):
  if len(a)!=len(b):return [{'path':p,'lengths':[len(a),len(b)]}]
  return sum((diff(x,y,p+'/'+str(i)) for i,(x,y)in enumerate(zip(a,b))),[])
 return [] if a==b else [{'path':p,'a':a,'b':b}]
rows=[]
for sa,sb in zip(a['shots'],b['shots']):
 assert sa['id']==sb['id'];pa=B/'render-baseline-r1'/sa['file'];pb=B/'render-candidate-r1'/sb['file']
 aa=np.array(Image.open(pa)).astype(np.int16);bb=np.array(Image.open(pb)).astype(np.int16);dd=np.abs(aa-bb)
 changes=diff(sa,sb);ignored={'/sha256','/file','/physics_frame','/process_frame','/drawn_frame'}; important=[x for x in changes if x['path']not in ignored]
 rows.append({'id':sa['id'],'baseline_sha256':hashlib.sha256(pa.read_bytes()).hexdigest(),'candidate_sha256':hashlib.sha256(pb.read_bytes()).hexdigest(),'same_controls':not important,'metadata_differences':changes,'unignored_differences':important,'pixel_difference':{'changed_pixels':int(np.any(dd>0,axis=-1).sum()),'max_channel_delta':int(dd.max()),'mean_absolute_channel_delta':float(dd.mean())}})
result={'scope':'Actual still comparison; pixel differences measure image changes, not quality or performance','same_controls':all(x['same_controls']for x in rows),'shots':rows}
(B/'actual-comparison-r1.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'same_controls':result['same_controls'],'rows':[{'id':r['id'],'unignored':[x['path']for x in r['unignored_differences']],'changed_pixels':r['pixel_difference']['changed_pixels']}for r in rows]}))
