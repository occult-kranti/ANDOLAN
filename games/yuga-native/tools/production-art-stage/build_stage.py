"""Reuse accepted YUGA sources in an isolated, editable Blender art stage.

Blender 4.3.2: blender -b -t 2 --python THIS -- --output NEW_DIR --render
This script never edits canonical assets or exports a replacement gameplay hero.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
import time

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[4]
PROJECT = ROOT / 'games/yuga-native'
SOURCES = {
    'hero': PROJECT / 'assets/heroes/rama-hero.glb',
    'court': PROJECT / 'assets/environment/lanka_courtyard.glb',
    'nature': PROJECT / 'assets/world/nature.glb',
    'diya': PROJECT / 'art/concepts/cloud-diya-pilot/candidate.glb',
    'sandstone_diff': PROJECT / 'art/source-kits/production-reuse-oct23/sandstone-blocks-05/textures/sandstone_blocks_05_diff_1k.png',
    'sandstone_normal': PROJECT / 'art/source-kits/production-reuse-oct23/sandstone-blocks-05/textures/sandstone_blocks_05_nor_gl_1k.png',
    'sandstone_roughness': PROJECT / 'art/source-kits/production-reuse-oct23/sandstone-blocks-05/textures/sandstone_blocks_05_rough_1k.png',
    'sandstone_manifest': PROJECT / 'art/source-kits/production-reuse-oct23/sandstone-blocks-05/manifest.json',
}
VIEWS = [
    ('hero-front', (2, -6, 2.05), (0, 0, 1.02), 2.32),
    ('hero-face', (.36, -3, 1.83), (0, -.025, 1.735), .48),
    ('hero-profile', (5, -.1, 2.05), (0, 0, 1), 2.32),
    ('hero-rear', (-2.6, 5.5, 2.2), (0, .05, 1), 2.3),
]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def aim(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat('-Z', 'Y').to_euler()


def collection(name):
    c = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(c)
    return c


def move(objects, dest):
    for obj in objects:
        for c in list(obj.users_collection):
            c.objects.unlink(obj)
        dest.objects.link(obj)


def import_source(path, dest):
    old = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(path))
    objects = [obj for obj in bpy.data.objects if obj not in old]
    # glTF skeleton display custom shapes are authoring helpers, not GLB meshes.
    for obj in objects:
        if obj.type == 'MESH' and obj.name.startswith('Icosphere'):
            obj.hide_render = True
    move(objects, dest)
    for obj in objects:
        obj['source_path'] = str(path.relative_to(ROOT))
        obj['source_sha256'] = sha(path)
    return objects


def material(name, color, roughness=.6, metallic=0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = (*color, 1)
    p.inputs['Roughness'].default_value = roughness
    p.inputs['Metallic'].default_value = metallic
    return m


def area(name, location, target, energy, size, color):
    data = bpy.data.lights.new(name, type='AREA')
    data.energy, data.size, data.shape, data.color = energy, size, 'DISK', color
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = location
    aim(obj, target)
    return obj


def finite_geometry(objects):
    result = []
    for obj in objects:
        if obj.type != 'MESH' or obj.hide_render:
            continue
        if any(not all(math.isfinite(x) for x in v.co) for v in obj.data.vertices):
            raise RuntimeError('Nonfinite source geometry: ' + obj.name)
        obj.data.calc_loop_triangles()
        result.append({'name': obj.name, 'vertices': len(obj.data.vertices),
                       'triangles': len(obj.data.loop_triangles),
                       'materials': [m.name if m else None for m in obj.data.materials]})
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--render', action='store_true')
    parser.add_argument('--samples', type=int, default=16)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    if not 8 <= args.samples <= 64:
        parser.error('Samples must be 8..64')
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    before_hashes = {name: sha(path) for name, path in SOURCES.items()}
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    hero_collection = collection('01 Accepted Rama — unchanged source')
    court_collection = collection('02 Reused Lanka coastal court')
    detail_collection = collection('03 Reused diya and nature details')
    studio_collection = collection('04 Neutral review ground')
    hero = import_source(SOURCES['hero'], hero_collection)
    rigs = [obj for obj in hero if obj.type == 'ARMATURE']
    if len(rigs) != 1 or len(rigs[0].data.bones) != 164:
        raise RuntimeError('Unexpected accepted hero skeleton')
    rig = rigs[0]
    rig.animation_data_create()
    for track in rig.animation_data.nla_tracks:
        track.mute = True
    idle = next((a for a in bpy.data.actions if a.name.startswith('idle_')), None)
    if idle is None:
        raise RuntimeError('Expected embedded idle action')
    rig.animation_data.action = idle
    rig.data.pose_position = 'POSE'
    scene.frame_set(1)
    hero_report = finite_geometry(hero)
    # All four cameras share this exact pose and accepted geometry; no C9 groom.
    court = import_source(SOURCES['court'], court_collection)
    court_root = bpy.data.objects.new('Court layout transform — presentation only', None)
    court_collection.objects.link(court_root)
    for obj in court:
        if obj.parent is None:
            obj.parent = court_root
    court_root.rotation_euler.z = 0
    # Bounded material-only adoption of one officially published CC0 texture set.
    # Existing court UVs use 0.5 cycles/metre; scale by 2/3 for the 3m tile.
    sandstone_images = {}
    for role in ['sandstone_diff', 'sandstone_normal', 'sandstone_roughness']:
        image = bpy.data.images.load(str(SOURCES[role]), check_existing=True)
        image.colorspace_settings.name = 'sRGB' if role == 'sandstone_diff' else 'Non-Color'
        image.pack()
        sandstone_images[role] = image
    overridden_materials = []
    for mat in bpy.data.materials:
        if not mat.name.startswith('Courtyard_stone_'):
            continue
        nodes, links = mat.node_tree.nodes, mat.node_tree.links
        shader = next(n for n in nodes if n.type == 'BSDF_PRINCIPLED')
        texcoord = nodes.new('ShaderNodeTexCoord')
        mapping = nodes.new('ShaderNodeVectorMath')
        mapping.operation = 'SCALE'
        mapping.inputs[3].default_value = 2 / 3
        links.new(texcoord.outputs['UV'], mapping.inputs[0])
        texture_nodes = {}
        for role, image in sandstone_images.items():
            tex = nodes.new('ShaderNodeTexImage')
            tex.image = image
            links.new(mapping.outputs['Vector'], tex.inputs['Vector'])
            texture_nodes[role] = tex
        links.new(texture_nodes['sandstone_diff'].outputs['Color'], shader.inputs['Base Color'])
        links.new(texture_nodes['sandstone_roughness'].outputs['Color'], shader.inputs['Roughness'])
        normal = nodes.new('ShaderNodeNormalMap')
        normal.inputs['Strength'].default_value = .3
        links.new(texture_nodes['sandstone_normal'].outputs['Color'], normal.inputs['Color'])
        links.new(normal.outputs['Normal'], shader.inputs['Normal'])
        overridden_materials.append(mat.name)
    # Place the reused court's gate about ten metres behind the portrait stage.
    court_root.location.y = -15
    diya = import_source(SOURCES['diya'], detail_collection)
    diya_meshes = [obj for obj in diya if obj.type == 'MESH' and not obj.hide_render]
    for obj in diya_meshes:
        obj.scale = (.66, .66, .66)
        obj.location = (1.12, -.05, .332)
    nature = import_source(SOURCES['nature'], detail_collection)
    for obj in nature:
        obj.hide_render = True
    # Reuse existing complete lotus/rock meshes; do not synthesize a new kit.
    for index, (name, location, scale) in enumerate([
        ('lotus_cluster', (2.3, -.1, .024), (.8, .8, .22)),
        ('lotus_cluster', (2.6, 1.3, .024), (.55, .55, .16)),
        ('rock_island', (2.6, 2.4, .015), (1.1, .7, .32)),
    ]):
        source = next(obj for obj in nature if obj.name == name)
        obj = source.copy()
        obj.data = source.data
        detail_collection.objects.link(obj)
        obj.name = 'Staged reused detail %02d %s' % (index, name)
        obj.location, obj.scale, obj.hide_render = location, scale, False
    # A local shallow-water plane is presentation set dressing, not map collision.
    bpy.ops.mesh.primitive_plane_add(size=2, location=(2.7, 1.0, .012))
    water = bpy.context.object
    water.name = 'Presentation water patch — no gameplay collision'
    water.scale = (1.1, 2.3, 1)
    water.data.materials.append(material('Stage water — teal reflected surface', (.016, .075, .073), .17, .25))
    move([water], detail_collection)
    bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, -.025))
    floor = bpy.context.object
    floor.name = 'Neutral source review ground'
    floor.data.materials.append(material('Review ground — charcoal', (.034, .043, .057), .72))
    move([floor], studio_collection)
    scene.world = bpy.data.worlds.new('Indigo coastal evening')
    scene.world.use_nodes = True
    scene.world.node_tree.nodes['Background'].inputs['Color'].default_value = (.075, .11, .17, 1)
    scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value = .32
    lights = [
        area('Warm key — full source form', (3, -4, 4), (0, 0, 1.2), 610, 3.4, (1, .83, .64)),
        area('Cool fill — readable cobalt', (-3, -1, 2.5), (0, 0, 1.2), 280, 3, (.56, .73, 1)),
        area('Pale gold rim — hair separation', (0, 3, 3.5), (0, 0, 1.2), 740, 2.8, (1, .9, .7)),
    ]
    sun_data = bpy.data.lights.new('Coastal dusk environment sun', 'SUN')
    sun_data.energy, sun_data.angle, sun_data.color = 1.15, .18, (1, .76, .52)
    sun = bpy.data.objects.new('Coastal dusk environment sun', sun_data)
    scene.collection.objects.link(sun)
    sun.rotation_euler = (.6, -.4, -.75)
    camera_data = bpy.data.cameras.new('Source-matched review camera')
    camera = bpy.data.objects.new('Source-matched review camera', camera_data)
    scene.collection.objects.link(camera)
    scene.camera = camera
    camera_data.type = 'ORTHO'
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = args.samples
    scene.cycles.use_denoising = False
    scene.render.threads_mode = 'FIXED'
    scene.render.threads = 2
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.view_settings.view_transform = 'AgX'
    scene.view_settings.look = 'AgX - Medium High Contrast'
    scene.render.film_transparent = False
    scene['stage_scope'] = 'Presentation prototype. Accepted hero unchanged; not finished-groom, gameplay, animation or Deadlock-parity acceptance.'
    scene['source_hashes_json'] = json.dumps(before_hashes, sort_keys=True)
    renders = []

    def render(name, width, height, camera_contract):
        scene.render.resolution_x, scene.render.resolution_y = width, height
        path = output / (name + '.png')
        scene.render.filepath = str(path)
        if args.render:
            begin = time.monotonic()
            bpy.ops.render.render(write_still=True)
            renders.append({'path': path.name, 'sha256': sha(path), 'bytes': path.stat().st_size,
                            'width': width, 'height': height, 'seconds': time.monotonic() - begin,
                            'camera': camera_contract})

    court_collection.hide_render = detail_collection.hide_render = True
    sun.hide_render = True
    for name, position, target, scale in VIEWS:
        camera_data.type, camera_data.ortho_scale = 'ORTHO', scale
        camera.location = position
        aim(camera, target)
        render(name, 640, 800, {'position': position, 'target': target, 'ortho_scale': scale,
                              'pose': 'embedded idle, frame 1; fixed for all four'})
    court_collection.hide_render = detail_collection.hide_render = False
    studio_collection.hide_render = True
    sun.hide_render = False
    camera_data.type, camera_data.lens = 'PERSP', 52
    camera.location = (3.3, -6.0, 2.35)
    aim(camera, (.25, .3, 1.04))
    camera_data.dof.use_dof = True
    camera_data.dof.focus_distance = (camera.location - Vector((0, 0, 1.05))).length
    camera_data.dof.aperture_fstop = 6.3
    render('lanka-water-court', 960, 640, {'position': list(camera.location), 'target': [.25, .3, 1.04],
                                       'lens_mm': 52, 'fstop': 6.3})
    for image in bpy.data.images:
        if image.size[0] > 0 and image.size[1] > 0 and not image.packed_file:
            image.pack()
    scene_path = output / 'lanka-water-stage.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(scene_path), compress=True)
    after_hashes = {name: sha(path) for name, path in SOURCES.items()}
    if before_hashes != after_hashes:
        raise RuntimeError('A canonical source changed during the stage')
    report = {
        'schema_version': 1, 'title': 'Rama / Lanka coastal-water presentation stage',
        'scope': scene['stage_scope'], 'runtime_promoted': False, 'game_completion_credit': 0,
        'blender': bpy.app.version_string, 'renderer': 'Cycles CPU', 'samples': args.samples,
        'denoising': False, 'threads': 2, 'script_sha256': sha(__file__),
        'sources': [{'role': name, 'path': str(path.relative_to(ROOT)), 'sha256': before_hashes[name],
                     'bytes': path.stat().st_size} for name, path in SOURCES.items()],
        'canonical_source_hashes_unchanged': True,
        'presentation_material_overrides': {'materials': overridden_materials,
            'source': 'Poly Haven sandstone_blocks_05, Rob Tuytel, CC0',
            'tile_metres': 3, 'normal_strength': .3, 'displacement_used': False,
            'albedo_color_space': 'sRGB', 'normal_roughness_color_space': 'Non-Color'},
        'imported_images': [{'name': im.name, 'width': im.size[0], 'height': im.size[1],
                             'packed': bool(im.packed_file)} for im in bpy.data.images if im.size[0] > 0],
        'hero_meshes': hero_report,
        'hero_bones': len(rig.data.bones), 'hero_actions': [a.name for a in bpy.data.actions],
        'hero_geometry_edited': False, 'hero_pose': 'embedded idle, frame 1',
        'scene': {'path': scene_path.name, 'sha256': sha(scene_path), 'bytes': scene_path.stat().st_size},
        'renders': renders, 'elapsed_seconds': time.monotonic() - started,
        'open_gates': ['Artist-controlled hair sweep/gather/joins', 'Costume drape and anatomical refinement',
                       'Continuous pose/contact review', 'Diya topology/LODs/collision/flame effect',
                       'Gameplay-distance art and physical-GPU performance', 'Commercial-quality parity'],
    }
    (output / 'stage-manifest.json').write_text(json.dumps(report, indent=2) + '\n')
    print('YUGA_PRODUCTION_ART_STAGE=' + json.dumps(report, separators=(',', ':')), flush=True)


if __name__ == '__main__':
    main()
