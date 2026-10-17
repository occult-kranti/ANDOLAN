from pathlib import Path
import subprocess,time,json,hashlib,sys
out=Path('/workspace/scratch/rea-reuse-restore-r1')
label=sys.argv[1]; cmd=json.loads(sys.argv[2]); log=out/'logs'/(label+'.log.txt'); start=time.monotonic()
try:
 with log.open('w') as f: p=subprocess.run(cmd,cwd='/workspace/ANDOLAN',stdout=f,stderr=subprocess.STDOUT,timeout=1100)
 code=p.returncode; error=None
except Exception as e: code=None; error=type(e).__name__+': '+str(e)
r={'label':label,'argv':cmd,'exit_code':code,'error':error,'elapsed_seconds':round(time.monotonic()-start,3),'log':str(log),'log_sha256':hashlib.sha256(log.read_bytes()).hexdigest() if log.exists() else None}
(out/(label+'.json')).write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps(r))
if log.exists(): print(log.read_text()[-2500:])
sys.exit(0 if code==0 else 1)

