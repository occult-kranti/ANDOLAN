# SPDX-License-Identifier: GPL-3.0-or-later
"""One source-derived card fit over the retained R1 opaque nape sculpture.

Blender's standard posterior PROJECT Shrinkwrap acts only against the exact
audited nine-component source region. It cannot touch body/crown/rig. A failed
orientation/fold guard retains its diagnostic but refuses a runtime export.
"""
import argparse
import json
import struct
import sys
import time
from pathlib import Path

import bpy
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_candidate import sha, digest

UNDERLAYER_SHA = '85c16967bdec0eeb6cf4c5b331fe07d236df114ebf3730937d97300e4dda0777'


def read_accessor(doc, binary, index):
    a = doc['accessors'][index]
    v = doc['bufferViews'][a['bufferView']]
    size = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[a['type']]
    dtype = {5123: np.uint16, 5125: np.uint32, 5126: np.float32}[a['componentType']]
    assert not v.get('byteStride') or v['byteStride'] == size * np.dtype(dtype).itemsize
    return np.frombuffer(binary, dtype=dtype, count=a['count'] * size,
                         offset=v.get('byteOffset', 0) + a.get('byteOffset', 0)).reshape(-1, size)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--receipt', type=Path, required=True)
    p.add_argument('--underlayer', type=Path, required=True)
    p.add_argument('--mask', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args(sys.argv[sys.argv.index('--') + 1:])
    receipt = json.loads(a.receipt.read_text())
    master = next(item for item in receipt['outputs'] if item['path'].endswith('.blend'))
    source = a.receipt.parent / master['path']
    assert sha(source) == master['sha256'] and sha(a.underlayer) == UNDERLAYER_SHA
    a.output.mkdir(parents=True, exist_ok=False)
    start = time.monotonic()
    mask = json.loads(a.mask.read_text())
    raw = a.underlayer.read_bytes()
    length = struct.unpack_from('<I', raw, 12)[0]
    doc = json.loads(raw[20:20 + length])
    binary = raw[28 + length:]
    primitive = doc['meshes'][mask['mesh_index']]['primitives'][mask['primitive_index']]
    positions = read_accessor(doc, binary, primitive['attributes']['POSITION'])
    triangles = read_accessor(doc, binary, primitive['indices']).reshape(-1, 3)
    selected = mask['selected_accessor_vertex_ids']
    selected_set = set(selected)
    faces = triangles[mask['removed_triangle_ids']]
    assert len(selected) == 3996 and len(faces) == 7344
    assert all(int(v) in selected_set for face in faces for v in face)
    lookup = {v: i for i, v in enumerate(selected)}
    xyz = [(float(positions[i][0]), -float(positions[i][2]), float(positions[i][1])) for i in selected]
    bpy.ops.wm.open_mainfile(filepath=str(source))
    scene = bpy.context.scene
    cards = bpy.data.objects['YUGA MPFB nape cards near CANDIDATE']
    rig = next(o for o in scene.objects if o.type == 'ARMATURE')
    rig.data.pose_position = 'REST'
    before = np.array([tuple(v.co) for v in cards.data.vertices], dtype=np.float64)
    uv_before = digest([tuple(v.uv) for v in cards.data.uv_layers.active.data])
    weights_before = digest([[(g.group, g.weight) for g in v.groups] for v in cards.data.vertices])
    mesh = bpy.data.meshes.new('Exact R1 nine-nape-components shrinkwrap target')
    mesh.from_pydata(xyz, [], [tuple(lookup[int(v)] for v in face) for face in faces])
    mesh.update()
    target = bpy.data.objects.new('HIDDEN unchanged R1 opaque nape projection target', mesh)
    scene.collection.objects.link(target)
    target.hide_render = True
    target['source_sha256'] = UNDERLAYER_SHA
    target['mask_sha256'] = sha(a.mask)
    mod = cards.modifiers.new('ONE standard Blender posterior projection on exact R1 nape', 'SHRINKWRAP')
    mod.target = target
    mod.wrap_method = 'PROJECT'
    mod.wrap_mode = 'ABOVE_SURFACE'
    mod.use_project_x = False
    mod.use_project_y = True
    mod.use_project_z = False
    mod.use_positive_direction = True
    mod.use_negative_direction = False
    mod.cull_face = 'FRONT'
    mod.offset = .003
    mod.project_limit = .20
    bpy.ops.object.select_all(action='DESELECT')
    cards.select_set(True)
    bpy.context.view_layer.objects.active = cards
    while list(cards.modifiers).index(mod) > 0:
        bpy.ops.object.modifier_move_up(modifier=mod.name)
    bpy.ops.object.modifier_apply(modifier=mod.name)
    after = np.array([tuple(v.co) for v in cards.data.vertices], dtype=np.float64)
    delta = np.linalg.norm(after - before, axis=1)
    cards.data.calc_loop_triangles()
    tris = np.array([tuple(t.vertices) for t in cards.data.loop_triangles], dtype=int)
    old = before[tris]
    new = after[tris]
    old_cross = np.cross(old[:, 1] - old[:, 0], old[:, 2] - old[:, 0])
    new_cross = np.cross(new[:, 1] - new[:, 0], new[:, 2] - new[:, 0])
    old_area = np.linalg.norm(old_cross, axis=1)
    new_area = np.linalg.norm(new_cross, axis=1)
    inverted = np.where((old_cross * new_cross).sum(axis=1) < -1e-12)[0]
    collapsed = np.where(new_area < np.maximum(old_area * .02, 1e-12))[0]
    ratios = []
    for a0, a1 in ((0, 1), (1, 2), (2, 0)):
        ratios.extend(np.linalg.norm(new[:, a1] - new[:, a0], axis=1) / np.maximum(np.linalg.norm(old[:, a1] - old[:, a0], axis=1), 1e-9))
    checks = {
        'finite_geometry': bool(np.isfinite(after).all()),
        'some_actual_fitted_vertices': bool((delta > 1e-7).any()),
        'all_displacement_below_ray_limit_plus_offset': float(delta.max()) <= .204,
        'no_inverted_triangles': len(inverted) == 0,
        'no_collapsed_triangles': len(collapsed) == 0,
        'edge_stretch_below4': bool(max(ratios) < 4),
        'uv_exact': uv_before == digest([tuple(v.uv) for v in cards.data.uv_layers.active.data]),
        'skin_weights_exact': weights_before == digest([[(g.group, g.weight) for g in v.groups] for v in cards.data.vertices]),
        'source_files_exact': sha(source) == master['sha256'] and sha(a.underlayer) == UNDERLAYER_SHA,
    }
    result = {
        'schema_version': 1, 'scope': 'One source-derived posterior projection of existing MPFB cards onto exact R1 opaque nape',
        'underlayer_sha256': UNDERLAYER_SHA, 'source_card_master_sha256': sha(source),
        'source_receipt_sha256': sha(a.receipt), 'mask_sha256': sha(a.mask), 'script_sha256': sha(__file__),
        'settings': {'mode': 'PROJECT', 'axis': 'Blender+Y', 'cull_face': 'FRONT', 'offset_m': .003, 'ray_limit_m': .20},
        'target_vertices': len(selected), 'target_triangles': len(faces), 'card_vertices': len(before),
        'moved_vertices': int((delta > 1e-7).sum()), 'unmoved_vertices': int((delta <= 1e-7).sum()),
        'max_displacement_m': float(delta.max()), 'maximum_edge_ratio': float(max(ratios)),
        'inverted_triangle_ids': inverted.tolist(), 'collapsed_triangle_ids': collapsed.tolist(),
        'checks': checks, 'eligible_for_native_review': all(checks.values()), 'canonical_promoted': False,
        'elapsed_seconds': time.monotonic() - start,
    }
    # Keep a compact numeric witness for every original/projection position.
    np.savez_compressed(a.output / 'projection-witness.npz', before=before, after=after, triangles=tris, delta=delta)
    if all(checks.values()):
        rig.select_set(True)
        glb = a.output / 'mpfb-nape-layered-cards.glb'
        bpy.ops.export_scene.gltf(filepath=str(glb), export_format='GLB', use_selection=True,
            export_animations=False, export_apply=False, export_extras=True,
            export_skins=True, export_def_bones=False, export_yup=True)
        master_path = a.output / 'rama-mpfb-layered-candidate.blend'
        bpy.ops.wm.save_as_mainfile(filepath=str(master_path))
        result['outputs'] = [{'path': f.name, 'bytes': f.stat().st_size, 'sha256': sha(f)} for f in (glb, master_path)]
    else:
        result['runtime_export'] = 'REFUSED by geometry guards; prior candidates preserved'
    (a.output / 'receipt.json').write_text(json.dumps(result, indent=2) + '\n')
    print('MPFB_UNDERLAYER=' + json.dumps(result, separators=(',', ':')))
    if not all(checks.values()):
        raise RuntimeError('Projected card fit rejected by geometry guards')


if __name__ == '__main__':
    main()
