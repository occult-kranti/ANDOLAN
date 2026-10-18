#!/usr/bin/env python3
"""Compare retained source-bound native transition tapes; no engine invocation."""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path


def load(path):
    data = path.read_bytes()
    value = json.loads(gzip.decompress(data) if path.suffix == '.gz' else data)
    if 'trace' in value:
        trace = Path(value['trace']['path'])
        # Legacy receipts retain their original absolute output spelling. The
        # adjacent archived bytes remain authoritative through both hash checks.
        trace = path.parent / trace.name
        compressed = trace.read_bytes()
        raw = gzip.decompress(compressed)
        assert hashlib.sha256(compressed).hexdigest() == value['trace']['sha256']
        assert hashlib.sha256(raw).hexdigest() == value['trace']['uncompressed_sha256']
        value = json.loads(raw)
    return value


def world(row, index):
    point = row['poses'][index][:3]
    tr = row['rig']
    q, w = tr[3:6], tr[6]
    cross = lambda a, b: [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]
    t = [2*x for x in cross(q, point)]
    u = cross(q, t)
    return [tr[i]+point[i]+w*t[i]+u[i] for i in range(3)]


def stats(value, label):
    rows = [r for r in value['rows'] if r['label'] == label]
    # The first tapes changed labels after return_to_menu; preserve those raw
    # rows but separate the subsequent authority generation from this phase.
    original_count = len(rows)
    generation = rows[0]['kit']['generation']
    rows = [r for r in rows if r['kit']['generation'] == generation]
    grounded = [r for r in rows if r['grounded']]
    foot_ids = [value['bone_names'].index('foot.'+s) for s in ('L', 'R')]
    steps = [(math.dist(world(a, i), world(b, i)), a, b, i) for a, b in zip(rows, rows[1:]) for i in foot_ids]
    peak = max(steps, key=lambda item: item[0], default=None)
    max_step = peak[0] if peak else 0
    witness = None
    if peak:
        _, a, b, i = peak
        delta = [world(b,i)[axis]-world(a,i)[axis] for axis in range(3)]
        witness = {'physics_from':a['physics'], 'physics_to':b['physics'], 'bone':value['bone_names'][i],
                   'delta_xyz_m':delta, 'horizontal_m':math.hypot(delta[0],delta[2]),
                   'locked_from':a['motion']['foot_locks'], 'locked_to':b['motion']['foot_locks']}
    locked = sum(r['motion']['foot_locks'][s] for r in rows for s in ('L', 'R'))
    actual_contact = sum(-.005 <= r['soles'][s]['minimum_m'] <= .005 for r in grounded for s in ('L', 'R'))
    return {'callbacks': len(rows), 'later_reset_rows_separated':original_count-len(rows), 'authority_generation':generation,
            'grounded_side_samples': 2*len(grounded), 'locked_side_samples': locked,
            'actual_floor_contact_side_samples': actual_contact,
            'grounded_minimum_m': min((r['soles'][s]['minimum_m'] for r in grounded for s in ('L', 'R')), default=None),
            'all_minimum_m': min(r['soles'][s]['minimum_m'] for r in rows for s in ('L', 'R')),
            'max_adjacent_world_ankle_step_m': max_step, 'peak_step_witness':witness}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--evidence', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    checks, trials, inputs = [], [], {}
    def check(name, passed, **detail):
        checks.append({'name': name, 'passed': bool(passed), 'detail': detail})
    for hz in (30, 60, 120):
        paths = [args.evidence / (f'{kind}-60'+('' if kind=='baseline' else '-r1')+'.json.gz' if hz==60 else f'{kind}-{hz}-r2.json') for kind in ('baseline','candidate')]
        a, b = map(load, paths)
        inputs[str(hz)] = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
        aligned = len(a['rows']) == len(b['rows']) and all(x['label']==y['label'] and x['physics']==y['physics'] for x,y in zip(a['rows'], b['rows']))
        check(f'{hz}Hz native callback rows align', aligned, rows=len(b['rows']))
        pairs = list(zip(a['rows'], b['rows']))
        check(f'{hz}Hz roots velocities and authority reports exact', all(all(x[k]==y[k] for k in ('root','rig','velocity','kit','army_elapsed')) for x,y in pairs) and a['events']==b['events'])
        check(f'{hz}Hz action phase transition clocks and locks exact', all(x['motion']==y['motion'] and x['transition_age']==y['transition_age'] and x['transition_duration']==y['transition_duration'] for x,y in pairs))
        check(f'{hz}Hz weapon sockets and plant anchors exact', all(x['sockets']==y['sockets'] and x['targets']==y['targets'] for x,y in pairs))
        excluded = [i for i,n in enumerate(a['bone_names']) if not ('leg' in n or n.startswith('foot') or n.startswith('toe'))]
        check(f'{hz}Hz all nonleg global poses exact', all(all(x['poses'][i]==y['poses'][i] for i in excluded) for x,y in pairs))
        check(f'{hz}Hz public cancel and protected Step full poses exact', all(x['poses']==y['poses'] for x,y in pairs if x['label'] in ('bow_cancel_entry','bow_cancel_fade','protected_measured_step')))
        labels = list(dict.fromkeys(r['label'] for r in a['rows']))
        measurements = {label: {'baseline':stats(a,label), 'candidate':stats(b,label)} for label in labels}
        target_labels = ['training_entry','reset_move_forward','reset_move_back','reset_move_left']
        check(f'{hz}Hz every targeted grounded sole improves to minus5mm gate', all(measurements[k]['candidate']['grounded_minimum_m'] >= -.005 and measurements[k]['candidate']['grounded_minimum_m'] > measurements[k]['baseline']['grounded_minimum_m'] for k in target_labels))
        check(f'{hz}Hz no phase has deeper minimum sole penetration', all(v['candidate']['all_minimum_m'] >= v['baseline']['all_minimum_m']-.000001 for v in measurements.values()))
        check(f'{hz}Hz targeted entry ankle step does not worsen', all(measurements[k]['candidate']['max_adjacent_world_ankle_step_m'] <= measurements[k]['baseline']['max_adjacent_world_ankle_step_m']+.000001 for k in target_labels))
        trials.append({'hz':hz,'measurements':measurements,'candidate_motion':b['source_sha256']['res://scripts/rama_motion.gd'],'baseline_motion':a['source_sha256']['res://scripts/rama_motion.gd'],'visible_lod_cohorts':sorted(set((r['lod'],r['cohort_vertices']) for r in b['rows']))})
    result={'passed':all(c['passed'] for c in checks),'count':len(checks),'checks':checks,'trials':trials,'inputs_sha256':inputs,'scope':'Native headless callback geometry and exact authority/write comparisons. Phase minima and adjacent ankle steps are diagnostics, not continuous rendered or C1 acceptance; same-time exclusions are separately tested.'}
    args.report.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'passed':result['passed'],'count':len(checks),'failures':[c['name'] for c in checks if not c['passed']]}))
    raise SystemExit(0 if result['passed'] else 1)


if __name__ == '__main__':
    main()
