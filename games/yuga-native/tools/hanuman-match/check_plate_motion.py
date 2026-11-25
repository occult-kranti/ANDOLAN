"""Measure arm isolation on the saved Hanuman cuirass without saving changes."""

from __future__ import annotations

import argparse
from hashlib import file_digest
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Matrix


CLIPS = ("cast", "cast1", "cast2", "cast3", "defeat", "fire", "idle",
         "jump", "mountain_pulse", "run", "tail_sweep")
SIDES = ("L", "R")
SAMPLES_PER_CLIP = 9
PERTURBATION_DEGREES = 20
PLATE_LIMIT_M = 0.000001
WITNESS_MIN_M = 0.005


def snapshot(rig, plate):
    graph = bpy.context.evaluated_depsgraph_get()
    shell = plate.evaluated_get(graph)
    evaluated_rig = rig.evaluated_get(graph)
    coordinates = [shell.matrix_world @ vertex.co for vertex in shell.data.vertices]
    hands = {side: evaluated_rig.matrix_world @ evaluated_rig.pose.bones[f"wrist.{side}"].head
             for side in SIDES}
    return coordinates, hands


def perturb(rig, plate, bone_name, before):
    bone = rig.pose.bones[bone_name]
    rest = bone.matrix_basis.copy()
    turn = Matrix.Rotation(math.radians(PERTURBATION_DEGREES), 4, "X")
    bone.matrix_basis = rest @ turn
    bpy.context.view_layer.update()
    after = snapshot(rig, plate)
    bone.matrix_basis = rest
    bpy.context.view_layer.update()
    maximum = max((a-b).length for a, b in zip(before[0], after[0], strict=True))
    return maximum, {side: (before[1][side]-after[1][side]).length for side in SIDES}


def measure_frame(rig, plate):
    before = snapshot(rig, plate)
    result = {}
    for side in SIDES:
        plate_difference, wrist_difference = perturb(rig, plate, f"upperarm01.{side}", before)
        result[side] = (plate_difference, wrist_difference[side])
    return result


def summarize(frames, measures):
    return {"sample_frames": frames,
            "per_arm": {side: {
                "maximum_plate_displacement_m": max(frame[side][0] for frame in measures),
                "minimum_wrist_witness_displacement_m": min(frame[side][1] for frame in measures),
            } for side in SIDES}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else [])
    blend = Path(bpy.data.filepath).resolve()
    scene = bpy.context.scene
    rig = scene.objects.get("YugaHeroRig")
    plate = scene.objects.get("Ref · dark forged cuirass")
    if not rig or not plate or not any(modifier.type == "ARMATURE" and modifier.object == rig
                                      for modifier in plate.modifiers):
        raise ValueError("Open a keyframe blend containing the skinned Hanuman cuirass")
    if set(bpy.data.actions.keys()) != set(CLIPS):
        raise ValueError("The keyframe must contain the eleven original Hanuman actions")
    with blend.open("rb") as stream:
        digest = file_digest(stream, "sha256").hexdigest()

    # Limit graph evaluation to the loaded plate and its rig. These changes
    # stay in memory, so the same scene can be reopened for any other check.
    for obj in scene.objects:
        obj.hide_set(obj not in (rig, plate))
    bpy.context.view_layer.update()
    coords, wrists = snapshot(rig, plate)
    spine_witness, _ = perturb(rig, plate, "spine01", (coords, wrists))
    still = summarize([scene.frame_current_final], [measure_frame(rig, plate)])
    animation = rig.animation_data or rig.animation_data_create()
    animation.use_nla = False
    clips = {}
    for name in CLIPS:
        action = bpy.data.actions[name]
        animation.action = action
        first, last = action.frame_range
        frames = [first+(last-first)*i/(SAMPLES_PER_CLIP-1) for i in range(SAMPLES_PER_CLIP)]
        samples = []
        for frame in frames:
            whole = math.floor(frame)
            scene.frame_set(whole, subframe=frame-whole)
            samples.append(measure_frame(rig, plate))
        clips[name] = summarize([round(frame, 6) for frame in frames], samples)
    sides = [measure for summary in (still, *clips.values()) for measure in summary["per_arm"].values()]
    passed = (spine_witness >= WITNESS_MIN_M and
              all(side["maximum_plate_displacement_m"] <= PLATE_LIMIT_M and
                  side["minimum_wrist_witness_displacement_m"] >= WITNESS_MIN_M for side in sides))
    result = {
        "blend": blend.name, "blend_sha256": digest, "blender": bpy.app.version_string,
        "method": "world-space vertex differences under independent upper-arm rotations",
        "rotation_local_x_degrees": PERTURBATION_DEGREES,
        "maximum_plate_displacement_limit_m": PLATE_LIMIT_M, "minimum_sensitivity_witness_m": WITNESS_MIN_M,
        "evaluated_vertex_count": len(coords), "saved_pose": still,
        "spine_rotation_plate_witness_m": spine_witness,
        "clip_count": len(clips), "clip_pose_samples": sum(len(clip["sample_frames"]) for clip in clips.values()),
        "clips": clips, "passed": passed,
    }
    args.report.write_text(json.dumps(result, indent=2, allow_nan=False)+"\n", encoding="utf-8")
    if not passed:
        raise AssertionError(f"Plate isolation failed. See {args.report}")
    print(f"Plate isolation passed for {len(clips)} clips. See {args.report}")


if __name__ == "__main__":
    main()
