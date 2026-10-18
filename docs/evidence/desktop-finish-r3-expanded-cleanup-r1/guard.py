"""Verify the fixed published map; removal requires explicit later lead invocation.
Default mode is read-only apart from a fresh --report. Never removes directories.
"""
from pathlib import Path
import argparse, datetime, hashlib, importlib.util, json, os, stat, subprocess, zipfile
HERE=Path(__file__).resolve().parent
REPO=Path('/workspace/ANDOLAN')
MAP_SHA='bc64c58a83126da779128c6bac31c4c82a4b565f85c1237b87328566567c05f2'
spec=importlib.util.spec_from_file_location('r3_duplicate_audit',HERE/'audit.py')
audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)

def meta(p):
 s=p.lstat()
 assert stat.S_ISREG(s.st_mode) and s.st_nlink==1,p
 return (s.st_dev,s.st_ino,s.st_nlink,s.st_size,s.st_blocks*512,stat.S_IMODE(s.st_mode),s.st_mtime_ns,s.st_ctime_ns)
def expected(r):
 return (r['device'],r['inode'],r['hardlinks'],r['bytes'],r['allocated_bytes'],int(r['disk_mode'],8),r['mtime_ns'],r['ctime_ns'])
def main():
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument('--report',type=Path,required=True)
 ap.add_argument('--remove',action='store_true')
 ap.add_argument('--published-commit')
 a=ap.parse_args();assert not a.report.exists() and not a.report.is_symlink()
 raw=(HERE/'recovery-map.json').read_bytes();assert hashlib.sha256(raw).hexdigest()==MAP_SHA
 m=json.loads(raw);assert m['roots']==[str(p) for p in audit.ROOTS] and m['standalone_paths']==[str(p) for p in audit.TARGET_FILES] and m['count']==len(m['files'])==114
 assert len({(r['root'],r['path']) for r in m['files']})==114
 if a.remove:
  assert a.published_commit and len(a.published_commit)==40
  remote=subprocess.check_output(['git','ls-remote','origin','refs/heads/game/yuga-native-production'],cwd=REPO,text=True).split()[0]
  subprocess.run(['git','merge-base','--is-ancestor',a.published_commit,remote],cwd=REPO,check=True)
  for name in ['recovery-map.json','audit.py','guard.py','ownership.json']:
   p=HERE/name
   assert subprocess.check_output(['git','show',a.published_commit+':'+p.relative_to(REPO).as_posix()],cwd=REPO)==p.read_bytes(),name
  subprocess.run(['git','merge-base','--is-ancestor',m['source_commit'],remote],cwd=REPO,check=True)
 else:assert a.published_commit is None,'published commit is meaningful only for explicit removal'
 for root in audit.ROOTS:
  audit.safe(root)
  actual=set()
  for p in root.rglob('*'):
   audit.safe(p)
   if not p.is_dir():assert stat.S_ISREG(p.lstat().st_mode);actual.add(p.relative_to(root).as_posix())
  assert actual=={r['path'] for r in m['files'] if r['root']==str(root)},root
 for name,pin in m['archives'].items():
  p=audit.safe(Path(name));assert audit.pin(p)==pin
 with_zip={}
 for name in m['archives']:
  with zipfile.ZipFile(name) as z:
   infos=z.infolist();assert len(infos)==len({i.filename for i in infos})==(39 if 'linux' in name else 34)
   with_zip[name]={}
   for i in infos:
    assert stat.S_ISREG(i.external_attr>>16)
    with z.open(i) as f:h=audit.sha_stream(f)
    with_zip[name][i.filename]=(i.file_size,h,oct(stat.S_IMODE(i.external_attr>>16)))
 for r in m['files']:
  root=Path(r['root']);rel=Path(r['path']);assert (str(root) in m['roots'] or str(root/rel) in m['standalone_paths']) and not rel.is_absolute() and '..' not in rel.parts and rel.as_posix()==r['path']
  p=audit.safe(root/rel);assert meta(p)==expected(r)
  assert audit.pin(p)=={'bytes':r['bytes'],'sha256':r['sha256']}
  assert with_zip[r['archive']][r['member']]==(r['bytes'],r['sha256'],r['zip_mode'])
 for r in m['directories_retained']:
  p=audit.safe(Path(r['root'])/r['path']);assert p.is_dir() and stat.S_IMODE(p.stat().st_mode)==int(r['mode'],8)
 processes=audit.process_observation();assert not processes['holders'] and not processes['inaccessible_owned_entries'],processes
 before=os.statvfs('/tmp');removed=[]
 if a.remove:
  for r in m['files']:
   p=audit.safe(Path(r['root'])/r['path']);assert meta(p)==expected(r);p.unlink();removed.append(str(p))
  assert all(not (Path(r['root'])/r['path']).exists() for r in m['files'])
 after=os.statvfs('/tmp')
 result={'schema':1,'status':'removed_exact_files' if a.remove else 'verified_only_no_deletion','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'map_sha256':MAP_SHA,'published_commit':a.published_commit,'verified_files':114,'removed_files':len(removed),'removed_paths':removed,'logical_bytes':m['logical_bytes'],'allocated_file_bytes':m['allocated_file_bytes'],'process_observation':processes,'tmp_available_before':before.f_bavail*before.f_frsize,'tmp_available_after':after.f_bavail*after.f_frsize,'scope':'Only114 mapped regular files:3r3 expansions plus2 explicit Windows rawPCKs; all directories, archives, LinuxrawPCKs, unrelated build siblings, unique metadata/logs/users/cache and other roots retained. Concurrent writes can affect free-space delta.'}
 a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({k:result[k] for k in ['status','verified_files','removed_files','logical_bytes','allocated_file_bytes']}))
if __name__=='__main__':main()
