"""Review-only smooth authored refit of the original diadem rail; no Blender/export/runtime write.

Uses the original tube UV as its centerline parameter. Existing tube offsets
are transported to a fitted centerline, retaining original topology and radius.
Only selected POSITION/NORMAL/TANGENT records in copied GLBs may change.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "art/hero-rama-lod"))
from glb_lod import GLB, DTYPES, WIDTHS
sys.path.insert(0, str(ROOT / "docs/evidence/visual-rounds/round3/role10"))
from geometry_probe import point_tri, compare, selfcheck

PINS = {
    "near": ("rama-hero.glb", "8b6cf0f4c5520696d1d843e5bdebb2454c1dbd4341e17171c5b6d20353384d5c"),
    "mid": ("rama-hero-mid.glb", "d95a061e2243477afc0227bf52564252fbcb20cb039d303ad10292ea5d85beed"),
    "far": ("rama-hero-far.glb", "ee2e35278ce49efdda6751850fddbb8f1b4de99ad019e6992c10e7702dc6317c"),
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def unit(v):
    return v / np.maximum(np.linalg.norm(v, axis=-1, keepdims=True), 1e-15)


def rail(g):
    primitive = g.doc["meshes"][2]["primitives"][2]
    assert g.doc["materials"][primitive["material"]]["name"] == "Worked warm gold"
    v = g.array(primitive["attributes"]["POSITION"])
    t = g.array(primitive["indices"]).reshape(-1, 3)
    high = t[np.all(v[t, 1] > 1.75, axis=1)]
    used = np.unique(high)
    _, welded = np.unique(np.round(v[used], 6), axis=0, return_inverse=True)
    lookup = np.full(len(v), -1); lookup[used] = welded
    wt = lookup[high]
    edges = np.concatenate([wt[:, [0, 1]], wt[:, [1, 2]], wt[:, [2, 0]]])
    count, labels = connected_components(coo_matrix(
        (np.ones(len(edges)), (edges[:, 0], edges[:, 1])),
        shape=(int(welded.max()) + 1,) * 2), directed=False)
    matches = []
    for label in range(count):
        ids = used[labels[welded] == label]
        lo, hi = v[ids].min(0), v[ids].max(0)
        if lo[1] > 1.784 and hi[1] < 1.800 and hi[0] - lo[0] > .20 and hi[2] - lo[2] > .27:
            matches.append(ids)
    assert len(matches) == 1, "rail component must be unique"
    ids = matches[0]
    touches = t[np.any(np.isin(t, ids), axis=1)]
    assert np.all(np.isin(touches, ids)), "no shared boundary with other goldwork"
    return primitive, ids, touches


def head_surfaces(g):
    result = []
    for pi in (0, 11):
        p = g.doc["meshes"][2]["primitives"][pi]
        v = g.array(p["attributes"]["POSITION"]).astype(float)
        t = g.array(p["indices"]).reshape(-1, 3)
        tri = v[t]
        # Every excluded triangle lies wholly below 1.70m. Its vertical
        # distance to the rail exceeds the measured nearest-distance bounds.
        result.append(tri[np.any(tri[:, :, 1] > 1.70, axis=1)])
    return np.concatenate(result)


def distances(points, triangles):
    centers = triangles.mean(1)
    radius = np.linalg.norm(triangles - centers[:, None], axis=2).max(1)
    tree = cKDTree(centers)
    out = []
    for p in points:
        _, near = tree.query(p, k=8)
        upper = point_tri(p[None], triangles[near]).min()
        candidates = tree.query_ball_point(p, float(upper + radius.max() + 1e-8))
        out.append(float(point_tri(p[None], triangles[candidates]).min()))
    return np.array(out)


def ray_distance(origin, direction, triangles):
    a = triangles[:, 0]
    e1, e2 = triangles[:, 1] - a, triangles[:, 2] - a
    h = np.cross(direction, e2); det = np.einsum("ij,ij->i", e1, h)
    inv = np.divide(1., det, out=np.zeros_like(det), where=abs(det) > 1e-12)
    s = origin - a; u = np.einsum("ij,ij->i", s, h) * inv
    q = np.cross(s, e1); vv = q @ direction * inv
    d = np.einsum("ij,ij->i", e2, q) * inv
    ok = (abs(det) > 1e-12) & (u >= -1e-8) & (vv >= -1e-8) & (u + vv <= 1 + 1e-8) & (d > .01) & (d < .25)
    assert ok.any(), "missing source-envelope ray"
    return float(d[ok].max())


def centerline(triangles):
    theta = np.linspace(0, 2 * np.pi, 81)
    old = np.c_[.105 * np.cos(theta), 1.792 + .003 * np.cos(6 * theta), .029 - .137 * np.sin(theta)]
    # A single authored planar ellipse forms the side/rear rail. Its radii
    # do not sample individual hair lobes; full-triangle checks admit/reject
    # the resulting envelope instead of sculpting a wire around each bump.
    arc = np.c_[.100 * np.cos(theta), np.full(81, 1.792), .044 - .130 * np.sin(theta)]
    origins = np.c_[np.zeros(81), old[:, 1], np.full(81, .045)]
    direction = unit(old - origins)
    # Keep the original protected crest sector. A broad quintic blend has
    # zero first/second endpoint derivatives, avoiding a temple dogleg.
    front = np.clip((direction[:, 2] + .05) / .90, 0, 1)
    front = front ** 3 * (front * (6 * front - 15) + 10)
    new = arc * (1 - front[:, None]) + old * front[:, None]
    new[front == 1] = old[front == 1]
    assert np.max(np.linalg.norm(new - old, axis=1)) < .035
    return old, new


def rotate_minimal(v, old_direction, new_direction):
    a, b = unit(old_direction), unit(new_direction)
    k = np.cross(a, b); cosine = float(a @ b)
    assert cosine > .5, "unexpected tube turn"
    return v + np.cross(k, v) + np.cross(k, np.cross(k, v)) / (1 + cosine)


def frames(positions, uv, triangles):
    normal = np.zeros_like(positions, dtype=float)
    tangent = np.zeros_like(normal); bitangent = np.zeros_like(normal)
    e1 = positions[triangles[:, 1]] - positions[triangles[:, 0]]
    e2 = positions[triangles[:, 2]] - positions[triangles[:, 0]]
    face = np.cross(e1, e2)
    du = uv[triangles[:, 1]] - uv[triangles[:, 0]]
    dv = uv[triangles[:, 2]] - uv[triangles[:, 0]]
    determinant = du[:, 0] * dv[:, 1] - du[:, 1] * dv[:, 0]
    inv = np.divide(1., determinant, out=np.zeros_like(determinant), where=abs(determinant) > 1e-12)
    ft = (e1 * dv[:, 1, None] - e2 * du[:, 1, None]) * inv[:, None]
    fb = (e2 * du[:, 0, None] - e1 * dv[:, 0, None]) * inv[:, None]
    for k in range(3):
        np.add.at(normal, triangles[:, k], face)
        np.add.at(tangent, triangles[:, k], ft)
        np.add.at(bitangent, triangles[:, k], fb)
    _, weld = np.unique(np.round(positions, 7), axis=0, return_inverse=True)
    joined = np.zeros((int(weld.max()) + 1, 3)); np.add.at(joined, weld, normal)
    normal = unit(joined[weld])
    tangent -= normal * np.sum(normal * tangent, axis=1)[:, None]
    bad = np.linalg.norm(tangent, axis=1) < 1e-10
    for i in np.flatnonzero(bad):
        axis = np.eye(3)[np.argmin(abs(normal[i]))]
        tangent[i] = np.cross(axis, normal[i])
    tangent = unit(tangent)
    sign = np.where(np.sum(np.cross(normal, tangent) * bitangent, axis=1) < 0, -1., 1.)
    assert np.isfinite(normal).all() and np.isfinite(tangent).all()
    assert np.max(abs(np.linalg.norm(normal, axis=1) - 1)) < 1e-6
    assert np.max(abs(np.sum(normal * tangent, axis=1))) < 1e-6
    return normal.astype('<f4'), np.c_[tangent, sign].astype('<f4'), float(np.linalg.norm(face, axis=1).min() / 2)


def patch(g, primitive, ids, values, output):
    binary = bytearray(g.binary)
    allowed = np.zeros(len(binary), dtype=bool)
    for name, data in values.items():
        acc = g.doc['accessors'][primitive['attributes'][name]]
        assert 'sparse' not in acc
        view = g.doc['bufferViews'][acc['bufferView']]
        dtype = DTYPES[acc['componentType']]; width = WIDTHS[acc['type']]
        assert dtype == np.dtype('<f4') and data.shape == (len(ids), width)
        size = dtype.itemsize * width
        stride = view.get('byteStride', size)
        base = view.get('byteOffset', 0) + acc.get('byteOffset', 0)
        for i, vertex in enumerate(ids):
            start = base + int(vertex) * stride
            binary[start:start + size] = data[i].astype(dtype).tobytes()
            allowed[start:start + size] = True
        for field, op in [('min', np.min), ('max', np.max)]:
            if field in acc:
                assert np.all(op(data, axis=0) >= np.array(acc[field]) - 1e-7) if field == 'min' else np.all(op(data, axis=0) <= np.array(acc[field]) + 1e-7)
    before = np.frombuffer(g.binary, dtype='u1'); after = np.frombuffer(binary, dtype='u1')
    different = before != after
    assert not np.any(different & ~allowed)
    prefix_size = len(g.raw) - len(g.binary)
    raw = g.raw[:prefix_size] + binary
    output.write_bytes(raw)
    reread = GLB(output)
    assert reread.doc == g.doc and np.array_equal(before[~allowed], after[~allowed])
    for name, ai in primitive['attributes'].items():
        old = g.array(ai); new = reread.array(ai)
        if name in values:
            other = np.ones(len(old), bool); other[ids] = False
            assert np.array_equal(old[other], new[other])
        else:
            assert np.array_equal(old, new)
    return {'sha256': sha(raw), 'bytes': len(raw), 'changed_binary_bytes': int(different.sum()),
            'allowed_record_bytes': int(allowed.sum()), 'outside_selected_records_exact': True,
            'json_exact': True, 'file_size_exact': True}


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(); args.output.mkdir(parents=True, exist_ok=False)
    assert sha((Path(__file__).parent.parent / 's4-diadem-fit/build_candidate.py').read_bytes()) == 'c785e858881f85aa3ed09f0b0dec0323a27ba1d2b209dd1224b681b0b22b8c58', 'sealed first builder changed'
    source = GLB(ROOT / 'assets/heroes/rama-hero.glb')
    assert sha(source.raw) == PINS['near'][1]
    surfaces = head_surfaces(source); old_centers, new_centers = centerline(surfaces)
    report = {'schema': 1, 'scope': 'Review-only original diadem rail. Source-rest measurements; native pose/render pending.',
              'generator_sha256': sha(Path(__file__).read_bytes()), 'derived_builder_sha256': sha((Path(__file__).parent.parent / 's4-diadem-fit/build_candidate.py').read_bytes()), 'design': {'side_rear_arc': 'planar ellipse with broad quintic protected-front blend; no pointwise hair sampling', 'ellipse_x_radius_m': .100, 'ellipse_z_radius_m': .130, 'ellipse_z_center_m': .044, 'side_rear_y_m': 1.792, 'original_tube_radius_m': .0035}, 'narrow_phase_control': selfcheck(),
              'centerline': {'original': old_centers.tolist(), 'candidate': new_centers.tolist()}, 'levels': {}}
    for level, (name, expected) in PINS.items():
        path = ROOT / 'assets/heroes' / name; g = GLB(path); assert sha(g.raw) == expected
        p, ids, tri = rail(g)
        if level == 'near': assert np.array_equal(ids, np.arange(24830, 25559))
        attrs = {k: g.array(ai, k == 'COLOR_0') for k, ai in p['attributes'].items()}
        assert np.all(attrs['JOINTS_0'][ids, 0] == 104)
        assert np.all(attrs['WEIGHTS_0'][ids] == [1, 0, 0, 0])
        assert np.all(attrs['COLOR_0'][ids, 3] == 0)
        ring = np.rint((1 - attrs['TEXCOORD_0'][ids, 1]) * 80).astype(int)
        assert np.all((ring >= 0) & (ring <= 80))
        original = attrs['POSITION'][ids].astype(float)
        candidate = original.copy()
        for index, r in enumerate(ring):
            prev, nxt = max(0, r - 1), min(80, r + 1)
            delta = original[index] - old_centers[r]
            assert abs(np.linalg.norm(delta) - .0035) < 3e-6
            candidate[index] = new_centers[r] + rotate_minimal(delta, old_centers[nxt] - old_centers[prev], new_centers[nxt] - new_centers[prev])
        lookup = np.full(len(attrs['POSITION']), -1); lookup[ids] = np.arange(len(ids))
        localtri = lookup[tri]
        n, tangent, min_area = frames(candidate, attrs['TEXCOORD_0'][ids], localtri)
        assert min_area > 1e-10
        target = args.output / name
        write = patch(g, p, ids, {'POSITION': candidate.astype('<f4'), 'NORMAL': n, 'TANGENT': tangent}, target)
        colliders = head_surfaces(g)
        before, after = distances(original, colliders), distances(candidate, colliders)
        full = compare(candidate[localtri], colliders, band=.040)
        assert full['crossings'] == 0 and full['guaranteed_lower_bound_m'] > .002, json.dumps({'rejected_level': level, 'full_triangle_clearance': full})
        displacement = np.linalg.norm(candidate - original, axis=1)
        report['levels'][level] = {'source': str(path.relative_to(ROOT)), 'source_sha256': expected,
            'output': str(target), **write, 'selected_vertex_ids': ids.tolist(),
            'selected_triangles': len(tri), 'selected_vertices': len(ids),
            'rig_joint': 'head', 'joint_index': 104, 'weight': 1, 'secondary_alpha': 0,
            'before_vertex_surface_distance_quantiles_m': np.quantile(before, [0,.5,.95,1]).tolist(),
            'after_vertex_surface_distance_quantiles_m': np.quantile(after, [0,.5,.95,1]).tolist(),
            'candidate_full_triangle_clearance': full, 'minimum_triangle_area_m2': min_area,
            'maximum_vertex_displacement_m': float(displacement.max()),
            'source_bounds': [original.min(0).tolist(), original.max(0).tolist()],
            'candidate_bounds': [candidate.min(0).tolist(), candidate.max(0).tolist()]}
        print(level, 'triangles', len(tri), 'max_move_mm', float(displacement.max()) * 1000,
              'full_clearance_mm', full['guaranteed_lower_bound_m'] * 1000, flush=True)
    (args.output / 'source-manifest.json').write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    main()
