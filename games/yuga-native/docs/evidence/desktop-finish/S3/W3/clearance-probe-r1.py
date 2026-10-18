#!/usr/bin/env python3
"""Replay exported imported-skin influences; never load/import the native scene."""
import argparse
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
NARROW = ROOT/'docs/evidence/visual-rounds/round3/role10/geometry_probe.py'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def transform(points, matrix):
    return (np.c_[points, np.ones(len(points))] @ matrix.T)[:, :3]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('native', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    native_bytes = args.native.read_bytes()
    if args.native.suffix == '.gz':
        native_bytes = gzip.decompress(native_bytes)
    native = json.loads(native_bytes)
    mesh_path = Path(__file__).with_name('candidate-mesh.json')
    geometry = json.loads(mesh_path.read_text())
    spec = importlib.util.spec_from_file_location('r3_triangle_narrow_phase', NARROW)
    narrow = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(narrow)
    assert native['passed'] and len(native['samples']) == 27
    assert native['source_before'] == native['source_after']
    assert native['source_before']['res://art/hero-finish/s3-arrow-fletching/candidate-mesh.json'] == sha(mesh_path)
    assert native['hand_geometry']['max_rest_reconstruction_error_m'] < .00002
    primitives = narrow.selfcheck()
    influences = native['hand_geometry']['vertices']
    count = len(influences)
    hand_triangles = np.array(native['hand_geometry']['triangles'], dtype=int)
    points, bones, weights, destination = [], [], [], []
    for index, slots in enumerate(influences):
        for slot in slots:
            points.append([*slot['point'], 1.0])
            bones.append(slot['bone'])
            weights.append(slot['weight'])
            destination.append(index)
    points, bones, weights, destination = map(np.array, (points, bones, weights, destination))
    fletching = np.array(geometry['vertices'])
    rows = []
    for sample in native['samples']:
        globals_ = np.array(sample['bone_globals'])
        weighted = np.einsum('nij,nj->ni', globals_[bones], points)[:, :3] * weights[:, None]
        local = np.zeros((count, 3))
        np.add.at(local, destination, weighted)
        posed_hand = transform(local, np.array(sample['rig_global']))[hand_triangles]
        posed_fletching = transform(fletching, np.array(sample['arrow_global'])).reshape(-1, 3, 3)
        assert np.isfinite(posed_hand).all() and np.isfinite(posed_fletching).all()
        assert sample['arrow_global'] == sample['helper_global'] and sample['visible']
        result = narrow.compare(posed_fletching, posed_hand, band=.04)
        # Repeat the closest triangle pair with no broad phase. A separate
        # actual-hand counterexample crosses a real face through its centroid.
        witness = result.get('witness_triangles')
        if witness:
            a, b = witness
            distance, crossing = narrow.narrow(posed_fletching[a:a+1], posed_hand[b:b+1])
            assert abs(float(distance[0])-result['minimum_distance_m']) < 1e-10
        face = posed_hand[np.argmax(np.linalg.norm(np.cross(posed_hand[:, 1]-posed_hand[:, 0], posed_hand[:, 2]-posed_hand[:, 0]), axis=1))]
        center = face.mean(0)
        normal = np.cross(face[1]-face[0], face[2]-face[0])
        normal /= np.linalg.norm(normal)
        adversary = np.array([[center-normal*.01, center+normal*.01, face[0]]])
        _, hit = narrow.narrow(adversary, face[None])
        assert bool(hit[0]), 'actual-hand edge-through-face negative control missed'
        pixel_extent = np.array(sample['projection']['bounds_max']) - sample['projection']['bounds_min']
        rows.append({'id': sample['id'], **result,
                     'projected_bounds_size_px': pixel_extent.tolist(),
                     'actual_hand_crossing_adversary_detected': True})
    clear = all(row['crossings'] == 0 and row['guaranteed_lower_bound_m'] > .002 for row in rows)
    result = {
        'passed': clear,
        'sources': {str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path): sha(path)
                    for path in [Path(__file__).resolve(), mesh_path, NARROW, NARROW.parent.parent/'role09/glb_read.py', args.native.resolve()]},
        'native_runtime_sources': native['source_before'],
        'native_report_uncompressed_sha256': hashlib.sha256(native_bytes).hexdigest(),
        'checks': {
            'native_fixture_passed': native['passed'],
            'imported_skin_influences_preserved_without_normalizing': True,
            'finite_posed_triangles_and_exact_inherited_arrow_frame': True,
            'all_declared_samples_clear_by_more_than_2mm': clear,
            'actual_hand_crossing_adversaries_detected': all(row['actual_hand_crossing_adversary_detected'] for row in rows),
            'narrow_phase_primitive_selfcheck': primitives,
        },
        'hand_vertices': count, 'hand_triangles': len(hand_triangles),
        'fletching_triangles': len(fletching)//3,
        'minimum_lower_bound_m': min(row['guaranteed_lower_bound_m'] for row in rows),
        'projection_extent_min_px': np.min([row['projected_bounds_size_px'] for row in rows], axis=0).tolist(),
        'projection_extent_max_px': np.max([row['projected_bounds_size_px'] for row in rows], axis=0).tolist(),
        'samples': rows,
        'scope': '27 declared direct RamaMotion draw samples, 3 abilities x3 aim pitches x3 windup fractions. Actual imported hand triangles selected by aggregate wrist/finger influence >0.2 on any triangle vertex; all selected triangle vertices retained. Full edge-face/edge-edge/point-triangle separation, 40mm conservative broad-phase band. No all-body, motion-continuity, projectile, rasterized visibility, shimmer or art acceptance claim. Camera projection is a fixed default-distance fixture only.',
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
    print(json.dumps({key: result[key] for key in ['passed', 'minimum_lower_bound_m', 'hand_vertices', 'hand_triangles', 'projection_extent_min_px', 'projection_extent_max_px']}))
    raise SystemExit(0 if clear else 1)


if __name__ == '__main__':
    main()
