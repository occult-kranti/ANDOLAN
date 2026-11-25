#!/usr/bin/env python3
"""Compare a Hanuman candidate's rig and skinned geometry with the shipped GLB.

Blender is run separately for sampled evaluated poses; --skip-blender restricts
this command to the structural GLB checks and is not an animation sign-off.
"""
import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ART = HERE.parent
sys.path.insert(0, str(ART / 'hero-rama-lod'))
from glb_lod import GLB

BASE = ART / 'hanuman-hero-finish/models/hanuman-enhanced.glb'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def equal_accessors(a, ai, b, bi, label):
    first, second = a.array(ai), b.array(bi)
    require(first.shape == second.shape and first.dtype == second.dtype and np.array_equal(first, second), label)


def structure(a, b):
    da, db = a.doc, b.doc
    na, nb = da['nodes'], db['nodes']
    require(len(na) == len(nb), 'Node count changed')
    node_fields = ('name', 'children', 'matrix', 'translation', 'rotation', 'scale', 'mesh', 'skin')
    for i, (x, y) in enumerate(zip(na, nb)):
        require(all(x.get(f) == y.get(f) for f in node_fields), f'Node transform/hierarchy changed: {i}')
    skins_a, skins_b = da['skins'], db['skins']
    require(len(skins_a) == len(skins_b), 'Skin count changed')
    for i, (x, y) in enumerate(zip(skins_a, skins_b)):
        require(x['joints'] == y['joints'] and x.get('skeleton') == y.get('skeleton'), f'Skin joint mapping changed: {i}')
        equal_accessors(a, x['inverseBindMatrices'], b, y['inverseBindMatrices'], f'Inverse bind matrices changed: skin {i}')

    animations_a, animations_b = da['animations'], db['animations']
    require(len(animations_a) == len(animations_b), 'Animation count changed')
    clip_details = []
    for aa, ab in zip(animations_a, animations_b):
        name = aa.get('name')
        require(name == ab.get('name') and len(aa['channels']) == len(ab['channels']), f'Animation/channels changed: {name}')
        times = []
        for ca, cb in zip(aa['channels'], ab['channels']):
            require(ca['target'] == cb['target'], f'Animation target changed: {name}')
            sa, sb = aa['samplers'][ca['sampler']], ab['samplers'][cb['sampler']]
            require(sa.get('interpolation', 'LINEAR') == sb.get('interpolation', 'LINEAR'), f'Interpolation changed: {name}')
            for key in ('input', 'output'):
                equal_accessors(a, sa[key], b, sb[key], f'Animation {key} changed: {name}')
            t = a.array(sa['input']).reshape(-1)
            require(np.isfinite(t).all() and (len(t) < 2 or np.all(np.diff(t) > 0)), f'Invalid animation time: {name}')
            if len(t):
                times.append((float(t[0]), float(t[-1])))
        clip_details.append({'name': name, 'channels': len(aa['channels']),
                             'first_seconds': min(x[0] for x in times), 'last_seconds': max(x[1] for x in times)})

    pa, pb = list(a.primitives()), list(b.primitives())
    require(len(pa) == len(pb), 'Primitive count changed')
    stats = []
    joint_count = len(skins_a[0]['joints'])
    for (mi, pi, x), (mj, pj, y) in zip(pa, pb):
        require((mi, pi) == (mj, pj) and x.get('material') == y.get('material') and x.get('mode', 4) == y.get('mode', 4), f'Primitive material/order/mode changed: {mi}/{pi}')
        equal_accessors(a, x['indices'], b, y['indices'], f'Topology indices changed: {mi}/{pi}')
        tx, ty = x.get('targets', []), y.get('targets', [])
        require(len(tx) == len(ty), f'Morph target count changed: {mi}/{pi}')
        for ti, (u, v) in enumerate(zip(tx, ty)):
            require(set(u) == set(v), f'Morph target attributes changed: {mi}/{pi}/{ti}')
            for semantic in u:
                equal_accessors(a, u[semantic], b, v[semantic], f'Morph target changed: {mi}/{pi}/{ti}/{semantic}')
        require(set(x['attributes']) == set(y['attributes']), f'Vertex attributes changed: {mi}/{pi}')
        xa, ya = x['attributes'], y['attributes']
        for semantic in xa:
            if semantic not in ('POSITION', 'NORMAL', 'TANGENT'):
                equal_accessors(a, xa[semantic], b, ya[semantic], f'{semantic} changed: {mi}/{pi}')
        xp, yp = a.array(xa['POSITION']), b.array(ya['POSITION'])
        require(xp.shape == yp.shape and np.isfinite(yp).all(), f'Bad positions: {mi}/{pi}')
        normal = b.array(ya['NORMAL'])
        lengths = np.linalg.norm(normal, axis=1)
        require(np.isfinite(lengths).all() and np.allclose(lengths, 1.0, atol=0.002), f'Bad normals: {mi}/{pi}')
        weights = b.array(ya['WEIGHTS_0'], normalized=True)
        joints = b.array(ya['JOINTS_0'])
        require(np.isfinite(weights).all() and (weights >= 0).all() and np.allclose(weights.sum(axis=1), 1.0, atol=0.0001), f'Bad skin weights: {mi}/{pi}')
        require(int(joints.max()) < joint_count, f'Out-of-range joint index: {mi}/{pi}')
        delta = np.linalg.norm(yp - xp, axis=1)
        stats.append({'material': da['materials'][x['material']].get('name'), 'vertices': len(xp),
                      'triangles': len(a.array(x['indices'])) // 3,
                      'max_influences': int((weights > 1e-6).sum(axis=1).max()),
                      'changed_vertices': int((delta > 1e-7).sum()),
                      'max_displacement_m': float(delta.max(initial=0))})
    return {'node_count': len(na), 'skin_joint_counts': [len(s['joints']) for s in skins_a],
            'animations': clip_details, 'primitives': stats,
            'comparison': 'Node transforms, skin joints, inverse binds, animation targets/times/values, topology, UV, colors and skin weights are exactly equal. Position, normal and tangent edits are permitted.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=Path, default=BASE)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--blender', default='blender')
    parser.add_argument('--skip-blender', action='store_true')
    args = parser.parse_args()
    baseline, candidate = args.baseline.resolve(), args.candidate.resolve()
    report = {'baseline_sha256': sha(baseline), 'candidate_sha256': sha(candidate),
              'compare_script_sha256': sha(HERE / 'compare.py'), 'blender_script_sha256': sha(HERE / 'blender_samples.py'), 'result': 'fail',
              'scope': 'Binary glTF rig/skin/action checks and, when enabled, selected Blender-evaluated pose comparisons.',
              'limits': ['Not a visual or topology-quality review.', 'Selected bone poses and vertex deltas do not prove absence of skin intersections or contact defects.', 'No engine import, runtime footage, game performance or human art acceptance is established.']}
    try:
        report['structural'] = structure(GLB(baseline), GLB(candidate))
        if not args.skip_blender:
            with tempfile.TemporaryDirectory(prefix='hanuman-rig-qa-') as temp:
                sample_file = Path(temp) / 'blender-samples.json'
                subprocess.run([args.blender, '-b', '-t', '2', '--python-exit-code', '1', '-P', str(HERE / 'blender_samples.py'), '--', str(baseline), str(candidate), str(sample_file)], check=True)
                report['blender'] = json.loads(sample_file.read_text())
        report['result'] = 'pass'
    except Exception as exc:
        report['error'] = str(exc)
        raise
    finally:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n')
    print(json.dumps({'result': report['result'], 'baseline_sha256': report['baseline_sha256'], 'candidate_sha256': report['candidate_sha256'], 'report': str(args.report)}, indent=2))


if __name__ == '__main__':
    main()
