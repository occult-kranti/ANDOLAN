#!/usr/bin/env python3
"""Finite pending-identity gates only. No engine, network or Git subprocess."""
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import socket
import subprocess
import sys
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
REPO=Path('/workspace/ANDOLAN')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def local_state():
 h=(REPO/'.git/HEAD').read_text().strip()
 ref=h.removeprefix('ref: ')
 return {'head_file':h,'source_commit':(REPO/'.git'/ref).read_text().strip(),'index_sha256':sha(REPO/'.git/index')}
def load(name,file):
 s=importlib.util.spec_from_file_location(name,HERE/file);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
before=local_state();checks=[];calls=[]
def forbidden(*a,**k):calls.append(repr(a));raise AssertionError('external operation attempted')
with patch.object(subprocess,'run',forbidden),patch.object(subprocess,'Popen',forbidden),patch.object(subprocess,'check_output',forbidden),patch.object(socket,'socket',forbidden):
 g=load('pending_generator','generate.py');u=load('pending_uploader','upload_template.py');p=load('pending_push','push.py')
 def rejected(name,fn,argv=None):
  with patch.object(sys,'argv',argv or ['pending']):
   try:fn()
   except ValueError as e:
    if 'UNBOUND' not in str(e):raise
    checks.append({'name':name,'passed':True,'reason':str(e)})
   else:raise AssertionError('pending operation accepted: '+name)
 rejected('default generator rejects pending identities before snapshot',g.main,['generate.py'])
 rejected('materialization flag cannot bypass pending identities',g.main,['generate.py','--materialize'])
 rejected('manifest path is not opened before pending uploader gate',lambda:u.read_manifest('/nonexistent/do-not-read'))
 rejected('upload rejects before output inspection or API',lambda:u.upload({},None,forbidden))
 rejected('release identity validator rejects unbound draft',lambda:u.check_release({},{}))
 rejected('push main rejects before receipt read or remote/ref operation',p.main,['push.py','--push-fixed-draft'])
 rejected('push receipt path rejects before local Git object access',lambda:p.validate_local({}, {},git=forbidden,snapshot=forbidden))
 rejected('verify CLI rejects pending manifest before any output creation',u.main,['upload_template.py','verify','--manifest','/nonexistent/do-not-read','--output','/nonexistent/do-not-create'])
 rejected('upload CLI rejects pending manifest before API',u.main,['upload_template.py','upload','--manifest','/nonexistent/do-not-read','--output','/nonexistent/do-not-read'])
 sources=['generate.py','upload_template.py','push.py','test_guards.py','test_push_guards.py','test_pending.py']
 for f in sources:ast.parse((HERE/f).read_text(),filename=f)
after=local_state()
assert before==after and not calls
assert before['source_commit']=='79e5c15d8a3657e16fda67acb277b2406120dcd1'
r={'schema':1,'passed':True,'count':len(checks),'checks':checks,'syntax_parsed_sources':len(sources),'checkout_before':before,'checkout_after':after,'external_subprocess_socket_calls':calls,'source_pins':{f:sha(HERE/f) for f in sources},'scope':'Only unbound template rejection; existing22+10 final transport guards NOT executed, no qualification or asset validation.'}
(HERE/'pending-guard.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps({'passed':True,'count':len(checks),'external_operations':len(calls),'source_commit':before['source_commit']}))
