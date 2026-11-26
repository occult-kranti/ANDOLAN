"""Build the four floor studies and four registered architectural GLBs in Blender.

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
sys.path.insert(0,str(ROOT / "massing"))
from architecture import Architecture, PALETTE, threshold_glyph
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
                    for stroke in threshold_glyph(link["quarter_turns"]):
                        self.stroke([(x+u,z+v) for u,v in stroke],.16,"Fold")
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
    export_glb(destination)
    plan.height.cache_clear()


def export_glb(destination):
    bpy.ops.export_scene.gltf(filepath=str(destination),export_format="GLB",export_extras=True,
                              export_animations=False,export_texcoords=False,export_yup=True,
                              export_cameras=False,export_lights=False)


def build_architecture(source, destination):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    data=json.loads(source.read_text())
    arch=Architecture(data)
    root=bpy.data.objects.new(arch.name,None)
    bpy.context.collection.objects.link(root)
    root.location=(*arch.node["xz"],arch.level)
    root.rotation_euler.z=-math.radians(arch.bearing)
    root["kind"]="district_architecture"
    root["room_id"]=data["architecture"]["node"]
    root["map_id"]=data["id"]
    root["source_sha256"]=hashlib.sha256(source.read_bytes()).hexdigest()
    root["source_id"]=arch.source_id
    root["units"]="metres"
    root["purpose"]="Registered architectural study"
    colors={k:material(k,v[1:]) for k,v in PALETTE.items()}
    for part in arch.parts:
        obj=mesh(part.name,part.vertices,part.faces)
        obj.data.materials.append(colors[part.material])
        obj.parent=root
    export_glb(destination)


def verify_architecture(source, asset):
    from mathutils import Vector
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(asset))
    data=json.loads(source.read_text())
    a=Architecture(data)
    scene=bpy.context.scene
    root,=(o for o in scene.objects if o.get("kind")=="district_architecture")
    if root.get("source_sha256")!=hashlib.sha256(source.read_bytes()).hexdigest():
        raise ValueError(f"{asset.name}: obsolete architecture source")
    bpy.context.view_layer.update()
    if (root.matrix_world.translation-Vector((*a.node["xz"],a.level))).length>.001:
        raise ValueError(f"{asset.name}: world registration drifted")
    objects={o.name:o for o in scene.objects if o.type=="MESH"}
    if objects.keys()!={p.name for p in a.parts}:
        raise ValueError(f"{asset.name}: missing named architectural course")
    inverse=root.matrix_world.inverted()
    vertices=[inverse @ (o.matrix_world @ v.co) for o in objects.values() for v in o.data.vertices]
    extents=(min(v.x for v in vertices),max(v.x for v in vertices),min(v.y for v in vertices),
             max(v.y for v in vertices),max(v.z for v in vertices))
    expected=(-a.w/2,a.w/2,-a.d/2,a.d/2,a.height)
    if any(abs(p-q)>.002 for p,q in zip(extents,expected)):
        raise ValueError(f"{asset.name}: expected envelope {expected} and measured {extents}")
    # World direction comes from the source bearing, independently of the imported root.
    forward=Vector((math.sin(math.radians(a.bearing)),math.cos(math.radians(a.bearing)),0))
    right=Vector((forward.y,-forward.x,0))
    if ((root.matrix_world.to_3x3() @ Vector((0,1,0))).normalized()-forward).length>.001:
        raise ValueError(f"{asset.name}: axis does not point to the authored exit")
    graph=bpy.context.evaluated_depsgraph_get()
    ray_heights=[.12,1.70,2.12] + ([a.clear_height-.04] if a.clear_height is not None else [])
    centre=Vector((*a.node["xz"],a.level))
    rays=0
    for offset in [-.495,0,.495]:
        for eye in ray_heights:
            for sign in (-1,1):
                start=centre+right*(offset*a.opening)-sign*forward*(a.d/2+.15)+Vector((0,0,eye))
                hit,_,_,_,ob,_=scene.ray_cast(graph,start,sign*forward,distance=a.d+.30)
                if hit:
                    raise ValueError(f"{asset.name}: {ob.name} blocks the {eye:.2f} m axial test")
                rays+=1
    if a.water_level is not None:
        for side in (-1,1):
            local_x=side*(a.w+a.opening)/4
            origin=centre+right*local_x+Vector((0,0,a.height+1))
            hit,pos,_,_,ob,_=scene.ray_cast(graph,origin,Vector((0,0,-1)),distance=a.height+5)
            if not hit or not ob.name.startswith("Water surface") or abs(pos.z-a.level-a.water_level)>.002:
                raise ValueError(f"{asset.name}: recessed water plane failed at {local_x}")
        below=centre+Vector((0,0,2))
        hit,pos,_,_,ob,_=scene.ray_cast(graph,below,Vector((0,0,-1)),distance=3)
        if not hit or ob.name!="Dry causeway" or abs(pos.z-a.level)>.002:
            raise ValueError(f"{asset.name}: central deck lacks a dry continuous datum")
    else:
        # The aperture should have solid framing beside the clear route.
        # Check the sill at an actual support centre. An open-sided hall has no continuous wall.
        support=next(p for p in a.parts if p.name.endswith("bottom course") or "plinth" in p.name.lower())
        footprint=[v for v in support.vertices if v[2]==min(p[2] for p in support.vertices)]
        sx=sum(p[0] for p in footprint)/len(footprint)
        sy=sum(p[1] for p in footprint)/len(footprint)
        spot=centre+right*sx+forward*sy+Vector((0,0,.015))
        hit,_,_,_,_,_=scene.ray_cast(graph,spot,Vector((0,0,1)),distance=a.height+.05)
        if not hit:
            raise ValueError(f"{asset.name}: frame is missing alongside the aperture")
    return len(objects),rays


def verify_approaches(source, floor_path):
    """Layer the registered floor onto the imported building; test its incident routes."""
    data = json.loads(source.read_text())
    arch = Architecture(data)
    host = data["architecture"]["node"]
    bpy.ops.import_scene.gltf(filepath=str(floor_path))
    bpy.context.view_layer.update()
    scene = bpy.context.scene
    graph = bpy.context.evaluated_depsgraph_get()
    box = scene.objects[arch.name].matrix_world.inverted()
    counts = {}
    for edge in data["links"]:
        if edge["kind"] == "fold" or host not in (edge["from"],edge["to"]):
            continue
        points = [data["nodes"][edge["from"]]["xz"],*edge.get("via",[]),
                  data["nodes"][edge["to"]]["xz"]]
        if edge["to"] == host:
            points.reverse()
        # End the sweep just past the real building envelope, where the open
        # corridor takes over. Include every authored bend inside the envelope.
        route = []
        outside = False
        for p,q in zip(points,points[1:]):
            start = Vector((*p,arch.level))
            direction = Vector((q[0]-p[0],q[1]-p[1],0))
            length = direction.length
            direction.normalize()
            steps = math.ceil(length/.20)
            for i in range(1,steps+1):
                end = start+direction*(length*i/steps)
                local = box @ end
                if abs(local.x)>arch.w/2+.35 or abs(local.y)>arch.d/2+.35:
                    outside = True
                    break
            route.append((start,end))
            if outside:
                break
        count = 0
        for start,end in route:
            delta = end-start
            ray = delta.normalized()
            sideways = Vector((-ray.y,ray.x,0))
            for offset in (-.28,0,.28):
                for h in (.25,1.70,2.12):
                    origin = start+sideways*offset+Vector((0,0,h))
                    hit,_,_,_,obj,_ = scene.ray_cast(graph,origin,ray,distance=delta.length)
                    if hit:
                        raise ValueError(f"{source.stem}: path {edge['from']}–{edge['to']} hits {obj.name} at {h} m")
                    count += 1
        neighbor = edge["from"] if edge["to"] == host else edge["to"]
        counts[data["nodes"][neighbor]["label"]] = count
    return counts


def verify_footprint(source, asset, import_model=True):
    """Reopen the GLB and sample both the floors and the empty courtyard gaps."""
    from mathutils.bvhtree import BVHTree

    # Reuse the blueprint auditor's independent analytical corridor-distance test.
    sys.path.insert(0, str(ROOT))
    from audit import segment_distance

    if import_model:
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
    return counts[1],counts[0]


if __name__ == "__main__":
    out = ROOT / "massing"
    checking = "--check" in sys.argv
    if not checking:
        out.mkdir(exist_ok=True)
    for source in sorted((ROOT / "maps").glob("*.json")):
        destination = out / (source.stem + ".glb")
        district = out / (source.stem + "-architecture.glb")
        if checking:
            verify_footprint(source, destination)
            parts, rays = verify_architecture(source, district)
            print(f"{district.name}: {parts} structural parts and {rays} clear axial rays passed")
            print(f"{district.name}: registered approaches passed: {verify_approaches(source, destination)}")
        else:
            build(source, destination)
            build_architecture(source, district)
