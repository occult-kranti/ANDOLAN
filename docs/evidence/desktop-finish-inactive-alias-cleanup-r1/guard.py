"""Fixed eleven-file alias cleanup; default verifies only, explicit root invocation removes."""
from pathlib import Path
import argparse, datetime, hashlib, importlib.util, json, os, subprocess

HERE=Path(__file__).resolve().parent
ROOT=Path('/workspace/ANDOLAN')
spec=importlib.util.spec_from_file_location('inactive_alias_audit', HERE/'audit.py')
audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--report',type=Path,required=True)
    p.add_argument('--remove',action='store_true')
    p.add_argument('--published-commit')
    p.add_argument('--confirm-owner-release',action='store_true')
    a=p.parse_args()
    assert not a.report.exists() and not a.report.is_symlink()
    raw=(HERE/'recovery-map.json').read_bytes();saved=json.loads(raw)
    assert saved['verified_remote_branch_commit']==audit.COMMIT
    assert [r['path'] for r in saved['files']]==audit.selected
    assert saved['candidate_files']==len(saved['files'])==11
    assert saved['logical_bytes']==171704653 and saved['allocated_file_bytes']==171728896
    if a.remove:
        assert a.confirm_owner_release and a.published_commit and len(a.published_commit)==40
        remote=audit.git('ls-remote','origin','refs/heads/game/yuga-native-production').decode().split()[0]
        for commit in (audit.COMMIT,a.published_commit):
            subprocess.run(['git','-C',str(ROOT),'merge-base','--is-ancestor',commit,remote],check=True)
        for name in ('recovery-map.json','audit.py','guard.py','ownership.json','README.md'):
            f=HERE/name
            assert audit.git('show',a.published_commit+':'+str(f.relative_to(ROOT)))==f.read_bytes(), name
    else:
        assert a.published_commit is None and not a.confirm_owner_release
    # Re-read every file, Git recovery blob and gzip, all modes/inodes, Git index,
    # and accessible live process holders. This audit never modifies candidates.
    fresh=audit.audit()
    assert fresh['files']==saved['files'], 'Candidate or recovery identity changed'
    assert not fresh['fresh_process_holders'] and not fresh['inaccessible_owned_processes']
    before=os.statvfs('/workspace');removed=[];failure=None
    try:
        if a.remove:
            for row in saved['files']:
                f=ROOT/row['path']
                assert audit.ident(f)==row['filesystem']
                assert not audit.git('ls-files','--',row['path']), 'Candidate became tracked'
                assert hashlib.sha256(f.read_bytes()).hexdigest()==row['sha256']
                f.unlink()
                removed.append({k:row[k] for k in ('path','sha256','git_blob','filesystem','recovery')})
            assert all(not (ROOT/row['path']).exists() for row in saved['files'])
        # Retained recovery sources must remain exact after execution.
        for row in saved['files']:
            rec=row['recovery'];f=ROOT/rec['path']
            assert f.resolve()==f.absolute() and hashlib.sha256(f.read_bytes()).hexdigest()==rec['stored_sha256']
    except BaseException as exc:
        failure=type(exc).__name__+': '+str(exc)
        raise
    finally:
        after=os.statvfs('/workspace')
        report={'schema':1,'status':'failed_with_partial_record' if failure else ('removed_exact_files' if a.remove else 'verified_only_no_deletion'),'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'map_sha256':hashlib.sha256(raw).hexdigest(),'published_commit':a.published_commit,'verified_files':11,'removed_files':len(removed),'removed':removed,'failure':failure,'logical_bytes':sum(r['filesystem']['size'] for r in removed),'allocated_file_bytes':sum(r['filesystem']['allocated_bytes'] for r in removed),'proposed_allocated_file_bytes':saved['allocated_file_bytes'],'workspace_available_before':before.f_bavail*before.f_frsize,'workspace_available_after':after.f_bavail*after.f_frsize,'process_observation':{k:v for k,v in fresh.items() if 'process' in k or 'zombies' in k},'scope':'Only fixed untracked aliases; directories, retained Git/gzip sources, actual r4 release, current art, caches/user state and unique evidence untouched. Concurrent writes can affect free-space delta.'}
        a.report.write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps({k:report[k] for k in ('status','verified_files','removed_files','allocated_file_bytes')}))

if __name__=='__main__':main()
