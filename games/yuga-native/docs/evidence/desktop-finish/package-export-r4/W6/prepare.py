"""Authorized exact owned-checkout restoration/update; no engine invocation."""
import hashlib,json,os,shutil,stat,subprocess,time,sys
from pathlib import Path
repo=Path('/tmp/yuga-desktop-integrated-package-r1/ANDOLAN'); canonical=Path('/workspace/ANDOLAN'); project=repo/'games/yuga-native'
out=Path('/workspace/scratch/yuga-desktop-integrated-package-r4'); prior='f8dec5fa4f9bbd2d20c58f6102fb984d0b19a9f1'; target='96d5b9cd3114b9732f7dc80433b1ca0a1d4a9b12'; reserve=128*1024*1024
report={'started_unix':time.time(),'prior':prior,'target':target,'project':str(project),'status':'preflight'}
def git(*args):return subprocess.check_output(['git',*args],cwd=repo)
def rec(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return {'bytes':p.stat().st_size,'sha256':h.hexdigest()}
def write(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
def free(path):s=os.statvfs(path);return s.f_bavail*s.f_frsize
def tree(commit):
 return {p.decode():(mode.decode(),blob.decode(),int(size)) for row in git('ls-tree','-rlz',commit).split(b'\0') if row for h,p in [row.split(b'\t',1)] for mode,typ,blob,size in [h.split()]}
def safe(p):
 assert not p.is_symlink() and p.resolve()==p,p
 for parent in p.parents:assert not parent.is_symlink(),parent
try:
 assert not (out/'preparation-receipt.json').exists() and not (out/'build').exists()
 assert git('rev-parse','HEAD').decode().strip()==prior
 assert not git('diff','--cached','--name-only') and not git('ls-files','--others','--exclude-standard')
 map_path=canonical/'docs/evidence/desktop-finish-package-source-cleanup-r1/recovery-map.json'
 assert rec(map_path)['sha256']=='fd3ad43d21c0bc118de05961edc438fbe4d75515c1cf6a18908571a4381a1f07'
 rows=json.loads(map_path.read_text())['files'];assert len(rows)==2732
 deleted=set(git('diff','--diff-filter=D','--name-only','-z','HEAD').decode().split('\0'))-{''}
 assert deleted=={x['path'] for x in rows} and not git('diff','--diff-filter=ACMRTUXB','--name-only','HEAD')
 old=tree(prior);new=tree(target)
 idx={p.decode():(m.decode(),b.decode()) for row in git('ls-files','--stage','-z').split(b'\0') if row for h,p in [row.split(b'\t',1)] for m,b,s in [h.split()]}
 for row in rows:
  path=repo/row['path'];safe(path);assert not path.exists()
  assert idx[row['path']]==(row['git_mode'],row['git_blob'])==old[row['path']][:2]
  assert old[row['path']][2]==row['size']
 growth=sum(((v[2]+4095)//4096)*4096 for p,v in new.items() if p not in old or old[p][1]!=v[1]);restore=sum(x['allocated_bytes'] for x in rows)
 report['capacity_before']={'tmp_free':free('/tmp'),'restore':restore,'target_delta_conservative':growth,'reserve':reserve,'workspace_free':free('/workspace')}
 assert free('/tmp')>=restore+growth+reserve,report['capacity_before']
 assert free('/workspace')>=784232448+reserve
 holders=[]
 for proc in Path('/proc').iterdir():
  if not proc.name.isdigit() or int(proc.name)==os.getpid():continue
  try:
   exe=(proc/'exe').resolve().name.lower();cwd=(proc/'cwd').resolve();argv=(proc/'cmdline').read_bytes()
  except (OSError,RuntimeError):continue
  if (cwd.is_relative_to(repo) or str(repo).encode() in argv) and ('godot' in exe or b'package-native.py' in argv):holders.append(proc.name)
 assert not holders,holders
 report['source_holders']=holders
 audit=json.loads((repo.parent/'uid-generation-audit.json').read_text());assert len(audit['new_files'])==115
 for row in audit['new_files']:assert rec(repo/row['path'])=={k:row[k] for k in ['bytes','sha256']}
 exclude=repo/'.git/info/exclude';prior_exclude=Path('/tmp/yuga-desktop-integrated-package-r3/git-info-exclude.txt');assert exclude.read_bytes()==prior_exclude.read_bytes()
 (out/'logs').mkdir();shutil.copy2(exclude,out/'git-info-exclude-before.txt')
 names=b''.join(x['path'].encode()+b'\0' for x in rows);(out/'restore-paths.nul').write_bytes(names)
 with (out/'logs/restore.log').open('wb') as log:
  subprocess.run(['git','checkout-index','--stdin','-z'],input=names,cwd=repo,stdout=log,stderr=subprocess.STDOUT,check=True)
 for row in rows:
  p=repo/row['path'];safe(p);assert p.is_file() and rec(p)=={'bytes':row['size'],'sha256':row['sha256']};p.chmod(int(row['mode'],8))
 assert not git('diff','--name-only','HEAD')
 report['restored_files']=len(rows);report['tmp_after_restore']=free('/tmp');write(out/'restoration-receipt.json',report)
 assert free('/tmp')>=growth+reserve,{'free':free('/tmp'),'growth':growth,'reserve':reserve}
 with (out/'logs/checkout.log').open('wb') as log:subprocess.run(['git','checkout','--detach',target],cwd=repo,stdout=log,stderr=subprocess.STDOUT,check=True)
 assert git('rev-parse','HEAD').decode().strip()==target and not git('status','--porcelain=v1')
 assert free('/tmp')>=reserve
 new_line='/games/yuga-native/tests/ui_focus_recovery_cases.gd.uid'
 text=exclude.read_text();assert new_line not in text.splitlines();exclude.write_text(text+('' if text.endswith('\n') else '\n')+new_line+'\n');shutil.copy2(exclude,out/'git-info-exclude.txt')
 assert exclude.read_text().splitlines()==prior_exclude.read_text().splitlines()+[new_line]
 tracked={name:rec(repo/name) for name in new};write(out/'tracked-source-before.json',tracked)
 for name,(mode,blob,size) in new.items():
  p=repo/name;assert p.is_file() and not p.is_symlink();assert p.stat().st_size==size
  assert bool(p.stat().st_mode&0o111)==(mode=='100755')
 assert not git('status','--porcelain=v1') and not git('diff','--name-only','HEAD')
 runtime={str(p.relative_to(project)):rec(p) for folder in ['scripts','shaders','scenes','assets'] for p in sorted((project/folder).rglob('*')) if p.is_file()}
 for name in ['project.godot','export_presets.cfg']:runtime[name]=rec(project/name)
 old_runtime=json.loads(Path('/tmp/yuga-desktop-integrated-package-r3/runtime-source-before.json').read_text());delta={p:{'before':old_runtime.get(p),'after':runtime.get(p)} for p in sorted(set(old_runtime)|set(runtime)) if old_runtime.get(p)!=runtime.get(p)}
 expected={'scripts/rama_hero_panel.gd':'b4badc8338d68d7861954408580c4ebcaaf355544f0bd57f8121c04875eea119','scripts/controls_overlay.gd':'423dac3e2bca461070a8feb3216c860400ef1e3c1ca03beda3e91976f27bca84'}
 assert set(delta)==set(expected) and all(delta[p]['after']['sha256']==h for p,h in expected.items()),delta
 write(out/'runtime-source-before.json',runtime);write(out/'runtime-delta-from-r3.json',delta)
 cache={str(p.relative_to(project/'.godot')):rec(p) for p in sorted((project/'.godot').rglob('*')) if p.is_file()};write(out/'cache-before-inventory.json',cache)
 for row in audit['new_files']:assert rec(repo/row['path'])=={k:row[k] for k in ['bytes','sha256']}
 protected={}
 for attempt in ['r1','r2','r3']:
  root=Path('/tmp/yuga-desktop-integrated-package-'+attempt)
  protected[attempt]={str(p.relative_to(root)):rec(p) for folder in ['build','logs'] for p in sorted((root/folder).rglob('*')) if p.is_file()}
 write(out/'preserved-prior-outputs.json',protected)
 (out/'build').mkdir()
 report.update({'status':'prepared','passed':True,'source_status':'clean','restored_files':len(rows),'tracked_files':len(tracked),'runtime_files':len(runtime),'runtime_delta':delta,'cache_files':len(cache),'all115_generated_metadata_preserved':True,'exact_added_exclusion':new_line,'exclude_before':rec(out/'git-info-exclude-before.txt'),'exclude_after':rec(out/'git-info-exclude.txt'),'tmp_free_after':free('/tmp'),'workspace_free_after':free('/workspace'),'finished_unix':time.time(),'scope':'Authorized owned-checkout restoration/update only; no engine invocation. Prior outputs inventoried after separately authorized duplicate cleanup.'})
 assert free('/tmp')>=reserve
 write(out/'preparation-receipt.json',report);print(json.dumps(report),flush=True)
except BaseException as e:
 report.update({'status':'failed','error':repr(e),'finished_unix':time.time(),'tmp_free':free('/tmp')});write(out/'preparation-failure.json',report);raise
