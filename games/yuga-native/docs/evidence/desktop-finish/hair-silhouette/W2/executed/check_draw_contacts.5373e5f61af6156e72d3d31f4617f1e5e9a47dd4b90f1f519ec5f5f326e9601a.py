"""Offline complete-hair/hand/bow/arrow checks on captured native component poses.

The arrow uses conservative capsules enclosing the actual procedural shaft and
head. A negative capsule bound is a hold, not proof that the rendered mesh clips.
"""
import argparse
import json
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
from check_contacts import narrow, setup, part, posed
from build_candidate import sha, PINS


def transform(v, m):
    return (np.c_[v, np.ones(len(v))] @ m.T)[:, :3]


def capsule_bound(triangles, start, end, radius, band=.025):
    lo = np.maximum(triangles.min(1) - np.maximum(start, end), np.minimum(start, end) - triangles.max(1))
    selected = triangles[np.linalg.norm(np.maximum(lo, 0), axis=1) <= band + radius]
    if not len(selected):
        return {'guaranteed_lower_bound_m': band, 'near_triangles': 0}
    a, b = np.broadcast_to(start, (len(selected), 3)), np.broadcast_to(end, (len(selected), 3))
    d = np.minimum(narrow.point_tri(a, selected), narrow.point_tri(b, selected))
    for i in range(3):
        d = np.minimum(d, narrow.edge_edge(a, b, selected[:, i], selected[:, (i+1)%3]))
    d[narrow.edge_cross(a, b, selected)] = 0
    return {'guaranteed_lower_bound_m': float(min(band, d.min() - radius)), 'near_triangles': len(selected)}


def capsule_selfcheck():
    t = np.array([[[0.,0,0],[1,0,0],[0,1,0]]])
    gap = capsule_bound(t, np.array([.2,.2,.005]), np.array([.3,.2,.005]), .001)
    crossing = capsule_bound(t, np.array([.2,.2,-.01]), np.array([.2,.2,.01]), .001)
    assert abs(gap['guaranteed_lower_bound_m']-.004)<1e-10
    assert crossing['guaranteed_lower_bound_m']==-.001
    return {'parallel_capsule_gap_m':gap['guaranteed_lower_bound_m'], 'capsule_through_triangle_bound_m':crossing['guaranteed_lower_bound_m']}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--manifest', type=Path, required=True)
    ap.add_argument('--native', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    ap.add_argument('--level', choices=['near', 'mid', 'far'], default='near')
    ap.add_argument('--start', type=int, default=0)
    ap.add_argument('--count', type=int, default=348)
    a = ap.parse_args()
    assert not a.output.exists()
    m = json.loads(a.manifest.read_text())
    row, g, old, new, lower, allhair, inv, names = setup(m, a.level)
    tape = json.loads(a.native.read_text())
    assert tape['passed'] and len(tape['samples']) == 348 and tape['source_before'] == tape['source_after']
    assert tape['source_before']['res://assets/heroes/rama-hero.glb'] == PINS['near']
    # Imported skin vertices can be reordered: reconstruct them from actual bind
    # influences and prove correspondence to the original near source point set.
    near = old if a.level == 'near' else type(old)(m['levels']['near']['source'])
    near_inv = near.array(near.doc['skins'][0]['inverseBindMatrices']).reshape(-1, 4, 4).transpose(0, 2, 1).astype(float)
    assert names == [near.doc['nodes'][i]['name'] for i in near.doc['skins'][0]['joints']]
    rest = np.linalg.inv(near_inv)
    influences = tape['hand_geometry']['vertices']
    points, bones, weights, destinations, recovered, spread = [], [], [], [], [], []
    for index, slots in enumerate(influences):
        ps = []
        for slot in slots:
            points.append([*slot['point'], 1]); bones.append(slot['bone'])
            weights.append(slot['weight']); destinations.append(index)
            ps.append((rest[slot['bone']] @ [*slot['point'], 1])[:3])
        recovered.append(ps[0]); spread.append(float(np.linalg.norm(np.array(ps)-ps[0], axis=1).max()))
    skin = near.doc['meshes'][2]['primitives'][11]
    error, _ = cKDTree(near.array(skin['attributes']['POSITION'])).query(recovered)
    assert error.max() < 2e-6 and max(spread) < 2e-6
    points, bones, weights, destinations = map(np.array, [points, bones, weights, destinations])
    hands_tri = np.array(tape['hand_geometry']['triangles'])
    hair = part(g, 2, 0)
    bow = [part(old, 0, i) for i in range(len(old.doc['meshes'][0]['primitives']))]
    results = []
    output = {'scope': 'Offline source candidate on exact accepted-R2 348 fixed-step direct-API samples; no candidate native execution, continuous-gameplay or rendered clearance claim.',
        'manifest_sha256': sha(a.manifest), 'native_sha256': sha(a.native), 'checker_sha256': sha(__file__),
        'level': a.level, 'start': a.start, 'count': a.count, 'triangle_selfcheck': narrow.selfcheck(), 'capsule_selfcheck': capsule_selfcheck(),
        'hand_source_point_max_error_m': float(error.max()), 'hand_influence_rest_max_spread_m': max(spread),
        'arrow_capsules': [{'start_y_m': 0, 'end_y_m': .72, 'radius_m': .003}, {'start_y_m': .72, 'end_y_m': .785, 'radius_m': .012}], 'rows': results}
    for sample in tape['samples'][a.start:a.start+a.count]:
        poses, rig = np.array(sample['bone_globals']), np.array(sample['rig_global'])
        local_hair = posed(hair, poses @ inv)
        world_hair = transform(local_hair.reshape(-1, 3), rig).reshape(-1, 3, 3)
        weighted = np.einsum('nij,nj->ni', poses[bones], points)[:, :3] * weights[:, None]
        hands = np.zeros((len(influences), 3)); np.add.at(hands, destinations, weighted)
        world_hands = transform(hands, rig)[hands_tri]
        local_bow = np.concatenate([posed(piece, poses @ inv) for piece in bow])
        world_bow = transform(local_bow.reshape(-1, 3), rig).reshape(-1, 3, 3)
        comparisons = {'actual_imported_hands': narrow.compare(world_hair, world_hands, band=.025),
            'source_bow_and_string': narrow.compare(world_hair, world_bow, band=.025)}
        arrow = np.array(sample['arrow_global'])
        for label, start, end, radius in [('shaft', 0, .72, .003), ('tip', .72, .785, .012)]:
            ends = transform(np.array([[0, start, 0], [0, end, 0]]), arrow)
            comparisons['conservative_arrow_'+label] = capsule_bound(world_hair, *ends, radius)
        passed = all(v.get('crossings', 0) == 0 and v['guaranteed_lower_bound_m'] > .0002 for v in comparisons.values())
        results.append({'id': sample['id'], 'passed': passed, 'comparisons': comparisons})
        output.update(passed=all(r['passed'] for r in results), complete=False)
        a.output.write_text(json.dumps(output, indent=2)+'\n')
        print(sample['id'], passed, {k: round(v['guaranteed_lower_bound_m']*1000, 3) for k, v in comparisons.items()}, flush=True)
    output['complete'] = True
    a.output.write_text(json.dumps(output, indent=2)+'\n')
    raise SystemExit(0 if output['passed'] else 1)

if __name__ == '__main__':
    main()
