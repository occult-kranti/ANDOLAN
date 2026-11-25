"""Assemble an editable Blender camera and NLA shot sequence from a production GLB and shots.json.

blender -b -t 3 -P blender_scene.py -- --hero rama --model /path/rama-near.glb --save /tmp/rama.blend
Optional --render /tmp/rama- frames a lossless PNG sequence with Blender EEVEE.
"""

import argparse
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
NATIVE = HERE.parents[3]


def import_glb(path):
    prior = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(path.resolve()))
    return set(bpy.data.objects) - prior


def studio_light(scene, name, pos, energy, tint, size, target=(0, 0, 1)):
    lamp = bpy.data.lights.new(name, "AREA")
    lamp.energy, lamp.color, lamp.shape, lamp.size = energy, tint, "DISK", size
    source = bpy.data.objects.new(name, lamp)
    scene.collection.objects.link(source)
    source.location = pos
    source.rotation_euler = (Vector(target) - source.location).to_track_quat("-Z", "Y").to_euler()


def effect_material(tint):
    rgb = [int(tint[i : i + 2], 16) / 255 for i in (1, 3, 5)]
    material = bpy.data.materials.new("Ability light")
    material.diffuse_color = (*rgb, 1)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    emission = nodes.new("ShaderNodeEmission")
    emission.inputs["Color"].default_value = (*rgb, 1)
    emission.inputs["Strength"].default_value = 1.8
    material.node_tree.links.new(emission.outputs[0], nodes.get("Material Output").inputs["Surface"])
    return material


def ring_mesh(material):
    vertices, faces = [], []
    for i in range(64):
        angle = i * math.tau / 64
        for radius in (0.987, 1.013):
            vertices.append((radius * math.cos(angle), radius * math.sin(angle), 0))
        a, b = i * 2, (i * 2 + 2) % 128
        faces.append((a, a + 1, b + 1, b))
    mesh = bpy.data.meshes.new("Shared ring section")
    mesh.from_pydata(vertices, [], faces)
    mesh.materials.append(material)
    return mesh


def visibility(obj, frame, visible):
    for name in ("hide_render", "hide_viewport"):
        setattr(obj, name, not visible)
        obj.keyframe_insert(data_path=name, frame=frame)


def motion_effects(scene, sequence, arm, hero):
    collection = bpy.data.collections.new("Presentation VFX · editable")
    scene.collection.children.link(collection)
    material = effect_material(hero["accent"])
    ring = ring_mesh(material)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=6)
    template = bpy.context.object
    shaft = template.data
    shaft.materials.append(material)
    bpy.data.objects.remove(template, do_unlink=True)
    onsets = {
        "gada": 0.26,
        "breath": 0.5,
        "vault": 0.68,
        "tail": 0.43,
        "pulse": 0.66,
        "ward": 0.06,
        "crescent": 0.30,
        "threefold": 0.37,
        "coil": 0.32,
        "tandava": 0.66,
        "chakra": 0.25,
        "star": 0.28,
        "refrain": 0.29,
        "canopy": 0.36,
    }
    for shot, first, last in sequence:
        kind = shot.get("effect")
        if not kind:
            continue
        start = first + round((last - first) * onsets.get(kind, 0))
        scene.frame_set(start)
        bone_name = "bowstring" if kind in ("arrow", "volley") else "wrist.R"
        wrist = arm.pose.bones.get(bone_name) or arm.pose.bones.get("wrist.R")
        source = arm.matrix_world @ wrist.head if wrist else Vector((0, 0, 1.2))
        darts = kind in ("arrow", "volley")
        launched = kind in ("star", "chakra", "crescent")
        count = 5 if kind == "volley" else (1 if darts or launched else 2)
        for index in range(count):
            obj = bpy.data.objects.new(shot["label"] + " · " + str(index + 1), shaft if darts else ring)
            collection.objects.link(obj)
            begin = min(last - 1, start + index)
            visibility(obj, 0, False)
            visibility(obj, begin, True)
            visibility(obj, last + 1, False)
            obj["presentation_effect"] = kind
            for step in range(5):
                t = step / 4
                if darts:
                    spread = (index - (count - 1) / 2) * 0.11
                    obj.location = source + Vector(
                        (math.sin(spread) * t * 3.8, -math.cos(spread) * t * 3.8, 0.02)
                    )
                    obj.rotation_euler.z = spread
                    obj.scale = (0.013, 0.36, 0.013)
                elif launched:
                    reach = (math.sin(t * math.pi) if kind == "star" else t) * 2.2
                    obj.location = source + Vector((0.15 * reach, -reach, math.sin(t * math.pi) * 0.16))
                    obj.rotation_euler = (math.radians(54 + t * 25), 0, t * math.tau)
                    obj.scale = (0.12 if kind == "crescent" else 0.2,) * 3
                else:
                    elevated = kind in ("breath", "coil", "canopy", "refrain")
                    level = (
                        1.90 + 0.26 * t
                        if kind == "canopy"
                        else (
                            1.15 + 0.04 * index
                            if kind == "refrain"
                            else 0.15 + t if elevated else 0.025 + 0.005 * index
                        )
                    )
                    obj.location = (0, -1.65 if kind == "pulse" else (-0.68 if kind == "gada" else 0), level)
                    obj.rotation_euler.x = math.radians(65) if kind == "refrain" else 0
                    radius = 0.2 + t * (0.65 if elevated else 1.22)
                    obj.scale = (radius, radius, radius)
                at = begin + round((last - begin) * t)
                for prop in ("location", "rotation_euler", "scale"):
                    obj.keyframe_insert(data_path=prop, frame=at)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hero", required=True)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--save", type=Path, required=True)
    parser.add_argument("--render", type=Path)
    parser.add_argument("--threads", type=int, default=3)
    options = parser.parse_args(sys.argv[sys.argv.index("--") + 1 :])
    spec = json.loads((HERE / "shots.json").read_text())
    hero = spec["heroes"][options.hero]
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.fps = spec["fps"]
    scene.render.resolution_x, scene.render.resolution_y = spec["width"], spec["height"]
    scene.render.resolution_percentage = 100
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.eevee.taa_render_samples = 12
    scene.render.threads_mode, scene.render.threads = "FIXED", options.threads
    scene.render.use_persistent_data = True
    scene.view_settings.view_transform = "AgX"

    actor = import_glb(options.model)
    arm = next(o for o in actor if o.type == "ARMATURE")
    anim = arm.animation_data
    actions = {t.name: t.strips[0].action for t in anim.nla_tracks if t.strips}
    for action in actions.values():
        action.use_fake_user = True
    anim.action = None
    for original in list(anim.nla_tracks):
        anim.nla_tracks.remove(original)
    anim.use_nla = True
    timeline = anim.nla_tracks.new()
    timeline.name = hero["title"] + " · motion reference"
    stage = import_glb(NATIVE / "assets/environment/lanka_courtyard.glb")
    courtyard = bpy.data.objects.new("Lanka courtyard · motion stage", None)
    scene.collection.objects.link(courtyard)
    for obj in stage:
        if not obj.parent:
            obj.parent = courtyard
    courtyard.scale = (0.53,) * 3

    scene.world = bpy.data.worlds.new("Dusk")
    scene.world.use_nodes = True
    scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.10, 0.16, 0.19, 1)
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.7
    studio_light(scene, "Warm key", (2.4, -4.1, 4.8), 575, (1, 0.79, 0.60), 2.8)
    studio_light(scene, "Cool bounce", (-3, -1.8, 2.6), 320, (0.56, 0.77, 1), 3.1)
    studio_light(scene, "Gold edge", (0.2, 3, 3.8), 730, (1, 0.72, 0.45), 2.3)

    cam = bpy.data.objects.new("Portrait and action lens", bpy.data.cameras.new("Portrait lens"))
    scene.collection.objects.link(cam)
    cam.data.sensor_fit = "VERTICAL"
    cam.data.lens = cam.data.sensor_height / (2 * math.tan(math.radians(15)))
    scene.camera = cam
    first = 1
    sequence = []
    for shot in hero["shots"]:
        clip = shot["clip"]
        if clip not in actions:
            raise ValueError(f"Missing {clip} on {arm.name}. Found {list(actions)}")
        action = actions[clip]
        last = first + shot["frames"] - 1
        strip = timeline.strips.new(shot["label"], first, action)
        source_first, source_last = action.frame_range
        begin, end = shot.get("range", [0, 0.999])
        strip.action_frame_start = source_first + (source_last - source_first) * begin
        strip.action_frame_end = source_first + (source_last - source_first) * end
        strip.scale = (last - first) / (strip.action_frame_end - strip.action_frame_start)
        strip.extrapolation = "NOTHING"
        scene.timeline_markers.new(shot["label"], frame=first)
        sequence.append((shot, first, last))
        for index in range(shot["frames"]):
            t = index / (shot["frames"] - 1)
            t = t * t * (3 - 2 * t)
            az = math.radians(shot["angle"][0] + (shot["angle"][1] - shot["angle"][0]) * t)
            cam.location = (
                math.sin(az) * shot["distance"],
                -math.cos(az) * shot["distance"],
                1.29 + 0.16 * math.cos(az),
            )
            cam.rotation_euler = (
                (Vector((0, 0, shot["height"])) - cam.location).to_track_quat("-Z", "Y").to_euler()
            )
            cam.keyframe_insert(data_path="location", frame=first + index)
            cam.keyframe_insert(data_path="rotation_euler", frame=first + index)
        first = last + 1
    scene.frame_end = first - 1
    motion_effects(scene, sequence, arm, hero)
    scene.frame_set(1)
    options.save.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(options.save.resolve()), compress=True)
    if options.render:
        options.render.parent.mkdir(parents=True, exist_ok=True)
        scene.render.image_settings.file_format = "PNG"
        scene.render.filepath = str(options.render.resolve())
        bpy.ops.render.render(animation=True)


if __name__ == "__main__":
    main()
