"""Verify the ground-only glTF edit and register rebuilt vertices against the compiled map.

Dependencies for this inspection are NumPy and SciPy. Neither library is part of the game.
All samples are drawn from the original BSP. No exporter manifest defines coverage counts.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import copy
import hashlib
import json
import math
from pathlib import Path
import struct

import numpy as np
from scipy.spatial import cKDTree
from scipy.spatial.transform import Rotation

from native import Bsp, insist, texture_chain


GLTF_TYPES = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}
COMPONENTS = {
    5120: "i1",
    5121: "u1",
    5122: "<i2",
    5123: "<u2",
    5125: "<u4",
    5126: "<f4",
}


def file_sha(path):
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


class Glb:
    def __init__(self, path):
        self.path = Path(path)
        length = self.path.stat().st_size
        with self.path.open("rb") as f:
            magic, version, size = struct.unpack("<4sII", f.read(12))
            insist((magic, version, size) == (b"glTF", 2, length), "Invalid GLB header")
            count, kind = struct.unpack("<I4s", f.read(8))
            insist(kind == b"JSON" and count <= length - 28, "Invalid JSON chunk")
            self.doc = json.loads(f.read(count))
            nb, kind = struct.unpack("<I4s", f.read(8))
            insist(
                kind == b"BIN\0" and nb == length - f.tell(),
                "Expected one embedded BIN chunk",
            )
            self.binary = np.memmap(
                self.path, mode="r", offset=f.tell(), dtype="u1", shape=(nb,)
            )
        buffers = self.doc["buffers"]
        insist(
            len(buffers) == 1
            and "uri" not in buffers[0]
            and 0 <= nb - buffers[0]["byteLength"] <= 3,
            "Expected a single self-contained GLB",
        )
        for image in self.doc.get("images", []):
            insist(
                "bufferView" in image and "uri" not in image,
                "External images cannot be frozen by this check",
            )

    def accessor(self, i):
        acc = self.doc["accessors"][i]
        insist("sparse" not in acc, "Sparse accessors require a separate comparison")
        view = self.doc["bufferViews"][acc["bufferView"]]
        width = GLTF_TYPES[acc["type"]]
        dtype = np.dtype(COMPONENTS[acc["componentType"]])
        size = dtype.itemsize * width
        stride = view.get("byteStride", size)
        count = acc["count"]
        local = acc.get("byteOffset", 0)
        insist(
            view["buffer"] == 0
            and (count - 1) * stride + size + local <= view["byteLength"]
            and stride >= size,
            "Accessor exceeds its view",
        )
        return np.ndarray(
            (count, width),
            dtype=dtype,
            buffer=self.binary,
            offset=view.get("byteOffset", 0) + local,
            strides=(stride, dtype.itemsize),
        )

    def root_matrices(self):
        def walk(idx, parent, parents):
            insist(idx not in parents, "Scene contains a cycle")
            n = self.doc["nodes"][idx]
            m = parent @ local_matrix(n)
            yield n, m
            for child in n.get("children", []):
                yield from walk(child, m, parents | {idx})

        roots = self.doc["scenes"][self.doc.get("scene", 0)]["nodes"]
        for root in roots:
            yield from walk(root, np.eye(4), set())

    def groups(self):
        for node, mat in self.root_matrices():
            if "mesh" not in node:
                continue
            mesh = self.doc["meshes"][node["mesh"]]
            for j, prim in enumerate(mesh["primitives"]):
                insist(
                    prim.get("mode", 4) == 4 and "POSITION" in prim["attributes"],
                    "Expected a triangle mesh",
                )
                verts = self.accessor(prim["attributes"]["POSITION"])
                insist(
                    verts.shape[1] == 3 and np.isfinite(verts).all(),
                    "Mesh has invalid coordinates",
                )
                if "indices" in prim:
                    indices = self.accessor(prim["indices"]).ravel()
                else:
                    indices = np.arange(len(verts))
                insist(
                    len(indices) % 3 == 0
                    and len(indices) > 0
                    and indices.max() < len(verts),
                    "Invalid triangle indices",
                )
                world = verts @ mat[:3, :3].T + mat[:3, 3]
                yield (node, prim, j, world, indices.reshape(-1, 3))


def local_matrix(n):
    if "matrix" in n:
        return np.array(n["matrix"], dtype=float).reshape(4, 4).T
    qx, qy, qz, qw = n.get("rotation", (0.0, 0.0, 0.0, 1.0))
    scale = np.array(n.get("scale", (1.0, 1.0, 1.0)))
    m = np.eye(4)
    m[:3, :3] = (
        np.array(
            [
                [
                    1 - 2 * (qy * qy + qz * qz),
                    2 * (qx * qy - qz * qw),
                    2 * (qx * qz + qy * qw),
                ],
                [
                    2 * (qx * qy + qz * qw),
                    1 - 2 * (qx * qx + qz * qz),
                    2 * (qy * qz - qx * qw),
                ],
                [
                    2 * (qx * qz - qy * qw),
                    2 * (qy * qz + qx * qw),
                    1 - 2 * (qx * qx + qy * qy),
                ],
            ]
        )
        * scale
    )
    m[:3, 3] = n.get("translation", (0.0, 0.0, 0.0))
    return m


def compare_materials(original, variant):
    a, b = original.doc, variant.doc
    bin_a = hashlib.sha256(original.binary).hexdigest()
    bin_b = hashlib.sha256(variant.binary).hexdigest()
    insist(
        bin_a == bin_b,
        "Binary chunks differ; positions, indices, UVs, textures or other binary data changed",
    )
    work = copy.deepcopy(b)
    baseline = a["materials"]
    updated = work["materials"]
    changes = []
    insist(
        len(baseline) == len(updated),
        "New materials should already be staged in the reference scene",
    )
    for i, (orig, change) in enumerate(zip(baseline, updated)):
        p0 = orig.get("pbrMetallicRoughness", {})
        p1 = change.get("pbrMetallicRoughness", {})
        c0 = p0.get("baseColorFactor", [1, 1, 1, 1])
        c1 = p1.get("baseColorFactor", [1, 1, 1, 1])
        is_ground = orig.get("extras", {}).get("yugaGround", False) is True
        if is_ground:
            insist(
                c0 != c1 and len(c1) == len(c0) == 4 and c0[3] == c1[3],
                f"No RGB-only change on ground material {i}",
            )
            insist(
                all(math.isfinite(c) and 0 <= c <= 1 for c in c1),
                f"Invalid color on material {i}",
            )
            changes.append(
                {
                    "id": i,
                    "name": orig.get("name"),
                    "source": orig.get("extras", {}).get("sourceMaterial"),
                    "before": c0,
                    "after": c1,
                }
            )
            if "baseColorFactor" in p0:
                p1["baseColorFactor"] = p0["baseColorFactor"]
            else:
                p1.pop("baseColorFactor", None)
    insist(
        changes and work == a,
        "Non-ground material, node, mesh, texture, transform, geometry or metadata changed",
    )
    return changes, bin_a


def ground_stats(original, changes):
    selected = {p["id"] for p in changes}
    bounds = np.array([[np.inf] * 3, [-np.inf] * 3])
    ground_bounds = bounds.copy()
    area = 0.0
    min_up = 1.0
    triangles = 0
    ground_triangles = 0
    degenerate_ground = 0
    instances = 0
    primitive_uses = 0
    unique_materials = set()
    # Keep one copy of each placed vertex, not expanded triangles, for independent registration.
    # Large props can repeat thousands of times; only BSP architectural vertices need to feed the tree.
    all_vertices = []
    ground_vertices = []
    for n, m in original.root_matrices():
        if "mesh" in n:
            instances += 1
    for node, primitive, _, points, indices in original.groups():
        ntri = len(indices)
        triangles += ntri
        primitive_uses += 1
        verts = points[np.unique(indices)]
        bounds[0] = np.minimum(bounds[0], verts.min(axis=0))
        bounds[1] = np.maximum(bounds[1], verts.max(axis=0))
        if "sourceModel" in node.get("extras", {}):
            all_vertices.append(verts.astype(np.float32, copy=False))
        if primitive.get("material") not in selected:
            continue
        unique_materials.add(primitive["material"])
        ground_triangles += ntri
        ground_vertices.append(verts.astype(np.float32, copy=False))
        ground_bounds[0] = np.minimum(ground_bounds[0], verts.min(axis=0))
        ground_bounds[1] = np.maximum(ground_bounds[1], verts.max(axis=0))
        for start in range(0, ntri, 8192):
            face = points[indices[start : start + 8192]]
            norm = np.cross(face[:, 1] - face[:, 0], face[:, 2] - face[:, 0])
            mag = np.linalg.norm(norm, axis=1)
            live = mag > 1e-8
            if live.any():
                y = norm[live, 1] / mag[live]
                min_up = min(min_up, float(y.min()))
            area += float(mag.sum()) / 2
            degenerate_ground += int((~live).sum())
    insist(
        unique_materials == selected,
        "A changed ground material has no visible triangles",
    )
    insist(
        all_vertices and ground_vertices and 0 < ground_triangles < triangles,
        "Ground selection or mesh span is empty",
    )
    stats = {
        "triangles_instanced": triangles,
        "ground_triangles": ground_triangles,
        "fixed_non_ground_triangles": triangles - ground_triangles,
        "placed_mesh_nodes": instances,
        "placed_primitives": primitive_uses,
        "mesh_count": len(original.doc["meshes"]),
        "scene_node_count": len(original.doc["nodes"]),
        "material_count": len(original.doc["materials"]),
        "ground_area_m2": round(area, 4),
        "minimum_signed_ground_normal_y": round(min_up, 6),
        "steepest_geometric_ground_deg": round(
            math.degrees(math.acos(max(-1.0, min(1.0, min_up)))), 4
        ),
        "degenerate_ground_triangles": degenerate_ground,
        "all_bounds_gltf_m": bounds.round(5).tolist(),
        "ground_bounds_gltf_m": ground_bounds.round(5).tolist(),
    }
    return stats, np.concatenate(all_vertices), np.concatenate(ground_vertices)


def source_samples(bsp):
    """Use the native polygon's extreme base vertices or the grid diagonal and centre.

    A bilinear quad centre is the mean of its four corners independent of UV/grid
    axis convention. Both end corners and the centre have unambiguous dispvert slots.
    """
    verts = np.frombuffer(bsp.get(3), dtype="<f4").reshape(-1, 3)
    edges = np.frombuffer(bsp.get(12), dtype="<u2").reshape(-1, 2)
    surf = np.frombuffer(bsp.get(13), dtype="<i4")
    dispvert = np.frombuffer(bsp.get(33), dtype="<f4").reshape(-1, 5)
    face = bsp.get(7)
    disp = bsp.get(26)
    names = bsp.texture_names()
    texnames = [
        names[texture_chain(bsp, i)[1]].lower() for i in range(bsp.count(6, 72))
    ]
    models = bsp.models()
    model = models[0]
    entity_xforms = {}
    for e in bsp.entities():
        name = e.get("model", "")
        if name.startswith("*") and name[1:].isdigit():
            idx = int(name[1:])
            pitch, yaw, roll = (float(x) for x in e.get("angles", "0 0 0").split())
            rot = Rotation.from_euler(
                "ZYX", (yaw, pitch, roll), degrees=True
            ).as_matrix()
            origin = np.array([float(x) for x in e.get("origin", "0 0 0").split()])
            for j in range(models[idx][10], models[idx][10] + models[idx][11]):
                entity_xforms[j] = (rot, origin)
    world_range = range(model[10], model[10] + model[11])
    samples = []
    for f in range(bsp.count(7, 56)):
        first, nedges, ti, di = struct.unpack_from("<ihhh", face, 56 * f + 4)
        if ti < 0 or nedges < 3:
            continue
        tex = texnames[ti]
        (flags,) = struct.unpack_from("<i", bsp.get(6), ti * 72 + 64)
        seg = surf[first : first + nedges]
        points = verts[edges[np.abs(seg), (seg < 0).astype(np.intp)]]
        if di >= 0:
            at = di * 176
            start = np.array(struct.unpack_from("<3f", disp, at))
            firstdisp, _, p = struct.unpack_from("<iii", disp, at + 12)
            size = 2**p + 1
            insist(nedges == 4, f"Displacement {di} has {nedges} base edges")
            corner = int(np.argmin(np.linalg.norm(points - start, axis=1)))
            positions = np.array(
                [points[corner], points.mean(axis=0), points[(corner + 2) % 4]]
            )
            offsets = dispvert[
                [firstdisp, firstdisp + (size * size) // 2, firstdisp + size * size - 1]
            ]
            vertices = positions + offsets[:, :3] * offsets[:, 3, None]
        else:
            # Opposite base vertices work with either winding and common fan triangulation.
            vertices = points[[0, len(points) // 2, -1]]
        if f in entity_xforms:
            rot, origin = entity_xforms[f]
            vertices = vertices @ rot.T + origin
        vertices = vertices[:, [0, 2, 1]].astype("f8") * 0.0254
        vertices[:, 2] *= -1
        source_kind = "world" if f in world_range else "brush_entity"
        visual = not (tex.startswith("tools/") or flags & (0x02 | 0x04 | 0x80))
        samples.append((f, source_kind, visual, di >= 0, tex, vertices))
    return samples


def registration(bsp, all_points, ground_points, ground_ids, epsilon):
    rows = source_samples(bsp)
    query = np.concatenate([r[-1] for r in rows])
    result = {}
    # cKDTree leaves still compare measured metre coordinates; duplicate vertices cost memory without adding evidence.
    for group, points in [("architectural", all_points), ("ground", ground_points)]:
        unique = np.unique(points, axis=0)
        tree = cKDTree(unique)
        dist, _ = tree.query(query, k=1, distance_upper_bound=epsilon)
        result[group] = np.isfinite(dist).reshape(len(rows), 3)
    counts = defaultdict(Counter)
    misses = defaultdict(list)
    primary = Counter()
    for j, (f, kind, visual, disp, tex, vec) in enumerate(rows):
        buckets = [kind + ("_visible" if visual else "_tool_or_invisible")]
        if kind == "world" and visual and disp:
            buckets.append("visible_world_displacement")
        for name in buckets:
            counts[name]["source_faces"] += 1
            value = result["architectural"][j]
            counts[name]["all_three_registered"] += int(np.all(value))
            counts[name]["any_registered"] += int(np.any(value))
            if not np.all(value):
                misses[name].append(f)
        if ground_ids is not None and f in ground_ids:
            value = result["ground"][j]
            primary["selected_source_faces"] += 1
            primary["all_three_on_ground_material"] += int(np.all(value))
            primary["any_on_ground_material"] += int(np.any(value))
            if not np.all(value):
                misses["ground"].append(f)
    if ground_ids is not None:
        insist(
            primary["selected_source_faces"] == len(ground_ids),
            "A selected face is missing from the BSP",
        )
    for category in (
        "world_visible",
        "visible_world_displacement",
        "brush_entity_visible",
    ):
        if category in counts:
            item = counts[category]
            insist(
                item["source_faces"] == item["all_three_registered"],
                f"Native vertices did not register for {category}: {misses.get(category, [])[:10]}",
            )
    if ground_ids is not None:
        insist(
            primary["selected_source_faces"] == primary["all_three_on_ground_material"],
            "Native floor witnesses missing",
        )
    return {
        "tolerance_m": epsilon,
        "method": "Three original Source positions per face, converted to (x,z,-y) in metres; displaced diagonal endpoints and bilinear centre use original displacement vectors. Counts accept only positions found within the given Euclidean tolerance.",
        "face_classes": dict(counts),
        "selected_ground": dict(primary),
        "unmatched_face_id_examples": {k: v[:20] for k, v in misses.items()},
        "limitations": "Vertex registration tests sampled shape and placement. The native-lump comparison checks full compiled contents. Invisible utility faces are counted separately.",
    }


def crosscheck_source_ledger(bsp, glb, ground_ids):
    """Match native brush ranges and all static prop sockets to independently read records."""

    models = bsp.models()
    faces = bsp.get(7)
    classes = {}
    for entity in bsp.entities():
        brush = entity.get("model", "")
        if brush.startswith("*") and brush[1:].isdigit():
            classes[int(brush[1:])] = entity
    names = bsp.texture_names()
    infos = [names[texture_chain(bsp, i)[1]].lower() for i in range(bsp.count(6, 72))]
    invisible = {
        "func_areaportal",
        "func_occluder",
        "func_buyzone",
        "func_bomb_target",
        "func_clip_vphysics",
    }
    eligible = set()
    material_by_face = {}
    for model_id, model in enumerate(models):
        name = classes.get(model_id, {}).get("classname", "")
        if name in invisible or name.startswith("trigger_"):
            continue
        for f in range(model[10], model[10] + model[11]):
            (ti,) = struct.unpack_from("<h", faces, f * 56 + 10)
            (flags,) = struct.unpack_from("<i", bsp.get(6), ti * 72 + 64)
            if ti >= 0 and not (
                flags & (2 | 4 | 128) or infos[ti].startswith("tools/")
            ):
                eligible.add(f)
                material_by_face[f] = infos[ti]
    registered = set()
    changed_ids = set()
    model_ids = set()
    static_nodes = {}
    overlay_lump = bsp.get(45)
    native_overlays = {}
    for start in range(0, len(overlay_lump), 352):
        overlay_id, ti, tag = struct.unpack_from("<ihH", overlay_lump, start)
        face_ids = struct.unpack_from(
            "<" + str(tag & 0x3FFF) + "i", overlay_lump, start + 8
        )
        native_overlays[overlay_id] = (list(face_ids), tag >> 14, infos[ti])
    overlay_triangles = 0
    registered_overlays = set()
    tri_count = 0
    for node, mat in glb.root_matrices():
        e = node.get("extras", {})
        if "sourceStaticPropIndex" in e:
            j = e["sourceStaticPropIndex"]
            insist(
                j not in static_nodes and "mesh" in node,
                "Duplicate or geometry-free static placement",
            )
            static_nodes[j] = (node, mat)
        if "sourceOverlayId" in e:
            idx = e["sourceOverlayId"]
            insist(
                idx in native_overlays and idx not in registered_overlays,
                "Invalid or duplicate native overlay",
            )
            registered_overlays.add(idx)
            faces_original, order, material = native_overlays[idx]
            insist(
                e["sourceOverlayFaces"] == faces_original
                and e["sourceRenderOrder"] == order,
                "Overlay faces or order changed",
            )
            for prim in glb.doc["meshes"][node["mesh"]]["primitives"]:
                tex = glb.doc["materials"][prim["material"]]["extras"]
                insist(
                    tex["sourceMaterial"].lower() == material
                    and tex["yugaGround"] is False,
                    "Overlay shader assignment changed",
                )
                overlay_triangles += glb.doc["accessors"][prim["indices"]]["count"] // 3
        if "sourceModel" not in e:
            continue
        model = e["sourceModel"]
        insist(
            model not in model_ids and 0 <= model < len(models),
            "Invalid brush model index",
        )
        model_ids.add(model)
        if "mesh" not in node:
            continue
        for prim in glb.doc["meshes"][node["mesh"]]["primitives"]:
            extra = prim.get("extras", {})
            runs = extra.get("faceTriangleRuns")
            if runs is None:
                continue
            if extra.get("sourceModel") != model:
                raise ValueError("Primitive registered on wrong brush model")
            total = 0
            for face_id, ntri in runs:
                insist(
                    face_id not in registered
                    and ntri > 0
                    and models[model][10]
                    <= face_id
                    < models[model][10] + models[model][11],
                    "Missing, repeated or misplaced dface entry",
                )
                registered.add(face_id)
                total += ntri
                matinfo = glb.doc["materials"][prim["material"]].get("extras", {})
                insist(
                    matinfo.get("sourceMaterial", "").lower()
                    == material_by_face.get(face_id),
                    f"Material assignment changed on dface {face_id}",
                )
                if matinfo.get("yugaGround"):
                    changed_ids.add(face_id)
            insist(
                total * 3 == glb.doc["accessors"][prim["indices"]]["count"],
                "Face run triangle counts do not fill primitive",
            )
            tri_count += total
    insist(
        model_ids == set(range(len(models))),
        "Not all native brush models have a scene identity",
    )
    insist(
        registered == eligible,
        f"Renderable face set differs from native layout by {len(registered ^ eligible)}",
    )
    if ground_ids is not None:
        insist(
            changed_ids == set(ground_ids),
            "Face-run ground assignments differ from native edit",
        )
    game = bsp.get(35)
    (n,) = struct.unpack_from("<I", game)
    entries = [struct.unpack_from("<4sHHii", game, 4 + 16 * i) for i in range(n)]
    record = next(v for v in entries if v[0] in (b"prps", b"sprp"))
    fmt, flags, version, off, length = record
    insist(flags == 0 and version == 11, "Expected Source v11 static props")
    (count,) = struct.unpack_from("<I", bsp.data, off)
    at = off + 4
    paths = [
        bytes(bsp.data[at + 128 * i : at + 128 * i + 128])
        .split(b"\0")[0]
        .decode("cp1252")
        .replace("\\", "/")
        .lower()
        for i in range(count)
    ]
    at += 128 * count
    (leaves,) = struct.unpack_from("<i", bsp.data, at)
    at += 4 + leaves * 2
    (count,) = struct.unpack_from("<i", bsp.data, at)
    at += 4
    insist(
        set(static_nodes) == set(range(count)),
        "Not every native static prop is placed once",
    )
    basis = np.array([[1, 0, 0], [0, 0, 1], [0, -1, 0]])
    max_origin, max_basis = 0.0, 0.0
    for i, (node, mat) in static_nodes.items():
        row = at + 80 * i
        x, y, z, pitch, yaw, roll = struct.unpack_from("<6f", bsp.data, row)
        (model_index,) = struct.unpack_from("<H", bsp.data, row + 24)
        (skin,) = struct.unpack_from("<i", bsp.data, row + 32)
        (scale,) = struct.unpack_from("<f", bsp.data, row + 76)
        props = node["extras"]
        insist(
            props["sourceMdl"].lower() == paths[model_index]
            and props["sourceSkin"] == skin,
            f"Prop {i} refers to a different model or skin",
        )
        expected_origin = basis @ np.array([x, y, z]) * 0.0254
        R = Rotation.from_euler("ZYX", (yaw, pitch, roll), degrees=True).as_matrix()
        max_origin = max(
            max_origin, float(np.linalg.norm(mat[:3, 3] - expected_origin))
        )
        max_basis = max(
            max_basis, float(np.max(np.abs(mat[:3, :3] - basis @ R @ basis.T * scale)))
        )
    insist(
        max_origin < 0.001 and max_basis < 0.0001,
        "A native static transform or scale changed",
    )
    insist(
        registered_overlays == set(native_overlays),
        "Rebuilt scene is missing an original map overlay",
    )
    return {
        "overlay_ids_matching_native_faces_order_and_material": len(
            registered_overlays
        ),
        "overlay_triangles": overlay_triangles,
        "source_brush_models_represented": len(model_ids),
        "native_renderable_dfaces": len(eligible),
        "dface_ids_verified_once": len(registered),
        "native_utility_or_invisible_faces": bsp.count(7, 56) - len(eligible),
        "world_and_brush_triangles_from_face_runs": tri_count,
        "ground_face_ids_verified": len(changed_ids),
        "static_props_matched_by_source_index_path_skin_and_transform": len(
            static_nodes
        ),
        "maximum_static_origin_error_m": round(max_origin, 9),
        "maximum_basis_element_error": round(max_basis, 9),
    }


def verify(before, after, bspfile, ids, epsilon):
    a = Glb(before)
    b = Glb(after)
    changes, binary_sha = compare_materials(a, b)
    stats, all_vertices, ground_vertices = ground_stats(a, changes)
    result = {
        "schema": "yuga.dust2.scene-verification.v1",
        "baseline_sha256": file_sha(before),
        "variant_sha256": file_sha(after),
        "identical_binary_sha256": binary_sha,
        "equal_except_ground_rgb": True,
        "changed_materials": changes,
        "geometry": stats,
    }
    if bspfile:
        with Bsp(bspfile) as bsp:
            result["source_ledger"] = crosscheck_source_ledger(bsp, a, ids)
            result["source_registration"] = registration(
                bsp, all_vertices, ground_vertices, ids, epsilon
            )
    return result


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("baseline", type=Path)
    p.add_argument("variant", type=Path)
    p.add_argument("--bsp", type=Path)
    p.add_argument("--face-ids", type=Path)
    p.add_argument("--tolerance-m", type=float, default=0.005)
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    ids = set(json.loads(args.face_ids.read_text())) if args.face_ids else None
    result = verify(args.baseline, args.variant, args.bsp, ids, args.tolerance_m)
    body = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.write_text(body)
    else:
        print(body, end="")
