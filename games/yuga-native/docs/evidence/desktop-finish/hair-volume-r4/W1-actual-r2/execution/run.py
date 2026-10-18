from pathlib import Path
import hashlib,json,subprocess,shutil,os,signal,time,datetime
W=Path(__file__).parent;OUT=W.parent/'actual-r2'
SCENE=W.parent/'build-r2/whole-hair-volume-r4.blend'
HELPER=Path('/workspace/ANDOLAN/games/yuga-native/art/hero-finish/hair-sculpt-design/clay-volume-r4/capture_volume.py')
DEPENDENCY=HELPER.parent.parent/'clay-framing-r3/projection_contract.py'
PINS={str(SCENE):'da97ad89b5660eadc688eb58e4c73cad42b7b3f767daefb99c17028758439a88',str(HELPER):'0d05dacf96490ae3a130e513c9e807bddad2931073fa2fe18942fe131f899dc7',str(DEPENDENCY):'89072ccb9656879ca26c5f4c3d043597cc901a260c0ea163d0bc592a34b477df'}
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert not OUT.exists() and not (W/'execution.json').exists()
assert shutil.disk_usage(W).free>=550*1024**2
before={p:sha(p) for p in PINS};assert before==PINS
cmd=['taskset','-c','0,1','/usr/bin/blender','--background',str(SCENE),'--threads','2','--python-exit-code','1','--python',str(HELPER),'--','--output',str(OUT),'--expected-scene-sha256',PINS[str(SCENE)]]
env=os.environ.copy()
for key,name in [('TMPDIR','temp'),('XDG_CACHE_HOME','cache'),('XDG_CONFIG_HOME','config')]:
 (W/name).mkdir();env[key]=str(W/name)
record={'scope':'Single authorized C4 correction final four-view authoring clay take. Author fresh-load topology/projection checks are separate from visible silhouette/hardware review; no runtime, animated-cast or art acceptance from execution.','argv':cmd,'source_before':before,'blender_sha256':sha('/usr/bin/blender'),'overall_seconds':900,'start_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'workspace_free_before':shutil.disk_usage(W).free,'private_environment_paths':{k:env[k] for k in ('TMPDIR','XDG_CACHE_HOME','XDG_CONFIG_HOME')}}
start=time.monotonic()
with (W/'run.log').open('xb') as log:
 proc=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,env=env);record['pid']=proc.pid;(W/'execution.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({'pid':proc.pid,'output':str(OUT)}),flush=True)
 try:code=proc.wait(timeout=900);reason='process_exit'
 except subprocess.TimeoutExpired:
  reason='overall900_timeout';os.killpg(proc.pid,signal.SIGTERM)
  try:code=proc.wait(timeout=10)
  except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);code=proc.wait()
after={p:sha(p) for p in PINS};capture=json.loads((OUT/'capture.json').read_text()) if (OUT/'capture.json').exists() else {}
record.update(exit_code=code,reason=reason,elapsed_seconds=time.monotonic()-start,source_after=after,source_unchanged=before==after,workspace_free_after=shutil.disk_usage(W).free,complete=bool(code==0 and capture.get('complete') and capture.get('saved_scene_unchanged') and len(list(OUT.glob('*.png')))==4 and before==after))
(W/'execution.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({'complete':record['complete'],'exit_code':code,'elapsed_seconds':record['elapsed_seconds']}),flush=True);raise SystemExit(0 if record['complete'] else 1)
