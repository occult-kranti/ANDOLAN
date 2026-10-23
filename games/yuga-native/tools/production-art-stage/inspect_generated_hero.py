"""Inspect/render the exact newly generated unrigged Rama source candidate.

Reuses Blender's official glTF importer and the same bounded studio intake as the
prior diya pilot. No retopology, rigging, animation, collision or promotion.
"""
import argparse
from pathlib import Path
import hashlib
import json
import math
import sys
import time
import bpy
from mathutils import Vector


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def aim(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat('-Z', 'Y').to_euler()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--front-sign', type=int, choices=[-1, 1], default=-1)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    source, output = args.source.resolve(), args.output.resolve()
    if sha(source) != '0c9fe46baa0a2f6e5f9cdb9386aad1405f9f22470a729c2538142576981f5c0b':
        raise RuntimeError('Input differs from the bound generation')
    output.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(source))
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']
    rigs = [obj for obj in bpy.context.scene.objects if obj.type == 'ARMATURE']
    if not meshes:
        raise RuntimeError('No imported source mesh')
    if any(not all(math.isfinite(x) for x in v.co) for obj in meshes for v in obj.data.vertices):
        raise RuntimeError('Nonfinite generated source')
    points = [obj.matrix_world @ Vector(v) for obj in meshes for v in obj.bound_box]
    low = Vector([min(p[i] for p in points) for i in range(3)])
    high = Vector([max(p[i] for p in points) for i in range(3)])
    center, span = (low + high) * .5, max(high - low)
    if not math.isfinite(span) or span <= 0:
        raise RuntimeError('Degenerate generated source bounds')
    details = []
    for obj in meshes:
        obj.data.calc_loop_triangles()
        details.append({'name': obj.name, 'vertices': len(obj.data.vertices), 'triangles': len(obj.data.loop_triangles),
                        'uv_layers': len(obj.data.uv_layers), 'material_slots': [m.name if m else None for m in obj.data.materials]})
    source_images = [{'name': im.name, 'width': im.size[0], 'height': im.size[1], 'packed': bool(im.packed_file)} for im in bpy.data.images]
    if any(im['width'] <= 0 or im['height'] <= 0 for im in source_images):
        raise RuntimeError('Missing generated image data')
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 32
    scene.cycles.use_denoising = False
    scene.render.threads_mode = 'FIXED'
    scene.render.threads = 2
    scene.render.resolution_x, scene.render.resolution_y = 640, 800
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.view_settings.view_transform = 'AgX'
    scene.view_settings.look = 'AgX - Medium High Contrast'
    scene.world = bpy.data.worlds.new('Generated source neutral studio')
    scene.world.use_nodes = True
    scene.world.node_tree.nodes['Background'].inputs['Color'].default_value = (.08, .105, .14, 1)
    scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value = .45
    bpy.ops.mesh.primitive_plane_add(size=span * 20, location=(center.x, center.y, low.z - span * .012))
    floor = bpy.context.object
    floor.name = 'Source review ground'
    mat = bpy.data.materials.new('Source review ground charcoal')
    mat.diffuse_color = (.065, .075, .09, 1)
    mat.use_nodes = True
    mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (.065, .075, .09, 1)
    mat.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = .8
    floor.data.materials.append(mat)
    for name, offset, power, color in [
        ('warm key', (2, -3, 4), 550, (1, .88, .72)),
        ('cool fill', (-3, -1, 2), 260, (.65, .8, 1)),
        ('ivory rim', (1, 3, 3), 650, (1, .93, .8)),
    ]:
        data = bpy.data.lights.new(name, 'AREA')
        data.energy, data.color, data.size, data.shape = power * span * span, color, span * 3, 'DISK'
        light = bpy.data.objects.new(name, data)
        scene.collection.objects.link(light)
        light.location = center + Vector(offset) * span
        aim(light, center)
    data = bpy.data.cameras.new('Generated source review camera')
    camera = bpy.data.objects.new('Generated source review camera', data)
    scene.collection.objects.link(camera)
    scene.camera = camera
    data.type, data.ortho_scale = 'ORTHO', span * 1.25
    renders = []
    sign = args.front_sign
    for name, offset in [('generated-front-three-quarter', (1.1, sign * 3, .75)),
                         ('generated-rear-three-quarter', (-1.1, sign * -3, .75))]:
        camera.location = center + Vector(offset) * span
        aim(camera, center)
        path = output / (name + '.png')
        scene.render.filepath = str(path)
        begin = time.monotonic()
        bpy.ops.render.render(write_still=True)
        renders.append({'path': path.name, 'sha256': sha(path), 'bytes': path.stat().st_size,
                        'seconds': time.monotonic() - begin, 'camera_offset_in_source_span': offset,
                        'target': list(center), 'ortho_scale': data.ortho_scale})
    scene['source_scope'] = 'Unrigged ML-generated source candidate. No runtime promotion or finished-game quality acceptance.'
    scene['source_sha256'] = sha(source)
    for image in bpy.data.images:
        if image.size[0] > 0 and image.type != 'RENDER_RESULT' and not image.packed_file:
            image.pack()
    scene_path = output / 'rama-generated-source-intake.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(scene_path), compress=True)
    report = {'schema_version': 1, 'scope': scene['source_scope'], 'source_sha256': sha(source),
              'source_bytes': source.stat().st_size, 'script_sha256': sha(__file__),
              'blender': bpy.app.version_string, 'renderer': 'Cycles CPU', 'samples': 32, 'denoising': False, 'threads': 2,
              'mesh_objects': details, 'images': source_images, 'armatures': len(rigs), 'actions': len(bpy.data.actions),
              'bounds_min': list(low), 'bounds_max': list(high), 'real_world_scale_qualified': False,
              'finite_geometry': True, 'runtime_promoted': False, 'game_completion_credit': 0,
              'renders': renders, 'scene': {'path': scene_path.name, 'sha256': sha(scene_path), 'bytes': scene_path.stat().st_size},
              'elapsed_seconds': time.monotonic() - started,
              'open_gates': ['Rear/occluded geometry and texture reconstruction', 'Facial and hand topology',
                             'Retopology and UV/material authoring', 'Game rig, skin weights, deformation and continuous animation',
                             'Physics/collision, LODs and real hardware performance', 'Weight/dependency/output licensing intake']}
    (output / 'source-intake.json').write_text(json.dumps(report, indent=2) + '\n')
    print('YUGA_GENERATED_SOURCE_INTAKE=' + json.dumps(report, separators=(',', ':')))


if __name__ == '__main__':
    main()
