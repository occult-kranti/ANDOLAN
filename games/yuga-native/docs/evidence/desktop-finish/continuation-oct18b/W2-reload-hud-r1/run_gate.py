from pathlib import Path
import os,sys,subprocess,time,json,hashlib
base=Path(sys.argv[1]);base.mkdir(parents=True,exist_ok=False)
project=Path('/workspace/ANDOLAN/games/yuga-native')
cmd=['taskset','-c','4','timeout','45','godot','--headless','--path',str(project),'--script','res://tests/ui_hud_reload_availability_cases.gd','--','--report='+str(base/'report.json')]+sys.argv[2:]
env=os.environ.copy();env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',XDG_DATA_HOME=str(base/'data'),XDG_CONFIG_HOME=str(base/'config'))
paths=[project/'scripts/rama_hero_hud.gd',project/'tests/ui_hud_reload_availability_cases.gd']
pins={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
start=time.monotonic()
with (base/'run.log').open('wb') as stream:result=subprocess.run(cmd,env=env,stdout=stream,stderr=subprocess.STDOUT)
r={'command':cmd,'exit_code':result.returncode,'duration_seconds':time.monotonic()-start,'source_before':pins,'source_after':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
(base/'execution.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps(r))
if (base/'report.json').exists():
 d=json.loads((base/'report.json').read_text());print('checks',d['count'],'passed',sum(c['passed'] for c in d['checks']))
 print('failures',[c['name'] for c in d['checks'] if not c['passed']])
else:print((base/'run.log').read_text()[-3000:])
