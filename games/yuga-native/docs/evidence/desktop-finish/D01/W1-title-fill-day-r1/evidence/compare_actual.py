from pathlib import Path
import json,hashlib,numpy as np
from PIL import Image
A=Path('/tmp/yuga-title-floor-normal-r1/render-baseline-r1');B=Path('/tmp/yuga-title-fill-r1/render-candidate-r1')
a=json.loads((A/'capture.json').read_text());b=json.loads((B/'capture.json').read_text())
ra=json.loads((A.parent/(A.name+'-logs')/'run.json').read_text());rb=json.loads((B.parent/(B.name+'-logs')/'run.json').read_text())
def diff(a,b,p=''):
 if type(a)!=type(b):return [{'path':p,'a':a,'b':b}]
 if isinstance(a,dict):return sum((diff(a.get(k),b.get(k),p+'/'+k) for k in sorted(set(a)|set(b))),[])
 if isinstance(a,list):
  if len(a)!=len(b):return [{'path':p,'lengths':[len(a),len(b)]}]
  return sum((diff(x,y,p+'/'+str(i)) for i,(x,y) in enumerate(zip(a,b))),[])
 return [] if a==b else [{'path':p,'a':a,'b':b}]
rows=[]
for x,y in zip(a['shots'],b['shots']):
 assert x['id']==y['id'];pa=A/(x['id']+'.png');pb=B/(y['id']+'.png');aa=np.array(Image.open(pa)).astype(np.int16);bb=np.array(Image.open(pb)).astype(np.int16);d=np.abs(aa-bb)
 changes=diff(x,y);important=[z for z in changes if z['path'] not in {'/sha256','/file'}]
 rows.append({'id':x['id'],'same_recorded_controls':not important,'metadata_differences':changes,'unignored_differences':important,'pixel_difference':{'changed_pixels':int(np.any(d,axis=-1).sum()),'max_channel_delta':int(d.max()),'mean_absolute_channel_delta':float(d.mean())},'baseline_sha256':hashlib.sha256(pa.read_bytes()).hexdigest(),'candidate_sha256':hashlib.sha256(pb.read_bytes()).hexdigest()})
delta=[k for k in sorted(set(ra['source_files'])|set(rb['source_files'])) if ra['source_files'].get(k)!=rb['source_files'].get(k)]
keys=['engine_sha256','runner_sha256','helper_sha256','affinity','thread_limits','godot_worker_pool_limit','render_thread_override','shader_cache_seed','godot_shader_cache_seed']
equality={k:ra[k]==rb[k] for k in keys}
r={'passed':all(x['same_recorded_controls'] for x in rows) and all(equality.values()) and delta==['scripts/courtyard.gd'] and a['source_unchanged'] and b['source_unchanged'],'same_recorded_controls':all(x['same_recorded_controls'] for x in rows),'rows':rows,'source_delta':delta,'equal_launch_controls':equality,'baseline_reused':str(A),'candidate':str(B),'scope':'Exact recorded scene/camera/hero/state/clock controls. Helper does not record all164 final bone matrices or actual light numeric state; light-only assignments are source-pinned.'}
Path('/tmp/yuga-title-fill-r1/evidence/actual-comparison.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps({'passed':r['passed'],'source_delta':delta,'equal_launch_controls':equality,'rows':[{'id':x['id'],'unignored':x['unignored_differences'],'pixels':x['pixel_difference']} for x in rows]},indent=2))
