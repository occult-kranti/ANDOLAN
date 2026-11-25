"""Measure Blender's evaluated deformation in the five authored Trial actions."""
from __future__ import annotations

import argparse
from hashlib import file_digest
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils.bvhtree import BVHTree

NATIVE = Path(__file__).resolve().parents[2]
KIT = NATIVE / "assets/design/hanuman-ability-kit.json"
MOTION = NATIVE / "assets/heroes/hanuman/hanuman-ability-motion.tres"
POSE_SAMPLES = 17


def digest(path):
    with path.open("rb") as stream:
        return file_digest(stream, "sha256").hexdigest()


def sample(scene, rig, anatomy, soles, markers, start, end, phase):
    frame = start + (end - start) * phase
    base_frame = math.floor(frame)
    scene.frame_set(base_frame, subframe=frame - base_frame)
    graph = bpy.context.evaluated_depsgraph_get()
    shoe_surfaces = [obj.evaluated_get(graph) for obj in soles]
    minima = [min((obj.matrix_world @ vertex.co).z for vertex in obj.data.vertices) for obj in shoe_surfaces]
    points = {name: obj.evaluated_get(graph).matrix_world.translation.copy() for name, obj in markers.items()}
    body = anatomy.evaluated_get(graph)
    to_body = body.matrix_world.inverted()
    surface = BVHTree.FromObject(anatomy, graph)
    grip = to_body @ points["gada_grip"]
    head = to_body @ points["gada_head"]
    direction = (head - grip).normalized()
    shaft_start = grip + direction * .16
    hit, _, _, _ = surface.ray_cast(shaft_start, direction, (head - shaft_start).length)
    tail_distance = surface.find_nearest(to_body @ points["tail_tip"])[3]
    root = rig.pose.bones["root"].matrix
    finite = all(math.isfinite(value) for value in [*minima, tail_distance, *(c for p in points.values() for c in p)])
    return {
        "phase": phase,
        "frame": frame,
        "sole_z_m": minima,
        "markers_m": {name: list(value) for name, value in points.items()},
        "root_position_m": list(root.translation),
        "root_orientation_wxyz": list(root.to_quaternion()),
        "shaft_body_intersection": hit is not None,
        "tail_tip_body_clearance_m": tail_distance,
        "finite": finite,
    }


def size(vector):
    return math.sqrt(sum(component * component for component in vector))


def verify_move(scene, rig, anatomy, soles, markers, rule):
    action = bpy.data.actions[f"TrialMotion_{rule['motion']}"]
    source = bpy.data.actions[rule["motion"]]
    start, end = action.frame_range
    release = float(action["hanuman_release_phase"])
    impact = action.get("hanuman_impact_phase")
    start_, end_ = source.frame_range
    assert abs(start - start_) < 1e-5 and abs(end - end_) < 1e-5, action.name
    assert abs(release - rule["motion_phase"]) < 1e-5, action.name
    assert impact is None or release < impact < 1, action.name
    assert all('pose.bones["root"]' not in curve.data_path for curve in action.fcurves), action.name
    phases = {release, *(i / (POSE_SAMPLES - 1) for i in range(POSE_SAMPLES))}
    if impact is not None:
        phases.add(float(impact))
    rig.animation_data.action = action
    rows = [
        sample(scene, rig, anatomy, soles, markers, start, end, phase)
        for phase in sorted(phases)
    ]
    root_reference = rows[0]["root_position_m"]
    rotation_reference = rows[0]["root_orientation_wxyz"]
    root_travel = max(size(a - b for a, b in zip(root_reference, row["root_position_m"])) for row in rows)
    root_rotation_delta = max(
        min(size(a - b for a, b in zip(rotation_reference, row["root_orientation_wxyz"])),
            size(a + b for a, b in zip(rotation_reference, row["root_orientation_wxyz"])))
        for row in rows
    )
    shaft_intersections = sum(row["shaft_body_intersection"] for row in rows)
    floor_clearance = min(min(row["sole_z_m"]) for row in rows)
    tail_clearance = min(row["tail_tip_body_clearance_m"] for row in rows)
    assert all(row["finite"] for row in rows), action.name
    assert root_travel <= .000001 and root_rotation_delta <= .000001, action.name
    assert shaft_intersections == 0 and floor_clearance >= 0 and tail_clearance > .04, action.name
    return {
        "action": action.name,
        "source_frame_range": [start, end],
        "release": {"phase": release, "frame": start + (end - start) * release},
        "impact": None if impact is None else {"phase": impact, "frame": start + (end - start) * impact},
        "sample_count": len(rows),
        "min_skinned_sole_z_m": floor_clearance,
        "min_tail_tip_to_body_m": tail_clearance,
        "shaft_centerline_intersections": shaft_intersections,
        "max_root_translation_m": root_travel,
        "max_root_quaternion_delta": root_rotation_delta,
        "phases": [row["phase"] for row in rows],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    scene = bpy.context.scene
    rig = scene.objects["YugaHeroRig"]
    assert len(rig.data.bones) == 167
    rig.animation_data.use_nla = False
    rig.data.pose_position = "POSE"
    anatomy = next(obj for obj in scene.objects if obj.name.startswith("Hanuman · contiguous"))
    soles = [scene.objects[f"Sandal soles · {side}"] for side in ("L", "R")]
    markers = {name: scene.objects[name] for name in ("gada_grip", "gada_head", "tail_tip")}
    rules = json.loads(KIT.read_text())["abilities"]
    clips = {rule["id"]: verify_move(scene, rig, anatomy, soles, markers, rule) for rule in rules}
    receipt = {
        "blender": bpy.app.version_string,
        "editable_actions_sha256": digest(Path(bpy.data.filepath)),
        "authoring_script_sha256": digest(Path(__file__).with_name("author_ability_motion.py")),
        "audit_script_sha256": digest(Path(__file__)),
        "ability_kit_sha256": digest(KIT),
        "runtime_animation_library_sha256": digest(MOTION),
        "bones": len(rig.data.bones),
        "checks": ["source frame windows and release keys", "fixed root transform",
                   "finite landmarks", "skinned soles above source floor",
                   "gada shaft centerline beyond the grip versus contiguous donor body",
                   "tail-tip landmark distance versus contiguous donor body"],
        "pose_samples": sum(clip["sample_count"] for clip in clips.values()),
        "clips": clips,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2) + "\n")


if __name__ == "__main__":
    main()
