"""Raycast the exported GLBs in Blender. See massing/sightlines.md to reproduce."""

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parent
MAPS = ("mandala", "lanka", "ayodhya", "kurukshetra")
EYE_HEIGHTS = (0.9, 1.7, 2.8)
METRE_TOLERANCE = 0.02


def require(condition, message):
    if not condition:
        raise ValueError(message)


def checksum(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def assert_position(actual, expected, label):
    require(len(actual) == len(expected) and all(
        math.isfinite(v) and abs(v - t) <= METRE_TOLERANCE for v, t in zip(actual, expected)
    ), f"{label}: found {tuple(actual)}, expected {tuple(expected)}")


def plan_position(point, elevation):
    # Plan north is +Z in drawing space; glTF stores it as −Z, Blender as +Y.
    return Vector((point[0], point[1], elevation))


def ground_reader(floor, graph):
    mesh_obj = floor.evaluated_get(graph)
    matrix = mesh_obj.matrix_world
    vertices = [matrix @ v.co for v in mesh_obj.data.vertices]
    faces = [p.vertices[:] for p in mesh_obj.data.polygons]
    tree = BVHTree.FromPolygons(vertices, faces)
    ceiling = max(v.z for v in vertices) + 1
    depth = ceiling - min(v.z for v in vertices) + 1

    def floor_at(point):
        hit, normal, _, _ = tree.ray_cast(plan_position(point, ceiling), Vector((0, 0, -1)), depth)
        require(hit is not None and abs(normal.z) > 0.05,
                f"{floor.name}: no top surface beneath {point}")
        return hit.z

    return floor_at


def verify_placement(data, source, floor, graph, ground):
    require(floor.get("source_sha256") == checksum(source), f"{source.name}: stale model source")
    require(floor.get("map_id") == data["id"] and floor.get("units") == "metres", "map or unit mismatch")
    scene = bpy.context.scene
    anchors = [o for o in scene.objects if o.get("kind") == "room_anchor"]
    by_id = {o.get("room_id"): o for o in anchors}
    require(len(anchors) == len(by_id) and set(by_id) == set(data["nodes"]), "room anchors differ")
    for room_id, node in data["nodes"].items():
        expected = plan_position(node["xz"], node["y"])
        assert_position(by_id[room_id].matrix_world.translation, expected, node["label"] + " anchor")
        assert_position([ground(node["xz"])], [node["y"]], node["label"] + " floor")
    covers = {o.name: o for o in scene.objects if o.type == 'MESH' and o.get("kind") == "authored_cover"}
    require(set(covers) == {c["label"] for c in data["cover"]}, "cover objects differ")
    tops = {}
    for item in data["cover"]:
        obj = covers[item["label"]].evaluated_get(graph)
        vertices = [obj.matrix_world @ p.co for p in obj.data.vertices]
        x, y = item["xz"]
        width, depth = item["size"]
        assert_position((min(p.x for p in vertices), min(p.y for p in vertices),
                         max(p.x for p in vertices), max(p.y for p in vertices)),
                        (x - width/2, y - depth/2, x + width/2, y + depth/2), obj.name + " footprint")
        tops[obj.name] = max(p.z for p in vertices)
        assert_position([tops[obj.name]], [ground(item["xz"]) + item["height"]], obj.name + " top")
    return tops


def first_surface(start, target, graph):
    # Exclude only the mathematical segment ends to avoid self-hits at shared vertices.
    delta = target - start
    direction = delta.normalized()
    trim = 0.0001
    require(delta.length > 2*trim, "coincident sightline endpoints")
    hit, pos, _, face, obj, _ = bpy.context.scene.ray_cast(
        graph, start + direction*trim, direction, distance=delta.length - 2*trim)
    if not hit:
        return "Clear", None
    if obj.get("kind") == "atlas_floor":
        mesh = obj.evaluated_get(graph).data
        slot = mesh.polygons[face].material_index
        name = "Floor (" + mesh.materials[slot].name + ")"
    else:
        name = obj.name
    return name, (pos - start).length


def cast_pair(probe, ground, graph):
    a = plan_position(probe["from"], ground(probe["from"]))
    b = plan_position(probe["to"], ground(probe["to"]))
    results = []
    for height in EYE_HEIGHTS:
        eye = Vector((0, 0, height))
        results.append((first_surface(a + eye, b + eye, graph),
                        first_surface(b + eye, a + eye, graph)))
    return a, b, results


def cells(results):
    out = []
    for outbound, inbound in results:
        a, b = outbound[0], inbound[0]
        out.append(a if a == b else f"{a} / {b}")
    fwd, back = results[1]
    distances = ["—" if v is None else f"{v:.2f}" for v in (fwd[1], back[1])]
    return out + [" / ".join(distances)]


def markdown():
    rows, hashes, cover_edges = [], [], []
    total_anchors = total_covers = 0
    for map_id in MAPS:
        source = ROOT / "maps" / (map_id + ".json")
        model = ROOT / "massing" / (map_id + ".glb")
        data = json.loads(source.read_text(encoding="utf-8"))
        bpy.ops.wm.read_factory_settings(use_empty=True)
        require(bpy.ops.import_scene.gltf(filepath=str(model)) == {'FINISHED'}, f"import failed: {model.name}")
        bpy.context.view_layer.update()
        graph = bpy.context.evaluated_depsgraph_get()
        floors = [o for o in bpy.context.scene.objects if o.type == 'MESH' and o.get("kind") == "atlas_floor"]
        require(len(floors) == 1, f"{model.name}: expected one continuous floor mesh")
        ground = ground_reader(floors[0], graph)
        cover_tops = verify_placement(data, source, floors[0], graph, ground)
        total_anchors += len(data["nodes"])
        total_covers += len(data["cover"])
        hashes.append(f"| [{data['title']}]({model.name}) | `{checksum(source)[:16]}` | "
                      f"`{checksum(model)[:16]}` |")
        for probe in data["sightlines"]:
            a, b, results = cast_pair(probe, ground, graph)
            elevations = f"{round(a.z, 2) or 0:.2f} / {round(b.z, 2) or 0:.2f}"
            row = [data["title"], probe["label"], elevations, *cells(results)]
            rows.append("| " + " | ".join(row) + " |")
            surface, distance = results[1][0]
            if surface in cover_tops:
                # Raising both endpoints equally preserves the horizontal crossing.
                fraction = distance / (b - a).length
                high_ray_z = a.z + (b.z - a.z)*fraction + EYE_HEIGHTS[-1]
                cover_edges.append(f"| {data['title']} · {probe['label']} | {surface} | {cover_tops[surface]:.2f} "
                                   f"| {high_ray_z:.2f} | {results[-1][0][0]} |")
    intro = [
        "# Sightlines in the exported 3D maps", "",
        f"Blender imported all four GLBs and cast {len(rows)*len(EYE_HEIGHTS)*2} sight rays through their "
        f"triangles. Each of the {len(rows)} sights in the [drawings](../README.md) uses a pair of "
        "grounded endpoints. Each column raises both ends by the stated height above their local floors "
        "and tests the segment in both directions. Heights are example probes for low, standing and elevated views.", "",
        "| Map | Sightline | Floor at start / end (m) | 0.9 m | 1.7 m | 2.8 m | First hit at 1.7 m, forward / reverse (m) |",
        "| --- | --- | ---: | --- | --- | --- | ---: |", *rows, "",
        "A single label identifies the same first mesh from both ends. A slash lists different first hits, "
        "starting with the direction specified in the map JSON. **Clear** means the line reached the "
        "opposite endpoint. First-hit distances are measured along that 3D segment.", "",
        "## Edges that screen a standing view", "",
        "For each standing ray whose first hit from the start is a cover mesh, compare the top of the mesh "
        "with the elevated ray at that same forward edge. Both values use the map's common vertical datum. "
        "A screen on higher ground can still catch a ray raised by 2.8 m at both endpoints.", "",
        "| Sightline | Cover | Top elevation (m) | Elevated ray at forward edge (m) | Elevated result from start |",
        "| --- | --- | ---: | ---: | --- |", *cover_edges, "",
        "These meshes contain floor surfaces, exposed edge skirts, ground markings and the named cover pieces. "
        "The graybox still needs the final walls, ceilings, corner cameras and heroes. A clear central view "
        "can change when the camera moves to the outside shoulder. Check each entry again with the real "
        "camera offset, avatar height, aiming ray and visibility rules on both sides.", "",
        "## Model identity and placement", "",
        f"After import, Blender checked the positions and local floor heights of {total_anchors} room anchors "
        f"and the ground-relative top elevation and footprint of {total_covers} cover meshes against the "
        "map JSON within 0.02 m. North is positive Y in Blender and negative Z in glTF. Dropping a ray "
        "onto the continuous floor mesh supplies the height at each probe end. Sightline casts then use the whole scene.", "",
        "The floor's embedded SHA-256 must match its full JSON input. Prefixes below identify the tested files.", "",
        "| Map GLB | Map JSON SHA-256 prefix | GLB SHA-256 prefix |", "| --- | --- | --- |", *hashes, "",
        "Reproduce from the repository root with Blender 4.3.2. Omit the final `-- --check` to regenerate this report.", "",
        "```sh",
        "blender -b --factory-startup -t 1 --python-exit-code 1 --python games/yuga-native/docs/design/ember-rite-5v5/atlas/probe_massing.py -- --check",
        "```", "",
    ]
    return "\n".join(intro)


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if the checked-in report differs")
    check = parser.parse_args(args).check
    report = markdown()
    path = ROOT / "massing" / "sightlines.md"
    if check:
        require(path.exists() and path.read_text(encoding="utf-8") == report,
                "Sightlines report is stale. Run the probe script without --check to update it.")
    else:
        path.write_text(report, encoding="utf-8")
    print("Verified Blender map placement and sightline report.")


if __name__ == "__main__":
    main()
