"""Owned-checkout r3 preparation; preserve all prior outputs and exact UID metadata."""
import hashlib,json,shutil,subprocess,time
from pathlib import Path
repo=Path('/tmp/yuga-desktop-integrated-package-r1/ANDOLAN'); project=repo/'games/yuga-native'
out=Path('/tmp/yuga-desktop-integrated-package-r3'); commit='f8dec5fa4f9bbd2d20c58f6102fb984d0b19a9f1'; prior='5542e61610d20e591effbed9dec15fd10398e31d'
def cmd(*args):return subprocess.check_output(args,cwd=repo).decode().strip()
def rec(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return {'bytes':path.stat().st_size,'sha256':h.hexdigest()}
def write(path,value):path.write_text(json.dumps(value,indent=2)+'\n')
assert not out.exists();assert cmd('git','rev-parse','HEAD')==prior;assert not cmd('git','status','--porcelain=v1')
assert not cmd('git','diff','--name-only','HEAD');subprocess.run(['git','cat-file','-e',commit+'^{commit}'],cwd=repo,check=True)
for process in Path('/proc').iterdir():
 if not process.name.isdigit():continue
 try:exe=(process/'exe').resolve().name.lower();cwd=(process/'cwd').resolve();argv=(process/'cmdline').read_bytes()
 except (OSError,RuntimeError):continue
 assert not (cwd.is_relative_to(repo) and ('godot' in exe or b'package-native.py' in argv)),process.name
prior_outputs={}
for attempt in ['r1','r2']:
 previous=Path('/tmp/yuga-desktop-integrated-package-'+attempt)
 prior_outputs[attempt]={str(f.relative_to(previous)):rec(f) for directory in ['build','logs'] for f in sorted((previous/directory).rglob('*')) if f.is_file()}
audit=json.loads((repo.parent/'uid-generation-audit.json').read_text());assert len(audit['new_files'])==115
for row in audit['new_files']:assert rec(repo/row['path'])=={k:row[k] for k in ['bytes','sha256']}
exclude=repo/'.git/info/exclude';previous_exclude=Path('/tmp/yuga-desktop-integrated-package-r2/git-info-exclude.txt');assert exclude.read_bytes()==previous_exclude.read_bytes()
paths=(project/'docs/evidence/desktop-finish/package-export-r1/W6/approved-generated-metadata-exclusions.txt').read_text().splitlines();assert len(paths)==113
assert all(x.startswith(('/games/yuga-native/tests/','/games/yuga-native/tools/')) and x.endswith('.gd.uid') and not any(c in x for c in '*?[]') for x in paths)
out.mkdir();(out/'build').mkdir();(out/'logs').mkdir();shutil.copy2(exclude,out/'git-info-exclude.txt')
with (out/'logs/checkout.log').open('w') as f:subprocess.run(['git','checkout','--detach',commit],cwd=repo,stdout=f,stderr=subprocess.STDOUT,check=True)
assert cmd('git','rev-parse','HEAD')==commit;assert not cmd('git','status','--porcelain=v1');assert exclude.read_bytes()==previous_exclude.read_bytes()
tracked={raw:rec(repo/raw) for raw in subprocess.check_output(['git','ls-files','-z'],cwd=repo).decode().split('\0') if raw};write(out/'tracked-source-before.json',tracked)
runtime={str(f.relative_to(project)):rec(f) for folder in ['scripts','shaders','scenes','assets'] for f in sorted((project/folder).rglob('*')) if f.is_file()}
for name in ['project.godot','export_presets.cfg']:runtime[name]=rec(project/name)
oldruntime=json.loads(Path('/tmp/yuga-desktop-integrated-package-r2/runtime-source-before.json').read_text());assert runtime==oldruntime
write(out/'runtime-source-before.json',runtime)
cache={str(f.relative_to(project/'.godot')):rec(f) for f in sorted((project/'.godot').rglob('*')) if f.is_file()};write(out/'cache-before-inventory.json',cache)
for attempt,entries in prior_outputs.items():
 for name,value in entries.items():assert rec(Path('/tmp/yuga-desktop-integrated-package-'+attempt)/name)==value
for row in audit['new_files']:assert rec(repo/row['path'])=={k:row[k] for k in ['bytes','sha256']}
write(out/'preserved-prior-outputs.json',prior_outputs)
write(out/'preparation-receipt.json',{'passed':True,'commit':commit,'project':str(project),'checkout_reused_from':prior,'all_115_generated_metadata_preserved':True,'runtime_bodies_equal_r2':True,'prior_build_logs_unchanged':True,'exclusions_count':113,'exclude':rec(exclude),'tracked_source_files':len(tracked),'runtime_source_files':len(runtime),'source_status':'clean','cache_files':len(cache),'tmp_free':shutil.disk_usage('/tmp').free,'completed_unix':time.time()})
shutil.copy2(Path(__file__),out/'preparation-driver.py')
print(json.dumps({'prepared':str(out),'commit':commit,'tracked_files':len(tracked),'runtime_files':len(runtime),'free':shutil.disk_usage('/tmp').free}))
