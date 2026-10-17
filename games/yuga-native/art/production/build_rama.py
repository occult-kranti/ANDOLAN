"""Author Rama's first native production art revision from the existing CC0 rig.

blender -b -t 2 --python games/yuga-native/art/production/build_rama.py
Add -- --preview only when the shared render slot has been allocated.

This is original mesh/material authoring, not commercial asset extraction or
an image-to-3D reconstruction. Existing animation curves are preserved exactly.
"""
from pathlib import Path
import sys, json, math, hashlib, struct, time
import bpy, bmesh, numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree

HERE = Path(__file__).resolve().parent
GAME = HERE.parents[1]
ROOT = GAME.parents[1]
PIPELINE = ROOT / 'games/yuga/art/pipeline'
sys.path.insert(0, str(PIPELINE))
from geometry import Sculpt, costume, weapon

SOURCE = Path('/workspace/tooling/yuga-art/output/rama-authored.blend')
OUT = GAME / 'assets/heroes/rama-production.glb'
TEXTURES = HERE / 'textures/rama'
BLEND = Path('/workspace/tooling/yuga-art/output/rama-production.blend')
TAU = math.tau
H = 1.85


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def curve_hashes():
    result = {}
    for action in bpy.data.actions:
        curves = [(fc.data_path, fc.array_index,
                   [(tuple(k.co), tuple(k.handle_left), tuple(k.handle_right), k.interpolation)
                    for k in fc.keyframe_points]) for fc in action.fcurves]
        result[action.name] = hashlib.sha256(json.dumps(curves, sort_keys=True).encode()).hexdigest()
    return result


def image_file(name, rgb, non_color=False):
    size = rgb.shape[0]
    pixels = np.ones((size, size, 4), dtype=np.float32)
    pixels[:, :, :3] = np.clip(rgb, 0, 1)
    img = bpy.data.images.new('Rama ' + name, width=size, height=size)
    if non_color:
        img.colorspace_settings.name = 'Non-Color'
    img.pixels.foreach_set(pixels.ravel())
    path = TEXTURES / (name + '.png')
    img.filepath_raw = str(path)
    img.file_format = 'PNG'
    img.save()
    img.pack()
    return img


def pbr(name, color, metal=0, rough=.5, texture_kind=None):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.diffuse_color = (*color, 1)
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*color, 1)
    bsdf.inputs['Metallic'].default_value = metal
    bsdf.inputs['Roughness'].default_value = rough
    if not texture_kind:
        return mat
    n = 512
    y, x = np.mgrid[0:n, 0:n] / n
    # Deterministic authored weave / pores / engraved waves, no source images.
    weave = np.sin(x * TAU * 128) * np.cos(y * TAU * 128)
    grain = np.sin((x * 197 + y * 149) * TAU) * np.cos((x * 109 - y * 173) * TAU)
    if texture_kind == 'cloth':
        height = .45 + .11 * weave + .035 * grain
        variation = .97 + .025 * weave + .015 * grain
    elif texture_kind == 'gold':
        height = .5 + .13 * np.sin((y * 18 + .3 * np.sin(x * TAU * 4)) * TAU) + .025 * grain
        variation = .97 + .02 * grain
    elif texture_kind == 'hair':
        height = .5 + .16 * np.sin((x * 48 + .15 * np.sin(y * TAU * 3)) * TAU)
        variation = .91 + .07 * np.sin(x * TAU * 48)
    else:
        height = .5 + .025 * grain
        variation = .98 + .02 * grain
    albedo = np.stack([variation * c for c in color], axis=2)
    dy, dx = np.gradient(height)
    normal = np.stack([-dx * .65, -dy * .65, np.ones_like(dx)], axis=2)
    normal /= np.linalg.norm(normal, axis=2)[:, :, None]
    normal = normal * .5 + .5
    roughmap = np.repeat(np.clip(rough + (height - .5) * .14, 0, 1)[:, :, None], 3, axis=2)
    for suffix, rgb, socket, noncolor in [('albedo', albedo, 'Base Color', False),
                                         ('roughness', roughmap, 'Roughness', True),
                                         ('normal', normal, 'Normal', True)]:
        img = image_file(name.lower().replace(' ', '-') + '-' + suffix, rgb, noncolor)
        tex = mat.node_tree.nodes.new('ShaderNodeTexImage'); tex.image = img
        if socket == 'Normal':
            node = mat.node_tree.nodes.new('ShaderNodeNormalMap')
            node.inputs['Strength'].default_value = .45
            mat.node_tree.links.new(tex.outputs['Color'], node.inputs['Color'])
            mat.node_tree.links.new(node.outputs['Normal'], bsdf.inputs[socket])
        else:
            mat.node_tree.links.new(tex.outputs['Color'], bsdf.inputs[socket])
    return mat


def materials():
    return dict(
        skin=pbr('Warm living skin', (.55, .29, .15), rough=.72, texture_kind='skin'),
        cloth=pbr('Cobalt woven silk', (.035, .16, .53), rough=.57, texture_kind='cloth'),
        ivory=pbr('Ivory folded silk', (.88, .79, .59), rough=.64, texture_kind='cloth'),
        gold=pbr('Brushed antique gold', (.78, .46, .12), metal=.88, rough=.29, texture_kind='gold'),
        gem=pbr('Deep sapphire', (.015, .15, .57), metal=.30, rough=.16),
        hair=pbr('Grouped black hair', (.025, .018, .013), rough=.42, texture_kind='hair'),
        eyes=pbr('Warm eye whites', (.78, .73, .63), rough=.25),
        iris=pbr('Amber brown iris', (.14, .055, .018), rough=.29),
        lips=pbr('Natural lip warmth', (.33, .095, .065), rough=.5),
        leather=pbr('Dark bow grip leather', (.055, .025, .014), rough=.7),
    )


def volume(obj, thickness=.003):
    mod = obj.modifiers.new('Woven cloth thickness', 'SOLIDIFY')
    mod.thickness = thickness; mod.offset = 0
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=mod.name)


def embellish(s, point, material, count=9, bone=None):
    """Sparse modeled leaf stitching, restricted to a garment border."""
    for j in range(count):
        v = .09 + .82 * j / max(1, count - 1)
        for sign in (-1, 1):
            points = [point(.09 + sign * .025 * math.sin(math.pi * k / 8),
                            v + (k / 8 - .5) * .025) for k in range(9)]
            s.tube('Sparse leaf embroidery', points, .0016, material, bone, sides=5)


def costume_revision(s, m):
    # Reuse already authored articulated cuffs, sandals and shoulder ornaments.
    before = len(s.objects)
    costume(s, H, dict(id='rama', sex='male', width=1, ivory_skirt=True), m)
    remove_prefixes = ('Tailored woven bodice', 'Gathered loose trousers', 'Sculpted pleated dhoti',
                       'Dhoti embroidered border', 'Brocade overfold', 'Tabard gold piping',
                       'Folded diagonal silk sash', 'Sash woven gold edge', 'Layered silk mantle',
                       'Mantle gold border', 'Mantle scalloped hem')
    for obj in list(s.objects[before:]):
        if obj.name.startswith(remove_prefixes):
            s.objects.remove(obj); bpy.data.objects.remove(obj, do_unlink=True)

    # Loose trousers follow the individual anatomical legs; no rigid tube pants.
    # Native rest-pose hands descend to hip height. Height alone would cover
    # them with ivory cloth: restrict this selector to the actual leg region.
    eligible_lower_leg_faces = []
    omitted_lower_leg_faces = []
    for face in s.body.data.polygons:
        if not .17 < face.center.z < 1.015:
            continue
        totals = {}
        for index in face.vertices:
            for weight in s.body.data.vertices[index].groups:
                name = s.body.vertex_groups[weight.group].name
                totals[name] = totals.get(name, 0) + weight.weight
        dominant = max(totals, key=totals.get)
        if dominant.startswith('lowerleg'):
            eligible_lower_leg_faces.append(face.index)
            if abs(face.center.x) >= .25:
                omitted_lower_leg_faces.append(face.index)
    assert eligible_lower_leg_faces and not omitted_lower_leg_faces, (
        'Trouser selector omitted genuine lower-leg faces', omitted_lower_leg_faces)
    trousers = s.fitted('Gathered ivory trousers', m['ivory'],
                       lambda p: .17 < p.z < 1.015 and abs(p.x) < .25, .022)
    assert not any(g.name.startswith(('finger', 'wrist', 'lowerarm', 'upperarm'))
                   for g in trousers.vertex_groups), 'Trouser selector included hand/arm anatomy'
    for vert in trousers.data.vertices:
        z = vert.co.z
        fold = .004 * math.sin(z * 62 + vert.co.x * 55)
        vert.co.y += fold
    volume(trousers, .002)

    # Draped central dhoti, shaped as overlapping folds rather than a bell skirt.
    def dhoti(u, v):
        width = .235 - .095 * v
        x = (u - .5) * width
        z = 1.045 - .65 * v + .065 * math.cos(u * math.pi) * v
        y = -.165 - .045 * math.sin(math.pi * v) - .022 * math.cos(u * TAU * 4 + v * 2)
        return x, y, z
    volume(s.cloth('Overlapping ivory dhoti folds', dhoti, m['ivory'], rows=38, columns=32), .004)
    for u in (0, 1):
        s.tube('Dhoti narrow woven border', [dhoti(u, j / 40) for j in range(41)], .004, m['gold'])
    s.tube('Ivory dhoti shaped hem', [dhoti(j / 40, 1) for j in range(41)], .004, m['gold'])

    # A fitted diagonal sash exposes real chest anatomy and leaves quiet blue fields.
    def sash(u, v):
        x = .17 - .32 * v + (u - .5) * .115
        z = 1.515 - .465 * v
        y = -.145 - .025 * math.sin(math.pi * v) - .004 * math.cos(u * TAU * 3)
        return x, y, z
    volume(s.cloth('Folded cobalt shoulder sash', sash, m['cloth'], rows=32, columns=16))
    for u in (0, 1):
        s.tube('Restrained sash gold border', [sash(u, j / 32) for j in range(33)], .003, m['gold'])
    embellish(s, lambda u, v: tuple(Vector(sash(u, v)) + Vector((0, -.004, 0))), m['gold'])

    # The two long tails sit beside the legs, with a shorter central back panel.
    # Each tail follows pelvis + its own thigh gradually, avoiding cross-leg weights.
    for side in (-1, 1):
        def tail(u, v, side=side):
            width = .14 + .07 * math.sin(v * math.pi)
            x = side * (.155 + .12 * v) + (u - .5) * width
            y = .115 + .19 * v + .02 * math.cos(u * TAU * 3) * (.3 + v)
            z = 1.49 - (1.02 if side == 1 else .93) * v + .055 * math.sin(u * math.pi) * v
            return x, y, z
        obj = s.cloth('Split cobalt mantle tail ' + str(side), tail, m['cloth'], rows=36, columns=24, bone='spine01')
        obj.vertex_groups.clear()
        groups = {b: obj.vertex_groups.new(name=b) for b in ('spine01', 'spine05', 'upperleg01.' + ('L' if side == 1 else 'R'))}
        for vert in obj.data.vertices:
            v = vert.index // 25 / 36
            upper = max(0, 1 - v * 2)
            thigh = max(0, v - .5) * .25
            for name, w in [('spine01', upper), ('spine05', 1 - upper - thigh),
                            ('upperleg01.' + ('L' if side == 1 else 'R'), thigh)]:
                if w > 0:
                    groups[name].add([vert.index], w, 'REPLACE')
        volume(obj)
        # Border shares the garment's nearest body weights; later join retains skinning.
        for u in (0, 1):
            edge = s.tube('Mantle sewn gold edge', [tail(u, j / 40) for j in range(41)], .004, m['gold'], 'spine05')
            transfer_weights(edge, obj)
        edge = s.tube('Mantle sculpted gold hem', [tail(j / 40, 1) for j in range(41)], .0045, m['gold'], 'spine05')
        transfer_weights(edge, obj)
        # The first in-engine review showed tiny outline medallions reading as
        # puncture holes. Keep this broad cobalt field quiet; only sewn edges
        # remain until a higher-quality embroidered garment is authored.

    def back(u, v):
        return ((u - .5) * (.32 + .04 * v), .125 + .09 * v + .014 * math.cos(u * TAU * 5), 1.48 - .50 * v)
    volume(s.cloth('Short gathered cobalt back mantle', back, m['cloth'], rows=24, columns=28, bone='spine02'))
    # Long shinguards articulate with the lower leg, leaving knees unobstructed.
    for side in ('L', 'R'):
        b = s.rig.data.bones['lowerleg02.' + side]
        center = b.head_local.lerp(b.tail_local, .5)
        s.ellipsoid('Shaped gold shin plate ' + side, center + Vector((0, -.053, .025)),
                    (.044, .020, .12), m['gold'], 'lowerleg02.' + side, 20, 12, ridge=.04)
        for k in (-1, 1):
            s.tube('Shin plate raised leaf', [(center.x + k * .025 * math.sin(j / 16 * math.pi),
                                             center.y - .074, center.z - .07 + j / 16 * .19)
                                            for j in range(17)], .002, m['ivory'], 'lowerleg02.' + side, sides=5)
    return dict(eligibleFaces=len(eligible_lower_leg_faces), omittedFaces=len(omitted_lower_leg_faces),
                selector='height band plus |x|<0.25m on fixed 1.85m Rama anatomy',
                eligibility='dominant aggregated face joint starts with lowerleg')


def transfer_weights(target, source):
    tree = KDTree(len(source.data.vertices))
    for vert in source.data.vertices:
        tree.insert(vert.co, vert.index)
    tree.balance()
    target.vertex_groups.clear()
    groups = {g.index: target.vertex_groups.new(name=g.name) for g in source.vertex_groups}
    for vert in target.data.vertices:
        nearest = source.data.vertices[tree.find(vert.co)[1]]
        for weight in nearest.groups:
            groups[weight.group].add([vert.index], weight.weight, 'REPLACE')


def face_revision(s, m):
    # Smaller seated eyeballs with genuinely modeled almond openings.
    for side in ('L', 'R'):
        eye = s.rig.data.bones['eye.' + side].head_local + Vector((0, 0, -.001))
        s.ellipsoid('Seated eye sclera ' + side, eye, (.019, .022, .018), m['eyes'], 'eye.' + side, 24, 16)
        s.ellipsoid('Warm iris ' + side, eye + Vector((0, -.0217, 0)), (.0058, .0012, .0062), m['iris'], 'eye.' + side, 20, 12)
        s.ellipsoid('Dark pupil ' + side, eye + Vector((0, -.0227, 0)), (.0027, .0006, .0031), m['hair'], 'eye.' + side, 16, 10)
        def eyelid(u, v):
            a = TAU * u
            dx = (.0158 + .010 * v) * math.cos(a)
            dz = (.0048 + .020 * v) * math.sin(a)
            y = eye.y - math.sqrt(max(.00001, .023 ** 2 - dx * dx - dz * dz)) - .0008
            return eye.x + dx, y, eye.z + dz
        s.cloth('Almond eyelid ' + side, eyelid, m['skin'], rows=7, columns=40, wrap=True, bone='head')
        sign = 1 if side == 'L' else -1
        s.tube('Shaped dark brow ' + side, [(eye.x + sign * (j / 20 - .5) * .044,
                                            eye.y - .0255,
                                            eye.z + .018 + .004 * math.sin(j / 20 * math.pi) - .003 * j / 20)
                                           for j in range(21)], .0032, m['hair'], 'head', sides=7,
               taper=lambda t: .3 + .7 * math.sin(math.pi * t))

    # Swept cap plus separate curling locks create an irregular silhouette.
    def cap(u, v):
        a = TAU * u
        p = .03 + v * (1.57 + .09 * math.sin(a) + .05 * math.sin(a * 3))
        ripple = 1 + .015 * math.cos(a * 22 + v * 5)
        return (.100 * math.sin(p) * math.cos(a) * ripple,
                -.028 + .130 * math.sin(p) * math.sin(a) * ripple,
                1.758 + .112 * math.cos(p))
    s.cloth('Swept sculpted hair cap', cap, m['hair'], rows=28, columns=72, wrap=True, bone='head')
    for i in range(20):
        s.tube('Swept individual hair group', [cap(i / 20 + .018 * math.sin(v * math.pi), v) for v in np.linspace(.15, 1, 25)],
               .0032, m['hair'], 'head', sides=7, taper=lambda t: .7 + .3 * math.sin(math.pi * t))
    for side in (-1, 1):
        for k in range(4):
            pts = []
            for j in range(29):
                t = j / 28
                pts.append((side * (.075 + .012 * k + .013 * math.sin(t * TAU * 1.5 + k)),
                            -.015 + .038 * k + .025 * math.sin(t * TAU * 1.25),
                            1.80 - t * (.25 + .025 * k)))
            s.tube('Falling black hair clump', pts, .014 - .001 * k, m['hair'], 'head', sides=10,
                   taper=lambda t: 1 - .85 * t)
        # Short temple locks break the straight cap edge without covering the eyes.
        s.tube('Temple swept lock', [(side * (.062 + .027 * t), -.119 + .055 * t, 1.795 - .11 * t + .01 * math.sin(t * math.pi))
                                    for t in np.linspace(0, 1, 20)], .012, m['hair'], 'head', sides=9,
               taper=lambda t: 1 - .88 * t)
    for j in range(4):
        s.tube('Bound sculpted topknot', [(.026 * math.cos(t * TAU), .035 + .028 * math.sin(t * TAU),
                                         1.878 + j * .010 + .004 * math.sin(t * TAU * 3)) for t in np.linspace(0, 1, 41)],
               .012, m['hair'], 'head', sides=9)
    s.ring('Topknot gold binding', (0, .035, 1.879), (.032, .033), m['gold'], 'head', .0025)
    # Restrained diadem follows the source concept, instead of a tall leaf wall.
    s.ring('Narrow chased diadem', (0, -.033, 1.783), (.103, .139), m['gold'], 'head', .0045, segments=64, wave=.002)
    s.ellipsoid('Diadem lotus setting', (0, -.171, 1.795), (.018, .008, .027), m['gold'], 'head', 16, 12, ridge=.08)
    s.ellipsoid('Diadem sapphire', (0, -.179, 1.795), (.008, .004, .015), m['gem'], 'head', 10, 8)
    for side in (-1, 1):
        s.tube('Diadem swept flourish', [(side * .018, -.173, 1.79), (side * .043, -.167, 1.804),
                                         (side * .067, -.154, 1.792)], .003, m['gold'], 'head')
    s.tube('Ivory forehead tilaka', [(0, -.166, 1.75), (0, -.168, 1.775)], .0025, m['ivory'], 'head')
    # Deliberately subtle lip treatment avoids a floating oversized lip ridge.
    s.tube('Natural lip line', [(j * .002, -.169 + .004 * abs(j) / 10, 1.647 + .001 * math.cos(j * .3))
                               for j in range(-10, 11)], .0009, m['lips'], 'head', sides=5,
           taper=lambda t: .25 + .75 * math.sin(math.pi * t))


def weapon_revision(s, m):
    before = len(s.objects)
    weapon(s, H, dict(weapon='bow'), m)
    # Existing grip frame and bowstring bone are preserved exactly.
    bone = s.rig.data.bones['wrist.R']; origin = bone.head_local; rot = bone.matrix_local.to_3x3()
    def p(x, y, z):
        return origin + rot @ (Vector((z, y, -x)) + Vector((0, .105, .025)))
    s.tube('Leather wrapped bow grip', [p(0, 0, z) for z in np.linspace(-.046, .046, 10)], .022,
           m['leather'], 'wrist.R', sides=12)
    for z in np.linspace(-.04, .04, 7):
        s.tube('Bow grip fine gold wrap', [p(.023 * math.cos(t * TAU), .023 * math.sin(t * TAU), z)
                                          for t in np.linspace(0, 1, 25)], .0017, m['gold'], 'wrist.R', sides=5)
    # A genuine back quiver and feathered shafts read above the shoulder.
    base = Vector((-.15, .135, 1.21)); top = Vector((-.21, .16, 1.64))
    s.tube('Cobalt leather quiver', [base.lerp(top, t) for t in np.linspace(0, 1, 15)], .050, m['cloth'], 'spine01', sides=20)
    direction = (top - base).normalized()
    a = direction.cross(Vector((0, 1, 0))).normalized(); b = direction.cross(a)
    for t in (.04, .9, 1):
        center = base.lerp(top, t)
        s.tube('Quiver gold mouth ring', [center + .052 * (a * math.cos(j * TAU / 40) + b * math.sin(j * TAU / 40)) for j in range(41)],
               .004, m['gold'], 'spine01', sides=7)
    for k in range(5):
        end = top + direction * (.16 + .018 * (k % 3)) + a * ((k - 2) * .016)
        start = end - direction * .28
        s.tube('Arrow shaft ' + str(k), [start, end], .0023, m['gold'], 'spine01', sides=7)
        for sign in (-1, 1):
            vertices = [end - direction * .015, end - direction * .085,
                        end - direction * .07 + a * .014 * sign, end - direction * .023 + a * .012 * sign]
            feather = s.mesh('Ivory arrow feather', vertices, [(0, 1, 2, 3)], m['ivory'], 'spine01')
            volume(feather, .0008)


def verify_weights(objects, rig):
    count = 0
    for obj in objects:
        assert obj.type == 'MESH'
        valid = {g.index for g in obj.vertex_groups if g.name in rig.data.bones}
        for v in obj.data.vertices:
            weights = [g.weight for g in v.groups if g.group in valid and g.weight > 0]
            assert weights and len(weights) <= 4, (obj.name, v.index, weights)
            assert abs(sum(weights) - 1) < .001, (obj.name, v.index, sum(weights))
            assert all(math.isfinite(c) for c in v.co)
            count += 1
    return count


def sample_poses(body, rig):
    result = []
    for action in sorted(bpy.data.actions, key=lambda a: a.name):
        rig.animation_data.action = action
        for fraction in (0, .25, .5, .75, 1):
            frame = action.frame_range[0] + fraction * (action.frame_range[1] - action.frame_range[0])
            bpy.context.scene.frame_set(int(frame), subframe=frame % 1)
            bpy.context.view_layer.update()
            evaluated = body.evaluated_get(bpy.context.evaluated_depsgraph_get())
            mesh = evaluated.to_mesh()
            coords = np.array([tuple(v.co) for v in mesh.vertices])
            assert np.isfinite(coords).all()
            minimum = coords.min(axis=0); maximum = coords.max(axis=0)
            assert np.max(maximum - minimum) < 4
            result.append(dict(clip=action.name, frame=round(frame, 4), fraction=fraction,
                               minimum=minimum.tolist(), maximum=maximum.tolist()))
            evaluated.to_mesh_clear()
    rig.animation_data.action = bpy.data.actions['idle']; bpy.context.scene.frame_set(1)
    return result


def preview(rig):
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'; scene.cycles.device = 'CPU'; scene.cycles.samples = 20
    scene.cycles.use_denoising = False
    scene.render.resolution_x = 900; scene.render.resolution_y = 1080; scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'; scene.view_settings.view_transform = 'AgX'
    scene.world.color = (.06, .07, .10)
    ground = pbr('Studio ground', (.045, .052, .065), rough=.8)
    bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, -.022)); bpy.context.object.data.materials.append(ground)
    for pos, power, size in [((3, -4, 4), 650, 4), ((-3, -2, 2), 350, 3), ((0, 3, 3), 850, 3)]:
        data = bpy.data.lights.new('Studio softbox', 'AREA'); data.energy = power; data.shape = 'DISK'; data.size = size
        obj = bpy.data.objects.new('Studio softbox', data); scene.collection.objects.link(obj); obj.location = pos
        obj.rotation_euler = (Vector((0, 0, 1.1)) - obj.location).to_track_quat('-Z', 'Y').to_euler()
    data = bpy.data.cameras.new('Actual authored model'); camera = bpy.data.objects.new('Actual authored model', data)
    scene.collection.objects.link(camera); scene.camera = camera; data.type = 'ORTHO'; data.ortho_scale = 2.6
    for name, pos, clip, frame in [('front', (2.8, -5.4, 2.3), 'idle', 1),
                                    ('rear', (-2.8, 5.4, 2.3), 'idle', 1),
                                    ('stride', (2.8, -5.4, 2.3), 'run', 7)]:
        rig.animation_data.action = bpy.data.actions[clip]; scene.frame_set(frame)
        camera.location = pos; camera.rotation_euler = (Vector((0, 0, 1)) - camera.location).to_track_quat('-Z', 'Y').to_euler()
        scene.render.filepath = str(HERE / ('rama-production-' + name + '.png'))
        bpy.ops.render.render(write_still=True)


def main():
    if '--preview-only' in sys.argv:
        bpy.ops.wm.open_mainfile(filepath=str(BLEND))
        preview(bpy.data.objects['YugaHeroRig'])
        return
    started = time.monotonic(); TEXTURES.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    before_curves = curve_hashes()
    assert set(before_curves) == {'idle', 'run', 'fire', 'cast', 'cast1', 'cast2', 'cast3', 'jump', 'defeat'}
    rig = bpy.data.objects['YugaHeroRig']; assert len(rig.data.bones) == 164
    for bone in rig.pose.bones:
        bone.matrix_basis.identity()
    rig.data.pose_position = 'REST'
    source_body = bpy.data.objects['ValidationAnatomy']
    body = source_body.copy(); body.data = source_body.data.copy(); body.name = 'rama_production_skinned_hero'
    bpy.context.collection.objects.link(body); body.hide_render = False; body.hide_set(False)
    # Preserve the native facial topology. Gentle thorax shaping only, no rig edits.
    for v in body.data.vertices:
        z = v.co.z
        if 1.08 < z < 1.50 and abs(v.co.x) < .25:
            chest = math.sin((z - 1.08) / .42 * math.pi)
            v.co.x *= 1 + .035 * chest
            if v.co.y < 0:
                v.co.y -= .005 * chest
    body.data.update()
    weights = [[(body.vertex_groups[w.group].name, w.weight) for w in v.groups if w.weight > 0]
               for v in body.data.vertices]
    tree = KDTree(len(body.data.vertices))
    for v in body.data.vertices: tree.insert(v.co, v.index)
    tree.balance()
    for obj in list(bpy.data.objects):
        if obj not in (body, rig): bpy.data.objects.remove(obj, do_unlink=True)
    m = materials(); body.data.materials.clear(); body.data.materials.append(m['skin'])
    for polygon in body.data.polygons: polygon.material_index = 0; polygon.use_smooth = True
    sculpt = Sculpt(rig, body, weights, tree)
    leg_coverage = costume_revision(sculpt, m)
    face_revision(sculpt, m); weapon_revision(sculpt, m)
    # Remove anatomy fully covered by fitted trousers; torso/arms remain real skin.
    hand_groups = {g.index for g in body.vertex_groups if g.name.startswith(('finger', 'wrist'))}
    hands_before = sum(any(g.group in hand_groups and g.weight > .001 for g in v.groups)
                       for v in body.data.vertices)
    edit = bmesh.new(); edit.from_mesh(body.data)
    bmesh.ops.delete(edit, geom=[f for f in edit.faces
                               if .18 < f.calc_center_median().z < 1.0
                               and abs(f.calc_center_median().x) < .25], context='FACES')
    bmesh.ops.delete(edit, geom=[v for v in edit.verts if not v.link_faces], context='VERTS')
    edit.to_mesh(body.data); edit.free(); body.data.update()
    hands_after = sum(any(g.group in hand_groups and g.weight > .001 for g in v.groups)
                      for v in body.data.vertices)
    assert hands_before > 0 and hands_after == hands_before, 'Covered-anatomy deletion removed hand vertices'
    original_object_count = len(sculpt.objects)
    weighted_vertices = verify_weights(sculpt.objects, rig)
    bpy.ops.object.select_all(action='DESELECT')
    for obj in sculpt.objects: obj.select_set(True)
    bpy.context.view_layer.objects.active = body; bpy.ops.object.join()
    for mod in list(body.modifiers)[1:]: body.modifiers.remove(mod)
    # Tube end caps are n-gons. Explicit triangulation is required before glTF
    # tangent generation; retaining n-gons silently drops normal-map tangents.
    triangulate = body.modifiers.new('Export tangent triangulation', 'TRIANGULATE')
    bpy.ops.object.modifier_apply(modifier=triangulate.name)
    rig.data.pose_position = 'POSE'
    poses = sample_poses(body, rig)
    assert curve_hashes() == before_curves, 'Existing animation curves changed'
    bpy.ops.object.select_all(action='DESELECT'); body.select_set(True); rig.select_set(True)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.export_scene.gltf(filepath=str(OUT), export_format='GLB', use_selection=True,
                             export_animations=True, export_animation_mode='ACTIONS', export_force_sampling=True,
                             export_frame_range=False, export_skins=True, export_all_influences=False,
                             export_yup=True, export_tangents=True, export_image_format='AUTO')
    data = OUT.read_bytes(); size, kind = struct.unpack_from('<II', data, 12); doc = json.loads(data[20:20 + size])
    primitives = [p for mesh in doc['meshes'] for p in mesh['primitives']]
    clips = sorted(a['name'] for a in doc.get('animations', []))
    assert clips == sorted(before_curves), clips
    assert all(len(skin['joints']) == 164 for skin in doc['skins'])
    assert len(data) < 25 * 1024 * 1024
    assert all('TANGENT' in p['attributes'] for p in primitives)
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
    metadata = dict(schema=1, asset='Original Rama native production revision',
        scope='Incremental authored hero art; not target concept likeness or commercial-game parity.',
        output=str(OUT.relative_to(ROOT)), bytes=len(data), sha256=sha(OUT), blender=bpy.app.version_string,
        sourceBlend=str(SOURCE), sourceBlendSha256=sha(SOURCE), generator=str(Path(__file__).relative_to(ROOT)),
        generatorSha256=sha(__file__), sourcePipelineHashes={p.name:sha(p) for p in [PIPELINE/'geometry.py', PIPELINE/'anatomy.py']},
        referenceImageHashes={str(p.relative_to(ROOT)):sha(p) for p in [ROOT/'games/yuga/art/references/rama-hanuman-sita.png', ROOT/'games/yuga/art/production-concepts/priority-model-direction.png']},
        sourceAnatomyLicense='CC0 MakeHuman data; original costume, hair, weapons and animation code',
        generatedTextureLicense='CC0-1.0 original mathematical texture fields',
        textureFiles=[dict(file=str(p.relative_to(ROOT)), sha256=sha(p), bytes=p.stat().st_size) for p in sorted(TEXTURES.glob('*.png'))],
        materials=len(doc['materials']), originalAuthoredMeshPieces=original_object_count,
        meshCount=len(doc['meshes']), vertices=sum(doc['accessors'][p['attributes']['POSITION']]['count'] for p in primitives),
        triangles=sum(doc['accessors'][p['indices']]['count']//3 for p in primitives),
        boneCount=164, animationClips=clips, preservedAnimationCurveHashes=before_curves,
        handAnatomyVerticesPreserved=hands_after, trousersExcludeHandArmGroups=True,
        lowerLegFaceCoverage=leg_coverage,
        verifiedWeightedVertices=weighted_vertices, poseSamples=poses, units='metres', up='+Y', front='+Z',
        buildSeconds=round(time.monotonic()-started, 2),
        limitations=['No facial blendshapes, hair strands, cloth simulation or LODs.',
                     'Pose samples prove finite bounded deformation, not exhaustive clipping or anatomy quality.',
                     'The inherited animation motions are unchanged; no commercial animations were extracted.',
                     'Production naming identifies this development track, not a declaration of finished art.'])
    (HERE/'rama-production.provenance.json').write_text(json.dumps(metadata, indent=2)+'\n')
    print('RAMA_PRODUCTION', json.dumps({k:metadata[k] for k in ['bytes','sha256','vertices','triangles','boneCount','animationClips','buildSeconds']}), flush=True)
    if '--preview' in sys.argv: preview(rig)


if __name__ == '__main__': main()
