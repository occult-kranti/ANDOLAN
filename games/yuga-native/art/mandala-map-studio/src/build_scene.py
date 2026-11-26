"""Assemble the original Mandala art at its registered metre coordinates.

blender -b --factory-startup -t 2 --python-exit-code 1 --python src/build_scene.py
"""

import argparse
from collections import defaultdict
from functools import lru_cache
import hashlib
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Quaternion, Vector
from mathutils.bvhtree import BVHTree

HERE = Path(__file__).resolve().parent
STUDIO = HERE.parent
ATLAS = STUDIO.parents[1] / "docs/design/ember-rite-5v5/atlas"
sys.path.insert(0, str(HERE))
import artlib as A
from props import build_artifact, build_cover, build_rite
from rooms import build_room
from district_backdrop import build_backdrop


def collection(name, parent):
    col = bpy.data.collections.new(name)
    parent.children.link(col)
    return col


def active(col):
    def find(layer):
        if layer.collection == col:
            return layer
        for sub in layer.children:
            hit = find(sub)
            if hit is not None:
                return hit

    bpy.context.view_layer.active_layer_collection = find(bpy.context.view_layer.layer_collection)


def imported(path, target):
    before = set(bpy.context.scene.objects)
    bpy.ops.import_scene.gltf(filepath=str(path))
    batch = sorted(set(bpy.context.scene.objects) - before, key=lambda obj: obj.name)
    for obj in batch:
        if target not in obj.users_collection:
            target.objects.link(obj)
        for col in list(obj.users_collection):
            if col != target:
                col.objects.unlink(obj)
    return batch


def local_parts(col, place, yaw, make, index=0):
    active(col)
    before = set(bpy.context.scene.objects)
    make()
    batch = set(bpy.context.scene.objects) - before
    if not batch:
        raise ValueError(f"{col.name} contains no authored pieces")
    rotation = Quaternion((0, 0, 1), yaw)
    origin = Vector(place)
    for obj in batch:
        obj["study_id"] = col.name
        obj["socket_index"] = index
        if col not in obj.users_collection:
            col.objects.link(obj)
        if obj.parent in batch:
            continue
        obj.location = origin + rotation @ obj.location
        if yaw:
            initial = (
                obj.rotation_quaternion.copy()
                if obj.rotation_mode == "QUATERNION"
                else obj.rotation_euler.to_quaternion()
            )
            obj.rotation_mode = "QUATERNION"
            obj.rotation_quaternion = rotation @ initial


def distance_segment(x, y, p, q):
    dx, dy = q[0] - p[0], q[1] - p[1]
    t = max(0, min(1, ((x - p[0]) * dx + (y - p[1]) * dy) / (dx * dx + dy * dy)))
    return math.hypot(x - p[0] - t * dx, y - p[1] - t * dy)


class Survey:
    def __init__(self, plan, floor):
        w = floor.matrix_world
        self.surface = BVHTree.FromPolygons(
            [w @ v.co for v in floor.data.vertices], [tuple(p.vertices) for p in floor.data.polygons]
        )
        self.rooms = [
            (n["xz"][0], n["xz"][1], n["size"][0] / 2, n["size"][1] / 2) for n in plan["nodes"].values()
        ]
        self.segments = []
        for e in plan["links"]:
            if e["kind"] == "fold":
                continue
            path = [plan["nodes"][e["from"]]["xz"], *e.get("via", []), plan["nodes"][e["to"]]["xz"]]
            self.segments.extend((a, b, e["width"] / 2) for a, b in zip(path, path[1:]))

    @lru_cache(None)
    def floor(self, x, y):
        hit = self.surface.ray_cast((x, y, 20), (0, 0, -1), 40)[0]
        return None if hit is None else hit.z

    def in_room(self, x, y, margin=0):
        return any(abs(x - a) <= w + margin and abs(y - b) <= d + margin for a, b, w, d in self.rooms)

    def clear_footprint(self, x, y, radius):
        for a, b, w, d in self.rooms:
            if math.hypot(max(0, abs(x - a) - w), max(0, abs(y - b) - d)) <= radius:
                return False
        return all(distance_segment(x, y, a, b) > width + radius for a, b, width in self.segments)


class Tesserae:
    """Batch thousands of individually shaped street stones in a few editable meshes."""

    def __init__(self, survey):
        self.groups = defaultdict(lambda: ([], []))
        self.survey = survey

    def place(self, key, polygon, raise_by):
        vertices, faces = self.groups[key]
        coords = []
        for x, y in polygon:
            z = self.survey.floor(round(x, 4), round(y, 4))
            if z is None:
                return
            coords.append((x, y, z + raise_by))
        base = len(vertices)
        vertices.extend(coords)
        faces.append(tuple(range(base, base + len(coords))))

    def finish(self, prefix):
        for key, (vertices, faces) in self.groups.items():
            if faces:
                A.mesh(prefix + " / " + key, vertices, faces, key)


def dress_route(row, survey):
    tiles = Tesserae(survey)
    points = row["points_xyz"]
    if row["travel_kind"] == "fold":
        for x, y, z in (points[0], points[-1]):
            # Both thresholds are real; the discontinuity between them has no mesh.
            north = row["from"].endswith("_n")
            marks = (
                [[(-0.7, 0.43), (0, -0.38)], [(0, -0.38), (0.7, 0.43)]]
                if not north
                else [[(-0.7, j), (0.7, j)] for j in (-0.25, 0.25)]
            )
            for p, q in marks:
                A.beam(
                    "Fold sill inlay",
                    (x + p[0], y + p[1], z + 0.055),
                    (x + q[0], y + q[1], z + 0.055),
                    0.085,
                    "brass",
                    8,
                )
        return
    water = row["travel_kind"] == "water"
    width = row["width_m"]
    for i, (start, end) in enumerate(zip(points, points[1:])):
        dx, dy = end[0] - start[0], end[1] - start[1]
        length = math.hypot(dx, dy)
        ex, ey = dx / length, dy / length

        def world(u, v):
            return (start[0] + ex * u - ey * v, start[1] + ey * u + ex * v)

        def tile(u0, v0, u1, v1, key, h):
            tiles.place(key, [world(u0, v0), world(u1, v0), world(u1, v1), world(u0, v1)], h)

        count = max(1, round(length / (2.0 if water else 1.8)))
        run = length / count
        for j in range(count):
            u = (j + 0.5) * run
            x, y = world(u, 0)
            if survey.in_room(x, y, 0.25):
                continue
            if water:
                sign = 1 if (i + j) % 2 else -1
                lateral = sign * (0.3 + (0.16 * ((i * 11 + j * 7) % 7))) * width / 3
                tile(u - 0.14, lateral, u + 0.13, lateral + min(1.2, width * 0.19), "#76aaa0", 0.032)
                if j % 3 == 0:
                    tile(u + 0.3, lateral - 0.45, u + 0.38, lateral + 0.14, "#9bbdb0", 0.034)
                continue
            # The slab bed and its interleaved courses sit on the surveyed grade.
            for k in range(3):
                v0 = -width * 0.40 + k * width * 0.265
                inset = 0.07 if (i + j + k) % 3 else 0.12
                key = ("#BDAD8E", "#C9B798", "#C2AE8D", "#AE9D84", "#C7B399")[(i * 5 + j * 7 + k * 11) % 5]
                tile(
                    u - run * 0.5 + inset,
                    v0 + 0.035,
                    u + run * 0.5 - inset,
                    v0 + width * 0.265 - 0.04,
                    key,
                    0.021,
                )
            for sign in (-1, 1):
                side = width * sign * 0.465
                tile(u - run * 0.47, side - 0.10, u + run * 0.47, side + 0.10, "#85775D", 0.026)
            if row["travel_kind"] == "ramp" and j % 3 == 1:
                tile(u - 0.07, -width * 0.36, u + 0.055, width * 0.36, "brass", 0.030)
    tiles.finish(row["title"])
    if not any(obj.type == "MESH" for obj in bpy.context.collection.objects):
        # A short link can lie almost entirely on its two landings.
        a, b = points[0], points[-1]
        x, y = (a[0] + b[0]) * 0.5, (a[1] + b[1]) * 0.5
        ground = survey.floor(x, y)
        if ground is None:
            x, y = a[:2]
            ground = a[2]
        A.cyl("Threshold survey stud", (x, y, ground + 0.025), 0.15, 0.035, "brass", 16)


def aim(obj, point):
    obj.rotation_euler = (Vector(point) - obj.location).to_track_quat("-Z", "Y").to_euler()


def setup_studio(scene):
    rigs = collection("Lighting and study cameras", scene.collection)

    def light(name, kind, loc, power, color, point, shape):
        data = bpy.data.lights.new(name, kind)
        data.energy = power
        data.color = color
        if kind == "SUN":
            data.angle = shape
        else:
            data.shape = "DISK"
            data.size = shape
        ob = bpy.data.objects.new(name, data)
        rigs.objects.link(ob)
        ob.location = loc
        aim(ob, point)

    light("Late monsoon sun", "SUN", (-75, -99, 126), 3.3, (1, 0.83, 0.64), (0, 0, 0), 0.16)
    light("Canal bounce", "AREA", (-40, -12, 45), 14000, (0.64, 0.82, 1), (0, 0, 0), 54)
    scene.world = bpy.data.worlds.new("River sky")
    scene.world.use_nodes = True
    scene.world.node_tree.nodes["Background"].inputs[0].default_value = (0.55, 0.69, 0.76, 1)
    scene.world.node_tree.nodes["Background"].inputs[1].default_value = 0.58
    cameras = [
        ("District isometric", (173, -207, 192), (0, 0, 0), 42),
        ("Ghat towards market", (-19, -15, 7), (11, 2, 2.9), 37),
        ("Quay towards dry bank", (-62, -18, 5), (-28, 1, 2), 39),
        ("Market towards temple", (49, 12, 5), (27, -16, 3), 38),
        ("South fold lintel", (17, -42, 3.2), (12, -34, 2.4), 35),
    ]
    for name, pos, look, lens in cameras:
        camera = bpy.data.cameras.new(name)
        camera.lens = lens
        camera.clip_end = 1500
        ob = bpy.data.objects.new(name, camera)
        rigs.objects.link(ob)
        ob.location = pos
        aim(ob, look)
        if name == "District isometric":
            camera.type = "ORTHO"
            camera.ortho_scale = 287
            scene.camera = ob
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 16
    scene.cycles.use_denoising = True
    scene.render.resolution_x = 1440
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == "VIEW_3D":
                space = area.spaces.active
                space.shading.type = "SOLID"
                space.shading.color_type = "MATERIAL"
                space.shading.show_cavity = True
                space.shading.cavity_type = "WORLD"
                space.region_3d.view_distance = 160
                space.region_3d.view_location = (0, 0, 0)
                space.region_3d.view_rotation = scene.camera.rotation_euler.to_quaternion()


def export_district(root, destination):
    """Export the district with authored tangent frames for its normal maps."""
    bpy.ops.object.select_all(action="DESELECT")
    for obj in root.all_objects:
        if obj.type in ("MESH", "CURVE", "FONT", "EMPTY"):
            obj.select_set(True)
    bpy.ops.export_scene.gltf(
        filepath=str(destination),
        export_format="GLB",
        use_selection=True,
        export_yup=True,
        export_tangents=True,
        export_extras=False,
        export_animations=False,
    )
    bpy.ops.object.select_all(action="DESELECT")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=STUDIO)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else [])
    args.out.mkdir(parents=True, exist_ok=True)
    plan_path = ATLAS / "maps/mandala.json"
    plan = json.loads(plan_path.read_text())
    catalog = json.loads((STUDIO / "catalog.json").read_text())
    source_hash = hashlib.sha256(plan_path.read_bytes()).hexdigest()
    assert catalog["layout_sha256"] == source_hash
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.name = "Mandala Rift · Environment study"
    root = collection("world_art", scene.collection)
    floor_group = collection("base-floor", root)
    active(floor_group)
    source = imported(ATLAS / "massing/mandala.glb", floor_group)
    (floor,) = [o for o in source if "continuous floor" in o.name]
    for obj in source:
        if obj != floor:
            bpy.data.objects.remove(obj, do_unlink=True)
    bpy.context.view_layer.update()
    survey = Survey(plan, floor)
    covers = {c["label"]: c for c in plan["cover"]}
    for row in catalog["elements"]:
        key = row["id"]
        kind = row["kind"]
        col = collection(key, root)
        active(col)
        col["catalog_id"] = key
        col["title"] = row["title"]
        if kind == "room":
            node_key = row["source_key"]
            local_parts(col, row["center_xyz"], 0, lambda: build_room(node_key, plan["nodes"][node_key]))
        elif kind == "route":
            dress_route(row, survey)
        elif kind == "architecture":
            imported(ATLAS / "massing/mandala-architecture.glb", col)
        elif kind == "cover":
            local_parts(
                col,
                row["center_xyz"],
                0,
                lambda: build_cover(key.removeprefix("cover-"), covers[row["source_key"]]),
            )
        elif kind == "artifact":
            for i, anchor in enumerate(row["placements_xyz"]):
                variant = (
                    ("south", "south-pyramid", "north", "north-pyramid")[i]
                    if key == "artifact-fold-lintels"
                    else "south"
                )
                local_parts(
                    col,
                    anchor,
                    math.pi if i >= 2 else 0,
                    lambda: build_artifact(key.removeprefix("artifact-"), variant),
                    i,
                )
        elif kind == "rite":
            local_parts(col, row["center_xyz"], 0, lambda: build_rite(key.removeprefix("rite-")))
        else:
            raise ValueError(kind)
        if not any(o.type == "MESH" for o in col.all_objects):
            raise ValueError(f"{key}: no model")
    background = collection("district-backdrop", root)
    active(background)
    build_backdrop(plan, survey.clear_footprint)
    scene["layout_sha256"] = source_hash
    scene["art_scope"] = (
        "Mandala district environment art and surveyed approaches. Runtime collision remains in the tactical map."
    )
    setup_studio(scene)
    active(root)
    bpy.context.view_layer.update()
    export_district(root, args.out / "mandala-rift.glb")
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(args.out / "mandala-rift.blend"), compress=True)
    print(f"Saved {len(catalog['elements'])} studies with {len(root.all_objects)} scene objects.")


if __name__ == "__main__":
    main()
