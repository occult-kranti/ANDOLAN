#!/usr/bin/env python3
"""Exact r2 ZIP-backed generated duplicates only; prepare/check by default.

Removal additionally requires explicit --remove and a remote-verified backup
of this guard, the exact plan and the qualified receipt. No directories removed.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import time
import zipfile
ROOT=Path('/workspace/ANDOLAN')
HERE=Path(__file__).resolve().parent
OWNER_RELEASE=HERE/'owner-release.json'
ARTIFACT=Path('/workspace/scratch/yuga-continuation-W6-r1/package-successor-r2')
BUILD=ARTIFACT/'build'
COMMIT='79e5c15d8a3657e16fda67acb277b2406120dcd1'
QUALIFICATION=ROOT/'games/yuga-native/docs/evidence/desktop-finish/continuation-oct18/W6-package-r2/qualification-receipt-uid-reviewed.json'
QUALIFICATION_SHA='e924d90af27dad48c96fcb99ad9bbbe2cfd84ac01899b2221491199baf00f400'

def record(path):
    if path.resolve()!=path.absolute() or not stat.S_ISREG(path.lstat().st_mode):
        raise ValueError('Nonregular/symlink input: '+str(path))
    h=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(1048576),b''):h.update(block)
    return {'bytes':path.stat().st_size,'sha256':h.hexdigest()}

def member_record(archive,name):
    h,size=hashlib.sha256(),0
    with archive.open(name) as stream:
        for block in iter(lambda:stream.read(1048576),b''):h.update(block);size+=len(block)
    return {'bytes':size,'sha256':h.hexdigest()}

def snapshot(path):
    value=record(path);s=path.stat()
    if s.st_nlink!=1:raise ValueError('Selected duplicate has shared inodes: '+str(path))
    return {**value,'device':s.st_dev,'inode':s.st_ino,'mode':stat.S_IMODE(s.st_mode),
            'mtime_ns':s.st_mtime_ns,'nlink':s.st_nlink,'allocated_bytes':s.st_blocks*512}

def valid_candidate(path):
    try:relative=path.relative_to(BUILD)
    except ValueError:return False
    return (path.absolute()==path and '..' not in path.parts and
            (relative.as_posix()=='yuga-native-windows.pck' or
             (len(relative.parts)>1 and relative.parts[0] in ['yuga-native-linux-x86_64','yuga-native-windows-x86_64'])))

def build_core():
    if record(QUALIFICATION)['sha256']!=QUALIFICATION_SHA:raise ValueError('Exact sealed package qualification required')
    q=json.loads(QUALIFICATION.read_text())
    if q.get('passed') is not True or q.get('source_commit')!=COMMIT or len(q.get('checks',[]))!=40 or not all(c['passed'] for c in q['checks']):raise ValueError('Qualified source/40 gates required')
    retained={};rows=[]
    for name,value in q['five_assets'].items():
        path=BUILD/name
        if record(path)!=value:raise ValueError('Retained qualified file changed: '+name)
        retained[str(path)]=value
    retained[str(BUILD/'yuga-native-linux.pck')]={k:q['archives']['linux']['pck'][k] for k in ['bytes','sha256']}
    if record(BUILD/'yuga-native-linux.pck')!=retained[str(BUILD/'yuga-native-linux.pck')]:raise ValueError('Retained Linux raw PCK differs')
    for platform in ['linux','windows']:
        prefix='yuga-native-'+platform+'-x86_64';staging=BUILD/prefix;archive_path=BUILD/(prefix+'.zip')
        expected=q['archives'][platform]['member_records']
        found={p.relative_to(BUILD).as_posix() for p in staging.rglob('*') if p.is_file()}
        if found!=set(expected) or any(p.is_symlink() for p in staging.rglob('*')):raise ValueError('Staging member census or symlink changed')
        with zipfile.ZipFile(archive_path) as archive:
            if len(archive.namelist())!=len(set(archive.namelist())) or set(archive.namelist())!=set(expected):raise ValueError('Exact ZIP member census required')
            for member,value in sorted(expected.items()):
                path=BUILD/member
                if not valid_candidate(path):raise ValueError('Unsafe candidate')
                info=archive.getinfo(member);actual=snapshot(path)
                if {k:actual[k] for k in ['bytes','sha256']}!=value or member_record(archive,member)!=value:raise ValueError('ZIP-backed duplicate bytes differ')
                rows.append({'path':str(path),**actual,'recovery':{'archive':str(archive_path),'archive_sha256':q['five_assets'][archive_path.name]['sha256'],'member':member,'crc32':f'{info.CRC:08x}','member_mode':stat.S_IMODE(info.external_attr>>16)}})
            if platform=='windows':
                path=BUILD/'yuga-native-windows.pck';actual=snapshot(path);member=prefix+'/yuga-native.pck';value=expected[member]
                if {k:actual[k] for k in ['bytes','sha256']}!=value:raise ValueError('Windows raw PCK differs from exact ZIP member')
                info=archive.getinfo(member);rows.append({'path':str(path),**actual,'recovery':{'archive':str(archive_path),'archive_sha256':q['five_assets'][archive_path.name]['sha256'],'member':member,'crc32':f'{info.CRC:08x}','member_mode':stat.S_IMODE(info.external_attr>>16)}})
    if len({r['path'] for r in rows})!=len(rows) or any(not valid_candidate(Path(r['path'])) for r in rows):raise ValueError('Duplicate/unsafe selected paths')
    for name,value in retained.items():
        if record(Path(name))!=value:raise ValueError('Retained file changed during check')
    return {'schema':1,'source_commit':COMMIT,'artifact':str(ARTIFACT),'qualification':{'path':str(QUALIFICATION),'sha256':QUALIFICATION_SHA},'retained_files':retained,'files':rows,'count':len(rows),'logical_bytes':sum(r['bytes'] for r in rows),'allocated_bytes':sum(r['allocated_bytes'] for r in rows),'directories_retained':True,'scope':'Only new r2 expanded staging regular files and duplicate Windows raw PCK. Both ZIPs/Linux raw PCK/manifests/proofs/logs/cache/source/actual extraction/user state remain protected. Recover exact selected bytes from the retained qualified ZIP member, then apply recorded filesystem mode. No prior-output cleanup.'}

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
        except (PermissionError,OSError):inaccessible.append(int(proc.name))
    return {'references':refs,'inaccessible_pids':sorted(inaccessible)}

def backup_bound(commit,branch,plan):
    if not re.fullmatch('[0-9a-f]{40}',commit or '') or not re.fullmatch(r'backup/yuga-desktop[A-Za-z0-9._/-]*',branch or '') or '..' in branch:raise ValueError('Exact backup commit and bounded branch required')
    remote=subprocess.check_output(['git','-C',str(ROOT),'ls-remote','--exit-code','origin','refs/heads/'+branch],text=True).split()
    if remote!=[commit,'refs/heads/'+branch]:raise ValueError('Exact backup branch is not remotely verified')
    release=json.loads(OWNER_RELEASE.read_text())
    if (release.get('source_commit')!=COMMIT or release.get('map_sha256')!=record(plan)['sha256'] or
            release.get('selected_files')!=82 or release.get('w1_released') is not True or release.get('w6_released') is not True):raise ValueError('Exact scoped W1/W6 owner releases required')
    for path in [Path(__file__).resolve(),plan,QUALIFICATION,OWNER_RELEASE]:
        relative=path.relative_to(ROOT).as_posix();blob=subprocess.check_output(['git','-C',str(ROOT),'cat-file','blob',commit+':'+relative])
        if hashlib.sha256(blob).hexdigest()!=record(path)['sha256']:raise ValueError('Remote-backed map/guard/qualification bytes differ: '+relative)

def dump_new(path,value):
    with path.open('x') as stream:json.dump(value,stream,indent=2);stream.write('\n')

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--prepare',action='store_true');p.add_argument('--plan',type=Path,required=True);p.add_argument('--plan-sha256');p.add_argument('--report',type=Path);p.add_argument('--remove',action='store_true');p.add_argument('--backup-commit');p.add_argument('--backup-branch');a=p.parse_args()
    if a.plan.resolve().parent!=HERE or a.plan.is_symlink():p.error('Plan must be a direct owned evidence file')
    if a.prepare:
        if a.remove or a.report or a.plan.exists():p.error('Fresh map-only preparation required')
        core=build_core();core['process_probe']=process_refs({r['path'] for r in core['files']});core['prepared_unix']=time.time();dump_new(a.plan,core);print(json.dumps({'plan':str(a.plan),'sha256':record(a.plan)['sha256'],'count':core['count'],'allocated_bytes':core['allocated_bytes'],'removed':0}));return 0
    if not a.report or a.report.resolve().parent!=HERE or a.report.exists() or record(a.plan)['sha256']!=a.plan_sha256:p.error('Exact plan hash and fresh owned verification report required')
    saved=json.loads(a.plan.read_text());current=build_core();result={'plan_sha256':a.plan_sha256,'source_commit':COMMIT,'removal_requested':a.remove,'removed':[],'passed':False}
    try:
        if {k:saved[k] for k in current}!=current:raise ValueError('Exact candidate/source/retained/recovery identities changed')
        probe=process_refs({r['path'] for r in current['files']});result['process_probe']=probe
        if probe['references']:raise ValueError('An accessible process owns a selected file')
        if a.remove:
            backup_bound(a.backup_commit,a.backup_branch,a.plan);result['backup_commit']=a.backup_commit;result['backup_branch']=a.backup_branch
            for name,value in current['retained_files'].items():
                if record(Path(name))!=value:raise ValueError('Retained recovery file changed before removal')
            dump_new(a.report,result)
            for row in current['files']:
                path=Path(row['path'])
                if not valid_candidate(path) or snapshot(path)!={k:row[k] for k in ['bytes','sha256','device','inode','mode','mtime_ns','nlink','allocated_bytes']}:raise ValueError('Candidate changed before unlink')
                path.unlink();result['removed'].append(row);a.report.write_text(json.dumps(result,indent=2)+'\n')
        result['passed']=True;result['verified_files']=current['count'];result['allocated_bytes_selected']=current['allocated_bytes'];result['allocated_bytes_removed']=sum(r['allocated_bytes'] for r in result['removed'])
    except Exception as error:result['failure']=repr(error)
    result['finished_unix']=time.time()
    if a.report.exists():a.report.write_text(json.dumps(result,indent=2)+'\n')
    else:dump_new(a.report,result)
    print(json.dumps({k:result.get(k) for k in ['passed','verified_files','allocated_bytes_removed','failure']}));return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
