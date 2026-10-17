#!/usr/bin/env python3
"""Independently reject failed, altered, ambiguous or warning-bearing final receipts."""
from pathlib import Path
import hashlib,json,re
ROOT=Path(__file__).resolve().parent

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def pairs(items):
 result={}
 for key,value in items:
  if key in result:raise ValueError('duplicate JSON key: '+key)
  result[key]=value
 return result
def constant(value):raise ValueError('nonfinite JSON number: '+value)
def load(path):return json.loads(path.read_text(),object_pairs_hook=pairs,parse_constant=constant)
def runtime(data):
 records=data.get('files',data)
 return {k:v for k,v in records.items() if k.startswith(('scripts/','shaders/','scenes/','assets/')) or k in ('project.godot','export_presets.cfg')}
results={}; runtime_sets=[]; logs_checked=0; warning_lines=[]
for label,expected_suites in [('visual',12),('quality',16),('resources',1)]:
 base=ROOT/label; summary=load(base/'summary.json')
 assert summary['passed'] is True,(label,'failed summary')
 assert summary['checked_sources_unchanged'] is True,(label,'changed checked sources')
 before=load(base/'source-before.json'); after=load(base/'source-after.json')
 assert before==after,(label,'changed sources')
 runtime_sets.append(runtime(before))
 entries=summary.get('suites',[summary.get('suite')]);assert len(entries)==expected_suites
 count=0; audio_files=0
 for entry in entries:
  assert entry['passed'] is True and entry['exit_code']==0,(label,entry['id'],'not clean exit/pass')
  for flag in ['timed_out','log_limit_exceeded']:
   assert not entry.get(flag,False),(label,entry['id'],flag)
  assert not entry.get('problems',[]) and not entry.get('logged_errors',[]) and not entry.get('engine_errors',[])
  report_path=base/entry['report'];assert sha(report_path)==entry['report_sha256'],str(report_path)
  report=load(report_path);assert report['passed'] is True
  if isinstance(report.get('checks'),list):
   assert report['checks'] and all(type(check.get('passed')) is bool and check['passed'] for check in report['checks'])
   count+=len(report['checks'])
  else:
   assert entry['id']=='action-audio-build' and report.get('mode')=='check' and report.get('files')==15 and not report.get('failures')
   audio_files+=report['files']
  for key in ['stdout','stderr','log']:
   if key in entry:
    path=base/entry[key];assert sha(path)==entry[key+'_sha256'],str(path)
 for path in sorted((base/'logs').iterdir()):
  if not path.is_file():continue
  logs_checked+=1
  for line_number,line in enumerate(path.read_text(errors='strict').splitlines(),1):
   if re.search(r'^\s*(SCRIPT ERROR:|ERROR:|WARNING:)',line):warning_lines.append({'path':str(path.relative_to(ROOT)),'line':line_number,'text':line})
 results[label]={'suites':expected_suites,'assertions':count,'audio_files':audio_files,'source_unchanged':True,'native_exit_codes':[entry['exit_code'] for entry in entries]}
assert not warning_lines,warning_lines
assert runtime_sets[0]==runtime_sets[1]==runtime_sets[2],'runtime identities differ between sequential runners'
assert results['visual']['assertions']==727
assert results['quality']['assertions']==777 and results['quality']['audio_files']==15
assert results['resources']['assertions']==51
resource=load(ROOT/'resources/reports/resource-budget.json')
assert resource['effects']['complete'] is True
assert len(resource['cycles'])==5
current_runtime=runtime_sets[0]
output={'passed':True,'catalogs':results,'shared_runtime_files':len(current_runtime),'logs_checked':logs_checked,'engine_errors':[],'engine_warnings':[],'strict_json':'duplicate object keys and NaN/Infinity rejected at every depth','source_identity':'All three sequential runs have identical full runtime records and unchanged before/after source pins.','scope':'Numerical contracts and allocation/lifecycle evidence; no rendered quality, FPS, hardware GPU, online or release acceptance.'}
print(json.dumps(output,indent=2,sort_keys=True))
