"""Independently reopen and measure the editable Hanuman keyframe in Blender."""

from __future__ import annotations

import argparse
from hashlib import file_digest, sha256
import json
import math
from pathlib import Path
from statistics import median
import sys

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector
from mathutils.kdtree import KDTree


ART = Path(__file__).resolve().parents[2] / "art" / "hanuman"
BODY_PREFIX = "Hanuman · contiguous skinned anatomy"
GROUND_PREFIX = "Court ground ·"
KEYFRAME_CLIPS = {"cast", "cast1", "cast2", "cast3", "defeat", "fire", "idle", "jump", "mountain_pulse", "run", "tail_sweep"}
REST_MIDLINE_M = 0.001
REST_MIN_SAMPLES_PER_SIDE = 100
REST_P95_TOLERANCE_MM = 0.1
REST_MAX_TOLERANCE_MM = 0.5


def digest(path):
    with path.open("rb") as handle:
        return file_digest(handle, "sha256").hexdigest()


def r5_contract(rig):
    bones = [(bone.name, bone.parent.name if bone.parent else None, bone.use_deform,
              tuple(tuple(row) for row in bone.matrix_local)) for bone in rig.data.bones]
    actions = {}
    for action in bpy.data.actions:
        curves = []
        for curve in action.fcurves:
            keys = [(tuple(key.co), tuple(key.handle_left), tuple(key.handle_right),
                     key.handle_left_type, key.handle_right_type, key.interpolation,
                     key.easing, key.amplitude, key.back, key.period) for key in curve.keyframe_points]
            modifiers = [(modifier.type, modifier.mute) for modifier in curve.modifiers]
            samples = [tuple(point.co) for point in curve.sampled_points]
            curves.append((curve.data_path, curve.array_index, curve.extrapolation, curve.mute,
                           modifiers, samples, keys))
        markers = [(marker.name, marker.frame) for marker in action.pose_markers]
        playback = (action.use_cyclic, action.use_frame_range, tuple(action.frame_range))
        serialized = json.dumps((playback, markers, curves), separators=(",", ":"))
        actions[action.name] = sha256(serialized.encode()).hexdigest()
    return {"bones": len(bones), "rest_hierarchy_hash": sha256(json.dumps(bones).encode()).hexdigest(),
            "action_key_hashes": actions}


def screen_point(scene, point):
    screen = world_to_camera_view(scene, scene.camera, point)
    return tuple(round(value, 6) for value in (screen.x, 1 - screen.y, screen.z))


def hero_bounds(scene, rig, graph):
    min_x = min_y = math.inf
    max_x = max_y = -math.inf
    behind = vertices = objects = 0
    # Reuse the fixed perspective camera frame across every posed mesh.
    inv = scene.camera.matrix_world.normalized().inverted()
    frame = scene.camera.data.view_frame(scene=scene)
    x0, x1 = min(v.x / -v.z for v in frame), max(v.x / -v.z for v in frame)
    y0, y1 = min(v.y / -v.z for v in frame), max(v.y / -v.z for v in frame)
    for mesh in scene.objects:
        if mesh.type != "MESH" or mesh.hide_render:
            continue
        if not (mesh.parent == rig or any(m.type == "ARMATURE" and m.object == rig for m in mesh.modifiers)):
            continue
        obj = mesh.evaluated_get(graph)
        if not obj.data.vertices:
            continue
        objects += 1
        matrix = inv @ obj.matrix_world
        for vertex in obj.data.vertices:
            point = matrix @ vertex.co
            if point.z >= 0:
                behind += 1
                continue
            vertices += 1
            x = (point.x / -point.z - x0) / (x1 - x0)
            y = 1 - (point.y / -point.z - y0) / (y1 - y0)
            min_x, min_y = min(min_x, x), min(min_y, y)
            max_x, max_y = max(max_x, x), max(max_y, y)
    return {"visible_weighted_objects": objects, "projected_vertices": vertices,
            "vertices_behind_camera": behind,
            "left_top_right_bottom_uv": [round(v, 6) for v in (min_x, min_y, max_x, max_y)]}


def support_surface(point, surfaces):
    start = point + Vector((0, 0, 0.35))
    hits = []
    for floor in surfaces:
        matrix = floor.matrix_world
        inverse = matrix.inverted()
        local = inverse @ start
        down = inverse.to_3x3() @ Vector((0, 0, -1))
        found, local_hit, _, _ = floor.ray_cast(local, down, distance=0.55 * down.length)
        if found:
            hits.append(((matrix @ local_hit).z, floor.name))
    return max(hits) if hits else None


def foot_support(scene, rig, source, graph):
    evaluated = source.evaluated_get(graph)
    coords = [evaluated.matrix_world @ vertex.co for vertex in evaluated.data.vertices]
    surfaces = [obj.evaluated_get(graph) for obj in scene.objects if obj.type == "MESH"
                and obj.name.startswith(GROUND_PREFIX) and not obj.hide_render]
    feet = {"L": [], "R": []}
    for side in feet:
        anchor = rig.matrix_world @ rig.pose.bones[f"foot.{side}"].head
        near = sorted((coord for coord in coords if abs(coord.x - anchor.x) < .16
                       and abs(coord.y - anchor.y) < .33 and coord.z < anchor.z + .02), key=lambda p: p.z)
        for point in near[:16]:
            surface = support_surface(point, surfaces)
            if surface:
                floor_z, floor = surface
                feet[side].append({"point_m": list(point), "floor_m": floor_z, "floor_object": floor,
                                   "gap_m": round(point.z - floor_z, 6)})
    return feet


def rest_anatomy_symmetry(rig, body):
    """Measure reflected nearest neighbors on the unposed donor anatomy only."""
    into_rig = rig.matrix_world.inverted() @ body.matrix_world
    coords = [into_rig @ vertex.co for vertex in body.data.vertices]
    regions = {
        "head": lambda p: p.z >= 1.72 and abs(p.x) < 0.21,
        "torso": lambda p: 1.24 < p.z < 1.68 and abs(p.x) < 0.25,
        "lower_legs": lambda p: 0.105 < p.z < 0.49 and 0.12 < abs(p.x) < 0.36,
    }
    summary = {}
    for name, contains in regions.items():
        points = [point for point in coords if contains(point)]
        positive = [point for point in points if point.x > REST_MIDLINE_M]
        negative = [point for point in points if point.x < -REST_MIDLINE_M]
        errors_mm = []
        if positive and negative:
            for side, opposite in ((positive, negative), (negative, positive)):
                tree = KDTree(len(opposite))
                for index, point in enumerate(opposite):
                    tree.insert(point, index)
                tree.balance()
                for point in side:
                    _, _, distance = tree.find(Vector((-point.x, point.y, point.z)))
                    errors_mm.append(distance * 1000)
        errors_mm.sort()
        p95 = errors_mm[math.ceil(0.95 * len(errors_mm)) - 1] if errors_mm else None
        maximum = errors_mm[-1] if errors_mm else None
        passed = (min(len(positive), len(negative)) >= REST_MIN_SAMPLES_PER_SIDE
                  and p95 <= REST_P95_TOLERANCE_MM and maximum <= REST_MAX_TOLERANCE_MM)
        summary[name] = {"sample_count": len(points), "positive_x_samples": len(positive),
                         "negative_x_samples": len(negative), "midline_samples": len(points) - len(positive) - len(negative),
                         "directed_pairs": len(errors_mm), "median_mm": round(median(errors_mm), 6) if errors_mm else None,
                         "p95_mm": round(p95, 6) if p95 is not None else None,
                         "maximum_mm": round(maximum, 6) if maximum is not None else None, "passed": passed}
    return {"method": "nearest opposite rest vertex after reflection across armature-local X=0, both directions",
            "mesh": body.name, "mesh_vertices": len(coords), "midline_band_m": REST_MIDLINE_M,
            "minimum_samples_per_side": REST_MIN_SAMPLES_PER_SIDE, "p95_tolerance_mm": REST_P95_TOLERANCE_MM,
            "maximum_tolerance_mm": REST_MAX_TOLERANCE_MM, "regions": summary}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, default=ART / "hanuman.blend")
    parser.add_argument("--reference", type=Path, default=ART / "lookdev" / "hanuman-imagegen-reference.png")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    path = Path(bpy.data.filepath).resolve()
    scene = bpy.context.scene
    rig = scene.objects.get("YugaHeroRig")
    if not rig or not scene.camera or scene.camera.data.type != "PERSP":
        raise ValueError("Open a keyframe blend containing YugaHeroRig and its perspective shot camera")
    body = next(obj for obj in scene.objects if obj.type == "MESH" and obj.name.startswith(BODY_PREFIX))
    graph = bpy.context.evaluated_depsgraph_get()
    reference_sha = digest(args.reference)
    source_sha = digest(args.baseline)
    files = []
    for image in bpy.data.images:
        if image.source not in ("FILE", "TILED", "SEQUENCE", "MOVIE"):
            continue
        packed_bytes = [pack.packed_file.data for pack in image.packed_files] or (
            [image.packed_file.data] if image.packed_file else [])
        files.append({"name": image.name, "file": Path(image.filepath).name,
                      "packed_sha256": [sha256(p).hexdigest() for p in packed_bytes],
                      "source": image.source})
    bounds = hero_bounds(scene, rig, graph)
    contacts = foot_support(scene, rig, body, graph)
    symmetry = rest_anatomy_symmetry(rig, body)
    gap_summary = {side: {"samples": len(items), "minimum_gap_m": min((p["gap_m"] for p in items), default=None),
                          "maximum_gap_m": max((p["gap_m"] for p in items), default=None)}
                   for side, items in contacts.items()}
    limbs = {name: screen_point(scene, rig.matrix_world @ rig.pose.bones[name].head)
             for name in ("head", "foot.R", "foot.L", "lowerarm01.R", "lowerarm01.L", "wrist.R", "wrist.L")}
    contract = r5_contract(rig)
    result = {"checked_blend": str(path), "blend_sha256": digest(path), "blender": bpy.app.version_string,
              "scene": scene.name, "resolution": [scene.render.resolution_x, scene.render.resolution_y],
              "renderer": scene.render.engine, "view_transform": scene.view_settings.view_transform,
              "render_features": {"compositor_active": scene.use_nodes, "dof": scene.camera.data.dof.use_dof,
                                  "normal_pass": scene.view_layers[0].use_pass_normal, "depth_pass": scene.view_layers[0].use_pass_z},
              "baseline_sha256": source_sha, "reference_sha256": reference_sha,
              "contract": contract, "file_images": files, "external_libraries": len(bpy.data.libraries),
              "contacts": contacts, "gap_summary": gap_summary, "rest_anatomy_symmetry": symmetry,
              "hero_bounds": bounds, "limb_image_uv_depth": limbs}
    checks = {"candidate_pins_source": scene.get("hanuman_source_sha256") == source_sha,
              "candidate_pins_reference": scene.get("hanuman_reference_sha256") == reference_sha,
              "images_packed_no_libraries": all(f["packed_sha256"] for f in files) and not result["external_libraries"],
              "reference_not_a_packed_render_source": all(reference_sha not in f["packed_sha256"]
                  and Path(f["file"]).stem != args.reference.stem for f in files),
              "uncomposited_cycles_scene": scene.render.engine == "CYCLES" and not scene.use_nodes,
              "both_feet_sampled": all(summary["samples"] >= 8 for summary in gap_summary.values()),
              "rest_anatomy_bilateral_samples_match": all(region["passed"] for region in symmetry["regions"].values()),
              "pose_geometry_projected": bounds["projected_vertices"] > 10000 and not bounds["vertices_behind_camera"],
              "expected_167_bones_and_11_clips": contract["bones"] == 167 and set(contract["action_key_hashes"]) == KEYFRAME_CLIPS}
    # The exact source rest transforms and action keys remain a separate check
    # from the new world-space pose or above-ground contact measurements.
    bpy.ops.wm.open_mainfile(filepath=str(args.baseline.resolve()), load_ui=False)
    checks["r5_rest_and_actions_match_exactly"] = contract == r5_contract(bpy.context.scene.objects["YugaHeroRig"])
    result["checks"] = checks
    result["passed"] = all(checks.values())
    args.report.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    if not result["passed"]:
        raise AssertionError(f"Check failed. See {args.report}")
    print(json.dumps({"report": str(args.report), "checks": sum(checks.values()), "foot_gaps": gap_summary,
                      "hero_bounds": bounds["left_top_right_bottom_uv"]}))


if __name__ == "__main__":
    main()
