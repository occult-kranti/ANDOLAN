"""Renderer-owner Blender slot: inspect source, import candidate, save editable.

Run with Blender 4.3.2 -b -t 1 --python this.py -- --candidate ... --output ...
This deliberately does not export a new GLB or change reviewed runtime bytes.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import bpy
from mathutils import Vector


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def snapshot():
    rigs = [o for o in bpy.data.objects if o.type == 'ARMATURE']
    meshes = [o for o in bpy.data.objects if o.type == 'MESH' and o.name != 'Icosphere']
    return {"armatures": len(rigs), "bones": [len(r.data.bones) for r in rigs], "mesh_objects": [{"name": o.name, "vertices": len(o.data.vertices), "polygons": len(o.data.polygons), "morphs": [k.name for k in o.data.shape_keys.key_blocks] if o.data.shape_keys else []} for o in meshes], "actions": [a.name for a in bpy.data.actions], "images": [{"name": i.name, "packed": bool(i.packed_file), "size": list(i.size)} for i in bpy.data.images if i.type == 'IMAGE']}


p = argparse.ArgumentParser()
p.add_argument('--candidate', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
p.add_argument('--native-source', type=Path, required=True)
p.add_argument('--reconstruction-source', type=Path, required=True)
p.add_argument('--partition', type=Path, default=Path(__file__).resolve().parents[2] / 'hero-rama-face/candidate.json')
a = p.parse_args(sys.argv[sys.argv.index('--') + 1:])
assert not a.output.exists()
report = {"generator_sha256": sha(__file__), "candidate_sha256": sha(a.candidate), "blender": bpy.app.version_string, "source_inspections": []}
for source in [a.reconstruction_source, a.native_source]:
    bpy.ops.wm.open_mainfile(filepath=str(source.resolve()))
    report['source_inspections'].append({"path": str(source.resolve()), "sha256": sha(source), "data": snapshot()})
    if source == a.native_source:
        face = bpy.data.objects['RamaFace']
        partition = json.loads(a.partition.read_text())
        boundary = [Vector(row['position']) for row in partition['boundary']]
        seam = {v.index for v in face.data.vertices if any((v.co - point).length < 1e-7 for point in boundary)}
        held = set(seam)
        for polygon in face.data.polygons:
            if set(polygon.vertices) & seam:
                held.update(polygon.vertices)
        assert len(seam) == 146 and len(held) == 288
        ring = {"source_sha256": sha(source), "partition_sha256": sha(a.partition), "boundary_vertices": len(seam), "held_vertices": len(held), "positions_gltf_m": [[face.data.vertices[i].co.x, face.data.vertices[i].co.z, -face.data.vertices[i].co.y] for i in sorted(held)], "scope": "Original native quad mesh: union every vertex in a polygon incident on the146shared attachment vertices."}
        ring_path = a.output.with_suffix('.held-ring.json')
        ring_path.parent.mkdir(parents=True, exist_ok=True)
        ring_path.write_text(json.dumps(ring, indent=2) + '\n')
        report['original_held_ring_sha256'] = sha(ring_path)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(a.candidate.resolve()))
report['candidate_import'] = snapshot()
assert report['candidate_import']['armatures'] == 1
assert report['candidate_import']['bones'] == [164]
assert len(report['candidate_import']['actions']) == 9
face = next(o for o in bpy.data.objects if o.name == 'RamaFace')
assert [k.name for k in face.data.shape_keys.key_blocks] == ['Basis', 'rama_blink_left', 'rama_blink_right', 'rama_blink_half_left', 'rama_blink_half_right']
for image in bpy.data.images:
    if image.type == 'IMAGE':
        assert image.packed_file and image.size[0] > 0
for rig in [o for o in bpy.data.objects if o.type == 'ARMATURE']:
    rig.animation_data.action = None
    rig.data.pose_position = 'REST'
bpy.ops.wm.save_as_mainfile(filepath=str(a.output.resolve()), compress=True)
bpy.ops.wm.open_mainfile(filepath=str(a.output.resolve()))
report['reopened'] = snapshot()
assert report['reopened'] == report['candidate_import']
report['editable_sha256'] = sha(a.output)
report['scope'] = 'Editable imported candidate preserving original GLB runtime separately. No original modeling-history recovery or roundtrip export equivalence claim.'
a.output.with_suffix('.inspection.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({"editable_sha256": report['editable_sha256'], "generator_sha256": report['generator_sha256'], "candidate_sha256": report['candidate_sha256'], "bones": report['reopened']['bones'], "actions": len(report['reopened']['actions']), "packed_images": len(report['reopened']['images']), "held_ring_sha256": report['original_held_ring_sha256']}))
