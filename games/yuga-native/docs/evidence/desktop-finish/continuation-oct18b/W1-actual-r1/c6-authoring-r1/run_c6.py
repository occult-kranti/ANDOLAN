from pathlib import Path
import os,subprocess,time,shutil,json,hashlib
W=Path('/workspace/scratch/yuga-next-W1-r1');S=Path('/workspace/scratch/yuga-next-W3-r1/build-r1/whole-hair-sculpt-r6.blend');H=Path('/workspace/ANDOLAN/games/yuga-native/art/hero-finish/hair-sculpt-design/clay-volume-r6/capture_sculpt.py');O=Path('/workspace/scratch/yuga-next-W3-r1/actual-r1');L=W/'c6-actual-r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(S)=='e41417ff09dd5d22de35b0f3b0b7dd5db3711057fe11ffe1f6b3fd819f044aee' and sha(H)=='0d05dacf96490ae3a130e513c9e807bddad2931073fa2fe18942fe131f899dc7';assert not O.exists() and not L.exists();assert shutil.disk_usage(W).free>=500*1024**2
L.mkdir();tmp=L/'tmp';tmp.mkdir();os.sched_setaffinity(0,{0,1});env=os.environ.copy();env.update(LP_NUM_THREADS='2',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='1',TMPDIR=str(tmp))
command=['/usr/bin/blender','--background',str(S),'--threads','2','--python',str(H),'--','--expected-scene-sha256',sha(S),'--output',str(O)]
r={'command':command,'scene_sha256':sha(S),'helper_sha256':sha(H),'minimum_actual_free_bytes':500*1024**2,'affinity':[0,1],'samples':32,'denoising':False,'scope':'Four locked authoring clay views only; no animated/runtime/GLB acceptance.'};p=None;start=time.monotonic();minimum=shutil.disk_usage(W).free
try:
 with (L/'blender.log').open('w') as log:
  p=subprocess.Popen(command,env=env,stdout=log,stderr=subprocess.STDOUT);r['pid']=p.pid
  while p.poll() is None:
   minimum=min(minimum,shutil.disk_usage(W).free)
   if minimum<500*1024**2:raise RuntimeError('500MiB actual floor crossed')
   if time.monotonic()-start>900:raise TimeoutError('900s fourview deadline')
   time.sleep(.25)
 r['exit']=p.returncode;r['source_unchanged']=sha(S)==r['scene_sha256'] and sha(H)==r['helper_sha256'];r['pngs']={a.name:sha(a) for a in O.glob('*.png')};r['complete']=r['exit']==0 and r['source_unchanged'] and len(r['pngs'])==4
except Exception as e:r['complete']=False;r['failure']=str(e)
finally:
 if p and p.poll() is None:
  p.terminate()
  try:p.wait(timeout=5)
  except subprocess.TimeoutExpired:p.kill();p.wait()
 r['elapsed_seconds']=time.monotonic()-start;r['minimum_observed_free_bytes']=minimum;(L/'receipt.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps(r));raise SystemExit(0 if r['complete'] else 1)
