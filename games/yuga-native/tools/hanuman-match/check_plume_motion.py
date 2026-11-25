"""Measure the tail and plume tethers on the saved Hanuman rig."""

from __future__ import annotations

import argparse
from hashlib import file_digest
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Vector


CLIPS = ("cast", "cast1", "cast2", "cast3", "defeat", "fire", "idle",
         "jump", "mountain_pulse", "run", "tail_sweep")
SAMPLES = 9
TAIL_SIDES = 16
TAIL_RINGS = 85
CORE_SIDES = 28
CORE_RINGS = 37
JOIN_RING = 77
FIRST_GROOM_RING = 15

LIMITS = {
    "minimum_tail_segment_ratio": .70,
    "maximum_tail_segment_ratio": 1.50,
    "maximum_tail_core_join_m": .002,
    "maximum_plume_root_distance_error_m": .00001,
    "maximum_plume_root_vector_error_m": .00001,
    "maximum_guard_root_distance_error_m": .002,
    "minimum_tip_witness_m": .005,
}


def get_mesh(scene, name, rig):
    obj = scene.objects.get(name)
    if not obj or obj.type != "MESH" or not any(mod.type == "ARMATURE" and mod.object == rig
                                                for mod in obj.modifiers):
        raise ValueError(f"Missing skinned mesh {name!r} on the saved rig")
    return obj


def centers(obj, stride, span=None):
    vertices = obj.data.vertices
    width = stride if span is None else span
    return [obj.matrix_world @ (sum((vertex.co for vertex in vertices[i:i + width]), Vector()) / width)
            for i in range(0, len(vertices), stride)]


def lengths(points):
    return [(b - a).length for a, b in zip(points, points[1:])]


def maximum_delta(a, b):
    return max(abs(x - y) for x, y in zip(a, b, strict=True))


def guard_distances(groom, tail):
    # The tail builder places one guard hair per surface vertex after ring 14.
    # Tests use that same skinning correspondence on already saved meshes.
    offset = FIRST_GROOM_RING * TAIL_SIDES
    return [(root - tail.matrix_world @ tail.data.vertices[offset + index].co).length
            for index, root in enumerate(centers(groom, groom["vertices_per_fiber"], 4))]


def summarize(frames, samples):
    keys = samples[0].keys() - {"tip_in_base_tail_frame_m"}
    return {"sample_frames": frames, **{
        key: (min if key.startswith("minimum") else max)(sample[key] for sample in samples)
        for key in sorted(keys)
    }}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    blend = Path(bpy.data.filepath).resolve()
    scene = bpy.context.scene
    rig = scene.objects.get("YugaHeroRig")
    if not rig or rig.type != "ARMATURE" or rig.animation_data is None:
        raise ValueError("Open the saved Hanuman keyframe with its original rig")
    if set(bpy.data.actions.keys()) != set(CLIPS):
        raise ValueError("The keyframe must contain the eleven original Hanuman actions")
    tail = get_mesh(scene, "Curved articulated Vayu tail", rig)
    core = get_mesh(scene, "Ref · rounded chestnut plume core", rig)
    plume = get_mesh(scene, "Ref · layered tail tuft fibers", rig)
    groom = get_mesh(scene, "Ref · close copper tail groom", rig)
    plume_stride = plume["vertices_per_fiber"]
    guard_stride = groom["vertices_per_fiber"]
    if (len(tail.data.vertices) != TAIL_RINGS * TAIL_SIDES
            or len(core.data.vertices) != CORE_RINGS * CORE_SIDES
            or len(plume.data.vertices) != 328 * plume_stride
            or len(groom.data.vertices) != (TAIL_RINGS - FIRST_GROOM_RING) * TAIL_SIDES * guard_stride):
        raise ValueError("The saved tail, core or fiber topology differs from the wardrobe contract")
    with blend.open("rb") as source:
        digest = file_digest(source, "sha256").hexdigest()

    # Isolate this portion of the loaded rig in memory. The .blend stays intact.
    for obj in scene.objects:
        obj.hide_set(obj not in (rig, tail, core, plume, groom))
    bpy.context.view_layer.update()
    unit = scene.unit_settings.scale_length
    core_center = centers(core, CORE_SIDES)[0]
    rest_segments = lengths(centers(tail, TAIL_SIDES))
    rest_vectors = [root - core_center for root in centers(plume, plume_stride, 4)]
    rest_plume_distances = [point.length for point in rest_vectors]
    rest_guard_distances = guard_distances(groom, tail)
    rest_pose_basis = rig.matrix_world @ rig.data.bones["tail_04"].matrix_local
    rest_basis_inverse = rest_pose_basis.to_3x3().inverted()

    def measure():
        graph = bpy.context.evaluated_depsgraph_get()
        fitted_tail, fitted_core, fitted_plume, fitted_groom = (
            obj.evaluated_get(graph) for obj in (tail, core, plume, groom)
        )
        fitted_rig = rig.evaluated_get(graph)
        tail_centers = centers(fitted_tail, TAIL_SIDES)
        core_centers = centers(fitted_core, CORE_SIDES)
        plume_vectors = [root - core_centers[0] for root in centers(fitted_plume, plume_stride, 4)]
        fitted_basis = fitted_rig.matrix_world @ fitted_rig.pose.bones["tail_04"].matrix
        difference_map = fitted_basis.to_3x3() @ rest_basis_inverse
        vector_error = max((posed - difference_map @ rest).length
                           for posed, rest in zip(plume_vectors, rest_vectors, strict=True))
        stretch = [posed / rest for posed, rest in zip(lengths(tail_centers), rest_segments, strict=True)]
        base = fitted_rig.matrix_world @ fitted_rig.pose.bones["tail_01"].matrix
        relative_tip = base.to_quaternion().inverted() @ (core_centers[-1] - base.translation) * unit
        return {
            "minimum_tail_segment_ratio": min(stretch),
            "maximum_tail_segment_ratio": max(stretch),
            "maximum_tail_core_join_m": (tail_centers[JOIN_RING] - core_centers[0]).length * unit,
            "maximum_plume_root_distance_error_m": maximum_delta(
                [point.length for point in plume_vectors], rest_plume_distances) * unit,
            "maximum_plume_root_vector_error_m": vector_error * unit,
            "maximum_guard_root_distance_error_m": maximum_delta(
                guard_distances(fitted_groom, fitted_tail), rest_guard_distances) * unit,
            "tip_in_base_tail_frame_m": relative_tip,
        }

    still = summarize([scene.frame_current_final], [measure()])
    animation = rig.animation_data
    animation.use_nla = False
    clips = {}
    witness = {}
    for name in CLIPS:
        animation.action = bpy.data.actions[name]
        first, last = animation.action.frame_range
        if first >= last:
            raise ValueError(f"Original action {name} has an empty time span")
        frames = [first + (last - first) * i / (SAMPLES - 1) for i in range(SAMPLES)]
        poses = []
        for frame in frames:
            whole = math.floor(frame)
            scene.frame_set(whole, subframe=frame - whole)
            poses.append(measure())
        frames = [round(frame, 6) for frame in frames]
        clips[name] = summarize(frames, poses)
        if name == "tail_sweep":
            start_tip = poses[0]["tip_in_base_tail_frame_m"]
            displacements = [(pose["tip_in_base_tail_frame_m"] - start_tip).length for pose in poses]
            greatest = max(range(len(frames)), key=displacements.__getitem__)
            witness = {
                "clip": name, "reference_frame": frames[0], "peak_sample_frame": frames[greatest],
                "maximum_tip_displacement_in_base_tail_frame_m": displacements[greatest],
            }

    poses = [still, *clips.values()]
    extrema = {key: (min if key.startswith("minimum") else max)(pose[key] for pose in poses)
               for key in poses[0] if key != "sample_frames"}
    passed = (all((extrema[key] >= LIMITS[key] if key.startswith("minimum") else extrema[key] <= LIMITS[key])
                  for key in extrema)
              and witness["maximum_tip_displacement_in_base_tail_frame_m"] >= LIMITS["minimum_tip_witness_m"])
    result = {
        "blend": blend.name, "blend_sha256": digest, "scene": scene.name, "blender": bpy.app.version_string,
        "linear_units": "meters", "meters_per_blender_unit": unit,
        "tail_segment_ratio_units": "evaluated length divided by rest length",
        "method": {
            "core_join": "world-space distance between tail ring 77 and the first core-ring center",
            "plume_tethers": "root centers versus the core root using rest distances and the tail_04 bone transform",
            "guard_tethers": "root centers versus their corresponding tail surface vertices",
            "motion_witness": "core tip in the rotating tail_01 frame, excluding whole-body motion",
        },
        "tail_rings": TAIL_RINGS, "core_rings": CORE_RINGS,
        "plume_fibers": len(rest_vectors), "guard_hairs": len(rest_guard_distances),
        "limits": LIMITS, "extrema": extrema, "saved_pose": still, "motion_witness": witness,
        "clip_count": len(clips), "clip_pose_samples": sum(len(clip["sample_frames"]) for clip in clips.values()),
        "clips": clips, "passed": passed,
    }
    args.report.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    if not passed:
        raise AssertionError(f"Plume motion verification failed. See {args.report}")
    print(f"Plume motion passed for {len(clips)} clips. See {args.report}")


if __name__ == "__main__":
    main()
