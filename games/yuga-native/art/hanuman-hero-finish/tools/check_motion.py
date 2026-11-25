"""Compare root/prop/foot contacts and tail landmarks on two actual Blender imports."""

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Matrix

CLIP = "mountain_pulse"
BODY = ("root", "head", "wrist.L", "wrist.R", "foot.L", "foot.R")
TAIL = ("tail_01", "tail_02", "tail_03", "tail_04", "tail_tip")
SOCKETS = ("gada_grip", "gada_head", "tail_tip")
BEATS = (0, 0.55, 0.78, 0.82, 0.835, 0.86, 0.875, 0.90, 0.915, 0.945, 0.965, 1)


def positions(path, phases):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.fps = 30
    bpy.ops.import_scene.gltf(filepath=str(path))
    (rig,) = (o for o in scene.objects if o.type == "ARMATURE")
    data = rig.animation_data
    (track,) = (t for t in data.nla_tracks if t.name == CLIP)
    action = track.strips[0].action
    for t in data.nla_tracks:
        t.mute = True
    data.action = None
    for joint in rig.pose.bones:
        joint.matrix_basis = Matrix.Identity(4)
    data.action = action
    start, end = action.frame_range
    result = {}
    for phase in phases:
        f = start + (end - start) * phase
        scene.frame_set(math.floor(f), subframe=f % 1)
        graph = bpy.context.evaluated_depsgraph_get()
        actor = rig.evaluated_get(graph)
        points = {
            n: actor.matrix_world @ actor.pose.bones[n].head
            for n in (*BODY, *TAIL[:-1])
        }
        for n in SOCKETS:
            points[n] = (
                scene.objects[n].evaluated_get(graph).matrix_world.translation.copy()
            )
        result[phase] = points
    return result


def distance(a, b):
    return (a - b).length


def segment_distance(point, start, end):
    segment = end - start
    weight = max(0.0, min(1.0, (point - start).dot(segment) / segment.length_squared))
    return distance(point, start + weight * segment)


def point(v):
    return [round(float(x), 5) for x in v]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("finished", type=Path)
    parser.add_argument("receipt", type=Path)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1 :])
    phases = sorted({*BEATS, *(i / 160 for i in range(161))})
    before, after = (positions(path, phases) for path in (args.source, args.finished))

    def delta(t, n):
        return distance(before[t][n], after[t][n])

    peak = max(phases, key=lambda t: delta(t, "tail_tip"))
    protected = (*BODY, "gada_grip", "gada_head")
    planted_delta = max(delta(t, n) for t in phases for n in protected)
    begin = max(delta(t, n) for t in phases if t <= 0.78 for n in TAIL)
    end = max(delta(1, n) for n in TAIL)
    assert planted_delta < 1e-5 and begin < 0.001 and end < 1e-5
    assert 0.03 < delta(peak, "tail_tip") < 0.50 and 0.78 < peak < 0.98

    # Compare the distal tail centreline with the actual imported head/feet/gada
    # centres. These are point-to-segment landmarks, not mesh intersection tests.
    def clearance(points, collider):
        return min(
            segment_distance(p[collider], p[a], p[b])
            for t, p in points.items()
            for a, b in zip(TAIL[1:], TAIL[2:])
            if t >= 0.78
        )

    summary = {
        "clip": CLIP,
        "blender": bpy.app.version_string,
        "source_sha256": digest(args.source),
        "enhanced_sha256": digest(args.finished),
        "samples": len(phases),
        "up_axis": "Blender Z",
        "peak_tip_displacement_m": round(delta(peak, "tail_tip"), 6),
        "peak_phase": peak,
        "max_protected_body_or_gada_displacement_m": round(planted_delta, 7),
        "protected_landmarks": protected,
        "max_tail_change_through_impact_m": round(begin, 7),
        "tail_reset_displacement_m": round(end, 7),
        "distal_chain_minimum_centerline_separation_m": {
            n: {
                "before": round(clearance(before, n), 5),
                "after": round(clearance(after, n), 5),
            }
            for n in ("foot.L", "foot.R", "head", "gada_head")
        },
        "after_impact_distal_chain_lows_m": {
            name: round(
                min(p[n].z for t, p in data.items() if t >= 0.78 for n in TAIL[1:]), 5
            )
            for name, data in (("before", before), ("after", after))
        },
        "screening": "Centreline of tail_02 through tail_tip vs joint/socket points. Floor is Z=0. Collision radii, fur, costume and weapon surface are outside this check.",
        "keyframes": [
            {
                "phase": t,
                "before_tip_m": point(before[t]["tail_tip"]),
                "after_tip_m": point(after[t]["tail_tip"]),
                "distance_m": round(delta(t, "tail_tip"), 6),
            }
            for t in BEATS
        ],
    }
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(summary, indent=2) + "\n")
    print(summary["peak_tip_displacement_m"], "m tip change at", peak, flush=True)


if __name__ == "__main__":
    main()
