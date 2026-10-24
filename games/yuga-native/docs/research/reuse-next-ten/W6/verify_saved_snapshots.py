#!/usr/bin/env python3
"""Read-only check of saved native/received snapshots; no runtime or network.

Godot re-encodes received floating JSON numbers when writing client reports.
Numeric equality uses absolute 1e-9; IDs, booleans and all other metadata remain exact.
"""
import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIELDS = ['x', 'y', 'z', 'yaw', 'pitch', 'bridgeAckSeq', 'bridgeInputTick', 'bridgeSlot', 'bridgeEpoch', 'nativeTick', 'grounded', 'support', 'shot', 'velocity']
MAX_DELTA = 0.0


def equivalent(left, right):
    global MAX_DELTA
    if isinstance(left, bool) or isinstance(right, bool):
        return type(left) is type(right) and left == right
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        if not math.isfinite(left) or not math.isfinite(right):
            return False
        delta = abs(left - right)
        MAX_DELTA = max(MAX_DELTA, delta)
        return delta <= 1e-9
    if isinstance(left, dict) and isinstance(right, dict):
        return left.keys() == right.keys() and all(equivalent(left[key], right[key]) for key in left)
    if isinstance(left, list) and isinstance(right, list):
        return len(left) == len(right) and all(equivalent(a, b) for a, b in zip(left, right))
    return type(left) is type(right) and left == right


def main():
    positive = json.loads((HERE / 'positive-report.json').read_text())
    fixture = positive['sourceSha256']['games/yuga-native/assets/contracts/physics-fixture-v1.json']
    contract = positive['sourceSha256']['games/yuga-native/tools/arena-bridge-pilot/bridge-contract.json']
    native = {int(row['nativeTick']): row for row in positive['native']['samples']}
    stage_names = ['stacked', 'ramp-stairs', 'ledge-ceiling', 'aim', 'underpass', 'expiry']
    checks, coverage = [], {}
    for role in ['host', 'guest']:
        recordings = json.loads((HERE / f'{role}-report.json').read_text())['recordings']
        count, matched, tail, bad = 0, 0, [], []
        for index, snapshot in enumerate(recordings):
            bridge = snapshot['bridge']
            if bridge['fixtureHash'] != fixture or bridge['contractHash'] != contract or bridge['schema'] != 1 or bridge['authority'] != 'native-3d-pilot-v1' or bridge['browserPlanarStepDisabled'] is not True:
                bad.append({'index': index, 'error': 'contract identity'})
            tick = int(bridge['nativeTick'])
            if tick == 0:
                continue
            count += 1
            if bridge['stage'] != stage_names[int(bridge['epoch'])]:
                bad.append({'index': index, 'error': 'stage epoch'})
            if len(snapshot['actors']) != 2 or {a['bridgeSlot'] for a in snapshot['actors']} != {0, 1}:
                bad.append({'index': index, 'error': 'slot mapping'})
            if tick not in native:
                tail.append(tick)
                continue
            state = native[tick]
            rows = {actor['id']: actor for actor in state['actors']}
            if not equivalent({key: bridge[key] for key in ['epoch', 'stage', 'nativeTime']}, {key: state[key] for key in ['epoch', 'stage', 'nativeTime']}):
                bad.append({'index': index, 'error': 'envelope mismatch'})
            for actor in snapshot['actors']:
                if actor['id'] not in rows or not equivalent({key: actor.get(key) for key in FIELDS}, {key: rows[actor['id']].get(key) for key in FIELDS}):
                    bad.append({'index': index, 'error': 'native actor payload mismatch', 'identity': actor['id']})
            matched += 1
        coverage[role] = {'all_snapshots': len(recordings), 'nonwaiting_snapshots': count, 'native_saved_sample_matches': matched, 'tail_native_ticks_after_saved_report': tail, 'failures': bad}
        checks.append({'name': role + ' every received snapshot contract identity and native saved-sample parity', 'passed': not bad})
    report = {'schema': 1, 'scope': 'Read-only saved snapshots. Numeric absolute tolerance 1e-9 covers Godot JSON re-encoding; metadata/types remain exact. Last client tick 603 lies after saved native report tick 600 and is explicitly uncovered by sample parity.', 'fixture_sha256': fixture, 'contract_sha256': contract, 'source_reports': {name: hashlib.sha256((HERE / name).read_bytes()).hexdigest() for name in ['positive-report.json', 'host-report.json', 'guest-report.json']}, 'numeric_tolerance_absolute': 1e-9, 'maximum_observed_numeric_delta': MAX_DELTA, 'coverage': coverage, 'checks': checks, 'passed': all(check['passed'] for check in checks)}
    print(json.dumps(report, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
