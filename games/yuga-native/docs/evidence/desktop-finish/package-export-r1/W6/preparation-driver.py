import hashlib,json,os,re,shutil,subprocess,time
from pathlib import Path
SOURCE=Path('/workspace/ANDOLAN'); ROOT=Path('/tmp/yuga-desktop-integrated-package-r1'); COMMIT='b4d2871723a8cb66354d66abb17bd56fbd22c598'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
 return h.hexdigest()
def cmd(*a,cwd=SOURCE): return subprocess.check_output(a,cwd=cwd).decode().strip()
def write(p,x): p.write_text(json.dumps(x,indent=2)+'\n')
def record(p): return {'bytes':p.stat().st_size,'sha256':sha(p)}
assert not ROOT.exists()
entries=[]
for entry in subprocess.check_output(['git','ls-tree','-rlz',COMMIT],cwd=SOURCE).split(b'\0'):
 if not entry: continue
 meta,path=entry.split(b'\t',1); mode,typ,oid,size=meta.decode().split()
 assert typ=='blob'
 entries.append({'path':path.decode(),'mode':mode,'git_blob':oid,'bytes':int(size)})
free=shutil.disk_usage('/tmp').free; total=sum(x['bytes'] for x in entries)
assert free>total+int(2.25*1024**3)+1024**2,(free,total)
ROOT.mkdir(); (ROOT/'logs').mkdir(); (ROOT/'build').mkdir()
write(ROOT/'tracked-source-inventory.json',{'commit':COMMIT,'files':entries,'bytes':total})
receipt={'commit':COMMIT,'started_unix':time.time(),'free_bytes_before':free,'tracked_bytes':total,'source_inventory_sha256':sha(ROOT/'tracked-source-inventory.json'),'cache_copy_scope':'Only imported payloads/MD5s, global class cache, UID cache and .gdignore; no shader seed, editor state or prior exported packs.'}
try:
 for name,path,expected in [('linux','/opt/godot/4.6.3/Godot_v4.6.3-stable_linux.x86_64','f64d4ed19fc9df9440321653fcc80df8c6e365ba7b6de0a29e2cfa9fa71bfeb3'),('windows','/workspace/tooling/native-engine/Godot_v4.6.3-stable_win64.exe','ef90e929ba1a6a4322860285d97f40f4aa349c90329a91b0e8b55b8df0f4cb00')]:
  receipt[name+'_engine']={'path':path,**record(Path(path))}; assert receipt[name+'_engine']['sha256']==expected
 with (ROOT/'logs/clone.log').open('w') as log:
  subprocess.run(['git','clone','--shared','--no-checkout',str(SOURCE),str(ROOT/'ANDOLAN')],check=True,stdout=log,stderr=subprocess.STDOUT)
  subprocess.run(['git','checkout','--detach',COMMIT],cwd=ROOT/'ANDOLAN',check=True,stdout=log,stderr=subprocess.STDOUT)
 assert cmd('git','rev-parse','HEAD',cwd=ROOT/'ANDOLAN')==COMMIT
 status=cmd('git','status','--porcelain=v1',cwd=ROOT/'ANDOLAN'); (ROOT/'source-initial-status.txt').write_text(status); assert not status
 canonical=SOURCE/'games/yuga-native'; project=ROOT/'ANDOLAN/games/yuga-native'
 runtime={}
 for folder in ['scripts','shaders','scenes','assets']:
  for p in sorted((project/folder).rglob('*')):
   if p.is_file():
    relative=str(p.relative_to(project)); runtime[relative]=record(p)
    assert record(canonical/relative)==runtime[relative],relative
 for relative in ['project.godot','export_presets.cfg']:
  runtime[relative]=record(project/relative); assert record(canonical/relative)==runtime[relative]
 write(ROOT/'runtime-source-before.json',runtime)
 mapping=[]
 for desc in sorted((project/'assets').rglob('*.import')):
  txt=desc.read_text(); rel=str(desc.relative_to(project)); raw=re.search(r'^source_file="res://([^"]+)"',txt,re.M).group(1)
  destinations=re.findall(r'"res://([^"]+)"',re.search(r'^dest_files=\[(.*?)\]',txt,re.M).group(1))
  assert raw in runtime and rel in runtime
  row={'descriptor':rel,'descriptor_sha256':sha(desc),'raw':raw,'raw_sha256':sha(project/raw),'destinations':[]}
  for d in destinations:
   assert d.startswith('.godot/imported/'); p=canonical/d; assert p.is_file(),d
   md5=p.with_suffix('.md5'); assert md5.is_file(),str(md5)
   md5text=md5.read_text(); expected=re.search(r'^source_md5="([a-f0-9]+)"',md5text,re.M).group(1)
   actual=hashlib.md5((project/raw).read_bytes()).hexdigest(); assert actual==expected,raw
   row['destinations'].append({'path':d,**record(p),'md5_file':str(md5.relative_to(canonical)),'md5_sha256':sha(md5),'raw_md5':actual})
  mapping.append(row)
 cache=canonical/'.godot'; selected=sorted(p for p in (cache/'imported').rglob('*') if p.is_file())+[cache/name for name in ['global_script_class_cache.cfg','uid_cache.bin','.gdignore'] if (cache/name).exists()]
 cachepins={str(p.relative_to(cache)):record(p) for p in selected}
 for relative,rec in cachepins.items():
  a=cache/relative; b=project/'.godot'/relative
  assert not a.is_symlink(); b.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(a,b)
  assert record(b)==rec and record(a)==rec,relative
  assert (a.stat().st_dev,a.stat().st_ino)!=(b.stat().st_dev,b.stat().st_ino),relative
 assert not cmd('git','status','--porcelain=v1',cwd=ROOT/'ANDOLAN')
 write(ROOT/'cache-copy-manifest.json',{'canonical_cache':str(cache),'copied_cache':str(project/'.godot'),'files':cachepins,'imports':mapping,'all_raw_md5_match':True,'all_copied_bytes_match':True,'independent_inodes':True})
 receipt.update({'complete':True,'cache_files':len(cachepins),'import_mappings':len(mapping),'runtime_files':len(runtime),'runtime_inventory_sha256':sha(ROOT/'runtime-source-before.json'),'cache_manifest_sha256':sha(ROOT/'cache-copy-manifest.json')})
except Exception as e:
 receipt.update({'complete':False,'failure':repr(e)}); raise
finally:
 receipt.update({'finished_unix':time.time(),'free_bytes_after':shutil.disk_usage('/tmp').free}); write(ROOT/'preparation-receipt.json',receipt); print(json.dumps(receipt,indent=2))
