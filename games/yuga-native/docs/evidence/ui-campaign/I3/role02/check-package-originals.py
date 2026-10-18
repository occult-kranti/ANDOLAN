#!/usr/bin/env python3
"""Independent captured-frame expectations and identity audit; no renderer."""
import argparse, hashlib, json, pathlib, re, struct

p = argparse.ArgumentParser()
p.add_argument('--capture', required=True, type=pathlib.Path)
p.add_argument('--export', required=True, type=pathlib.Path)
p.add_argument('--report', required=True, type=pathlib.Path)
a = p.parse_args()

def sha(path):
    with path.open('rb') as file:
        return hashlib.file_digest(file, 'sha256').hexdigest()

def at(value, path):
    for key in path.split('.'):
        if not isinstance(value, dict) or key not in value:
            return None
        value = value[key]
    return value

run = json.loads((a.capture / 'run.json').read_text())
export = json.loads(a.export.read_text())
checks = []

def check(name, value, detail=None):
    checks.append({'name': name, 'passed': bool(value), 'detail': detail})

check('Completed exact package run and native Quit0', run.get('mode') == 'package' and run.get('complete') is True and run.get('verified_exit_code') == 0 and run.get('cleanup_exit') == 0)
check('Export identity and all committed source pins agree', run['export_manifest']['sha256'] == sha(a.export) and run['export_manifest']['source'] == export['source'] and run['source_sha256'] == {k: v['sha256'] for k, v in export['source']['files'].items()})
check('Captured package identity is final independently audited archive', run['package_archive']['sha256'] == '56a435f909b05a9674a693dc3c5b50c45aefc5d0aaca8455b73571af9ea340b5' == sha(pathlib.Path(run['package_archive']['path'])) and all(sha(pathlib.Path(k)) == v for k, v in run['package_sha256'].items()) and export['packs']['linux']['sha256'] in run['package_sha256'].values())
check('Package source instrumentation and manifest stayed unchanged', all(run.get(k) is True for k in ['package_unchanged', 'source_unchanged', 'instrumentation_unchanged', 'archive_unchanged', 'export_manifest_unchanged']))
check('Native input events identify owned windows', bool(run.get('events')) and all(type(e.get('window_id')) is int and e['window_id'] > 0 for e in run['events']))
planned = [s for s in run['plan'] if 'capture' in s]
shots = run['shots']
automatic = run['automatic_shots']
check('Every planned original captured once', len(shots) == len(planned) and len({s['file'] for s in shots}) == len(shots) and {s['file'] for s in shots} == {s['capture'] + '.png' for s in planned})
for step in planned:
    name = step['capture']
    receipt = json.loads((a.capture / (name + '.json')).read_text())
    image = a.capture / receipt['file']
    recorded = next((s for s in shots if s['file'] == receipt['file']), None)
    data = image.read_bytes()
    check(name + ' original image and complete receipt agree', receipt == recorded and receipt['sha256'] == sha(image) and receipt['png_status'] == 0 and data[:8] == b'\x89PNG\r\n\x1a\n' and struct.unpack('>II', data[16:24]) == (960, 540) and receipt['size'] == [960, 600])
    mismatches = {k: {'expected': v, 'captured': at(receipt, k)} for k, v in step.get('expect', {}).items() if at(receipt, k) != v}
    check(name + ' planned state holds in actual captured frame', not mismatches, mismatches)
for recorded in automatic:
    image = a.capture / recorded['file']
    receipt = json.loads(image.with_suffix('.json').read_text())
    data = image.read_bytes()
    check(recorded['file'] + ' automatic original and receipt agree', recorded == receipt and sha(image) == receipt['sha256'] and receipt['png_status'] == 0 and data[:8] == b'\x89PNG\r\n\x1a\n' and struct.unpack('>II', data[16:24]) == (960, 540))
check('Exact PNG inventory with no duplicate or unrecorded originals', len({s['file'] for s in shots + automatic}) == len(shots + automatic) and {s['file'] for s in shots + automatic} == {f.name for f in a.capture.glob('*.png')})
stages = run['authority_staging']['stages']
planned_stages = [s['stage'] for s in run['plan'] if 'stage' in s]
check('Explicit stages agree with plan', len(stages) == len(planned_stages) and [s['action'] for s in stages] == planned_stages and all(s['passed'] is True and s['scope'].startswith('STAGED AUTHORITY:') for s in stages) and run['authority_staging']['enabled'] == bool(planned_stages))
diagnostics = re.findall(r'^.*(?:SCRIPT ERROR|ERROR:|WARNING:|ObjectDB instances leaked).*$', (a.capture / 'godot.log').read_text(), re.M)
check('No engine diagnostics', not diagnostics, diagnostics)
result = {'passed': all(c['passed'] for c in checks), 'count': len(checks), 'passed_count': sum(c['passed'] for c in checks), 'checks': checks, 'run_sha256': sha(a.capture / 'run.json'), 'manual_count': len(shots), 'automatic_count': len(automatic), 'scope': 'Independent exact-package identity, original image integrity and captured plan expectations. Pixel legibility is separately reviewed from unedited originals; stages remain explicitly labeled.'}
a.report.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({k: result[k] for k in ['passed', 'count', 'passed_count', 'manual_count', 'automatic_count']}))
raise SystemExit(0 if result['passed'] else 1)
