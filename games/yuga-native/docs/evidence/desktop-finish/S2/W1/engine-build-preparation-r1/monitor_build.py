from pathlib import Path
import subprocess,os,time,signal,shutil,json,resource
base=Path('/tmp/yuga-engine-source-baseline-r1');source=base/'godot-35e80b3a8822a9df9be390814b62f44c0a9c69e8';receipt=base/'receipts';floor=3*1024**3;limit=7200
command=['python3','-m','SCons','-j2','platform=linuxbsd','target=editor','dev_build=no','debug_symbols=no','lto=none','use_sowrap=yes']
env=os.environ.copy();env['PYTHONPATH']=str(base/'scons');env['PATH']='/workspace/tooling/wayland-scanner-local/root/usr/bin:'+env['PATH'];env.update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
assert shutil.which('wayland-scanner',path=env['PATH'])
assert sorted(os.sched_getaffinity(0))==[0,1]
def tree_pids(pid):
 result=[pid]
 try:
  children=Path(f'/proc/{pid}/task/{pid}/children').read_text().split()
  for child in children:result.extend(tree_pids(int(child)))
 except (FileNotFoundError,ProcessLookupError):pass
 return result
def rss(pid):
 try:return int(Path(f'/proc/{pid}/statm').read_text().split()[1])*os.sysconf('SC_PAGE_SIZE')
 except (FileNotFoundError,ProcessLookupError):return 0
record={'source':str(source),'command':command,'source_patches':0,'affinity':sorted(os.sched_getaffinity(0)),'compiler_jobs':2,'disk_floor_bytes':floor,'overall_deadline_seconds':limit,'started_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'samples':[],'completed':False}
started=time.monotonic();failure=None;last_print=-60
with (receipt/'build.log').open('x') as log:
 p=subprocess.Popen(command,cwd=source,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True);record['pid']=p.pid
 try:
  while p.poll() is None:
   age=time.monotonic()-started;free=shutil.disk_usage('/tmp').free;pids=tree_pids(p.pid)
   s={'elapsed_s':age,'free_tmp_bytes':free,'processes':len(pids),'sampled_tree_rss_bytes':sum(rss(i) for i in pids),'log_bytes':(receipt/'build.log').stat().st_size};record['samples'].append(s)
   if free<floor:failure='Free scratch below declared3GiB floor';break
   if age>limit:failure='Declared2hour build deadline reached';break
   if age-last_print>=60:
    print(json.dumps(s),flush=True);last_print=age
   record['status']='building';(receipt/'build-progress.json').write_text(json.dumps(record,indent=2)+'\n');time.sleep(5)
 finally:
  if p.poll() is None:
   os.killpg(p.pid,signal.SIGTERM)
   try:p.wait(timeout=10)
   except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
record.update(status='complete' if p.returncode==0 and failure is None else 'stopped',completed=p.returncode==0 and failure is None,exit_code=p.returncode,failure=failure,elapsed_s=time.monotonic()-started,child_rusage_maxrss_kib=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,ended_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()))
record['maximum_sampled_tree_rss_bytes']=max((s['sampled_tree_rss_bytes'] for s in record['samples']),default=0);record['minimum_sampled_free_tmp_bytes']=min((s['free_tmp_bytes'] for s in record['samples']),default=0)
(receipt/'build-progress.json').write_text(json.dumps(record,indent=2)+'\n');(receipt/'build-result.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({k:v for k,v in record.items() if k!='samples'}),flush=True)
raise SystemExit(0 if record['completed'] else 1)
