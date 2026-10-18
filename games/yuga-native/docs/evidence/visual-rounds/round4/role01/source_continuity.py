#!/usr/bin/env python3
"""CPU source continuity audit; archived motion summaries are not full pose replay."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import zipfile
import numpy as np
from scipy.spatial import cKDTree


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--r7', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    project = args.project.resolve()
    sys.path.insert(0, str(project / 'art/hero-rama-lod'))
    from glb_lod import GLB
    source = project / 'art/visual-rounds/face/principal-form-v1/candidate.glb'
    old, new = GLB(source), GLB(args.r7)
    spec = importlib.util.spec_from_file_location('p', project / 'tools/package-native.py')
    packaging = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(packaging)
    preserved = packaging.rama_groom_preservation(source, args.r7)
    names = [old.doc['nodes'][index]['name'] for index in old.doc['skins'][0]['joints']]
    def primitive(pair):
        return old.doc['meshes'][pair[0]]['primitives'][pair[1]]
    def arrays(pair):
        p = primitive(pair)
        return {key: old.array(value, normalized=True) for key, value in p['attributes'].items()}
    def dense(a):
        result = np.zeros((len(a['POSITION']), len(names)))
        np.add.at(result, (np.arange(len(result))[:, None], a['JOINTS_0'].astype(int)), a['WEIGHTS_0'])
        return result
    seams = []
    for first, second in (((1, 0), (2, 11)), ((2, 12), (2, 11))):
        a, b = arrays(first), arrays(second)
        distances, ids = cKDTree(b['POSITION']).query(a['POSITION'])
        indices = np.where(distances <= 1e-6)[0]
        target = ids[indices]
        p = primitive(first)
        morphs = {name: float(np.linalg.norm(old.array(morph['POSITION'])[indices], axis=1).max())
                  for name, morph in zip(old.doc['meshes'][first[0]].get('extras', {}).get('targetNames', []), p.get('targets', []))}
        seams.append({'source_surface': first, 'target_surface': second,
                      'source_material': old.doc['materials'][p['material']]['name'],
                      'target_material': old.doc['materials'][primitive(second)['material']]['name'],
                      'material_indices': [p['material'], primitive(second)['material']],
                      'coincident_source_vertices': len(indices),
                      'max_rest_gap_m': float(distances[indices].max()),
                      'max_joint_weight_l1_difference': float(np.abs(dense(a)[indices] - dense(b)[target]).sum(1).max()),
                      'max_normal_vector_difference': float(np.linalg.norm(a['NORMAL'][indices] - b['NORMAL'][target], axis=1).max()),
                      'face_morph_boundary_max_delta_m': morphs,
                      'example_pairs': [[int(x), int(y)] for x, y in zip(indices[:8], target[:8])]})
    body = arrays((2, 11))
    joints, weights = body['JOINTS_0'].astype(int), body['WEIGHTS_0']
    is_foot = np.array([name.startswith(('foot', 'toe')) for name in names])
    total = (weights * is_foot[joints]).sum(1)
    individual = ((weights > .5) & is_foot[joints]).any(1)
    dominated = total > .5
    missed = dominated & ~individual
    sampled = np.arange(len(weights)) % 96 == 0
    witnesses = []
    for index in np.where(missed & sampled)[0]:
        witnesses.append({'body_primitive_vertex': int(index), 'position_m': body['POSITION'][index].tolist(),
                          'combined_foot_toe_weight': float(total[index]),
                          'weights': {names[int(j)]: float(w) for j, w in zip(joints[index], weights[index]) if w > 0},
                          'old_individual_gt_half_tag': False})
    foot = {'body_vertex_count': len(weights), 'foot_toe_dominated_count': int(dominated.sum()),
            'missed_by_individual_influence_classifier': int(missed.sum()),
            'missed_rest_y_range_m': [float(body['POSITION'][missed, 1].min()), float(body['POSITION'][missed, 1].max())],
            'source_order_stride96_total': int(sampled.sum()),
            'source_order_stride96_foot_dominated': int((sampled & dominated).sum()),
            'source_order_stride96_missed': int((sampled & missed).sum()),
            'witnesses': witnesses,
            'scope': 'Exact original GLB body weights; source-order stride is diagnostic only because imported surface reordering has not been measured. This affects the foot-tagged contact subset, not all-skin minimum-height or maximum-step measurements.'}
    archive_dir = project / 'docs/evidence/visual-rounds/round4/role05'
    archive = archive_dir / 'motion-continuity-study.zip'
    manifest = json.loads((archive_dir / 'archive-manifest.json').read_text())
    assert sha(archive) == manifest['archive_sha256']
    historical_path = project / 'art/hero-rama-face/rama-hero-face.glb'
    historical = GLB(historical_path)
    hp = historical.doc['meshes'][2]['primitives'][11]
    ha = {key: historical.array(value, normalized=True) for key, value in hp['attributes'].items()}
    lower = ha['POSITION'][:, 1] < .3
    inheritance = {'historical_report_hero_sha256': sha(historical_path),
                   'later_role05_source_pin': json.loads((archive_dir / 'source-pins.json').read_text())['games/yuga-native/assets/heroes/rama-hero.glb'],
                   'historical_to_r2_body_positions_changed': int(np.any(ha['POSITION'] != body['POSITION'], axis=1).sum()),
                   'historical_to_r2_body_joint_indices_exact': bool(np.array_equal(ha['JOINTS_0'], body['JOINTS_0'])),
                   'historical_to_r2_body_weights_exact': bool(np.array_equal(ha['WEIGHTS_0'], body['WEIGHTS_0'])),
                   'lower_body_vertices_below_y_0_3': int(lower.sum()),
                   'lower_body_all_vertex_attributes_exact': all(np.array_equal(ha[k][lower], body[k][lower]) for k in ha),
                   'nodes_and_skin_json_exact': historical.doc['nodes'] == old.doc['nodes'] and historical.doc['skins'] == old.doc['skins'],
                   'inverse_bind_bytes_exact': np.array_equal(historical.array(historical.doc['skins'][0]['inverseBindMatrices']), old.array(old.doc['skins'][0]['inverseBindMatrices']))}
    motion = []
    with zipfile.ZipFile(archive) as z:
        for filename in ('continuity-r3a.json', 'continuity-r4.json'):
            raw = z.read(filename)
            assert hashlib.sha256(raw).hexdigest() == manifest['members'][filename]
            report = json.loads(raw)
            assert report['hero_sha256'] == sha(historical_path)
            for pair in report['trials']:
                if pair['baseline']['hz'] != 120 or pair['baseline']['name'] not in ('accelerated_reversal', 'start_stop'):
                    continue
                row = {'report': filename, 'sha256': manifest['members'][filename], 'scenario': pair['baseline']['name'], 'hz': 120}
                for branch in ('baseline', 'candidate'):
                    trial = pair[branch]
                    row[branch] = {key: trial[key] for key in ('maximum_joint_step_detail', 'maximum_skin_step_m', 'minimum_sampled_skin_y_m', 'sampled_skin_vertices', 'floor_contact_frames')}
                    row[branch]['full_joint_pose_matrices_present'] = False
                    row[branch]['worst_skin_vertex_identity_present'] = False
                    assert not any('positions' in item or 'bone_global_poses' in item for item in trial['rows'])
                motion.append(row)
    result = {'task': 'R4-01', 'status': 'source-continuity-contract-with-motion-limits',
              'pins': {'r2': sha(source), 'r7': sha(args.r7), 'archive': sha(archive), 'probe': sha(__file__),
                       'finish': sha(project / 'scripts/rama_surface_finish.gd'), 'motion': sha(project / 'scripts/rama_motion.gd')},
              'nonhair_preservation': preserved, 'seams': seams, 'foot_subset_counterexample': foot,
              'archived_motion_transition_witnesses': motion, 'archive_source_reconciliation': inheritance,
              'interpretation': ['Shared seam positions, normalized joint weights and zero blink boundary deltas imply identical skinned seam positions for the same joint transforms; this is a source C0 seam statement, not smooth motion acceptance.',
                                 'Raw motion reports use historical de61dc4c source, while the later source-pins ledger lists R2 140f8ff. Lower-body arrays and skin bindings are independently compared here; R7 does not constitute a new motion replay or repair.',
                                 'The archived R4-05 packet compacts out joint positions and does not retain full bone bases or worst-skinned-vertex identities. Exact independent per-frame skin replay requires those data or a new authorized lightweight runtime probe.',
                                 'Combined foot/toe weight may exceed half while every individual influence is at most half. Aggregate side groups are required for future foot-contact subset selection. Existing all-skin failures remain valid.'],
              'changes': 'Evidence only; no resculpt, weights, runtime, imports or render changes.'}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'seams': len(seams), 'missed_foot_vertices': int(missed.sum()), 'motion_witness_pairs': len(motion), 'output': str(args.output)}))


if __name__ == '__main__':
    main()
