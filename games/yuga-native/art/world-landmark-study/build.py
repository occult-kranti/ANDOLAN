"""Build the YUGA wetland landmark composition from the pinned world kit.

Run with Blender 4.3.2 and use --variant first for the first look, or refined
for the reviewed composition. Blender's Z axis is up; coordinates are metres.
"""
import argparse
import hashlib
import json
import math
import random
import sys
from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
NATIVE = HERE.parents[1]
KIT = NATIVE / "art/reuse-library/yuga-world-elements.blend"
ROCK = HERE / "sources/rock_face_01/rock_face_01_1k.gltf"
HDR = HERE / "sources/the_lost_city_1k.hdr"
COURT = NATIVE / "assets/environment/lanka_courtyard.glb"
HERO = NATIVE / "art/hanuman-hero-finish/models/hanuman-enhanced.glb"
EXPECTED_KIT = "10ee96ea906ca095dbfbc12b15a137a3dc263a77440f332d845a11dbec8616a7"
EXPECTED_ROCK = "96c332c01d173a2431115f3bac29be101fba341e5500e2a08e384f4edd17299e"
EXPECTED_HDR = "53380c24561f972f2a2066f18ecf1d70a474eb715399d18d184c974629c0ca69"
EXPECTED_COURT = "1454e03627e9a7708557f64122cf8f170d0f8365256e69fa7689e94cd3585c33"
EXPECTED_HERO = "6612e710578c2527fc1edb84cd8c2c64936cd7ec2a0b201d4a714eead870273a"
NAMES = (
    "Lanka Shikhara", "Lanka Watchtower", "Temple Sandstone", "Temple Crown",
    "Swamp Shrine", "Rock Island", "Reed Cluster", "Mangrove Roots",
    "Diya Niche", "Lotus Cluster",
)
rng = random.Random(1961)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def collection(name):
    existing = bpy.data.collections.get(name)
    if existing:
        return existing
    item = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(item)
    return item


def move_to(obj, target):
    for parent in list(obj.users_collection):
        parent.objects.unlink(obj)
    target.objects.link(obj)


def point_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def instance(source, target, name, loc, scale, angle=0):
    copy = source.copy()
    copy.data = source.data
    target.objects.link(copy)
    copy.name = name
    copy.location = loc
    copy.scale = scale
    copy.rotation_euler = (0, 0, angle)
    return copy


def box(name, target, location, scale, material):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material)
    move_to(obj, target)
    bevel = obj.modifiers.new("Worn edges", "BEVEL")
    bevel.width = 0.055
    bevel.segments = 2
    bevel.affect = "EDGES"
    obj.modifiers.new("Weighted corner normals", "WEIGHTED_NORMAL")
    return obj


def material(name, color, roughness, metallic=0.0):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1)
    shader.inputs["Roughness"].default_value = roughness
    shader.inputs["Metallic"].default_value = metallic
    return mat


def world_water():
    mat = material("Backwater · shallow teal", (0.037, 0.135, 0.13), 0.2, 0.08)
    tree = mat.node_tree
    nodes = tree.nodes
    links = tree.links
    shader = nodes.get("Principled BSDF")
    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 38
    noise.inputs["Detail"].default_value = 2
    noise.inputs["Roughness"].default_value = 0.6
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.18
    bump.inputs["Distance"].default_value = 0.065
    links.new(noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], shader.inputs["Normal"])
    return mat


def add_sun():
    bpy.ops.object.light_add(type="SUN", location=(-20, -15, 35))
    light = bpy.context.object
    light.name = "Late afternoon sun"
    light.data.energy = 2.5
    light.data.color = (1.0, 0.79, 0.58)
    light.data.angle = math.radians(10)
    light.rotation_euler = (math.radians(28), math.radians(-25), math.radians(-32))
    move_to(light, collection("Lighting and camera"))


def set_scene(variant, width, samples):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.preferences.filepaths.save_version = 0
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = samples
    scene.cycles.use_denoising = bool(getattr(bpy.app.build_options, "openimagedenoise", False))
    scene.cycles.max_bounces = 5
    scene.cycles.diffuse_bounces = 2
    scene.cycles.glossy_bounces = 2
    scene.render.threads_mode = "FIXED"
    scene.render.threads = 2
    scene.render.resolution_x = width
    scene.render.resolution_y = round(width * 9 / 16)
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Medium High Contrast"
    world = bpy.data.worlds.new("Dusk sky")
    scene.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.25, 0.37, 0.43, 1)
    background = world.node_tree.nodes["Background"]
    background.inputs["Strength"].default_value = 0.55
    if variant == "refined":
        env = world.node_tree.nodes.new("ShaderNodeTexEnvironment")
        env.image = bpy.data.images.load(str(HDR))
        env.label = "Poly Haven · The Lost City (CC0)"
        coordinates = world.node_tree.nodes.new("ShaderNodeTexCoord")
        mapping = world.node_tree.nodes.new("ShaderNodeMapping")
        mapping.inputs["Rotation"].default_value[2] = math.radians(145)
        world.node_tree.links.new(coordinates.outputs["Generated"], mapping.inputs["Vector"])
        world.node_tree.links.new(mapping.outputs["Vector"], env.inputs["Vector"])
        world.node_tree.links.new(env.outputs["Color"], background.inputs["Color"])
        background.inputs["Strength"].default_value = 0.7
        # Keep the HDRI as illumination while the camera sees an original sky.
        sky = world.node_tree.nodes.new("ShaderNodeTexSky")
        sky.sky_type = "NISHITA"
        sky.sun_elevation = math.radians(18)
        sky.sun_rotation = math.radians(120)
        sky.sun_disc = False
        sky.air_density = 1.2
        sky.dust_density = 2.0
        camera_sky = world.node_tree.nodes.new("ShaderNodeBackground")
        camera_sky.inputs["Strength"].default_value = .48
        rays = world.node_tree.nodes.new("ShaderNodeLightPath")
        mix = world.node_tree.nodes.new("ShaderNodeMixShader")
        output = world.node_tree.nodes.get("World Output")
        world.node_tree.links.new(sky.outputs["Color"], camera_sky.inputs["Color"])
        world.node_tree.links.new(rays.outputs["Is Camera Ray"], mix.inputs[0])
        world.node_tree.links.new(background.outputs[0], mix.inputs[1])
        world.node_tree.links.new(camera_sky.outputs[0], mix.inputs[2])
        world.node_tree.links.new(mix.outputs[0], output.inputs["Surface"])

    with bpy.data.libraries.load(str(KIT), link=False) as (available, requested):
        missing = set(NAMES) - set(available.collections)
        if missing:
            raise ValueError("Missing world library collections: " + ", ".join(sorted(missing)))
        requested.collections = list(NAMES)
    sources = {}
    for imported in requested.collections:
        objects = [o for o in imported.all_objects if o.type == "MESH"]
        if len(objects) != 1:
            raise ValueError(f"Expected one mesh in {imported.name}")
        sources[imported.name] = objects[0]

    rock_before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(ROCK))
    imported = set(bpy.data.objects) - rock_before
    rock_objects = [o for o in imported if o.type == "MESH"]
    if len(rock_objects) != 1:
        raise ValueError("Expected one Poly Haven rock mesh")
    rock = rock_objects[0]
    move_to(rock, collection("01 · Rocks and terrain"))
    rock.name = "Rock face · source mesh"
    rock.location = (-14, 35, 0)
    rock.scale = (3.1, 2.4, 2.8)
    rock.rotation_euler.z = math.radians(36)

    architecture = collection("02 · Temple and thresholds")
    foreground = collection("03 · Wetlands and plants")
    path = collection("04 · Ghat and causeway")
    terrain = collection("01 · Rocks and terrain")
    wet = world_water()
    ground = material("Ground · dusky sandstone", (0.24, 0.20, 0.13), 0.83)
    paving = bpy.data.materials["Confluence_honey_sandstone"]

    floor = box("Shallow ground", terrain, (0, 8, -0.8), (140, 170, 1.4), ground)
    for mod in list(floor.modifiers):
        floor.modifiers.remove(mod)
    bpy.ops.mesh.primitive_plane_add(size=2, location=(0, 7, 0.02))
    water = bpy.context.object
    water.name = "Wetland surface"
    water.scale = (70, 85, 1)
    water.data.materials.append(wet)
    move_to(water, terrain)

    # The 1 m source units are scaled into the temple's final footprint.
    if variant == "refined":
        instance(sources["Temple Crown"], architecture, "Temple · terraced plinth",
                 (0, 38, .5), (23, 18, 5))
    instance(sources["Temple Sandstone"], architecture, "Temple · foundation",
             (0, 38, 5.5), (20, 15, 12))
    instance(sources["Lanka Shikhara"], architecture, "Temple · landmark shikhara",
             (0, 38, 17.5), (21, 17, 22))
    for side in (-1, 1):
        instance(sources["Lanka Watchtower"], architecture, f"Gate · pavilion {side}",
                 (side * 13, 32, 3.7), (9, 9, 13))
        instance(sources["Swamp Shrine"], architecture, f"Water shrine {side}",
                 (side * 10.5, 15, 0.4), (5, 5, 6))
        instance(sources["Mangrove Roots"], foreground, f"Mangrove {side} rear",
                 (side * 21, 17, 0.15), (7, 7, 7))
        instance(sources["Mangrove Roots"], foreground, f"Mangrove {side} front",
                 (side * 17, -15, 0.12), (6, 6, 7))

    # A continuous ghat ascends through shallow water toward the temple.
    for i in range(29):
        y = -36 + i * 2.35
        t = i / 28
        x = 3.0 * math.sin(t * math.pi * 1.4) * (1 - .32 * t)
        z = 0.20 + 3.4 * max(0, (t - .68) / .32)
        if variant == "refined":
            for column in (-1, 0, 1):
                tile = box(f"Causeway slab {i+1:02} {column}", path,
                           (x + column * 1.68, y, z), (1.64, 2.31, .34), paving)
                tile.rotation_euler.z = math.radians(rng.uniform(-.25, .25))
        else:
            tile = box(f"Causeway slab {i+1:02}", path, (x, y, z), (5.1, 2.32, .34), paving)
            tile.rotation_euler.z = math.radians(rng.uniform(-.5, .5))
        if i % 4 == 1:
            for side in (-1, 1):
                instance(sources["Diya Niche"], path, f"Causeway diya {side} {i}",
                         (x + side * 3.1, y, z + .2), (.55, .55, 1.05))

    # These are instances of the actual PBR rock, sharing mesh and texture data.
    rocks = [
        (14, 35, 0, 3.1, 2.6, 2.8, -15), (-22, 38, 0, 2.8, 2.2, 3.0, 20),
        (22, 38, 0, 2.8, 2.2, 3.0, -18), (0, 49, 1.5, 3.8, 3.5, 3.0, 15),
        (-19, 25, -.7, 2.1, 2.0, 2.1, -15), (19, 25, -.7, 2.1, 2.0, 2.1, 15),
        (-14, 0, -.7, 1.4, 1.2, 1.1, 30), (14, 2, -.7, 1.5, 1.4, 1.5, -23),
        (-16, -20, -.9, 1.3, 1.2, 1.0, -8), (16, -23, -.8, 1.4, 1.2, 1.2, 20),
        (-33, 42, 0, 2.6, 2.1, 4.0, -12), (33, 42, 0, 2.6, 2.1, 4.0, 12),
    ]
    if variant == "refined":
        rocks.extend([(-28, 26, -.8, 1.7, 1.5, 2, 12), (28, 26, -.8, 1.7, 1.5, 2, -12)])
    for i, (x, y, z, sx, sy, sz, angle) in enumerate(rocks):
        instance(rock, terrain, f"Rock face · {i+1:02}", (x, y, z),
                 (sx, sy, sz), math.radians(angle))

    if variant == "refined":
        # Reuse the detailed first-party courtyard as a foreground threshold.
        before = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=str(COURT))
        courtyard_parts = set(bpy.data.objects) - before
        root = bpy.data.objects.new("Lanka courtyard · editable shared threshold", None)
        architecture.objects.link(root)
        root.location = (0, -25, 0.17)
        root.scale = (.30, .30, .30)
        for obj in courtyard_parts:
            if not obj.name.startswith(("COL_", "DECOR_")) or obj.type != "MESH":
                bpy.data.objects.remove(obj, do_unlink=True)
                continue
            obj.parent = root
            move_to(obj, architecture)
        instance(rock, terrain, "Rock face · central foundation", (0, 37, 0),
                 (4.1, 3.0, 3.1), math.radians(6))
        # A known 2.1 m game character gives the camera a visual scale reference.
        before = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=str(HERO))
        hero_parts = set(bpy.data.objects) - before
        hero_group = collection("05 · Character scale reference")
        anchor = bpy.data.objects.new("Hanuman · scale reference", None)
        hero_group.objects.link(anchor)
        anchor.location = (-.6, -29.6, .359)
        anchor.rotation_euler.z = math.pi
        rigs = [o for o in hero_parts if o.type == "ARMATURE"]
        if len(rigs) != 1:
            raise ValueError("Expected one Hanuman armature")
        rig = rigs[0]
        for track in rig.animation_data.nla_tracks:
            track.mute = True
        action = next((a for a in bpy.data.actions if a.name == "idle"), None)
        if action is None:
            action = next(a for a in bpy.data.actions if a.name.startswith("idle_"))
        rig.animation_data.action = action
        scene.frame_set(round(action.frame_range[0]))
        for obj in hero_parts:
            if obj.parent is None:
                obj.parent = anchor
            move_to(obj, hero_group)
            if obj.type == "MESH" and obj.name.startswith("Icosphere"):
                # glTF's bone-display helper is not part of the hero.
                obj.hide_render = True
                obj.hide_set(True)

    for side in (-1, 1):
        for j in range(14):
            y = -28 + j * 4.1 + rng.uniform(-1.0, 1.0)
            x = side * (7.5 + rng.uniform(0.0, 6.5))
            instance(sources["Reed Cluster"], foreground, f"Reeds {side} {j:02}",
                     (x, y, .03), (.9, .9, rng.uniform(1.3, 2.0)),
                     rng.uniform(-math.pi, math.pi))
        for j in range(5):
            y = -20 + j * 8.0 + rng.uniform(-1, 1)
            x = side * (5.3 + rng.uniform(0.0, 3.0))
            instance(sources["Lotus Cluster"], foreground, f"Lotus {side} {j:02}",
                     (x, y, .08), (1.25, 1.25, .22),
                     rng.uniform(-math.pi, math.pi))

    add_sun()
    if variant == "refined":
        bpy.ops.object.light_add(type="AREA", location=(-3, 11, 25))
        fill = bpy.context.object
        fill.name = "Entrance · warm fill"
        fill.data.energy = 7000
        fill.data.shape = "DISK"
        fill.data.size = 22
        fill.data.color = (1, .72, .48)
        point_at(fill, (0, 38, 12))
        move_to(fill, collection("Lighting and camera"))
    camera_position = (-4, -47, 3.4) if variant == "refined" else (-21, -61, 20)
    bpy.ops.object.camera_add(location=camera_position)
    camera = bpy.context.object
    camera.name = "Causeway view"
    camera.data.lens = 24 if variant == "refined" else 38
    camera.data.clip_end = 350
    point_at(camera, (0, 29, 15) if variant == "refined" else (0, 25, 11))
    move_to(camera, collection("Lighting and camera"))
    scene.camera = camera
    return scene


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--variant", choices=("first", "refined"), default="refined")
    parser.add_argument("--output", type=Path, default=HERE)
    parser.add_argument("--width", type=int, default=1280)
    parser.add_argument("--samples", type=int, default=24)
    args = parser.parse_args(args)
    if (sha(KIT) != EXPECTED_KIT or sha(ROCK) != EXPECTED_ROCK
            or sha(HDR) != EXPECTED_HDR or sha(COURT) != EXPECTED_COURT
            or sha(HERO) != EXPECTED_HERO):
        raise ValueError("Pinned source asset has changed")
    args.output.mkdir(parents=True, exist_ok=True)
    scene = set_scene(args.variant, args.width, args.samples)
    bpy.ops.file.pack_all()
    destination = args.output / ("landmark.blend" if args.variant == "refined" else "first-pass.blend")
    bpy.ops.wm.save_as_mainfile(filepath=str(destination), compress=True)
    image = args.output / ("landmark-raw.png" if args.variant == "refined" else "first-pass.png")
    scene.render.filepath = str(image)
    bpy.ops.render.render(write_still=True)
    print(json.dumps({"scene": str(destination), "image": str(image), "variant": args.variant,
                      "source": {"kit": sha(KIT), "rock": sha(ROCK)}, "blender": bpy.app.version_string}))


if __name__ == "__main__":
    main()
