import json,os,subprocess,sys,time
from pathlib import Path
out=Path('/workspace/scratch/yuga-desktop-integrated-package-r4');repo=Path('/tmp/yuga-desktop-integrated-package-r1/ANDOLAN');phase=sys.argv[1];assert phase in ['export','package']
receipt=out/(phase+'-execution.json');assert not receipt.exists()
assert json.loads((out/'preparation-receipt.json').read_text())['passed']
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()=='96d5b9cd3114b9732f7dc80433b1ca0a1d4a9b12'
assert os.statvfs('/tmp').f_bavail*os.statvfs('/tmp').f_frsize>=128*1024*1024
command=['taskset','-c','0,1','python3','games/yuga-native/tools/package-native.py','--linux-engine','/opt/godot/4.6.3/Godot_v4.6.3-stable_linux.x86_64','--linux-runtime','/workspace/tooling/godot-public-4.6.3/binaries/godot-4.6.3-public-template-debug-pipeline-low-priority','--linux-runtime-variant','pipeline-low-priority','--linux-runtime-provenance',str(repo/'games/yuga-native/docs/evidence/desktop-finish/G0/template-priority-build-r1/finished-build-verification.json'),'--windows-engine','/workspace/tooling/native-engine/Godot_v4.6.3-stable_win64.exe','--build-dir',str(out/'build'),'--'+phase+'-only']
env=os.environ.copy();overrides={k:str(out/'user'/v) for k,v in [('XDG_DATA_HOME','data'),('XDG_CONFIG_HOME','config'),('XDG_CACHE_HOME','cache')]};overrides.update({'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1'});env.update(overrides)
for v in ['data','config','cache']:(out/'user'/v).mkdir(parents=True,exist_ok=True)
r={'command':command,'cwd':str(repo),'source_commit':'96d5b9cd3114b9732f7dc80433b1ca0a1d4a9b12','started_unix':time.time(),'environment':overrides}
with (out/'logs'/(phase+'.stdout')).open('w') as stdout,(out/'logs'/(phase+'.stderr')).open('w') as stderr:
 try:r['exit_code']=subprocess.run(command,cwd=repo,env=env,stdout=stdout,stderr=stderr,timeout=300).returncode
 except subprocess.TimeoutExpired:r['exit_code']=124;r['timeout']=True
r['finished_unix']=time.time();receipt.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'phase':phase,'exit_code':r['exit_code'],'elapsed_s':r['finished_unix']-r['started_unix']}));sys.exit(r['exit_code'])
