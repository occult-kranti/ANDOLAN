"""Build the four planning GLBs with Blender's bundled Python and glTF exporter.

    blender -b --factory-startup -t 1 --python-exit-code 1 --python massing.py
    blender -b --factory-startup -t 1 --python-exit-code 1 --python massing.py -- --check

Plan X/Z is Blender X/Y, elevation is Blender Z. Export maps north to glTF −Z.
Rooms are flat. Ramps interpolate between the edges of their landing rooms.
The continuous top surface includes inlaid markings. Only authored cover has
a vertical gameplay footprint. Floor skirts show the edges of this study.
"""
import hashlib
import json
import math
import sys
from collections import defaultdict
from functools import lru_cache
from pathlib import Path

import bpy
from mathutils import Vector
from mathutils.geometry import delaunay_2d_cdt

ROOT = Path(__file__).resolve().parent
COLORS = {
    "Room": "cfbc99", "Walk": "aa9b82", "Ramp": "8d9c7e", "Water": "5099a4",
    "Skirt": "566366", "Cover": "485659", "Ember": "bd502c", "Spawn": "285b63",
    "Fold": "78578b",
}


def material(name, hex_color):
    color = [int(hex_color[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    rgba = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in color] + [1]
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = rgba
    mat.use_nodes = True
    shader = mat.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = rgba
    shader.inputs["Roughness"].default_value = .89
    return mat


def box(item):
    x, z = item["xz"]
    w, d = item["size"]
    return [(x - w/2, z - d/2), (x + w/2, z - d/2),
            (x + w/2, z + d/2), (x - w/2, z + d/2)]


def outside_room(point, room):
    return math.hypot(*(max(abs(p - c) - w/2, 0)
                        for p, c, w in zip(point, room["xz"], room["size"])))


def circle(x, z, radius, count):
    return [(x + radius*math.cos(i*math.tau/count), z + radius*math.sin(i*math.tau/count))
            for i in range(count)]


def ribbons(p, q, width, cuts=1):
    """Adjacent subdivision faces share the very same section coordinates."""
    dx, dz = q[0] - p[0], q[1] - p[1]
    scale = width / (2 * math.hypot(dx, dz))
    sx, sz = -dz * scale, dx * scale
    last = None
    for i in range(cuts + 1):
        x, z = p[0] + dx * i / cuts, p[1] + dz * i / cuts
        current = ((x - sx, z - sz), (x + sx, z + sz))
        if last:
            yield [last[0], current[0], current[1], last[1]]
        last = current


class Corridor:
    def __init__(self, link, nodes):
        self.start, self.end = nodes[link["from"]], nodes[link["to"]]
        self.points = [self.start["xz"], *link.get("via", []), self.end["xz"]]
        self.kind = link["kind"].title()
        self.width = link["width"]
        self.lengths = [math.dist(a, b) for a, b in zip(self.points, self.points[1:])]
        # A plane between the two supporting room faces stays flat across the
        # full landing, even when a route turns back along the side of a room.
        self.run = []
        self.lip = []
        for a, b, w, d in zip(self.start["xz"], self.end["xz"], self.start["size"], self.end["size"]):
            direction = 1 if b > a else -1
            self.run.append(direction * max(0, abs(b-a) - (w+d)/2))
            self.lip.append(a + direction*w/2)
        self.run_squared = sum(r*r for r in self.run)
        if not self.run_squared and self.start["y"] != self.end["y"]:
            raise ValueError(f'Conflicting landing heights between {self.start["label"]} and {self.end["label"]}')

    def sample(self, point):
        closest = math.inf
        for p, q, length in zip(self.points, self.points[1:], self.lengths):
            dx, dz = q[0] - p[0], q[1] - p[1]
            fraction = ((point[0] - p[0])*dx + (point[1] - p[1])*dz) / length**2
            fraction = min(1.0, max(0.0, fraction))
            distance = math.dist(point, (p[0] + dx*fraction, p[1] + dz*fraction))
            closest = min(closest, distance)
        if self.run_squared:
            t = sum((p-a)*r for p, a, r in zip(point, self.lip, self.run)) / self.run_squared
            t = max(0.0, min(1.0, t))
        else:
            t = 0.0
        return closest, self.start["y"] + t*(self.end["y"] - self.start["y"])


class FloorPlan:
    def __init__(self, data):
        self.vertices = []
        self.indices = {}
        self.polygons = []
        self.regions = []
        self.rooms = data["nodes"]
        self.routes = []
        for room in self.rooms.values():
            self.add(box(room), ("room", "Room"))
        for link in data["links"]:
            if link["kind"] == "fold":
                for end in (link["from"], link["to"]):
                    x, z = self.rooms[end]["xz"]
                    corners = [(x, z - 1.6), (x + 1.6, z), (x, z + 1.6), (x - 1.6, z)]
                    self.stroke(corners + corners[:1], .28, "Fold")
                continue
            route = Corridor(link, self.rooms)
            self.routes.append(route)
            tag = ("route", route.kind)
            for a, b, length in zip(route.points, route.points[1:], route.lengths):
                cuts = math.ceil(length/4) if route.start["y"] != route.end["y"] else 1
                for polygon in ribbons(a, b, route.width, cuts):
                    self.add(polygon, tag)
            for x, z in route.points[1:-1]:
                self.add(circle(x, z, route.width/2, 20), tag)
        self.markers()

    def add(self, polygon, tag):
        ids = []
        for point in polygon:
            xy = tuple(round(v, 6) for v in point)
            if xy not in self.indices:
                self.indices[xy] = len(self.vertices)
                self.vertices.append(Vector(xy))
            ids.append(self.indices[xy])
        self.polygons.append(ids)
        points = [tuple(self.vertices[i]) for i in ids]
        xs, zs = zip(*points)
        edges = [(b[0]-a[0], b[1]-a[1], a[0], a[1]) for a, b in zip(points, points[1:] + points[:1])]
        self.regions.append(((min(xs), min(zs), max(xs), max(zs)), edges, tag))

    def material_at(self, x, z):
        # CDT constraints divide the plane. In a heavily overlapped junction its
        # returned source face IDs may extend into the exterior. Classify each
        # open triangle at its centroid against the actual convex input shapes.
        inside = {}
        for (left, low, right, high), edges, (layer, color) in self.regions:
            if left <= x <= right and low <= z <= high:
                if all(dx*(z-z0) - dz*(x-x0) >= -1e-8 for dx, dz, x0, z0 in edges):
                    inside[layer] = color
        if "room" in inside or "route" in inside:
            return inside.get("mark") or inside.get("room") or inside["route"]
        return None

    def stroke(self, path, width, color):
        for p, q in zip(path, path[1:]):
            self.add(next(ribbons(p, q, width)), ("mark", color))

    def markers(self):
        letters = {
            "a": [[(-.88, -.86), (0, .95), (.88, -.86)], [(-.50, -.10), (.50, -.10)]],
            "b": [[(-.68, -.84), (-.68, .86), (.23, .86), (.68, .52),
                   (.68, .26), (.25, .00), (-.68, .00)], [(0.25, .00), (.75, -.26),
                   (.75, -.55), (.30, -.84), (-.68, -.84)]],
        }
        for key, glyph in letters.items():
            x, z = self.rooms[key]["xz"]
            outer, inner = circle(x, z, 3.0, 32), circle(x, z, 2.68, 32)
            for i in range(len(outer)):
                self.add([outer[i-1], outer[i], inner[i], inner[i-1]], ("mark", "Ember"))
            for line in glyph:
                self.stroke([(x+u, z+v) for u, v in line], .26, "Ember")
        for key in ("atk", "def"):
            x, z = self.rooms[key]["xz"]
            if key == "atk":
                self.stroke([(x-2, z-.65), (x, z+1.25), (x+2, z-.65)], .42, "Spawn")
            else:
                shield = [(-1.7, .9), (1.7, .9), (1.5, -.35), (0, -1.4), (-1.5, -.35), (-1.7, .9)]
                self.stroke([(x+u,z+v) for u, v in shield], .38, "Spawn")

    @lru_cache(maxsize=65536)
    def height(self, x, z):
        for room in self.rooms.values():
            if outside_room((x, z), room) < .0001:
                return room["y"]
        total = weighted_height = 0.0
        for route in self.routes:
            distance, height = route.sample((x, z))
            margin = route.width/2 - distance
            if margin >= -.0001:
                weight = max(.0001, margin) / route.width
                total += weight
                weighted_height += weight * height
        if not total:
            raise ValueError(f"Floor vertex outside every width at {(x, z)}")
        return weighted_height/total

    def triangulate(self):
        coords, _, triangles, _, _, _ = delaunay_2d_cdt(
            self.vertices, [], self.polygons, 0, .00003, False)
        verts, faces, materials = [], [], []
        remap = {}
        sides = defaultdict(list)
        for tri in triangles:
            x = sum(coords[i].x for i in tri) / 3
            z = sum(coords[i].y for i in tri) / 3
            color = self.material_at(x, z)
            if color is None:
                continue
            top = []
            for j in tri:
                if j not in remap:
                    x, z = coords[j]
                    remap[j] = len(verts)
                    verts.append((x, z, self.height(x, z)))
                top.append(remap[j])
            faces.append(top)
            materials.append(color)
            for p, q in zip(top, top[1:] + top[:1]):
                sides[tuple(sorted((p, q)))].append((p, q))
        # A single piece of top geometry carries all room, path and ink boundaries.
        # Only exposed edges receive a skirt. There are no internal vertical walls.
        bottom = {}
        for pair in sides.values():
            if len(pair) == 2:
                continue
            if len(pair) != 1:
                raise ValueError("Non-manifold edge in floor surface")
            p, q = pair[0]
            for i in (p, q):
                if i not in bottom:
                    x, z, y = verts[i]
                    bottom[i] = len(verts)
                    verts.append((x, z, y - .65))
            faces.append([p, bottom[p], bottom[q], q])
            materials.append("Skirt")
        return verts, faces, materials


def mesh(name, verts, faces):
    data = bpy.data.meshes.new(name)
    data.from_pydata(verts, [], faces)
    data.update()
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    return obj


def build(source, destination):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    data = json.loads(source.read_text())
    mats = {k: material(k, c) for k, c in COLORS.items()}
    plan = FloorPlan(data)
    verts, faces, colors = plan.triangulate()
    floor = mesh(data["title"] + " • continuous floor", verts, faces)
    floor["kind"] = "atlas_floor"
    floor["map_id"] = data["id"]
    floor["source_sha256"] = hashlib.sha256(source.read_bytes()).hexdigest()
    floor["units"] = "metres"
    floor["orientation"] = "north is -Z in glTF and +Y in Blender"
    floor["purpose"] = "Editable massing for site and route review"
    for name in dict.fromkeys(colors):
        floor.data.materials.append(mats[name])
    slots = {m.name: i for i, m in enumerate(floor.data.materials)}
    for polygon, name in zip(floor.data.polygons, colors):
        polygon.material_index = slots[name]
    for item in data["cover"]:
        corners = box(item)
        y = plan.height(*item["xz"])
        bottom = [(x, z, y-.04) for x, z in corners]
        top = [(x, z, y+item["height"]) for x, z in corners]
        cover = mesh(item["label"], bottom + top, [[3,2,1,0],[4,5,6,7],
                     [0,1,5,4],[1,2,6,5],[2,3,7,6],[3,0,4,7]])
        cover["kind"] = "authored_cover"
        cover.data.materials.append(mats["Cover"])
    for key, node in data["nodes"].items():
        anchor = bpy.data.objects.new(key + " • " + node["label"], None)
        anchor.location = (node["xz"][0], node["xz"][1], node["y"])
        anchor.empty_display_type = 'PLAIN_AXES'
        anchor.empty_display_size = .75
        anchor["kind"], anchor["room_id"] = "room_anchor", key
        bpy.context.collection.objects.link(anchor)
    bpy.ops.export_scene.gltf(filepath=str(destination), export_format='GLB', export_extras=True,
                              export_animations=False, export_texcoords=False, export_yup=True,
                              export_cameras=False, export_lights=False)
    plan.height.cache_clear()


def verify_footprint(source, asset):
    """Reopen the GLB and sample both the floors and the empty courtyard gaps."""
    from mathutils.bvhtree import BVHTree

    # Reuse the blueprint auditor's independent analytical corridor-distance test.
    sys.path.insert(0, str(ROOT))
    from audit import segment_distance

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(asset))
    data = json.loads(source.read_text())
    floor, = (obj for obj in bpy.context.scene.objects if obj.get("kind") == "atlas_floor")
    if floor["source_sha256"] != hashlib.sha256(source.read_bytes()).hexdigest():
        raise ValueError(f"{asset.name}: source layout changed")
    tree = BVHTree.FromObject(floor, bpy.context.evaluated_depsgraph_get())
    rooms = list(data["nodes"].values())
    segments = []
    for link in data["links"]:
        if link["kind"] != "fold":
            points = [data["nodes"][link["from"]]["xz"], *link.get("via", []),
                      data["nodes"][link["to"]]["xz"]]
            segments.extend((a, b, link["width"]/2) for a, b in zip(points, points[1:]))
    left, low, right, high = data["bounds"]
    counts = [0, 0]
    for x in range(math.floor(left) + 1, math.ceil(right), 2):
        for z in range(math.floor(low) + 1, math.ceil(high), 2):
            gap = max(min(w/2 - abs(p - c) for p, c, w in zip((x, z), r["xz"], r["size"]))
                      for r in rooms)
            gap = max(gap, *(w - segment_distance((x, z), a, b) for a, b, w in segments))
            if abs(gap) <= .15:
                continue  # Arc tessellation is inscribed inside the design radius.
            # A ray exactly on a triangle seam can miss in single precision.
            hit = any(tree.ray_cast((x+dx, z+dz, 30), (0, 0, -1), 60)[0] is not None
                      for dx, dz in [(0, 0), (.0002, .0002), (-.0002, -.0002)])
            if hit != (gap > 0):
                raise ValueError(f"{asset.name}: unexpected floor occupancy at {(x, z)}")
            counts[hit] += 1
    print(f"{asset.name}: {counts[1]} interior and {counts[0]} exterior samples passed")


if __name__ == "__main__":
    out = ROOT / "massing"
    checking = "--check" in sys.argv
    if not checking:
        out.mkdir(exist_ok=True)
    for source in sorted((ROOT / "maps").glob("*.json")):
        destination = out / (source.stem + ".glb")
        if checking:
            verify_footprint(source, destination)
        else:
            build(source, destination)
