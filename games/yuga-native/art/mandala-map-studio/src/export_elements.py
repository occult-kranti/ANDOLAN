"""Export or check the Mandala studio's registered standalone assets.

nice -n 12 blender -b mandala-rift.blend -t 1 --python-exit-code 1 --python src/export_elements.py
python3 src/export_elements.py --check
blender -b mandala-rift.blend -t 1 --python-exit-code 1 --python src/export_elements.py -- --roundtrip
"""

import argparse
import hashlib
import json
import math
import struct
import sys
import tempfile
from pathlib import Path

STUDIO = Path(__file__).resolve().parents[1]
MODELS = STUDIO / "models"
EPS = 1e-7


def area(poly):
    if len(poly) < 3:
        return 0.0
    a = poly[0]
    return (
        sum(
            (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
            for b, c in zip(poly[1:-1], poly[2:])
        )
        / 2
    )


def bounds_xy(poly):
    xs, ys = zip(*((p[0], p[1]) for p in poly))
    return min(xs), min(ys), max(xs), max(ys)


def touches(a, b):
    return a[0] <= b[2] and b[0] <= a[2] and a[1] <= b[3] and b[1] <= a[3]


def rectangle(x, y, w, h):
    return [
        (x - w / 2, y - h / 2),
        (x + w / 2, y - h / 2),
        (x + w / 2, y + h / 2),
        (x - w / 2, y + h / 2),
    ]


def masks(row):
    """Use the room/ribbon and twenty-sided bend geometry of atlas/massing.py."""
    if row["kind"] == "room":
        return [rectangle(*row["center_xyz"][:2], *row["size_m"])]
    points, width = row["points_xyz"], row["width_m"]
    if row["travel_kind"] == "fold":
        return [rectangle(*p[:2], width, width) for p in (points[0], points[-1])]
    polys = []
    for p, q in zip(points, points[1:]):
        dx, dy = q[0] - p[0], q[1] - p[1]
        k = width / (2 * math.hypot(dx, dy))
        sx, sy = -dy * k, dx * k
        polys.append(
            [
                (p[0] - sx, p[1] - sy),
                (q[0] - sx, q[1] - sy),
                (q[0] + sx, q[1] + sy),
                (p[0] + sx, p[1] + sy),
            ]
        )
    for p in points[1:-1]:
        polys.append(
            [
                (
                    p[0] + width / 2 * math.cos(i * math.tau / 20),
                    p[1] + width / 2 * math.sin(i * math.tau / 20),
                )
                for i in range(20)
            ]
        )
    return polys


def partition(poly, a, b):
    """Divide a 3D polygon at an oriented XY line, interpolating the real floor Z."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    ds = [dx * (p[1] - a[1]) - dy * (p[0] - a[0]) for p in poly]
    if min(ds) >= -EPS:
        return poly, []
    if max(ds) <= EPS:
        return [], poly
    inside, outside = [], []
    for j, p in enumerate(poly):
        k = (j + 1) % len(poly)
        if ds[j] >= -EPS:
            inside.append(p)
        if ds[j] <= EPS:
            outside.append(p)
        if (ds[j] < -EPS and ds[k] > EPS) or (ds[j] > EPS and ds[k] < -EPS):
            t = ds[j] / (ds[j] - ds[k])
            point = tuple(p[i] + t * (poly[k][i] - p[i]) for i in range(3))
            inside.append(point)
            outside.append(point)
    return inside, outside


def intersection_parts(triangle, box, shapes):
    # Each piece goes to the first mask that contains it. This preserves a single
    # floor surface where two ribbons and a rounded bend overlap.
    pending = [triangle]
    for boundary, limits in shapes:
        if not pending or not touches(box, limits):
            continue
        remaining = []
        for poly in pending:
            if not touches(bounds_xy(poly), limits):
                remaining.append(poly)
                continue
            for a, b in zip(boundary, boundary[1:] + boundary[:1]):
                poly, exterior = partition(poly, a, b)
                if abs(area(exterior)) > EPS:
                    remaining.append(exterior)
                if abs(area(poly)) <= EPS:
                    break
            else:
                yield poly
        pending = remaining


class Floor:
    def __init__(self, obj):
        self.materials = list(obj.data.materials)
        points = [tuple(obj.matrix_world @ v.co) for v in obj.data.vertices]
        obj.data.calc_loop_triangles()
        self.triangles = []
        for tri in obj.data.loop_triangles:
            face = [points[i] for i in tri.vertices]
            if self.materials[tri.material_index].name != "Skirt" and abs(area(face)) > EPS:
                self.triangles.append((face, bounds_xy(face), tri.material_index))

    def patch(self, row, collection):
        import bpy

        shapes = [(p, bounds_xy(p)) for p in masks(row)]
        vertices, faces, slots, known = [], [], [], {}
        for triangle, box, material in self.triangles:
            for poly in intersection_parts(triangle, box, shapes):
                indices = []
                for p in poly:
                    key = tuple(round(x, 6) for x in p)
                    if key not in known:
                        known[key] = len(vertices)
                        vertices.append(p)
                    indices.append(known[key])
                for b, c in zip(indices[1:-1], indices[2:]):
                    tri = (indices[0], b, c)
                    if abs(area([vertices[i] for i in tri])) <= EPS:
                        continue
                    faces.append(tri)
                    slots.append(material)
        if not faces:
            raise ValueError(f"No floor under {row['id']}")
        data = bpy.data.meshes.new("Registered floor cut")
        data.from_pydata(vertices, [], faces)
        for material in self.materials:
            data.materials.append(material)
        data.polygons.foreach_set("material_index", slots)
        data.update()
        obj = bpy.data.objects.new("Surveyed floor · " + row["id"], data)
        collection.objects.link(obj)
        return obj


def read_glb(path):
    data = path.read_bytes()
    if data[:4] != b"glTF" or struct.unpack_from("<II", data, 4) != (2, len(data)):
        raise ValueError(f"Invalid glTF header: {path}")
    length, kind = struct.unpack_from("<I4s", data, 12)
    end = 20 + length
    binary_length, binary_kind = struct.unpack_from("<I4s", data, end)
    if kind != b"JSON" or binary_kind != b"BIN\x00" or end + 8 + binary_length != len(data):
        raise ValueError(f"Invalid binary chunks: {path}")
    return json.loads(data[20:end]), data[end + 8 :]


def write_glb(path, doc, binary):
    desc = json.dumps(doc, ensure_ascii=False, separators=(",", ":")).encode()
    desc += b" " * (-len(desc) % 4)
    with path.open("wb") as f:
        f.write(
            struct.pack("<4sIIII", b"glTF", 2, 28 + len(desc) + len(binary), len(desc), 0x4E4F534A)
        )
        f.write(desc)
        f.write(struct.pack("<I4s", len(binary), b"BIN\x00"))
        f.write(binary)


def translation(point):
    x, y, z = point
    return [x, z, -y]


def local_matrix(n):
    if "matrix" in n:
        return [tuple(n["matrix"][j * 4 + i] for j in range(4)) for i in range(4)]
    x, y, z, w = n.get("rotation", [0, 0, 0, 1])
    sx, sy, sz = n.get("scale", [1, 1, 1])
    tx, ty, tz = n.get("translation", [0, 0, 0])
    return [
        (
            (1 - 2 * y * y - 2 * z * z) * sx,
            (2 * x * y - 2 * z * w) * sy,
            (2 * x * z + 2 * y * w) * sz,
            tx,
        ),
        (
            (2 * x * y + 2 * z * w) * sx,
            (1 - 2 * x * x - 2 * z * z) * sy,
            (2 * y * z - 2 * x * w) * sz,
            ty,
        ),
        (
            (2 * x * z - 2 * y * w) * sx,
            (2 * y * z + 2 * x * w) * sy,
            (1 - 2 * x * x - 2 * y * y) * sz,
            tz,
        ),
        (0, 0, 0, 1),
    ]


def compose(a, b):
    return [tuple(sum(x * y for x, y in zip(row, col)) for col in zip(*b)) for row in a]


def inspect(path):
    doc, binary = read_glb(path)
    buffers = doc["buffers"]
    if (
        len(buffers) != 1
        or "uri" in buffers[0]
        or not 0 <= len(binary) - buffers[0]["byteLength"] <= 3
    ):
        raise ValueError(f"{path}: external or truncated buffer")
    for view in doc["bufferViews"]:
        if (
            view.get("buffer", 0) != 0
            or view.get("byteOffset", 0) + view["byteLength"] > buffers[0]["byteLength"]
        ):
            raise ValueError(f"{path}: unbound data view")
    for image in doc.get("images", []):
        if "uri" in image or "bufferView" not in image:
            raise ValueError(f"{path}: image needs an external file")

    def values(idx):
        acc = doc["accessors"][idx]
        v = doc["bufferViews"][acc["bufferView"]]
        fmt = {5121: "B", 5123: "H", 5125: "I", 5126: "f"}[acc["componentType"]]
        count = {"VEC3": 3, "SCALAR": 1}[acc["type"]]
        item = struct.Struct("<" + str(count) + fmt)
        start = acc.get("byteOffset", 0)
        stride = v.get("byteStride", item.size)
        if start + (acc["count"] - 1) * stride + item.size > v["byteLength"]:
            raise ValueError(f"{path}: truncated accessor")
        off = v.get("byteOffset", 0) + start
        return [item.unpack_from(binary, off + i * stride) for i in range(acc["count"])]

    primitive_data = []
    for mesh in doc["meshes"]:
        parts = []
        for primitive in mesh["primitives"]:
            if primitive.get("mode", 4) != 4 or "indices" not in primitive:
                raise ValueError(f"{path}: expected indexed triangles")
            pts = values(primitive["attributes"]["POSITION"])
            ids = values(primitive["indices"])
            if (
                not pts
                or not ids
                or len(ids) % 3
                or max(i[0] for i in ids) >= len(pts)
                or not all(math.isfinite(k) for pt in pts for k in pt)
            ):
                raise ValueError(f"{path}: invalid indices or positions")
            parts.append((pts, len(ids) // 3))
        primitive_data.append(parts)
    lower, upper = [math.inf] * 3, [-math.inf] * 3
    triangles = instances = 0

    def walk(idx, parent):
        nonlocal triangles, instances
        node = doc["nodes"][idx]
        mat = compose(parent, local_matrix(node))
        if "mesh" in node:
            instances += 1
            for points, count in primitive_data[node["mesh"]]:
                triangles += count
                for row, k in zip(mat, range(3)):
                    p, q, r, t = row
                    coord = [p * x + q * y + r * z + t for x, y, z in points]
                    lower[k] = min(lower[k], min(coord))
                    upper[k] = max(upper[k], max(coord))
        for child in node.get("children", []):
            walk(child, mat)

    for node in doc["scenes"][doc["scene"]]["nodes"]:
        walk(node, local_matrix({}))
    if (
        not instances
        or not triangles
        or not all(map(math.isfinite, lower + upper))
        or max(b - a for a, b in zip(lower, upper)) < 0.01
    ):
        raise ValueError(f"{path}: no usable geometry")
    return [lower, upper], triangles, instances


def close_bounds(a, b):
    return max(abs(x - y) for p, q in zip(a, b) for x, y in zip(p, q)) < 0.001


def blender_bounds(objects, origin):
    import numpy as np

    objects = [o for o in objects if o.type == "MESH"]
    lo = np.full(3, np.inf)
    hi = -lo.copy()
    for obj in objects:
        vertices = np.empty(len(obj.data.vertices) * 3, dtype=np.float32)
        obj.data.vertices.foreach_get("co", vertices)
        mat = np.array(obj.matrix_world)
        xyz = vertices.reshape(-1, 3) @ mat[:3, :3].T + mat[:3, 3] - np.array(origin)
        gltf = xyz[:, [0, 2, 1]]
        gltf[:, 2] *= -1
        lo = np.minimum(lo, np.amin(gltf, axis=0))
        hi = np.maximum(hi, np.amax(gltf, axis=0))
    return [lo.tolist(), hi.tolist()]


def group(row, catalog):
    import bpy

    own = set(bpy.data.collections[row["id"]].all_objects)
    if row["kind"] != "room":
        return own
    key = row["source_key"]
    x, y, _ = row["center_xyz"]
    w, h = row["size_m"]
    for item in catalog:
        if item["kind"] not in ("artifact", "cover", "architecture"):
            continue
        col = bpy.data.collections[item["id"]]
        if item["id"] == "artifact-fold-lintels":
            inside = {
                i
                for i, p in enumerate(item["placements_xyz"])
                if abs(p[0] - x) <= w / 2 and abs(p[1] - y) <= h / 2
            }
            own.update(o for o in col.all_objects if o.get("socket_index", -1) in inside)
        elif item.get("host") == key:
            own.update(col.all_objects)
    return own


def build(studio, destination):
    import bpy

    if not bpy.data.filepath:
        bpy.ops.wm.open_mainfile(filepath=str(studio / "mandala-rift.blend"))
    cat = json.loads((studio / "catalog.json").read_text())
    rows = cat["elements"]
    if bpy.context.scene.get("layout_sha256") != cat["layout_sha256"]:
        raise ValueError("Open the matching, finished mandala-rift.blend")
    floor = Floor(next(iter(bpy.data.collections["base-floor"].all_objects)))
    destination.mkdir(parents=True, exist_ok=True)
    manifest = {
        "schema": 1,
        "units": "meters",
        "axes": ["east", "up", "south"],
        "placement": "Add origin_gltf_m to the model root in a metre-scale glTF scene. origin_map_xyz_m is east, north, up in the source Blender scene.",
        "source_blend": "../mandala-rift.blend",
        "layout_sha256": cat["layout_sha256"],
        "models": {},
    }
    with tempfile.TemporaryDirectory(dir=destination) as directory:
        stage = Path(directory)
        for row in rows:
            key = row["id"]
            objs = group(row, rows)
            patch = None
            origin = row["center_xyz"]
            location = translation(origin)
            if row["kind"] in ("room", "route"):
                patch = floor.patch(row, bpy.context.scene.collection)
                objs.add(patch)
            bpy.context.view_layer.update()
            wbox = blender_bounds(objs, origin)
            bpy.ops.object.select_all(action="DESELECT")
            for o in objs:
                o.select_set(True)
            path = stage / (key + ".glb")
            bpy.ops.export_scene.gltf(
                filepath=str(path),
                export_format="GLB",
                use_selection=True,
                export_yup=True,
                export_animations=False,
                export_extras=False,
                export_texcoords=True,
                export_normals=True,
                export_tangents=True,
                export_all_influences=False,
            )
            doc, binary = read_glb(path)
            scene = doc["scenes"][doc["scene"]]
            root = len(doc["nodes"])
            doc["nodes"].append(
                {"name": key, "children": scene["nodes"], "translation": [-v for v in location]}
            )
            scene["nodes"] = [root]
            write_glb(path, doc, binary)
            bounds, triangles, instances = inspect(path)
            if not close_bounds(bounds, wbox):
                raise ValueError(f"{key} source/GLB extents differ: {wbox}, {bounds}")
            info = {
                "file": path.name,
                "bytes": path.stat().st_size,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "origin_map_xyz_m": origin,
                "origin_gltf_m": location,
                "bounds_local_gltf_m": [[round(v, 5) for v in pt] for pt in bounds],
                "size_m": [round(b - a, 5) for a, b in zip(*bounds)],
                "triangles": triangles,
                "mesh_instances": instances,
                "floor_triangles": len(patch.data.polygons) if patch else 0,
            }
            donors = sorted(
                {str(o["donor_collection"]) for o in objs if o.get("donor_collection")}
            )
            if donors:
                info["donor_collections"] = donors
            manifest["models"][key] = info
            if patch:
                mesh = patch.data
                bpy.data.objects.remove(patch, do_unlink=True)
                bpy.data.meshes.remove(mesh)
        index = stage / "index.json"
        index.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
        for asset in stage.glob("*.glb"):
            asset.replace(destination / asset.name)
        index.replace(destination / "index.json")


def check(studio, destination):
    cat = json.loads((studio / "catalog.json").read_text())
    index = json.loads((destination / "index.json").read_text())
    if (
        set(index["models"]) != {r["id"] for r in cat["elements"]}
        or index["layout_sha256"] != cat["layout_sha256"]
    ):
        raise ValueError("Model catalog does not match the registered district")
    for row in cat["elements"]:
        key = row["id"]
        rec = index["models"][key]
        path = destination / rec["file"]
        bounds, triangles, instances = inspect(path)
        if (
            hashlib.sha256(path.read_bytes()).hexdigest() != rec["sha256"]
            or path.stat().st_size != rec["bytes"]
            or triangles != rec["triangles"]
            or instances != rec["mesh_instances"]
            or rec["origin_gltf_m"] != translation(row["center_xyz"])
            or not close_bounds(bounds, rec["bounds_local_gltf_m"])
            or ((row["kind"] in ("room", "route")) != (rec["floor_triangles"] > 0))
        ):
            raise ValueError(f"Geometry or registration mismatch: {key}")
    print(f"Verified {len(index['models'])} embedded, indexed glTF models against the catalog.")


def roundtrip(studio, destination):
    """Re-import representative exports and probe their restored surfaces against the blend."""
    import bpy
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree

    if not bpy.data.filepath:
        bpy.ops.wm.open_mainfile(filepath=str(studio / "mandala-rift.blend"))
    catalog = {r["id"]: r for r in json.loads((studio / "catalog.json").read_text())["elements"]}
    records = json.loads((destination / "index.json").read_text())["models"]

    def surface(obj, origin):
        points = [obj.matrix_world @ v.co + Vector(origin) for v in obj.data.vertices]
        return BVHTree.FromPolygons(points, [tuple(f.vertices) for f in obj.data.polygons])

    def height(tree, p):
        hit = tree.ray_cast((p[0], p[1], 40), (0, 0, -1), 80)[0]
        return hit.z if hit is not None else None

    source = surface(next(iter(bpy.data.collections["base-floor"].all_objects)), (0, 0, 0))
    # Includes the model using packed donor normal maps and an off-origin fixture.
    cases = [
        "room-pyramid_n",
        "route-mid-b-ramp",
        "route-steps_s-ford-water",
        "route-temple_s-pyramid_s-fold",
        "route-temple_n-pyramid_n-fold",
        "architecture-quarter-turn-pavilion",
        "rite-water-ewer",
    ]
    count = 0
    for key in cases:
        record, row = records[key], catalog[key]
        before = set(bpy.context.scene.objects)
        bpy.ops.import_scene.gltf(filepath=str(destination / record["file"]))
        imported = set(bpy.context.scene.objects) - before
        bounds = blender_bounds(imported, [0, 0, 0])
        if not close_bounds(bounds, record["bounds_local_gltf_m"]):
            raise ValueError(f"{key}: Blender re-import lost local registration")
        if row["kind"] in ("room", "route"):
            (floor,) = [o for o in imported if o.name.startswith("Surveyed floor")]
            sample = surface(floor, row["center_xyz"])
            if row["kind"] == "room":
                x, y, _ = row["center_xyz"]
                w, h = row["size_m"]
                probes = [(x, y), (x - w * 0.47, y - h * 0.47), (x + w * 0.47, y + h * 0.47)]
            elif row["travel_kind"] == "fold":
                p, q = row["points_xyz"][0], row["points_xyz"][-1]
                probes = [p, q, (p[0] + 0.8, p[1]), (q[0] - 0.8, q[1])]
                between = ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2)
                if height(sample, between) is not None:
                    raise ValueError(f"{key}: a floor bridge crosses the discontinuity")
            else:
                pts = row["points_xyz"]
                probes = []
                for a, b in zip(pts, pts[1:]):
                    probes.extend(
                        [
                            tuple(a[i] + (b[i] - a[i]) * u for i in (0, 1))
                            for u in (0.05, 0.5, 0.95)
                        ]
                    )
            for xy in probes:
                observed, expected = height(sample, xy), height(source, xy)
                if observed is None or expected is None or abs(observed - expected) > 0.001:
                    raise ValueError(
                        f"{key}: floor placement differs at {xy}: {observed} vs {expected}"
                    )
            count += len(probes)
        for obj in imported:
            bpy.data.objects.remove(obj, do_unlink=True)
    print(
        f"Reimported {len(cases)} model types; {count} restored floor points matched within 1 mm and both folds had open gaps."
    )


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--check", action="store_true")
    p.add_argument("--out", type=Path, default=MODELS)
    p.add_argument("--roundtrip", action="store_true")
    args = p.parse_args(
        sys.argv[sys.argv.index("--") + 1 :]
        if "--" in sys.argv
        else (sys.argv[1:] if "bpy" not in sys.modules else [])
    )
    if args.check:
        check(STUDIO, args.out)
    elif args.roundtrip:
        roundtrip(STUDIO, args.out)
    else:
        build(STUDIO, args.out)
