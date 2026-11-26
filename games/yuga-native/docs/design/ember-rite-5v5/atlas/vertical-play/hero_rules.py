"""Check the hero profiles with Python or remeasure their four skinned GLBs in Blender.

Run python3 hero_rules.py for numerical/source checks. To measure actual rest vertices:
OPENBLAS_NUM_THREADS=1 blender -b -t 1 --python-exit-code 1 -P hero_rules.py -- --measure
"""

import hashlib
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
NATIVE = HERE.parents[4]
RUST = NATIVE.parent / "yuga-rust"
FILE = HERE / "heroes.json"
EMBER = {
    "arjuna",
    "hanuman",
    "kali",
    "krishna",
    "durga",
    "karna",
    "shakuni",
    "ravana",
    "ghatotkacha",
    "draupadi",
}


def load():
    return json.loads(FILE.read_text())


def xz_distance(a, b):
    return math.dist(a, b)


def reach(length, pitch_deg):
    """Horizontal reach and change in elevation in a straight unobstructed trajectory."""
    a = math.radians(pitch_deg)
    return length * math.cos(a), length * math.sin(a)


def first_contact_counts(outbound, returning):
    """Expected first-contact order for distinct targets; a blocked leg ends upstream."""
    return tuple(dict.fromkeys((*outbound, *returning)))


def check(data):
    rows = data["heroes"]
    by_id = {row["id"]: row for row in rows}
    assert len(rows) == len(by_id) == 12
    assert {row["id"] for row in rows if row["scope"].startswith("ember_ten")} == EMBER
    assert by_id["rama"]["scope"] == "live_additional"
    assert by_id["shiva"]["scope"] == "motion_appendix"
    rig = data["field_rig"]["common"]
    assert (
        rig["standing_eye_m"] < rig["standing_height_m"]
        and rig["crouch_eye_m"] < rig["crouch_height_m"] < rig["standing_height_m"]
    )
    assert rig["route_clearance_radius_m"] >= rig["hurt_radius_m"]
    rules = data["profiles"]
    assert {row["primary_profile"] for row in rows} == set(rules)
    for row in rows:
        assert row["field_rig"] == "common" and all(
            row[k] for k in ("counter", "first_choice", "alternate")
        )
        profile = rules[row["primary_profile"]]
        assert profile["max_reach_m"] > 0 and profile["cooldown_s"] > 0 and profile["windup_s"] >= 0
        assert 0 <= profile["standing_release_m"] <= rig["standing_height_m"]
    bow = json.loads((NATIVE / "assets/design/rama-ability-kit.json").read_text())["abilities"][0]
    assert bow["id"] == "kodanda"
    for live_key, source_key in [
        ("max_reach_m", "range_m"),
        ("cooldown_s", "cooldown_s"),
        ("speed_mps", "speed_mps"),
        ("radius_m", "radius_m"),
        ("windup_s", "windup_s"),
        ("damage", "damage"),
    ]:
        assert rules["kodanda"][live_key] == bow[source_key]
    muzzle = json.loads((RUST / "assets/rama-muzzles.json").read_text())["kodanda"][1]
    assert math.isclose(rules["kodanda"]["standing_release_m"], muzzle, abs_tol=1e-8)
    for actor, info in data["measured_glbs"].items():
        src = NATIVE / info["source"]
        assert hashlib.sha256(src.read_bytes()).hexdigest() == info["sha256"], f"{actor} GLB changed"
        assert abs(info["skin"]["dx_dy_dz"][2] - by_id[actor]["art_body_target_m"]) < 1e-4


def measure(data):
    """Compare all evaluated, rigged vertices in world space; helpers and cameras are excluded."""
    import bpy
    import numpy as np

    def bounds(parts):
        vertices = np.concatenate(parts)
        low, high = vertices.min(axis=0), vertices.max(axis=0)
        return {"min": low, "max": high, "dx_dy_dz": high - low, "vertices": len(vertices)}

    for name, source in data["measured_glbs"].items():
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.import_scene.gltf(filepath=str(NATIVE / source["source"]), import_pack_images=False)
        for obj in bpy.context.scene.objects:
            if obj.animation_data:
                obj.animation_data_clear()
            if obj.type == "ARMATURE":
                obj.data.pose_position = "REST"
        bpy.context.view_layer.update()
        graph = bpy.context.evaluated_depsgraph_get()
        full, skin = [], []
        for obj in bpy.context.scene.objects:
            if obj.type != "MESH" or not obj.find_armature():
                continue
            obj = obj.evaluated_get(graph)
            mesh = obj.to_mesh()
            try:
                vertices = np.empty(len(mesh.vertices) * 3, dtype=np.float32)
                mesh.vertices.foreach_get("co", vertices)
                transform = np.asarray(obj.matrix_world)
                world = vertices.reshape(-1, 3) @ transform[:3, :3].T + transform[:3, 3]
                full.append(world)
                selected = {
                    i for i, m in enumerate(mesh.materials) if m and m.name == source["skin_material"]
                }
                skin_ids = {
                    i for poly in mesh.polygons if poly.material_index in selected for i in poly.vertices
                }
                if skin_ids:
                    skin.append(world[list(skin_ids)])
            finally:
                obj.to_mesh_clear()
        for label, parts in (("all", full), ("skin", skin)):
            found, expected = bounds(parts), source[label]
            assert found["vertices"] == expected["vertices"], f"{name} {label} vertex count"
            for axis in ("min", "max", "dx_dy_dz"):
                assert np.allclose(found[axis], expected[axis], rtol=0, atol=0.00006), (
                    name,
                    label,
                    axis,
                )
            print(
                f"{name} {label}: {found['vertices']} evaluated vertices, height {found['dx_dy_dz'][2]:.4f} m"
            )


if __name__ == "__main__":
    profiles = load()
    check(profiles)
    if "--measure" in sys.argv:
        measure(profiles)
    print("Twelve entries, four model sources and the released bow profile verified.")
