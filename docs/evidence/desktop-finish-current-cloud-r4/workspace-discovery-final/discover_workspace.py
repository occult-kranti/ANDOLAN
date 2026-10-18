"""Metadata-only full /workspace discovery; prune .git internals, follow no links."""
from pathlib import Path
import datetime
import json
import hashlib
import os
import subprocess
from urllib.parse import urlsplit

ROOT = Path('/workspace')
OUT = Path(__file__).resolve().parent
EXPECTED_HEAD = 'b843eaf1026e835cc18765c2342dfdf34fd66c90'
DEPENDENCY_ROOTS = {
 '/workspace/scratch/community-reuse/animation/sources/blender-addons',
 '/workspace/scratch/community-reuse/animation/sources/ozz-animation',
 '/workspace/scratch/community-reuse/animation/sources/godot-demo-projects',
 '/workspace/scratch/community-reuse/art/upstream/material-maker',
}
MARKERS = {'package.json','project.godot','pyproject.toml','Cargo.toml','go.mod','SConstruct','CMakeLists.txt','composer.json'}

def redact_url(raw):
    if '://' in raw:
        p=urlsplit(raw)
        return p.scheme+'://'+str(p.hostname or '')+p.path
    if '@' in raw and ':' in raw.split('@',1)[1]:
        return 'ssh://'+raw.split('@',1)[1].replace(':','/',1).split('?',1)[0]
    return raw.split('?',1)[0]

def category(path, origin=''):
    s=str(path)
    if s=='/workspace/ANDOLAN':return 'primary project monorepo'
    if s in DEPENDENCY_ROOTS:return 'third-party dependency/reference Git checkout; not an owned product repository'
    if '/node_modules/' in s or '/thirdparty/' in s or '/vendor/' in s:return 'third-party dependency/reference subtree'
    if s.startswith('/workspace/tooling/'):return 'tooling or third-party reference checkout; not a product source'
    if s.startswith('/workspace/scratch/'):return 'task snapshot/evidence/reference workspace; not an independent product'
    if s.startswith('/workspace/ANDOLAN/'):return 'project subtree; attribution/manifest needed for dependency distinction'
    if 'occult-kranti/ANDOLAN' in origin:return 'additional clone of the primary project'
    if origin:return 'other repository; classify from pinned origin before adoption'
    return 'local project/reference candidate without Git identity'

def main():
    def root_state():
        head=subprocess.check_output(['git','--no-optional-locks','-C','/workspace/ANDOLAN','rev-parse','HEAD'],text=True).strip()
        return dict(head=head,index_sha256=hashlib.sha256(Path('/workspace/ANDOLAN/.git/index').read_bytes()).hexdigest())
    before=root_state();assert before['head']==EXPECTED_HEAD
    stack=[ROOT];dirs=files=0;links=[];errors=[];repos=[];markers=[];pruned=[]
    started=datetime.datetime.now(datetime.timezone.utc).isoformat()
    while stack:
        folder=stack.pop();dirs+=1
        try: entries=sorted(os.scandir(folder),key=lambda x:x.name)
        except OSError as e:errors.append(dict(path=str(folder),error_type=type(e).__name__,errno=e.errno));continue
        names={e.name for e in entries}
        local_markers=sorted(names&MARKERS)
        if local_markers:markers.append(dict(path=str(folder),markers=local_markers,classification=category(folder)))
        git=next((e for e in entries if e.name=='.git'),None)
        if git:
            repos.append(dict(path=str(folder),git_marker_kind='symlink'if git.is_symlink()else 'directory'if git.is_dir(follow_symlinks=False)else 'file',classification=category(folder)))
        elif {'HEAD','config','objects','refs'}<=names:
            repos.append(dict(path=str(folder),git_marker_kind='possible-bare',classification=category(folder)))
        for e in entries:
            try:
                if e.is_symlink():links.append(dict(path=e.path,target=os.readlink(e.path)));continue
                if e.is_dir(follow_symlinks=False):
                    if e.name=='.git':pruned.append(e.path)
                    else:stack.append(Path(e.path))
                else:files+=1
            except OSError as ex:errors.append(dict(path=e.path,error_type=type(ex).__name__,errno=ex.errno))
    for r in repos:
        if r['git_marker_kind']!='directory':
            r['metadata_note']='Marker retained without resolving link/worktree pointer or guessing bare identity.';continue
        env={**os.environ,'GIT_OPTIONAL_LOCKS':'0'}
        for key,args in [('head',['rev-parse','HEAD']),('origin',['config','--get','remote.origin.url'])]:
            p=subprocess.run(['git','--no-optional-locks','-C',r['path'],*args],capture_output=True,text=True,env=env,timeout=10)
            if p.returncode==0:r[key]=redact_url(p.stdout.strip())if key=='origin'else p.stdout.strip()
            else:r[key]=None
        r['classification']=category(Path(r['path']),r.get('origin')or'')
    after=root_state();assert before==after
    prior=json.loads(Path('/workspace/ANDOLAN/games/yuga-native/docs/evidence/desktop-finish/backup-after-96d5-r1/workspace-discovery.json').read_text())
    previous_roots={r['path']for r in prior['repositories']};current_roots={r['path']for r in repos}
    result=dict(git_before=before,git_after=after,normal_head_index_unchanged=True,root_membership_unchanged_from_backup_A=previous_roots==current_roots,new_git_markers=sorted(current_roots-previous_roots),removed_git_markers=sorted(previous_roots-current_roots),symlink_limit='Symlink entries are recorded and never traversed; repository roots reachable only through a link or outside /workspace are outside this scan. No unknown ordinary directory was deliberately omitted.',scope='Full metadata walk of /workspace. Only .git directory internals pruned; no symlink traversal. No project builds, downloads, source/content census or legal reuse inference.',started_at=started,finished_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),complete=not errors,directories_visited=dirs,non_symlink_files_seen=files,git_internals_pruned=pruned,repositories=repos,project_manifest_roots=markers,symlinks_not_followed=links,errors=errors)
    (OUT/'workspace-discovery.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(dict(complete=result['complete'],directories=dirs,files=files,git_markers=len(repos),manifest_roots=len(markers),symlinks=len(links),errors=errors,repositories=repos)))

if __name__=='__main__':main()
