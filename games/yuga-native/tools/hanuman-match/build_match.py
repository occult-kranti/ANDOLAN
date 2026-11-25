"""Rebuild the Hanuman keyframe from the packed R5 rig and editable Blender stages."""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import math
import sys
from pathlib import Path

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Matrix, Vector


TOOLS = Path(__file__).resolve().parent
ART = TOOLS.parents[1] / "art" / "hanuman"
STUDIO = {"Granite display plinth", "Plane", "Key · warm softbox", "Fill · pale teal",
          "Rim · sky edge", "Eyes · soft bounce", "Asset review camera"}
HERO_STAGES = ("character", "body_detail", "extremities", "wardrobe")
R5_HASH = "b27582783f7a68f35225cd0545e7e31e3c09762c736da1e6a689cabaa400e589"
REFERENCE_HASH = "ec2b8360cf22bc75b5d38b0f57a8c33f42d3837dd5fe4f9e497bc4699cab561b"


def arguments():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", type=Path, default=TOOLS / "reference-profile.json")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--width", type=int, default=960)
    parser.add_argument("--samples", type=int, default=36)
    parser.add_argument("--stages", nargs="*", choices=(*HERO_STAGES, "textile", "hand_pose", "court"),
                        default=[*HERO_STAGES, "textile", "hand_pose", "court"])
    parser.add_argument("--build-only", action="store_true")
    return parser.parse_args(sys.argv[sys.argv.index("--") + 1:])


def sha256(path):
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def update():
    bpy.context.view_layer.update()


def select_shot(rig, scene):
    scene.frame_set(1)
    update()
    pose = {bone.name: bone.matrix_basis.copy() for bone in rig.pose.bones}
    # Keep the original action datablocks and isolate the hero shot from playback.
    for action in bpy.data.actions:
        action.use_fake_user = True
    rig.animation_data.action = None
    for track in rig.animation_data.nla_tracks:
        track.mute = True
    for name, basis in pose.items():
        rig.pose.bones[name].matrix_basis = basis
    update()


def turn_about_head(bone, rotation):
    matrix = bone.matrix.copy()
    matrix = rotation.to_4x4() @ matrix
    matrix.translation = bone.head[:]
    bone.matrix = matrix
    update()


def rotate(bone, degrees, axis):
    turn_about_head(bone, Matrix.Rotation(math.radians(degrees), 3, axis))


def aim_joint(bone, existing, desired):
    turn_about_head(bone, existing.rotation_difference(desired).to_matrix())


def solve_limb(bones, start, middle, end, target, pole):
    shoulder, joint, tip = (bones[name] for name in (start, middle, end))
    origin = shoulder.head.copy()
    v1 = joint.head - origin
    v2 = tip.head - joint.head
    direction = (target - origin).normalized()
    distance = min(max((target - origin).length, abs(v1.length - v2.length) + 0.001),
                   v1.length + v2.length - 0.001)
    along = (v1.length_squared + distance * distance - v2.length_squared) / (2 * distance)
    outward = (pole - direction * pole.dot(direction)).normalized()
    bend = math.sqrt(max(0, v1.length_squared - along * along))
    aim_joint(shoulder, v1, direction * along + outward * bend)
    aim_joint(joint, tip.head - joint.head, origin + distance * direction - joint.head)


def arm(bones, side, target, pole):
    solve_limb(bones, f"upperarm01.{side}", f"lowerarm01.{side}", f"wrist.{side}",
               Vector(target), Vector(pole))


def apply_pose(rig, profile):
    bones = rig.pose.bones
    config = profile["pose"]
    root = bones["root"]
    root_matrix = root.matrix.copy()
    root_matrix.translation.z += config["root_height_change_m"]
    root.matrix = root_matrix
    update()
    rotate(bones["spine01"], config["chest_yaw_degrees"], "Z")
    rotate(bones["head"], config["head_yaw_degrees"], "Z")
    rotate(bones["head"], config["head_tilt_degrees"], "X")
    for side in ("R", "L"):
        stance = Vector(config["ankles"][side])
        solve_limb(bones, f"upperleg01.{side}", f"lowerleg01.{side}", f"foot.{side}",
                   stance, Vector(config["leg_pole"]))
        foot = bones[f"foot.{side}"]
        sole = Matrix.Rotation(math.radians(config["foot_yaw_degrees"][side]), 4, "Z")
        foot_matrix = sole @ foot.bone.matrix_local
        foot_matrix.translation = foot.head[:]
        foot.matrix = foot_matrix
        update()

    arm(bones, "L", config["left_wrist"], config["left_elbow_pole"])
    left = bones["wrist.L"]
    aim_joint(left, left.tail - left.head, Vector((-0.52, -0.40, -0.71)))
    rotate(left, -12, "Y")
    if not profile.get("wardrobe_enabled"):
        return

    grip = Vector(config["mace_grip"])
    offset = Vector(config["mace_palm_bone_offset"])
    axis = Vector(config["mace_axis"]).normalized()
    wrist = bones["wrist.R"]
    wrist_target = grip + Vector((-0.024, 0.028, -0.102))
    original = wrist.matrix.to_quaternion()
    aim = original @ Vector((1, 0, 0))
    orient = aim.rotation_difference(axis) @ original
    orientation = Matrix.Rotation(math.radians(config["mace_roll_degrees"]), 3, axis)
    orientation = orientation.to_quaternion() @ orient
    for _ in range(3):
        arm(bones, "R", wrist_target, config["right_elbow_pole"])
        matrix = orientation.to_matrix().to_4x4()
        matrix.translation = wrist.head[:]
        wrist.matrix = matrix
        update()
        wrist_target += grip - wrist.matrix @ offset

    # The wrist-local positions are shared by the wardrobe model and actual shot measurements.
    rig["hanuman_match_grip_error_m"] = (grip - wrist.matrix @ offset).length


def pointed_object(data, name, location, target):
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    obj.location = location
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()
    return obj


def configure_scene(scene, profile, args):
    for name in STUDIO:
        obj = scene.objects.get(name)
        if obj:
            obj.hide_render = True
            obj.hide_set(True)

    config = profile["camera"]
    data = bpy.data.cameras.new("Hanuman reference camera")
    data.lens = config["lens_mm"]
    data.shift_y = config.get("shift_y", 0)
    data.clip_end = 180
    data.dof.use_dof = True
    data.dof.focus_distance = config["focus_m"]
    data.dof.aperture_fstop = config["aperture"]
    scene.camera = pointed_object(data, data.name, config["location"], config["target"])

    scene.world = bpy.data.worlds.new("Temple court dusk")
    scene.world.use_nodes = True
    background = scene.world.node_tree.nodes.get("Background")
    background.inputs["Color"].default_value = (*profile["light"]["world"]["color"], 1)
    background.inputs["Strength"].default_value = profile["light"]["world"]["strength"]
    for area in profile["light"]["areas"]:
        data = bpy.data.lights.new(area["name"], type="AREA")
        data.energy, data.size, data.color = area["power_w"], area["size_m"], area["color"]
        if "height_m" in area:
            data.shape = "RECTANGLE"
            data.size_y = area["height_m"]
        data.spread = math.radians(area.get("spread_degrees", 180))
        pointed_object(data, data.name, area["location"], area["target"])

    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = args.samples
    scene.cycles.adaptive_threshold = 0.045
    # Debian Blender lacks built-in OIDN. Preserve raw output for portable external denoising.
    scene.cycles.use_denoising = False
    scene.cycles.max_bounces = 8
    scene.cycles.volume_bounces = 1
    scene.render.threads_mode = "AUTO"
    scene.render.resolution_x = args.width
    scene.render.resolution_y = args.width * 3 // 4
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.film_transparent = False
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.view_settings.exposure = 0.0
    scene.name = "Hanuman | Temple Court Keyframe"
    # Available for manual multilayer work in the saved scene.
    scene.view_layers[0].use_pass_z = True
    scene.view_layers[0].use_pass_normal = True
    scene.view_layers[0].use_pass_diffuse_color = True
    update()


def rounded(coords):
    return [round(component, 5) for component in coords]


def measurements(scene, rig, profile):
    config = profile["pose"]
    points = {name: rig.pose.bones[name].head.copy()
              for name in ("head", "foot.R", "foot.L", "lowerarm01.R", "lowerarm01.L", "wrist.L")}
    wrist = rig.pose.bones["wrist.R"]
    grip_offset = Vector(config["mace_palm_bone_offset"])
    if profile.get("wardrobe_enabled"):
        points["mace_grip"] = wrist.matrix @ grip_offset
        points["mace_bulb"] = wrist.matrix @ (grip_offset + Vector((
            profile.get("wardrobe", {}).get("mace_head_center_m", 0.632), 0, 0)))
    results = {}
    for name, xyz in points.items():
        position = world_to_camera_view(scene, scene.camera, xyz)
        results[name] = {"world_m": rounded(xyz), "image_uv": rounded((position.x, 1 - position.y))}
    return results


def main():
    args = arguments()
    if args.width < 160 or args.width % 4 or args.samples < 1:
        raise ValueError("Use a width divisible by four (at least 160) and positive samples")
    source = Path(bpy.data.filepath)
    if sha256(source) != R5_HASH:
        raise ValueError("Open the pinned R5 Hanuman blend before running this builder")
    profile = json.loads(args.profile.read_text())
    reference = ART / profile["reference"]
    if sha256(reference) != REFERENCE_HASH:
        raise ValueError("Hanuman reference SHA changed")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    profile["wardrobe_enabled"] = "wardrobe" in args.stages
    if texture := profile.get("wardrobe", {}).get("cloth_texture"):
        profile["wardrobe"]["cloth_texture"] = str(ART / texture)

    if "textile" in args.stages and not profile["wardrobe_enabled"]:
        raise ValueError("The textile stage requires the wardrobe stage")
    scene = bpy.context.scene
    rig = scene.objects["YugaHeroRig"]
    select_shot(rig, scene)
    configure_scene(scene, profile, args)
    sys.path.insert(0, str(TOOLS))
    sys.dont_write_bytecode = True
    reports = {}
    rig.data.pose_position = "REST"
    update()
    for stage in HERO_STAGES:
        if stage in args.stages:
            reports[stage] = importlib.import_module(stage).apply(scene, profile)
    if "textile" in args.stages:
        reports["textile"] = importlib.import_module("textile").apply(scene, profile)
    rig.data.pose_position = "POSE"
    update()
    apply_pose(rig, profile)
    if "hand_pose" in args.stages:
        reports["hand_pose"] = importlib.import_module("hand_pose").apply(rig, profile)
    if "court" in args.stages:
        reports["court"] = importlib.import_module("court").apply(scene, profile)
    update()
    scene.render.filepath = "//hanuman-keyframe.png"
    scene["hanuman_source_sha256"] = R5_HASH
    scene["hanuman_reference_sha256"] = REFERENCE_HASH
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == "VIEW_3D":
                area.spaces.active.region_3d.view_perspective = "CAMERA"
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(output / "hanuman-keyframe.blend"))

    report = {"blender": bpy.app.version_string, "source_sha256": R5_HASH,
              "reference_sha256": REFERENCE_HASH, "profile_sha256": sha256(args.profile),
              "builder_sha256": sha256(Path(__file__)),
              "stage_source_sha256": {name: sha256(TOOLS / f"{name}.py") for name in reports},
              "stages": reports, "bone_count": len(rig.data.bones),
              "source_actions": sorted(action.name for action in bpy.data.actions),
              "resolution": [scene.render.resolution_x, scene.render.resolution_y],
              "samples": args.samples, "grip_error_m": rig.get("hanuman_match_grip_error_m"),
              "landmarks": measurements(scene, rig, profile)}
    (output / "build-report.json").write_text(json.dumps(report, indent=2) + "\n")
    if not args.build_only:
        bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    main()
