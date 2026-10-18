"""Read stored candidate bytes and replay retained native draw transforms.

This does not import the new GLB or claim native candidate execution. Godot
reorders skin vertices, so source vertex IDs are not used as a correspondence.
Actual native influence points are checked against the source rest point set.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
from scipy.spatial import cKDTree

from build_candidate import ROOT, GLB, head_surfaces, compare, selfcheck, DTYPES, WIDTHS


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def transform(v, matrix):
    return (np.c_[v, np.ones(len(v))] @ matrix.T)[:, :3]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--candidate', type=Path, required=True)
    ap.add_argument('--native', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    a = ap.parse_args()
    manifest = json.loads((a.candidate / 'source-manifest.json').read_text())
    result = {'schema': 1, 'scope': 'Stored GLB preservation/rest and offline source-candidate replay on retained native draw samples. New candidate not imported or rendered.',
              'sources': {str(p): sha(p) for p in [Path(__file__), Path(__file__).with_name('build_candidate.py'), a.candidate / 'source-manifest.json', a.native]},
              'primitive_controls': selfcheck(), 'levels': {}}
    for level, row in manifest['levels'].items():
        old = GLB(ROOT / row['source']); new = GLB(a.candidate / Path(row['output']).name)
        assert hashlib.sha256(old.raw).hexdigest() == row['source_sha256']
        assert hashlib.sha256(new.raw).hexdigest() == row['sha256']
        assert old.doc == new.doc and len(old.raw) == len(new.raw)
        ids = np.array(row['selected_vertex_ids']); p = old.doc['meshes'][2]['primitives'][2]
        allowed = np.zeros(len(old.binary), bool)
        for name in ['POSITION', 'NORMAL', 'TANGENT']:
            ac = old.doc['accessors'][p['attributes'][name]]; view = old.doc['bufferViews'][ac['bufferView']]
            size = DTYPES[ac['componentType']].itemsize * WIDTHS[ac['type']]
            for i in ids:
                start = view.get('byteOffset', 0) + ac.get('byteOffset', 0) + int(i) * view.get('byteStride', size)
                allowed[start:start + size] = True
        b, c = np.frombuffer(old.binary, dtype='u1'), np.frombuffer(new.binary, dtype='u1')
        assert not np.any((b != c) & ~allowed)
        # Counterexample: a mutation outside those records must fail the same gate.
        outside = int(np.flatnonzero(~allowed)[0]); changed = c.copy(); changed[outside] ^= 1
        assert np.any((b != changed) & ~allowed)
        v = new.array(p['attributes']['POSITION']); n = new.array(p['attributes']['NORMAL'])[ids]
        tangent = new.array(p['attributes']['TANGENT'])[ids]
        assert np.isfinite(v).all() and np.isfinite(n).all() and np.isfinite(tangent).all()
        assert np.max(abs(np.linalg.norm(n, axis=1) - 1)) < 1e-6
        assert np.max(abs(np.linalg.norm(tangent[:, :3], axis=1) - 1)) < 1e-6
        assert np.max(abs(np.sum(n * tangent[:, :3], axis=1))) < 1e-6
        assert np.all(np.isin(tangent[:, 3], [-1, 1]))
        tri = new.array(p['indices']).reshape(-1, 3)
        tri = tri[np.any(np.isin(tri, ids), axis=1)]
        assert np.all(np.isin(tri, ids))
        actual = compare(v[tri].astype(float), head_surfaces(new), band=.04)
        assert actual['crossings'] == 0 and actual['guaranteed_lower_bound_m'] > .001
        result['levels'][level] = {'actual_stored_float_rest_clearance': actual,
            'json_and_size_exact': True, 'outside_selected_bytes_exact': True,
            'outside_byte_mutation_rejected': True, 'finite_unit_orthogonal_frames': True}
        print(level, 'stored float gap mm', actual['guaranteed_lower_bound_m'] * 1000, flush=True)
    old = GLB(ROOT / manifest['levels']['near']['source'])
    new = GLB(a.candidate / 'rama-hero.glb')
    native_raw = gzip.decompress(a.native.read_bytes()) if a.native.suffix == '.gz' else a.native.read_bytes()
    native = json.loads(native_raw)
    assert native['passed'] and len(native['samples']) == 348
    assert native['source_before'] == native['source_after']
    assert native['source_before']['res://assets/heroes/rama-hero.glb'] == manifest['levels']['near']['source_sha256']
    ib = old.array(old.doc['skins'][0]['inverseBindMatrices']).reshape(-1, 4, 4).transpose(0, 2, 1).astype(float)
    rest = np.linalg.inv(ib)
    assert old.doc['nodes'][old.doc['skins'][0]['joints'][104]]['name'] == 'head'
    skin = old.doc['meshes'][2]['primitives'][11]
    source_points = old.array(skin['attributes']['POSITION'])
    influences = native['hand_geometry']['vertices']
    points, bones, weights, destinations, recovered, spread = [], [], [], [], [], []
    for index, slots in enumerate(influences):
        ps = []
        for slot in slots:
            points.append([*slot['point'], 1]); bones.append(slot['bone'])
            weights.append(slot['weight']); destinations.append(index)
            ps.append((rest[slot['bone']] @ [*slot['point'], 1])[:3])
        ps = np.array(ps); recovered.append(ps[0]); spread.append(float(np.linalg.norm(ps - ps[0], axis=1).max()))
    error, _ = cKDTree(source_points).query(recovered)
    assert error.max() < 2e-6 and max(spread) < 2e-6
    points, bones, weights, destinations = map(np.array, [points, bones, weights, destinations])
    p = new.doc['meshes'][2]['primitives'][2]
    ids = np.array(manifest['levels']['near']['selected_vertex_ids'])
    v = new.array(p['attributes']['POSITION']); tri = new.array(p['indices']).reshape(-1, 3)
    tri = tri[np.all(np.isin(tri, ids), axis=1)]
    lookup = np.full(len(v), -1); lookup[ids] = np.arange(len(ids)); tri = lookup[tri]
    head_points = transform(v[ids], ib[104])
    hand_triangles = np.array(native['hand_geometry']['triangles'])
    rows = []
    for s in native['samples']:
        poses = np.array(s['bone_globals']); rig = np.array(s['rig_global'])
        weighted = np.einsum('nij,nj->ni', poses[bones], points)[:, :3] * weights[:, None]
        hand = np.zeros((len(influences), 3)); np.add.at(hand, destinations, weighted)
        hand = transform(hand, rig)[hand_triangles]
        rail = transform(transform(head_points, poses[104]), rig)[tri]
        assert np.isfinite(rail).all() and np.isfinite(hand).all()
        check = compare(rail, hand, band=.04)
        rows.append({'id': s['id'], **check})
    passed = all(r['crossings'] == 0 and r['guaranteed_lower_bound_m'] > .002 for r in rows)
    result['draw_replay'] = {'native_raw_sha256': hashlib.sha256(native_raw).hexdigest(),
        'native_motion_sha256': native['source_before']['res://scripts/rama_motion.gd'],
        'near_only': True, 'samples': len(rows), 'passed': passed,
        'maximum_native_influence_rest_spread_m': max(spread), 'maximum_recovered_source_point_error_m': float(error.max()),
        'source_vertex_indices_not_used_for_correspondence': True,
        'minimum_separation_lower_bound_m': min(r['guaranteed_lower_bound_m'] for r in rows),
        'total_crossing_pairs': sum(r['crossings'] for r in rows), 'rows': rows}
    result['passed'] = passed
    a.output.write_text(json.dumps(result, indent=2) + '\n')
    print('348 near rail/hand replay', passed, result['draw_replay']['minimum_separation_lower_bound_m'], flush=True)
    sys.exit(0 if passed else 1)


if __name__ == '__main__':
    main()
