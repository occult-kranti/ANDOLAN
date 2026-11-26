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
        for dx, dy in ((0,0),(.0002,.0002),(-.0002,-.0002)):
            start = plan_position((point[0]+dx,point[1]+dy),ceiling)
            hit, normal, _, _ = tree.ray_cast(start, Vector((0,0,-1)), depth)
            if hit is not None and normal.z > .05:
                return hit.z
        raise ValueError(f"{floor.name}: no top surface beneath {point}")

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


def route_profiles(data,ground):
    """Sample across the corridor. Report the largest sustained centre-line grade."""
    nodes = data["nodes"]
    peaks = {}
    rays = 0
    for link in data["links"]:
        if link["kind"] == "fold":
            continue
        start,end = link["from"],link["to"]
        points = [nodes[start]["xz"],*link.get("via",[]),nodes[end]["xz"]]
        profile = []
        total = 0.
        for a,b in zip(points,points[1:]):
            length = math.dist(a,b)
            steps = math.ceil(length/.25)
            dx,dy = (b[0]-a[0])/length,(b[1]-a[1])/length
            for i in range(steps+1):
                x,y = a[0]+(b[0]-a[0])*i/steps,a[1]+(b[1]-a[1])*i/steps
                for offset in (-.46,0,.46):
                    z = ground((x-dy*link["width"]*offset,y+dx*link["width"]*offset))
                    rays += 1
                    if offset == 0 and (i>0 or not profile):
                        profile.append((total+length*i/steps,z))
            total += length
        left = 0
        maximum,run = 0.,0.
        for right,height in profile:
            while left+1 < len(profile) and right-profile[left+1][0] >= 2:
                left += 1
            distance = right-profile[left][0]
            if distance >= 2:
                grade = abs(height-profile[left][1])/distance
                if grade > maximum or run == 0:
                    maximum,run = grade,distance
        peaks[start,end] = maximum,run
    return rays,peaks


def markdown():
    sys.path.insert(0,str(ROOT))
    from massing import verify_footprint
    rows, hashes, cover_edges = [], [], []
    profiles = []
    total_anchors = total_covers = 0
    inside = outside = total_samples = 0
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
        occupied,empty = verify_footprint(source,model,import_model=False)
        inside += occupied
        outside += empty
        casts,peaks = route_profiles(data,ground)
        total_samples += casts
        peak = max(peaks,key=peaks.get)
        cases = [peak]
        if map_id == "mandala":
            for site in ("a","b"):
                sluice = next(pair for pair in peaks if set(pair) == {"mid",site})
                if sluice not in cases:
                    cases.append(sluice)
        for j,route in enumerate(cases):
            grade,run = peaks[route]
            names = " → ".join(data["nodes"][k]["label"] for k in route)
            profiles.append(f"| {data['title']} | {casts if j==0 else 'as above'} | {names} | "
                            f"{grade*100:.1f}% | {run:.2f} m |")
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
        f"Blender imported the four district floor models and cast {len(rows)*len(EYE_HEIGHTS)*2} sight rays through their "
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
        "## Corridor grades", "",
        f"Blender took {total_samples:,} floor samples at most 0.25 m apart along each physical corridor, at its centre and "
        "at 46% of its width on either side. The table shows the steepest sustained centreline grade per "
        "map, plus the Sluice descents to both sites. A moving window spans at least 2 m "
        "of horizontal travel. Water measures the modeled bed. These measurements guide character-controller trials.", "",
        "| District | Floor samples | Measured route | Peak grade | Window |",
        "| --- | ---: | --- | ---: | ---: |",*profiles,"",
        "## Model identity and placement", "",
        f"A 2 m grid yielded {inside:,} successful interior floor hits and {outside:,} successful exterior misses. "
        "The occupancy checks omit samples within 0.15 m of the analytical boundary to allow for the tessellated curves.", "",
        f"After import, Blender checked the positions and local floor heights of {total_anchors} room anchors "
        f"and the ground-relative top elevation and footprint of {total_covers} cover meshes against the "
        "map JSON within 0.02 m. North is positive Y in Blender and negative Z in glTF. Dropping a ray "
        "onto the continuous floor mesh supplies the height at each probe end. Sightline casts then use the whole floor-study scene. "
        "The [separate architectural models and doorway tests](architecture-checks.md) use the same map registration.", "",
        "The floor's embedded SHA-256 must match its full JSON input. Prefixes below identify the tested files.", "",
        "| Map GLB | Map JSON SHA-256 prefix | GLB SHA-256 prefix |", "| --- | --- | --- |", *hashes, "",
        "Reproduce from the repository root with Blender 4.3.2. Omit the final `-- --check` to regenerate this report.", "",
        "```sh",
        "blender -b --factory-startup -t 1 --python-exit-code 1 --python games/yuga-native/docs/design/ember-rite-5v5/atlas/probe_massing.py -- --check",
        "```", "",
    ]
    return "\n".join(intro)


def architecture_report():
    sys.path.insert(0,str(ROOT))
    from massing import verify_architecture, verify_approaches
    from architecture import Architecture
    rows,ids,approaches = [],[],[]
    for key in MAPS:
        source = ROOT / "maps" / f"{key}.json"
        model = ROOT / "massing" / f"{key}-architecture.glb"
        data = json.loads(source.read_text())
        arch = Architecture(data)
        parts,rays = verify_architecture(source,model)
        route_checks = verify_approaches(source,ROOT / "massing" / f"{key}.glb")
        approaches.append(f"| {arch.name} | "+", ".join(route_checks)+f" | {sum(route_checks.values())} |")
        head = f"{arch.clear_height:.2f} m" if arch.clear_height is not None else "Open to sky"
        rows.append(f"| [{arch.name}]({model.name}) · [{arch.source_id}](../RESEARCH_ROUNDS.md) | "
                    f"{arch.w:g} × {arch.d:g} × {arch.height:g} m | {arch.opening:g} m | "
                    f"{head} | {parts} | {rays} |")
        pos = " → ".join(f"({x:g}, {z:g})" for x,z in arch.thresholds)
        ids.append(f"| {data['title']} · {arch.node['label']} | {pos} | "
                   f"{arch.bearing:g}° | {arch.level:+g} m | `{checksum(model)[:16]}` |")
    return "\n".join([
        "# Architectural models and measured clearances","",
        "Each building imports in metres at the host room’s map coordinates. Combine its GLB with the corresponding "
        "[district floor study](sightlines.md) at the scene origin to rehearse its approaches. "
        "The standalone models retain individual named courses, piers, arch stones and gauge elements for editing. "
        "Each third sheet in the [12-page atlas](../blueprints/yuga-map-atlas.pdf) cuts the same geometry.","",
        "![Four orthographic building studies rendered from the exported GLBs](architecture-overview.jpg)","",
        "| Building and research reference | Width × axial depth × height above sill | Clear width | Full-width headroom | Named mesh parts | Clear axial rays |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",*rows,"",
        "| District and host room | Entrance I → exit II, map X/Z | I → II bearing | Dry sill | GLB SHA-256 prefix |",
        "| --- | --- | ---: | ---: | --- |",*ids,"",
        "In Blender the horizontal coordinates are X east and Y north. In glTF, north is negative Z and elevation is positive Y. "
        "Bearings turn clockwise from north. A ray traversed the whole building in both directions at its centre and at "
        "±49.5% of its clear width. Test heights were 0.12, 1.70 and 2.12 m above the dry sill, plus 0.04 m below "
        "the recorded headroom on covered buildings. Each import passed source-hash, room registration, bearing and bounding-envelope checks.","",
        "## Approach routes with both models loaded","",
        "Blender then imported the district and the building together at the shared origin. It tested each incident ordinary "
        "corridor from the host room centre to just outside the architectural footprint, following the authored bends. "
        "Casts at 0.25, 1.70 and 2.12 m above the host sill used the centreline and both 0.28 m shoulder offsets.","",
        "| Building | Ordinary approaches | Clear segment rays |","| --- | --- | ---: |",*approaches,"",
        "The pavilion has four corbelled courses and a one-notch inlay at the entrance. The gallery’s two rows of "
        "four columns leave three recurring bays. The gate has eleven separate arch stones at each end. The well has "
        "three treads on each bank and a recessed water surface. Three additional vertical rays touched both water surfaces at +0.20 m "
        "and the central causeway at +1.00 m. In an integrated district scene, cut openings in the host floor over the two basin rectangles "
        "before enabling water visuals or collision. The ray samples leave shoulder-camera clipping, a swept character capsule "
        "and lateral movement outside the authored approaches for a playable build.","",
        "From this atlas directory, regenerate both Blender reports and the capture sheets with:","",
        "```sh","blender -b --factory-startup -t 1 --python-exit-code 1 --python probe_massing.py",
        "python3 massing/render_studies.py","```",""])


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if the checked-in report differs")
    check = parser.parse_args(args).check
    for name,report in (("sightlines.md",markdown()),("architecture-checks.md",architecture_report())):
        path = ROOT / "massing" / name
        if check:
            require(path.exists() and path.read_text(encoding="utf-8") == report,
                    f"{name} is stale. Run the probe script without --check to update it.")
        else:
            path.write_text(report, encoding="utf-8")
    print("Verified floor grades, model placement, architectural clearances and sightlines.")


if __name__ == "__main__":
    main()
