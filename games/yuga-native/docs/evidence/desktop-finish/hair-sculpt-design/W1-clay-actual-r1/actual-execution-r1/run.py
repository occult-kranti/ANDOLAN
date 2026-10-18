from pathlib import Path
import subprocess,hashlib,json,os,time,signal,shutil,datetime
root=Path(__file__).parent;src=root.parent/'framing-r3';out=src/'render-r1'
expected={'whole-hair-clay-framing-r3.blend':'71763ab25ed84719a8479bcce771732d50db980780b47c7c4b68114bf2bb9c2f','capture_clay_framing_r3.py':'206e30aa75c8eecbb4da95b7515f9dc70c0b2a20d732c370f48fc3bad32932ef','projection_contract.py':'89072ccb9656879ca26c5f4c3d043597cc901a260c0ea163d0bc592a34b477df'}
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert not out.exists();assert shutil.disk_usage('/workspace').free>=500*1024**2
before={k:h(src/k) for k in expected};assert before==expected
exe=Path('/usr/bin/blender');cmd=['taskset','-c','0,1',str(exe),'--background',str(src/'whole-hair-clay-framing-r3.blend'),'--threads','2','--python-exit-code','1','--python',str(src/'capture_clay_framing_r3.py'),'--','--output',str(out)]
rec={'scope':'Four CPU Cycles authoring clay originals; no Godot/runtime/animated cast/material acceptance.','argv':cmd,'source_before':before,'blender':{'path':str(exe),'bytes':exe.stat().st_size,'sha256':h(exe)},'overall_seconds':900,'workspace_free_before':shutil.disk_usage('/workspace').free,'start_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
assert not (root/'execution.json').exists()
env=os.environ.copy()
for key,name in [('TMPDIR','temp'),('XDG_CACHE_HOME','cache'),('XDG_CONFIG_HOME','config')]:
 (root/name).mkdir(exist_ok=True);env[key]=str(root/name)
rec['private_environment_paths']={key:env[key] for key in ('TMPDIR','XDG_CACHE_HOME','XDG_CONFIG_HOME')}
started=time.monotonic()
with (root/'run.log').open('wb') as log:
 proc=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,env=env);rec['pid']=proc.pid;(root/'execution.json').write_text(json.dumps(rec,indent=2)+'\n');print(json.dumps({'pid':proc.pid,'output':str(out)}),flush=True)
 try:code=proc.wait(timeout=900);reason='process_exit'
 except subprocess.TimeoutExpired:
  reason='overall900_timeout';os.killpg(proc.pid,signal.SIGTERM)
  try:code=proc.wait(timeout=10)
  except subprocess.TimeoutExpired:os.killpg(proc.pid,signal.SIGKILL);code=proc.wait()
rec.update(exit_code=code,reason=reason,elapsed_seconds=time.monotonic()-started,source_after={k:h(src/k) for k in expected},workspace_free_after=shutil.disk_usage('/workspace').free)
rec['source_unchanged']=rec['source_after']==before
capture=json.loads((out/'capture.json').read_text()) if (out/'capture.json').exists() else {}
rec['complete']=bool(code==0 and capture.get('complete') and len(list(out.glob('*.png')))==4 and rec['source_unchanged'])
(root/'execution.json').write_text(json.dumps(rec,indent=2)+'\n');print(json.dumps({'complete':rec['complete'],'elapsed_seconds':rec['elapsed_seconds'],'exit_code':code}),flush=True);raise SystemExit(0 if rec['complete'] else 1)
