#!/usr/bin/env python3
"""Finite review witnesses; synthetic private files and original predicate replay only."""
import ast,contextlib,copy,hashlib,importlib.util,io,json,subprocess,socket,sys,tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
SOURCE=HERE/'qualifier-original.py.txt'
RAW=SOURCE.read_bytes()
assert hashlib.sha256(RAW).hexdigest()=='d76324480cf6b4b54fa463c744a86d8c74421db63571a6a9e4db6b19fff42334'
tree=ast.parse(RAW);checks={}
for node in ast.walk(tree):
 if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=='check' and len(node.args)>=2:
  checks[ast.unparse(node.args[0])]=node.args[1]
def predicate(fragment,ns):
 nodes=[v for k,v in checks.items() if fragment in k]
 assert len(nodes)==1,(fragment,list(checks))
 return bool(eval(compile(ast.Expression(nodes[0]),str(SOURCE),'eval'),ns))
results=[]
commit='a'*40
phase={'exit_code':0,'after_source_passed':True,'source_commit':commit,'preparation_sha256':'1'*64,'cwd':'/expected/artifact/ANDOLAN','command':['expected','--export-only']}
for field,bad in [('preparation_sha256','2'*64),('cwd','/different/artifact/ANDOLAN'),('command',['unrelated','--package-only'])]:
 altered=copy.deepcopy(phase);altered[field]=bad
 accepted=predicate('exit0 and unchanged after-source audit',{'receipt':altered,'a':SimpleNamespace(expected_commit=commit)})
 results.append({'name':'phase '+field+' substitution','kind':'exact original predicate replay, not full package qualification','accepted':accepted,'unexpected_acceptance':accepted,'altered':altered})
wrong_exit=copy.deepcopy(phase);wrong_exit['exit_code']=1
results.append({'name':'nonzero export exit negative control','accepted':predicate('exit0 and unchanged after-source audit',{'receipt':wrong_exit,'a':SimpleNamespace(expected_commit=commit)}),'expected_rejection':True})
proof={'checks':1,'sources':{},'report':{'bytes':1,'sha256':'0'*64}}
results.append({'name':'contract manifest summary with unverified raw report','kind':'exact original predicate only; raw report is not read by this gate','accepted':predicate('native contract checks nonempty passed',{'packaged':{'native_contracts':proof},'exported':{'native_contracts':proof}}),'unbound_report':proof})
provenance={'files':[{'name':'Godot_v4.6.3-stable_win64.exe','bytes':1,'sha256':'0'*64}]}
class Archive:
 def read(self,name):return b'Run with bundled official Godot'
pm={'runtime':{'bytes':1,'sha256':'0'*64,'provenance':provenance},'windows_engine_provenance':provenance}
results.append({'name':'self-consistent arbitrary Windows provenance','kind':'exact original Windows provenance predicate, not whole ZIP admission','accepted':predicate('Windows official engine provenance',{'pm':pm,'base':'win/','names':[],'archive':Archive()}),'arbitrary_engine_sha256':'0'*64})
calls=[]
def forbidden(*a,**k):calls.append(repr(a));raise AssertionError('subprocess/socket forbidden')
with tempfile.TemporaryDirectory(prefix='w5-qualifier-order-') as temporary:
 root=Path(temporary);area=root/'area';area.mkdir();artifact=area/'package-successor-witness';repo=artifact/'ANDOLAN';tool=repo/'games/yuga-native/tools/package-native.py';tool.parent.mkdir(parents=True)
 helper=root/'qualifier.py';helper.write_bytes(RAW)
 marker=root/'import-happened';audit_marker=root/'audit-happened'
 tool.write_text('from pathlib import Path\nPath('+repr(str(marker))+').write_text("artifact module executed before admission")\n')
 stub='from pathlib import Path\nimport json\nAREA=Path('+repr(str(area))+')\nNATIVE=Path("games/yuga-native")\nSOURCE=Path("/synthetic/canonical")\ndef audit(*args):\n Path('+repr(str(audit_marker))+').write_text("called")\n raise ValueError("synthetic tracked-source rejection")\ndef dump_new(path,result):\n path.write_text(json.dumps(result))\n'
 (root/'prepare-package-snapshot.py').write_text(stub)
 prep={'materialized':True,'source_commit':commit,'artifact_root':str(artifact),'repository':str(repo),'entries':[]}
 preparation=root/'preparation.json';preparation.write_text(json.dumps(prep));digest=hashlib.sha256(preparation.read_bytes()).hexdigest()
 (artifact/'export-execution.json').write_text(json.dumps({'exit_code':1,'after_source_passed':False,'source_commit':commit}))
 report=root/'report.json';spec=importlib.util.spec_from_file_location('original_qualifier',helper);q=importlib.util.module_from_spec(spec)
 with patch.object(subprocess,'run',forbidden),patch.object(subprocess,'Popen',forbidden),patch.object(subprocess,'check_output',forbidden),patch.object(socket,'socket',forbidden),patch.object(sys,'argv',['qualifier.py','--preparation',str(preparation),'--preparation-sha256',digest,'--expected-commit',commit,'--report',str(report)]),contextlib.redirect_stdout(io.StringIO()):
  spec.loader.exec_module(q);code=q.main()
 results.append({'name':'actual original helper imports artifact module before failing export phase/source audit','kind':'full main synthetic private fixture; no real package files touched','exit_code':code,'artifact_module_executed':marker.exists(),'tracked_audit_called':audit_marker.exists(),'report':json.loads(report.read_text())})
assert not calls
assert all(x['accepted'] for x in results[:3]) and results[3]['accepted'] is False
assert results[4]['accepted'] and results[5]['accepted']
assert results[6]['exit_code']==1 and results[6]['artifact_module_executed'] and not results[6]['tracked_audit_called']
result={'schema':1,'original_qualifier_sha256':hashlib.sha256(RAW).hexdigest(),'witnesses':results,'subprocess_socket_operations':calls,'scope':'Import-order reproduced through original main with synthetic private files; phase/contract/Windows findings replay only exact original predicates, not a forged full-package acceptance. No engine/network/Git or actual artifact mutation.'}
(HERE/'original-witnesses.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'witnesses':len(results),'import_before_rejection':True,'external_operations':len(calls)}))
