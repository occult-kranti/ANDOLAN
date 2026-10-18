#!/usr/bin/env python3
"""Freeze committed runtime and independently verified current imported resources."""
import argparse,hashlib,json,shutil,subprocess,tarfile
from pathlib import Path

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--project',type=Path,required=True);p.add_argument('--commit',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 assert a.output.is_absolute() and not a.output.exists();a.output.mkdir(parents=True)
 repository=Path(subprocess.check_output(['git','rev-parse','--show-toplevel'],cwd=a.project,text=True).strip());prefix=a.project.relative_to(repository).as_posix()+'/'
 names=['assets','scripts','shaders','scenes','project.godot','tools/visual-campaign/capture.gd','tools/visual-campaign/run.py','tools/visual-rounds/capture.gd','tools/visual-rounds/capture_groom.gd','tools/visual-rounds/run.py']
 command=['git','archive',a.commit,*[prefix+n for n in names]]
 process=subprocess.Popen(command,cwd=repository,stdout=subprocess.PIPE)
 with tarfile.open(fileobj=process.stdout,mode='r|') as archive:
  for member in archive:
   if not member.isfile(): continue
   relative=Path(member.name.removeprefix(prefix));assert '..' not in relative.parts
   destination=a.output/relative;destination.parent.mkdir(parents=True,exist_ok=True)
   with archive.extractfile(member) as source,destination.open('xb') as target:shutil.copyfileobj(source,target)
 assert process.wait()==0
 # Font descriptors are generated and ignored by Git. Reuse only descriptors
 # whose corresponding committed source is byte-exact; their resource MD5 is
 # independently checked below, without running an editor import.
 for descriptor in (a.project/'assets').rglob('*.import'):
  relative=descriptor.relative_to(a.project);target=a.output/relative
  if target.exists():continue
  source=Path(str(relative)[:-7])
  assert (a.output/source).exists() and sha(a.output/source)==sha(a.project/source)
  shutil.copy2(descriptor,target)
 cache=a.output/'.godot';cache.mkdir();shutil.copytree(a.project/'.godot/imported',cache/'imported')
 for name in ['uid_cache.bin','global_script_class_cache.cfg']:
  source=a.project/'.godot'/name
  if source.exists():shutil.copy2(source,cache/name)
 promotion=a.project/'docs/evidence/visual-rounds/round3/integration/promotion.json';receipt=json.loads(promotion.read_text());checks=[]
 for name,pin in receipt['cache_files'].items():
  checks.append({'path':name,'sha256':sha(a.output/name),'expected':pin['sha256'],'exact':sha(a.output/name)==pin['sha256']})
 assert all(x['exact'] for x in checks)
 imports=[]
 for desc in sorted((a.output/'assets').rglob('*.import')):
  source=Path(str(desc)[:-7]);text=desc.read_text();import re
  match=re.search(r'^path="res://([^\"]+)"',text,re.M)
  if not match:continue
  resource=a.output/match.group(1);md5=resource.with_suffix('.md5')
  origin=re.search(r'source_md5="([a-f0-9]+)"',md5.read_text())
  fresh=origin is not None and origin.group(1)==hashlib.md5(source.read_bytes()).hexdigest()
  imports.append({'source':str(source.relative_to(a.output)),'fresh':fresh})
 assert all(x['fresh'] for x in imports),'Stale imported source in frozen project'
 files={str(f.relative_to(a.output)):sha(f) for f in sorted(a.output.rglob('*')) if f.is_file()}
 result={'source_commit':a.commit,'source_project':str(a.project),'freeze_command':command,'runtime_and_imports':files,'promotion_receipt_sha256':sha(promotion),'promotion_cache_checks':checks,'import_freshness':imports,'scope':'Committed current runtime plus existing fresh imported cache. No editor import or historical image identity transfer. Capture helper and contract pinned separately.'}
 (a.output/'motion-freeze.json').write_text(json.dumps(result,indent=2)+'\n')
 for name in ['capture_motion.gd','motion_contract.json','run_motion.py']:
  shutil.copy2(a.project/'tools/visual-rounds'/name,a.output/'tools/visual-rounds'/name)
 print(json.dumps({'complete':True,'source_commit':a.commit,'files':len(files),'fresh_imports':len(imports),'project':str(a.output)}))
if __name__=='__main__':main()
