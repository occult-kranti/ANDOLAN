"""Blender CPU probe of groom tips and the game-exported right-hand sockets over five casts.

blender -b -t 1 --python-exit-code 1 -P verify_clearance.py -- INPUT.glb OUTPUT.json
"""

import json
import sys
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree

PACK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACK.parent / "four-hero-motion/tools"))
from blender_stills import load_model, select_pose

sys.path.insert(0, str(PACK.parent.parent / "tools/hanuman-review"))
from audit_glb import Payload
from hashlib import sha256


def points(mesh, obj):
    xyz = np.empty(len(mesh.vertices) * 3, dtype=np.float32)
    mesh.vertices.foreach_get("co", xyz)
    world = np.asarray(obj.matrix_world)
    return xyz.reshape(-1, 3) @ world[:3, :3].T + world[:3, 3]


def collect(source):
    raw = source.read_bytes()
    glb = Payload(raw)
    doc = glb.document
    rig, (obj,) = load_model(source)
    assert (
        bpy.data.objects["gada_grip"].parent_bone == "wrist.R"
        and bpy.data.objects["gada_head"].parent_bone == "wrist.R"
    )
    assert bpy.data.objects["tail_tip"].parent_bone == "tail_04"
    mesh = obj.data
    materials = [m.name for m in mesh.materials]
    originals = [
        tuple(f.vertices)
        for f in mesh.polygons
        if materials[f.material_index].startswith("Vanara · painted copper anatomy")
    ]
    assert originals, "Missing anatomical surface"
    # Select the actual torso and head, excluding the anatomical tail and limbs.
    region = (
        lambda v: sum(
            g.weight
            for g in v.groups
            if obj.vertex_groups[g.group].name.startswith(("spine", "neck", "head", "clavicle", "shoulder"))
        )
        > 0.60
    )
    rest = points(mesh, obj)
    torso_vertex = {
        v.index
        for v in mesh.vertices
        if region(v) or (rest[v.index, 2] > 1.65 and abs(rest[v.index, 0]) < 0.2)
    }
    body_faces = [p for p in originals if all(i in torso_vertex for i in p)]
    tree = KDTree(len(rest))
    for i, p in enumerate(rest):
        tree.insert(p, i)
    tree.balance()
    tips = {}
    mapping_error = 0.0
    for prim in doc["meshes"][0]["primitives"]:
        regions = prim.get("extras", {}).get("studioRegions", [])
        if not regions:
            continue
        raw_xyz = np.asarray(glb.accessor(prim["attributes"]["POSITION"]))
        uv = np.asarray(glb.accessor(prim["attributes"]["TEXCOORD_0"]))
        for region_info in regions:
            name = region_info["name"]
            a = region_info["firstVertex"]
            per = region_info["vertices"] // region_info["clumps"]
            tip_ids = []
            for j in range(region_info["clumps"]):
                start = a + j * per
                section = uv[start : start + per]
                # Pick one point at the terminal ring per individual hair lock.
                idx = start + int(np.argmax(section[:, 1]))
                x, y, z = raw_xyz[idx]
                _, i, d = tree.find((x, -z, y))
                mapping_error = max(mapping_error, d)
                tip_ids.append(i)
            tips[name] = np.asarray(tip_ids, dtype=np.int32)
    assert mapping_error < 0.0001, f"Groom/Blender vertex mapping differs ({mapping_error} m)"
    keynames = ["idle", "fire", "cast2", "cast1", "tail_sweep", "mountain_pulse"]
    findings = {}
    right_ref = []
    shaft_length = []
    for clip in keynames:
        samples = []
        for phase in [0, 0.25, 0.5, 0.75, 1]:
            select_pose(rig, clip, phase)
            deps = bpy.context.evaluated_depsgraph_get()
            model = obj.evaluated_get(deps)
            xyz = points(model.data, model)
            bvh = BVHTree.FromPolygons(xyz, body_faces, all_triangles=True)
            full_skin = BVHTree.FromPolygons(xyz, originals, all_triangles=True)
            root = rig.evaluated_get(deps)
            wrist = root.matrix_world @ root.pose.bones["wrist.R"].matrix
            grip = bpy.data.objects["gada_grip"].evaluated_get(deps).matrix_world.translation.copy()
            head = bpy.data.objects["gada_head"].evaluated_get(deps).matrix_world.translation.copy()
            right_ref.append(list(wrist.inverted_safe() @ grip))
            shaft_length.append((head - grip).length)
            tip = bpy.data.objects["tail_tip"].evaluated_get(deps).matrix_world.translation.copy()
            loc, normal, _, dist = bvh.find_nearest(tip)
            sample = {"phase": phase, "tail_marker_to_torso_m": round(dist, 5), "groom": {}}
            for name, ids in tips.items():
                distances = []
                interior = []
                examples = []
                for p in xyz[ids]:
                    q = Vector(p)
                    hit, n, _, d = bvh.find_nearest(q)
                    signed = d if (q - hit).dot(n) >= 0 else -d
                    distances.append(signed)
                    if signed < -0.01:
                        exits = 0
                        for direction in [
                            (1, 0.071, 0.092),
                            (-1, 0.175, -0.055),
                            (0.12, 1, -0.06),
                            (-0.041, -1, 0.159),
                            (0.11, 0.135, 1),
                            (-0.041, 0.123, -1),
                        ]:
                            ray = Vector(direction).normalized()
                            where, normal, _, _ = full_skin.ray_cast(q, ray)
                            if where is not None and normal.dot(ray) > 0:
                                exits += 1
                        if exits >= 5:
                            interior.append(len(distances) - 1)
                            if len(examples) < 3:
                                examples.append(
                                    {
                                        "clump": len(distances) - 1,
                                        "inside_m": round(-signed, 5),
                                        "exit_directions": exits,
                                    }
                                )
                sample["groom"][name] = {
                    "count": len(ids),
                    "min_signed_m": round(min(distances), 5),
                    "median_signed_m": round(float(np.median(distances)), 5),
                    "tips_inside_over_1cm": sum(d < -0.01 for d in distances),
                    "ray_confirmed_inside": len(interior),
                    "examples": examples,
                }
            samples.append(sample)
        findings[clip] = samples
    grip_drift = float(np.max(np.linalg.norm(np.array(right_ref) - right_ref[0], axis=1)))
    assert (
        grip_drift < 0.0001 and np.ptp(shaft_length) < 0.0001
    ), "Gada socket drifts away from anatomical right wrist"
    return {
        "model_sha256": sha256(raw).hexdigest(),
        "verifier_sha256": sha256(Path(__file__).read_bytes()).hexdigest(),
        "source": source.name,
        "blender": bpy.app.version_string,
        "poses": len(keynames) * 5,
        "criterion": "Outward signed nearest-point distance to skin triangles of torso, neck and head for one terminal-ring point per clump. Distances deeper than 1 cm are checked against six rays on all anatomical skin; at least five first back-face hits support burial. Embedded roots and strand-on-strand contacts are outside this test.",
        "isolated_torso_triangles": len(body_faces),
        "max_correspondence_error_m": mapping_error,
        "right_hand_grip_drift_m": grip_drift,
        "grip_to_gada_head_m": float(np.median(shaft_length)),
        "min_tail_marker_to_torso_m": min(
            p["tail_marker_to_torso_m"] for seq in findings.values() for p in seq
        ),
        "shots": findings,
    }


if __name__ == "__main__":
    source, out = map(Path, sys.argv[sys.argv.index("--") + 1 :])
    receipt = collect(source)
    out.write_text(json.dumps(receipt, indent=2) + "\n")
    print(receipt["source"], receipt["min_tail_marker_to_torso_m"], receipt["right_hand_grip_drift_m"])
