#!/usr/bin/env python3
"""Finite exact75 UID-warning mutation controls; no engine or archive changes."""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import tempfile
from unittest.mock import patch
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('uid_qualifier',HERE/'qualify-successor-package-uid-aware.py');q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)
area=Path('/workspace/scratch/yuga-continuation-W6-r1');out=area/'package-successor-r2';prep=json.loads((area/'package-successor-r2-preparation.json').read_text());expected=json.loads((HERE/'uid-regeneration-allowlist.json').read_text());phases={p:json.loads((out/(p+'-execution.json')).read_text()) for p in ['export','package']};runtime={v['uid'] for v in json.loads((out/'build/native-export-manifest.json').read_text())['runtime_uids']['sidecars'].values()};diagnostics={'build/export-linux.log':[r['line'] for r in expected['warnings']]};checks=[]
def check(name,value):
 checks.append({'name':name,'passed':bool(value)})
 if not value:raise AssertionError(name)
def rejected(name,fn):
 try:fn()
 except (ValueError,FileNotFoundError):check(name,True)
 else:check(name,False)
external=[]
def forbidden(*args,**kwargs):external.append(True);raise AssertionError('External operation forbidden')
with tempfile.TemporaryDirectory(prefix='w6-uid-qualifier-guards-',dir=area) as temporary:
 root=Path(temporary);repo=root/'artifact';canonical=root/'canonical'
 for row in expected['warnings']:
  for base,rel in [(repo,row['source_path']),(repo,row['uid_path']),(canonical,row['uid_path'])]:
   target=base/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(out/'ANDOLAN'/rel,target)
 def admit(d=None,e=None,p=None,ph=None,rt=None):
  return q.admit_uid_regeneration(d if d is not None else diagnostics,e if e is not None else expected,repo,canonical,p if p is not None else prep,expected['preparation_sha256'],ph if ph is not None else phases,rt if rt is not None else runtime)
 with patch.object(subprocess,'run',forbidden),patch.object(subprocess,'Popen',forbidden),patch.object(subprocess,'check_output',forbidden),patch.object(socket,'socket',forbidden):
  check('exact75 actual-input bindings accepted in private copies',len(admit())==75)
  for label,change in [('unknown warning',lambda d:d['build/export-linux.log'].__setitem__(0,'WARNING: unknown')),('engine error',lambda d:d['build/export-linux.log'].append('ERROR: synthetic')),('script error',lambda d:d['build/export-linux.log'].append('SCRIPT ERROR: synthetic')),('missing warning',lambda d:d['build/export-linux.log'].pop()),('duplicate warning',lambda d:d['build/export-linux.log'].__setitem__(1,d['build/export-linux.log'][0])),('reordered warning',lambda d:d['build/export-linux.log'].reverse()),('relocated warning',lambda d:d.update({'build/export-windows.log':d.pop('build/export-linux.log')}))]:
   d=copy.deepcopy(diagnostics);change(d);rejected('reject '+label,lambda d=d:admit(d=d))
  for field,bad in [('source_commit','0'*40),('preparation_sha256','0'*64),('approved_exclusion_sha256','0'*64),('expected_warning_count',74),('log','build/export-windows.log')]:
   e=copy.deepcopy(expected);e[field]=bad;rejected('reject observation '+field,lambda e=e:admit(e=e))
  for field,bad in [('source_blob','0'*40),('source_sha256','0'*64),('uid','uid://abc'),('metadata',{'bytes':1,'sha256':'0'*64})]:
   e=copy.deepcopy(expected);e['warnings'][0][field]=bad;rejected('reject exact row '+field,lambda e=e:admit(e=e))
  e=copy.deepcopy(expected);e['warnings'][0]['line']='WARNING: Missing .uid file for path "res://scripts/player.gd". The file was re-created from cache.';d=copy.deepcopy(diagnostics);d['build/export-linux.log'][0]=e['warnings'][0]['line'];rejected('reject runtime UID warning even with matched observation',lambda:admit(d=d,e=e))
  e=copy.deepcopy(expected);e['warnings'][0]['line']='WARNING: Missing .uid file for path "res://tests/../../scripts/player.gd". The file was re-created from cache.';d=copy.deepcopy(diagnostics);d['build/export-linux.log'][0]=e['warnings'][0]['line'];rejected('reject traversal warning even with matched observation',lambda:admit(d=d,e=e))
  first=expected['warnings'][0];p=copy.deepcopy(prep);p['exclude_text']=p['exclude_text'].replace('/'+first['uid_path']+'\n','');rejected('reject sidecar absent from exact approved exclusions',lambda:admit(p=p))
  p=copy.deepcopy(prep);p['entries'].append({'path':first['uid_path']});rejected('reject tracked UID metadata admission',lambda:admit(p=p))
  ph=copy.deepcopy(phases);ph['export']['generated_ignored_uid_files'][first['uid_path']]['sha256']='0'*64;rejected('reject export phase metadata substitution',lambda:admit(ph=ph))
  ph=copy.deepcopy(phases);ph['package']['generated_ignored_uid_files'][first['uid_path']]['sha256']='0'*64;rejected('reject package phase metadata substitution',lambda:admit(ph=ph))
  rejected('reject collision with runtime UID',lambda:admit(rt=runtime|{first['uid']}))
  side=repo/first['uid_path'];can=canonical/first['uid_path'];raw=side.read_bytes();side.write_bytes(b'uid://abc\n');rejected('reject changed generated UID bytes',admit);side.write_bytes(raw)
  can.write_bytes(b'uid://abc\n');rejected('reject changed canonical UID bytes',admit);can.write_bytes(raw)
  side.unlink();side.symlink_to(can);rejected('reject generated UID symlink',admit);side.unlink();side.write_bytes(raw)
  side.unlink();os.link(can,side);rejected('reject shared mutable canonical UID inode',admit);side.unlink();side.write_bytes(raw)
  script=repo/first['source_path'];source=script.read_bytes();script.write_bytes(source+b'\n');rejected('reject changed tracked source script',admit);script.write_bytes(source)
  check('restored private copies still accept exact75',len(admit())==75)
check('no engine subprocess socket or actual artifact mutation',not external)
# Replay all38 previously accepted base seams against the successor in copies.
base=area/'uid-qualifier-base-replay-r1';base.mkdir()
for src,dst in [(HERE/'qualify-successor-package-uid-aware.py',base/'qualify-successor-package.py'),(HERE/'check-qualification-guards.py',base/'check-qualification-guards.py')]:shutil.copy2(src,dst)
r=subprocess.run([sys.executable,str(base/'check-qualification-guards.py')],capture_output=True,text=True);check('all38 prior qualification controls still pass unchanged',r.returncode==0 and json.loads((base/'qualification-guard-checks.json').read_text())['count']==38)
result={'passed':True,'count':len(checks),'checks':checks,'helper_sha256':hashlib.sha256((HERE/'qualify-successor-package-uid-aware.py').read_bytes()).hexdigest(),'allowlist_sha256':hashlib.sha256((HERE/'uid-regeneration-allowlist.json').read_bytes()).hexdigest(),'test_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'base38_replay_report':str(base/'qualification-guard-checks.json'),'scope':'Exact actual75 data replayed in private source/UID copies plus finite rejection mutations and unchanged38 base controls. No engine, network, extraction, archive or canonical source/cache write.'}
p=HERE/'uid-qualification-guard-checks.json'
with p.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps({'passed':True,'count':len(checks),'helper_sha256':result['helper_sha256'],'report_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'test_sha256':result['test_sha256']}))
