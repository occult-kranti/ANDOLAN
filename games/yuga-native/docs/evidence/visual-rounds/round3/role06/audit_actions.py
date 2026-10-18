#!/usr/bin/env python3
"""Audit the original six-shot public-cast receipts without modifying captures."""
import argparse
import hashlib
import json
from pathlib import Path

EXPECTED = {
    'kodanda-normal': (.15, 'windup', 0),
    'piercing_dawn-normal': (.60, 'windup', 0),
    'measured_step-normal': (.20, 'recovery', 1),
    'guardian_circle-normal': (.50, 'windup', 0),
    'dawn_volley-normal': (.90, 'windup', 0),
    'dawn_volley-reduced': (.90, 'windup', 0),
}

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence', type=Path, default=Path(__file__).parent)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists(), 'Use a fresh receipt path'
    reports, records, reduced = {}, [], []
    for branch in ['baseline', 'candidate-r7']:
        directory = args.evidence / branch / 'actions'
        report = json.loads((directory / 'capture.json').read_text())
        reports[branch] = report
        shots = {row['id']: row for row in report['shots']}
        controls = {row['id']: row for row in report['sequence_controls']}
        assert set(shots) == set(controls) == set(EXPECTED)
        for name, (age, stage, releases) in EXPECTED.items():
            shot, control = shots[name], controls[name]
            checks = {
                'raw_hash': digest(directory / shot['file']) == shot['sha256'],
                'source_unchanged': report['source_unchanged'],
                'public_cast_accepted': control['cast']['accepted'],
                'authority_age': abs(control['actual_authority_age_s'] - age) < 1e-10,
                'motion_stage': shot['motion']['stage'] == stage,
                'release_count': control['release_count'] == releases,
                'native_target': control['native_aim_ray']['collider'].endswith('/Target03'),
                'hero_in_frame': shot['bounds']['passed'],
                'receiver_in_frame': control['receiver_bounds']['passed'],
                'visible_warnings_in_frame': all(x['passed'] for x in control['active_warning_bounds']),
                'actual_floor': shot['ground_contact']['hit'] and shot['ground_contact']['collider'] == 'CourtyardFloor',
                'reduced_effects': control['effects']['reduced_effects'] == name.endswith('-reduced'),
                'no_reduced_motion': not control['effects']['reduced_motion'],
            }
            records.append({'branch': branch, 'id': name, 'checks': checks,
                            'authority_age_s': control['actual_authority_age_s'],
                            'effect_age_s': control['effects']['casts'][0]['age_s'],
                            'raw_sha256': shot['sha256']})
        normal, limited = shots['dawn_volley-normal'], shots['dawn_volley-reduced']
        nc, lc = controls['dawn_volley-normal'], controls['dawn_volley-reduced']
        keys = ['camera', 'player_transform', 'visual_yaw', 'night', 'pose_pin',
                'rendered_pose_pin', 'rendered_pose_globals', 'light', 'viewport',
                'render_settings', 'body_velocity', 'ground_contact']
        same = {key: normal[key] == limited[key] for key in keys}
        same.update({key: nc[key] == lc[key] for key in
                     ['actual_authority_age_s', 'native_aim_ray', 'receiver_bounds',
                      'active_warning_bounds', 'release_count']})
        same['effect_cast_phase'] = nc['effects']['casts'] == lc['effects']['casts']
        same['fewer_effect_triangles'] = lc['effects']['triangles'] < nc['effects']['triangles']
        reduced.append({'branch': branch, 'controls': same,
                        'normal_triangles': nc['effects']['triangles'],
                        'reduced_triangles': lc['effects']['triangles'],
                        'scope': 'Separate reset/cast generations and administrative sample/reset counters differ; final geometry pose, camera, light, aim and authority/effect phase are exact.'})
    base, candidate = reports['baseline'], reports['candidate-r7']
    pair = {
        'all_six_action_receipts_exact': base['sequence_controls'] == candidate['sequence_controls'],
        'all_ability_events_exact': base['ability_events'] == candidate['ability_events'],
    }
    passed = all(all(row['checks'].values()) for row in records) and all(all(row['controls'].values()) for row in reduced) and all(pair.values())
    result = {'complete': True, 'passed': passed, 'script_sha256': digest(Path(__file__)),
              'report_sha256': {branch: digest(args.evidence / branch / 'actions/capture.json') for branch in reports},
              'shots': records, 'reduced_effects_comparisons': reduced, 'paired_receipts': pair,
              'scope': 'Native authority/framing provenance only. Original-image review separately decides visibility and art quality. Effect presentation clock leads authority by one recorded 30 Hz tick.'}
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'passed': passed, 'originals': len(records), 'paired_receipts': pair}))
    raise SystemExit(0 if passed else 1)

if __name__ == '__main__':
    main()
