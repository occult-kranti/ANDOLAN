"""Validate the exported courtyard without Blender or third-party packages."""
import hashlib
import json
import math
import struct
from pathlib import Path


def validate():
    directory = Path(__file__).resolve().parents[1] / "assets" / "environment"
    path = directory / "lanka_courtyard.glb"
    raw = path.read_bytes()
    magic, version, length = struct.unpack_from("<4sII", raw)
    assert (magic, version, length) == (b"glTF", 2, len(raw)), "Invalid GLB header"
    json_length, json_kind = struct.unpack_from("<II", raw, 12)
    assert json_kind == 0x4E4F534A
    doc = json.loads(raw[20:20+json_length])
    binary_offset = 20+json_length
    binary_length, binary_kind = struct.unpack_from("<II", raw, binary_offset)
    assert binary_kind == 0x004E4942
    binary = raw[binary_offset+8:binary_offset+8+binary_length]
    assert len(binary) == binary_length
    assert all("uri" not in image and "bufferView" in image for image in doc["images"])
    assert "animations" not in doc and "cameras" not in doc
    assert "KHR_lights_punctual" not in doc.get("extensionsUsed", [])

    sizes = {"SCALAR":1, "VEC2":2, "VEC3":3, "VEC4":4}
    formats = {5126:"f", 5125:"I", 5123:"H", 5121:"B"}
    def values(accessor_index):
        accessor = doc["accessors"][accessor_index]
        view = doc["bufferViews"][accessor["bufferView"]]
        fmt = "<"+formats[accessor["componentType"]]*sizes[accessor["type"]]
        size = struct.calcsize(fmt)
        stride = view.get("byteStride", size)
        offset = view.get("byteOffset", 0)+accessor.get("byteOffset", 0)
        assert offset+(accessor["count"]-1)*stride+size <= len(binary)
        return [struct.unpack_from(fmt, binary, offset+i*stride) for i in range(accessor["count"])]

    triangles = 0
    vertices = 0
    primitive_count = 0
    for mesh in doc["meshes"]:
        for primitive in mesh["primitives"]:
            assert primitive.get("mode",4) == 4, "Expected explicit triangles"
            attrs = primitive["attributes"]
            assert {"POSITION","NORMAL","TEXCOORD_0","TANGENT"}.issubset(attrs)
            positions = values(attrs["POSITION"])
            count = len(positions)
            for name in ["POSITION","NORMAL","TEXCOORD_0","TANGENT"]:
                rows = values(attrs[name])
                assert len(rows) == count
                assert all(math.isfinite(v) for row in rows for v in row), name+" contains nonfinite values"
                if name == "NORMAL":
                    assert all(.98 <= sum(v*v for v in row) <= 1.02 for row in rows), "Invalid normal length"
                if name == "TANGENT":
                    assert all(.98 <= sum(v*v for v in row[:3]) <= 1.02 and abs(abs(row[3])-1)<.001 for row in rows), "Invalid tangent"
            indices = [row[0] for row in values(primitive["indices"])]
            assert len(indices)%3 == 0 and all(0 <= index < count for index in indices)
            triangles += len(indices)//3
            vertices += count
            primitive_count += 1
    assert triangles < 300_000 and len(raw) < 25*1024*1024
    metadata = json.loads((directory / "lanka_courtyard.metadata.json").read_text())
    digest = hashlib.sha256(raw).hexdigest()
    assert digest == metadata["glb_sha256"]
    assert triangles == metadata["triangles"]
    assert vertices == metadata["exported_vertices"]
    assert len(doc["images"]) == metadata["embedded_textures"]
    collision_nodes = [node for node in doc["nodes"] if node.get("name", "").startswith("COL_")]
    assert collision_nodes and all("mesh" in node for node in collision_nodes)
    report = {"status":"pass", "glb_sha256":digest, "bytes":len(raw),
        "triangles":triangles, "exported_vertices":vertices, "mesh_primitives":primitive_count,
        "embedded_images":len(doc["images"]), "collision_meshes":len(collision_nodes),
        "checks":["GLB header/chunks", "all images embedded", "triangle index ranges",
            "finite positions/UVs", "unit normals/tangents", "metadata counts and SHA-256",
            "no cameras/animations/punctual lights", "size and triangle budgets"]}
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    validate()
