"""Strict roof-pair metadata comparison. No image quality inference."""
import argparse
import hashlib
import json
from pathlib import Path

IGNORED = {'process_frame', 'physics_frame', 'drawn_frame', 'file', 'sha256', 'roof', 'collision_objects'}

def differences(a, b, path=''):
    if type(a) is not type(b): return [{'path': path, 'a': a, 'b': b}]
    if isinstance(a, dict):
        result = []
        for key in sorted(a.keys() | b.keys()):
            if key not in a or key not in b: result.append({'path': path + '/' + key, 'missing': 'baseline' if key not in a else 'candidate'})
            else: result.extend(differences(a[key], b[key], path + '/' + key))
        return result
    if isinstance(a, list):
        if len(a) != len(b): return [{'path': path, 'length_a': len(a), 'length_b': len(b)}]
        return [entry for i, (x, y) in enumerate(zip(a, b)) for entry in differences(x, y, path + '/' + str(i))]
    return [] if a == b else [{'path': path, 'a': a, 'b': b}]

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    a, b = (json.loads(p.read_text()) for p in (args.baseline, args.candidate))
    assert a['complete'] and b['complete'] and len(a['shots']) == len(b['shots']) == 2
    results = []
    for x, y in zip(a['shots'], b['shots']):
        assert x['id'] == y['id']
        control_diff = differences({k: v for k, v in x.items() if k not in IGNORED}, {k: v for k, v in y.items() if k not in IGNORED})
        old = x['collision_objects']
        added = [entry for entry in y['collision_objects'] if '/ReviewBlock2RoofLoggia/' in entry['path']]
        retained = [entry for entry in y['collision_objects'] if '/ReviewBlock2RoofLoggia/' not in entry['path']]
        collision_diff = differences(old, retained)
        added_ok = len(added) == 1 and added[0]['layer'] == 1 and added[0]['mask'] == 0 and len(added[0]['shapes']) == 1 and added[0]['shapes'][0]['class'] == 'ConcavePolygonShape3D' and added[0]['shapes'][0]['faces'] == 828
        roof_ok = x['roof']['branch'] == 'baseline' and x['roof']['old_visible'] and x['roof']['new_environment_bodies'] == 0 and y['roof']['branch'] == 'candidate' and not y['roof']['old_visible'] and y['roof']['candidate_triangles'] == 828 and y['roof']['new_environment_bodies'] == 1 and x['roof']['old_transform'] == y['roof']['old_transform']
        results.append({'id': x['id'], 'passed': not control_diff and not collision_diff and added_ok and roof_ok,
                        'control_differences': control_diff, 'existing_collision_differences': collision_diff,
                        'declared_added_collision': added, 'added_collision_ok': added_ok, 'roof_replacement_ok': roof_ok,
                        'global_frame_counters': {key: [x[key], y[key]] for key in ('process_frame', 'physics_frame', 'drawn_frame')}})
    report = {'passed': all(row['passed'] for row in results), 'scope': 'Strict sampled camera/hero164bone poses/unit root+joints/light/UI/clocks and retained collision equality. One named roof/collider difference only. This does not verify final deformed mesh pixels, elevated combat, all approaches or performance.',
              'baseline_report_sha256': hashlib.sha256(args.baseline.read_bytes()).hexdigest(), 'candidate_report_sha256': hashlib.sha256(args.candidate.read_bytes()).hexdigest(),
              'shots': results}
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'passed': report['passed'], 'shots': [{'id': row['id'], 'passed': row['passed'], 'control_differences': len(row['control_differences']), 'collision_differences': len(row['existing_collision_differences'])} for row in results]}, indent=2))
    raise SystemExit(0 if report['passed'] else 1)

if __name__ == '__main__': main()
