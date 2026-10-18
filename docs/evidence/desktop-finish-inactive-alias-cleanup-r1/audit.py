#!/usr/bin/env python3
"""Read-only, fixed eleven-file proposal; never removes or restores files."""
from pathlib import Path
import datetime, gzip, hashlib, json, os, stat, subprocess

ROOT = Path('/workspace/ANDOLAN')
OUT = Path(__file__).resolve().parent
COMMIT = '37bb953503a1a374f7c0c6aae1ef3d43cfba8867'
MAP = ROOT / 'games/yuga-native/docs/evidence/desktop-finish/backup-after-96d5-r1/inventory-and-recovery.json'
G = 'games/yuga-native/'
selected = [G+'art/hero-finish/hair-silhouette-r1/candidate-r2/'+n for n in ('rama-hero.glb','rama-hero-mid.glb','rama-hero-far.glb')]
selected += [G+'docs/evidence/desktop-finish/hair-silhouette/W2/'+n for n in ('smooth-parent-draw-r2.json','smooth-parent-draw-r3.json','canonical-pose-r1-meshes.json','smooth-parent-pose-r1-meshes.json')]
selected += [G+'docs/evidence/desktop-finish/hair-collected-r6/W1-native-r1/'+n for n in ('baseline/render/cast-three-quarter.png','baseline/render/rest-front.png','baseline/render/rest-rear.png','import-and-tools/baseline-import-semantics-r1.json')]

def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args])
def sha(data): return hashlib.sha256(data).hexdigest()
def blob(data): return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
def ident(p):
    assert p.resolve() == p.absolute(), 'Symlink ancestor: '+str(p)
    s=p.lstat()
    assert stat.S_ISREG(s.st_mode) and s.st_nlink == 1, p
    return {'size':s.st_size,'mode':oct(stat.S_IMODE(s.st_mode)),'device':s.st_dev,'inode':s.st_ino,'nlink':s.st_nlink,'allocated_bytes':s.st_blocks*512,'mtime_ns':s.st_mtime_ns}

def audit():
    d=json.loads(MAP.read_bytes())
    assert git('show',COMMIT+':'+str(MAP.relative_to(ROOT))) == MAP.read_bytes()
    rows={x['path']:x for x in d['files']+d['historical_exclusions']}
    assert len(selected)==11 and len(set(selected))==11
    result=[]
    for name in selected:
        row=rows[name]; rec=row['recovery']; p=ROOT/name
        before=ident(p); raw=p.read_bytes()
        assert (len(raw),sha(raw),blob(raw),before['mode']) == (row['bytes'],row['sha256'],row['git_blob'],row['mode']), name
        compressed=rec['kind']=='historical_lossless_gzip_mapping'
        source=rec['prior_recovery']['source'] if compressed else rec['source']
        chain=[source]
        # A gzip alias can itself point to an already committed identical gzip.
        while source in rows and rows[source]['recovery']['kind'] in ('recover_from_head_blob','recover_from_selected_file','historical_duplicate_covered_by_d1_history'):
            source=rows[source]['recovery']['source']; assert source not in chain; chain.append(source)
        tree=git('ls-tree',COMMIT,'--',source).decode().strip().split('\t')
        assert len(tree)==2 and tree[1]==source
        gitmode,kind,oid=tree[0].split(); assert gitmode in ('100644','100755') and kind=='blob'
        stored=git('cat-file','blob',oid)
        recovered=gzip.decompress(stored) if compressed else stored
        assert recovered==raw and (ROOT/source).read_bytes()==stored, name
        assert ident(p)==before
        assert not git('ls-files','--',name), 'Do not propose tracked-path deletion: '+name
        result.append({'path':name,'sha256':sha(raw),'git_blob':blob(raw),'filesystem':before,'map_row':row,'recovery':{'commit':COMMIT,'path':source,'alias_chain':chain,'git_blob':oid,'git_mode':gitmode,'stored_bytes':len(stored),'stored_sha256':sha(stored),'operation':'gzip_decompress' if compressed else 'write_blob_bytes','restore_mode':before['mode']}})

    absolute={str(ROOT/n) for n in selected}; holders=[]; inaccessible=[]; inaccessible_other=[]; zombies=0
    for proc in Path('/proc').iterdir():
        if not proc.name.isdigit(): continue
        try:
            status=dict(line.split(':',1) for line in (proc/'status').read_text().splitlines() if ':' in line)
            if status.get('State','').strip().startswith('Z'):
                zombies+=1; continue
            owned=int(status['Uid'].split()[0])==os.getuid()
            cmd=(proc/'cmdline').read_bytes().split(b'\0')
            if any(x.decode(errors='replace') in absolute for x in cmd):holders.append({'pid':int(proc.name),'kind':'exact_argv_path'})
            for fd in (proc/'fd').iterdir():
                try:
                    target=os.readlink(fd).removesuffix(' (deleted)')
                    if target in absolute:holders.append({'pid':int(proc.name),'kind':'fd','path':target})
                except FileNotFoundError:pass
            for line in (proc/'maps').read_text().splitlines():
                fields=line.split(None,5)
                if len(fields)==6 and fields[5].removesuffix(' (deleted)') in absolute:holders.append({'pid':int(proc.name),'kind':'mmap','path':fields[5]})
        except FileNotFoundError:pass
        except PermissionError:
            (inaccessible if owned else inaccessible_other).append(int(proc.name))
    assert not holders and not inaccessible, {'holders':holders,'inaccessible_owned':inaccessible}
    for row in result: assert ident(ROOT/row['path']) == row['filesystem']
    v=os.statvfs('/workspace')
    report={'schema':1,'status':'proposal_only_no_deletion','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_map':str(MAP.relative_to(ROOT)),'source_map_sha256':sha(MAP.read_bytes()),'verified_remote_branch_commit':COMMIT,'remote_observation':'git ls-remote origin refs/heads/game/yuga-native-production returned exact commit before this audit','candidate_files':len(result),'logical_bytes':sum(x['filesystem']['size'] for x in result),'allocated_file_bytes':sum(x['filesystem']['allocated_bytes'] for x in result),'workspace_available_bytes':v.f_bavail*v.f_frsize,'required_reserve_bytes':500*1024*1024,'fresh_process_holders':holders,'inaccessible_owned_processes':inaccessible,'inaccessible_other_uid_processes':inaccessible_other,'zombies_without_live_file_descriptors':zombies,'files':result,'exclusions':['All current W1/W2/W4 art/capture/preparation paths','All canonical runtime assets and scripts','All actual r4 release/public/extraction artifacts','All ambient caches, user state and unique originals','Retained recovery-source paths and Git object store','Already removed r4 expanded payloads'], 'execution_gate':'No deletion is authorized. Root approval, remote-backed exact proposal, renewed owner/process and per-file identity checks are required before any separate execution.'}
    return report

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report',type=Path,required=True)
    args=parser.parse_args()
    assert not args.report.exists() and not args.report.is_symlink()
    result=audit()
    args.report.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('status','candidate_files','logical_bytes','allocated_file_bytes','workspace_available_bytes','fresh_process_holders','inaccessible_owned_processes')}))
