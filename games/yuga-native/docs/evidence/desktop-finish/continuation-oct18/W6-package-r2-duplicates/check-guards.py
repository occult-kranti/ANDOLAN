#!/usr/bin/env python3
"""Finite path/inode/backup rejection tests; no real cleanup or network."""
import hashlib,importlib.util,json,os
from pathlib import Path
import subprocess,sys,tempfile
from unittest.mock import patch
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('duplicates',HERE/'duplicates.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
checks=[]
def check(name,value):
 checks.append({'name':name,'passed':bool(value)})
 if not value:raise AssertionError(name)
def rejects(name,fn):
 try:fn()
 except ValueError:check(name,True)
 else:check(name,False)
for relative in ['yuga-native-linux-x86_64/godot','yuga-native-windows-x86_64/yuga-native.pck','yuga-native-windows.pck']:check('permit exact generated duplicate namespace '+relative,m.valid_candidate(m.BUILD/relative))
for path in [m.BUILD/'yuga-native-linux.pck',m.BUILD/'yuga-native-linux-x86_64.zip',m.BUILD/'native-export-manifest.json',m.ARTIFACT/'logs/export.stdout',m.ARTIFACT/'ANDOLAN/games/yuga-native/project.godot',Path('/workspace/scratch/yuga-continuation-W1-r1/package-r2-extracted/godot'),m.BUILD/'yuga-native-linux-x86_64/../outside',m.BUILD/'yuga-native-linux-x86_64']:
 check('protect noncandidate '+str(path),not m.valid_candidate(path))
with tempfile.TemporaryDirectory(prefix='w6-duplicate-guards-',dir='/workspace/scratch/yuga-continuation-W6-r1') as temporary:
 p=Path(temporary);a=p/'a';a.write_bytes(b'fixture');check('regular private fixture accepted',m.snapshot(a)['nlink']==1)
 b=p/'b';os.link(a,b);rejects('shared inode duplicate rejected',lambda:m.snapshot(a));b.unlink();b.symlink_to(a);rejects('symlink duplicate rejected',lambda:m.record(b))
 calls=[]
 def forbidden(*a,**k):calls.append(True);raise AssertionError('External operation forbidden')
 with patch.object(subprocess,'check_output',forbidden):
  for commit,branch in [('0','backup/yuga-desktop-test'),('a'*40,'game/yuga-native-production'),('a'*40,'backup/yuga-desktop/../bad')]:rejects('invalid backup identity rejected before network '+branch,lambda c=commit,b=branch:m.backup_bound(c,b,HERE/'recovery-map.json'))
 check('invalid backup tests made no Git/network calls',not calls)
 with patch.object(subprocess,'check_output',return_value=('b'*40+'\trefs/heads/backup/yuga-desktop-test\n').encode()):
  rejects('wrong remote backup tip rejected',lambda:m.backup_bound('a'*40,'backup/yuga-desktop-test',HERE/'recovery-map.json'))
verification=json.loads((HERE/'verification.json').read_text());check('actual readonly map verification passed82 with no removals',verification['passed'] and verification['verified_files']==82 and not verification['removed'] and verification['allocated_bytes_removed']==0)
result={'passed':True,'count':len(checks),'checks':checks,'guard_sha256':hashlib.sha256((HERE/'duplicates.py').read_bytes()).hexdigest(),'map_sha256':hashlib.sha256((HERE/'recovery-map.json').read_bytes()).hexdigest(),'scope':'Synthetic namespace/inode and invalid remote-identity negatives, plus recorded actual read-only82-file verification. No cleanup, engine, cache mutation or network.'}
p=HERE/'guard-checks.json'
with p.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps({'passed':True,'count':len(checks),'guard_sha256':result['guard_sha256'],'report_sha256':hashlib.sha256(p.read_bytes()).hexdigest()}))
