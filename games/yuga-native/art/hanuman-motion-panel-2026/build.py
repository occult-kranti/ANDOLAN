"""Create a source-bound Hanuman ability presentation study.

Run from the repository root with Blender 4.3:
  blender -b -t 1 --python-exit-code 1 -P games/yuga-native/art/hanuman-motion-panel-2026/build.py
The output is a separate editable scene; no gameplay source or hero GLB is altered.
"""
import hashlib
import json
import math
import re
from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
NATIVE = HERE.parents[1]
ART = NATIVE / "art/hanuman-hero-finish"
BASE = ART / "blender/hanuman.blend"
KIT = NATIVE / "assets/design/hanuman-ability-kit.json"
MARKERS = NATIVE / "assets/heroes/hanuman/hanuman-ability-motion.tres"
LOOK = HERE / "look.json"
OUTPUT = HERE / "hanuman-layered-abilities.blend"
MANIFEST = HERE / "timeline.json"
BASE_HASH = "f0fc5798d7cfec0afc2ae084b8b8f5a76950ad94bcc1ec9f89fbc24f5952e7b0"
MODEL_HASH = "6612e710578c2527fc1edb84cd8c2c64936cd7ec2a0b201d4a714eead870273a"


def digest(path):
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def read_markers():
    result = {}
    name = None
    for line in MARKERS.read_text().splitlines():
        if line.startswith('resource_name = '):
            name = line.split('"')[1]
            result[name] = {}
        match = re.match(r"metadata/hanuman_(release|impact)_phase = ([0-9.]+)$", line)
        if match:
            result[name][match.group(1)] = float(match.group(2))
    return result


def material(name, hex_color, strength):
    rgb = [int(hex_color[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    shader = nodes.get("Principled BSDF")
    material.node_tree.nodes.remove(shader)
    emit = nodes.new("ShaderNodeEmission")
    emit.inputs["Color"].default_value = (*rgb, 1.0)
    emit.inputs["Strength"].default_value = strength
    material.node_tree.links.new(emit.outputs[0], nodes.get("Material Output").inputs["Surface"])
    material.diffuse_color = (*rgb, 1.0)
    return material


def ring(collection, name, material, radius, width, centre, start, end):
    segments = max(16, round(80 * abs(end - start) / math.tau))
    vertices = []
    faces = []
    for i in range(segments + 1):
        theta = start + (end - start) * i / segments
        for distance in (radius - width / 2, radius + width / 2):
            vertices.append((math.sin(theta) * distance, -math.cos(theta) * distance, 0))
        if i:
            a = (i - 1) * 2
            faces.append((a, a + 1, a + 3, a + 2))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.materials.append(material)
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    obj.location = centre
    obj["radius_m"] = radius
    return obj


def curve(collection, name, material, points, width):
    path = bpy.data.curves.new(name, "CURVE")
    path.dimensions = "3D"
    path.resolution_u = 1
    path.bevel_depth = width / 2
    path.bevel_resolution = 2
    spline = path.splines.new("POLY")
    spline.points.add(len(points) - 1)
    for item, point in zip(spline.points, points):
        item.co = (*point, 1)
    path.materials.append(material)
    obj = bpy.data.objects.new(name, path)
    collection.objects.link(obj)
    return obj


def show_between(obj, start, stop):
    for frame, hidden in ((1, True), (max(1, start - 1), True), (start, False), (stop, False), (stop + 1, True)):
        obj.hide_render = hidden
        obj.keyframe_insert(data_path="hide_render", frame=frame)
    if obj.animation_data and obj.animation_data.action:
        for channel in obj.animation_data.action.fcurves:
            for key in channel.keyframe_points:
                key.interpolation = "CONSTANT"


def heading_point(radius, angle, height=0.045):
    return (radius * math.sin(angle), -radius * math.cos(angle), height)


def line_of_fan(collection, name, mat, radius, theta, angle, width):
    return curve(collection, name, mat,
                 [heading_point(0.14, theta + angle), heading_point(radius, theta + angle)], width)


def fan_effect(collection, ability, frames, style, primary, secondary, width):
    geometry = ability["geometry"]
    radius = geometry["range_m"]
    center_angle = math.pi if geometry.get("direction") == "rear" else 0
    half = math.acos(geometry["half_angle_cos"])
    start_angle, end_angle = center_angle - half, center_angle + half
    floor = (0, 0, 0.045)
    pre = [
        ring(collection, ability["id"] + " · fan boundary", secondary, radius, width, floor, start_angle, end_angle),
        line_of_fan(collection, ability["id"] + " · left bound", secondary, radius, center_angle, -half, width * 0.7),
        line_of_fan(collection, ability["id"] + " · right bound", secondary, radius, center_angle, half, width * 0.7),
    ]
    # A short segmented inner fan supplies a shape cue that remains readable in
    # grayscale; line pattern distinguishes the protective fan from attacks.
    segments = 4 if style == "shield_fan" else 7
    for index in range(segments):
        a = start_angle + (end_angle - start_angle) * (index + 0.16) / segments
        b = start_angle + (end_angle - start_angle) * (index + 0.74) / segments
        pre.append(ring(collection, ability["id"] + f" · pattern {index + 1}", secondary,
                        radius * 0.82, width * 0.6, floor, a, b))
    for obj in pre:
        obj["role"] = "windup boundary"
        show_between(obj, frames["start"], frames["release"] - 1)
    hit = ring(collection, ability["id"] + " · contact arc", primary, radius, width * 2.8,
               (0, 0, 0.055), start_angle, end_angle)
    hit["role"] = "contact accent"
    end = frames["field_end"] if geometry.get("direction") == "rear" else min(
        frames["end"], frames["impact"] + 8)
    show_between(hit, frames["impact"], end)
    for index in range(5):
        theta = center_angle - half * 0.7 + (half * 1.4) * index / 4
        x, y, z = heading_point(radius * 0.64, theta, 0.07)
        flare = ring(collection, ability["id"] + f" · contact trace {index + 1}", primary,
                     radius * 0.11, width * 0.65, (x, y, z), 0, math.tau)
        flare["role"] = "contact pattern"
        show_between(flare, frames["impact"], min(end, frames["impact"] + 7))
        if style == "shield_fan":
            # Upright protective arches differ from the low attacking sparks,
            # allowing this cue to remain distinct in monochrome.
            x, y, _ = heading_point(0.68, theta, 0)
            points = [(x, y, 0.25), (x * 1.2, y * 1.2, 1.15),
                      (x * 0.8, y * 0.8, 1.75)]
        else:
            near = heading_point(radius * 0.22, theta, 0.08)
            far = heading_point(radius * 0.54, theta, 0.12)
            middle = tuple((a + b) / 2 for a, b in zip(near, far))
            points = [near, (middle[0], middle[1], 0.65), far]
        spark = curve(collection, ability["id"] + f" · airborne accent {index + 1}",
                      primary, points, width * 0.55)
        spark["role"] = "protective arch" if style == "shield_fan" else "brief impact spark"
        show_between(spark, frames["impact"], min(end, frames["impact"] + 7))
    return {"radius_m": radius, "half_angle_degrees": round(math.degrees(half), 4),
            "direction": geometry.get("direction", "front")}


def vault_effect(collection, ability, frames, distance, primary, secondary, width):
    geometry = ability["geometry"]
    if not 0 < distance <= geometry["target_range_m"]:
        raise ValueError("Vault example must be within the ability range")
    path = curve(collection, ability["id"] + " · forward corridor", secondary,
                 [(0, 0, 0.045), (0, -distance, 0.045)], width)
    path["role"] = "non-damaging path"
    show_between(path, frames["start"], frames["impact"] - 1)
    endpoint = ring(collection, ability["id"] + " · nominal landing", secondary,
                    0.48, width, (0, -distance, 0.05), 0, math.tau)
    endpoint["role"] = "nominal landing"
    show_between(endpoint, frames["start"], frames["impact"] - 1)
    landing = ring(collection, ability["id"] + " · landing accent", primary,
                   0.58, width * 1.7, (0, -distance, 0.055), 0, math.tau)
    landing["role"] = "nominal ground contact"
    show_between(landing, frames["impact"], min(frames["end"], frames["impact"] + 7))
    for side in (-1, 1):
        for index in range(3):
            x = side * (0.35 + index * 0.19)
            ribbon = curve(collection, ability["id"] + f" · wind {side} {index}", primary,
                           [(x, -distance * 0.18, 0.18),
                            (x * 1.3, -distance * 0.48, 1.0 - index * 0.15),
                            (x, -distance * 0.82, 0.2)], width * 0.55)
            ribbon["role"] = "movement trail"
            show_between(ribbon, frames["release"], frames["impact"] - 1)
    return {"example_distance_m": distance, "max_range_m": geometry["target_range_m"],
            "landing": "Nominal landing; actual contact may occur early at cover."}


def pulse_effect(collection, ability, frames, distance, primary, secondary, width):
    geometry = ability["geometry"]
    if not 0 <= distance <= geometry["target_range_m"]:
        raise ValueError("Pulse example target must be in cast range")
    center = (0, -distance, 0.05)
    radius = geometry["radius_m"]
    outer = ring(collection, ability["id"] + " · fixed target circumference",
                 secondary, radius, width, center, 0, math.tau)
    outer["role"] = "fixed target footprint"
    show_between(outer, frames["start"], frames["impact"] - 1)
    inner = ring(collection, ability["id"] + " · target focus",
                 secondary, 0.32, width * 1.1, center, 0, math.tau)
    inner["role"] = "fixed target center"
    show_between(inner, frames["start"], frames["impact"] - 1)
    for index in range(12):
        theta = index * math.tau / 12
        line = curve(collection, ability["id"] + f" · radial tick {index + 1}", secondary,
                     [(center[0] + (radius - 0.38) * math.sin(theta),
                       center[1] - (radius - 0.38) * math.cos(theta), 0.055),
                      (center[0] + radius * math.sin(theta),
                       center[1] - radius * math.cos(theta), 0.055)], width * 0.65)
        show_between(line, frames["start"], frames["impact"] - 1)
    blast = ring(collection, ability["id"] + " · landing circumference",
                 primary, radius, width * 2.2, (0, -distance, 0.065), 0, math.tau)
    blast["role"] = "landing accent"
    show_between(blast, frames["impact"], min(frames["end"], frames["impact"] + 8))
    travel = curve(collection, ability["id"] + " · release direction", primary,
                   [(0, 0, 1.6), (0, -distance * 0.45, 3.6), (0, -distance, 0.15)], width * 1.1)
    travel["role"] = "outgoing motion"
    show_between(travel, frames["release"], frames["impact"] - 1)
    for index in range(8):
        theta = index * math.tau / 8
        near = (center[0] + 0.7 * math.sin(theta),
                center[1] - 0.7 * math.cos(theta), 0.08)
        far = (center[0] + 1.4 * math.sin(theta),
               center[1] - 1.4 * math.cos(theta), 0.12)
        middle = ((near[0] + far[0]) / 2, (near[1] + far[1]) / 2, 0.85)
        spark = curve(collection, ability["id"] + f" · impact plume {index + 1}",
                      primary, [near, middle, far], width * 0.7)
        spark["role"] = "landing accent"
        show_between(spark, frames["impact"], min(frames["end"], frames["impact"] + 8))
    return {"example_distance_m": distance, "target_range_m": geometry["target_range_m"],
            "impact_radius_m": radius, "target": "Fixed world point during cast."}


def frame_at(start, tick, frames_per_tick):
    return start + tick * frames_per_tick


def authored_ticks(timing, hz):
    def ticks(seconds):
        return int(math.floor(seconds * hz + 0.5))
    release = ticks(timing["windup_s"])
    impact = release + ticks(timing["travel_s"])
    recovery = impact + ticks(timing["recovery_s"])
    field_end = impact + ticks(timing["active_s"])
    return {"release": release, "impact": impact, "recovery": recovery, "field_end": field_end}


def linearize(action):
    if action:
        for channel in action.fcurves:
            for key in channel.keyframe_points:
                key.interpolation = "LINEAR"


def main():
    if digest(BASE) != BASE_HASH or digest(ART / "models/hanuman-enhanced.glb") != MODEL_HASH:
        raise RuntimeError("The pinned source scene or hero model changed")
    kit = json.loads(KIT.read_text())
    options = json.loads(LOOK.read_text())
    markers = read_markers()
    fps = options["frames_per_second"]
    hz = options["authority_ticks_per_second"]
    if fps % hz:
        raise ValueError("Frame rate must be an integer multiple of the authority tick")
    frame_tick = fps // hz
    bpy.ops.wm.open_mainfile(filepath=str(BASE.resolve()), load_ui=False)
    scene = bpy.context.scene
    scene.render.fps = fps
    scene.render.fps_base = 1
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 8
    scene.cycles.use_denoising = False
    scene.render.threads_mode = "FIXED"
    scene.render.threads = 1
    scene.render.resolution_x = 768
    scene.render.resolution_y = 432
    scene.render.resolution_percentage = 100
    rig = next(o for o in scene.objects if o.type == "ARMATURE")
    if len(rig.pose.bones) != 167:
        raise ValueError("Unexpected skeleton")
    # glTF import retains this bone-display helper as a renderable mesh.
    # It otherwise casts a star-shaped shadow beneath the moving actor.
    helper = scene.objects.get("Icosphere")
    if helper:
        helper.hide_render = True
    # The courtyard's dark ground inlay resembles an impact icon at this
    # camera distance. Keep the stage clear for the new ability patterns.
    for obj in scene.objects:
        if obj.name.startswith("DECOR_Quiet_stone_inlay"):
            obj.hide_render = True
    data = rig.animation_data
    actions = {strip.action.name.split("_YugaHeroRig")[0]: strip.action
               for track in data.nla_tracks for strip in track.strips}
    for track in list(data.nla_tracks):
        data.nla_tracks.remove(track)
    data.action = None
    track = data.nla_tracks.new()
    track.name = "Gameplay-timed original clips"
    old = bpy.data.collections.get("Presentation VFX · editable")
    if old:
        for obj in list(old.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.collections.remove(old)
    effects = bpy.data.collections.new("Ability layers · editable")
    scene.collection.children.link(effects)
    scene.timeline_markers.clear()
    camera = scene.camera
    camera.animation_data_clear()
    camera.data.lens = 31
    width = options["accent_width_m"]
    shots = []
    cursor = 1
    for ability in kit["abilities"]:
        style = options["styles"][ability["id"]]
        beats = authored_ticks(ability["timing"], hz)
        end_tick = max(beats["recovery"], beats["field_end"])
        frames = {name: frame_at(cursor, tick, frame_tick) for name, tick in beats.items()}
        frames["start"] = cursor
        frames["end"] = frame_at(cursor, end_tick, frame_tick)
        clip = ability["motion"]
        if clip not in actions:
            raise ValueError(f"Missing source clip: {clip}")
        action = actions[clip]
        first, last = action.frame_range
        motion = markers[clip]
        release_phase = motion["release"]
        impact_phase = motion.get("impact", release_phase)
        strip = track.strips.new(ability["label"], cursor, action)
        strip.action_frame_start = first
        strip.action_frame_end = last
        strip.extrapolation = "NOTHING"
        strip.use_animated_time = True
        # Changing the action range resets the strip duration in Blender.
        # Apply the authored end afterwards so every recovery is evaluated.
        strip.frame_end = frames["end"]
        pose_keys = [(frames["start"], 0.0), (frames["release"], release_phase)]
        if frames["impact"] > frames["release"]:
            pose_keys.append((frames["impact"], impact_phase))
        pose_keys += [(frames["recovery"], 1.0), (frames["end"], 1.0)]
        for frame, phase in pose_keys:
            strip.strip_time = first + (last - first) * phase
            strip.keyframe_insert(data_path="strip_time", frame=frame)
        for channel in strip.fcurves:
            for key in channel.keyframe_points:
                key.interpolation = "LINEAR"
        scene.timeline_markers.new(ability["label"], frame=cursor)
        main_mat = material(ability["label"] + " · contact", style["color"], 1.2)
        muted_mat = material(ability["label"] + " · telegraph", style["color"], 0.7)
        motif = style["motif"]
        if motif in {"front_arc", "shield_fan", "rear_fan"}:
            spatial = fan_effect(effects, ability, frames, motif, main_mat, muted_mat, width)
        elif motif == "vault_path":
            spatial = vault_effect(effects, ability, frames, options["vault_distance_m"],
                                   main_mat, muted_mat, width)
        elif motif == "target_disk":
            spatial = pulse_effect(effects, ability, frames, options["mountain_target_m"],
                                   main_mat, muted_mat, width)
        else:
            raise ValueError("Unknown ability style: " + motif)
        # Mirror the nominal clear-route vault translation. Every other study is
        # planted at the origin. This does not affect collision or game state.
        distance = options["vault_distance_m"] if motif == "vault_path" else 0.0
        positions = [(cursor, 0.0, 0.0), (frames["release"], 0.0, 0.0)]
        if distance:
            arc_height = min(1.55, max(0.35, distance * 0.19))
            for tick in range(beats["release"] + 1, beats["impact"] + 1):
                progress = (tick - beats["release"]) / (beats["impact"] - beats["release"])
                positions.append((frame_at(cursor, tick, frame_tick), -distance * progress,
                                  arc_height * 4 * progress * (1 - progress)))
        positions.append((frames["end"], -distance, 0.0))
        for frame, y, z in positions:
            rig.location = (0, y, z)
            rig.keyframe_insert(data_path="location", frame=frame)
        position = Vector(style["camera"])
        aim = Vector(style["aim"])
        camera_points = [(cursor, 0.0), (frames["end"], -distance)]
        if distance:
            camera_points = [(cursor, 0.0), (frames["release"], 0.0),
                             (frames["impact"], -distance), (frames["end"], -distance)]
        for frame, offset in camera_points:
            camera.location = position + Vector((0, offset, 0))
            camera.rotation_euler = (aim - position).to_track_quat("-Z", "Y").to_euler()
            camera.keyframe_insert(data_path="location", frame=frame)
            camera.keyframe_insert(data_path="rotation_euler", frame=frame)
        shots.append({"id": ability["id"], "label": ability["label"], "clip": clip,
                      "ticks": beats, "frames": frames, "release_phase": release_phase,
                      "impact_phase": impact_phase, "spatial": spatial, "motif": motif,
                      "study_color": style["color"], "runtime_color": ability["color"]})
        cursor = frames["end"] + options["gap_frames"] + 1
    linearize(rig.animation_data.action)
    for channel in rig.animation_data.action.fcurves:
        for key in channel.keyframe_points:
            if any(round(key.co.x) == shot["frames"]["end"] for shot in shots):
                key.interpolation = "CONSTANT"
    if camera.animation_data and camera.animation_data.action:
        linearize(camera.animation_data.action)
        for channel in camera.animation_data.action.fcurves:
            for key in channel.keyframe_points:
                if any(round(key.co.x) == shot["frames"]["end"] for shot in shots):
                    key.interpolation = "CONSTANT"
    scene.frame_end = cursor - options["gap_frames"] - 1
    scene.frame_set(1)
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT.resolve()), compress=True)
    MANIFEST.write_text(json.dumps({
        "source_model_sha256": MODEL_HASH,
        "source_scene_sha256": BASE_HASH,
        "ability_profile_sha256": digest(KIT),
        "motion_markers_sha256": digest(MARKERS),
        "look_sha256": digest(LOOK),
        "fps": fps,
        "authority_hz": hz,
        "shots": shots,
        "scope": "Offline presentation study. Nominal vault landing assumes a clear route.",
    }, indent=2) + "\n")
    print(f"Saved {OUTPUT} with {len(shots)} timed abilities and {scene.frame_end} frames.")


if __name__ == "__main__":
    main()
