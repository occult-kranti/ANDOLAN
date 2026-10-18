import hashlib,json,os,pathlib,subprocess
R=pathlib.Path('/workspace/ANDOLAN');O=pathlib.Path('/workspace/scratch/yuga-continuation-root-r1/recovery-backup-r1');O.mkdir(exist_ok=False)
H='79e5c15d8a3657e16fda67acb277b2406120dcd1';B='backup/yuga-desktop-polish-recovery-2026-10-18'
base=R/'games/yuga-native/docs/evidence/desktop-finish/continuation-oct18'
paths=sorted([p for p in (base/'W6-package-r2-duplicates').iterdir() if p.is_file()]+[base/'W6-package-r2/qualification-receipt-uid-reviewed.json'])
def git(*args,env=None,data=None):return subprocess.check_output(['git','--no-optional-locks','-C',str(R),*args],env=env,input=data)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert git('rev-parse','HEAD').decode().strip()==H
index=R/'.git/index';before=sha(index);assert not git('diff','--name-only','HEAD')
assert not git('ls-remote','origin','refs/heads/'+B).strip()
assert any(p.name=='owner-release.json' for p in paths)
manifest=[];env=dict(os.environ,GIT_INDEX_FILE=str(O/'private.index'))
git('read-tree',H,env=env)
for p in paths:
 assert p.resolve()==p.absolute() and not p.is_symlink()
 rel=p.relative_to(R).as_posix();data=p.read_bytes();oid=git('hash-object','-w','--stdin',data=data).decode().strip()
 mode='100755' if p.stat().st_mode&0o111 else '100644';git('update-index','--add','--cacheinfo',mode,oid,rel,env=env)
 manifest.append({'path':rel,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'blob':oid,'mode':mode})
tree=git('write-tree',env=env).decode().strip();commit=git('commit-tree',tree,'-p',H,data=b'Back up exact qualified package duplicate recovery map [skip ci]\n').decode().strip()
changed=git('diff-tree','--no-commit-id','--name-only','-r',H,commit).decode().splitlines();assert set(changed)=={r['path'] for r in manifest}
for row in manifest:assert hashlib.sha256(git('cat-file','blob',commit+':'+row['path'])).hexdigest()==row['sha256']
assert sha(index)==before and git('rev-parse','HEAD').decode().strip()==H
(O/'manifest.json').write_text(json.dumps({'source':H,'backup_commit':commit,'branch':B,'tree':tree,'files':manifest,'canonical_index_before_sha256':before},indent=2)+'\n')
git('push','origin',commit+':refs/heads/'+B)
assert git('ls-remote','--exit-code','origin','refs/heads/'+B).decode().split()==[commit,'refs/heads/'+B]
assert sha(index)==before and git('rev-parse','HEAD').decode().strip()==H
(O/'remote-verification.json').write_text(json.dumps({'passed':True,'backup_commit':commit,'branch':B,'source_unchanged':H,'canonical_index_sha256':sha(index),'file_count':len(manifest)},indent=2)+'\n')
print(json.dumps({'passed':True,'commit':commit,'branch':B,'file_count':len(manifest)}))
