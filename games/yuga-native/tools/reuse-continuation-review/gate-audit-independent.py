#!/usr/bin/env python3
"""Challenge the gate-route acceptance oracle without writing gameplay state."""
from pathlib import Path
import argparse
import copy
import hashlib
import importlib.util
import json

parser = argparse.ArgumentParser()
parser.add_argument('--report', type=Path, required=True)
args = parser.parse_args()
if not args.report.is_absolute() or args.report.exists():
    parser.error('Use a fresh absolute report path')
target = Path(__file__).resolve().parents[1] / 'reuse-gate-input/run.py'
spec = importlib.util.spec_from_file_location('gate_owner_probe', target)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

def row(frame, z, y=0):
    return {'active': True, 'paused': False, 'overview': False,
            'physics_frame': frame, 'position': [-40, y, z],
            'grounded': True, 'gate_ray': {'clear': True},
            'input': {'forward': True, 'back': False, 'left': False, 'right': False, 'fire': False}}

# Both gate planes need to be cleared, not just the mathematical center line.
full = [row(i + 1, -64 + i * .1) for i in range(191)]
full += [row(len(full) + i + 1, -45 - i * .1) for i in range(191)]
center_jitter = [row(i + 1, z) for i, z in enumerate([-54.2, -54.1, -53.9, -53.8, -53.9, -54.1])]
elevated = copy.deepcopy(full)
for item in elevated:
    item['position'][1] = 12
no_input = copy.deepcopy(full)
for item in no_input:
    item['input'] = {key: False for key in item['input']}

cases = [('full-grounded-crossing-control', full, True),
         ('center-jitter-does-not-traverse-gate', center_jitter, False),
         ('grounded-above-roof-does-not-traverse-opening', elevated, False),
         ('no-ordinary-movement-intent-is-not-input-qualification', no_input, False)]
rows = []
for name, samples, expected in cases:
    result = module.audit_route(samples)
    rows.append({'name': name, 'expected_acceptance': expected,
                 'actual_acceptance': result['passed'], 'pass': result['passed'] == expected,
                 'oracle_result': result})
report = {'target': str(target), 'sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
          'scope': 'Synthetic challenge of acceptance oracle only; no actual game/input result.',
          'checks': rows, 'passed': all(row['pass'] for row in rows)}
args.report.parent.mkdir(parents=True, exist_ok=True)
args.report.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({'passed': report['passed'], 'checks': len(rows), 'failed': [row['name'] for row in rows if not row['pass']]}))
raise SystemExit(0 if report['passed'] else 1)
