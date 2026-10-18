#!/usr/bin/env python3
"""Read actual UID-warning inputs; run admission only and finite copied-data negatives."""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import socket
import subprocess
import sys
from unittest.mock import patch
sys.dont_write_bytecode = True
p=argparse.ArgumentParser();p.add_argument('--helper',type=Path,required=True);p.add_argument('--report',type=Path,required=True);args=p.parse_args()
if args.report.exists():raise SystemExit('Fresh report required')
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
base=Path('/workspace/scratch/yuga-continuation-W6-r1/package-successor-r2')
repo=base/'ANDOLAN';canonical=Path('/workspace/ANDOLAN');prep_path=Path(str(base)+'-preparation.json')
prep=json.loads(prep_path.read_text());phases={x:json.loads((base/(x+'-execution.json')).read_text()) for x in ['export','package']}
exported=json.loads((base/'build/native-export-manifest.json').read_text())
ids={row['uid'] for row in exported['runtime_uids']['sidecars'].values()}
allow=args.helper.parent/'uid-regeneration-allowlist.json';expected=json.loads(allow.read_text())
logs=[*sorted((base/'logs').glob('*')),*sorted((base/'build').glob('*.log'))]
diag={str(f.relative_to(base)):[line for line in f.read_text(errors='replace').splitlines() if any(marker in line for marker in ['ERROR:','WARNING:','SCRIPT ERROR:'])] for f in logs}
inputs={str(f):sha(f) for f in [args.helper,allow,prep_path,base/'export-execution.json',base/'package-execution.json',base/'build/native-export-manifest.json',*logs]}
external=[]
def forbidden(*a,**kw):external.append(True);raise AssertionError('External operation forbidden')
checks=[]
def check(name,value):
 checks.append({'name':name,'passed':bool(value)})
 if not value:raise AssertionError(name)
with patch.object(subprocess,'run',forbidden),patch.object(subprocess,'Popen',forbidden),patch.object(subprocess,'check_output',forbidden),patch.object(socket,'socket',forbidden):
 spec=importlib.util.spec_from_file_location('uid_qualifier',args.helper);q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)
 check('exact reviewed allowlist bytes',sha(allow)==q.UID_ALLOWLIST_SHA)
 admitted=q.admit_uid_regeneration(diag,expected,repo,canonical,prep,sha(prep_path),phases,ids)
 check('actual75 warnings admitted with complete original row records',len(admitted)==75 and all(row=={'log':expected['log'],**source} for row,source in zip(admitted,expected['warnings'])))
 changes=[('unrelated warning',lambda d:d[expected['log']].append('WARNING: unrelated diagnostic')),('script error',lambda d:d[expected['log']].append('SCRIPT ERROR: synthetic')),('missing warning',lambda d:d[expected['log']].pop()),('duplicate warning',lambda d:d[expected['log']].append(d[expected['log']][0])),('different warning text',lambda d:d[expected['log']].__setitem__(0,d[expected['log']][0]+' altered')),('relocated warning log',lambda d:d.__setitem__('build/export-windows.log',d.pop(expected['log'])))]
 for name,change in changes:
  d=copy.deepcopy(diag);change(d)
  try:q.admit_uid_regeneration(d,expected,repo,canonical,prep,sha(prep_path),phases,ids)
  except ValueError:check('reject '+name,True)
  else:check('reject '+name,False)
 altered=copy.deepcopy(phases);altered['package']['generated_ignored_uid_files'][expected['warnings'][0]['uid_path']]['sha256']='0'*64
 try:q.admit_uid_regeneration(diag,expected,repo,canonical,prep,sha(prep_path),altered,ids)
 except ValueError:check('reject substituted package-phase UID metadata',True)
 else:check('reject substituted package-phase UID metadata',False)
 try:q.admit_uid_regeneration(diag,expected,repo,canonical,prep,sha(prep_path),phases,ids|{expected['warnings'][0]['uid']})
 except ValueError:check('reject collision with runtime UID',True)
 else:check('reject collision with runtime UID',False)
check('all read-only input hashes unchanged',all(sha(Path(path))==digest for path,digest in inputs.items()))
check('no subprocess socket engine or archive audit occurred',not external)
result={'schema':1,'passed':all(x['passed'] for x in checks),'count':len(checks),'checks':checks,'source_commit':prep['source_commit'],'helper_sha256':sha(args.helper),'test_sha256':sha(Path(__file__)),'input_sha256':inputs,'scope':'Actual75-row admission plus copied-data mutation checks only. No full package qualifier execution, engine, archive changes, network or Git operations.'}
with args.report.open('x') as f:json.dump(result,f,indent=2);f.write('\n')
print(json.dumps({'passed':result['passed'],'count':result['count'],'report':str(args.report),'sha256':sha(args.report)}))
