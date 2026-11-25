"""Screen animated face-line depth along the posed head's local front axis.

Run with Blender --python-exit-code 1 -P this.py -- baseline.glb v1.glb v2.glb report.json
"""
import hashlib
import json
import sys
from pathlib import Path

import bpy
import numpy as np

BASE, V1, V2, OUT = map(Path, sys.argv[sys.argv.index('--') + 1:])
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'four-hero-motion/tools'))
from blender_stills import load_model, select_pose

CLIPS = ('idle', 'run', 'mountain_pulse', 'tail_sweep')
PHASES = (0.0, .25, .5, .75, 1.0)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def report_gap(points, skin, triangles):
    """Signed forward depth vs frontmost projected skin; not solid penetration."""
    tri = skin[triangles]
    tri = tri[(tri[:, :, 1].max(axis=1) > 1.74) & (tri[:, :, 1].min(axis=1) < 1.88) &
              (tri[:, :, 2].max(axis=1) > .1) & (np.abs(tri[:, :, 0]).min(axis=1) < .13)]
    a, b, c = tri[:, 0, :], tri[:, 1, :], tri[:, 2, :]
    den = (b[:, 1] - c[:, 1]) * (a[:, 0] - c[:, 0]) + (c[:, 0] - b[:, 0]) * (a[:, 1] - c[:, 1])
    valid = np.abs(den) > 1e-10
    gaps = np.full(len(points), np.nan)
    for i, (x, y, z) in enumerate(points):
        u = np.divide((b[:, 1] - c[:, 1]) * (x - c[:, 0]) + (c[:, 0] - b[:, 0]) * (y - c[:, 1]), den,
                      out=np.zeros_like(den), where=valid)
        v = np.divide((c[:, 1] - a[:, 1]) * (x - c[:, 0]) + (a[:, 0] - c[:, 0]) * (y - c[:, 1]), den,
                      out=np.zeros_like(den), where=valid)
        inside = valid & (u >= -1e-7) & (v >= -1e-7) & (u + v <= 1 + 1e-7)
        if inside.any():
            depth = u*a[:, 2] + v*b[:, 2] + (1-u-v)*c[:, 2]
            gaps[i] = z - depth[inside].max()
    return gaps


def xyz_to_rest_axes(coordinates, matrix):
    points = coordinates @ matrix[:3, :3].T + matrix[:3, 3]
    return points[:, (0, 2, 1)] * (1, 1, -1)


def stats(gaps, mask):
    result = gaps[mask]
    present = result[np.isfinite(result)]
    record = {'total': int(len(result)), 'ray_hits': int(len(present)), 'ray_misses': int(len(result) - len(present))}
    if len(present):
        record.update(min_mm=float(present.min()*1000), median_mm=float(np.median(present)*1000),
                      p95_mm=float(np.quantile(present, .95)*1000), max_mm=float(present.max()*1000),
                      behind_frontmost_skin=int((present < -1e-7).sum()))
    return record


def probe(path):
    rig, meshes = load_model(path)
    obj, = [o for o in meshes if any(slot.material and slot.material.name == 'Face · warm recessed lines' for slot in o.material_slots)]
    names = [slot.material.name if slot.material else None for slot in obj.material_slots]
    skin_slot, detail_slot = names.index('Vanara · painted copper anatomy'), names.index('Face · warm recessed lines')
    obj.data.calc_loop_triangles()
    skin_triangles = np.asarray([tuple(t.vertices) for t in obj.data.loop_triangles if t.material_index == skin_slot], dtype=int)
    detail_triangles = np.asarray([tuple(t.vertices) for t in obj.data.loop_triangles if t.material_index == detail_slot], dtype=int)
    detail_ids = np.unique(detail_triangles)
    assert len(detail_ids) == 346, f'Unexpected face-line vertices: {len(detail_ids)}'
    raw = np.empty(len(obj.data.vertices)*3, dtype=np.float32)
    obj.data.vertices.foreach_get('co', raw)
    rest = xyz_to_rest_axes(raw.reshape(-1, 3), np.asarray(obj.matrix_world))
    groups = {'mouth': rest[detail_ids, 1] < 1.82, 'nostrils': rest[detail_ids, 1] >= 1.82}
    samples = []
    for clip in CLIPS:
        for phase in PHASES:
            select_pose(rig, clip, phase)
            deps = bpy.context.evaluated_depsgraph_get()
            posed_rig = rig.evaluated_get(deps)
            bone = posed_rig.pose.bones['head']
            rigid = posed_rig.matrix_world @ bone.matrix @ bone.bone.matrix_local.inverted()
            posed_obj = obj.evaluated_get(deps)
            mesh = posed_obj.to_mesh()
            try:
                coordinates = np.empty(len(mesh.vertices)*3, dtype=np.float32)
                mesh.vertices.foreach_get('co', coordinates)
                to_rest = np.asarray(rigid.inverted() @ posed_obj.matrix_world)
                vertices = xyz_to_rest_axes(coordinates.reshape(-1, 3), to_rest)
            finally:
                posed_obj.to_mesh_clear()
            gaps = report_gap(vertices[detail_ids], vertices, skin_triangles)
            samples.append({'clip': clip, 'phase': phase, 'groups': {name: stats(gaps, mask) for name, mask in groups.items()}})
    return {'sha256': sha(path), 'samples': samples}


result = {'blender_version': bpy.app.version_string, 'script_sha256': sha(Path(__file__)),
          'method': 'For each evaluated pose, undo the rigid head transform, then project detail vertices along the anatomical front axis onto the front-most nearby skin triangles. Positive depth is in front of that surface; negative depth is behind it.',
          'limitations': ['A negative projected depth is not a watertight signed-distance or penetration measurement.',
                          'Nearby surface and anatomical forward-axis assumptions can miss a ray or select an occluding triangle.',
                          'Twenty body-action samples do not cover facial expressions, speech, all blends, continuous motion or actual engine rendering.'],
          'baseline': probe(BASE), 'v1': probe(V1), 'v2': probe(V2)}
OUT.write_text(json.dumps(result, indent=2, ensure_ascii=False)+'\n')
print('Animated clearance evaluated:', len(result['v2']['samples']), 'poses per model')
