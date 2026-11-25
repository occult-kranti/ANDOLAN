"""Measure belt-side hand clearance and finger intersections in a saved keyframe."""

from __future__ import annotations

import argparse
from hashlib import file_digest
from itertools import combinations
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils.bvhtree import BVHTree


BODY_PREFIX = "Hanuman · contiguous skinned anatomy"
MIN_WEIGHT = 0.75
GARMENT_GROUPS = {
    "left_hip_fold": ("Ref · diagonal hip fold L",),
    "waist_belt": ("Ref · cast bronze waist belt",),
    "belt_trim": ("Ref · belt struck lip", "Ref · belt stud", "Ref · round carved belt buckle"),
    "nearby_cloth": ("Ref · gathered dhoti leg", "Ref · diagonal hip fold R", "Ref · draped selvedge",
                     "Ref · inner crossover tabard", "Ref · hanging center panel"),
}


def weighted_vertices(mesh, group_names, prefixes):
    return {
        vertex.index for vertex in mesh.vertices
        if sum(group.weight for group in vertex.groups
               if group_names[group.group].endswith(".L")
               and group_names[group.group].startswith(prefixes)) >= MIN_WEIGHT
    }


def geometry(obj, graph):
    posed = obj.evaluated_get(graph)
    points = [posed.matrix_world @ v.co for v in posed.data.vertices]
    faces = [tuple(face.vertices) for face in posed.data.polygons]
    return points, faces


def region(points, polygons, held):
    faces = [face for face in polygons if all(index in held for index in face)]
    return (BVHTree.FromPolygons(points, faces) if faces else None), len(faces)


def outfit_contact(scene, graph, hand, samples):
    groups = {}
    for label, prefixes in GARMENT_GROUPS.items():
        surfaces = []
        for obj in scene.objects:
            if obj.type != "MESH" or obj.hide_render or not obj.name.startswith(prefixes):
                continue
            points, faces = geometry(obj, graph)
            if not points or not faces:
                continue
            surface = BVHTree.FromPolygons(points, faces)
            distances = [surface.find_nearest(pt)[3] for pt in samples]
            nearest = min((gap for gap in distances if gap is not None), default=None)
            surfaces.append({"mesh": obj.name, "faces": len(faces),
                             "tested_flesh_vertices": len(samples),
                             "nearest_mm": round(nearest * 1000, 6) if nearest is not None else None,
                             "overlap_pairs": len(hand.overlap(surface)) if hand is not None else 0})
        groups[label] = {
            "objects": len(surfaces),
            "nearest_mm": min((s["nearest_mm"] for s in surfaces if s["nearest_mm"] is not None),
                              default=None),
            "overlap_pairs": sum(s["overlap_pairs"] for s in surfaces),
            "surfaces": surfaces,
        }
    return groups


def check(scene, graph):
    rig = scene.objects.get("YugaHeroRig")
    body = next((o for o in scene.objects if o.type == "MESH" and o.name.startswith(BODY_PREFIX)), None)
    if rig is None or rig.type != "ARMATURE" or rig.data.pose_position != "POSE" or body is None:
        raise ValueError("Open a posed Hanuman keyframe with its skinned anatomy")
    if body.hide_render or not any(
        modifier.type == "ARMATURE" and modifier.object == rig
        and modifier.show_viewport and modifier.show_render for modifier in body.modifiers
    ):
        raise ValueError("The visible anatomy must use the active Hanuman rig")
    weight_names = {group.index: group.name for group in body.vertex_groups}
    points, faces = geometry(body, graph)
    if len(points) != len(body.data.vertices) or len(faces) != len(body.data.polygons):
        raise ValueError("The evaluated skin must preserve the source weight indices and polygons")

    held = weighted_vertices(body.data, weight_names, ("wrist", "finger"))
    samples = [points[i] for i in sorted(held)]
    if not all(math.isfinite(v) for point in samples for v in point):
        raise ValueError("The weighted hand contains invalid world-space coordinates")
    hand, hand_faces = region(points, faces, held)

    digit_bvh, digit_counts = {}, {}
    for digit in range(1, 6):
        indices = weighted_vertices(body.data, weight_names, (f"finger{digit}-",))
        digit_bvh[digit], face_count = region(points, faces, indices)
        digit_counts[digit] = {"vertices": len(indices), "faces": face_count}
    digit_pairs = {
        f"{first}-{second}": len(digit_bvh[first].overlap(digit_bvh[second]))
        if digit_bvh[first] is not None and digit_bvh[second] is not None else None
        for first, second in combinations(digit_bvh, 2)
    }
    outfit = outfit_contact(scene, graph, hand, samples)
    checks = {
        "hand_and_each_digit_sampled": hand_faces >= 100 and all(d["faces"] >= 10 for d in digit_counts.values()),
        "all_garment_groups_present": all(g["objects"] and g["nearest_mm"] is not None for g in outfit.values()),
        "no_cross_digit_overlaps": all(pairs == 0 for pairs in digit_pairs.values()),
        "no_unexpected_garment_overlaps": hand is not None
        and all(g["overlap_pairs"] == 0 for g in outfit.values()),
    }
    return {"hand": {"mesh": body.name, "vertices": len(held), "faces": hand_faces},
            "digits": digit_counts, "digit_overlap_pairs": digit_pairs, "garment_groups": outfit,
            "checks": checks, "passed": all(checks.values())}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    path = Path(bpy.data.filepath).resolve()
    if args.report.resolve() == path:
        raise ValueError("Keep the JSON report separate from the input blend")
    scene = bpy.context.scene
    result = check(scene, bpy.context.evaluated_depsgraph_get())
    with path.open("rb") as source:
        source_sha = file_digest(source, "sha256").hexdigest()
    result.update({"checked_blend": path.name, "blend_sha256": source_sha, "blender": bpy.app.version_string,
                   "frame": scene.frame_current, "minimum_left_group_skin_weight": MIN_WEIGHT,
                   "method": "Euclidean sampled skin-vertex distance to evaluated garments and world-space BVH face overlaps"})
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    if not result["passed"]:
        failed = [name for name, passed in result["checks"].items() if not passed]
        raise AssertionError(f"{', '.join(failed)}. See {args.report}")
    print(f"Verified saved hip hand and garments. See {args.report}")


if __name__ == "__main__":
    main()
