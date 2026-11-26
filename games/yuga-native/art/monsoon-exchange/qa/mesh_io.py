"""Read native and exported scene triangles independently, in Blender east/north/up metres."""

from collections import Counter
import json
import struct

import bpy
from mathutils import Matrix, Quaternion, Vector
from mathutils.bvhtree import BVHTree
import numpy as np


PROBED = {"floor", "wall", "cover", "ceiling"}


def need(ok, message):
    if not ok:
        raise ValueError(message)


class Triangles:
    def __init__(self):
        self.vertices = []
        self.faces = []
        self.owners = []
        self.tree = None

    def add(self, vertices, faces, owner):
        base = len(self.vertices)
        self.vertices.extend(vertices)
        self.faces.extend((a + base, b + base, c + base) for a, b, c in faces)
        self.owners.extend([owner] * len(faces))

    def index(self):
        if self.faces:
            self.tree = BVHTree.FromPolygons(
                self.vertices, self.faces, all_triangles=True
            )

    def ray(self, origin, direction, reach):
        if self.tree is None:
            return None
        point, normal, face, travel = self.tree.ray_cast(origin, direction, reach)
        return None if face is None else (point, normal, self.owners[face], travel)


class Build:
    def __init__(self):
        self.floor = Triangles()
        self.obstacles = Triangles()
        self.walls = {}
        self.roles = Counter()
        self.triangles = Counter()
        self.owners = {role: set() for role in PROBED}
        self.details = {}

    def add(self, role, owner, vertices, faces, wall_id=None):
        self.triangles[role] += len(faces)
        if role == "wall":
            need(wall_id, "Wall mesh has no survey ID")
            self.walls.setdefault(wall_id, Triangles()).add(vertices, faces, owner)
        if role in PROBED:
            self.owners[role].add(owner)
            target = self.floor if role == "floor" else self.obstacles
            target.add(vertices, faces, owner)

    def finish(self):
        self.floor.index()
        self.obstacles.index()
        for wall in self.walls.values():
            wall.index()
        need(
            self.floor.tree and self.obstacles.tree,
            "Missing actual floor or obstacle triangles",
        )
        return self


def drawn_objects(collection):
    if collection.hide_render:
        return set()
    eligible = {obj.name for obj in collection.objects if not obj.hide_render}
    for child in collection.children:
        eligible.update(drawn_objects(child))
    return eligible


def native_proxies(survey):
    guides = {
        obj.get("cover_id"): obj
        for obj in bpy.context.scene.objects
        if obj.type == "MESH" and obj.get("role") == "collision" and obj.get("cover_id")
    }
    require_ids = {c["id"] for c in survey["covers"]}
    need(
        set(guides) == require_ids,
        "Editable native scene lacks the surveyed set of cover guides",
    )
    max_error = 0.0
    for cover in survey["covers"]:
        obj = guides[cover["id"]]
        points = [obj.matrix_world @ Vector(p) for p in obj.bound_box]
        x, y = cover["center"]
        w, d, h = cover["size"]
        z = cover["z"]
        actual = [min(p[k] for p in points) for k in range(3)] + [
            max(p[k] for p in points) for k in range(3)
        ]
        expected = [x - w / 2, y - d / 2, z, x + w / 2, y + d / 2, z + h]
        max_error = max(max_error, max(abs(a - b) for a, b in zip(actual, expected)))
    need(
        max_error < 0.002, "Native cover authoring bounds deviate from the 2D register"
    )
    return {
        "hidden_editable_cover_guides": len(guides),
        "max_guide_extent_error_m": round(max_error, 6),
    }


def native_scene(filename):
    bpy.ops.wm.open_mainfile(filepath=str(filename))
    scene = bpy.context.scene
    deps = bpy.context.evaluated_depsgraph_get()
    result = Build()
    need(
        abs(scene.unit_settings.scale_length - 1.0) < 1e-6,
        "Blender unit scale must be 1 m",
    )
    external = [lib.name for lib in bpy.data.libraries if not lib.packed_file]
    external.extend(
        img.name
        for img in bpy.data.images
        if img.source in {"FILE", "TILED", "SEQUENCE", "MOVIE"}
        and img.filepath
        and not img.packed_files
    )
    external.extend(
        font.name for font in bpy.data.fonts if font.filepath and not font.packed_file
    )
    need(not external, "External scene dependencies: " + ", ".join(external))
    meshes = set()
    renderable = drawn_objects(scene.collection)
    for obj in scene.objects:
        if obj.type != "MESH" or obj.name not in renderable:
            continue
        role = obj.get("role", "unclassified")
        result.roles[role] += 1
        meshes.add(obj.data.name)
        if role not in PROBED:
            continue
        measured = obj.evaluated_get(deps)
        mesh = measured.to_mesh()
        try:
            mesh.calc_loop_triangles()
            vertices = [tuple(measured.matrix_world @ v.co) for v in mesh.vertices]
            faces = [tuple(t.vertices) for t in mesh.loop_triangles]
            owner = obj.get("cover_id") if role == "cover" else obj.get("element")
            result.add(role, owner or obj.name, vertices, faces, obj.get("wall_id"))
        finally:
            measured.to_mesh_clear()
    cameras = sorted(o.name for o in scene.objects if o.type == "CAMERA")
    need(len(cameras) >= 4, "Expected a district overview and three grounded cameras")
    result.details = {
        "units": scene.unit_settings.system,
        "metres_per_unit": scene.unit_settings.scale_length,
        "visible_mesh_objects": sum(result.roles.values()),
        "unique_mesh_data": len(meshes),
        "cameras": cameras,
        "packed_file_images": sum(bool(i.packed_files) for i in bpy.data.images),
        "external_assets": external,
    }
    return result.finish()


class Gltf:
    """GLB 2.0 arrays, node transforms, and embedded payload, independent of the Blender importer."""

    DTYPES = {
        5120: "i1",
        5121: "u1",
        5122: "<i2",
        5123: "<u2",
        5125: "<u4",
        5126: "<f4",
    }
    WIDTHS = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}

    def __init__(self, path):
        data = path.read_bytes()
        magic, version, length = struct.unpack_from("<4sII", data)
        need((magic, version, length) == (b"glTF", 2, len(data)), "Invalid GLB header")
        blocks = {}
        pos = 12
        while pos + 8 <= len(data):
            n, kind = struct.unpack_from("<I4s", data, pos)
            pos += 8
            need(pos + n <= len(data) and kind not in blocks, "Invalid GLB chunk")
            blocks[kind] = memoryview(data)[pos : pos + n]
            pos += n
        need(pos == len(data), "Invalid GLB chunk length")
        self.meta = json.loads(bytes(blocks[b"JSON"]))
        self.bin = blocks[b"BIN\0"]
        buffers = self.meta["buffers"]
        need(
            len(buffers) == 1 and "uri" not in buffers[0], "GLB has an external buffer"
        )
        need(
            0 <= len(self.bin) - buffers[0]["byteLength"] <= 3,
            "GLB buffer length mismatch",
        )
        for view in self.meta["bufferViews"]:
            need(
                view["buffer"] == 0
                and view.get("byteOffset", 0) + view["byteLength"] <= len(self.bin),
                "Out of range GLB view",
            )
        for image in self.meta.get("images", []):
            need(
                "bufferView" in image
                and "uri" not in image
                and image["mimeType"].startswith("image/"),
                "External/invalid texture",
            )
            need(
                self.meta["bufferViews"][image["bufferView"]]["byteLength"] > 0,
                "Empty texture",
            )
        self.arrays = {}

    def array(self, index):
        if index not in self.arrays:
            a = self.meta["accessors"][index]
            need("sparse" not in a, "Sparse accessor not used by this edition")
            v = self.meta["bufferViews"][a["bufferView"]]
            dtype, width = (
                np.dtype(self.DTYPES[a["componentType"]]),
                self.WIDTHS[a["type"]],
            )
            stride = v.get("byteStride", dtype.itemsize * width)
            local = a.get("byteOffset", 0)
            needed = local + (a["count"] - 1) * stride + width * dtype.itemsize
            need(
                a["count"] > 0
                and stride >= width * dtype.itemsize
                and needed <= v["byteLength"],
                "GLB accessor escapes its view",
            )
            self.arrays[index] = np.ndarray(
                (a["count"], width),
                dtype=dtype,
                buffer=self.bin,
                offset=v.get("byteOffset", 0) + local,
                strides=(stride, dtype.itemsize),
            )
        return self.arrays[index]

    @staticmethod
    def node_matrix(node):
        if "matrix" in node:
            return Matrix(np.array(node["matrix"]).reshape((4, 4), order="F"))
        x, y, z, w = node.get("rotation", [0, 0, 0, 1])
        return Matrix.LocRotScale(
            Vector(node.get("translation", [0, 0, 0])),
            Quaternion((w, x, y, z)),
            Vector(node.get("scale", [1, 1, 1])),
        )

    def scene(self):
        m = self.meta
        result = Build()
        seen = set()
        used_meshes = set()
        axis = Matrix(((1, 0, 0, 0), (0, 0, -1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))

        def walk(index, parent):
            need(index not in seen, "GLB node reused or cyclic in default scene")
            seen.add(index)
            node = m["nodes"][index]
            world = parent @ self.node_matrix(node)
            if "mesh" in node:
                used_meshes.add(node["mesh"])
                extra = node.get("extras", {})
                role = extra.get("role", "unclassified")
                owner = (
                    extra.get("cover_id") if role == "cover" else extra.get("element")
                )
                owner = owner or node.get("name", str(index))
                result.roles[role] += 1
                for prim in m["meshes"][node["mesh"]]["primitives"]:
                    need(prim.get("mode", 4) == 4, "Expected triangle GLB primitives")
                    coords = self.array(prim["attributes"]["POSITION"])
                    need(
                        coords.shape[1] == 3 and np.isfinite(coords).all(),
                        "Nonfinite GLB vertex",
                    )
                    indices = (
                        self.array(prim["indices"]).reshape(-1)
                        if "indices" in prim
                        else np.arange(len(coords))
                    )
                    need(
                        len(indices) % 3 == 0 and indices.max() < len(coords),
                        "Invalid GLB triangle indices",
                    )
                    if role in PROBED:
                        affine = np.asarray(world, dtype=float)
                        verts = coords @ affine[:3, :3].T + affine[:3, 3]
                        result.add(
                            role,
                            owner,
                            verts.tolist(),
                            indices.reshape(-1, 3).tolist(),
                            extra.get("wall_id"),
                        )
                    else:
                        result.triangles[role] += len(indices) // 3
            for child in node.get("children", []):
                walk(child, world)

        for node in m["scenes"][m.get("scene", 0)]["nodes"]:
            walk(node, axis)
        result.details = {
            "unit": "metre",
            "glTF_to_Blender": "[x, -z, y]",
            "default_scene_nodes": len(seen),
            "mesh_instances": sum(result.roles.values()),
            "unique_meshes_used": len(used_meshes),
            "triangles_at_all_instances": sum(result.triangles.values()),
            "materials": len(m.get("materials", [])),
            "embedded_images": len(m.get("images", [])),
            "external_assets": [],
        }
        return result.finish()
