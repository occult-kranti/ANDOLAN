#!/usr/bin/env python3
"""Inspect a self-contained Blender GLB independently of the exporter and Godot.

This covers payload integrity and inventory. It does not inspect pose quality,
rig retargeting, deformation, materials under actual lighting, or geometry LOD.
"""

import argparse
import hashlib
import json
import math
import struct
from collections import Counter
from pathlib import Path


COMPONENTS = {5120: "b", 5121: "B", 5122: "h", 5123: "H", 5125: "I", 5126: "f"}
WIDTHS = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def item(values, index):
    require(type(index) is int and 0 <= index < len(values), f"invalid index {index!r}")
    return values[index]


class Payload:
    def __init__(self, raw):
        require(28 <= len(raw) <= 96 * 1024**2, "unexpected GLB byte length")
        require(struct.unpack_from("<III", raw) == (0x46546C67, 2, len(raw)), "GLB v2 header mismatch")
        length, kind = struct.unpack_from("<II", raw, 12)
        require(kind == 0x4E4F534A and length % 4 == 0 and length <= len(raw) - 28, "bad JSON chunk")
        self.document = json.loads(raw[20 : 20 + length])
        binary_length, binary_kind = struct.unpack_from("<II", raw, 20 + length)
        self.binary = memoryview(raw)[28 + length :]
        require(binary_kind == 0x004E4942 and binary_length == len(self.binary), "bad BIN chunk")
        buffers = self.document["buffers"]
        require(len(buffers) == 1 and "uri" not in buffers[0], "expected a single embedded buffer")
        self.length = buffers[0]["byteLength"]
        require(0 <= len(self.binary) - self.length < 4, "buffer length mismatch")

    def view(self, index):
        view = item(self.document["bufferViews"], index)
        offset, length = view.get("byteOffset", 0), view["byteLength"]
        require(view["buffer"] == 0 and length > 0 and 0 <= offset <= self.length - length, "bad bufferView")
        return view, self.binary[offset : offset + length]

    def accessor(self, index):
        accessor = item(self.document["accessors"], index)
        require("sparse" not in accessor, "sparse accessor outside audit scope")
        view, data = self.view(accessor["bufferView"])
        code, width = accessor["componentType"], WIDTHS[accessor["type"]]
        layout = struct.Struct("<" + COMPONENTS[code] * width)
        offset, count = accessor.get("byteOffset", 0), accessor["count"]
        stride = view.get("byteStride", layout.size)
        require(count > 0 and offset >= 0 and stride >= layout.size, "bad accessor extent")
        require(offset + (count - 1) * stride + layout.size <= len(data), "accessor exceeds bufferView")
        rows = [layout.unpack_from(data, offset + i * stride) for i in range(count)]
        if code == 5126:
            require(all(math.isfinite(v) for row in rows for v in row), "nonfinite float in accessor")
        if accessor.get("normalized", False):
            require(code in {5121, 5123}, "only unsigned normalized streams are supported")
            divisor = {5121: 255, 5123: 65535}[code]
            rows = [tuple(v / divisor for v in row) for row in rows]
        return rows


def skin_influences(joints, weights, count, names):
    require(len(joints) == len(weights) == count, "mismatched skin streams")
    distribution = Counter()
    for joint, weight in zip(joints, weights, strict=True):
        require(len(joint) == len(weight) == 4, "skin stream must hold four inputs")
        require(all(0 <= w <= 1 and math.isfinite(w) for w in weight), "invalid skin weight")
        require(abs(sum(weight) - 1) <= 0.005, "skin weight normalization")
        for index, amount in zip(joint, weight, strict=True):
            name = item(names, index)
            if amount > 1e-6:
                distribution[name] += 1
    return distribution


def scene_nodes(doc):
    nodes = doc["nodes"]
    roots = item(doc["scenes"], doc.get("scene", 0)).get("nodes", [])
    visited = set()
    pending = list(roots)
    while pending:
        index = pending.pop()
        node = item(nodes, index)
        require(index not in visited, "node has multiple parents or a cycle")
        visited.add(index)
        for key, size in (("matrix", 16), ("translation", 3), ("rotation", 4), ("scale", 3)):
            if key in node:
                row = node[key]
                require(len(row) == size and all(math.isfinite(v) for v in row), f"invalid node {key}")
        pending.extend(node.get("children", []))
    return roots, visited


def audit(raw):
    payload = Payload(raw)
    doc = payload.document
    nodes, skins = doc["nodes"], doc.get("skins", [])
    materials = doc.get("materials", [])
    roots, visible = scene_nodes(doc)
    images = []
    for image in doc.get("images", []):
        require("uri" not in image, "external image URI")
        _, embedded = payload.view(image["bufferView"])
        formats = {"image/png": b"\x89PNG\r\n\x1a\n", "image/jpeg": b"\xff\xd8\xff"}
        require(image["mimeType"] in formats, f"unknown image format {image['mimeType']}")
        signature = formats[image["mimeType"]]
        require(embedded[: len(signature)] == signature, "image MIME and payload disagree")
        images.append({"name": image.get("name", ""), "bytes": len(embedded), "sha256": hashlib.sha256(embedded).hexdigest()})

    joint_names = []
    for skin in skins:
        names = [item(nodes, index).get("name", str(index)) for index in skin["joints"]]
        require(len(names) == len(set(names)) > 0, "assert distinct named joints")
        if "inverseBindMatrices" in skin:
            binds = payload.accessor(skin["inverseBindMatrices"])
            require(len(binds) == len(names) and len(binds[0]) == 16, "inverse bind size mismatch")
        joint_names.append(names)

    results = []
    for node_index in sorted(visible):
        node = nodes[node_index]
        if "mesh" not in node:
            continue
        mesh = item(doc["meshes"], node["mesh"])
        entry = {"node": node.get("name", ""), "mesh": mesh.get("name", ""), "primitives": []}
        for primitive in mesh["primitives"]:
            require(primitive.get("mode", 4) == 4, "only triangle primitives supported")
            attrs = primitive["attributes"]
            points = payload.accessor(attrs["POSITION"])
            count = len(points)
            require(len(points[0]) == 3, "expected three-dimensional positions")
            faces = [row[0] for row in payload.accessor(primitive["indices"])] if "indices" in primitive else range(count)
            require(len(faces) > 0 and len(faces) % 3 == 0, "invalid triangle count")
            require(all(type(face) is int and 0 <= face < count for face in faces), "triangle index outside positions")
            record = {
                "vertices": count, "triangles": len(faces) // 3,
                "bounds_local": [[min(r[i] for r in points) for i in range(3)], [max(r[i] for r in points) for i in range(3)]],
                "material": item(materials, primitive["material"]).get("name", "") if "material" in primitive else None,
            }
            for semantic in ("NORMAL", "TANGENT", "TEXCOORD_0", "TEXCOORD_1", "COLOR_0"):
                if semantic in attrs:
                    require(len(payload.accessor(attrs[semantic])) == count, f"mismatched {semantic} length")
            if "skin" in node:
                record["influences"] = dict(skin_influences(
                    payload.accessor(attrs["JOINTS_0"]), payload.accessor(attrs["WEIGHTS_0"]),
                    count, item(joint_names, node["skin"]),
                ))
            entry["primitives"].append(record)
        results.append(entry)
    require(results, "no visible geometry payload")

    motions = []
    for animation in doc.get("animations", []):
        duration = 0.0
        targets = set()
        for channel in animation["channels"]:
            sampler = item(animation["samplers"], channel["sampler"])
            times = payload.accessor(sampler["input"])
            require(len(times[0]) == 1 and times[0][0] >= 0, "invalid animation time start")
            require(all(a[0] < b[0] for a, b in zip(times, times[1:])), "animation times must increase")
            duration = max(duration, times[-1][0])
            values = payload.accessor(sampler["output"])
            target = channel["target"]
            target_node = item(nodes, target["node"])
            targets.add(target_node.get("name", str(target["node"])))
            factor = 3 if sampler.get("interpolation") == "CUBICSPLINE" else 1
            if target["path"] != "weights":
                require(len(values) == len(times) * factor, "mismatched animation sample counts")
        motions.append({"name": animation.get("name", ""), "duration_s": duration, "targets": sorted(targets)})

    primitives = [primitive for entry in results for primitive in entry["primitives"]]
    return {
        "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(), "nodes": len(nodes),
        "active_scene_roots": roots, "active_scene_nodes": len(visible),
        "mesh_nodes": results, "triangles": sum(p["triangles"] for p in primitives),
        "skinned_primitives": sum("influences" in p for p in primitives),
        "scene_primitives": len(primitives), "joint_names": joint_names, "animations": motions,
        "images": images,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("asset", type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--requires-skin", action="store_true")
    args = parser.parse_args()
    if args.report.exists():
        parser.error("report destination already exists")
    result = {"asset": args.asset.name, "scope": "raw embedded GLB payload and inventory"}
    try:
        require(args.asset.stat().st_size <= 96 * 1024**2, "input exceeds audit maximum")
        result.update(audit(args.asset.read_bytes()))
        require(not args.requires_skin or result["skinned_primitives"] > 0, "no skinned geometry")
        result["passed"] = True
    except (ValueError, KeyError, TypeError, IndexError, OSError, struct.error) as error:
        result.update(passed=False, error=str(error))
    args.report.parent.mkdir(parents=True, exist_ok=True)
    with args.report.open("x") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({k: result[k] for k in ("passed", "asset", "triangles", "skinned_primitives", "error") if k in result}))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
