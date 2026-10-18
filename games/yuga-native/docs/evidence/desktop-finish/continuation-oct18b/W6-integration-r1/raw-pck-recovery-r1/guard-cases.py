#!/usr/bin/env python3
"""Finite no-delete controls for the exact raw PCK recovery guard."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from unittest.mock import patch
P=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('raw_pck_guard',P/'raw-linux-pck.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
checks=[]
def case(name,fn,accept=False):
    try:fn();ok=accept
    except (ValueError,KeyError,FileNotFoundError):ok=not accept
    checks.append({'name':name,'passed':ok})
    if not ok:raise AssertionError(name)
plan=P/'recovery-map.json';saved=json.loads(plan.read_text());map_sha=m.record(plan)['sha256'];core=m.build_core();case('actual exact onePCK and retained member proof stable',lambda:m.need({k:saved[k]for k in core}==core and core['count']==1,'core'),True)
case('only exact old raw PCK admitted',lambda:m.need(m.valid_candidate(m.CANDIDATE),'candidate'),True)
for path in (m.ARCHIVE,m.ACTUAL/'yuga-native.pck',m.ACTUAL/'godot',m.base.BUILD/'native-export-manifest.json',m.base.BUILD/'yuga-native-windows.pck',m.base.BUILD/'other.pck',m.base.BUILD/'..'/'yuga-native-linux.pck'):
    case('reject protected or unrelated path '+str(path),lambda p=path:m.need(m.valid_candidate(p),'unsafe'))
row=core['files'][0];candidate={k:v for k,v in row.items()if k not in ('path','recovery')};actual=core['retained_files'][str(m.ACTUAL/'yuga-native.pck')];expected={k:row[k]for k in ('bytes','sha256')}
case('private distinct exact PCK pair accepted',lambda:m.base.pair_check(candidate,actual,expected),True)
case('shared candidate inode rejects',lambda:m.base.pair_check({**candidate,'nlink':2},actual,expected))
case('candidate bytes mismatch rejects',lambda:m.base.pair_check({**candidate,'sha256':'0'*64},actual,expected))
case('same actual-runtime PCK inode rejects',lambda:m.base.pair_check(candidate,{**actual,'device':candidate['device'],'inode':candidate['inode']},expected))
owner={'source_commit':m.SOURCE,'release_id':m.base.RELEASE_ID,'map_sha256':map_sha,'selected_paths':[str(m.CANDIDATE)],'root_released':True,'w1_released':True,'w3_retained_custody':True,'w6_released':True}
case('all exact owner releases accept',lambda:m.owner_check(owner,map_sha),True)
for key in ('root_released','w1_released','w3_retained_custody','w6_released'):case('missing '+key+' rejects',lambda k=key:m.owner_check({**owner,k:False},map_sha))
case('wrong owner map rejects',lambda:m.owner_check(owner,'0'*64))
case('extra target owner selection rejects',lambda:m.owner_check({**owner,'selected_paths':owner['selected_paths']+[str(m.ARCHIVE)]},map_sha))
with m.CANDIDATE.open('rb'):
    probe=m.base.process_refs({str(m.CANDIDATE)});case('accessible own open-file reference observed',lambda:m.need(bool(probe['references']),'probe'),True)
commit='d'*40;branch='backup/yuga-desktop-raw-pck-2026-10-18b'
def fake(cmd,**kw):
    if 'ls-remote'in cmd:return commit+'\trefs/heads/'+branch+'\n'
    return (m.ROOT/cmd[-1].split(':',1)[1]).read_bytes()
# Backup admission's local owner binding is mocked only for these transport
# predicates; its positive/negative field checks are independently above.
with patch.object(m,'owner_check',return_value=None),patch.object(m.OWNER.__class__,'read_text',autospec=True,side_effect=lambda p,*a,**k:'{}' if p==m.OWNER else Path.read_text(p,*a,**k)):
    with patch.object(m.subprocess,'check_output',return_value='0'*40+'\trefs/heads/'+branch+'\n'):case('wrong remote commit rejects',lambda:m.backup_bound(commit,branch,plan))
case('unsafe backup branch rejects before network',lambda:m.backup_bound(commit,'backup/../bad',plan))
result={'passed':all(x['passed']for x in checks),'count':len(checks),'checks':checks,'engines':0,'network_calls':0,'git_calls':0,'files_deleted':0,'scope':'Exact current read-only proof plus selector/private-inode/owner-map/open-file/remote-identity predicates. No candidate or retained bytes changed.'};m.atomic_json(P/'guard-cases.json',result,True);print(json.dumps({'passed':result['passed'],'count':result['count']}))
