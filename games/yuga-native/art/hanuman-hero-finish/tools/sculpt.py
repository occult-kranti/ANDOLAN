"""Sculpt the existing weighted Hanuman in Blender, then graft the groom onto its original GLB.

blender -b -t 2 --python-exit-code 1 -P tools/sculpt.py -- --output /tmp/hanuman-sculpt.glb
Optional --blend FILE stores the editable groom patch, with named regions and weight groups.
Build the release with the sibling finish.py after the independent surface and motion passes.
"""

import argparse
import hashlib
import io
import json
import math
import os
import random
import struct
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from PIL import Image

PACK = Path(__file__).resolve().parents[1]
REPO = PACK.parents[3]
sys.path.insert(0, str(PACK.parent / "hero-rama-lod"))
from glb_lod import GLB

CFG = json.loads((PACK / "design/groom.json").read_text())
PI = math.pi
TAU = math.tau
UP, DEPTH = Vector((0, 1, 0)), Vector((0, 0, 1))
rng = random.Random(CFG["seed"])


def smooth(a, b, x):
    t = min(1.0, max(0.0, (x - a) / (b - a)))
    return t * t * (3.0 - 2.0 * t)


def unit(v):
    if v.length < 1e-8:
        raise ValueError("Degenerate hair frame")
    return v.normalized()


def lin(v):
    return ((v + 0.055) / 1.055) ** 2.4 if v > 0.04045 else v / 12.92


class Writer:
    def __init__(self, glb):
        self.doc = glb.doc
        self.raw = bytearray(glb.binary[: self.doc["buffers"][0]["byteLength"]])

    def view(self, data, target=None):
        self.raw.extend(b"\0" * ((-len(self.raw)) % 4))
        item = {"buffer": 0, "byteOffset": len(self.raw), "byteLength": len(data)}
        if target:
            item["target"] = target
        self.raw.extend(data)
        self.doc["bufferViews"].append(item)
        return len(self.doc["bufferViews"]) - 1

    def attribute(self, values, component, kind, target=34962, normalize=False, bounds=False):
        types = {5126: "<f4", 5123: "<u2", 5125: "<u4", 5121: "u1"}
        a = np.asarray(values, dtype=types[component])
        record = {
            "bufferView": self.view(a.tobytes(), target),
            "componentType": component,
            "count": len(a),
            "type": kind,
        }
        if normalize:
            record["normalized"] = True
        if bounds:
            record.update(min=a.min(axis=0).tolist(), max=a.max(axis=0).tolist())
        self.doc["accessors"].append(record)
        return len(self.doc["accessors"]) - 1

    def write(self, path):
        self.doc["buffers"][0]["byteLength"] = len(self.raw)
        self.raw.extend(b"\0" * (-len(self.raw) % 4))
        j = json.dumps(self.doc, ensure_ascii=False, separators=(",", ":")).encode()
        j += b" " * (-len(j) % 4)
        data = (
            struct.pack("<4sIIII", b"glTF", 2, 28 + len(j) + len(self.raw), len(j), 0x4E4F534A) + j
        )
        data += struct.pack("<II", len(self.raw), 0x004E4942) + self.raw
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.with_suffix(".tmp")
        temp.write_bytes(data)
        os.replace(temp, path)


def surface(glb, primitives):
    points, faces = [], []
    for primitive in primitives:
        pos = glb.array(primitive["attributes"]["POSITION"])
        indices = glb.array(primitive["indices"]).reshape(-1, 3)
        faces.extend((indices + len(points)).tolist())
        points.extend(pos.tolist())
    return BVHTree.FromPolygons(points, faces, all_triangles=True)


def hit(tree, center, outward):
    r = unit(outward)
    p, _, index, _ = tree.ray_cast(center + r * 0.53, -r, 0.72)
    if index is None:
        raise ValueError(f"No fitted root at {list(center)} along {list(r)}")
    return p


def compact_muzzle(glb, warp):
    # Existing lips, nostrils and skin must coincidentally follow one continuous deformation.
    # The spatial window excludes the eyes, ears, sword, costume and tilak.
    cfg = CFG["muzzle"]

    def transform(p):
        x, y, z = p.T

        def gate(a, b, v):
            t = np.clip((v - a) / (b - a), 0, 1)
            return t * t * (3 - 2 * t)

        zone = gate(1.705, 1.765, y) * (1 - gate(1.843, 1.88, y)) * (1 - gate(0.078, 0.118, abs(x)))
        deep = gate(cfg["depth_start"], cfg["depth_full"], z) * zone
        return np.column_stack(
            [
                x * (1 + cfg["lateral_expand"] * deep),
                y + 0.005 * deep * (1 - gate(1.792, 1.84, y)),
                z - cfg["retract"] * deep,
            ]
        )

    report = {}
    for _, _, prim in glb.primitives():
        name = glb.doc["materials"][prim["material"]]["name"]
        if not name.startswith(("Vanara ·", "Eyelids ·", "Face · warm recessed")):
            continue
        a = prim["attributes"]
        pos = glb.array(a["POSITION"]).astype(float)
        p = transform(pos)
        difference = np.linalg.norm(p - pos, axis=1)
        if difference.max() < 1e-6:
            continue
        eps = 1e-5
        J = np.stack(
            [(transform(pos + d * eps) - transform(pos - d * eps)) / (2 * eps) for d in np.eye(3)],
            axis=2,
        )
        if np.linalg.det(J).min() < 0.15:
            raise ValueError("Muzzle warp folds the donor surface")
        n = glb.array(a["NORMAL"]).astype(float)
        normal = np.linalg.solve(J.transpose(0, 2, 1), n[:, :, None])[:, :, 0]
        normal /= np.linalg.norm(normal, axis=1, keepdims=True).clip(1e-8)
        a["POSITION"] = warp.attribute(p, 5126, "VEC3", bounds=True)
        normal[difference < 1e-10] = n[difference < 1e-10]
        a["NORMAL"] = warp.attribute(normal, 5126, "VEC3")
        if "TANGENT" in a:
            tangents = glb.array(a["TANGENT"]).astype(float)
            tangent = (J @ tangents[:, :3, None])[:, :, 0]
            tangent /= np.linalg.norm(tangent, axis=1, keepdims=True).clip(1e-8)
            tangent[difference < 1e-10] = tangents[difference < 1e-10, :3]
            a["TANGENT"] = warp.attribute(np.column_stack([tangent, tangents[:, 3]]), 5126, "VEC4")
        report[name] = {
            "moved_vertices": int((difference > 1e-6).sum()),
            "max_m": round(float(difference.max()), 6),
        }
    return report


class Groom:
    def __init__(self, name, skin):
        self.name = name
        self.skin = skin
        self.points = []
        self.faces = []
        self.colors = []
        self.uv = []
        self.joints = []
        self.weights = []
        self.locks = 0

    def lock(self, path, width, depth, palette, weights):
        # path returns a flowing guide and outward surface frame. Each cross-section has
        # a shallow dorsal ridge and an asymmetrically tapering elliptical cross-section.
        first = len(self.points)
        rings = CFG["sections"]
        sides = CFG["cross_sections"]
        guide = [path(t) for t in rings]
        phase = rng.uniform(0, TAU)
        light = rng.uniform(0.89, 1.12)
        low_root = 0.51 if self.name in ("Whiskered cheek fans", "Layered nape mantle") else 0.6
        for i, (t, (pt, n)) in enumerate(zip(rings, guide)):
            tangent = unit(guide[min(i + 1, len(rings) - 1)][0] - guide[max(0, i - 1)][0])
            n = unit(n - tangent * n.dot(tangent))
            side = unit(n.cross(tangent))
            shape = (0.5 + 0.55 * smooth(0, 0.27, t)) * (max(0.00024, 1 - t) ** 0.68)
            w = width * shape
            h = depth * shape
            blend = weights(t)
            blend = [(k, float(np.float32(v))) for k, v in blend if np.float32(v) > 0]
            joints = [self.skin.index(k) for k, v in blend]
            vals = [v for k, v in blend]
            if abs(sum(vals) - 1) > 1e-5:
                raise ValueError("Hair weights do not sum to one")
            for j in range(sides + 1):
                angle = TAU * j / sides
                ca, sa = math.cos(angle), math.sin(angle)
                radial = h * sa * (1 + 0.14 * math.cos(3 * angle + phase + t))
                self.points.append(tuple(pt + side * w * ca + n * radial))
                self.uv.append((j / sides, t))
                ridge = 0.04 * max(0, sa) + 0.028 * math.cos(2 * angle + phase)
                factor = (
                    (low_root + (0.955 - low_root) * smooth(0, 0.52, t) + ridge)
                    * (1 - 0.16 * smooth(0.74, 1, t))
                    * light
                )
                self.colors.append([round(255 * lin(min(1, r * factor))) for r in palette] + [255])
                self.joints.append((joints + [0] * 4)[:4])
                self.weights.append((vals + [0.0] * 4)[:4])
        for i in range(len(rings) - 1):
            for j in range(sides):
                a = first + i * (sides + 1) + j
                b = a + sides + 1
                self.faces.extend([(a, a + 1, b + 1), (a, b + 1, b)])
        self.locks += 1

    def editable(self):
        # Face normals are evaluated by Blender on a real editable mesh in Blender axes.
        mesh = bpy.data.meshes.new(self.name)
        mesh.from_pydata([(x, -z, y) for x, y, z in self.points], [], self.faces)
        mesh.update()
        mesh.polygons.foreach_set("use_smooth", [True] * len(mesh.polygons))
        mesh.materials.append(bpy.data.materials["Hanuman | swept copper guard hair"])
        obj = bpy.data.objects.new(self.name, mesh)
        bpy.context.collection.objects.link(obj)
        colors = mesh.color_attributes.new(
            name="Copper variation", type="FLOAT_COLOR", domain="POINT"
        )
        colors.data.foreach_set("color", (np.asarray(self.colors, dtype=float) / 255).ravel())
        uv = mesh.uv_layers.new(name="Fiber direction")
        vi = np.asarray([l.vertex_index for l in mesh.loops])
        uv.data.foreach_set("uv", np.asarray(self.uv, dtype=float)[vi].ravel())
        for bone in set(
            self.skin[j]
            for js, ws in zip(self.joints, self.weights)
            for j, w in zip(js, ws)
            if w > 0.00001
        ):
            group = obj.vertex_groups.new(name=bone)
            j = self.skin.index(bone)
            batches = {}
            for i, (indices, weights) in enumerate(zip(self.joints, self.weights)):
                total = sum(w for idx, w in zip(indices, weights) if idx == j)
                if total > 1e-5:
                    batches.setdefault(round(total, 7), []).append(i)
            for weight, ids in batches.items():
                group.add(ids, weight, "REPLACE")
        norms = np.empty(len(mesh.vertices) * 3, dtype="f4")
        mesh.vertices.foreach_get("normal", norms)
        norms = norms.reshape(-1, 3)[:, [0, 2, 1]].copy()
        norms[:, 2] *= -1
        stride = CFG["cross_sections"] + 1
        seam = norms[::stride] + norms[stride - 1 :: stride]
        seam /= np.linalg.norm(seam, axis=1)[:, None].clip(1e-9)
        norms[::stride] = norms[stride - 1 :: stride] = seam
        if np.linalg.norm(norms, axis=1).min() < 0.9:
            raise ValueError("Invalid groom normals")
        return {
            "POSITION": self.points,
            "NORMAL": norms,
            "COLOR_0": self.colors,
            "TEXCOORD_0": self.uv,
            "JOINTS_0": self.joints,
            "WEIGHTS_0": self.weights,
        }


def append_groom(writer, regions, mat):
    # One material, one GPU draw. Keep named edit objects, and preserve their
    # contiguous vertex/index ranges in primitive extras for independent QA.
    streams = {}
    index_stream = []
    stats = []
    offset = 0
    for region in regions:
        for attribute, values in region.editable().items():
            streams.setdefault(attribute, []).append(np.asarray(values))
        indices = np.asarray(region.faces).ravel() + offset
        stats.append(
            dict(
                name=region.name,
                clumps=region.locks,
                firstVertex=offset,
                vertices=len(region.points),
                firstIndex=sum(len(a) for a in index_stream),
                triangles=len(region.faces),
            )
        )
        index_stream.append(indices)
        offset += len(region.points)
    layouts = {
        "POSITION": (5126, "VEC3"),
        "NORMAL": (5126, "VEC3"),
        "COLOR_0": (5121, "VEC4"),
        "TEXCOORD_0": (5126, "VEC2"),
        "JOINTS_0": (5121, "VEC4"),
        "WEIGHTS_0": (5126, "VEC4"),
    }
    attrs = {
        name: writer.attribute(
            np.concatenate(groups),
            *layouts[name],
            normalize=name == "COLOR_0",
            bounds=name == "POSITION",
        )
        for name, groups in streams.items()
    }
    primitive = {
        "attributes": attrs,
        "material": mat,
        "mode": 4,
        "indices": writer.attribute(
            np.concatenate(index_stream), 5123 if offset <= 65535 else 5125, "SCALAR", 34963
        ),
        "extras": {"studioRegions": stats},
    }
    writer.doc["meshes"][0]["primitives"].append(primitive)
    return stats


def pigment(writer):
    # Very fine longitudinal modulation sits below the modeled strand widths.
    # No alpha cards: every visible silhouette is a lit, two-sided volume in depth.
    h, w = 256, 128
    y, x = np.mgrid[0:h, 0:w] / np.array([[[h]], [[w]]])
    v = (
        0.90
        + 0.035 * np.cos(TAU * (11 * x + 0.22 * np.sin(TAU * y)))
        + 0.023 * np.sin(TAU * (29 * x - 0.17 * np.sin(TAU * y)))
    )
    v += 0.012 * np.cos(TAU * (57 * x + 0.5 * y))
    img = Image.fromarray(np.uint8(np.clip(v, 0, 1) * 255)).convert("RGB")
    blob = io.BytesIO()
    img.save(blob, format="PNG", optimize=True)
    # The same fiber map and artist-adjustable pigment are visible on the .blend patch.
    preview = bpy.data.materials.new("Hanuman | swept copper guard hair")
    preview.diffuse_color = (0.22, 0.068, 0.028, 1)
    preview.use_nodes = True
    nodes = preview.node_tree.nodes
    shader = nodes.get("Principled BSDF")
    shader.inputs["Roughness"].default_value = 0.59
    vertex = nodes.new("ShaderNodeVertexColor")
    vertex.layer_name = "Copper variation"
    fibers = nodes.new("ShaderNodeTexImage")
    fibers.image = bpy.data.images.new("Longitudinal cuticle grain.png", width=w, height=h)
    fibers.image.pack(data=blob.getvalue(), data_len=len(blob.getvalue()))
    mul = nodes.new("ShaderNodeMixRGB")
    mul.blend_type = "MULTIPLY"
    mul.inputs[0].default_value = 1
    links = preview.node_tree.links
    links.new(vertex.outputs["Color"], mul.inputs[1])
    links.new(fibers.outputs["Color"], mul.inputs[2])
    links.new(mul.outputs["Color"], shader.inputs["Base Color"])
    doc = writer.doc
    doc["images"].append(
        {
            "name": "Longitudinal cuticle grain",
            "bufferView": writer.view(blob.getvalue()),
            "mimeType": "image/png",
        }
    )
    doc["textures"].append({"source": len(doc["images"]) - 1})
    doc["materials"].append(
        {
            "name": "Hanuman | swept copper guard hair",
            "pbrMetallicRoughness": {
                "metallicFactor": 0.0,
                "roughnessFactor": 0.59,
                "baseColorTexture": {"index": len(doc["textures"]) - 1},
            },
            "doubleSided": False,
        }
    )
    return len(doc["materials"]) - 1


def head(_):
    return [("head", 1.0)]


def mane(tree, scalp, regions):
    center = Vector(CFG["scalp_center"])
    axes = Vector(CFG["scalp_axes"])
    for row in CFG["crest_rows"]:
        for i in range(row["count"]):
            lane = (2 * (i + 0.45 + rng.uniform(-0.25, 0.25)) / row["count"] - 1) * 0.91
            a = math.radians(
                row["start"]
                + 11 * abs(lane)
                + 11 * math.exp(-(((lane + 0.13) / 0.24) ** 2))
                + rng.uniform(-6, 5)
            )
            b = math.radians(row["end"] + 15 * abs(lane) + rng.uniform(-9, 8))
            swirl = rng.uniform(-0.05, 0.05)
            fan = math.tanh(5 * (lane + 0.13))

            def crown(t):
                theta = a + (b - a) * t
                lat = np.clip(
                    lane + 0.137 * fan * math.sin(PI * t) + 0.035 * math.sin(PI * t) + swirl * t,
                    -0.96,
                    0.96,
                )
                k = math.sqrt(1 - lat * lat)
                v = Vector((lat, k * math.sin(theta), k * math.cos(theta)))
                anchor = hit(scalp, center, Vector([v[i] * axes[i] for i in range(3)]))
                lift = (
                    row["lift"]
                    * (math.sin(0.89 * PI * t) ** 0.83)
                    * (0.78 + 0.35 * (1 - abs(lane)))
                )
                return anchor + v * (lift - 0.0015) + Vector((0, 0.004 * t, -0.015 * t * t)), v

            pastel = rng.uniform(-0.045, 0.05)
            regions["crest"].lock(
                crown,
                row["width"] * rng.uniform(0.8, 1.12),
                0.0052,
                (0.65 + pastel, 0.324 + pastel * 0.6, 0.165 + pastel * 0.5),
                head,
            )
    for ir, row in enumerate(CFG["nape_rows"]):
        for i in range(row["count"]):
            a = (2 * (i + 0.4 + rng.uniform(-0.18, 0.18)) / row["count"] - 1) * 1.32
            out = unit(Vector((math.sin(a), 0, -math.cos(a))))
            y = row["root_y"] + rng.uniform(-0.011, 0.013)
            try:
                anchor = hit(scalp, Vector((0, y, 0.025)), out)
            except ValueError:
                # Below the original cap the lowest mantle starts on the donor neck.
                anchor = hit(tree, Vector((0, y, 0.025)), out)
            drop = row["drop"] * (1 - 0.32 * abs(math.sin(a))) * rng.uniform(0.89, 1.1)
            flare = rng.uniform(0.009, 0.023)
            sweep = rng.uniform(-0.012, 0.012)

            def nape(t):
                bell = math.sin(PI * t)
                p = anchor + out * (-0.002 + (0.022 + ir * 0.004) * bell + flare * t * t)
                p += Vector(
                    (sweep * t + 0.007 * math.sin(2 * PI * t + a) * t, -drop * t, -0.023 * bell)
                )
                return p, out

            def neck(t):
                amount = (0.32 + 0.34 * math.cos(a) ** 2) * smooth(0.35, 0.98, t)
                return [("head", 1 - amount), ("neck03", amount * 0.65), ("neck02", amount * 0.35)]

            shade = rng.uniform(-0.04, 0.06)
            regions["nape"].lock(
                nape,
                row["width"] * rng.uniform(0.8, 1.18),
                0.006,
                (0.53 + shade, 0.246 + shade * 0.65, 0.135 + shade * 0.4),
                neck,
            )
    for s in (-1, 1):
        n = CFG["cheek_count_each"]
        for i in range(n):
            f = (i + rng.uniform(0.1, 0.9)) / n
            y = 1.856 + 0.055 * f + 0.007 * math.sin(i * 2.3)
            z = 0.076 + 0.081 * f
            out = unit(Vector((s, 0.02, 0.22 + 0.22 * f)))
            start = hit(tree, Vector((0, y, z)), out)
            reach = 0.050 + 0.017 * (1 - f) + rng.uniform(-0.008, 0.006)

            def cheek(t):
                p = start + Vector(
                    (
                        s * (0.012 * math.sin(PI * t) + 0.004 * t),
                        -reach * t,
                        0.019 * t + 0.007 * math.sin(PI * t),
                    )
                )
                return p + out * (-0.0015 + 0.0018 * t), out

            shade = rng.uniform(-0.040, 0.045)
            regions["cheeks"].lock(
                cheek,
                rng.uniform(0.0062, 0.010),
                0.004,
                (0.515 + shade, 0.211 + shade * 0.7, 0.112 + shade * 0.5),
                head,
            )
        for i in range(CFG["brow_count_each"]):
            f = (i + 0.5) / CFG["brow_count_each"]
            x = 0.019 + 0.068 * f
            y = 1.911 + 0.009 * math.sin(PI * f)

            def brow(t):
                xx = x + 0.011 * t
                yy = y + 0.0028 * math.sin(PI * t) - 0.0030 * t
                p = hit(tree, Vector((s * xx, yy, 0)), DEPTH)
                return p + DEPTH * (0.0028 + 0.0014 * math.sin(PI * t)), DEPTH

            regions["brows"].lock(brow, 0.0026, 0.0022, (0.33, 0.147, 0.082), head)


def brush(region):
    ctrl = [Vector(x) for x in CFG["tail_controls"]]

    def center(f):
        # Same Catmull-Rom rest guide as the shipped Blender donor.
        if f > 1.0:
            v = unit(ctrl[-1] - ctrl[-2])
            return (
                ctrl[-1]
                + v * ((f - 1) * 1.55)
                + Vector((-0.105, 0.44, 0.09)) * (max(0.0, f - 1) ** 1.35)
            )
        q = max(0, f) * (len(ctrl) - 1)
        j = min(int(q), len(ctrl) - 2)
        t = q - j
        a, b = ctrl[j : j + 2]
        m = (b - ctrl[max(0, j - 1)]) * 0.5
        n = (ctrl[min(len(ctrl) - 1, j + 2)] - a) * 0.5
        return (
            a * (2 * t**3 - 3 * t * t + 1)
            + b * (-2 * t**3 + 3 * t * t)
            + m * (t**3 - 2 * t * t + t)
            + n * (t**3 - t * t)
        )

    for ix, row in enumerate(CFG["tail_rows"]):
        for j in range(row["count"]):
            phi = TAU * (j + rng.uniform(-0.25, 0.25)) / row["count"]
            base = row["root"] + rng.uniform(-0.018, 0.014)
            end = row["end"] + rng.uniform(-0.018, 0.019)
            twist = rng.uniform(0.14, 0.51)
            full = row["fullness"] * rng.uniform(0.86, 1.16)

            def tail(t):
                f = base + (end - base) * t
                tan = unit(center(f + 0.0006) - center(f - 0.0006))
                d = unit(DEPTH - tan * tan.dot(DEPTH))
                side = unit(tan.cross(d))
                a = phi + twist * t
                normal = unit(d * math.cos(a) + side * math.sin(a))
                core = 0.041 * (0.25 + 0.75 * max(0, 1 - min(1.0, f)) ** 0.93)
                rad = (core - 0.002) * (1 - smooth(0.74, 1, t)) + full * math.sin(
                    0.94 * PI * t
                ) ** 0.72
                return center(f) + normal * rad, normal

            def weight(t):
                f = base + (end - base) * t
                w = smooth(60 / 84, 76 / 84, f)
                return [("tail_03", 1 - w), ("tail_04", w)]

            tone = rng.uniform(-0.045, 0.048)
            region.lock(
                tail,
                row["width"] * rng.uniform(0.83, 1.16),
                0.0055,
                (
                    0.49 + tone - 0.028 * ix,
                    0.233 + tone * 0.6 - 0.014 * ix,
                    0.15 + tone * 0.5 - 0.007 * ix,
                ),
                weight,
            )


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--input", type=Path, default=REPO / CFG["source"])
    ap.add_argument("--output", required=True, type=Path)
    ap.add_argument("--receipt", type=Path)
    ap.add_argument("--blend", type=Path)
    args = ap.parse_args(sys.argv[sys.argv.index("--") + 1 :])
    source = GLB(args.input)
    if hashlib.sha256(source.raw).hexdigest() != CFG["source_sha256"]:
        raise ValueError(
            "Groom landmarks are fitted to the pinned export. Refit against the new source."
        )
    primitives = source.doc["meshes"][0]["primitives"]
    skin = [source.doc["nodes"][i]["name"] for i in source.doc["skins"][0]["joints"]]
    centers = surface(source, [primitives[0]])
    scalp = surface(source, [primitives[7], primitives[8]])
    writer = Writer(source)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    names = {
        "crest": "Crown swept guard locks",
        "nape": "Layered nape mantle",
        "cheeks": "Whiskered cheek fans",
        "brows": "Short angular brows",
        "brush": "Terminal tail brush",
    }
    regions = {key: Groom(label, skin) for key, label in names.items()}
    mane(centers, scalp, regions)
    brush(regions["brush"])
    moved = compact_muzzle(source, writer)
    mat = pigment(writer)
    stats = append_groom(writer, regions.values(), mat)
    writer.write(args.output)
    if args.blend:
        # Package the editable, named groom regions. The final GLB remains the rig/animation interchange.
        args.blend.parent.mkdir(parents=True, exist_ok=True)
        bpy.context.preferences.filepaths.save_version = 0
        bpy.ops.wm.save_as_mainfile(filepath=str(args.blend.resolve()), compress=True)
    receipt = {
        "source": CFG["source"],
        "source_sha256": CFG["source_sha256"],
        "reference": CFG["reference"],
        "sculpt_sha256": hashlib.sha256(args.output.read_bytes()).hexdigest(),
        "seed": CFG["seed"],
        "blender": bpy.app.version_string,
        "groom": stats,
        "muzzle_warp": moved,
        "skin_joints": len(skin),
        "unchanged_clip_names": [a["name"] for a in source.doc["animations"]],
    }
    if args.receipt:
        args.receipt.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(receipt, ensure_ascii=False))


if __name__ == "__main__":
    main()
