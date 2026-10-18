import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
sys.path.insert(0,str(ROOT/'tools/graphics-six'))
import snapshot
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def main():
    base=Path('/tmp/yuga-desktop-recovery-r1/current-project')
    engine=Path('/opt/godot/4.6.3/Godot_v4.6.3-stable_linux.x86_64')
    output=HERE/'native-bind-r1';assert not output.exists();output.mkdir()
    before=snapshot.verify(base)
    env=dict(os.environ)
    env.update({key:'1' for key in ['LP_NUM_THREADS','OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']})
    env.update(YUGA_SHOULDER_BIND_OUTPUT=str(output),XDG_DATA_HOME=str(output/'xdg-data'),XDG_CONFIG_HOME=str(output/'xdg-config'),XDG_CACHE_HOME=str(output/'xdg-cache'))
    command=['taskset','-c','4','timeout','15s',str(engine),'--headless','--path',str(base),'--audio-driver','Dummy','--script',str(HERE/'bind_probe.gd'),'--log-file',str(output/'godot.log')]
    pins={str(p):sha(p) for p in [engine,HERE/'bind_probe.gd',Path(__file__),base/snapshot.MARKER]}
    start=time.monotonic()
    with (output/'console.log').open('wb') as log:run=subprocess.run(command,env=env,stdout=log,stderr=subprocess.STDOUT)
    after=snapshot.verify(base)
    result={'command':command,'exit_code':run.returncode,'elapsed_s':time.monotonic()-start,'source_pins':pins,'base_and_store_exact':before==after,'base_files':len(before['files']),'passed':run.returncode==0 and before==after}
    if (output/'bind.json').exists():result['bind_sha256']=sha(output/'bind.json')
    else:result['passed']=False
    (output/'run.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
    sys.exit(0 if result['passed'] else 1)
if __name__=='__main__':main()
