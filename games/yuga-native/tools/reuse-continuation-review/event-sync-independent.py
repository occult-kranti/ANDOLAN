#!/usr/bin/env python3
"""Independent mutations of actual source-bound event/socket receiver capture."""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--trace', type=Path, required=True)
parser.add_argument('--report', type=Path, required=True)
args = parser.parse_args()
if not args.report.is_absolute() or args.report.exists():
    parser.error('Use fresh absolute report filename')
source = Path(__file__).resolve().parents[1] / 'reuse-event-sync/inspect_sidecar.py'
spec = importlib.util.spec_from_file_location('owner_sidecar', source)
owner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(owner)
trace, file_hash, raw_hash = owner.read_trace(args.trace)
base = copy.deepcopy(trace)
base['timelines'] = [base['timelines'][0]]
checks = []

def check(label, data, expect, extra=None):
    try:
        result = owner.inspect(data)
        checks.append({'name': label, 'passed': result['accepted'] == expect and (extra(result) if extra else True),
                       'expected_acceptance': expect, 'actual_acceptance': result['accepted'],
                       'findings': result['findings']})
    except Exception as error:
        checks.append({'name': label, 'passed': False, 'exception': repr(error)})

def mutate(label, action, extra=None):
    value = copy.deepcopy(base)
    action(value['timelines'][0])
    check(label, value, False, extra)

check('exact-retained-capture-positive', trace, True)
mutate('missing-effect-observation-stays-null', lambda t: t['events'][2].pop('effect'),
       lambda result: result['timelines'][0]['observations'][2]['effect'] is None)
mutate('missing-audio-observation-stays-null', lambda t: t['events'][2].pop('audio'),
       lambda result: result['timelines'][0]['observations'][2]['audio'] is None)
mutate('wrong-event-socket-identity-rejected', lambda t: t['events'][2].__setitem__('socket_observed_for', [999, 999]))
mutate('duplicated-receiver-event-rejected', lambda t: t['events'].insert(3, copy.deepcopy(t['events'][2])))
mutate('receiver-return-failure-rejected', lambda t: t['events'][2]['audio']['return'].__setitem__('ok', False))
mutate('ten-second-presentation-delay-not-synchronous', lambda t: [frame.__setitem__('capture_clock_s', frame['capture_clock_s'] + 10) for frame in t['frames']])
mutate('missing-middle-presentation-frame-is-visible', lambda t: t['frames'].pop(len(t['frames']) // 2))
mutate('timeline-rate-label-cannot-be-forged', lambda t: t.__setitem__('presentation_hz', 1))
mutate('backwards-event-capture-clock-rejected', lambda t: t['events'][5].__setitem__('capture_clock_s', 0))
mutate('missing-presentation-motion-state-is-a-finding', lambda t: t['frames'][0].__setitem__('motion', None))
report = {'kind': 'independent-event-sync-review', 'trace_file_sha256': file_hash, 'trace_json_sha256': raw_hash,
          'implementation': {'path': str(source), 'sha256': hashlib.sha256(source.read_bytes()).hexdigest()},
          'scope': 'Actual capture inspection and synthetic corruption controls; no new raster or listening result.',
          'checks': checks, 'passed': all(c['passed'] for c in checks)}
args.report.parent.mkdir(parents=True, exist_ok=True)
args.report.write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({'passed': report['passed'], 'checks': len(checks), 'failures': [c['name'] for c in checks if not c['passed']]}))
raise SystemExit(0 if report['passed'] else 1)
