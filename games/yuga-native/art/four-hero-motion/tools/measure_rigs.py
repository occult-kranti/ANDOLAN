"""Blender measurement of four published skinned GLBs. Run blender -b -t 1 -P measure_rigs.py."""

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parents[1]
HEROES = ("hanuman", "rama", "shiva", "krishna")
TRACK = (
    "root",
    "head",
    "wrist.L",
    "wrist.R",
    "finger2-3.L",
    "finger2-3.R",
    "foot.L",
    "foot.R",
    "tail_01",
    "tail_02",
    "tail_03",
    "tail_04",
    "tail_tip",
    "bowstring",
    "gada_grip",
    "gada_head",
    "bansuri",
    "chakra",
)
QUARTERS = (0, 0.25, 0.5, 0.75, 1)


def rnd(x):
    return round(float(x), 5)


def vec(x):
    return [rnd(v) for v in x]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def summary(poses, phases, quarter_indices):
    positions = np.array([p[0] for p in poses])
    distances = np.linalg.norm(positions - positions[0], axis=1)
    quat = np.array([p[1] for p in poses], dtype=float)
    quat /= np.linalg.norm(quat, axis=1, keepdims=True)
    angles = 2 * np.degrees(np.arccos(np.clip(np.abs(quat @ quat[0]), 0, 1)))
    return {
        "range_xyz_m": [vec(positions.min(axis=0)), vec(positions.max(axis=0))],
        "quarter_positions_xyz_m": [vec(positions[i]) for i in quarter_indices],
        "max_from_first_m": rnd(distances.max()),
        "max_phase": rnd(phases[int(distances.argmax())]),
        "end_gap_m": rnd(distances[-1]),
        "max_rotation_from_first_deg": rnd(angles.max()),
        "end_rotation_gap_deg": rnd(angles[-1]),
    }


def cloud(obj, evaluated=False):
    if evaluated:
        obj = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = obj.data
    flat = np.empty(len(mesh.vertices) * 3, dtype=np.float32)
    mesh.vertices.foreach_get("co", flat)
    transform = np.array(obj.matrix_world)
    return flat.reshape(-1, 3) @ transform[:3, :3].T + transform[:3, 3]


def material_indices(obj, name):
    index = next(i for i, m in enumerate(obj.material_slots) if m.name == name)
    return np.array(
        sorted(
            {
                v
                for p in obj.data.polygons
                if p.material_index == index
                for v in p.vertices
            }
        )
    )


def flute_landmarks(body, instruments):
    lip = material_indices(body, "Muted lip vermilion")
    holes = material_indices(instruments, "Indigo black hair")
    rest = cloud(instruments)[holes]
    _, _, axes = np.linalg.svd(rest - rest.mean(axis=0), full_matrices=False)
    along = rest @ axes[0]
    order = np.argsort(along)
    groups = np.split(order, np.nonzero(np.diff(along[order]) > 0.015)[0] + 1)
    if len(groups) != 8:
        raise ValueError(
            f"Expected eight physically distinct tone markers, found {len(groups)}"
        )
    # Reconstruct the source ordering from unequal marker spacings along the bore.
    offsets = np.array([-0.248, -0.195, -0.155, -0.118, -0.078, -0.038, 0.010, 0.061])
    spacing = np.diff([along[g].mean() for g in groups])
    if np.linalg.norm(spacing[::-1] - np.diff(offsets)) < np.linalg.norm(
        spacing - np.diff(offsets)
    ):
        groups.reverse()
    return lip, [(rnd(x), holes[g]) for x, g in zip(offsets, groups, strict=True)]


def sole_landmarks(body):
    rest = cloud(body)
    result = {}
    for side in ("L", "R"):
        names = {
            g.index
            for g in body.vertex_groups
            if g.name == "foot." + side
            or (g.name.startswith("toe") and g.name.endswith("." + side))
        }
        ids = np.array(
            [
                v.index
                for v in body.data.vertices
                if rest[v.index, 2] < 0.15
                and sum(g.weight for g in v.groups if g.group in names) > 0.75
            ]
        )
        if len(ids) == 0:
            raise ValueError(f"No surface vertices for foot {side}")
        low = ids[rest[ids, 2] <= rest[ids, 2].min() + 0.005]
        result[side] = ids, low
    return result


def inspect(hero):
    path = ROOT / "models" / (hero + ".glb")
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.fps = 30
    scene.render.fps_base = 1
    bpy.ops.import_scene.gltf(filepath=str(path))
    (rig,) = [r for r in scene.objects if r.type == "ARMATURE"]
    data = rig.animation_data
    tracks = {t.name: t.strips[0].action for t in data.nla_tracks}
    for t in data.nla_tracks:
        t.mute = True
    # The exporter intentionally stores three non-deforming Hanuman sockets as
    # ordinary glTF nodes. Blender imports these as bone-parented empties.
    helpers = {
        n: scene.objects[n]
        for n in TRACK
        if n in scene.objects and scene.objects[n].type == "EMPTY"
    }
    names = [n for n in TRACK if n in rig.pose.bones or n in helpers]
    bindings = {
        n: ("bone-parented glTF node" if n in helpers else "skin joint") for n in names
    }
    # Rigid visual landmarks share their exported wrist/socket transform. The
    # offsets mirror the authored palm basis in build_models.py (in metres).
    markers = {}
    if hero == "shiva":
        markers["trishula_tip"] = ("wrist.R", Vector((0.920, 0.105, 0.025)))
        markers["trishula_butt"] = ("wrist.R", Vector((-0.800, 0.105, 0.025)))
    if hero == "krishna":
        markers["bansuri_blow"] = ("bansuri", Vector((-0.248, 0.0935, -0.025)))
        markers["chakra_center"] = ("chakra", Vector((0.124, 0.131, 0.025)))
    bindings.update({n: "authored rigid landmark" for n in markers})
    names.extend(markers)

    body = next(
        (o for o in scene.objects if "body and regalia" in o.name.lower()), None
    )
    prop = next(
        (o for o in scene.objects if "signature instruments" in o.name.lower()), None
    )
    lips, holes = flute_landmarks(body, prop) if hero == "krishna" else (None, None)
    foot_sets = sole_landmarks(body) if hero == "shiva" else {}
    rows = {}
    for name, action in sorted(tracks.items()):
        # Prevent partial tracks inheriting a different action's previous sample.
        data.action = None
        for joint in rig.pose.bones:
            joint.matrix_basis = Matrix.Identity(4)
        data.action = action
        start, end = map(float, action.frame_range)
        span = end - start
        if span <= 0:
            raise ValueError(f"{hero}/{name} has no time span")
        # Every 1/30 s of clip time, plus quarter markers and exact endpoint.
        times = sorted(
            {*map(float, range(math.ceil(span))), span, *[span * q for q in QUARTERS]}
        )
        phases = [t / span for t in times]
        quarters = [
            min(range(len(times)), key=lambda i: abs(times[i] - span * q))
            for q in QUARTERS
        ]
        sampled = {n: [] for n in names}
        measured = []
        chakra_scale = []
        for offset in times:
            frame = start + offset
            scene.frame_set(math.floor(frame), subframe=frame % 1)
            graph = bpy.context.evaluated_depsgraph_get()
            evaluated = rig.evaluated_get(graph)
            for n in names:
                if n in helpers:
                    matrix = helpers[n].evaluated_get(graph).matrix_world
                    position = matrix.translation
                elif n in markers:
                    bone, local_point = markers[n]
                    matrix = evaluated.matrix_world @ evaluated.pose.bones[bone].matrix
                    position = matrix @ local_point
                else:
                    matrix = evaluated.matrix_world @ evaluated.pose.bones[n].matrix
                    position = matrix.translation
                sampled[n].append((tuple(position), tuple(matrix.to_quaternion())))
                if n == "chakra":
                    chakra_scale.append(float(matrix.to_scale().x))
            if hero == "krishna" and name == "cast2":
                lip_cloud, markers_cloud = cloud(body, True)[lips], cloud(prop, True)
                separation = [
                    np.sqrt(
                        np.min(
                            np.sum(
                                (markers_cloud[ids, None, :] - lip_cloud[None, :, :])
                                ** 2,
                                axis=2,
                            )
                        )
                    )
                    for _, ids in holes
                ]
                pads = {}
                for side, index in (("L", 6), ("R", 3)):
                    end_joint = evaluated.pose.bones["finger2-3." + side]
                    pad = np.array(
                        evaluated.matrix_world
                        @ end_joint.head.lerp(end_joint.tail, 0.8)
                    )
                    delta = pad - markers_cloud[holes[index][1]].mean(axis=0)
                    pads[side] = rnd(np.linalg.norm(delta))
                measured.append(
                    {
                        "offset_f30": rnd(offset),
                        "lip_to_each_marker_m": vec(separation),
                        "index_pad_to_assigned_marker_center_m": pads,
                    }
                )
            elif hero == "shiva" and name == "cast3":
                deformed = cloud(body, True)
                measured.append(
                    {
                        "offset_f30": rnd(offset),
                        "feet": {
                            side: {
                                "minimum_z_m": rnd(deformed[all_ids, 2].min()),
                                "sole_patch_center_xyz_m": vec(
                                    deformed[low_ids].mean(axis=0)
                                ),
                            }
                            for side, (all_ids, low_ids) in foot_sets.items()
                        },
                    }
                )
        result = {
            "frames_f30": [rnd(start), rnd(end)],
            "seconds": rnd(span / 30),
            "samples": len(times),
            "joints": {
                n: summary(samples, phases, quarters) for n, samples in sampled.items()
            },
        }
        if chakra_scale:
            result["chakra_uniform_scale_range"] = vec(
                (min(chakra_scale), max(chakra_scale))
            )
        if name in ("idle", "run"):
            gaps = {n: result["joints"][n]["end_gap_m"] for n in names}
            angular = {n: result["joints"][n]["end_rotation_gap_deg"] for n in names}
            result["loop_seam"] = {
                "worst_position_joint": max(gaps, key=gaps.get),
                "worst_position_m": max(gaps.values()),
                "worst_orientation_joint": max(angular, key=angular.get),
                "worst_orientation_deg": max(angular.values()),
            }
        if hero == "shiva" and name == "cast3":
            result["sole_contact"] = {
                "rest_vertex_counts": {
                    side: [len(a), len(b)] for side, (a, b) in foot_sets.items()
                },
                "sampled": measured,
            }
        if hero == "krishna" and name == "cast2":
            result["flute_contact"] = {
                "lip_vertices": len(lips),
                "marker_centres_authored_m": [v for v, _ in holes],
                "vertices_per_marker": [len(ids) for _, ids in holes],
                "assigned_marker_indices": {"blow": 0, "L": 6, "R": 3},
                "sampled": measured,
            }
        rows[name] = result
    expected = {"hanuman": 11, "rama": 19, "shiva": 9, "krishna": 9}[hero]
    if len(rows) != expected:
        raise ValueError(f"{hero} expected {expected} actions, found {len(rows)}")
    print(
        "Measured",
        hero,
        len(rows),
        sum(a["samples"] for a in rows.values()),
        flush=True,
    )
    return {"sha256": sha(path), "landmarks": bindings, "actions": rows}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=ROOT / "evidence/rig-motion.json")
    parser.add_argument(
        "--check-contacts",
        action="store_true",
        help="Require a sub-centimetre held blow-hole gap and stable Shiva contact",
    )
    args = parser.parse_args(
        sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    )
    heroes = {h: inspect(h) for h in HEROES}
    meta = {
        "blender": bpy.app.version_string,
        "axes": "Blender world XYZ, Z up, metres. Distal finger joint origins are knuckle landmarks.",
        "sampling": "One sample per 1/30 s plus exact endpoints and quarter times, on the imported active NLA action alone. Every reported orientation uses the shortest unsigned quaternion angle in world space.",
        "landmarks": "Shiva foot floor uses mesh vertices below rest Z 0.15 m with >75% combined foot/toe weights. The sole patch includes the lowest 5 mm in rest. Krishna distances are closest vertex-pair distances between the deformed painted-lip geometry and each of eight rigid dark marker surfaces. Markers are ordered by their exported spacing along the bore. Each index pad is a proxy at 80% along its distal joint, measured to the centre of its assigned marker. Rigid landmark offsets use the authoring geometry.",
        "actions": sum(len(h["actions"]) for h in heroes.values()),
        "poses": sum(
            a["samples"] for h in heroes.values() for a in h["actions"].values()
        ),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as out:
        out.write(
            '{\n  "method": '
            + json.dumps(meta, ensure_ascii=False)
            + ',\n  "heroes": {\n'
        )
        for i, (name, record) in enumerate(heroes.items()):
            out.write(
                "    "
                + json.dumps(name)
                + ': {"sha256": '
                + json.dumps(record["sha256"])
                + ', "landmarks": '
                + json.dumps(record["landmarks"])
                + ', "actions": {\n'
            )
            for j, (clip, result) in enumerate(record["actions"].items()):
                out.write(
                    "      "
                    + json.dumps(clip)
                    + ": "
                    + json.dumps(result, separators=(",", ":"), allow_nan=False)
                )
                out.write(",\n" if j < len(record["actions"]) - 1 else "\n")
            out.write("    }}" + (",\n" if i < len(heroes) - 1 else "\n"))
        out.write("  }\n}\n")
    print(meta["actions"], "actions", meta["poses"], "poses", flush=True)
    if args.check_contacts:
        flute = heroes["krishna"]["actions"]["cast2"]["flute_contact"]["sampled"]
        held = [p for p in flute if 6 <= p["offset_f30"] <= 17]
        if len(held) < 12 or max(p["lip_to_each_marker_m"][0] for p in held) >= 0.01:
            raise ValueError(
                "Krishna's blow hole separates from the lips during the held phrase"
            )
        feet = heroes["shiva"]["actions"]["cast3"]["sole_contact"]["sampled"]
        planted = [p["feet"] for p in feet if p["offset_f30"] >= 24]
        for side in ("L", "R"):
            contact = planted[0][side]["sole_patch_center_xyz_m"][:2]
            if any(
                p[side]["minimum_z_m"] < 0
                or p[side]["minimum_z_m"] > 0.02
                or math.dist(contact, p[side]["sole_patch_center_xyz_m"][:2]) > 0.002
                for p in planted
            ):
                raise ValueError(f"Shiva loses planted {side} contact after F24")


main()
