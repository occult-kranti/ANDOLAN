#!/usr/bin/env python3
"""Independently check native R4-09 receipt against bytes and promotion."""
from pathlib import Path
import hashlib, json, re, subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def local(path):
    return ROOT / path.removeprefix('res://')

native = json.loads((HERE / 'material-lifecycle-r3.json').read_text())
promotion_path = ROOT / 'docs/evidence/visual-rounds/round3/integration/promotion.json'
promotion = json.loads(promotion_path.read_text())
pins = native['source_sha256']
pin_mismatches = [p for p, expected in pins.items() if sha(local(p)) != expected]
promotion_rows = []
for group in ('source_files', 'cache_files'):
    for path, record in promotion[group].items():
        runtime_pin = pins.get('res://' + path)
        if runtime_pin is not None:
            promotion_rows.append({'path': path, 'group': group, 'native_sha256': runtime_pin,
                                   'promotion_sha256': record['sha256'], 'matches': runtime_pin == record['sha256']})
freshness = []
for path in pins:
    if not path.endswith('.import'): continue
    data = local(path).read_text()
    source = re.search(r'^source_file="([^"]+)"', data, re.M)
    imported = re.search(r'^path="([^"]+)"', data, re.M)
    if not source or not imported: continue
    md5_path = local(imported[1]).with_suffix('.md5')
    md5 = re.search(r'^source_md5="([^"]+)"', md5_path.read_text(), re.M)
    actual = hashlib.md5(local(source[1]).read_bytes()).hexdigest()
    freshness.append({'source': source[1], 'imported': imported[1], 'md5_receipt': str(md5_path.relative_to(ROOT)),
                      'raw_md5': actual, 'cache_source_md5': md5[1], 'matches': actual == md5[1]})
log = (HERE / 'material-lifecycle-r3.log').read_text()
checks = {
    'native_49_checks_passed': native['passed'] and native['count'] == 49 and len(native['checks']) == 49 and all(x['passed'] for x in native['checks']),
    'clean_final_engine_log': not re.search(r'(?m)^(?:SCRIPT ERROR|ERROR|WARNING):', log),
    'all_247_executed_pins_match_current_bytes': len(pins) == 247 and not pin_mismatches,
    'promoted_runtime_source_and_caches_match': len(promotion_rows) == 17 and all(x['matches'] for x in promotion_rows),
    'all_observed_import_caches_name_current_source_md5': bool(freshness) and all(x['matches'] for x in freshness),
    'accepted_motion_controller_unchanged': pins['res://scripts/rama_motion.gd'] == '4c72fd247704896bbf8b720658efff1388d850912f7aed6a916950538aa458c1',
}
report = {
    'task': 'R4-09', 'passed': all(checks.values()), 'checks': checks,
    'source_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
    'promotion_sha256': sha(promotion_path), 'strict_proposal_sha256': promotion['proposal_sha256'],
    'native_report_sha256': sha(HERE / 'material-lifecycle-r3.json'),
    'native_script_sha256': sha(HERE / 'material_lifecycle_probe.gd'),
    'native_log_sha256': sha(HERE / 'material-lifecycle-r3.log'),
    'promotion_matches': promotion_rows, 'pin_mismatches': pin_mismatches, 'cache_freshness': freshness,
    'source_sha256': pins,
    'command': ['taskset', '-c', '3', 'timeout', '45s', 'godot', '--headless', '--max-threads', '1',
                '--path', str(ROOT), '--script', 'res://docs/evidence/visual-rounds/round4/role09/material_lifecycle_probe.gd',
                '--', '--report=' + str(HERE / 'material-lifecycle-r3.json')],
    'environment': {'OPENBLAS_NUM_THREADS': '1', 'OMP_NUM_THREADS': '1', 'LP_NUM_THREADS': '1',
                    'XDG_DATA_HOME': '/tmp/yuga-r4-role09-r3/data', 'XDG_CONFIG_HOME': '/tmp/yuga-r4-role09-r3/config',
                    'XDG_CACHE_HOME': '/tmp/yuga-r4-role09-r3/cache'},
    'native_exit_code': 0,
    'execution_scope': 'Existing promoted imports, native CPU only, no editor/import/render. Manual player presentation callback and existing modifier evaluation; actual tree pause. No authority, contact, pixels, continuous visual or GPU performance acceptance.',
}
(HERE / 'test-receipt.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({'passed': report['passed'], 'checks': checks, 'observed_imports': len(freshness), 'promotion_rows': len(promotion_rows)}, indent=2))
raise SystemExit(0 if report['passed'] else 1)
