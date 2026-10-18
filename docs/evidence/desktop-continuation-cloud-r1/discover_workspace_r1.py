#!/usr/bin/env python3
"""Read-only complete workspace Git discovery. Only new report files are written."""
import argparse,datetime,hashlib,json,os,re,stat,subprocess,sys
from pathlib import Path
from urllib.parse import urlsplit,urlunsplit

WORKSPACE=Path('/workspace')
PRIMARY=WORKSPACE/'ANDOLAN'
PRIOR=PRIMARY/'docs/evidence/desktop-finish-current-cloud-r4/workspace-discovery-final/workspace-discovery.json'
W6=PRIMARY/'games/yuga-native/docs/evidence/desktop-finish/continuation-oct18/W6-integration-r1'
AREA=WORKSPACE/'scratch/yuga-continuation-W6-r1'
REFERENCES={
 '/workspace/scratch/community-reuse/art/upstream/material-maker',
 '/workspace/scratch/community-reuse/animation/sources/ozz-animation',
 '/workspace/scratch/community-reuse/animation/sources/godot-demo-projects',
 '/workspace/scratch/community-reuse/animation/sources/blender-addons',
}
MARKERS={'package.json','project.godot','pyproject.toml','Cargo.toml','go.mod','SConstruct','CMakeLists.txt','composer.json'}
ENV={k:v for k,v in os.environ.items()if not k.startswith('GIT_')}
ENV.update(GIT_OPTIONAL_LOCKS='0',GIT_CONFIG_NOSYSTEM='1')

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def within(path):return path==WORKSPACE or WORKSPACE in path.parents

def git(root,*args):
 p=subprocess.run(['git','--no-optional-locks','-C',str(root),*args],env=ENV,capture_output=True,text=True,timeout=15)
 return p.returncode,p.stdout.strip()

def remote(raw,base):
 """Never retain userinfo, query, fragment, helper commands or unknown transports."""
 raw=raw.strip()
 if '://'in raw:
  try:
   p=urlsplit(raw)
   if p.scheme not in {'https','http','ssh','git','file'}:return '[redacted unsupported transport]'
   host=p.hostname or '';host='['+host+']'if ':'in host else host
   if p.port:host+=':'+str(p.port)
   return urlunsplit((p.scheme,host,p.path,'',''))
  except ValueError:return '[redacted malformed remote]'
 if '::'in raw:return '[redacted remote helper]'
 m=re.fullmatch(r'(?:[^@/:]+@)?([^/:]+):(.+)',raw)
 if m:return 'ssh://'+m[1]+'/'+m[2].split('?',1)[0].split('#',1)[0]
 return str((base/raw.split('?',1)[0].split('#',1)[0]).resolve())

def parse_gitfile(text):
 rows=text.splitlines()
 if len(rows)!=1 or not rows[0].startswith('gitdir: ')or not rows[0][8:]:raise ValueError('Invalid .git pointer')
 return rows[0][8:]

def head_result(commit_code,commit,symbolic_code,symbolic,ref_code):
 if commit_code==0 and re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}',commit):return dict(state='commit',commit=commit)
 if symbolic_code==0 and symbolic.startswith('refs/heads/')and ref_code==1:
  return dict(state='positively_unborn',commit=None,symbolic_ref=symbolic,proof='symbolic HEAD exists and exact referenced branch is absent (show-ref exit1)')
 raise ValueError('HEAD is neither a verified commit nor a positively unborn branch')

def head(root):
 code,commit=git(root,'rev-parse','--verify','HEAD^{commit}')
 sc,symbolic=git(root,'symbolic-ref','--quiet','HEAD')
 rc,_=git(root,'show-ref','--verify','--quiet',symbolic)if sc==0 else(-1,'')
 return head_result(code,commit,sc,symbolic,rc)

def metadata(root,kind):
 bc,bare=git(root,'rev-parse','--is-bare-repository')
 if bc or bare not in {'true','false'}:raise ValueError('Git marker does not resolve to a repository')
 dc,gitdir=git(root,'rev-parse','--absolute-git-dir')
 cc,common=git(root,'rev-parse','--path-format=absolute','--git-common-dir')
 if dc or cc:raise ValueError('Unresolved Git directory/common directory')
 if bare=='true':actual=Path(gitdir).resolve(strict=True)
 else:
  tc,top=git(root,'rev-parse','--show-toplevel')
  if tc:raise ValueError('Worktree root unresolved')
  actual=Path(top).resolve(strict=True)
 if actual!=root:raise ValueError('Marker resolves to a different root, not this directory')
 if not within(actual):raise ValueError('Actual Git root is outside /workspace')
 marker=root/'.git';pointer=None
 if kind!='bare':
  resolved_marker=marker.resolve(strict=True)
  if resolved_marker.is_file():
   if resolved_marker.stat().st_size>8192:raise ValueError('Oversize .git pointer')
   pointer=parse_gitfile(resolved_marker.read_text())
   resolved_marker=(marker.parent/pointer).resolve(strict=True)
  if resolved_marker!=Path(gitdir).resolve(strict=True):raise ValueError('.git marker and Git disagree')
 code,config=git(root,'config','--local','--null','--get-regexp',r'^remote\..*\.(url|pushurl)$')
 if code not in {0,1}:raise ValueError('Remote configuration cannot be read')
 remotes=[]
 for item in config.split('\0'):
  if not item:continue
  key,value=item.split('\n',1);remotes.append(dict(key=key,value=remote(value,root)))
 return dict(path=str(actual),git_marker_kind=kind,git_dir=str(Path(gitdir).resolve(strict=True)),common_git_dir=str(Path(common).resolve(strict=True)),git_pointer_resolved=pointer is not None,bare=bare=='true',head=head(root),remotes=remotes)

def proof(path,fields):return dict(path=str(path),sha256=sha(path),fields=fields)

def rules():
 prior=json.loads(PRIOR.read_text());result={}
 for row in prior['repositories']:
  if row['path']in REFERENCES:result[row['path']]=dict(kind='third_party_reference',head=row['head'],origin=row['origin'],proof=proof(PRIOR,dict(path=row['path'],head=row['head'],origin=row['origin'])))
 if set(result)!=REFERENCES:raise ValueError('Known four reference classifications lack prior exact evidence')
 for take in [1,2]:
  target=AREA/f'package-successor-r{take}/ANDOLAN'
  for p in sorted(AREA.glob(f'package-successor-r{take}-*.json')):
   r=json.loads(p.read_text())
   if r.get('repository')!=str(target)or not r.get('materialized'):continue
   if r.get('source_repository')!=str(PRIMARY)or r.get('artifact_root')!=str(target.parent)or r.get('classification')!='isolated export artifact; not a managed project':raise ValueError('Artifact receipt disagrees with exact classification')
   result[str(target)]=dict(kind='isolated_package_artifact',head=r['source_commit'],proof=proof(p,{k:r[k]for k in ['repository','artifact_root','source_repository','classification','source_commit','materialized']}))
 for p in sorted(W6.glob('snapshot-guard-checks*.json')):
  r=json.loads(p.read_text());fixture=r.get('fixture')
  if not fixture or not r.get('scope','').startswith('Synthetic source, index, inode'):continue
  f=Path(fixture)
  if f.parent!=AREA or not re.fullmatch(r'snapshot-guard-fixture-r[0-9]+',f.name):raise ValueError('Unexpected guard fixture root')
  result[str(f/'source')]=dict(kind='synthetic_guard_fixture',proof=proof(p,dict(fixture=fixture,scope=r['scope'],passed=r.get('passed'))))
 return result

def classify(row,known):
 path=row['path']
 if path==str(PRIMARY):return dict(kind='primary_project',managed_project=True,evidence='Explicit primary /workspace/ANDOLAN')
 rule=known.get(path)
 if rule is None:return dict(kind='unclassified',managed_project=None,blocker='No exact receipt-backed ownership classification; scratch location is not evidence')
 if rule.get('head')and row['head'].get('commit')!=rule['head']:return dict(kind='unclassified',managed_project=None,blocker='Known root HEAD differs from classification receipt')
 if rule['kind']=='third_party_reference'and not any(x['key']=='remote.origin.url'and x['value']==rule['origin']for x in row['remotes']):
  return dict(kind='unclassified',managed_project=None,blocker='Known reference origin differs from pinned evidence')
 return dict(kind=rule['kind'],managed_project=False,evidence=rule['proof'])

def primary_state():
 code,commit=git(PRIMARY,'rev-parse','--verify','HEAD^{commit}')
 if code:raise ValueError('Primary HEAD unresolved')
 _,gd=git(PRIMARY,'rev-parse','--absolute-git-dir');gd=Path(gd)
 _,common=git(PRIMARY,'rev-parse','--path-format=absolute','--git-common-dir');common=Path(common)
 _,ref=git(PRIMARY,'symbolic-ref','--quiet','HEAD')
 paths=[gd/'HEAD',gd/'index',common/'packed-refs']+([common/ref]if ref else[])
 state={}
 for p in paths:
  try:s=p.stat();state[str(p)]=dict(device=s.st_dev,inode=s.st_ino,mtime_ns=s.st_mtime_ns,ctime_ns=s.st_ctime_ns,bytes=s.st_size,sha256=sha(p))
  except FileNotFoundError:state[str(p)]=None
 return dict(head=commit,metadata=state)

def self_test():
 checks=[remote('https://u:SECRET@github.com/a/b.git?token=SECRET#SECRET',PRIMARY)=='https://github.com/a/b.git',remote('git@github.com:a/b.git?SECRET#SECRET',PRIMARY)=='ssh://github.com/a/b.git',remote('ext::secret command',PRIMARY)=='[redacted remote helper]',parse_gitfile('gitdir: ../meta\n')=='../meta',head_result(1,'',0,'refs/heads/main',1)['state']=='positively_unborn',classify(dict(path='/workspace/scratch/unknown'),{})['kind']=='unclassified']
 for values in [(1,'',1,'',1),(1,'',0,'refs/heads/main',128)]:
  try:head_result(*values);checks.append(False)
  except ValueError:checks.append(True)
 assert all(checks);print(json.dumps(dict(self_test_passed=True,count=len(checks))))

def main():
 p=argparse.ArgumentParser();p.add_argument('--expected-head');p.add_argument('--output',type=Path);p.add_argument('--self-test',action='store_true');a=p.parse_args()
 if a.self_test:self_test();return 0
 if not a.expected_head or not re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}',a.expected_head)or a.output is None:p.error('Full --expected-head and fresh --output are required')
 if a.output.exists()or a.output.is_symlink():p.error('Output must be a fresh file')
 started=datetime.datetime.now(datetime.timezone.utc).isoformat();errors=[];boundaries=[];links=[];aliases=[];repos=[];manifests=[];watched={};visited={};pruned=[];dirs=files=0;before=None;after=None
 def fail(path,reason,kind='blocker'):errors.append(dict(path=str(path),reason=reason,kind=kind))
 try:
  before=primary_state()
  if before['head']!=a.expected_head:raise ValueError('Primary HEAD differs from --expected-head before scan')
  known=rules();stack=[WORKSPACE]
  while stack:
   folder=stack.pop()
   try:
    folder=folder.resolve(strict=True)
    if not within(folder):boundaries.append(dict(path=str(folder),reason='outside_workspace_not_traversed'));continue
    s=folder.stat();identity=(s.st_dev,s.st_ino)
    if identity in visited:aliases.append(dict(path=str(folder),already_visited=visited[identity]));continue
    visited[identity]=str(folder);watched[folder]=(s.st_mtime_ns,s.st_ctime_ns);entries=sorted(os.scandir(folder),key=lambda e:e.name);dirs+=1
    names={e.name for e in entries};local=sorted(names&MARKERS)
    if local:manifests.append(dict(path=str(folder),markers=local,note='Inventory only; manifests are not independent managed-project classifications'))
    marker=next((e for e in entries if e.name=='.git'),None)
    candidate='symlink'if marker and marker.is_symlink()else'directory'if marker and marker.is_dir(follow_symlinks=False)else'file'if marker else'bare'if {'HEAD','config','objects','refs'}<=names else None
    if candidate:
     try:
      row=metadata(folder,candidate);row['classification']=classify(row,known);repos.append(row)
      if row['classification']['kind']=='unclassified':fail(folder,row['classification']['blocker'])
      if candidate=='bare':pruned.append(dict(path=str(folder),reason='verified_bare_git_storage'));continue
     except (OSError,ValueError,subprocess.SubprocessError)as e:fail(folder,type(e).__name__+': '+str(e));
    for entry in entries:
     try:
      if entry.name=='.git':pruned.append(dict(path=entry.path,reason='explicit_git_marker_metadata'));continue
      if entry.is_symlink():
       target=Path(entry.path).resolve(strict=True);mode=target.stat().st_mode
       row=dict(path=entry.path,target=str(target),target_kind='directory'if stat.S_ISDIR(mode)else'file'if stat.S_ISREG(mode)else'other',inside_workspace=within(target));links.append(row)
       if not within(target):boundaries.append(dict(path=entry.path,target=str(target),reason='outside_workspace_not_traversed'))
       elif stat.S_ISDIR(mode):stack.append(target)
       continue
      if entry.is_dir(follow_symlinks=False):stack.append(Path(entry.path))
      else:files+=1
     except (OSError,RuntimeError)as e:fail(entry.path,type(e).__name__+': '+str(e))
    if dirs%512==0:
     code,current=git(PRIMARY,'rev-parse','--verify','HEAD^{commit}')
     if code or current!=a.expected_head:raise ValueError('Primary HEAD changed during scan')
   except (OSError,RuntimeError)as e:fail(folder,type(e).__name__+': '+str(e))
  for folder,stamp in watched.items():
   try:
    s=folder.stat()
    if stamp!=(s.st_mtime_ns,s.st_ctime_ns):fail(folder,'Directory changed during discovery; rerun after writers settle','concurrent_change')
   except OSError as e:fail(folder,type(e).__name__+': '+str(e))
  for row in repos:
   try:
    if head(Path(row['path']))!=row['head']:fail(row['path'],'Repository HEAD changed during discovery','concurrent_change')
   except (OSError,ValueError,subprocess.SubprocessError)as e:fail(row['path'],type(e).__name__+': '+str(e))
  after=primary_state()
  if after!=before:fail(PRIMARY,'Primary HEAD/ref/index identity changed during discovery','concurrent_change')
 except (OSError,ValueError,subprocess.SubprocessError)as e:fail(PRIMARY,type(e).__name__+': '+str(e))
 managed=[r['path']for r in repos if r['classification'].get('managed_project')is True]
 if managed!=[str(PRIMARY)]and not errors:fail(PRIMARY,'Primary managed-project census is not exactly /workspace/ANDOLAN')
 result=dict(schema=1,scope='Complete read-only metadata walk of actual /workspace targets; Git storage explicitly pruned, outside-workspace symlink boundaries explicit. No build, network, Git write, configuration save, content/rights census or managed-project adoption.',expected_head=a.expected_head,started_at=started,finished_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),complete=not errors,git_before=before,git_after=after,primary_head_and_index_unchanged=before==after if before and after else False,directories_visited=dirs,files_seen=files,repositories=sorted(repos,key=lambda r:r['path']),managed_project_roots=managed,manifest_directories=manifests,symlinks=links,directory_aliases=aliases,explicit_boundaries=boundaries,git_storage_pruned=pruned,blockers=errors,script_sha256=sha(Path(__file__)))
 with a.output.open('x')as f:json.dump(result,f,indent=2);f.write('\n')
 print(json.dumps(dict(complete=result['complete'],repositories=result['repositories'],managed_project_roots=managed,directories=dirs,files=files,symlinks=len(links),blockers=errors,report=str(a.output))))
 return 0 if result['complete']else 1
if __name__=='__main__':sys.exit(main())
