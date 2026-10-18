import os,sys,subprocess,time,pathlib,json,hashlib
p=pathlib.Path(__file__).parent;branch=sys.argv[1]
engine='/opt/godot/4.6.3/Godot_v4.6.3-stable_linux.x86_64'
cmd=['taskset','-c','4',engine,'--headless','--path','/workspace/ANDOLAN/games/yuga-native','--script',str(p/'cases.gd'),'--','--branch='+branch]
env=os.environ.copy();env.update(LP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',XDG_DATA_HOME=str(p/(branch+'-data')),XDG_CONFIG_HOME=str(p/(branch+'-config')),XDG_CACHE_HOME=str(p/(branch+'-cache')))
t=time.monotonic()
with (p/(branch+'.log')).open('wb') as out:r=subprocess.run(cmd,env=env,stdout=out,stderr=subprocess.STDOUT,timeout=25)
log=(p/(branch+'.log')).read_text();receipt={'command':cmd,'exit_code':r.returncode,'elapsed_seconds':time.monotonic()-t,'fixture_sha256':hashlib.sha256((p/'cases.gd').read_bytes()).hexdigest(),'engine_sha256':hashlib.sha256(pathlib.Path(engine).read_bytes()).hexdigest(),'engine_log_clean':not any(s in log for s in ['SCRIPT ERROR:','ERROR:','WARNING:'])}
(p/(branch+'-run.json')).write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt));print(log)
