#!/usr/bin/env python3
"""Finite synthetic qualifier negatives; no engine, network or real artifact audit."""
import contextlib
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
from unittest.mock import patch
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('qualifier', HERE / 'qualify-successor-package.py')
q = importlib.util.module_from_spec(spec); spec.loader.exec_module(q)
checks = []
def check(name, value):
    checks.append({'name': name, 'passed': bool(value)})
    if not value: raise AssertionError(name)
repo = Path('/synthetic/area/artifact/ANDOLAN'); out = repo.parent; native = Path('games/yuga-native')
commit, preparation_sha = 'a' * 40, 'b' * 64
phase = {'exit_code': 0, 'after_source_passed': True, 'source_commit': commit,
         'preparation_sha256': preparation_sha, 'cwd': str(repo),
         'command': q.expected_phase_command(repo, out, native, 'export'),
         'environment': {name: str(out / 'user' / suffix) for name, suffix in [('XDG_DATA_HOME','data'),('XDG_CONFIG_HOME','config'),('XDG_CACHE_HOME','cache')]}}
phase['environment'].update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
def phase_ok(value): return q.phase_binding_matches(value,'export',preparation_sha,commit,repo,out,native)
check('exact phase binding positive control', phase_ok(phase))
for key, bad in [('preparation_sha256','c'*64),('cwd','/different'),('command',['unrelated']),('environment',{}),('source_commit','d'*40),('exit_code',1),('after_source_passed',False),('failure','synthetic failure'),('terminated_reason','floor')]:
    value=copy.deepcopy(phase);value[key]=bad;check('reject phase substitution '+key,not phase_ok(value))
source = {'input': {'bytes':1,'sha256':'e'*64}}; report_sources={'catalog':'f'*64}; record={'bytes':3,'sha256':'1'*64}
proof={'schema':1,'sources':source,'report':record,'checks':1};raw={'passed':True,'source_sha256':report_sources,'checks':[{'name':'required','passed':True}]}
def proof_ok(p,r,rec=record): return q.contract_proof_matches(p,r,rec,source,report_sources,{'required'})
check('exact raw proof positive control',proof_ok(proof,raw))
for label, change in [('report hash',lambda p,r:p['report'].update(sha256='2'*64)),('source closure',lambda p,r:p.update(sources={})),('report source hashes',lambda p,r:r.update(source_sha256={})),('failed gate',lambda p,r:r['checks'][0].update(passed=False)),('empty gates',lambda p,r:r.update(checks=[])),('missing required name',lambda p,r:r['checks'][0].update(name='different')),('count mismatch',lambda p,r:p.update(checks=2)),('top-level failure',lambda p,r:r.update(passed=False))]:
    p,r=copy.deepcopy(proof),copy.deepcopy(raw);change(p,r);check('reject raw proof '+label,not proof_ok(p,r))
windows_proof=json.loads(q.WINDOWS_PROOF.read_text());pm={'runtime':{**q.WINDOWS_ENGINE,'provenance':windows_proof},'windows_engine_provenance':windows_proof}
check('fixed Windows provenance positive control',q.windows_provenance_matches(pm,windows_proof))
bad=copy.deepcopy(pm);bad['runtime']['sha256']='0'*64;check('reject arbitrary Windows binary despite matching provenance',not q.windows_provenance_matches(bad,windows_proof))
bad=copy.deepcopy(pm);bad['runtime']['provenance']['archive_sha256']='0'*64;bad['windows_engine_provenance']=bad['runtime']['provenance'];check('reject self-consistent substituted Windows official-archive proof',not q.windows_provenance_matches(bad,windows_proof))
external=[]
def forbidden(*args,**kwargs): external.append(True);raise AssertionError('External operation forbidden')
with tempfile.TemporaryDirectory(prefix='w6-qualifier-guards-',dir='/workspace/scratch/yuga-continuation-W6-r1') as temporary:
    root=Path(temporary);area=root/'area';area.mkdir();artifact=area/'package-successor-witness';repo2=artifact/'ANDOLAN';tool=repo2/native/'tools/package-native.py';tool.parent.mkdir(parents=True)
    helper=root/'qualifier.py';helper.write_bytes((HERE/'qualify-successor-package.py').read_bytes())
    marker=root/'artifact-imported';audit_marker=root/'source-audited'
    tool.write_text('from pathlib import Path\nPath('+repr(str(marker))+').write_text("forbidden import")\n')
    (root/'prepare-package-snapshot.py').write_text('from pathlib import Path\nimport json\nAREA=Path('+repr(str(area))+')\nNATIVE=Path("games/yuga-native")\nSOURCE=Path("/synthetic/canonical")\ndef audit(*args):\n Path('+repr(str(audit_marker))+').write_text("called")\n raise ValueError("synthetic source rejection")\ndef dump_new(path,result):\n with path.open("x") as stream:json.dump(result,stream)\n')
    preparation=root/'preparation.json';preparation.write_text(json.dumps({'materialized':True,'source_commit':commit,'artifact_root':str(artifact),'repository':str(repo2),'entries':[]}));digest=hashlib.sha256(preparation.read_bytes()).hexdigest()
    for scenario in ['failed-phase','rejected-source']:
        for phase_name in ['export','package']:
            value=copy.deepcopy(phase);value.update(source_commit=commit,preparation_sha256=digest,cwd=str(repo2),command=q.expected_phase_command(repo2,artifact,native,phase_name),environment={name:str(artifact/'user'/suffix) for name,suffix in [('XDG_DATA_HOME','data'),('XDG_CONFIG_HOME','config'),('XDG_CACHE_HOME','cache')]});value['environment'].update(OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1')
            if scenario=='failed-phase':value['exit_code']=1
            (artifact/(phase_name+'-execution.json')).write_text(json.dumps(value))
        report=root/(scenario+'.json');new_spec=importlib.util.spec_from_file_location('synthetic_qualifier_'+scenario,helper);module=importlib.util.module_from_spec(new_spec)
        with patch.object(subprocess,'run',forbidden),patch.object(subprocess,'Popen',forbidden),patch.object(subprocess,'check_output',forbidden),patch.object(socket,'socket',forbidden),patch.object(sys,'argv',['qualifier.py','--preparation',str(preparation),'--preparation-sha256',digest,'--expected-commit',commit,'--report',str(report)]),contextlib.redirect_stdout(io.StringIO()):
            new_spec.loader.exec_module(module);code=module.main()
        check(scenario+' exits failure before artifact Python import',code==1 and not marker.exists())
        check(scenario+' source audit ordering correct',audit_marker.exists()==(scenario=='rejected-source'))
    logs=root/'required-logs'
    for name in q.required_log_names():
        target=logs/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_text('clean\n')
    def logs_present():return all((logs/name).is_file() and not (logs/name).is_symlink() for name in q.required_log_names())
    check('complete fixed required log census positive control',logs_present())
    for name in q.required_log_names():
        target=logs/name;target.unlink();check('missing required evidence log rejected '+name,not logs_present());target.write_text('clean\n')
check('no subprocess socket engine or real artifact operation occurred',not external)
result={'passed':True,'count':len(checks),'checks':checks,'helper_sha256':hashlib.sha256((HERE/'qualify-successor-package.py').read_bytes()).hexdigest(),'test_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'scope':'Exact pure binding/proof predicates plus full helper main with private synthetic failed phase/source fixtures. No real package audit, engine, import, network or canonical source edit.'}
report=HERE/'qualification-guard-checks.json'
with report.open('x') as stream:json.dump(result,stream,indent=2);stream.write('\n')
print(json.dumps({'passed':True,'count':len(checks),'helper_sha256':result['helper_sha256'],'report':str(report),'report_sha256':hashlib.sha256(report.read_bytes()).hexdigest()}))
