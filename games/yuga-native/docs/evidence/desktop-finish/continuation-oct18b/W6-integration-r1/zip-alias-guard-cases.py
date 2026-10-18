#!/usr/bin/env python3
"""Finite local source/predicate counterexamples. Never calls Git or removes files."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import tempfile
from unittest.mock import patch
P=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('aliases',P/'zip-aliases.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
results=[]
def case(name,fn,accept=False):
    try:fn();passed=accept
    except (ValueError,FileNotFoundError,KeyError):passed=not accept
    results.append({'name':name,'passed':passed})
    if not passed:raise AssertionError(name)
a=json.loads(m.AUDIT.read_text());q=json.loads(m.QUAL.read_text());d=json.loads((m.AUDIT.parent/'download-verification.json').read_text());api=json.loads((m.AUDIT.parent/'publication-api.json').read_text())
case('sealed actual public proof admitted',lambda:m.audit_semantics(a,q,d,api),True)
def mutate(which,key,value):
    values=copy.deepcopy([a,q,d,api]);values[which][key]=value;m.audit_semantics(*values)
for name,which,key,value in [
 ('failed audit',0,'passed',False),('wrong source',0,'source_commit','0'*40),('wrong release',0,'release_id',1),('wrong tag',0,'tag','old'),('failed qualification',1,'passed',False),('missing qualification checks',1,'checks',[]),('missing public asset',0,'retained_downloads',a['retained_downloads'][:-1]),('failed download',2,'passed',False),('wrong public release',2,'public_release_id',1),('draft still hidden',3,'draft',True),('wrong API source',3,'target_commitish','0'*40),('missing API asset',3,'assets',api['assets'][:-1])]:case(name,lambda w=which,k=key,v=value:mutate(w,k,v))
def alter_asset(field,value):
    values=copy.deepcopy([a,q,d,api]);values[3]['assets'][0][field]=value;m.audit_semantics(*values)
for key,value in [('digest','sha256:'+'0'*64),('size',0),('state','new'),('id',0),('browser_download_url','https://example.invalid/file')]:case('reject API '+key,lambda k=key,v=value:alter_asset(k,v))
core=json.loads((P/'zip-alias-map.json').read_text());row=core['files'][0];expected={k:row[k] for k in ('bytes','sha256')};candidate={k:v for k,v in row.items() if k not in ('path','recovery')};retained=core['retained_files'][row['recovery']['path']]
case('actual distinct aliases admitted',lambda:m.pair_check(candidate,retained,expected),True)
case('hardlinked candidate rejects',lambda:m.pair_check({**candidate,'nlink':2},retained,expected))
case('same recovery inode rejects',lambda:m.pair_check(candidate,{**retained,'device':candidate['device'],'inode':candidate['inode']},expected))
case('changed candidate bytes rejects',lambda:m.pair_check({**candidate,'sha256':'0'*64},retained,expected))
case('changed retained bytes rejects',lambda:m.pair_check(candidate,{**retained,'bytes':0},expected))
case('exact selection accepted',lambda:m.need(m.valid_candidate(m.BUILD/m.NAMES[0]),'selection'),True)
for path in [m.PUBLIC/m.NAMES[0],m.BUILD/'yuga-native-linux.pck',m.BUILD/'native-export-manifest.json',m.BUILD/'other.zip',m.BUILD/'x'/m.NAMES[0],m.BUILD/'..'/m.NAMES[0]]:case('unsafe candidate '+str(path),lambda p=path:m.need(m.valid_candidate(p),'unsafe'))
owner=json.loads(m.OWNER.read_text());plan=P/'zip-alias-map.json';plan_sha=m.record(plan)['sha256'];case('all owner releases admitted',lambda:m.owner_check(owner,plan_sha),True)
for key in ['root_released','w1_released','w3_released','w6_released']:case('missing '+key,lambda k=key:m.owner_check({**owner,k:False},plan_sha))
case('wrong owner map',lambda:m.owner_check(owner,'0'*64))
case('extra owner path',lambda:m.owner_check({**owner,'selected_paths':owner['selected_paths']+['/tmp/x']},plan_sha))
with tempfile.TemporaryDirectory(prefix='zip-alias-guards-',dir='/workspace/scratch/yuga-next-W6-r1') as temp:
    t=Path(temp);f=t/'regular';f.write_bytes(b'fixture');(t/'symlink').symlink_to(f)
    case('regular fixture accepts',lambda:m.record(f),True);case('symlink rejects',lambda:m.record(t/'symlink'));case('missing rejects',lambda:m.record(t/'missing'))
    m.atomic_json(t/'atomic.json',{'initial':True},True);case('atomic no clobber rejects',lambda:m.atomic_json(t/'atomic.json',{},True));m.atomic_json(t/'atomic.json',{'updated':True});case('atomic replacement valid',lambda:m.need(json.loads((t/'atomic.json').read_text())=={'updated':True},'atomic'),True)
commit='c'*40;branch='backup/yuga-desktop-oct18b-zip-aliases'
def fake(cmd,**kw):
    if 'ls-remote' in cmd:return commit+'\trefs/heads/'+branch+'\n'
    rel=cmd[-1].split(':',1)[1];return (m.ROOT/rel).read_bytes()
with patch.object(m.subprocess,'check_output',side_effect=fake):case('matching remote backed proof accepted',lambda:m.backup_bound(commit,branch,plan),True)
with patch.object(m.subprocess,'check_output',return_value='0'*40+'\trefs/heads/'+branch+'\n'):case('wrong remote backup rejects',lambda:m.backup_bound(commit,branch,plan))
with patch.object(m.subprocess,'check_output',side_effect=lambda cmd,**kw:fake(cmd,**kw) if 'ls-remote' in cmd else b'wrong blob'):case('wrong backed blob rejects',lambda:m.backup_bound(commit,branch,plan))
case('invalid backup branch rejects',lambda:m.backup_bound(commit,'backup/../wrong',plan))
report={'passed':all(x['passed'] for x in results),'checks':results,'total':len(results),'engines':0,'network_calls':0,'git_calls':0,'actual_files_removed':0,'scope':'Pure predicates, synthetic temporary regular files/atomic outputs, mocked remote backup reads. Actual candidate or retained bytes are never edited/removed.'};m.atomic_json(P/'guard-cases.json',report,True);print(json.dumps({'passed':report['passed'],'checks':len(results)}))
