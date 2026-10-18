#!/usr/bin/env python3
"""Only the two inactive original r2 ZIP aliases; public downloads stay retained.

Default commands are local read-only checks. --remove additionally requires a
root-authorized, exact remotely verified backup of this guard/map/owner proof.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import tempfile
import time
ROOT=Path('/workspace/ANDOLAN')
HERE=Path(__file__).resolve().parent
BUILD=Path('/workspace/scratch/yuga-continuation-W6-r1/package-successor-r2/build')
PUBLIC=Path('/workspace/scratch/yuga-continuation-W3-public-audit-r1')
SOURCE='79e5c15d8a3657e16fda67acb277b2406120dcd1'
TAG='yuga-desktop-polish-2026-10-18'
RELEASE_ID=416542426
OLD=ROOT/'games/yuga-native/docs/evidence/desktop-finish/continuation-oct18'
AUDIT=OLD/'W3-public-audit-r1/receipt.json'
AUDIT_SHA='55b5bc1e66c4837e22546a88b238f6366ec829c1d605ae99c0b04a9c4c1dda89'
QUAL=OLD/'W6-package-r2/qualification-receipt-uid-reviewed.json'
QUAL_SHA='e924d90af27dad48c96fcb99ad9bbbe2cfd84ac01899b2221491199baf00f400'
NAMES=('yuga-native-linux-x86_64.zip','yuga-native-windows-x86_64.zip')
ALL_NAMES=set(NAMES)|{'native-export-manifest.json','native-package-manifest.json','SHA256SUMS.txt'}
OWNER=HERE/'owner-release.json'

def need(value,message):
    if not value:raise ValueError(message)

def record(path):
    path=Path(path)
    need(path.is_absolute() and '..' not in path.parts and path.resolve()==path and stat.S_ISREG(path.lstat().st_mode),'Regular absolute nonsymlink file required: '+str(path))
    with path.open('rb') as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
    return {'bytes':path.stat().st_size,'sha256':digest}

def snapshot(path):
    before=path.lstat();result=record(path);s=path.lstat()
    need((before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns)==(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns),'File changed while hashing')
    return {**result,'device':s.st_dev,'inode':s.st_ino,'nlink':s.st_nlink,'mode':stat.S_IMODE(s.st_mode),'mtime_ns':s.st_mtime_ns,'allocated_bytes':s.st_blocks*512}

def valid_candidate(path):
    return path in {BUILD/name for name in NAMES}

def pair_check(candidate,retained,expected):
    need(candidate['nlink']==1,'Alias must have nlink1')
    need((candidate['device'],candidate['inode'])!=(retained['device'],retained['inode']),'Public recovery inode must be distinct')
    for row in (candidate,retained):need({k:row[k] for k in ('bytes','sha256')}==expected,'Exact public bytes required')

def audit_semantics(audit,qual,downloads,api):
    need(audit.get('passed') is True and audit.get('source_commit')==SOURCE and audit.get('release_id')==RELEASE_ID and audit.get('tag')==TAG and audit.get('public_assets')==5,'Exact passed public audit required')
    need(qual.get('passed') is True and qual.get('source_commit')==SOURCE and len(qual.get('checks',[]))==40 and all(x['passed'] is True for x in qual['checks']),'Exact 40-gate qualification required')
    expected=qual['five_assets'];need(set(expected)==ALL_NAMES,'Exact qualified five assets required')
    need(downloads.get('passed') is True and downloads.get('source_commit')==SOURCE and downloads.get('public_release_id')==RELEASE_ID and downloads.get('tag')==TAG,'Passed exact public download verification required')
    rows=audit['retained_downloads'];need(len(rows)==5 and {x['name'] for x in rows}==ALL_NAMES,'Exact public download census')
    need(downloads['downloads']==rows,'Public download records must agree')
    need(api['id']==RELEASE_ID and api['tag_name']==TAG and api['target_commitish']==SOURCE and api['draft'] is False and api['prerelease'] is True and api['published_at']==audit['published_at'],'Published release identity required')
    assets=api['assets'];need(len(assets)==5 and {x['name'] for x in assets}==ALL_NAMES,'Exact public API asset census')
    for row in rows:
        name=row['name'];value=expected[name];remote=next(x for x in assets if x['name']==name)
        need({k:row[k] for k in ('bytes','sha256')}==value,'Audit asset differs from qualification')
        url='https://github.com/occult-kranti/ANDOLAN/releases/download/'+TAG+'/'+name
        need(row['url']==url and remote['browser_download_url']==url and row['asset_id']==remote['id'] and remote['state']=='uploaded' and remote['size']==value['bytes'] and remote['digest']=='sha256:'+value['sha256'],'Exact public recovery identity/URL/digest required')
    return expected,rows

def build_core():
    need(record(AUDIT)['sha256']==AUDIT_SHA and record(QUAL)['sha256']==QUAL_SHA,'Immutable public audit and qualification receipts required')
    audit=json.loads(AUDIT.read_text());qual=json.loads(QUAL.read_text());proofs={str(AUDIT):record(AUDIT),str(QUAL):record(QUAL)}
    data={}
    for name in ('download-verification.json','publication-api.json','execution.json'):
        path=AUDIT.parent/name;need(record(path)==audit['files'][name],'Pinned public proof differs: '+name);proofs[str(path)]=record(path);data[name]=json.loads(path.read_text())
    need(data['execution.json']['exit_code']==0 and data['execution.json']['stdout']['passed'] is True,'Successful original public audit execution required')
    expected,downloads=audit_semantics(audit,qual,data['download-verification.json'],data['publication-api.json'])
    retained={};selected=[]
    for name,value in expected.items():
        path=PUBLIC/name;snap=snapshot(path);need({k:snap[k] for k in ('bytes','sha256')}==value,'Retained public file changed: '+name);retained[str(path)]=snap
    for name in NAMES:
        path=BUILD/name;need(valid_candidate(path),'Unsafe selection');snap=snapshot(path);recovery=PUBLIC/name;pair_check(snap,retained[str(recovery)],expected[name]);public=next(x for x in downloads if x['name']==name)
        selected.append({'path':str(path),**snap,'recovery':{'path':str(recovery),'bytes':snap['bytes'],'sha256':snap['sha256'],'mode':snap['mode'],'url':public['url'],'asset_id':public['asset_id']}})
    # Protect original build metadata, raw Linux resource pack, and actual extracted runtime.
    for name in ('native-export-manifest.json','native-package-manifest.json','SHA256SUMS.txt'):
        path=BUILD/name;need(record(path)==expected[name],'Protected build metadata changed');retained[str(path)]=snapshot(path)
    pck={k:qual['archives']['linux']['pck'][k] for k in ('bytes','sha256')}
    actual=Path('/workspace/scratch/yuga-continuation-W1-r1/package-r2-extracted')
    for path in (BUILD/'yuga-native-linux.pck',actual/'yuga-native.pck'):
        need(record(path)==pck,'Protected Linux PCK changed');retained[str(path)]=snapshot(path)
    runtime=actual/'godot';need(record(runtime)['sha256']=='e69af4f6f07876a83e49a02a86928db00993f88594c05ae589e4021d6916d54e','Protected actual runtime changed');retained[str(runtime)]=snapshot(runtime)
    need(len(selected)==2 and {r['path'] for r in selected}=={str(BUILD/n) for n in NAMES},'Exact two alias census')
    # End recheck detects inode/content changes while assembling the map.
    for name,value in retained.items():need(snapshot(Path(name))==value,'Retained file changed during audit')
    for row in selected:need(snapshot(Path(row['path']))=={k:v for k,v in row.items() if k not in ('path','recovery')},'Alias changed during audit')
    return {'schema':1,'source_commit':SOURCE,'tag':TAG,'release_id':RELEASE_ID,'proofs':proofs,'retained_files':retained,'files':selected,'count':2,'logical_bytes':sum(x['bytes'] for x in selected),'allocated_bytes':sum(x['allocated_bytes'] for x in selected),'scope':'Only two inactive original W6 build ZIP aliases; all five fresh public downloads, original build metadata/Linux PCK, actual extraction, caches/source/evidence/user state retained. Copy retained recovery path back to original alias and restore recorded mode to recover; exact public URL/asset ID also recorded.'}

def process_refs(paths):
    refs=[];inaccessible=[]
    for proc in Path('/proc').iterdir():
        if not proc.name.isdigit():continue
        try:
            links=[proc/'cwd',proc/'exe',*list((proc/'fd').iterdir())]
            for link in links:
                try:target=os.readlink(link)
                except FileNotFoundError:continue
                if target.removesuffix(' (deleted)') in paths:refs.append({'pid':int(proc.name),'kind':link.name,'path':target})
            for line in (proc/'maps').read_text().splitlines():
                parts=line.split(None,5)
                if len(parts)==6 and parts[5].removesuffix(' (deleted)') in paths:refs.append({'pid':int(proc.name),'kind':'maps','path':parts[5]})
        except (PermissionError,OSError):inaccessible.append(int(proc.name))
    return {'references':refs,'inaccessible_pids':sorted(set(inaccessible)),'limits':'Accessible /proc cwd/exe/fd/maps only; closed-file future use is covered by explicit W1/W3/W6/root owner release.'}

def owner_check(owner,plan_sha):
    need(owner.get('source_commit')==SOURCE and owner.get('release_id')==RELEASE_ID and owner.get('map_sha256')==plan_sha and owner.get('selected_paths')==[str(BUILD/n) for n in NAMES],'Exact owner release map/path binding required')
    need(all(owner.get(x) is True for x in ('root_released','w1_released','w3_released','w6_released')),'All four scoped owner releases required')

def backup_bound(commit,branch,plan):
    need(re.fullmatch('[0-9a-f]{40}',commit or '') and re.fullmatch(r'backup/yuga-desktop[A-Za-z0-9._/-]*',branch or '') and '..' not in branch,'Exact bounded backup commit/branch required')
    remote=subprocess.check_output(['git','--no-optional-locks','-C',str(ROOT),'ls-remote','--exit-code','origin','refs/heads/'+branch],text=True).split()
    need(remote==[commit,'refs/heads/'+branch],'Backup ref must be remotely verified')
    owner_check(json.loads(OWNER.read_text()),record(plan)['sha256'])
    for path in (Path(__file__).resolve(),plan,OWNER,AUDIT,QUAL):
        blob=subprocess.check_output(['git','--no-optional-locks','-C',str(ROOT),'cat-file','blob',commit+':'+path.relative_to(ROOT).as_posix()])
        need(hashlib.sha256(blob).hexdigest()==record(path)['sha256'],'Remote-backed recovery/guard/proof bytes differ: '+str(path))

def atomic_json(path,value,fresh=False):
    if fresh:need(not path.exists(),'Fresh output required')
    fd,name=tempfile.mkstemp(prefix='.'+path.name+'.',dir=path.parent)
    try:
        with os.fdopen(fd,'w') as f:json.dump(value,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
        if fresh:os.link(name,path);os.unlink(name)
        else:os.replace(name,path)
    finally:
        if os.path.exists(name):os.unlink(name)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--prepare',action='store_true');p.add_argument('--plan',type=Path,required=True);p.add_argument('--plan-sha256');p.add_argument('--report',type=Path);p.add_argument('--remove',action='store_true');p.add_argument('--backup-commit');p.add_argument('--backup-branch');a=p.parse_args()
    need(a.plan.parent==HERE and not a.plan.is_symlink(),'Direct owned plan path required')
    if a.prepare:
        need(not a.remove and not a.report and not a.plan.exists(),'Fresh prepare-only invocation required');core=build_core();core['process_probe']=process_refs({r['path'] for r in core['files']});core['prepared_unix']=time.time();atomic_json(a.plan,core,True);print(json.dumps({'map_sha256':record(a.plan)['sha256'],'count':2,'allocated_bytes':core['allocated_bytes'],'removed':0}));return 0
    need(a.report and a.report.parent==HERE and not a.report.exists() and record(a.plan)['sha256']==a.plan_sha256,'Pinned plan/fresh direct owned report required')
    result={'passed':False,'source_commit':SOURCE,'map_sha256':a.plan_sha256,'removal_requested':a.remove,'removed':[],'free_before':os.statvfs('/workspace').f_bavail*os.statvfs('/workspace').f_frsize}
    try:
        saved=json.loads(a.plan.read_text());current=build_core();need({k:saved[k] for k in current}==current,'Candidate/retained/proof identities drifted');probe=process_refs({r['path'] for r in current['files']});result['process_probe']=probe;need(not probe['references'],'Active process holds selected alias')
        owner_check(json.loads(OWNER.read_text()),a.plan_sha256)
        if a.remove:
            backup_bound(a.backup_commit,a.backup_branch,a.plan);result.update(backup_commit=a.backup_commit,backup_branch=a.backup_branch);atomic_json(a.report,result,True)
            for row in current['files']:
                # Both retained public ZIPs remain verified before each exact unlink.
                for name,value in current['retained_files'].items():need(snapshot(Path(name))==value,'Protected recovery/output changed before unlink')
                path=Path(row['path']);need(valid_candidate(path) and snapshot(path)=={k:v for k,v in row.items() if k not in ('path','recovery')},'Selected alias identity changed before unlink');path.unlink();result['removed'].append(row);atomic_json(a.report,result)
        result['passed']=True;result['verified_files']=2;result['allocated_bytes_selected']=current['allocated_bytes'];result['allocated_bytes_removed']=sum(x['allocated_bytes'] for x in result['removed'])
        for name,value in current['retained_files'].items():need(snapshot(Path(name))==value,'Protected output changed after checks/removal')
    except Exception as error:result['passed']=False;result['failure']=repr(error)
    result['free_after']=os.statvfs('/workspace').f_bavail*os.statvfs('/workspace').f_frsize;result['finished_unix']=time.time();atomic_json(a.report,result,fresh=not a.report.exists());print(json.dumps({k:result.get(k) for k in ('passed','verified_files','allocated_bytes_removed','failure')}));return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
