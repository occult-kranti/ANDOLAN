# SPDX-License-Identifier: GPL-3.0-or-later
"""Execute pinned MPFB card/atlas helpers on the accepted CC0 Rama donor study.

This isolated authoring adapter creates hair-only assets. It never writes the
canonical body, rig, clips or game scene. Upstream methods are extracted from
the retained exact source, not reimplemented or loaded through addon UI state.
"""
import argparse
import ast
import collections
import hashlib
import importlib.util
import json
import math
import sys
import time
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parents[3]
PACKET = ROOT / 'art/reuse-next-heroes/mpfb-native-r1'
MASTER_SHA = '8cd254da5f789c14a59a1f150ee738fcea556c2c1b9accb3e6193fc45f0b3ace'
CANONICAL_SHA = 'db4b2ec7a14cad72299d462c1265374f615d5e9d8b8852c4669e1f960f78245e'
CARD_SHA = 'cdfb13f0cd9cd33fef39b63ca54d5e4da0423d92770bff8130e0db51b95da83b'
BAKE_SHA = '7e2630351754397a784881f903af201c05a8f1f8993da8876513fc625a3c8bbe'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


class ImagePixels:
    """Blender's direct pixel API; no MPFB application state is emulated."""
    @staticmethod
    def read_image_pixels(image):
        pixels = np.empty(len(image.pixels), dtype=np.float32)
        image.pixels.foreach_get(pixels)
        return pixels

    @staticmethod
    def write_image_pixels(image, pixels):
        image.pixels.foreach_set(pixels.ravel())
        image.update()


def upstream():
    card_path = PACKET / 'upstream/haircardservice.py'
    bake_path = PACKET / 'upstream/hairbakeservice.py'
    assert sha(card_path) == CARD_SHA and sha(bake_path) == BAKE_SHA
    spec = importlib.util.spec_from_file_location('yuga_pinned_mpfb_cards', card_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    # These exact dependency-free methods are invoked directly. Addon operators,
    # registration and filesystem/user preference services are deliberately absent.
    wanted = {
        '_build_ray_portal_material', '_limit_shader_to_range',
        '_build_emit_material', '_white_color', '_build_holdout_material',
        '_find_uv_islands', '_pick_atlas_variants', '_has_generated_card_uvs',
        '_card_uv_cell_grid', '_pack_card_uvs_into_grid', '_shifted',
        '_dilate_image_colour',
    }
    tree = ast.parse(bake_path.read_text())
    cls = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == 'HairBakeService')
    cls.body = [node for node in cls.body if isinstance(node, ast.FunctionDef) and node.name in wanted]
    assert {node.name for node in cls.body} == wanted
    subset = ast.fix_missing_locations(ast.Module(body=[cls], type_ignores=[]))
    namespace = {
        'bpy': bpy, 'collections': collections, 'Any': object, 'Callable': object,
        '_PORTAL_DIRECTION_NODE': 'PortalDirection', '_PORTAL_LIFT_NODE': 'PortalLift',
        '_UV_PARKING_OFFSET': 10.0, 'HairEditorService': ImagePixels,
    }
    # Future annotations avoid importing type-only dependencies from the addon.
    exec(compile('from __future__ import annotations\n' + ast.unparse(subset), str(bake_path), 'exec'), namespace)
    return module.HairCardService, namespace['HairBakeService'], sorted(wanted)


def mesh_snapshot(obj):
    mesh = obj.data
    return {
        'positions': digest([tuple(v.co) for v in mesh.vertices]),
        'topology': digest([list(p.vertices) for p in mesh.polygons]),
        'uv': digest([tuple(v.uv) for v in mesh.uv_layers.active.data]),
    }


def input_socket(modifier, label, value):
    socket = next(s for s in modifier.node_group.interface.items_tree if s.item_type == 'SOCKET' and s.in_out == 'INPUT' and s.name == label)
    modifier[socket.identifier] = value


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--resolution', type=int, default=1024)
    parser.add_argument('--samples', type=int, default=24)
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    assert sha(args.source) == MASTER_SHA
    assert sha(ROOT / 'assets/heroes/rama-hero.glb') == CANONICAL_SHA
    assert args.resolution in (512, 1024) and 8 <= args.samples <= 32
    args.output.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    Card, Bake, methods = upstream()
    bpy.ops.wm.open_mainfile(filepath=str(args.source.resolve()))
    scene = bpy.context.scene
    hair = bpy.data.objects['MPFB CC0 fitted rear guides']
    body = bpy.data.objects['MPFB nape preview Rama']
    baseline = bpy.data.objects['APPROVED BASELINE Rama']
    human = bpy.data.objects['HIDDEN source Human for MPFB curve surface']
    rig = next(o for o in scene.objects if o.type == 'ARMATURE')
    protected = mesh_snapshot(body)
    rig_before = digest([(b.name, b.parent.name if b.parent else '', [list(row) for row in b.matrix_local]) for b in rig.data.bones])
    guides_before = digest([tuple(v.vector) for v in hair.data.attributes['position'].data])
    assert len(rig.data.bones) == 164
    assert 'head' in rig.data.bones
    deps = bpy.context.evaluated_depsgraph_get()
    evaluated = hair.evaluated_get(deps).data
    assert 0 < len(evaluated.curves) <= 20000 and 0 < len(evaluated.points) <= 1300000
    source_counts = {'curves': len(evaluated.curves), 'points': len(evaluated.points)}

    # Actual upstream k-means and arc-length averaged cluster strands.
    mesh = Card.build_cluster_ribbon_mesh(hair, 72, 3, 0, 24, depsgraph=deps)
    assert mesh is not None
    cards = bpy.data.objects.new('YUGA MPFB nape cards near CANDIDATE', mesh)
    scene.collection.objects.link(cards)
    cards.matrix_world = hair.matrix_world.copy()
    modifier = cards.modifiers.new('Pinned MPFB cluster-ribbon generator', 'NODES')
    modifier.node_group = Card.build_cluster_ribbon_node_group('YUGA pinned MPFB 72-cluster ribbons', human)
    settings = {'Profile steps': 16, 'Card width': .024, 'Width from cluster': .35,
                'Taper': .78, 'Offset': .002, 'Extend tip': .006, 'Twist': 0.0}
    for label, value in settings.items():
        input_socket(modifier, label, value)
    bpy.context.view_layer.update()
    evaluated_cards = cards.evaluated_get(bpy.context.evaluated_depsgraph_get())
    baked_mesh = bpy.data.meshes.new_from_object(evaluated_cards, preserve_all_data_layers=True, depsgraph=bpy.context.evaluated_depsgraph_get())
    assert len(baked_mesh.vertices) > 0 and len(baked_mesh.polygons) > 0
    cards.modifiers.clear()
    cards.data = baked_mesh
    for polygon in cards.data.polygons:
        polygon.use_smooth = True
    # World coordinates let the hair-only mesh share the exact current rig origin.
    cards.data.transform(cards.matrix_world)
    cards.matrix_world = Matrix.Identity(4)
    plan = Bake._pack_card_uvs_into_grid(cards, 1.0, args.resolution)
    assert not plan['final_uvs']  # Every card gets a unique cell, no off-atlas parked UVs.
    uv = [tuple(v.uv) for v in cards.data.uv_layers.active.data]
    assert all(math.isfinite(x) and 0 <= x <= 1 for row in uv for x in row)

    visibility = {o.name: o.hide_render for o in scene.objects}
    for obj in scene.objects:
        if obj.type in ('MESH', 'CURVES'):
            obj.hide_render = obj not in (hair, cards)
    for prop in ('visible_shadow', 'visible_diffuse', 'visible_glossy', 'visible_transmission', 'visible_volume_scatter'):
        setattr(cards, prop, False)
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = args.samples
    scene.cycles.use_denoising = False
    scene.cycles.transparent_max_bounces = 32
    scene.render.threads_mode = 'FIXED'
    scene.render.threads = 2
    scene.render.film_transparent = True
    scene.render.bake.use_selected_to_active = False
    scene.render.bake.use_pass_direct = False
    scene.render.bake.use_pass_indirect = False
    scene.render.bake.margin = 2
    portal = Bake._build_ray_portal_material(.015)
    cards.data.materials.clear()
    cards.data.materials.append(portal)
    image = bpy.data.images.new('MPFB donor nape actual coverage atlas', width=args.resolution, height=args.resolution, alpha=True)
    image.colorspace_settings.name = 'Non-Color'
    tex = portal.node_tree.nodes.new('ShaderNodeTexImage')
    tex.image = image
    portal.node_tree.nodes.active = tex
    original_mats = list(hair.data.materials)
    coverage_mat = Bake._build_emit_material('MPFB actual coverage only', Bake._white_color, {'ray_range': .08})
    hair.data.materials.clear()
    hair.data.materials.append(coverage_mat)
    bpy.ops.object.select_all(action='DESELECT')
    cards.select_set(True)
    bpy.context.view_layer.objects.active = cards
    bake_started = time.monotonic()
    bpy.ops.object.bake(type='EMIT')
    pixels = ImagePixels.read_image_pixels(image).reshape(-1, 4)
    alpha = np.clip(pixels[:, :3].max(axis=1), 0, 1)
    coverage = {'min': float(alpha.min()), 'max': float(alpha.max()), 'mean': float(alpha.mean()),
                'pixels_above_half': int(np.count_nonzero(alpha > .5)), 'pixels_above_01': int(np.count_nonzero(alpha > .01))}
    assert np.isfinite(pixels).all() and coverage['pixels_above_half'] > args.resolution ** 2 * .005, coverage
    # The atlas carries measured donor coverage. Constant warm-black albedo is
    # intentionally unlit; original curve BSDF cannot be exported to glTF.
    linear_albedo = np.array((.012, .008, .006), dtype=np.float32)
    encoded_albedo = np.where(linear_albedo <= .0031308, linear_albedo * 12.92,
                              1.055 * linear_albedo ** (1.0 / 2.4) - .055)
    pixels[:, :3] = encoded_albedo
    pixels[:, 3] = alpha
    # This non-float Blender image stores display-encoded byte values (measured
    # in R1/R2). glTF baseColorTexture is sRGB, so encode intended linear albedo
    # explicitly; metadata alone does not transform the image buffer.
    image.colorspace_settings.name = 'sRGB'
    ImagePixels.write_image_pixels(image, pixels)
    Bake._dilate_image_colour(image)
    image.filepath_raw = str((args.output / 'mpfb-nape-albedo-alpha.png').resolve())
    image.file_format = 'PNG'
    image.save()
    image.pack()
    bake_seconds = time.monotonic() - bake_started
    hair.data.materials.clear()
    for material in original_mats:
        hair.data.materials.append(material)
    material = bpy.data.materials.new('MPFB CC0 nape cards warm black')
    material.use_nodes = True
    material.surface_render_method = 'DITHERED'
    material.use_backface_culling = False
    nodes = material.node_tree.nodes
    principled = next(n for n in nodes if n.type == 'BSDF_PRINCIPLED')
    principled.inputs['Metallic'].default_value = 0
    principled.inputs['Roughness'].default_value = .48
    principled.inputs['IOR'].default_value = 1.46
    color = nodes.new('ShaderNodeTexImage')
    color.image = image
    material.node_tree.links.new(color.outputs['Color'], principled.inputs['Base Color'])
    material.node_tree.links.new(color.outputs['Alpha'], principled.inputs['Alpha'])
    cards.data.materials.clear()
    cards.data.materials.append(material)
    for prop in ('visible_shadow', 'visible_diffuse', 'visible_glossy', 'visible_transmission', 'visible_volume_scatter'):
        setattr(cards, prop, True)
    for obj in scene.objects:
        if obj.name in visibility:
            obj.hide_render = visibility[obj.name]
    hair.hide_render = True
    baseline.hide_render = True
    body.hide_render = False
    # Rigid-head binding is explicit first-stage eligibility. No cloth/physics
    # promise; shoulder/cape contact must still be reviewed in native clips.
    group = cards.vertex_groups.new(name='head')
    group.add(list(range(len(cards.data.vertices))), 1.0, 'REPLACE')
    armature = cards.modifiers.new('Existing Rama head bone', 'ARMATURE')
    armature.object = rig
    cards.parent = rig
    cards.matrix_parent_inverse = rig.matrix_world.inverted()
    cards.matrix_world = Matrix.Identity(4)
    cards['asset_license'] = 'CC0-1.0; Tomas Klecer MPFB donor, YUGA adaptation'
    cards['canonical_promoted'] = False
    # The existing rig is exported only as a compatibility carrier. No action is
    # authored or rest transform changed; the isolated scene reuses runtime clips.
    bpy.ops.object.select_all(action='DESELECT')
    cards.select_set(True)
    rig.select_set(True)
    bpy.context.view_layer.objects.active = cards
    rig.data.pose_position = 'REST'
    glb = args.output / 'mpfb-nape-cards-near.glb'
    bpy.ops.export_scene.gltf(filepath=str(glb), export_format='GLB', use_selection=True,
        export_animations=False, export_apply=False, export_extras=True,
        export_skins=True, export_def_bones=False, export_yup=True)
    master = args.output / 'rama-mpfb-card-candidate.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(master))
    assert mesh_snapshot(body) == protected and mesh_snapshot(baseline) == protected
    assert digest([tuple(v.vector) for v in hair.data.attributes['position'].data]) == guides_before
    assert digest([(b.name, b.parent.name if b.parent else '', [list(row) for row in b.matrix_local]) for b in rig.data.bones]) == rig_before
    assert sha(args.source) == MASTER_SHA and sha(ROOT / 'assets/heroes/rama-hero.glb') == CANONICAL_SHA
    cards.data.calc_loop_triangles()
    report = {
        'schema_version': 1, 'scope': 'Isolated actual MPFB cluster-card bake and head-bound export; no canonical promotion',
        'upstream_commit': 'b1a2dc98776da9d1eea751b159d42cf61778fe2e',
        'source_master_sha256': MASTER_SHA, 'canonical_sha256': CANONICAL_SHA,
        'script_sha256': sha(__file__), 'card_source_sha256': CARD_SHA, 'bake_source_sha256': BAKE_SHA,
        'reused_exact_bake_methods': methods, 'blender': bpy.app.version_string,
        'source_counts': source_counts, 'settings': settings, 'requested_clusters': 72,
        'mesh': {'vertices': len(cards.data.vertices), 'polygons': len(cards.data.polygons),
                 'triangles': len(cards.data.loop_triangles), 'surfaces': len(cards.data.materials),
                 'uv_count': len(uv), 'uv_sha256': digest(uv)},
        'coverage_bake': coverage, 'bake': {'resolution': args.resolution, 'samples': args.samples,
                   'seconds': bake_seconds, 'renderer': 'Cycles CPU two threads; EMIT via pinned ray portal'},
        'binding': {'bone': 'head', 'weight': 1.0, 'bones_in_unchanged_carrier': len(rig.data.bones),
                    'rest_digest': rig_before, 'physics': False},
        'protected_body_crown_topology_uv_exact': True, 'source_guides_exact': True,
        'outputs': [{'path': p.name, 'bytes': p.stat().st_size, 'sha256': sha(p)} for p in (glb, Path(image.filepath_raw), master)],
        'runtime_promoted': False, 'artistic_acceptance': 'pending actual matched views and native motion/contact',
        'elapsed_seconds': time.monotonic() - started,
    }
    (args.output / 'receipt.json').write_text(json.dumps(report, indent=2) + '\n')
    print('MPFB_NATIVE=' + json.dumps(report, separators=(',', ':')))


if __name__ == '__main__':
    main()
