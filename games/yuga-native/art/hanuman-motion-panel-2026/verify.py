"""Reopen the study and test source timing, geometry and selected bone poses."""
import hashlib
import json
import math
from pathlib import Path

import bpy

HERE = Path(__file__).resolve().parent
SCENE = HERE / "hanuman-layered-abilities.blend"
TIMELINE = HERE / "timeline.json"
BONES = ("head", "wrist.L", "wrist.R", "foot.L", "foot.R", "tail_02", "tail_04")


def sha(path):
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def sample_bones(rig):
    return {name: (rig.pose.bones[name].head.copy(), rig.pose.bones[name].matrix.to_quaternion())
            for name in BONES}


def main():
    manifest = json.loads(TIMELINE.read_text())
    bpy.ops.wm.open_mainfile(filepath=str(SCENE.resolve()), load_ui=False)
    scene = bpy.context.scene
    rig = next(o for o in scene.objects if o.type == "ARMATURE")
    if len(rig.pose.bones) != 167 or scene.render.fps != 40:
        raise RuntimeError("Rig or frame rate changed")
    helper = scene.objects.get("Icosphere")
    if helper and not helper.hide_render:
        raise RuntimeError("The rig's imported display helper remains visible")
    inlays = [obj for obj in scene.objects if obj.name.startswith("DECOR_Quiet_stone_inlay")]
    if any(not obj.hide_render for obj in inlays):
        raise RuntimeError("The courtyard inlay is competing with the effect patterns")
    texture_files = [im for im in bpy.data.images if im.users and im.source in ("FILE", "TILED")]
    if bpy.data.libraries or any(not image.packed_files for image in texture_files):
        raise RuntimeError("Scene has an external library or unpacked image")
    effect_group = bpy.data.collections.get("Ability layers · editable")
    if not effect_group:
        raise RuntimeError("No editable effect layers")
    strips = list(rig.animation_data.nla_tracks["Gameplay-timed original clips"].strips)
    if len(strips) != len(manifest["shots"]):
        raise RuntimeError("Shot count mismatch")
    source_action = rig.animation_data.action
    results = []
    for shot, strip in zip(manifest["shots"], strips):
        frames = shot["frames"]
        ticks = shot["ticks"]
        for name in ("release", "impact", "recovery", "field_end"):
            if frames[name] - frames["start"] != 2 * ticks[name]:
                raise RuntimeError(f"{shot['id']}: {name} differs from 20 Hz authority")
        if round(strip.frame_end) != frames["end"] or not strip.use_animated_time:
            raise RuntimeError(f"{shot['id']}: NLA duration is truncated")
        time_curve = next(curve for curve in strip.fcurves if curve.data_path == "strip_time")
        first, last = strip.action.frame_range
        rig.animation_data.action = source_action
        rig.animation_data.use_nla = True
        scene.frame_set(frames["start"])
        start_pose = sample_bones(rig)
        milestones = {"release": shot["release_phase"],
                      "impact": shot["impact_phase"],
                      "recovery": 1.0}
        errors = {}
        maximum_motion = 0.0
        for name, phase in milestones.items():
            frame = frames[name]
            expected_time = first + (last - first) * phase
            actual_time = time_curve.evaluate(frame)
            if abs(actual_time - expected_time) > 0.0001:
                raise RuntimeError(f"{shot['id']}: wrong {name} clip sample")
            rig.animation_data.action = source_action
            rig.animation_data.use_nla = True
            scene.frame_set(frame)
            actual = sample_bones(rig)
            maximum_motion = max(maximum_motion,
                                 max((actual[bone][0] - start_pose[bone][0]).length for bone in BONES))
            rig.animation_data.action = strip.action
            rig.animation_data.use_nla = False
            source_frame = math.floor(expected_time)
            scene.frame_set(source_frame, subframe=expected_time - source_frame)
            reference = sample_bones(rig)
            positional = max((actual[bone][0] - reference[bone][0]).length for bone in BONES)
            angular = max(actual[bone][1].rotation_difference(reference[bone][1]).angle for bone in BONES)
            if positional > 0.001 or angular > 0.001:
                raise RuntimeError(f"{shot['id']}: {name} source mismatch {positional:.6f} m, {angular:.6f} rad")
            errors[name] = {"maximum_position_m": round(positional, 7),
                            "maximum_angle_radians": round(angular, 7)}
        rig.animation_data.action = source_action
        rig.animation_data.use_nla = True
        if maximum_motion < 0.005:
            raise RuntimeError(f"{shot['id']}: sampled source joints show no articulated movement")
        results.append({"id": shot["id"], "ticks": ticks, "frames": frames,
                        "maximum_joint_displacement_m": round(maximum_motion, 5),
                        "bone_errors": errors})
    tail = next(s for s in manifest["shots"] if s["id"] == "lanka_dahan")
    tail_mark = next(o for o in effect_group.objects if o.name == "lanka_dahan · contact arc")
    scene.frame_set(tail["frames"]["recovery"] + 1)
    if tail_mark.hide_render:
        raise RuntimeError("Rear field disappeared at body recovery")
    scene.frame_set(tail["frames"]["field_end"] + 1)
    if not tail_mark.hide_render:
        raise RuntimeError("Rear field remained after its expiry")
    vault = next(s for s in manifest["shots"] if s["id"] == "maruti_udayana")
    distance = vault["spatial"]["example_distance_m"]
    max_height = min(1.55, max(0.35, distance * 0.19))
    errors = []
    release, impact = vault["ticks"]["release"], vault["ticks"]["impact"]
    for tick in range(release, impact + 1):
        progress = (tick - release) / (impact - release)
        scene.frame_set(vault["frames"]["start"] + tick * 2)
        expected = (0, -distance * progress, max_height * 4 * progress * (1 - progress))
        error = max(abs(a - b) for a, b in zip(rig.location, expected))
        errors.append(error)
    if max(errors) > 0.0001:
        raise RuntimeError("Vault staging differs from nominal clear-path authority arc")
    pulse = next(s for s in manifest["shots"] if s["id"] == "mountain_pulse")
    pulse_boundary = next(o for o in effect_group.objects if o.name == "mountain_pulse · fixed target circumference")
    if abs(pulse_boundary["radius_m"] - pulse["spatial"]["impact_radius_m"]) > 0.0001:
        raise RuntimeError("Mountain footprint radius differs")
    receipt = {
        "scene_sha256": sha(SCENE), "timeline_sha256": sha(TIMELINE),
        "builder_sha256": sha(HERE / "build.py"), "verifier_sha256": sha(Path(__file__)),
        "source_model_sha256": manifest["source_model_sha256"], "blender": bpy.app.version_string,
        "packed_texture_files": len(texture_files), "external_libraries": len(bpy.data.libraries),
        "rig_joints": len(rig.pose.bones), "effect_objects": len(effect_group.objects),
        "display_helper_hidden": bool(helper and helper.hide_render),
        "courtyard_inlays_hidden": len(inlays),
        "nominal_vault_max_position_error_m": round(max(errors), 8),
        "tail_field_outlives_recovery": True, "mountain_radius_m": pulse_boundary["radius_m"],
        "shots": results,
        "scope": "Offline presentation scene. Sampled source rig, nominal clear-path vault, effect timing and packed dependencies. No runtime or target-device performance claim."
    }
    (HERE / "evidence/verification.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
