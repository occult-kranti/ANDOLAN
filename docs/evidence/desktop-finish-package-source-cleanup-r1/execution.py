from pathlib import Path
import os,hashlib,json,subprocess,stat,datetime
repo=Path('/workspace/ANDOLAN');rel='docs/evidence/desktop-finish-package-source-cleanup-r1/recovery-map.json';p=repo/rel;raw=p.read_bytes();assert hashlib.sha256(raw).hexdigest()=='fd3ad43d21c0bc118de05961edc438fbe4d75515c1cf6a18908571a4381a1f07'
d=json.loads(raw);root=Path(d['clone']);head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip();assert head=='f8dec5fa4f9bbd2d20c58f6102fb984d0b19a9f1';remote=subprocess.check_output(['git','ls-remote','origin','refs/heads/game/yuga-native-production'],cwd=repo,text=True).split()[0];assert head==remote;assert subprocess.check_output(['git','show',head+':'+rel],cwd=repo)==raw;assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()==head
holders=[];inaccessible=[]
for proc in Path('/proc').iterdir():
 if not proc.name.isdigit():continue
 for entry in [proc/'cwd',*(proc/'fd').glob('*')]:
  try:value=os.readlink(entry)
  except PermissionError:inaccessible.append(str(entry));continue
  except OSError:continue
  if value==str(root) or value.startswith(str(root)+'/'):holders.append((str(entry),value))
 try:
  for line in (proc/'maps').read_text().splitlines():
   if str(root)+'/' in line:holders.append((str(proc/'maps'),line))
 except PermissionError:inaccessible.append(str(proc/'maps'))
 except OSError:pass
assert not holders,holders
unique={f['git_blob']:f['size'] for f in d['files']};checked=subprocess.run(['git','cat-file','--batch-check'],input='\n'.join(unique)+'\n',cwd=repo,text=True,capture_output=True,check=True)
assert len(checked.stdout.splitlines())==len(unique)
for line in checked.stdout.splitlines():
 oid,kind,size=line.split();assert kind=='blob' and int(size)==unique[oid]
for f in d['files']:
 q=root/f['path'];assert q.is_relative_to(root) and q.resolve()==q and not q.is_symlink();s=q.stat();assert stat.S_ISREG(s.st_mode);assert(s.st_dev,s.st_ino,s.st_nlink,s.st_size,s.st_blocks*512,stat.S_IMODE(s.st_mode))==(f['device'],f['inode'],f['hardlinks'],f['size'],f['allocated_bytes'],int(f['mode'],8));h=hashlib.sha256();blob=hashlib.sha1(('blob '+str(s.st_size)+'\0').encode())
 with q.open('rb') as stream:
  for block in iter(lambda:stream.read(1024*1024),b''):h.update(block);blob.update(block)
 assert h.hexdigest()==f['sha256'] and blob.hexdigest()==f['git_blob'],q
before=os.statvfs('/tmp');deleted=[]
for f in d['files']:
 q=root/f['path'];s=q.lstat();assert(s.st_dev,s.st_ino,s.st_nlink,s.st_size)==(f['device'],f['inode'],1,f['size']);q.unlink();deleted.append(f['path'])
assert all(not (root/f['path']).exists() for f in d['files']);after=os.statvfs('/tmp')
out={'schema':1,'status':'completed','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'recovery_map_commit':head,'recovery_source_commit':d['commit'],'recovery_map_sha256':hashlib.sha256(raw).hexdigest(),'clone_head':head,'removed_files':len(deleted),'logical_bytes':sum(f['size'] for f in d['files']),'allocated_file_bytes_reclaimed':sum(f['allocated_bytes'] for f in d['files']),'process_holders':holders,'inaccessible_process_entries':inaccessible,'process_limit':'Only accessible process entries were inspected; W1 and W6 explicitly released this exact historical scope after their source audits. This is not a complete machine-wide idle proof.','owner_release':'W6 completed exact f8dec export/package plus16,982 tracked and552 runtime unchanged audit; W1 confirms wrapper uses runtime/manifests/ZIP, no mapped historical source dependency. Root approved exact published map.','all_recovery_blobs_present':True,'all_selected_bytes_and_metadata_reverified':True,'tmp_available_before':before.f_bavail*before.f_frsize,'tmp_available_after':after.f_bavail*after.f_frsize,'measurement_limit':'Concurrent workers write other paths; free-space delta is not separately attributable.','preserved':'Runtime/config/import caches/.git/115generatedUID metadata, unique files, all build/extraction/cache/original/log/output roots and canonical source.','recovery':'Restore each exact git_blob and mode from published recovery-map.json before running source-dependent operations in this intentionally partial checkout.'}
(p.parent/'execution-receipt.json').write_text(json.dumps(out,indent=2)+'\n');(root.parent/'HISTORICAL-SOURCE-PARTIAL.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k!='inaccessible_process_entries'},indent=2))
