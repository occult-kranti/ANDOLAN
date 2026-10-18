from pathlib import Path
import json,sys,hashlib
B=Path(__file__).resolve().parent.parent;mode=sys.argv[1];name='preflight.json' if mode=='preflight' else 'capture.json';a=json.loads((B/(mode+'-baseline-r1')/name).read_text());b=json.loads((B/(mode+'-candidate-r1')/name).read_text())
def diff(a,b,p=''):
 if type(a)!=type(b):return [{'path':p,'a':a,'b':b}]
 if isinstance(a,dict):return sum((diff(a.get(k),b.get(k),p+'/'+k) for k in sorted(set(a)|set(b))),[])
 if isinstance(a,list):
  if len(a)!=len(b):return [{'path':p,'lengths':[len(a),len(b)]}]
  return sum((diff(x,y,p+'/'+str(i)) for i,(x,y) in enumerate(zip(a,b))),[])
 return [] if a==b else [{'path':p,'a':a,'b':b}]
rows=[]
for x,y in zip(a['shots'],b['shots']):
 changes=diff(x,y);allowed=lambda p:p in ['/sha256','/file','/portrait_light/energy','/portrait_light/position/0','/portrait_light/position/2','/portrait_light/color/0','/portrait_light/color/1','/portrait_light/color/2'];bad=[z for z in changes if not allowed(z['path'])]
 row={'id':x['id'],'same_controls_except_declared_light':not bad,'differences':changes,'unexpected_differences':bad,'final_bone_count':len(x['final_bones']),'all_final_bones_equal':x['final_bones']==y['final_bones']}
 if mode=='render':
  import numpy as np
  from PIL import Image
  pa=B/('render-baseline-r1')/(x['id']+'.png');pb=B/('render-candidate-r1')/(x['id']+'.png');aa=np.array(Image.open(pa)).astype(np.int16);bb=np.array(Image.open(pb)).astype(np.int16);d=np.abs(aa-bb);row['pixel_difference']={'changed_pixels':int(np.any(d,axis=-1).sum()),'mean_absolute_channel_delta':float(d.mean()),'max_channel_delta':int(d.max())};row['image_sha256']={'baseline':hashlib.sha256(pa.read_bytes()).hexdigest(),'candidate':hashlib.sha256(pb.read_bytes()).hexdigest()}
 rows.append(row)
ra=json.loads((B/(mode+'-baseline-r1-logs')/'run.json').read_text());rb=json.loads((B/(mode+'-candidate-r1-logs')/'run.json').read_text());delta=[k for k in sorted(set(ra['source_files'])|set(rb['source_files'])) if ra['source_files'].get(k)!=rb['source_files'].get(k)];keys=['engine_sha256','helper_sha256','runner_sha256','affinity','thread_limits','godot_worker_pool_limit','render_thread_override','shader_cache_seed','godot_shader_cache_seed'];equal={k:ra.get(k)==rb.get(k) for k in keys}
r={'passed':all(x['same_controls_except_declared_light'] and x['all_final_bones_equal'] and x['final_bone_count']==164 for x in rows) and delta==['scripts/courtyard.gd'] and all(equal.values()) and a['source_unchanged'] and b['source_unchanged'],'mode':mode,'source_delta':delta,'equal_launch_controls':equal,'rows':rows}
(B/'evidence'/(mode+'-comparison.json')).write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'passed':r['passed'],'source_delta':delta,'rows':[{'id':x['id'],'unexpected':x['unexpected_differences'],'bones_equal':x['all_final_bones_equal'],'pixel_difference':x.get('pixel_difference')} for x in rows]},indent=2))
if not r['passed']:raise SystemExit(1)
