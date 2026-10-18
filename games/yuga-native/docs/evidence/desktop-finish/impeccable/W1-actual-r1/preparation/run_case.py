from pathlib import Path
import argparse,hashlib,json,os,subprocess,signal,time,shutil,importlib.util,datetime
W=Path(__file__).resolve().parent.parent;P=W/'project';PRE=W/'preparation'
ENGINE=Path('/workspace/tooling/godot-public-4.6.3/binaries/godot-4.6.3-public-template-debug-pipeline-low-priority');ENGINE_SHA='e69af4f6f07876a83e49a02a86928db00993f88594c05ae589e4021d6916d54e'
G=Path('/tmp/yuga-public463-template-baseline-cold-600-r1-logs/user/data/godot/app_userdata/YUGA • Confluence/shader_cache');M=Path('/tmp/yuga-public463-template-baseline-cold-600-r1-logs/user/cache/mesa')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
spec=importlib.util.spec_from_file_location('snapshot','/workspace/scratch/yuga-frontage-production-r1/harness/snapshot.py');snap=importlib.util.module_from_spec(spec);spec.loader.exec_module(snap)
p=argparse.ArgumentParser();p.add_argument('case',choices=['title100','title200','recovery','cancel']);a=p.parse_args();case=a.case;out=W/(case+'-r1');meta=W/(case+'-execution-r1');assert not out.exists() and not meta.exists();meta.mkdir()
assert sha(ENGINE)==ENGINE_SHA and sha(P/snap.MARKER)=='1b99538c1aa1a0bc9842d691d7a329e6aa29720f89b8283006096627916bb24e';snap.verify(P)
scale='2' if case=='title200' else '1';title=case.startswith('title');display={'title100':180,'title200':181,'recovery':182,'cancel':183}[case]
plan=PRE/'title-plan.json' if title else (P/'tools/ui-campaign/boot-recovery-plan.json' if case=='recovery' else PRE/'cancel-plan.json')
allowance=(28 if title else 4)*1024**2;assert shutil.disk_usage(W).free>=500*1024**2+allowance
cmd=['taskset','-c','0,1','python3',str(P/'tools/ui-campaign/run.py'),'--project',str(P),'--mode','integrated' if title else ('boot_recovery' if case=='recovery' else 'transition_fixture'),'--plan',str(plan),'--engine',str(ENGINE),'--renderer','forward_plus' if title else 'gl_compatibility','--render-threads','2' if title else '1','--width','960','--height','540','--display',str(display),'--timeout','120','--output',str(out)]
if title:cmd+=['--godot-shader-cache-seed',str(G),'--shader-cache-seed',str(M)]
env=os.environ.copy();env['YUGA_UI_REVIEW_SCALE']=scale;env['TMPDIR']=str(meta/'temp');Path(env['TMPDIR']).mkdir()
inputs={str(p):sha(p) for p in [ENGINE,P/snap.MARKER,P/'tools/ui-campaign/run.py',P/'tools/ui-campaign/observer.gd',plan]}
record={'case':case,'scope':'Declared native-XTest title/loading presentation review; scale fixture1/2, tiny missing-scene/queued-cancel fixtures explicitly separate; no gameplay or package acceptance','argv':cmd,'env_ui_scale':scale,'inputs':inputs,'start_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'workspace_free_before':shutil.disk_usage(W).free,'floor_bytes':500*1024**2,'overall_seconds':600 if title else 150}
start=time.monotonic();reason='process_exit'
with (meta/'wrapper.log').open('xb') as log:
 proc=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,env=env,start_new_session=True);record['pid']=proc.pid;(meta/'execution.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({'case':case,'pid':proc.pid,'output':str(out)}),flush=True)
 while proc.poll() is None:
  if time.monotonic()-start>record['overall_seconds']:reason='overall_timeout';break
  if shutil.disk_usage(W).free<record['floor_bytes']:reason='storage_floor_stop';break
  time.sleep(1)
 if proc.poll() is None:
  os.killpg(proc.pid,signal.SIGTERM)
  try:proc.wait(timeout=10)
  except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);proc.wait()
code=proc.returncode
# Owned group contains runner, Xvfb and Godot; reap any remaining children after early failure.
try:os.killpg(proc.pid,signal.SIGTERM)
except ProcessLookupError:pass
run=json.loads((out/'run.json').read_text()) if (out/'run.json').exists() else {};shots=[json.loads(q.read_text()) for q in out.glob('*.json') if q.name not in ['run.json'] and q.with_suffix('.png').exists()];scale_ok=bool(shots) and all(x.get('content_scale_factor')==float(scale) for x in shots)
post={n:sha(n) for n in inputs};stable=post==inputs;snap.verify(P)
record.update(exit_code=code,reason=reason,elapsed_seconds=time.monotonic()-start,workspace_free_after=shutil.disk_usage(W).free,inputs_after=post,source_stable=stable,observed_scale_assertion=scale_ok,observed_png_count=len(shots),complete=bool(code==0 and run.get('complete') and stable and scale_ok))
(meta/'execution.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({k:record[k] for k in ['case','complete','exit_code','reason','elapsed_seconds','observed_png_count','observed_scale_assertion','workspace_free_after']}),flush=True);raise SystemExit(0 if record['complete'] else 1)
