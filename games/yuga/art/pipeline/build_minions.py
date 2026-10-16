"""Build the seven original lane/jungle skins without rewriting hero assets.

blender -b --factory-startup -t 2 --python games/yuga/art/pipeline/build_minions.py -- soldier yaksha --preview
Omit IDs to build all seven. Uses only the bundled, pinned CC0 anatomy data.
"""
import hashlib
import json
import math
import struct
import sys
from array import array
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from anatomy import build_anatomy
from geometry import Sculpt
from minion_geometry import sculpt_unit
from minion_animations import author_minion_animations, validate_unit_deformation

ART = HERE.parent
GAME = ART.parent
SOURCE = ART / 'sources/makehuman'
OUT = GAME / 'client/assets/units'
LOCAL = Path('/workspace/tooling/yuga-art/output/units')
PIPELINE_FILES = ['build_minions.py', 'minion_geometry.py', 'minion_animations.py', 'anatomy.py', 'geometry.py', 'animations.py']
PIPELINE_HASHES = {name: hashlib.sha256((HERE / name).read_bytes()).hexdigest() for name in PIPELINE_FILES}
UNITS = [
    dict(id='soldier', category='lane', height=1.45, width=1.03, face_width=1.0, triangles=7600, cloth=(.075, .14, .22), skin=(.35, .18, .09)),
    dict(id='city-watch', category='lane', height=1.42, width=1.0, face_width=.98, triangles=7400, cloth=(.30, .19, .065), skin=(.39, .22, .12)),
    dict(id='minister', category='lane', height=1.40, width=.98, face_width=1.03, triangles=7500, cloth=(.14, .035, .20), skin=(.30, .14, .065)),
    dict(id='king', category='lane', height=1.52, width=1.15, face_width=1.08, triangles=8000, cloth=(.34, .035, .045), skin=(.32, .15, .065)),
    dict(id='yaksha', category='neutral', height=2.05, width=1.28, face_width=1.16, triangles=10000, cloth=(.12, .21, .055), skin=(.23, .26, .13)),
    dict(id='naga', category='neutral', height=1.95, width=1.02, face_width=.94, triangles=10000, cloth=(.015, .24, .22), skin=(.13, .25, .20)),
    dict(id='sky-sentinel', category='neutral', height=1.90, width=1.08, face_width=.96, triangles=9500, cloth=(.07, .15, .30), skin=(.29, .22, .14)),
]


def material(name, color, metal=0, rough=.65):
    result = bpy.data.materials.new(name)
    result.diffuse_color = (*color, 1)
    result.use_nodes = True
    shader = result.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value = (*color, 1)
    shader.inputs['Metallic'].default_value = metal
    shader.inputs['Roughness'].default_value = rough
    return result


def materials(c):
    result = dict(skin=material('Unit skin', c['skin']), cloth=material('Original unit weave', c['cloth'], rough=.8),
                  trim=material('Brass unit trim', (.45, .28, .085), metal=.7, rough=.42),
                  dark=material('Hair leather and wood', (.022, .016, .01), rough=.85))
    if c['id'] == 'yaksha':
        result['trim'] = material('Carved weathered guardian bark', (.22, .17, .065), rough=.94)
    # Small deterministic original textile; no repeated multi-megabyte atlas.
    size = 256
    pixels = array('f')
    for y in range(size):
        for x in range(size):
            u, v = (x / size * 6) % 1 - .5, (y / size * 6) % 1 - .5
            edge = abs(abs(u) + abs(v) - .44) < .018
            if c['id'] == 'yaksha':
                edge = abs(u - .20 * math.sin(v * 7 + x / size)) < .035
            elif c['id'] == 'sky-sentinel':
                edge = abs(v - abs(u) * .65 + .14) < .025
            shade = .88 + .12 * ((x + y) % 2)
            color = (.40, .26, .085) if edge else c['cloth']
            pixels.extend((color[0] * shade, color[1] * shade, color[2] * shade, 1))
    image = bpy.data.images.new(c['id'] + ' original 256px woven diamond', width=size, height=size)
    image.pixels.foreach_set(pixels)
    image.pack()
    node = result['cloth'].node_tree.nodes.new('ShaderNodeTexImage')
    node.image = image
    result['cloth'].node_tree.links.new(node.outputs['Color'], result['cloth'].node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
    return result


def prune_rig(rig, meshes):
    prefixes = ('root', 'spine', 'neck', 'head', 'eye.', 'pelvis.', 'clavicle.', 'shoulder',
                'upperarm', 'lowerarm', 'wrist.', 'upperleg', 'lowerleg', 'foot.', 'finger', 'metacarpal')
    keep = {bone.name for bone in rig.data.bones if bone.name.startswith(prefixes)}
    for name in list(keep):
        parent = rig.data.bones[name].parent
        while parent:
            keep.add(parent.name)
            parent = parent.parent
    remap = {}
    for bone in rig.data.bones:
        parent = bone
        while parent and parent.name not in keep:
            parent = parent.parent
        remap[bone.name] = parent.name if parent else 'root'
    for obj in meshes:
        names = {g.index: g.name for g in obj.vertex_groups}
        rows = []
        for vertex in obj.data.vertices:
            combined = {}
            for group in vertex.groups:
                name = remap.get(names[group.group])
                if name:
                    combined[name] = combined.get(name, 0) + group.weight
            rows.append(sorted(combined.items(), key=lambda item: item[1], reverse=True)[:4])
        obj.vertex_groups.clear()
        groups = {}
        for index, row in enumerate(rows):
            total = sum(weight for _, weight in row)
            if total <= 0:
                raise AssertionError(f'Unweighted unit vertex {obj.name}/{index}')
            for name, weight in row:
                if name not in groups:
                    groups[name] = obj.vertex_groups.new(name=name)
                groups[name].add([index], weight / total, 'REPLACE')
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode='EDIT')
    for bone in list(rig.data.edit_bones):
        if bone.name not in keep:
            rig.data.edit_bones.remove(bone)
    bpy.ops.object.mode_set(mode='OBJECT')
    return len(keep)


def preview(rig, actions, c):
    scene = bpy.context.scene
    rig.animation_data.action = actions['idle']
    scene.frame_set(1)
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 16
    scene.cycles.use_denoising = False
    scene.render.resolution_x = 560
    scene.render.resolution_y = 720
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.world.color = (.04, .05, .07)
    bpy.ops.mesh.primitive_plane_add(size=100, location=(0, 0, -.02))
    bpy.context.object.data.materials.append(material('Preview floor', (.035, .045, .06)))
    target = Vector((0, 0, c['height'] * .55))
    for position, power in [((2, -4, 5), 500), ((-3, -1, 3), 300), ((0, 3, 4), 500)]:
        data = bpy.data.lights.new('Unit studio light', 'AREA')
        data.energy, data.size = power, 3
        obj = bpy.data.objects.new('Unit studio light', data)
        scene.collection.objects.link(obj)
        obj.location = position
        obj.rotation_euler = (target - obj.location).to_track_quat('-Z', 'Y').to_euler()
    data = bpy.data.cameras.new('Actual unit camera')
    camera = bpy.data.objects.new('Actual unit camera', data)
    scene.collection.objects.link(camera)
    camera.location = (2.4, -5.8, 2.6)
    camera.rotation_euler = (target - camera.location).to_track_quat('-Z', 'Y').to_euler()
    data.type, data.ortho_scale = 'ORTHO', c['height'] * 1.5
    scene.camera = camera
    scene.view_settings.view_transform = 'AgX'
    folder = ART / 'previews/units'
    folder.mkdir(parents=True, exist_ok=True)
    scene.render.filepath = str(folder / (c['id'] + '-actual-model.png'))
    bpy.ops.render.render(write_still=True)


def build(c, render=False):
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for action in list(bpy.data.actions):
        bpy.data.actions.remove(action)
    body, rig, weights, tree = build_anatomy(SOURCE, 'male', c['height'], c['width'], c['face_width'])
    rig.name = 'YugaUnitRig'
    validation = body.copy()
    validation.data = body.data.copy()
    validation.name = 'ValidationAnatomy'
    bpy.context.collection.objects.link(validation)
    validation.hide_render = True
    validation.hide_set(True)
    validation.select_set(False)
    mats = materials(c)
    for name in ('skin', 'cloth'):
        body.data.materials.append(mats[name])
    for polygon in body.data.polygons:
        p = polygon.center
        polygon.material_index = 1 if p.z < c['height'] * .54 or (p.z < c['height'] * .82 and abs(p.x) < c['height'] * .145) else 0
    sculpt = Sculpt(rig, body, weights, tree)
    sculpt_unit(sculpt, c, mats)
    edit = bmesh.new()
    edit.from_mesh(body.data)
    hidden = [face for face in edit.faces if
              c['height'] * .10 < face.calc_center_median().z < c['height'] * .53 or
              (c['height'] * .54 < face.calc_center_median().z < c['height'] * .82 and
               abs(face.calc_center_median().x) < c['height'] * .145)]
    bmesh.ops.delete(edit, geom=hidden, context='FACES')
    bmesh.ops.delete(edit, geom=[v for v in edit.verts if not v.link_faces], context='VERTS')
    edit.to_mesh(body.data)
    edit.free()
    body.data.update()
    bpy.ops.object.select_all(action='DESELECT')
    for obj in sculpt.objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.join()
    body.name = c['id'] + '_skinned_unit'
    for modifier in list(body.modifiers)[1:]:
        body.modifiers.remove(modifier)
    body.data.calc_loop_triangles()
    raw_triangles = len(body.data.loop_triangles)
    reduction = body.modifiers.new('Bounded unit topology reduction', 'DECIMATE')
    reduction.ratio = min(1, c['triangles'] / raw_triangles)
    bpy.ops.object.modifier_apply(modifier=reduction.name)
    bone_count = prune_rig(rig, [body, validation])
    # Source-body validation is retained separately; exported cloth and props
    # receive an independent GLB sampler and visual gate, not this body claim.
    actions = author_minion_animations(rig, c['id'])
    validation.hide_set(False)
    deformation = validate_unit_deformation(rig, validation, actions)
    validation.hide_set(True)
    rig.animation_data.action = actions['idle']
    bpy.context.scene.frame_set(1)
    bpy.context.view_layer.update()
    bpy.ops.object.select_all(action='DESELECT')
    body.select_set(True)
    rig.select_set(True)
    bpy.context.view_layer.objects.active = rig
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / (c['id'] + '.glb')
    bpy.ops.export_scene.gltf(filepath=str(path), export_format='GLB', use_selection=True,
        export_animations=True, export_animation_mode='ACTIONS', export_force_sampling=True,
        export_frame_range=False, export_skins=True, export_all_influences=False, export_yup=True,
        export_image_format='JPEG', export_jpeg_quality=82)
    binary = path.read_bytes()
    length, _ = struct.unpack_from('<II', binary, 12)
    doc = json.loads(binary[20:20 + length])
    primitives = [p for mesh in doc.get('meshes', []) for p in mesh['primitives']]
    positions = [doc['accessors'][p['attributes']['POSITION']] for p in primitives]
    bounds = dict(minimum=[min(p['min'][i] for p in positions) for i in range(3)],
                  maximum=[max(p['max'][i] for p in positions) for i in range(3)])
    result = dict(id=c['id'], category=c['category'], file=str(path.relative_to(GAME)),
        bytes=len(binary), sha256=hashlib.sha256(binary).hexdigest(),
        triangles=sum(doc['accessors'][p['indices']]['count'] // 3 for p in primitives),
        vertices=sum(p['count'] for p in positions), bones=bone_count,
        materials=len(doc.get('materials', [])), clips=[a['name'] for a in doc.get('animations', [])],
        heightMetres=c['height'], restBounds=bounds, restBoundsCoordinates='glTF mesh local Y-up, +Z forward, metres',
        textureResolution=256, sourceTrianglesBeforeReduction=raw_triangles, pipelineHashes=PIPELINE_HASHES)
    assert set(result['clips']) == {'idle', 'run', 'fire', 'defeat'}
    assert result['materials'] <= 4
    LOCAL.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(LOCAL / (c['id'] + '-authored.blend')))
    (LOCAL / (c['id'] + '-deformation.json')).write_text(json.dumps(deformation, indent=2) + '\n')
    print('YUGA_UNIT ' + json.dumps(result), flush=True)
    if render:
        preview(rig, actions, c)
    return result


def main():
    args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    requested = [arg for arg in args if not arg.startswith('--')]
    assert not set(requested) - {c['id'] for c in UNITS}, requested
    selected = [c for c in UNITS if not requested or c['id'] in requested]
    path = ART / 'unit-assets.json'
    previous = json.loads(path.read_text()) if path.exists() else {}
    models = {model['id']: model for model in previous.get('models', [])}
    for config in selected:
        models[config['id']] = build(config, '--preview' in args)
        manifest = dict(schema=1, sourceCommitMakeHuman='a8bc2d54ff0ac92e78ff71431b1023eda42bf482',
            sourceLicense='CC0-1.0 anatomy/rig data; original unit clothing/equipment/motion',
            sourceManifestSha256=hashlib.sha256((SOURCE / 'manifest.json').read_bytes()).hexdigest(),
            pipelineFiles=[dict(file='pipeline/' + name, sha256=sha) for name, sha in PIPELINE_HASHES.items()],
            models=[models[c['id']] for c in UNITS if c['id'] in models], front='+Z', up='+Y', units='metres',
            limitations=['Grounded humanoid guardians; naga does not slither and sentinel does not fly.',
                'No LODs, cloth simulation or facial animation; runtime population performance needs measurement.',
                'Four normalized skin influences; four materials and one original embedded 256px textile per unit.',
                'Art silhouettes and held props do not alter authoritative collider or attack range.'])
        path.write_text(json.dumps(manifest, indent=2) + '\n')


if __name__ == '__main__':
    main()
