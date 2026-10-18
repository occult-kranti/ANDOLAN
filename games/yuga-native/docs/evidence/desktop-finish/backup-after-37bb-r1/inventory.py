"""Prepare an exact unique-file backup list; never stage, write Git objects or alter sources."""
from pathlib import Path
import collections
import hashlib
import json
import os
import stat
import subprocess

OUT=Path(__file__).resolve().parent
REPO=Path('/workspace/ANDOLAN')
NATIVE=REPO/'games/yuga-native'
HEAD='37bb953503a1a374f7c0c6aae1ef3d43cfba8867'

def git(*args):return subprocess.check_output(['git','--no-optional-locks',*args],cwd=REPO)
def save(name,value):(OUT/name).write_text(json.dumps(value,indent=2)+'\n')
def generated(path):
 p=Path(path);return p.suffix in ('.uid','.pyc')or bool(set(p.parts)&{'__pycache__','.godot','XDG','xdg','user','user-data','user-cache'})or 'candidate-import-cache' in p.name
def category(path):
 p=Path(path)
 if p.name=='isolated-user-files.tar.gz':return 'sealed controlled experiment state/cache archive'
 if p.suffix=='.blend':return 'editable Blender source'
 if p.suffix=='.glb':return 'distinct authored GLB'
 if p.suffix=='.png':return 'AI-generated concept reference PNG' if '/hair-sculpt-design/concept-r1/' in str(path) else 'actual original PNG'
 if 'semantic' in p.name and p.name.endswith('.tar.gz'):return 'lossless imported semantic proof archive'
 if p.suffix=='.gz':return 'compressed source/pose audit'
 if p.suffix=='.json':return 'receipt/diagnostic JSON'
 return 'source/docs/logs/other'

def main():
 assert git('rev-parse','HEAD').decode().strip()==HEAD
 config=json.loads((OUT/'scope.json').read_text());tree={};byblob=collections.defaultdict(list)
 for raw in git('ls-tree','-r','-l','-z',HEAD).split(b'\0'):
  if not raw:continue
  meta,path=raw.split(b'\t',1);mode,kind,blob,size=meta.decode().split();path=path.decode()
  if kind=='blob':tree[path]=dict(mode=mode,git_blob=blob,bytes=int(size));byblob[blob].append(path)
 untracked={p.decode()for p in git('ls-files','--others','--exclude-standard','-z').split(b'\0')if p}
 oldmap_path=NATIVE/'docs/evidence/desktop-finish/backup-after-96d5-r1/inventory-and-recovery.json'
 olddoc=json.loads(oldmap_path.read_text());oldmap={x['path']:x for x in olddoc['files']+olddoc['historical_exclusions']}
 chosen=set(config['files']);symlinks=[]
 for prefix in config['prefixes']:
  root=REPO/prefix;assert root.is_dir(),prefix
  for parent,dirs,files in os.walk(root,followlinks=False):
   dirs[:]=[x for x in dirs if not(Path(parent)/x).is_symlink()]
   for name in files:
    p=Path(parent)/name
    if p.is_symlink():symlinks.append(str(p.relative_to(REPO)))
    else:chosen.add(str(p.relative_to(REPO)))
 cache={}
 def record(path):
  path=Path(path)
  if path in cache:return cache[path]
  before=path.lstat();assert stat.S_ISREG(before.st_mode),str(path)
  a=hashlib.sha256();b=hashlib.sha1();b.update(('blob '+str(before.st_size)+'\0').encode())
  with path.open('rb')as stream:
   for chunk in iter(lambda:stream.read(1024*1024),b''):a.update(chunk);b.update(chunk)
  after=path.lstat();assert(before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)==(after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns),str(path)
  v=dict(path=str(path.relative_to(REPO))if path.is_relative_to(REPO)else str(path),bytes=before.st_size,sha256=a.hexdigest(),git_blob=b.hexdigest(),mode=oct(stat.S_IMODE(before.st_mode)),git_mode='100755'if before.st_mode&0o111 else'100644',category=category(str(path)))
  cache[path]=v;return v
 rows=[];selected=[];newblob={};excluded=[]
 for rel in sorted(chosen):
  p=REPO/rel
  if not p.exists():raise FileNotFoundError(rel)
  if generated(rel):
   excluded.append(dict(path=rel,bytes=p.lstat().st_size,reason='generated UID/cache/user data or recoverable compiled import cache; not selected'));continue
  r=record(p).copy();r['ignored_but_explicit_frozen_artifact']=rel not in untracked and rel not in tree
  if r['git_blob']in byblob:
   src=rel if rel in tree and tree[rel]['git_blob']==r['git_blob']else sorted(byblob[r['git_blob']])[0]
   r['recovery']=dict(kind='already_in_head'if src==rel else'recover_from_head_blob',commit=HEAD,source=src,git_blob=r['git_blob'],source_git_mode=tree[src]['mode'])
  elif rel in tree and rel not in config.get('tracked_files_authorized',[]):
   r['recovery']=dict(kind='tracked_working_change_hold',reason='Not an untracked new file; coordinator must separately approve tracked edits')
  elif r['git_blob']in newblob:r['recovery']=dict(kind='recover_from_selected_file',source=newblob[r['git_blob']],git_blob=r['git_blob'])
  else:
   r['recovery']=dict(kind='include_new_file');newblob[r['git_blob']]=rel;selected.append(r)
  rows.append(r)
 historical=[];outside=[]
 for rel in sorted(untracked-chosen):
  p=REPO/rel
  if generated(rel):outside.append(dict(path=rel,reason='generated UID/cache excluded'));continue
  if rel in oldmap:
   prior=oldmap[rel];r={k:v for k,v in prior.items() if k!='recovery'}
   r['verification_scope']='Archived Backup A identity plus current37bb Git object availability; no repeated old working-file hash'
   if prior['recovery']['kind']=='excluded_generated_cache':r['recovery']=prior['recovery']
   elif r['git_blob']in byblob:
    src=sorted(byblob[r['git_blob']])[0];r['recovery']=dict(kind='historical_duplicate_covered_by_37bb_or_ancestor',commit=HEAD,git_blob=r['git_blob'],source=src,prior_recovery=prior['recovery'])
   elif prior['recovery']['kind'] in ('gzip_exact_raw','historical_lossless_gzip_mapping'):
    gzip_map=prior['recovery']
    while gzip_map['kind']=='historical_lossless_gzip_mapping':gzip_map=gzip_map['prior_recovery']
    assert gzip_map['kind']=='gzip_exact_raw'
    r['recovery']=dict(kind='historical_lossless_gzip_mapping',prior_recovery=gzip_map)
   else:r['recovery']=dict(kind='historical_mapping_requires_manual_resolution',prior_recovery=prior['recovery'])
   historical.append(r)
  else:outside.append(dict(path=rel,reason='Outside explicitly frozen scope or active/unrelated work; not selected'))
 # Verify explicit artifact tables without changing their sealed receipts.
 closure=[];external=[];mismatches=[]
 receipts=sorted(p for p in (REPO/x for x in chosen)if p.suffix=='.json'and('receipt' in p.name or p.name=='artifact-manifest.json')and not generated(str(p)))
 for receipt in receipts:
  try:doc=json.loads(receipt.read_text())
  except (UnicodeError,json.JSONDecodeError):continue
  for key in ('artifacts','files'):
   table=doc.get(key)
   entries=table.items()if isinstance(table,dict)else((x.get('path'),x)for x in table if isinstance(x,dict))if isinstance(table,list)else[]
   for name,pin in entries:
    if isinstance(pin,str)and len(pin)==64:pin={'sha256':pin}
    if not isinstance(name,str)or not isinstance(pin,dict)or not isinstance(pin.get('sha256'),str):continue
    alias=next((x for x in config.get('historical_receipt_path_aliases',[]) if x['receipt']==str(receipt.relative_to(REPO)) and x['entry']==name),None)
    if alias:assert pin['sha256']==alias['expected_sha256']
    q=Path(name);options=[REPO/alias['retained_path']]if alias else([q]if q.is_absolute()else[receipt.parent/q,NATIVE/q,REPO/q])
    target=next((x for x in options if x.is_file()and not x.is_symlink()),None)
    base=dict(receipt=str(receipt.relative_to(REPO)),entry=name,expected_sha256=pin['sha256'])
    if target is None or not target.is_relative_to(REPO):external.append(dict(**base,resolved_path=str(target)if target else None,scope='external/missing declared reference; not copied or qualified by this inventory'));continue
    actual=record(target);okay=actual['sha256']==pin['sha256']and('bytes'not in pin or actual['bytes']==pin['bytes'])
    item=dict(**base,path=str(target.relative_to(REPO)),passed=okay,generated_excluded=generated(str(target)),actual_sha256=actual['sha256'],historical_recovery=alias)
    closure.append(item)
    if not okay:mismatches.append(item)
 save('inventory-and-recovery.json',dict(head=HEAD,files=rows,historical_exclusions=historical,generated_exclusions=excluded,outside_scope=outside,symlinks_excluded=symlinks))
 save('receipt-closure.json',dict(checked=len(closure),passed=len(closure)-len(mismatches),mismatches=mismatches,checks=closure,external_or_missing=external))
 assert not mismatches,'Sealed receipt mismatch; do not stage'
 save('allowlist.json',dict(status='proposed_unique_untracked_backup_only_not_staged',head=HEAD,files=selected,count=len(selected),logical_bytes=sum(x['bytes']for x in selected)))
 (OUT/'allowlist.paths0').write_bytes(b''.join(x['path'].encode()+b'\0'for x in selected));(OUT/'allowlist.paths').write_text(''.join(x['path']+'\n'for x in selected))
 cats=collections.defaultdict(lambda:dict(files=0,bytes=0));prefixes={}
 for r in selected:cats[r['category']]['files']+=1;cats[r['category']]['bytes']+=r['bytes']
 for p in config['prefixes']:
  hits=[x for x in selected if x['path'].startswith(p+'/')];prefixes[p]=dict(files=len(hits),bytes=sum(x['bytes']for x in hits))
 summary=dict(head=HEAD,selected_files=len(selected),selected_bytes=sum(x['bytes']for x in selected),categories=dict(cats),prefixes=prefixes,individual_files=[x for x in selected if x['path']in config['files']],over_95_MiB=[x for x in selected if x['bytes']>95*1024*1024],scope_files=len(rows),recovery_kinds=dict(collections.Counter(x['recovery']['kind']for x in rows)),historical_exclusions=len(historical),historical_unresolved=[x for x in historical if x['recovery']['kind']=='historical_mapping_requires_manual_resolution'],generated_exclusions=len(excluded),outside_scope=len(outside),receipt_entries_checked=len(closure),external_or_missing_receipt_entries=len(external))
 save('summary.json',summary)
 assert git('rev-parse','HEAD').decode().strip()==HEAD
 before=json.loads((OUT/'git-before.json').read_text());index=REPO/'.git/index';after=dict(head=HEAD,index_sha256=hashlib.sha256(index.read_bytes()).hexdigest(),index_lock_exists=(REPO/'.git/index.lock').exists());save('git-after.json',after);assert before==after,'Git state changed; coordinate owner before freeze'
 print(json.dumps({k:v for k,v in summary.items()if k not in('prefixes','individual_files')},indent=2))

if __name__=='__main__':main()
