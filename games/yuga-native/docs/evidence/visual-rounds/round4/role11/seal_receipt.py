#!/usr/bin/env python3
"""Pin R4-11 native results and retain the nonmatched Kodanda pose witness."""
from pathlib import Path
import hashlib, json, math, re, subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def dump(name, value): (HERE / name).write_text(json.dumps(value, indent=2) + '\n')
main = json.loads((HERE / 'warning-lifecycle-r3.json').read_text())
replay = json.loads((HERE / 'options-replay.json').read_text())
promotion_file = ROOT / 'docs/evidence/visual-rounds/round3/integration/promotion.json'
promotion = json.loads(promotion_file.read_text())
ignored = ['generation', 'epoch', 'cast_id', 'event_seq']
def clean(value):
    if isinstance(value, dict): return {k:clean(v) for k,v in value.items() if k not in ignored}
    if isinstance(value, list): return [clean(v) for v in value]
    return value
def diffs(a, b, path=''):
    if isinstance(a, dict):
        return [d for k in a for d in diffs(a[k], b[k], path+'/'+k)]
    if isinstance(a, list):
        if len(a) != len(b): return [{'path':path, 'normal':a, 'reduced':b}]
        return [d for i,(x,y) in enumerate(zip(a,b)) for d in diffs(x,y,path+'/'+str(i))]
    return [] if a==b else [{'path':path,'normal':a,'reduced':b}]
pairs = []
for kind in ['release_impact','windup_cancel']:
    for ability in ['kodanda','piercing_dawn','measured_step','guardian_circle','dawn_volley']:
        pair = [t for t in main['trials'] if t['kind']==kind and t['ability']==ability]
        differences = diffs(clean(pair[0]['events']), clean(pair[1]['events']))
        row = {'ability':ability,'kind':kind,'exact_after_stripping_lifecycle_ids':not differences,'differences':differences}
        if ability=='kodanda' and kind=='release_impact':
            origins = [[e for e in t['events'] if e['kind']=='release'][0]['geometry']['projectiles'][0]['origin'] for t in pair]
            row['muzzle_difference_m'] = math.dist(*origins)
            row['interpretation'] = 'Independent actor trials did not enforce identical initial rig transition state. Short Kodanda retains a muzzle/contact difference. This is not exact pose pairing or evidence that options changed authority. Exact same-stream dual-effects replay separately tests option semantics.'
        pairs.append(row)
dump('cross-trial-pair-comparison.json', {'ignored_lifecycle_keys':ignored,'pairs':pairs,'exact_pairs':sum(p['exact_after_stripping_lifecycle_ids'] for p in pairs),'total_pairs':len(pairs)})
pin_mismatches = [p for p,s in main['source_sha256'].items() if sha(ROOT / p.removeprefix('res://')) != s]
promotion_rows = []
for group in ['source_files','cache_files']:
    for path,row in promotion[group].items():
        current = main['source_sha256'].get('res://'+path)
        if current is not None:promotion_rows.append({'path':path,'sha256':current,'matches':current==row['sha256']})
freshness=[]
for path in main['source_sha256']:
    if not path.endswith('.import'):continue
    data=(ROOT/path.removeprefix('res://')).read_text()
    source=re.search(r'^source_file="([^"]+)"',data,re.M)[1]
    imported=re.search(r'^path="([^"]+)"',data,re.M)[1]
    md5_path=(ROOT/imported.removeprefix('res://')).with_suffix('.md5')
    cache_md5=re.search(r'^source_md5="([^"]+)"',md5_path.read_text(),re.M)[1]
    raw_md5=hashlib.md5((ROOT/source.removeprefix('res://')).read_bytes()).hexdigest()
    freshness.append({'source':source,'cache_source_md5':cache_md5,'source_md5':raw_md5,'matches':cache_md5==raw_md5})
checks={
    'main_native_162_checks_pass':main['passed'] and main['count']==162 and all(x['passed'] for x in main['checks']),
    'twenty_exact_event_replays_pass':replay['passed'] and replay['count']==20 and all(x['passed'] for x in replay['checks']),
    'replay_pins_exact_accepted_event_report':replay['source_event_report_sha256']==sha(HERE/'warning-lifecycle-r3.json'),
    'both_final_logs_clean':all(not re.search(r'(?m)^(?:SCRIPT ERROR|ERROR|WARNING):',(HERE/name).read_text()) for name in ['warning-lifecycle-r3.log','options-replay.log']),
    'all_executed_source_pins_match':not pin_mismatches,
    'all_17_promotion_records_covering_16_unique_files_match':len(promotion_rows)==17 and len({r['path'] for r in promotion_rows})==16 and all(r['matches'] for r in promotion_rows),
    'four_observed_import_cache_sources_fresh':len(freshness)==4 and all(r['matches'] for r in freshness),
    'ten_independent_trial_pairs_reported_without_erasing_difference':len(pairs)==10 and sum(p['exact_after_stripping_lifecycle_ids'] for p in pairs)==9,
}
def command(script,report,timeout,fixed=False):
    cmd=['taskset','-c','3','timeout',str(timeout)+'s','godot','--headless','--max-threads','1']
    if fixed:cmd+=['--fixed-fps','60']
    return cmd+['--path',str(ROOT),'--script','res://docs/evidence/visual-rounds/round4/role11/'+script,'--','--report='+str(HERE/report)]
receipt={
    'task':'R4-11','passed':all(checks.values()),'checks':checks,
    'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
    'promotion_sha256':sha(promotion_file),'strict_proposal_sha256':promotion['proposal_sha256'],
    'sources':main['source_sha256'],'promotion_matches':promotion_rows,'import_freshness':freshness,
    'source_mismatches':pin_mismatches,'paired_replay_observations':sum(r['paired_observations'] for r in replay['checks']),
    'main_command':command('warning_lifecycle_probe.gd','warning-lifecycle-r3.json',55,True),
    'replay_command':command('options_replay_probe.gd','options-replay.json',25),
    'both_exit_codes':0,'thread_limits':{'OPENBLAS_NUM_THREADS':1,'OMP_NUM_THREADS':1,'LP_NUM_THREADS':1},
    'xdg_prefixes':{'main':'/tmp/yuga-r4-role11-r3','replay':'/tmp/yuga-r4-role11-replay'},
    'artifacts':{name:sha(HERE/name) for name in ['warning_lifecycle_probe.gd','warning-lifecycle-r3.json','warning-lifecycle-r3.log','options_replay_probe.gd','options-replay.json','options-replay.log','cross-trial-pair-comparison.json']},
    'scope':'Native accepted-event and real-node geometry/visibility tests plus exact-event dual-options replay. Existing promoted player imports. No imports/renders/pixel/camera/continuous motion clearance/GPU proof. Actor trial Kodanda muzzle difference and body Step overshoot retained.'}
dump('test-receipt.json',receipt)
print(json.dumps({'passed':receipt['passed'],'checks':checks,'paired_replay_observations':receipt['paired_replay_observations'],'muzzle_difference_m':pairs[0]['muzzle_difference_m']},indent=2))
raise SystemExit(0 if receipt['passed'] else 1)
