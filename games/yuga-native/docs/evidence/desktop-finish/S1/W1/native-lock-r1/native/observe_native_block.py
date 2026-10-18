from pathlib import Path
import json,time,subprocess,hashlib,os
scratch=Path('/tmp/yuga-g0-source-research-r1');project='/tmp/yuga-s1-textured-finish-project';log=Path('/tmp/yuga-s1-textured-finish-debug-r1-logs/godot.log');gdb=Path('/workspace/tooling/native-debug/gdb-local');receipt={'schema':1,'scope':'One root-authorized owned-engine read-only native attach; same shader/source. No acceptance timeout extension.','observer_started_unix_s':time.time(),'gdb_wrapper_sha256':hashlib.file_digest(gdb.open('rb'),'sha256').hexdigest()}
def find():
 for p in Path('/proc').iterdir():
  if not p.name.isdigit():continue
  try:
   args=[s.decode() for s in (p/'cmdline').read_bytes().split(b'\0') if s]
   if args and 'godot' in Path(args[0]).name.lower() and project in args:return p,args
  except (FileNotFoundError,PermissionError,ProcessLookupError):pass
 return None
def tasks(p):
 rows=[]
 for t in (p/'task').iterdir():
  row={'tid':int(t.name)}
  for key in ['wchan','syscall','stat']:
   try:row[key]=(t/key).read_text().strip()
   except (FileNotFoundError,PermissionError,ProcessLookupError) as e:row[key]=type(e).__name__
  rows.append(row)
 return rows
found=find();assert found,'Owned engine absent';p,args=found;receipt.update(engine_pid=int(p.name),engine_command=args,first_tasks=tasks(p),clock_ticks_per_s=os.sysconf('SC_CLK_TCK'))
# Determine actual process age from proc starttime and kernel uptime, not a guessed sleep.
def age():
 stat=(p/'stat').read_text();f=stat[stat.rfind(')')+2:].split();return float(Path('/proc/uptime').read_text().split()[0])-int(f[19])/os.sysconf('SC_CLK_TCK')
try:
 while age()<60:time.sleep(min(1,60-age()))
 receipt['attach_gate_unix_s']=time.time();receipt['engine_age_s']=age();receipt['before_tasks']=tasks(p)
 if 'after_initial_draw6' in log.read_text():receipt['result']='Skipped attach: initial draw already completed.'
 else:
  assert (p/'cmdline').read_bytes().split(b'\0')==[x.encode() for x in args]+[b''],'Owned command changed'
  command=[str(gdb),'--batch','-ex','set pagination off','-ex','set print frame-arguments none','-p',p.name,'-ex','info threads','-ex','thread apply all bt 32','-ex','info proc mappings','-ex','detach'];receipt['command']=command;receipt['gdb_started_unix_s']=time.time()
  with (scratch/'textured-native-gdb-r1.log').open('x') as h:r=subprocess.run(command,stdout=h,stderr=subprocess.STDOUT,timeout=20)
  receipt['gdb_exit']=r.returncode;receipt['gdb_finished_unix_s']=time.time();receipt['result']='Backtrace attempted; inspect raw output for actual unwind.';receipt['after_tasks']=tasks(p)
except Exception as e:receipt['failure']=repr(e)
finally:
 receipt['finished_unix_s']=time.time();(scratch/'textured-native-gdb-r1.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({k:v for k,v in receipt.items() if k not in ['first_tasks','before_tasks','after_tasks','engine_command','command']},indent=2))
