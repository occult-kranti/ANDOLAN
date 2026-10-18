"""Run only after the lead supplies a reviewed, remotely verified successor."""
import argparse,hashlib,json,shutil,subprocess,time
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--commit',required=True);a=p.parse_args()
assert len(a.commit)==40 and all(c in '0123456789abcdef' for c in a.commit)
repo=Path('/tmp/yuga-desktop-integrated-package-r1/ANDOLAN'); old=repo.parent; out=Path('/tmp/yuga-desktop-integrated-package-r2'); source=Path('/workspace/ANDOLAN');evidence=source/'games/yuga-native/docs/evidence/desktop-finish/package-export-r1/W6'
def command(*args):return subprocess.check_output(args,cwd=repo).decode().strip()
def sha(f):
 h=hashlib.sha256()
 with Path(f).open('rb') as s:
  for b in iter(lambda:s.read(1048576),b''):h.update(b)
 return h.hexdigest()
def rec(f):return {'bytes':f.stat().st_size,'sha256':sha(f)}
def write(f,x):f.write_text(json.dumps(x,indent=2)+'\n')
assert not out.exists();assert command('git','rev-parse','HEAD')=='b4d2871723a8cb66354d66abb17bd56fbd22c598';assert not command('git','diff','--name-only','HEAD')
subprocess.run(['git','cat-file','-e',a.commit+'^{commit}'],cwd=repo,check=True)
for process in Path('/proc').iterdir():
 if not process.name.isdigit():continue
 try:
  exe=(process/'exe').resolve().name.lower(); cwd=(process/'cwd').resolve(); argv=(process/'cmdline').read_bytes()
 except (OSError,RuntimeError):continue
 assert not (cwd.is_relative_to(repo) and ('godot' in exe or b'package-native.py' in argv)),process.name
old_outputs={str(f.relative_to(old)):rec(f) for directory in ['build','logs'] for f in sorted((old/directory).rglob('*')) if f.is_file()}
audit=json.loads((old/'uid-generation-audit.json').read_text()); assert len(audit['new_files'])==115
for row in audit['new_files']:assert rec(repo/row['path'])=={k:row[k] for k in ['bytes','sha256']}
listfile=evidence/'approved-generated-metadata-exclusions.txt';lines=listfile.read_text().splitlines();assert len(lines)==113
assert all(s.startswith(('/games/yuga-native/tests/','/games/yuga-native/tools/')) and s.endswith('.gd.uid') and not any(c in s for c in '*?[]') for s in lines)
out.mkdir();(out/'build').mkdir();(out/'logs').mkdir()
exclude=repo/'.git/info/exclude';before=exclude.read_bytes();addition=b'\n# Exact archived r1 generated non-runtime UID metadata, lead-approved.\n'+listfile.read_bytes();exclude.write_bytes(before+addition)
shutil.copy2(exclude,out/'git-info-exclude.txt')
# Move only the two archived untracked runtime sidecars aside, then obtain
# their exact approved successor bytes from Git; no canonical tree is touched.
(out/'preserved-untracked-runtime-uids').mkdir()
for relative in ['games/yuga-native/scripts/loading_presentation.gd.uid','games/yuga-native/scripts/rama_arrow_fletching.gd.uid']:
 f=repo/relative;expected=subprocess.check_output(['git','show',a.commit+':'+relative],cwd=repo);assert f.read_bytes()==expected
 shutil.move(str(f),str(out/'preserved-untracked-runtime-uids'/f.name))
with (out/'logs/checkout.log').open('w') as log:subprocess.run(['git','checkout','--detach',a.commit],cwd=repo,stdout=log,stderr=subprocess.STDOUT,check=True)
assert command('git','rev-parse','HEAD')==a.commit;status=command('git','status','--porcelain=v1');assert not status,status
tracked={}
for raw in subprocess.check_output(['git','ls-files','-z'],cwd=repo).decode().split('\0'):
 if raw:tracked[raw]=rec(repo/raw)
write(out/'tracked-source-before.json',tracked)
project=repo/'games/yuga-native';runtime={}
for folder in ['scripts','shaders','scenes','assets']:
 for f in sorted((project/folder).rglob('*')):
  if f.is_file():runtime[str(f.relative_to(project))]=rec(f)
for relative in ['project.godot','export_presets.cfg']:runtime[relative]=rec(project/relative)
write(out/'runtime-source-before.json',runtime)
cache={str(f.relative_to(project/'.godot')):rec(f) for f in sorted((project/'.godot').rglob('*')) if f.is_file()};write(out/'cache-before-inventory.json',cache)
assert all(rec(old/name)==record for name,record in old_outputs.items())
write(out/'preserved-r1-outputs.json',old_outputs)
write(out/'preparation-receipt.json',{'commit':a.commit,'project':str(project),'checkout_reused_from':'b4d2871723a8cb66354d66abb17bd56fbd22c598','prior_receipt':rec(evidence/'receipt.json'),'old_build_logs_unchanged':True,'exclusions_count':113,'exclude_sha256':sha(exclude),'tracked_source_files':len(tracked),'runtime_source_files':len(runtime),'source_status':status,'cache_files':len(cache),'tmp_free':shutil.disk_usage('/tmp').free,'completed_unix':time.time()})
print(json.dumps({'prepared':str(out),'commit':a.commit,'tracked_files':len(tracked),'runtime_files':len(runtime),'free':shutil.disk_usage('/tmp').free}))
