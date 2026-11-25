"""Compare imported Blender armature positions and evaluated mesh geometry."""
import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
import numpy as np

BASE, CANDIDATE, OUT = map(Path, sys.argv[sys.argv.index('--') + 1:])
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'four-hero-motion/tools'))
from blender_stills import load_model, select_pose

CLIPS = ('idle', 'run', 'mountain_pulse', 'tail_sweep')
PHASES = (0.0, .25, .5, .75, 1.0)
BONES = ('root', 'head', 'wrist.L', 'wrist.R', 'foot.L', 'foot.R', 'tail_01', 'tail_02', 'tail_03', 'tail_04')
SOCKETS = ('gada_grip', 'gada_head', 'tail_tip')


def samples(path):
    rig, meshes = load_model(path)
    result = {}
    for clip in CLIPS:
        for phase in PHASES:
            info = select_pose(rig, clip, phase)
            graph = bpy.context.evaluated_depsgraph_get()
            actor = rig.evaluated_get(graph)
            bones = {name: np.asarray(actor.matrix_world @ actor.pose.bones[name].head, dtype=float) for name in BONES}
            sockets = {name: np.asarray(bpy.context.scene.objects[name].evaluated_get(graph).matrix_world.translation, dtype=float) for name in SOCKETS}
            vertices = {}
            for source in meshes:
                obj = source.evaluated_get(graph)
                mesh = obj.to_mesh()
                try:
                    points = np.empty(len(mesh.vertices) * 3, dtype=np.float32)
                    mesh.vertices.foreach_get('co', points)
                    matrix = np.asarray(obj.matrix_world, dtype=float)
                    vertices[source.name] = points.reshape(-1, 3) @ matrix[:3, :3].T + matrix[:3, 3]
                finally:
                    obj.to_mesh_clear()
            result[f'{clip}/{phase:.2f}'] = {'pose': info, 'bones': bones, 'sockets': sockets, 'vertices': vertices}
    return result


def main():
    before, after = samples(BASE), samples(CANDIDATE)
    assert before.keys() == after.keys()
    reports = []
    for key in before:
        x, y = before[key], after[key]
        assert x['pose'] == y['pose'], f'Blender action phase mismatch: {key}'
        assert x['bones'].keys() == y['bones'].keys() and x['sockets'].keys() == y['sockets'].keys()
        differences = [float(np.linalg.norm(x['bones'][n] - y['bones'][n])) for n in BONES]
        differences += [float(np.linalg.norm(x['sockets'][n] - y['sockets'][n])) for n in SOCKETS]
        max_landmark = max(differences, default=0)
        assert max_landmark < 1e-5, f'Bone/socket moved at {key}: {max_landmark} m'
        assert x['vertices'].keys() == y['vertices'].keys(), f'Imported mesh names differ: {key}'
        changed, maximum = 0, 0.
        for name in x['vertices']:
            u, v = x['vertices'][name], y['vertices'][name]
            assert u.shape == v.shape and np.isfinite(v).all(), f'Evaluated mesh invalid: {key}/{name}'
            delta = np.linalg.norm(v-u, axis=1)
            changed += int((delta > 1e-7).sum())
            maximum = max(maximum, float(delta.max(initial=0)))
        reports.append({'clip_phase': key, 'max_bone_or_socket_delta_m': max_landmark,
                        'changed_evaluated_vertices': changed, 'max_evaluated_vertex_delta_m': maximum})
    result = {'blender_version': bpy.app.version_string, 'samples': reports, 'landmarks': list(BONES + SOCKETS),
              'limits': 'Sampled landmarks and evaluated vertex deltas only; no collision, eyelid contact, mesh occlusion, visual approval or runtime performance check.'}
    OUT.write_text(json.dumps(result, indent=2) + '\n')
    print('Blender imported and compared', len(reports), 'animation samples')


if __name__ == '__main__':
    main()
