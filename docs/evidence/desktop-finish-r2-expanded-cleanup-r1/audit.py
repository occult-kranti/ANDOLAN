"""Read-only fixed r2 expanded-package duplicate audit; never removes files."""
from pathlib import Path
import datetime, hashlib, json, os, stat, subprocess, zipfile
REPO = Path('/workspace/ANDOLAN')
BASE = Path('/tmp/yuga-desktop-integrated-package-r2')
OUT = Path(__file__).resolve().parent
ROOTS = (BASE/'build/yuga-native-linux-x86_64', BASE/'build/yuga-native-windows-x86_64', BASE/'extracted/yuga-native-linux-x86_64')
EXPECTED = {'yuga-native-linux-x86_64.zip':'88948751cde928ba17cc38f95b7f07bd056707b4b08bb7afd460f500d3e306a0','yuga-native-windows-x86_64.zip':'4c50c10020c0fb5c6c1d27f7ee295da177fe5ea092b44fcf4bb071c2101dfc7e'}
SOURCE='5542e61610d20e591effbed9dec15fd10398e31d'
def sha_stream(f):
 h=hashlib.sha256()
 for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
 return h.hexdigest()
def pin(p):
 with p.open('rb') as f:h=sha_stream(f)
 return {'bytes':p.stat().st_size,'sha256':h}
def safe(p):
 assert p.is_absolute() and p.resolve()==p and not p.is_symlink(),p
 for part in (p,*p.parents):assert not part.is_symlink(),part
 return p

def process_observation():
 holders=[];inaccessible=[];observed=[];ancestors=set();pid=os.getpid()
 while pid>1:
  ancestors.add(pid)
  try:pid=int((Path('/proc')/str(pid)/'stat').read_text().rsplit(')',1)[1].split()[1])
  except (OSError,ValueError):break
 for proc in Path('/proc').iterdir():
  if not proc.name.isdigit():continue
  try:
   status=(proc/'status').read_text();uid=int(next(x for x in status.splitlines() if x.startswith('Uid:')).split()[1])
   if '\nState:\tZ' in status:continue
  except (OSError,StopIteration):continue
  pid=int(proc.name)
  if uid!=os.getuid():continue
  observed.append(pid)
  def referenced(value):return any(value==str(r) or value.startswith(str(r)+'/') for r in ROOTS)
  for kind in ['cwd','exe']:
   try:
    value=os.readlink(proc/kind)
    if referenced(value):holders.append({'pid':pid,'kind':kind,'value':value})
   except PermissionError:inaccessible.append(str(proc/kind))
   except OSError:pass
  try:entries=list((proc/'fd').iterdir())
  except PermissionError:inaccessible.append(str(proc/'fd'));entries=[]
  except OSError:entries=[]
  for entry in entries:
   try:
    value=os.readlink(entry)
    if referenced(value):holders.append({'pid':pid,'kind':'fd','value':value})
   except PermissionError:inaccessible.append(str(entry))
   except OSError:pass
  try:
   for line in (proc/'maps').read_text().splitlines():
    if any(str(r)+'/' in line for r in ROOTS):holders.append({'pid':pid,'kind':'map','value':line})
  except PermissionError:inaccessible.append(str(proc/'maps'))
  except OSError:pass
  if pid not in ancestors:
   try:
    args=(proc/'cmdline').read_bytes().split(b'\0')
    matches=[a.decode(errors='replace') for a in args if any(str(r).encode() in a for r in ROOTS)]
    if matches:holders.append({'pid':pid,'kind':'argv','values':matches})
   except PermissionError:inaccessible.append(str(proc/'cmdline'))
   except OSError:pass
 return {'owned_live_processes':observed,'holders':holders,'inaccessible_owned_entries':inaccessible,'observer_ancestor_argv_excluded':sorted(ancestors),'scope':'Accessible same-UID live process cwd/exe/fd/maps/argv only; explicit W1/W6 owner releases are separate. Not a machine-wide idle proof.'}

def main():
 target=OUT/'recovery-map.json';assert not target.exists()
 archives={};members={};records=[];dirs=[]
 for name,expected in EXPECTED.items():
  p=safe(BASE/'build'/name);record=pin(p);assert record['sha256']==expected
  archives[str(p)]=record
  with zipfile.ZipFile(p) as z:
   infos=z.infolist();assert len(infos)==len({i.filename for i in infos})==34
   members[str(p)]={}
   for i in infos:
    member=Path(i.filename)
    assert not member.is_absolute() and '..' not in member.parts and str(member)==i.filename
    assert stat.S_ISREG(i.external_attr>>16) and not i.is_dir()
    with z.open(i) as f:h=sha_stream(f)
    members[str(p)][i.filename]={'bytes':i.file_size,'sha256':h,'zip_mode':oct(stat.S_IMODE(i.external_attr>>16)),'crc32':format(i.CRC,'08x')}
   inner=json.loads(z.read(name[:-4]+'/PACKAGE-MANIFEST.json'))
   assert inner['git']['head']==SOURCE and inner['git']['native_worktree_status']=='',inner.get('git')
 for root in ROOTS:
  safe(root);assert root.is_dir()
  zpath=str(BASE/'build'/(root.name+'.zip'));seen=[]
  for p in sorted(root.rglob('*')):
   safe(p);s=p.stat()
   if p.is_dir():dirs.append({'root':str(root),'path':str(p.relative_to(root)),'mode':oct(stat.S_IMODE(s.st_mode))});continue
   assert stat.S_ISREG(s.st_mode) and s.st_nlink==1,p
   member=root.name+'/'+p.relative_to(root).as_posix();m=members[zpath][member]
   filepin=pin(p);assert filepin['bytes']==m['bytes'] and filepin['sha256']==m['sha256'],p
   after=p.stat();assert(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)==(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns)
   records.append({'root':str(root),'path':p.relative_to(root).as_posix(),'archive':zpath,'member':member,**filepin,'disk_mode':oct(stat.S_IMODE(s.st_mode)),**{k:v for k,v in m.items() if k not in ('bytes','sha256')},'device':s.st_dev,'inode':s.st_ino,'hardlinks':s.st_nlink,'allocated_bytes':s.st_blocks*512,'mtime_ns':s.st_mtime_ns,'ctime_ns':s.st_ctime_ns})
   seen.append(member)
  assert set(seen)==set(members[zpath])
  dirs.append({'root':str(root),'path':'.','mode':oct(stat.S_IMODE(root.stat().st_mode))})
 processes=process_observation();assert not processes['holders'],processes['holders']
 remote=subprocess.check_output(['git','ls-remote','origin','refs/heads/game/yuga-native-production'],cwd=REPO,text=True).strip();remote_commit=remote.split()[0]
 subprocess.run(['git','merge-base','--is-ancestor',SOURCE,remote_commit],cwd=REPO,check=True)
 spaces={str(p):{'available_bytes':os.statvfs(p).f_bavail*os.statvfs(p).f_frsize,'device':p.stat().st_dev} for p in [Path('/tmp'),Path('/workspace')]}
 result={'schema':1,'status':'prepared_only_no_deletion','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_commit':SOURCE,'recovery_note':'Exact compiled payload bytes come from retained local ZIPs; source5542 provenance alone cannot reconstruct byte-identical PCKs. Restore disk_mode from this map, not ZIP mode. Directories remain. Timestamps are diagnostic metadata, not a promised restoration property.','roots':[str(r) for r in ROOTS],'archives':archives,'files':records,'directories_retained':dirs,'count':len(records),'logical_bytes':sum(r['bytes'] for r in records),'allocated_file_bytes':sum(r['allocated_bytes'] for r in records),'disk_zip_mode_differences':sum(r['disk_mode']!=r['zip_mode'] for r in records),'remote_source':{'branch_observation':remote,'source_is_ancestor':True},'space':spaces,'protected':'All ZIPs/raw PCKs/metadata/logs/users/caches, all r1/r3/current cold/owned clone/R6/unique evidence/art; only listed regular expanded files may later be removed.'}
 target.write_text(json.dumps(result,indent=2)+'\n');(OUT/'process-observation.json').write_text(json.dumps(processes,indent=2)+'\n')
 print(json.dumps({k:result[k] for k in ['count','logical_bytes','allocated_file_bytes','disk_zip_mode_differences','space']},indent=2))
if __name__=='__main__':main()
