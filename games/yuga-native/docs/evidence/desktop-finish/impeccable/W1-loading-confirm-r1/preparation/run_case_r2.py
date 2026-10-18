from pathlib import Path
import argparse,hashlib,json,os,subprocess,signal,time,shutil,datetime
W=Path(__file__).resolve().parent.parent;P=W/'source';PRE=W/'preparation'
E=Path('/workspace/tooling/godot-public-4.6.3/binaries/godot-4.6.3-public-template-debug-pipeline-low-priority');EH='e69af4f6f07876a83e49a02a86928db00993f88594c05ae589e4021d6916d54e'
def sha(f):return hashlib.sha256(Path(f).read_bytes()).hexdigest()
p=argparse.ArgumentParser();p.add_argument('scale',choices=['1','2']);a=p.parse_args();name='loading'+str(int(a.scale)*100);out=W/(name+'-r2');meta=W/(name+'-execution-r2');assert not out.exists() and not meta.exists()
manifest=json.loads((PRE/'source-r2.json').read_text());assert all(sha(P/f)==h for f,h in manifest['files'].items());assert sha(E)==EH
assert shutil.disk_usage(W).free>=502*1024**2;meta.mkdir();(meta/'temp').mkdir()
cmd=['taskset','-c','0,1','python3',str(PRE/'run_fixture.py'),'--project',str(P),'--mode','component','--plan',str(PRE/'plan.json'),'--engine',str(E),'--renderer','gl_compatibility','--render-threads','1','--width','960','--height','540','--display',str(184+int(a.scale)),'--timeout','20','--output',str(out)]
env=os.environ.copy();env.update(YUGA_UI_REVIEW_SCALE=a.scale,TMPDIR=str(meta/'temp'))
inputs={str(f):sha(f) for f in [E,PRE/'source-r2.json',PRE/'run_fixture.py',PRE/'plan.json',Path(__file__)]}
r={'scope':'Explicit 2D loading visual fixture: held samples at .475 are not native load timing; real keyboard production-controller error/Retry/Back/cancel. No world, no cache seeds, no package acceptance.','scale':float(a.scale),'argv':cmd,'inputs':inputs,'source_before':manifest['files'],'start_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'workspace_free_before':shutil.disk_usage(W).free,'floor_bytes':500*1024**2,'overall_seconds':90}
start=time.monotonic();reason='process_exit'
with (meta/'wrapper.log').open('xb') as log:
 proc=subprocess.Popen(cmd,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);r['pid']=proc.pid;(meta/'execution.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'pid':proc.pid,'output':str(out)}),flush=True)
 while proc.poll() is None:
  if time.monotonic()-start>90:reason='overall_timeout';break
  if shutil.disk_usage(W).free<500*1024**2:reason='storage_floor_stop';break
  time.sleep(.5)
 if proc.poll() is None:
  os.killpg(proc.pid,signal.SIGTERM)
  try:proc.wait(timeout=5)
  except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);proc.wait()
try:os.killpg(proc.pid,signal.SIGTERM)
except ProcessLookupError:pass
run=json.loads((out/'run.json').read_text()) if (out/'run.json').exists() else {};shots=[json.loads(f.with_suffix('.json').read_text()) for f in out.glob('*.png')]
stable=inputs=={f:sha(f) for f in inputs} and all(sha(P/f)==h for f,h in manifest['files'].items())
scales=bool(shots) and all(s['content_scale_factor']==float(a.scale) and s['logical_viewport_size']==[1280/float(a.scale),720/float(a.scale)] and s['framebuffer_size']==[960,540] for s in shots)
r.update(exit_code=proc.returncode,elapsed_seconds=time.monotonic()-start,reason=reason,source_stable=stable,actual_scale_canvas_assertion=scales,png_count=len(shots),workspace_free_after=shutil.disk_usage(W).free,complete=bool(proc.returncode==0 and run.get('complete') and stable and scales))
(meta/'execution.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:r[k] for k in ['complete','exit_code','elapsed_seconds','png_count','actual_scale_canvas_assertion','workspace_free_after']}),flush=True);raise SystemExit(0 if r['complete'] else 1)
