#!/usr/bin/env python3
"""Seal the two completed, exact extracted r4 package executions. No engine."""
import hashlib,json,shutil,datetime,os,re
from pathlib import Path
ROOT=Path('/workspace/ANDOLAN/games/yuga-native')
WORK=Path('/workspace/scratch/yuga-r4-review-preparation')
OUT=ROOT/'docs/evidence/desktop-finish/package-native-review/W1-patched-r1'
PREP=ROOT/'docs/evidence/desktop-finish/package-review-preparation/W1-r4-receipt-pin-r1'
PKG=Path('/workspace/scratch/yuga-desktop-integrated-package-r4')
SRC=Path('/tmp/yuga-desktop-integrated-package-r1/ANDOLAN/games/yuga-native')
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def read(p):return json.loads(Path(p).read_text())
def put(p,d):Path(p).write_text(json.dumps(d,indent=2,sort_keys=True)+'\n')
def pin(p):return {'sha256':sha(p),'bytes':Path(p).stat().st_size}
assert not (OUT/'receipt.json').exists(), 'Sealed owner packet must never be overwritten'
exp=read(PKG/'build/native-export-manifest.json')
extract=read(PKG/'extraction-verification.json')
prep=read(PREP/'receipt.json')
checks={}
checks['552_exported_runtime_files_exact']=len(exp['source']['files'])==552 and all((SRC/n).is_file() and pin(SRC/n)==v for n,v in exp['source']['files'].items())
exroot=PKG/'extracted/yuga-native-linux-x86_64'
checks['45_extracted_payloads_and_modes_exact']=len(extract['members'])==45 and all(pin(exroot/n)=={k:v[k] for k in ['sha256','bytes']} and oct((exroot/n).stat().st_mode&0o777)==v['mode'] for n,v in extract['members'].items())
checks['sealed_extraction_receipt_exact']=sha(PKG/'extraction-verification.json')=='740bca01edb24e0ab56be9bb9ace922f4cd8dcf10e024ecb1fe841be048e950b'
checks['all34_sealed_preparation_inputs_exact']=len(prep['files'])==34 and all(pin(PREP/n)==v for n,v in prep['files'].items())
expected={'build/yuga-native-linux-x86_64.zip':'27c36e5523643c647b245614721c0160b3d1548bf6da851d922886cffc180d0e','build/native-export-manifest.json':'4cb3316300092dcdb99016f3c0e6f024066df2f94999a3b7b4944247870aa4a7','build/native-package-manifest.json':'01581b3d740097aa61bd35c3722a85dca1021dddb1766a2a28e1c1b53645417c','qualification-receipt.json':'a82fa9d2e96034831f49d4fe036c0040d0aff9952e5dbf30077bc3adfadc5b52'}
checks['archive_export_package_qualification_exact']=all((PKG/n).exists() and sha(PKG/n)==v for n,v in expected.items())
phases={};live=[]
for phase in ['warm','cold']:
 raw=Path(f'/workspace/scratch/yuga-desktop-package-r4-{phase}-r1')
 wd=Path(str(raw)+'-watchdog');w=read(wd/'receipt.json');run=read(raw/'run.json')
 v=read(WORK/f'{phase}-validation.json');a=read(WORK/f'{phase}-original-audit.json')
 copied=read(WORK/f'{phase}-phase-archive.json')
 checks[f'{phase}_complete_quit_zero_within_original_bound']=w['complete'] and w['driver_exit']==0 and not w['overall_timeout'] and w['elapsed_seconds']<w['overall_limit_seconds'] and run['complete'] and run['verified_exit_code']==0
 checks[f'{phase}_route_and_original_audits_pass']=v['passed'] and a['passed'] and all(v['checks'].values()) and all(c['passed'] for c in a['checks'])
 checks[f'{phase}_all_recorded_identity_guards_true']=w['extracted_payloads_unchanged'] and all(v for k,v in run.items() if k.endswith('_unchanged'))
 checks[f'{phase}_fresh_preferences']=run['user_state']['before']=={}
 checks[f'{phase}_archived_phase_exact']=copied['passed'] and all(pin(OUT/phase/n)==pin(raw/n) for n in [p.name for p in raw.iterdir() if p.is_file()]) and all(pin(OUT/f'{phase}-watchdog'/p.name)==pin(p) for p in wd.iterdir() if p.is_file())
 lines=[line for line in (raw/'godot.log').read_text().splitlines() if re.search(r'(^|\s)(SCRIPT ERROR|ERROR|WARNING):|ObjectDB instances leaked|resources still in use',line)]
 checks[f'{phase}_engine_log_no_error_warning_leak']=not lines
 samples=[json.loads(s) for s in (wd/'process-samples.jsonl').read_text().splitlines()]
 for sample in samples:
  for row in sample['processes']:
   stat=Path(f"/proc/{row['pid']}/stat")
   if stat.exists():
    parts=stat.read_text().rsplit(')',1)[1].split()
    if int(parts[19])==row['start_ticks'] and parts[0]!='Z':live.append(row)
 seeds={}
 for key in ['shader_cache_seed','godot_shader_cache_seed']:
  seed=run[key];seeds[key]={'path':seed['path'],'file_count':len(seed['files_sha256'])}
  if seed['path']:
   checks[f'{phase}_{key}_source_still_exact']=all(sha(Path(seed['path'])/n)==h for n,h in seed['files_sha256'].items())
  elif phase=='cold':checks[f'{phase}_{key}_empty']=not seed['files_sha256'] and not seed.get('reused_isolated_cache_sha256',{})
 phases[phase]={'complete':True,'driver_exit':0,'elapsed_seconds':w['elapsed_seconds'],'whole_attempt_limit_seconds':w['overall_limit_seconds'],'first_saved_title_after_wrapper_start_seconds':min(p.stat().st_mtime for p in raw.glob('01-*.png'))-w['started_unix'],'saved_title_timing_limit':'File mtime of first saved title; not first drawable-frame measurement.','manual_originals':len(run['shots']),'automatic_originals':len(run['automatic_shots']),'route_check_count':len(v['checks']),'raw_check_count':a['count'],'authority_stage_count':len(run['authority_staging']['stages']),'seeds':seeds,'heading':v['heading'],'native_stack_observer_used':(wd/'native-gdb.log').exists(),'log_diagnostics':lines}
checks['no_live_sampled_owned_processes']=not live
checks['cold_no_stages']=phases['cold']['authority_stage_count']==0
checks['warm_six_declared_stages']=phases['warm']['authority_stage_count']==6
checks['distinct_isolated_user_directories']=read(OUT/'warm/run.json')['user_state']['path']!=read(OUT/'cold/run.json')['user_state']['path']
audit={'passed':all(checks.values()),'check_count':len(checks),'checks':checks,'owned_live':live,'source_commit':'96d5b9cd3114b9732f7dc80433b1ca0a1d4a9b12','phases':phases,'scope':'Artifact and bounded native route qualification; software renderer only.'}
put(OUT/'integrity-audit.json',audit)
assert audit['passed'], {k:v for k,v in checks.items() if not v}
shutil.copytree(PREP,OUT/'executed-preparation')
shutil.copy2(WORK/'archive_phase.py',OUT/'archive_phase.py')
shutil.copy2(__file__,OUT/'seal_actual.py')
shutil.copy2(WORK/'observed-warm-originals.json',OUT/'observed-warm-originals.json')
notes={'01-package-title':'Both modes, complete primary action and full hero visible; inherited dotted floor remains.','03-package-training-rotated':'Actual side-facing hero and default Q card visible; five HUD cards contained.','06-package-world-rotated':'Actual hero turned sideways, map and five cards readable with ordinary army present.','07-package-overview-rotated-a':'Full elevated world retained alongside separate scrollable overview card; actual marker direction sampled independently.','09-package-world-overview-return':'Ordinary following-camera framing and HUD return, hero facing retained.','10-package-night-pause':'Night world and focused Continue practice visible; pause list scroll is intentional and contained.'}
put(OUT/'observed-cold-originals.json',{'scope':'W1 directly opened these six full originals; W6 independently opened all19 cold originals. This is sampled visual review, not continuous motion playback.','originals':{n:{'sha256':sha(OUT/'cold'/f'{n}.png'),'directly_opened':True,'note':s} for n,s in notes.items()}})
for src,dest in [(PKG/'extraction-verification.json','extraction-verification.json'),(PKG/'qualification-receipt.json','qualification-receipt.json'),(PKG/'build/native-export-manifest.json','native-export-manifest.json'),(PKG/'build/native-package-manifest.json','native-package-manifest.json')]:shutil.copy2(src,OUT/dest)
refs=[
 'docs/evidence/desktop-finish/package-export-r4/W6/receipt.json',
 'docs/evidence/desktop-finish/package-review-preparation/W1-r4/receipt.json',
 'docs/evidence/desktop-finish/package-review-preparation/W5-r4-source-review-r1/receipt.json',
 'docs/evidence/desktop-finish/package-review-preparation/W5-r4-source-review-r1/witness.json',
 'docs/evidence/desktop-finish/package-review-preparation/W6-r4-independent/receipt.json',
 'docs/evidence/desktop-finish/package-review-preparation/W6-r4-receipt-pin-review-r1/receipt.json',
 'docs/evidence/desktop-finish/package-native-review/W1-public-r1/receipt.json',
 'docs/evidence/desktop-finish/package-native-review/W1-e69-diagnostic-r1/receipt.json',
 'docs/evidence/desktop-finish/package-native-review/W1-e69-diagnostic-r2/receipt.json']
put(OUT/'references.json',{'path_base':'games/yuga-native at repository root','references':{n:pin(ROOT/n) for n in refs},'pending_independent_final_closure':'W6 will seal the separate59-original central closure after this owner receipt; this receipt is not changed to add later companions.'})
put(OUT/'phase-summary.json',phases)
print(json.dumps({'integrity_checks':len(checks),'passed':True,'phases':{p:{k:v for k,v in d.items() if k not in ['heading','seeds']} for p,d in phases.items()}}))
