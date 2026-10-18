#!/usr/bin/env python3
"""Validate only this bounded latest-package route; originals require direct review."""
import argparse, hashlib, json
from pathlib import Path
from PIL import Image
import package_identity as I
HERE=Path(__file__).resolve().parent

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def matches(state,expected):
 for path,value in expected.items():
  current=state
  for key in path.split('.'):current=current.get(key) if isinstance(current,dict) else None
  if current!=value:return False
 return True

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',type=Path,required=True);p.add_argument('--phase',choices=['warm','cold'],required=True);p.add_argument('--report',type=Path,required=True);p.add_argument('--export-manifest',type=Path,required=True);a=p.parse_args()
 if a.report.exists():p.error('Fresh report required')
 if not I.approved_inputs_bound():p.error('Exact latest export and extraction identities remain unbound')
 r=read(a.run/'run.json');w=read(a.run.with_name(a.run.name+'-watchdog')/'receipt.json');plan=read(HERE/('package-'+a.phase+'-plan.json'));checks={};originals=[]
 checks['route_complete_native_quit_zero']=r.get('complete') is True and r.get('verified_exit_code')==0
 checks['watchdog_completed_without_storage_floor_or_timeout']=w.get('complete') is True and w.get('overall_timeout') is False and not w.get('storage_floor_failure')
 checks['exact_source_runtime_archive_pck_export']=w.get('expected_source_commit')==I.SOURCE and w.get('engine_sha256')==I.RUNTIME and w.get('archive_sha256')==I.ARCHIVE and w.get('package_sha256')==I.PCK and w.get('export_manifest_sha256')==I.EXPORT_MANIFEST and r.get('engine_sha256')==I.RUNTIME and r.get('export_manifest',{}).get('git',{}).get('head')==I.SOURCE
 checks['exact_exporter_runtime_selection']=sha(a.export_manifest)==I.EXPORT_MANIFEST and I.exact_selection(read(a.export_manifest)['engine_selection']) and I.exact_selection(w['engine_selection'])
 checks['exact_extraction_receipt_and_sibling_payloads']=w.get('archive_runtime_executed') is True and w.get('diagnostic_runtime_override') is False and w.get('extraction_report_sha256')==I.EXTRACTION_REPORT and w.get('extracted_payloads_unchanged') is True
 checks['source_archive_instrumentation_unchanged']=all(r.get(k) is True for k in ['package_unchanged','archive_unchanged','export_manifest_unchanged','instrumentation_unchanged','source_unchanged'])
 checks['same_declared_bounded_plan']=r.get('plan_sha256')==sha(HERE/('package-'+a.phase+'-plan.json'))
 checks['native_events_no_authority_stages']=bool(r.get('events')) and all(type(e.get('window_id')) is int and e['window_id']>0 for e in r['events']) and r.get('authority_staging',{}).get('enabled') is False and not r.get('authority_staging',{}).get('stages') and not any('stage' in s for s in plan)
 manual=[s for s in plan if 'capture' in s];manual_ok=len(r.get('shots',[]))==len(manual)
 for step in manual:
  side=a.run/(step['capture']+'.json');s=read(side) if side.is_file() else {};pic=a.run/s.get('file','MISSING')
  okay=pic.is_file() and pic.suffix=='.png' and sha(pic)==s.get('sha256') and s.get('png_status')==0 and s.get('size')==[960,540] and Image.open(pic).size==(960,540) and matches(s,step.get('expect',{}))
  manual_ok=manual_ok and okay
  originals.append({'id':step['capture'],'passed':okay,'png_sha256':sha(pic) if pic.is_file() else None,'sidecar_sha256':sha(side) if side.is_file() else None})
 checks['all_manual_raw_originals_and_captured_expectations']=manual_ok and bool(originals)
 auto_ok=True
 for s in r.get('automatic_shots',[]):
  pic=a.run/s.get('file','MISSING');auto_ok=auto_ok and pic.is_file() and sha(pic)==s.get('sha256') and s.get('png_status')==0
 checks['all_observed_automatic_original_hashes']=auto_ok
 seeds=r.get('shader_cache_seed',{}).get('files_sha256',{});gseeds=r.get('godot_shader_cache_seed',{}).get('files_sha256',{});prior=r.get('shader_cache_seed',{}).get('reused_isolated_cache_sha256',{})
 if a.phase=='warm':
  checks['warm_explicit_shader_seeds_unchanged']=bool(seeds and gseeds) and r.get('shader_cache_seed_unchanged') is True and r.get('godot_shader_cache_seed_unchanged') is True
  checks['warm_external_scale_gate_declared']=w.get('scale_hook_external_only') is True and all(read(a.run/(s['capture']+'.json')).get('package_review',{}).get('external_scale_hook_enabled') is True for s in manual)
 else:
  checks['cold_fresh_empty_caches_preferences_and_no_scale_gate']=not seeds and not gseeds and not prior and not r.get('user_state',{}).get('before') and w.get('scale_hook_external_only') is False and all(read(a.run/(s['capture']+'.json')).get('package_review',{}).get('external_scale_hook_enabled') is False for s in manual)
 text=(a.run/'godot.log').read_text();checks['no_engine_script_errors']='SCRIPT ERROR:' not in text and '\nERROR:' not in text
 result={'passed':all(checks.values()),'phase':a.phase,'checks':checks,'originals':originals,'manual_count':len(manual),'observed_auto_count':len(r.get('automatic_shots',[])),'scope':'This smaller ordinary latest-package route only; prior59screen qualification remains separate. External warm F8 changes only canvas scale; all navigation is native XTest. No outcome stages, physicalGPU FPS, listening or finished-art claim.'};a.report.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'passed':result['passed'],'checks':len(checks),'manual':len(manual)}));return 0 if result['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
