#!/usr/bin/env python3
"""Original Rama solar shoulder guard; Blender4.3 authoring, no foreign assets.

The compact guard is authored in upperarm01.R bone-local metres: +Y follows
that upper arm, +X faces the actor's front, -Z is the outward shoulder surface.
A runtime BoneAttachment carries it; this asset contains no skin/rig or collider.
Run in the lead's serialized authoring lane with eight threads.
"""
from pathlib import Path
import hashlib
import json
import math

import bpy

ROOT = Path(__file__).resolve().parents[2]
PROJECT = ROOT / 'games/yuga-native'
ART = PROJECT / 'art/hero-completion/gear'
ASSET = PROJECT / 'assets/heroes/rama-gear.glb'
if ASSET.exists():
    raise RuntimeError('Preserve the previous gear candidate before creating another')
ART.mkdir(parents=True, exist_ok=True)

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)


def material(name, color, metallic, roughness):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*color, 1)
    bsdf.inputs['Metallic'].default_value = metallic
    bsdf.inputs['Roughness'].default_value = roughness
    mat.diffuse_color = (*color, 1)
    return mat


materials = [
    material('Rama / solar indigo enamel', (.025, .065, .17), .15, .38),
    material('Rama / solar worked gold', (.56, .28, .065), .85, .32),
]
vertices, faces, slots, smooth = [], [], [], []


def face(points, slot, rounded=False):
    start = len(vertices)
    # Proper rotation from Godot bone-local Y-up to Blender Z-up.
    vertices.extend((x, -z, y) for x, y, z in points)
    faces.append(tuple(range(start, start+len(points))))
    slots.append(slot)
    smooth.append(rounded)


def perimeter(amount, index):
    angle = index * math.tau / 32
    # A quiet swept rear edge distinguishes the bow-arm silhouette.
    x = .112 * amount * math.cos(angle)
    y = .025 + .122 * amount * math.sin(angle)
    z = -.09 - .05 * (1-amount*amount)
    return (x, y, z)


# Curved indigo shell; separated rings give real edge/normal hierarchy.
rings = [0, .25, .5, .75, .9, 1]
for ring in range(len(rings)-1):
    low, high = rings[ring: ring+2]
    for index in range(32):
        nxt = (index+1) % 32
        if low == 0:
            face([perimeter(0, 0), perimeter(high, nxt), perimeter(high, index)], 0, True)
        else:
            face([perimeter(low, index), perimeter(low, nxt), perimeter(high, nxt), perimeter(high, index)], 1 if low >= .9 else 0, True)
# Eight-millimetre rolled outer edge and enclosed back; no zero-thickness cards.
for index in range(32):
    nxt = (index+1) % 32
    a, b = perimeter(1, index), perimeter(1, nxt)
    a_back = (a[0], a[1], a[2]+.008)
    b_back = (b[0], b[1], b[2]+.008)
    face([a, b, b_back, a_back], 1)
    face([(0, .025, -.075), a_back, b_back], 0)


def relief_polygon(points, front, depth, slot=1):
    top = [(x, y, front) for x, y in points]
    bottom = [(x, y, front+depth) for x, y in points]
    face(list(reversed(top)), slot)
    face(bottom, slot)
    for i in range(len(top)):
        j = (i+1) % len(top)
        face([top[i], top[j], bottom[j], bottom[i]], slot)


# Original twelve-ray solar medallion, raised over the enamel. No emblem from
# another game, sacred image scan, alpha card, texture or downloaded ornament.
star = []
for index in range(24):
    angle = index * math.tau/24 + math.pi/2
    radius = .058 if index % 2 == 0 else .044
    star.append((radius*math.cos(angle), .025+radius*math.sin(angle)))
relief_polygon(star, -.151, .009)
# The recessed blue centre and gold inner rim retain legible material breaks.
for inner, outer, z, slot in [(.025, .032, -.156, 1), (0, .025, -.157, 0)]:
    for index in range(32):
        a = index*math.tau/32
        b = (index+1)*math.tau/32
        p = [(inner*math.cos(a), .025+inner*math.sin(a), z),
             (inner*math.cos(b), .025+inner*math.sin(b), z),
             (outer*math.cos(b), .025+outer*math.sin(b), z),
             (outer*math.cos(a), .025+outer*math.sin(a), z)]
        face(p[1:] if inner == 0 else p, slot)

mesh = bpy.data.meshes.new('Original swept solar guard mesh')
mesh.from_pydata(vertices, [], faces)
mesh.materials.clear()
for mat in materials: mesh.materials.append(mat)
for polygon, slot, rounded in zip(mesh.polygons, slots, smooth):
    polygon.material_index = slot
    polygon.use_smooth = rounded
mesh.update()
obj = bpy.data.objects.new('RamaSolarGuard', mesh)
bpy.context.collection.objects.link(obj)
bpy.context.view_layer.objects.active = obj
obj.select_set(True)
obj['original_authoring'] = 'YUGA RAMA-COMPLETE-01'
obj['bind_bone'] = 'upperarm01.R'
obj['units'] = 'metres; rigid bone-local attachment'

triangles = sum(len(p.vertices)-2 for p in mesh.polygons)
assert 0 < triangles <= 3000
assert len(materials) == 2
assert all(math.isfinite(v) for vertex in mesh.vertices for v in vertex.co)
# Explicitly split finite planar shell from zero-area exporter artefacts.
for polygon in mesh.polygons:
    assert polygon.area > 1e-10, (polygon.index, polygon.area)

bpy.ops.wm.save_as_mainfile(filepath=str(ART/'rama-gear.blend'))
bpy.ops.export_scene.gltf(filepath=str(ASSET), export_format='GLB', use_selection=True,
                          export_cameras=False, export_lights=False, export_extras=True)
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
report = {
    'schema_version':1, 'task':'RAMA-COMPLETE-01', 'id':'rama-solar-shoulder-guard-v1',
    'scope':'Original artist-controlled rigid bow-arm shoulder guard. Candidate off by default until actual pose review. No canonical hero mesh, skin, animation, gameplay or collision replacement.',
    'asset':'games/yuga-native/assets/heroes/rama-gear.glb', 'asset_sha256':sha(ASSET),
    'editable':'games/yuga-native/art/hero-completion/gear/rama-gear.blend', 'editable_sha256':sha(ART/'rama-gear.blend'),
    'authoring_script':'tools/studio/build_rama_gear.py', 'authoring_script_sha256':sha(__file__),
    'blender_version':bpy.app.version_string, 'mesh_objects':1, 'triangles':triangles,
    'material_slots':2, 'materials':[m.name for m in materials], 'lights':0, 'rigs':0,
    'bind_bone':'upperarm01.R', 'dimensions_bone_local_m':[.224,.244,.082],
    'source_terms':'All new geometry, material design and code are original YUGA work; Blender is external GPL authoring software. No third-party game art or texture input.',
    'review_required':['front/rear/profile','raised and lowered bow','full defeat and return','draw/release/step/circle/volley','head/hair/cloth clearance','native close/mid distance'],
}
(ART/'manifest.json').write_text(json.dumps(report, indent=2)+'\n')
print('RAMA_GEAR', json.dumps(report))
