"""Strict topology-aware comparison of two actual imported shoulder resources.

This reads W1's resource-probe outputs. It does not import, execute a scene,
render, or infer source preservation from imported tolerances.
"""
import argparse
import collections
import copy
import hashlib
import json
from pathlib import Path
import sys
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from replace_left_cap import GLB, sha

MANIFEST_SHA = '886528206ee33e1b3809e0363840ba9e08666883725985796fefbdb8da93ee0e'
MATERIALS = {2: 'Worked warm gold', 3: 'Cobalt handwoven silk',
             5: 'Recessed antique gold', 6: 'Polished sapphire'}
WIDTHS = {0: 3, 1: 3, 2: 4, 3: 4, 4: 2, 10: 4, 11: 4}


def oriented_faces(records, triangles):
    """Cyclic rotation is equivalent; reversed winding and multiplicity are not."""
    result = collections.Counter()
    for triangle in triangles:
        a, b, c = (records[int(i)] for i in triangle)
        result[min((a, b, c), (b, c, a), (c, a, b))] += 1
    return result


def read_arrays(directory, surface):
    raw = {}
    arrays = {}
    for info in surface['arrays']:
        if 'file' not in info:
            assert info['type'] == 'Nil', 'Unexpected undumped array'
            continue
        path = directory / info['file']
        assert path.parent == directory and path.name == info['file']
        data = path.read_bytes()
        assert len(data) == info['bytes'] and sha(path) == info['raw_sha256']
        index = info['index']
        raw[index] = data
        if index in WIDTHS:
            dtype = '<i4' if index == 10 else '<f4'
            arrays[index] = np.frombuffer(data, dtype=dtype).reshape(-1, WIDTHS[index])
        elif index == 12:
            arrays[index] = np.frombuffer(data, dtype='<i4').reshape(-1, 3)
    n = len(arrays[0])
    assert set([0, 1, 2, 3, 4, 10, 11, 12]) <= set(arrays)
    assert all(len(arrays[i]) == n for i in WIDTHS)
    assert arrays[12].min() >= 0 and arrays[12].max() < n
    assert all(np.isfinite(a).all() for a in arrays.values())
    # Include every stored attribute, even custom arrays not interpreted above.
    widths = {i: len(data) // n for i, data in raw.items() if i != 12}
    assert all(widths[i] * n == len(raw[i]) for i in widths)
    records = [b''.join(bytes([i]) + widths[i].to_bytes(4, 'little') +
                        raw[i][row * widths[i]:(row + 1) * widths[i]]
                        for i in sorted(widths)) for row in range(n)]
    return arrays, records


def rigid_mask(arrays, joint, bind_map):
    canonical = np.asarray(bind_map)[arrays[10]]
    return np.sum(np.where(canonical == joint, arrays[11], 0), axis=1) > .9999


def triangle_mask(mask, triangles):
    selected = np.all(mask[triangles], axis=1)
    assert np.array_equal(np.any(mask[triangles], axis=1), selected), 'Mixed selected triangle'
    return selected


def verify_new_geometry(source, primitive, arrays, mask, triangle_selection, expected):
    p = source.doc['meshes'][2]['primitives'][primitive]
    a = {k: source.array(v) for k, v in p['attributes'].items()}
    count = expected['added_vertices']
    first = len(a['POSITION']) - count
    source_ids = np.arange(first, len(a['POSITION']))
    imported_ids = np.flatnonzero(mask)
    assert len(imported_ids) == count
    assert np.array_equal(np.unique(arrays[12][triangle_selection]), imported_ids)
    assert np.all(arrays[11][imported_ids].max(axis=1) == 1)
    assert np.all(np.sum(arrays[11][imported_ids] > 0, axis=1) == 1)
    assert arrays[3][imported_ids].tobytes() == np.tile(
        np.array([1, 1, 1, 0], dtype='<f4'), (count, 1)).tobytes()
    source_lookup = {}
    records = []
    for i in source_ids:
        key = a['POSITION'][i].tobytes() + a['TEXCOORD_0'][i].tobytes()
        source_lookup.setdefault(key, []).append(int(i))
        records.append(b''.join(a[k][i].tobytes() for k in sorted(a)))
    mapping = {}
    normal_error = 0.0
    tangent_error = 0.0
    for i in imported_ids:
        key = arrays[0][i].tobytes() + arrays[4][i].tobytes()
        assert key in source_lookup, 'New POSITION/UV has no exact source row'
        choices = source_lookup[key]
        si = min(choices, key=lambda j: float(np.linalg.norm(a['NORMAL'][j] - arrays[1][i])) +
                 float(np.linalg.norm(a['TANGENT'][j] - arrays[2][i])))
        ne = float(np.linalg.norm(a['NORMAL'][si] - arrays[1][i]))
        te = float(np.linalg.norm(a['TANGENT'][si, :3] - arrays[2][i, :3]))
        # Godot packs normal/tangent directions. These explicit bounds qualify
        # only the new decoded frames; retained imported records stay byte-exact.
        assert ne < .0003 and te < .0004 and a['TANGENT'][si, 3] == arrays[2][i, 3]
        assert abs(float(np.dot(arrays[1][i], arrays[2][i, :3]))) < .0005
        normal_error = max(normal_error, ne)
        tangent_error = max(tangent_error, te)
        mapping[int(i)] = si - first
    source_tri = source.array(p['indices']).reshape(-1, 3)
    source_tri = source_tri[np.all(source_tri >= first, axis=1)] - first
    imported_tri = np.array([[mapping[int(i)] for i in t]
                             for t in arrays[12][triangle_selection]])
    # Godot's native triangle convention reverses glTF winding, then may reorder
    # indices. This explicit conversion preserves orientation and multiplicity.
    assert oriented_faces(records, source_tri[:, [0, 2, 1]]) == oriented_faces(records, imported_tri)
    return {'source_added_vertex_ids': source_ids.tolist(),
            'imported_added_vertex_ids': imported_ids.tolist(),
            'exact_POSITION_UV_and_oriented_source_topology': True,
            'maximum_decoded_normal_error': normal_error,
            'maximum_decoded_tangent_error': tangent_error,
            'new_rigid49_weights_and_zero_secondary_masks': True}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--baseline', type=Path, required=True)
    ap.add_argument('--candidate', type=Path, required=True)
    ap.add_argument('--report', type=Path, required=True)
    args = ap.parse_args()
    assert not args.report.exists()
    manifest_path = HERE / 'replacement-r7/replacement-manifest.json'
    assert sha(manifest_path) == MANIFEST_SHA
    manifest = json.loads(manifest_path.read_text())
    before = json.loads((args.baseline / 'semantics.json').read_text())
    after = json.loads((args.candidate / 'semantics.json').read_text())
    assert before['complete'] and after['complete']
    assert len(before['lods']) == len(after['lods']) == 3
    clean_before, clean_after = copy.deepcopy(before), copy.deepcopy(after)
    levels = []
    for li, level in enumerate(['near', 'mid', 'far']):
        row = manifest['levels'][level]
        source = GLB(row['source'])
        candidate = GLB(row['output'])
        assert sha(source.path) == row['source_sha256'] and sha(candidate.path) == row['sha256']
        old, new = before['lods'][li], after['lods'][li]
        assert old['raw_sha256'] == row['source_sha256'] and new['raw_sha256'] == row['sha256']
        for key in ['raw_sha256', 'imported_sha256']:
            del clean_before['lods'][li][key]
            del clean_after['lods'][li][key]
        names = [source.doc['nodes'][j]['name'] for j in source.doc['skins'][0]['joints']]
        rigs = [n for n in new['nodes'] if n['class'] == 'Skeleton3D']
        assert len(rigs) == 1 and names == [b['name'] for b in rigs[0]['bone_order']] and len(names) == 164
        nodes = [(i, n) for i, n in enumerate(old['nodes']) if n['path'].endswith('/RamaHero')]
        assert len(nodes) == 1
        ni, body = nodes[0]
        new_body = new['nodes'][ni]
        assert body['bind_names'] == new_body['bind_names']
        bind_map = [names.index(name) if name else index for name, index in body['bind_names']]
        assert sorted(bind_map) == list(range(164))
        # Validate the changed body's bounds against all authored vertex arrays;
        # retained unused rows are intentionally present in this review GLB.
        for glb, node, clean in [(source, body, clean_before), (candidate, new_body, clean_after)]:
            positions = np.concatenate([glb.array(p['attributes']['POSITION'])
                                        for p in glb.doc['meshes'][2]['primitives']])
            bounds = np.r_[positions.min(0), positions.max(0) - positions.min(0)]
            assert np.max(abs(np.array(node['aabb_values']) - bounds)) < 2e-6
            del clean['lods'][li]['nodes'][ni]['aabb']
            del clean['lods'][li]['nodes'][ni]['aabb_values']
        materials = []
        for pi, material_name in MATERIALS.items():
            surfaces = [(i, s) for i, s in enumerate(body['surfaces']) if s['material']['name'] == material_name]
            assert len(surfaces) == 1
            si, surface = surfaces[0]
            new_surface = new_body['surfaces'][si]
            old_arrays, old_records = read_arrays(args.baseline, surface)
            new_arrays, new_records = read_arrays(args.candidate, new_surface)
            changed = next(r for r in row['changed_primitives'] if r['primitive'] == pi)
            old_mask = rigid_mask(old_arrays, 50, bind_map) if pi in [2, 5, 6] else np.zeros(len(old_records), bool)
            new_mask = rigid_mask(new_arrays, 49, bind_map) if pi in [2, 3, 5] else np.zeros(len(new_records), bool)
            old_tri_mask = triangle_mask(old_mask, old_arrays[12])
            new_tri_mask = triangle_mask(new_mask, new_arrays[12])
            assert int(old_tri_mask.sum()) == changed['removed_triangles']
            assert int(new_tri_mask.sum()) == changed['added_triangles']
            dead_old_cap = rigid_mask(new_arrays, 50, bind_map) if pi in [2, 5, 6] else np.zeros(len(new_records), bool)
            assert not np.any(dead_old_cap[new_arrays[12]]), 'Superseded cap is still drawn'
            assert collections.Counter(r for i, r in enumerate(old_records) if not old_mask[i]) == collections.Counter(
                r for i, r in enumerate(new_records) if not new_mask[i] and not dead_old_cap[i]), 'Noncap vertex records changed'
            assert oriented_faces(old_records, old_arrays[12][~old_tri_mask]) == oriented_faces(
                new_records, new_arrays[12][~new_tri_mask]), 'Noncap imported attribute/topology changed'
            data = {'material': material_name, 'primitive': pi,
                    'source_removed_vertex_ids': changed['removed_source_vertices'],
                    'imported_removed_vertex_ids': np.flatnonzero(old_mask).tolist(),
                    'imported_removed_triangle_ids': np.flatnonzero(old_tri_mask).tolist(),
                    'imported_added_triangle_ids': np.flatnonzero(new_tri_mask).tolist(),
                    'removed_triangles': int(old_tri_mask.sum()), 'added_triangles': int(new_tri_mask.sum()),
                    'retained_oriented_triangle_and_complete_attribute_bytes_exact': True}
            if changed['added_vertices']:
                data.update(verify_new_geometry(candidate, pi, new_arrays, new_mask, new_tri_mask, changed))
            materials.append(data)
            clean_before['lods'][li]['nodes'][ni]['surfaces'][si]['arrays'] = []
            clean_after['lods'][li]['nodes'][ni]['surfaces'][si]['arrays'] = []
        levels.append({'level': level, 'source_sha256': row['source_sha256'],
                       'candidate_sha256': row['sha256'], 'materials': materials})
    # Everything not individually validated above must remain exactly equal:
    # node/rig/bind/animation/morph/material/texture state and all14 other surfaces.
    assert clean_before == clean_after, 'Unexpected imported semantic difference'
    report = {'schema': 1, 'passed': True, 'comparator_sha256': sha(__file__),
              'probe_sha256': sha(HERE / 'shoulder_import_semantics.gd'),
              'manifest_sha256': MANIFEST_SHA, 'levels': levels,
              'baseline_semantics_sha256': sha(args.baseline / 'semantics.json'),
              'candidate_semantics_sha256': sha(args.candidate / 'semantics.json'),
              'scope': 'Actual imported resource semantics, with exact oriented noncap triangle/attribute records and explicit new-frame quantization limits. No runtime/controller, continuous pose, framebuffer or visual-art acceptance.'}
    args.report.write_text(json.dumps(report, indent=2) + '\n')
    print('PASS: strict shoulder imported topology, attributes, rig and material semantics at all3 LODs')


if __name__ == '__main__':
    main()
