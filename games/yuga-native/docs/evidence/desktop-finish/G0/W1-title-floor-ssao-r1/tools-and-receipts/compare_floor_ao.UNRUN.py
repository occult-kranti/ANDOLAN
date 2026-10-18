"""Strict controls for one AO-off pair; no pixel-quality conclusion.

Synthetic self-tests do not establish native parsing or native control equality.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path

BASE = '40739a23b74149cebda62acd6af8a7ca54ac1a39aab2538adbc5211d309a1373'
OFF = '25de5c6186aed64fa2e6df7fdb1eae545b07fea2594a6d2b9fbc0b9af6a85af0'
SCRIPT = 'scripts/hero_atmosphere.gd'
MARKER = '.graphics-six-snapshot.json'
HELPER = 'tools/graphics-six/capture_scene_anchors.gd'
OBSERVER = 'tools/ui-campaign/observer.gd'
SHOT_EXCLUSIONS = {'frame', 'physics_frame', 'render_frame', 'file', 'sha256',
                   'branch', 'atmosphere_sha256'}


def differences(a, b, path=''):
    if type(a) is not type(b):
        return [path + ': type differs']
    if isinstance(a, dict):
        errors = []
        for key in sorted(a.keys() | b.keys()):
            if key not in a or key not in b:
                errors.append(path + '/' + key + ': missing')
            else:
                errors.extend(differences(a[key], b[key], path + '/' + key))
        return errors
    if isinstance(a, list):
        if len(a) != len(b):
            return [path + ': list length differs']
        return [error for i, (x, y) in enumerate(zip(a, b))
                for error in differences(x, y, path + '/' + str(i))]
    return [] if a == b else [path + ': value differs']


def finite_tree(value):
    if isinstance(value, float):
        return math.isfinite(value)
    if isinstance(value, dict):
        return all(finite_tree(v) for v in value.values())
    if isinstance(value, list):
        return all(finite_tree(v) for v in value)
    return value is None or isinstance(value, (str, bool, int))


def normalized_shot(shot):
    shot = {k: copy.deepcopy(v) for k, v in shot.items() if k not in SHOT_EXCLUSIONS}
    # Only these two copies of the same actual enabled getter may differ.
    # Other AO parameters, all other properties and every material remain exact.
    shot['diagnostic']['ao'].pop('ssao_enabled')
    shot['diagnostic']['environment'].pop('ssao_enabled')
    return shot


def compare(a, b, allow_preflight=False):
    errors = []
    def require(ok, message):
        if not ok:
            errors.append(message)
    require(a.get('complete') is True and b.get('complete') is True, 'both branch reports complete')
    require(a.get('preflight') is b.get('preflight'), 'same preflight/native mode')
    preflight = a.get('preflight') is True
    require(not preflight or allow_preflight, 'preflight needs explicit opt-in and cannot qualify AO pixels')
    if not preflight:
        require(a.get('renderer') == b.get('renderer') == 'forward_plus', 'actual Forward+ required')
    for branch, report, expected in [('baseline', a, BASE), ('candidate', b, OFF)]:
        require(report.get('source_unchanged') is True, branch + ': source unchanged')
        sources = report.get('source_sha256', {})
        require(sources == report.get('source_after_sha256'), branch + ': before/after source dictionaries equal')
        require(sources.get(SCRIPT) == expected, branch + ': exact one-parameter source')
        for required in [MARKER, HELPER, OBSERVER]:
            require(required in sources and len(sources[required]) == 64, branch + ': pinned ' + required)
        cleanup = report.get('audio_cleanup', {})
        require(cleanup.get('observed_mixer_ticks') == 2 and 0 <= cleanup.get('wait_usec', -1) <= 250000,
                branch + ': two real mixer ticks in250ms bound')
        require(cleanup.get('budget_usec') == 250000 and cleanup.get('main_cleanup_frames') == 8,
                branch + ': shared cleanup bounds')
        require(all(c.get('passed') is True for c in report.get('checks', [])) and bool(report.get('checks')),
                branch + ': all helper checks pass')
    sa, sb = a.get('source_sha256', {}), b.get('source_sha256', {})
    require(sa.keys() == sb.keys(), 'same inventory path set')
    changed = sorted(k for k in sa.keys() | sb.keys() if sa.get(k) != sb.get(k))
    require(changed == sorted([SCRIPT, MARKER]), 'only atmosphere source and derived snapshot marker differ: ' + str(changed))
    shots_a, shots_b = a.get('shots', []), b.get('shots', [])
    require(len(shots_a) == len(shots_b) == 2, 'exactly two ordinary camera shots per branch')
    rows = []
    for index, (x, y) in enumerate(zip(shots_a, shots_b)):
        expected_id = ['00-title', '01-training'][index] if index < 2 else 'invalid'
        shot_errors = []
        require(x.get('id') == y.get('id') == expected_id, 'same prescribed shot order')
        for label, shot, expected_hash in [('baseline', x, BASE), ('candidate', y, OFF)]:
            diagnostic = shot.get('diagnostic', {})
            skeleton = diagnostic.get('hero_skeleton', {})
            names, poses = skeleton.get('bone_names', []), skeleton.get('bone_global_poses', [])
            valid_poses = len(poses) == 164 and all(isinstance(p, list) and len(p) == 4 and
                all(isinstance(v, list) and len(v) == 3 for v in p) for p in poses)
            require(len(names) == len(set(names)) == 164 and valid_poses,
                    expected_id + '/' + label + ': full unique164-bone pose')
            require(finite_tree(shot), expected_id + '/' + label + ': all controls finite')
            require(diagnostic.get('serialization_errors') == [], expected_id + '/' + label + ': no omitted/unsupported control')
            require(shot.get('branch') == label and shot.get('atmosphere_sha256') == expected_hash,
                    expected_id + '/' + label + ': declared source branch')
            for key in ['environment', 'ao', 'lights', 'meshes', 'materials', 'camera_properties', 'clocks', 'render_settings']:
                require(bool(diagnostic.get(key)), expected_id + '/' + label + ': controls present/' + key)
            expected_ao = label == 'baseline'
            if not preflight:
                require(diagnostic.get('ao', {}).get('ssao_enabled') is expected_ao and
                        diagnostic.get('environment', {}).get('ssao_enabled') is expected_ao,
                        expected_id + '/' + label + ': actual enabled getter')
        try:
            shot_errors = differences(normalized_shot(x), normalized_shot(y))
        except (KeyError, TypeError) as exc:
            shot_errors = ['required control missing: ' + str(exc)]
        errors.extend(expected_id + error for error in shot_errors)
        rows.append({'id': expected_id, 'control_differences': shot_errors,
                     'recorded_global_frame_counters': {k: [x.get(k), y.get(k)] for k in
                                                       ['frame', 'physics_frame', 'render_frame']}})
    return {'passed': not errors, 'errors': errors, 'shots': rows, 'source_delta': changed,
            'mode': 'headless preparation only' if preflight else 'actual Forward+ controls',
            'scope': 'Exact sampled164 poses, camera, simulation clocks, materials, lights, environment and UI controls; one AO-enabled toggle only. This does not judge pixels, temporal quality or hardware performance.'}


def selftest():
    transform = [[1, 0, 0], [0, 1, 0], [0, 0, 1], [0, 0, 0]]
    sources = {SCRIPT: BASE, MARKER: 'a'*64, HELPER: 'h'*64, OBSERVER: 'o'*64, 'project.godot': 'p'*64}
    shot = {'id': '00-title', 'branch': 'baseline', 'atmosphere_sha256': BASE,
            'frame': 10, 'physics_frame': 10, 'render_frame': 10, 'file': '00-title.png', 'sha256': 'x'*64,
            'diagnostic': {'hero_skeleton': {'bone_names': [str(i) for i in range(164)],
                                          'bone_global_poses': [copy.deepcopy(transform) for _ in range(164)]},
                'serialization_errors': [], 'ao': {'ssao_enabled': True, 'ssao_detail': .4},
                'environment': {'ssao_enabled': True, 'ssao_detail': .4, 'tonemap_exposure': 1.0},
                'lights': [{'energy': 1.3}], 'meshes': [{'global_transform': transform}],
                'materials': {'one': {'normal_depth': .6}}, 'camera_properties': {'near': .1},
                'clocks': {'elapsed': .2}, 'render_settings': {'msaa': 1}}}
    a = {'complete': True, 'preflight': False, 'renderer': 'forward_plus', 'source_unchanged': True,
         'source_sha256': sources, 'source_after_sha256': copy.deepcopy(sources),
         'audio_cleanup': {'observed_mixer_ticks': 2, 'wait_usec': 50000, 'budget_usec': 250000, 'main_cleanup_frames': 8},
         'checks': [{'passed': True}], 'shots': [shot, copy.deepcopy(shot)]}
    a['shots'][1]['id'] = '01-training'
    b = copy.deepcopy(a)
    for key in ['source_sha256', 'source_after_sha256']:
        b[key][SCRIPT] = OFF
        b[key][MARKER] = 'b'*64
    for s in b['shots']:
        s['branch'] = 'candidate'; s['atmosphere_sha256'] = OFF
        s['diagnostic']['ao']['ssao_enabled'] = False
        s['diagnostic']['environment']['ssao_enabled'] = False
        s['frame'] += 99
    checks = [{'name': 'one toggle and explicitly recorded global frame difference accepted', 'passed': compare(a, b)['passed']}]
    adversaries = {
        'bone pose drift': lambda q: q['shots'][0]['diagnostic']['hero_skeleton']['bone_global_poses'][163][3].__setitem__(1, .001),
        'simulation clock drift': lambda q: q['shots'][0]['diagnostic']['clocks'].__setitem__('elapsed', .3),
        'normal material drift': lambda q: q['shots'][0]['diagnostic']['materials']['one'].__setitem__('normal_depth', 0),
        'sun drift': lambda q: q['shots'][0]['diagnostic']['lights'][0].__setitem__('energy', 1.0),
        'AO detail drift': lambda q: q['shots'][0]['diagnostic']['ao'].__setitem__('ssao_detail', 0),
        'camera drift': lambda q: q['shots'][0]['diagnostic']['camera_properties'].__setitem__('near', .2),
        'AO still enabled': lambda q: q['shots'][0]['diagnostic']['ao'].__setitem__('ssao_enabled', True),
        'unrecorded material': lambda q: q['shots'][0]['diagnostic'].__setitem__('materials', {}),
        'helper differs': lambda q: q['source_sha256'].__setitem__(HELPER, 'z'*64),
        'incomplete pose': lambda q: q['shots'][0]['diagnostic']['hero_skeleton']['bone_global_poses'].pop(),
        'unsupported getter': lambda q: q['shots'][0]['diagnostic']['serialization_errors'].append('opaque RID'),
        'nonfinite pose': lambda q: q['shots'][0]['diagnostic']['hero_skeleton']['bone_global_poses'][0][0].__setitem__(0, float('nan')),
        'cleanup exhausted': lambda q: q['audio_cleanup'].__setitem__('observed_mixer_ticks', 1),
        'preflight cannot qualify actual AO': lambda q: q.__setitem__('preflight', True),
    }
    for name, mutate in adversaries.items():
        q = copy.deepcopy(b); mutate(q)
        checks.append({'name': name + ' rejected', 'passed': not compare(a, q)['passed']})
    return {'passed': all(c['passed'] for c in checks), 'checks': checks,
            'scope': 'Synthetic comparator disconfirmation only; native helper parse, getter coverage and actual equality remain unrun.'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--baseline', type=Path); p.add_argument('--candidate', type=Path)
    p.add_argument('--output', type=Path, required=True); p.add_argument('--allow-preflight', action='store_true')
    p.add_argument('--self-test', action='store_true'); args = p.parse_args()
    if args.output.exists(): p.error('fresh output required')
    if args.self_test:
        result = selftest()
    else:
        if args.baseline is None or args.candidate is None: p.error('both reports required')
        result = compare(json.loads(args.baseline.read_text()), json.loads(args.candidate.read_text()), args.allow_preflight)
        result['input_sha256'] = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in [args.baseline, args.candidate]}
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')
    print(json.dumps({'passed': result['passed'], 'mode': 'synthetic self-test' if args.self_test else result['mode']}))
    raise SystemExit(0 if result['passed'] else 1)

if __name__ == '__main__':
    main()
