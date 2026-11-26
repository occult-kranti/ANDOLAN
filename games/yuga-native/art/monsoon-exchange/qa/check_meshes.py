"""Reopen the shipped .blend and independently read its GLB, then sample both real scenes.

OPENBLAS_NUM_THREADS=1 blender -b -t 1 --factory-startup --python-exit-code 1 \
  --python games/yuga-native/art/monsoon-exchange/qa/check_meshes.py -- --check
"""

import argparse
from hashlib import sha256
import json
from math import dist
from pathlib import Path
import sys

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
from mesh_io import Gltf, native_proxies, native_scene, need  # noqa: E402
from walks import (  # noqa: E402
    DOWN,
    WalkGrid,
    blockers,
    printed_pins,
    objective_ring,
    probes,
    supported,
)
from visual_paths import visible_corridors  # noqa: E402


def hashed(file):
    return sha256(file.read_bytes()).hexdigest()


def patch_registration(scene, geometry):
    owners = {p["owner"] for p in geometry["floors"]}
    need(
        owners == scene.owners["floor"],
        f"Actual floor owners differ: {owners ^ scene.owners['floor']}",
    )
    max_height = 0.0
    hits = 0
    for patch in geometry["floors"]:
        vertices = patch["vertices"]
        center = tuple(sum(p[i] for p in vertices) / len(vertices) for i in range(3))
        # Pull each corner toward the centre; neighbours touch exactly at the seam.
        anchors = [center] + [
            tuple(0.94 * v + 0.06 * c for v, c in zip(vertex, center))
            for vertex in vertices
        ]
        for x, y, z in anchors:
            hit = scene.floor.ray((x, y, z + 0.4), DOWN, 0.8)
            need(
                hit and hit[2] == patch["owner"],
                f"Incorrect floor registration at {patch['id']} {x:.3f},{y:.3f}",
            )
            error = abs(hit[0].z - z)
            max_height = max(max_height, error)
            hits += 1
            need(
                error < 0.002 and hit[1].z > 0.76,
                f"Survey floor displaced by {error:.4f} m at {patch['id']}",
            )
    tested = 0
    for wall in geometry["walls"]:
        a, b = wall["a"], wall["b"]
        nx, ny = wall["outward"]
        x, y, z = ((a[k] + b[k]) / 2 for k in range(3))
        # Test the walking skin independently of visibility art or ground foundation.
        inside = scene.floor.ray((x - 0.12 * nx, y - 0.12 * ny, z + 0.5), DOWN, 1.0)
        outside = scene.floor.ray((x + 0.12 * nx, y + 0.12 * ny, z + 0.5), DOWN, 1.0)
        need(
            inside and not outside,
            f"Exterior boundary is open or floor leaks through {wall['id']}",
        )
        # Two wall foundations can meet on a thin return and have coplanar
        # front faces. Shoot the surveyed wall itself so both must exist.
        need(wall["id"] in scene.walls, f"Missing modeled wall ID {wall['id']}")
        strike = scene.walls[wall["id"]].ray(
            (x - 0.12 * nx, y - 0.12 * ny, z + 0.25), (nx, ny, 0), 0.8
        )
        need(
            strike and strike[2] == wall["owner"],
            f"Surveyed wall {wall['id']} is missing from the render geometry",
        )
        tested += 1
    return {
        "floor_patches": len(geometry["floors"]),
        "room_and_corridor_owners": len(owners),
        "interior_height_witnesses": hits,
        "max_error_m": round(max_height, 6),
        "outside_misses_paired_with_inside_hits": tested,
        "actual_wall_face_hits_25cm_above_floor": tested,
    }


def cameras(scene, geometry, rules):
    stage = bpy.context.scene
    markers = {item.name: item.camera for item in stage.timeline_markers}
    specs = {
        "north-up": (1180, 1260),
        "overview": (1500, 1110),
        "sun-court": (1280, 800),
        "indigo-cistern": (1280, 800),
        "weavers-gate": (1280, 800),
    }
    need(
        set(markers) == set(specs),
        "The five rendered views have no matching native camera cuts",
    )
    output = {}
    render = stage.render
    size = render.resolution_x, render.resolution_y
    try:
        for ident, (width, height) in specs.items():
            cam = markers[ident]
            need(
                cam and cam.name == "CAM." + ident,
                "Unregistered camera in native scene",
            )
            rotation = cam.matrix_world.to_quaternion()
            heading = rotation @ Vector((0, 0, -1))
            up = rotation @ Vector((0, 1, 0))
            loc = cam.matrix_world.translation
            render.resolution_x, render.resolution_y = width, height
            if ident in ("north-up", "overview"):
                need(cam.data.type == "ORTHO", "Broken map overview lens")
                corners = [
                    world_to_camera_view(stage, cam, Vector(v))
                    for patch in geometry["floors"]
                    for v in patch["vertices"]
                ]
                margin = min(min(v.x, v.y, 1 - v.x, 1 - v.y) for v in corners)
                need(
                    margin > 0 and min(v.z for v in corners) > 0,
                    "Overview clips playable floor",
                )
                if ident == "north-up":
                    need(
                        heading.z < -0.9999 and up.y > 0.9999,
                        "Plan camera rotates or flips the surveyed district",
                    )
                else:
                    need(
                        -0.95 < heading.z < -0.1,
                        "District overview must show relief obliquely",
                    )
                output[ident] = {
                    "floor_corners_in_frame": len(corners),
                    "minimum_frame_margin_percent": round(100 * margin, 2),
                }
            else:
                foot = scene.floor.ray((loc.x, loc.y, 40.0), DOWN, 80.0)
                need(
                    foot and cam.data.type == "PERSP",
                    f"{ident} viewpoint lost its walking floor or perspective lens",
                )
                standing_eye = loc.z - foot[0].z
                need(
                    abs(standing_eye - rules["standing_eye_m"]) < 0.02,
                    f"{ident} camera differs from a standing player eye",
                )
                output[ident] = {
                    "eye_above_floor_m": round(standing_eye, 4),
                    "lens_mm": cam.data.lens,
                }
    finally:
        render.resolution_x, render.resolution_y = size
    return output


def check_pads(scene, data):
    result = {}
    for spawn in data["spawns"]:
        pads = spawn["pads"]
        radius = data["rules"]["clearance_radius_m"]
        need(len(pads) == 5, f"Expected five selectable starting pads at {spawn['id']}")
        spacing = min(dist(a, b) for i, a in enumerate(pads) for b in pads[:i])
        need(spacing >= 2 * radius, "Intersecting players at spawn")
        need(
            all(supported(scene, p, data["rules"]) for p in pads),
            "Spawn blocked, or feet unsupported",
        )
        result[spawn["id"]] = {
            "legal_standing_pads": len(pads),
            "minimum_pair_distance_m": round(spacing, 3),
        }
    return result


def one(scene, data, geometry, pins):
    registration = patch_registration(scene, geometry)
    track, widths, heights = probes(scene, data)
    result = {
        "scene": scene.details,
        "mesh_objects_by_role": dict(sorted(scene.roles.items())),
        "triangle_counts_for_probe_roles": {
            k: scene.triangles[k] for k in ("floor", "wall", "cover", "ceiling")
        },
        "registration": registration,
        "corridors": track,
        "site_lips": widths,
        "spawn_pads": check_pads(scene, data),
        "site_disks": objective_ring(scene, data),
        "cover_sightlines": blockers(scene, data),
        "printed_pin_sightlines": printed_pins(scene, data, pins),
        "connectivity": WalkGrid(scene, data).gates(),
    }
    return result, heights


def run(folder):
    source = ROOT / "plan/survey.json"
    geometry_path = ROOT / "plan/geometry.json"
    blend = folder / "monsoon-exchange.blend"
    glb = folder / "monsoon-exchange.glb"
    metrics_path = ROOT / "plan/metrics.json"
    pins = json.loads(metrics_path.read_bytes())["shelter_witnesses"]
    data = json.loads(source.read_bytes())
    geometry = json.loads(geometry_path.read_bytes())
    # Read the common YUGA hero rig to prevent a relaxed radius passing this map in isolation.
    rig_path = (
        ROOT.parents[1] / "docs/design/ember-rite-5v5/atlas/vertical-play/heroes.json"
    )
    rig = json.loads(rig_path.read_bytes())["field_rig"]["common"]
    rules = data["rules"]
    need(
        rules["teams"] == len(data["spawns"]) == 2
        and rules["team_size"] == 5
        and rules["waves"] is False,
        "Map lacks the two five-player deployment groups",
    )
    need(
        {site["room"] for site in data["objectives"]} == {"a", "b"},
        "Both ritual courts are required",
    )
    need(
        [sum(e["site"] == which for e in data["entries"]) for which in ("a", "b")]
        == [4, 3],
        "Survey entrance count differs from reviewed site plates",
    )
    need(
        (
            rules["clearance_radius_m"],
            rules["standing_height_m"],
            rules["standing_eye_m"],
        )
        == (
            rig["route_clearance_radius_m"],
            rig["standing_height_m"],
            rig["standing_eye_m"],
        ),
        "Map rig differs from the existing standing rig",
    )
    blender_meshes = native_scene(blend)
    native, z1 = one(blender_meshes, data, geometry, pins)
    native["authoring_guides"] = native_proxies(data)
    native["camera_registration"] = cameras(blender_meshes, geometry, rules)
    native["visible_path_traces"] = visible_corridors(blender_meshes, data)
    del blender_meshes
    gltf_meshes = Gltf(glb).scene()
    exported, z2 = one(gltf_meshes, data, geometry, pins)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(glb))
    exported["visible_path_traces"] = visible_corridors(gltf_meshes, data)
    need(len(z1) == len(z2) and len(z1) > 0, "Different centre/cross-track sampling")
    dz = max(abs(a - b) for a, b in zip(z1, z2))
    need(
        dz < 0.002,
        "The GLB floor disagrees with the actual native scene by two millimetres or more",
    )
    need(
        {r: n for r, n in native["mesh_objects_by_role"].items() if r != "studio"}
        == exported["mesh_objects_by_role"],
        "Export missed visible Blender artwork",
    )
    for k in (
        "connectivity",
        "visible_path_traces",
        "printed_pin_sightlines",
        "spawn_pads",
        "site_disks",
        "site_lips",
        "cover_sightlines",
    ):
        need(
            native[k] == exported[k],
            "Independent source/export witnesses disagree: " + k,
        )
    return {
        "schema": 1,
        "map": data["title"],
        "result": "pass",
        "blender": bpy.app.version_string,
        "units": "metres",
        "body": {
            "standing_height": rules["standing_height_m"],
            "radius": rules["clearance_radius_m"],
            "eye": rules["standing_eye_m"],
        },
        "source_sha256": {
            "survey.json": hashed(source),
            "geometry.json": hashed(geometry_path),
            "metrics.json": hashed(metrics_path),
            "field-rig": hashed(rig_path),
            blend.name: hashed(blend),
            glb.name: hashed(glb),
        },
        "native": native,
        "glb": exported,
        "comparison": {
            "matched_cross_track_heights": len(z1),
            "max_native_glb_height_delta_m": round(dz, 6),
            "district_sites": len(data["objectives"]),
            "declared_gates": len(data["entries"]),
            "studio_only_meshes_excluded_from_glb": native["mesh_objects_by_role"].get(
                "studio", 0
            ),
            "assigned_shelters": sum(len(e["covers"]) for e in data["entries"]),
        },
        "scope": "Static floor and model geometry, two observer positions per site entrance, and a 0.75 m four-neighbour standing grid. Runtime collision, dynamic hero movement, player camera obstruction and 5v5 results require gameplay tests.",
    }


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--scene", type=Path, default=ROOT / "scene")
    cli.add_argument("--output", type=Path, default=HERE / "geometry-verification.json")
    cli.add_argument(
        "--check",
        action="store_true",
        help="Recompute and compare to the checked-in review",
    )
    a = cli.parse_args(sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else [])
    result = run(a.scene)
    payload = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if a.check:
        need(
            a.output.read_text() == payload,
            "Verification receipt changed. Inspect actual scene changes before recording a new result.",
        )
    else:
        a.output.write_text(payload)
    print(json.dumps(result["comparison"]))


if __name__ == "__main__":
    main()
