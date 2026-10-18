#!/usr/bin/env python3
"""Only the inactive79e5 W6 build Linux raw PCK; public ZIP and actual PCK stay."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import time
import zipfile
ROOT=Path('/workspace/ANDOLAN')
HERE=Path(__file__).resolve().parent
BASE=HERE.parent/'zip-aliases.py'
BASE_SHA='b551cbd45bff003cb26c95017518eded3bb92cf15b119d99f2e5c65ca6beadbe'
# Admit the immutable local helper bytes before importing any of its Python.
if BASE.resolve()!=BASE or BASE.is_symlink() or hashlib.sha256(BASE.read_bytes()).hexdigest()!=BASE_SHA:
    raise ValueError('Exact previously reviewed helper required before import')
spec=importlib.util.spec_from_file_location('sealed_alias_guard',BASE)
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
SOURCE=base.SOURCE
AUDIT=base.AUDIT
QUAL=base.QUAL
OWNER=HERE/'owner-release.json'
CANDIDATE=base.BUILD/'yuga-native-linux.pck'
ARCHIVE=base.PUBLIC/'yuga-native-linux-x86_64.zip'
MEMBER='yuga-native-linux-x86_64/yuga-native.pck'
ACTUAL=Path('/workspace/scratch/yuga-continuation-W1-r1/package-r2-extracted')
need,record,snapshot,atomic_json=base.need,base.record,base.snapshot,base.atomic_json

def valid_candidate(path):return path==CANDIDATE

def build_core():
    need(record(BASE)['sha256']==BASE_SHA,'Reviewed helper changed')
    need(record(AUDIT)['sha256']==base.AUDIT_SHA and record(QUAL)['sha256']==base.QUAL_SHA,'Exact old public/qualified receipts required')
    audit=json.loads(AUDIT.read_text());qual=json.loads(QUAL.read_text());proofs={str(BASE):record(BASE),str(AUDIT):record(AUDIT),str(QUAL):record(QUAL)};data={}
    for name in ('download-verification.json','publication-api.json','execution.json'):
        path=AUDIT.parent/name;need(record(path)==audit['files'][name],'Immutable audit proof changed');proofs[str(path)]=record(path);data[name]=json.loads(path.read_text())
    need(data['execution.json']['exit_code']==0 and data['execution.json']['stdout']['passed'] is True,'Original public audit execution must pass')
    expected,_=base.audit_semantics(audit,qual,data['download-verification.json'],data['publication-api.json'])
    retained={}
    for name,value in expected.items():
        f=base.PUBLIC/name;need(record(f)==value,'Retained public download changed');retained[str(f)]=snapshot(f)
    pck={key:qual['archives']['linux']['pck'][key]for key in ('bytes','sha256')}
    for name in ('native-export-manifest.json','native-package-manifest.json','SHA256SUMS.txt'):
        f=base.BUILD/name;need(record(f)==expected[name],'Protected build metadata changed');retained[str(f)]=snapshot(f)
    need(record(ACTUAL/'yuga-native.pck')==pck,'Protected actual extracted PCK changed');retained[str(ACTUAL/'yuga-native.pck')]=snapshot(ACTUAL/'yuga-native.pck')
    need(record(ACTUAL/'godot')['sha256']=='e69af4f6f07876a83e49a02a86928db00993f88594c05ae589e4021d6916d54e','Protected actual runtime changed');retained[str(ACTUAL/'godot')]=snapshot(ACTUAL/'godot')
    selected=snapshot(CANDIDATE);need(valid_candidate(CANDIDATE),'Exact bounded target required');base.pair_check(selected,retained[str(ACTUAL/'yuga-native.pck')],pck)
    with zipfile.ZipFile(ARCHIVE) as archive:
        names=archive.namelist();need(len(names)==len(set(names)) and set(names)==set(qual['archives']['linux']['member_records']),'Exact retained ZIP census required')
        entry=archive.getinfo(MEMBER);need(not entry.is_dir() and entry.file_size==pck['bytes'] and (entry.external_attr>>16)&0o170000==0o100000,'Regular exact recovery member required')
        digest=hashlib.sha256();size=0
        with archive.open(entry) as stream:
            for block in iter(lambda:stream.read(1024*1024),b''):digest.update(block);size+=len(block)
        need({'bytes':size,'sha256':digest.hexdigest()}==pck,'Recovery member exact bytes required')
        recovery={'archive':str(ARCHIVE),'archive_sha256':expected[ARCHIVE.name]['sha256'],'member':MEMBER,'bytes':size,'sha256':digest.hexdigest(),'crc32':f'{entry.CRC:08x}','member_mode':(entry.external_attr>>16)&0o777,'restore_mode':selected['mode'],'public_url':'https://github.com/occult-kranti/ANDOLAN/releases/download/'+base.TAG+'/'+ARCHIVE.name}
    row={'path':str(CANDIDATE),**selected,'recovery':recovery}
    for name,value in retained.items():need(snapshot(Path(name))==value,'Protected retained file changed during check')
    need(snapshot(CANDIDATE)==selected,'Candidate changed during check')
    return {'schema':1,'source_commit':SOURCE,'release_id':base.RELEASE_ID,'proofs':proofs,'retained_files':retained,'files':[row],'count':1,'logical_bytes':selected['bytes'],'allocated_bytes':selected['allocated_bytes'],'scope':'Only old inactive W6 build Linux raw PCK. Retain all public files/ZIPs, W1 extracted PCK/runtime, build metadata, caches/source/evidence/user state. Recover by reading the exact retained ZIP member into original path and restoring recorded mode; verify full bytes/hash before use.'}

def owner_check(owner,map_sha):
    need(owner.get('source_commit')==SOURCE and owner.get('release_id')==base.RELEASE_ID and owner.get('map_sha256')==map_sha and owner.get('selected_paths')==[str(CANDIDATE)],'Exact single-target owner map binding required')
    need(all(owner.get(key) is True for key in ('root_released','w1_released','w3_retained_custody','w6_released')),'All exact owner releases/custody required')

def backup_bound(commit,branch,plan):
    need(re.fullmatch('[0-9a-f]{40}',commit or '') and re.fullmatch(r'backup/yuga-desktop[A-Za-z0-9._/-]*',branch or '') and '..' not in branch,'Bounded exact backup identity required')
    remote=subprocess.check_output(['git','--no-optional-locks','-C',str(ROOT),'ls-remote','--exit-code','origin','refs/heads/'+branch],text=True).split();need(remote==[commit,'refs/heads/'+branch],'Exact backup ref must be remotely verified')
    owner_check(json.loads(OWNER.read_text()),record(plan)['sha256'])
    for path in (Path(__file__).resolve(),plan,OWNER,BASE,AUDIT,QUAL):
        blob=subprocess.check_output(['git','--no-optional-locks','-C',str(ROOT),'cat-file','blob',commit+':'+path.relative_to(ROOT).as_posix()]);need(hashlib.sha256(blob).hexdigest()==record(path)['sha256'],'Remote-backed helper/map/owner/proof differs')

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--prepare',action='store_true');p.add_argument('--plan',type=Path,required=True);p.add_argument('--plan-sha256');p.add_argument('--report',type=Path);p.add_argument('--remove',action='store_true');p.add_argument('--backup-commit');p.add_argument('--backup-branch');a=p.parse_args();need(a.plan.parent==HERE and not a.plan.is_symlink(),'Direct owned plan required')
    if a.prepare:
        need(not a.remove and not a.report and not a.plan.exists(),'Fresh preparation only');core=build_core();core['process_probe']=base.process_refs({str(CANDIDATE)});core['prepared_unix']=time.time();atomic_json(a.plan,core,True);print(json.dumps({'map_sha256':record(a.plan)['sha256'],'allocated_bytes':core['allocated_bytes'],'removed':0}));return 0
    need(a.report and a.report.parent==HERE and not a.report.exists() and record(a.plan)['sha256']==a.plan_sha256,'Exact map/fresh direct report required')
    result={'passed':False,'map_sha256':a.plan_sha256,'removal_requested':a.remove,'removed':[],'free_before':os.statvfs('/workspace').f_bavail*os.statvfs('/workspace').f_frsize}
    try:
        saved=json.loads(a.plan.read_text());current=build_core();need({k:saved[k]for k in current}==current,'Candidate/retained/proof identities drifted');probe=base.process_refs({str(CANDIDATE)});result['process_probe']=probe;need(not probe['references'],'Active selected-file process reference');owner_check(json.loads(OWNER.read_text()),a.plan_sha256)
        if a.remove:
            backup_bound(a.backup_commit,a.backup_branch,a.plan);result.update(backup_commit=a.backup_commit,backup_branch=a.backup_branch);atomic_json(a.report,result,True)
            for name,value in current['retained_files'].items():need(snapshot(Path(name))==value,'Protected recovery file changed before unlink')
            row=current['files'][0];need(valid_candidate(Path(row['path'])) and snapshot(CANDIDATE)=={k:v for k,v in row.items()if k not in ('path','recovery')},'Exact candidate changed before unlink');CANDIDATE.unlink();result['removed'].append(row);atomic_json(a.report,result)
        for name,value in current['retained_files'].items():need(snapshot(Path(name))==value,'Protected file changed after check/unlink')
        result.update(passed=True,verified_files=1,allocated_bytes_selected=current['allocated_bytes'],allocated_bytes_removed=sum(x['allocated_bytes']for x in result['removed']))
    except Exception as error:result['failure']=repr(error)
    result['free_after']=os.statvfs('/workspace').f_bavail*os.statvfs('/workspace').f_frsize;result['finished_unix']=time.time();atomic_json(a.report,result,not a.report.exists());print(json.dumps({k:result.get(k)for k in ('passed','verified_files','allocated_bytes_removed','failure')}));return 0 if result['passed']else 1
if __name__=='__main__':raise SystemExit(main())
