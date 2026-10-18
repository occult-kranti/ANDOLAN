"""Run unchanged G1 groom probe with the bounded G0 watchdog; no frame processing."""
import importlib.util,json,os,subprocess,sys
from pathlib import Path
project=Path(sys.argv[1]); output=Path(sys.argv[2]); seed=Path('/tmp/yuga-g1-native-r1/user/cache/mesa')
def module(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
snapshot=module('snapshot',project/'tools/graphics-six/snapshot.py'); snapshot.verify(project)
focus=module('focus',project/'tools/graphics-six/run_focus.py')
legacy=module('legacy',project/'tools/visual-rounds/run.py')
record={'complete':False,'project':str(project),'output':str(output),'driver_sha256':focus.sha(__file__),'snapshot_sha256':focus.sha(project/snapshot.MARKER),'legacy_runner_sha256':focus.sha(legacy.__file__),'helper_sha256':focus.sha(project/'tools/visual-rounds/capture_groom.gd'),'watchdog_helper_sha256':focus.sha(focus.__file__),'case':'unchanged prior G1 groom-probe on G2 runtime','overrides':['verbose logging','remove unsupported max-threads flag','300s overall and120s no-progress watchdog']}
original_run=subprocess.run

def bounded(command,**kwargs):
 if command[0] != '/usr/local/bin/godot':raise RuntimeError('Unexpected subprocess in one-shot probe')
 command=list(command);i=command.index('--max-threads');del command[i:i+2];command.insert(1,'--verbose');record['command']=command
 code=focus.run_engine(command,kwargs['env'],kwargs['stdout'],output.with_suffix('.godot.log'),output,300,120,record)
 return subprocess.CompletedProcess(command,code)
subprocess.run=bounded
os.environ.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
sys.argv=[str(legacy.__file__),'--project',str(project),'--output',str(output),'--mode','groom-probe','--display','194','--shader-cache-seed',str(seed)]
try:
 legacy.main();record['complete']=True
except Exception as e:
 record['failure']=repr(e);raise
finally:
 subprocess.run=original_run
 snapshot.verify(project);record['snapshot_unchanged']=focus.sha(project/snapshot.MARKER)==record['snapshot_sha256']
 record['logs']={str(p):focus.sha(p) for p in [output.with_suffix('.godot.log'),output.with_suffix('.xvfb.log')] if p.exists()}
 output.with_suffix('.diagnostic.json').write_text(json.dumps(record,indent=2)+'\n')
