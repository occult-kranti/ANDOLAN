"""Lossless GLB plumbing and independent measurements for candidate hero LODs.

The simplifier may choose existing vertices only. This module copies every
selected attribute and morph delta byte-for-byte; it never invents skin weights,
changes skeleton rest/animation or resizes material images.
"""
from __future__ import annotations
import copy
import hashlib
import json
import math
from pathlib import Path
import struct
import numpy as np

DTYPES = {5120: np.dtype("i1"), 5121: np.dtype("u1"), 5122: np.dtype("<i2"),
          5123: np.dtype("<u2"), 5125: np.dtype("<u4"), 5126: np.dtype("<f4")}
WIDTHS = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

class GLB:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.raw = self.path.read_bytes()
        if len(self.raw) < 28 or struct.unpack_from("<4sII", self.raw) != (b"glTF", 2, len(self.raw)):
            raise ValueError("Not a complete GLB2")
        length, kind = struct.unpack_from("<II", self.raw, 12)
        if kind != 0x4E4F534A:
            raise ValueError("Missing GLB JSON chunk")
        self.doc = json.loads(self.raw[20:20 + length])
        offset = 20 + length
        blen, bkind = struct.unpack_from("<II", self.raw, offset)
        if bkind != 0x004E4942 or offset + 8 + blen != len(self.raw):
            raise ValueError("Missing/trailing GLB binary chunk")
        self.binary = self.raw[offset + 8:]
        if len(self.doc.get("buffers", [])) != 1 or "uri" in self.doc["buffers"][0]:
            raise ValueError("Only one embedded binary buffer is supported")
        if any(k in self.doc.get("extensionsUsed", []) for k in ("KHR_draco_mesh_compression", "EXT_meshopt_compression")):
            raise ValueError("Decode compressed source before candidate generation")

    def array(self, index: int, normalized: bool = False) -> np.ndarray:
        a = self.doc["accessors"][index]
        dtype, width = DTYPES[a["componentType"]], WIDTHS[a["type"]]
        if a["count"] < 0: raise ValueError("Negative accessor count")
        if "bufferView" in a:
            v = self.doc["bufferViews"][a["bufferView"]]
            offset = v.get("byteOffset", 0) + a.get("byteOffset", 0)
            stride = v.get("byteStride", dtype.itemsize * width)
            end = offset + (a["count"] - 1) * stride + dtype.itemsize * width if a["count"] else offset
            if stride < dtype.itemsize * width or offset < v.get("byteOffset",0) or end > v.get("byteOffset",0)+v["byteLength"] or end > len(self.binary):
                raise ValueError("Accessor exceeds buffer view")
            data = np.ndarray((a["count"], width), dtype=dtype, buffer=self.binary,
                              offset=offset, strides=(stride, dtype.itemsize)).copy()
        else:
            data = np.zeros((a["count"], width), dtype=dtype)
        if "sparse" in a:
            sparse = a["sparse"]
            count = sparse["count"]
            if count <= 0 or count > a["count"]: raise ValueError("Invalid sparse count")
            def sparse_array(spec: dict, count: int, element_dtype, element_width: int):
                view = self.doc["bufferViews"][spec["bufferView"]]
                if "byteStride" in view: raise ValueError("Sparse buffer view must be tightly packed")
                offset = view.get("byteOffset",0)+spec.get("byteOffset",0)
                size = count*element_dtype.itemsize*element_width
                if offset < view.get("byteOffset",0) or offset+size > view.get("byteOffset",0)+view["byteLength"] or offset+size > len(self.binary):
                    raise ValueError("Sparse data exceeds buffer view")
                return np.frombuffer(self.binary,dtype=element_dtype,count=count*element_width,offset=offset).reshape(count,element_width)
            component = sparse["indices"]["componentType"]
            if component not in (5121,5123,5125): raise ValueError("Invalid sparse index component")
            indices = sparse_array(sparse["indices"],count,DTYPES[component],1).reshape(-1)
            if int(indices[-1]) >= a["count"] or not bool(np.all(indices[1:] > indices[:-1])): raise ValueError("Sparse indices must be strictly increasing and bounded")
            data[indices] = sparse_array(sparse["values"],count,dtype,width)
        if normalized and a.get("normalized"):
            data = data.astype(np.float64) / np.iinfo(dtype).max
            if dtype.kind == "i":
                data = np.maximum(data, -1)
        return data

    def image(self, image: dict) -> bytes:
        view = self.doc["bufferViews"][image["bufferView"]]
        start = view.get("byteOffset", 0)
        return self.binary[start:start + view["byteLength"]]

    def primitives(self):
        for mi, mesh in enumerate(self.doc.get("meshes", [])):
            for pi, primitive in enumerate(mesh["primitives"]):
                yield mi, pi, primitive

    def measure(self) -> dict:
        primitive_data, verts, tris, vertex_bytes, index_bytes = [], 0, 0, 0, 0
        for mi, pi, p in self.primitives():
            a = p["attributes"]
            v = len(self.array(a["POSITION"]))
            indices = self.array(p["indices"])
            t = len(indices) // 3
            vb = sum(self.array(i).nbytes for i in a.values())
            vb += sum(self.array(i).nbytes for target in p.get("targets", []) for i in target.values())
            primitive_data.append({"mesh": mi, "primitive": pi, "material": self.doc["materials"][p["material"]].get("name"),
                                   "vertices": v, "triangles": t, "vertexBytes": vb, "indexBytes": indices.nbytes})
            verts += v; tris += t; vertex_bytes += vb; index_bytes += indices.nbytes
        textures = []
        for image in self.doc.get("images", []):
            data = self.image(image)
            if not data.startswith(b"\x89PNG\r\n\x1a\n"):
                raise ValueError("Only explicit PNG dimensions are measured; unsupported image")
            width, height = struct.unpack_from(">II", data, 16)
            mip_pixels, w, h = 0, width, height
            while True:
                mip_pixels += w * h
                if w == h == 1: break
                w, h = max(1, w // 2), max(1, h // 2)
            textures.append({"name": image.get("name"), "sha256": digest(data), "encodedBytes": len(data),
                             "width": width, "height": height, "rgba8FullMipBytes": mip_pixels * 4})
        unique = {t["sha256"]: t["rgba8FullMipBytes"] for t in textures}
        return {"sha256": digest(self.raw), "fileBytes": len(self.raw), "vertices": verts, "triangles": tris,
                "vertexBytes": vertex_bytes, "indexBytes": index_bytes,
                "materialSlots": len(self.doc.get("materials", [])), "primitiveDrawsPerViewPass": len(primitive_data),
                "skinJointCounts": [len(s["joints"]) for s in self.doc.get("skins", [])],
                "textures": textures, "uniqueRgba8FullMipBytes": sum(unique.values()),
                "primitives": primitive_data,
                "limits": ["RGBA8+mips is an explicit uncompressed estimate, not measured engine VRAM.",
                           "Primitive count assumes no batching and excludes shadows/additional passes.",
                           "Compact vertex bytes exclude driver alignment/import changes and live skeleton/animation state.",
                           "No physical-GPU timing or commercial quality acceptance is implied."]}

def write_compacted(source: GLB, selected: dict, output: Path, extras: dict) -> None:
    """Replace triangles and compact every channel; retained source data is exact."""
    doc = copy.deepcopy(source.doc)
    arrays = {i: source.array(i) for i in range(len(doc["accessors"]))}
    for mi, pi, old in source.primitives():
        indices = np.asarray(selected[(mi, pi)], dtype=np.uint32).reshape(-1)
        if len(indices) % 3 or not len(indices): raise ValueError("Candidate must contain complete nonempty triangles")
        vertex_count = len(source.array(old["attributes"]["POSITION"]))
        if int(indices.max()) >= vertex_count: raise ValueError("Candidate references an unknown source vertex")
        used, remapped = np.unique(indices, return_inverse=True)
        p = doc["meshes"][mi]["primitives"][pi]
        def add(original: int, value: np.ndarray) -> int:
            spec = copy.deepcopy(doc["accessors"][original])
            spec.pop("min", None); spec.pop("max", None); spec.pop("byteOffset", None); spec.pop("sparse", None)
            spec["count"] = len(value)
            if spec["componentType"] == 5126 and spec["type"] != "MAT4":
                spec["min"] = value.min(axis=0).astype(float).tolist()
                spec["max"] = value.max(axis=0).astype(float).tolist()
            index = len(doc["accessors"]); doc["accessors"].append(spec); arrays[index] = value.copy()
            return index
        for semantic, ai in old["attributes"].items(): p["attributes"][semantic] = add(ai, arrays[ai][used])
        for ti, target in enumerate(old.get("targets", [])):
            for semantic, ai in target.items(): p["targets"][ti][semantic] = add(ai, arrays[ai][used])
        # Force uint32 indices so the accessor component type always agrees.
        ii = add(old["indices"], remapped.astype("<u4").reshape(-1, 1))
        doc["accessors"][ii]["componentType"] = 5125
        doc["accessors"][ii].pop("normalized", None)
        p["indices"] = ii
    references = []
    for mesh in doc.get("meshes", []):
        for p in mesh["primitives"]:
            references += [(p, "indices")]
            references += [(p["attributes"], k) for k in p["attributes"]]
            references += [(target, k) for target in p.get("targets", []) for k in target]
    references += [(s, "inverseBindMatrices") for s in doc.get("skins", []) if "inverseBindMatrices" in s]
    references += [(s, k) for animation in doc.get("animations", []) for s in animation["samplers"] for k in ("input", "output")]
    used = sorted({parent[key] for parent, key in references})
    remap = {old: new for new, old in enumerate(used)}
    for parent, key in references: parent[key] = remap[parent[key]]
    new_accessors, views, binary = [], [], bytearray()
    def view(payload: bytes) -> int:
        while len(binary) % 4: binary.append(0)
        index = len(views); views.append({"buffer": 0, "byteOffset": len(binary), "byteLength": len(payload)})
        binary.extend(payload); return index
    for old in used:
        a = copy.deepcopy(doc["accessors"][old]); a["bufferView"] = view(arrays[old].tobytes(order="C"))
        a.pop("byteOffset", None); a.pop("sparse", None); new_accessors.append(a)
    for image in doc.get("images", []): image["bufferView"] = view(source.image(image))
    doc["accessors"], doc["bufferViews"], doc["buffers"] = new_accessors, views, [{"byteLength": len(binary)}]
    doc.setdefault("extras", {})["yugaLodCandidate"] = extras
    raw_json = json.dumps(doc, separators=(",", ":"), ensure_ascii=False).encode()
    raw_json += b" " * (-len(raw_json) % 4)
    binary += b"\0" * (-len(binary) % 4)
    header = struct.pack("<4sII", b"glTF", 2, 12 + 8 + len(raw_json) + 8 + len(binary))
    output.write_bytes(header + struct.pack("<II", len(raw_json), 0x4E4F534A) + raw_json + struct.pack("<II", len(binary), 0x004E4942) + binary)

def validate_pair(source: GLB, candidate: GLB) -> dict:
    """Independent pair checks; identity of selected vertex records is enforced."""
    checks = []
    def require(value: bool, name: str):
        if not value: raise ValueError(name)
        checks.append(name)
    s, c = source.doc, candidate.doc
    for key in ("nodes", "scenes", "scene", "materials", "textures", "samplers", "extensionsUsed", "extensionsRequired"):
        require(s.get(key) == c.get(key), f"Unchanged {key}")
    require(len(s.get("skins", [])) == len(c.get("skins", [])), "Skin count preserved")
    for ss, cs in zip(s.get("skins", []), c.get("skins", [])):
        require({k:v for k,v in ss.items() if k != "inverseBindMatrices"} == {k:v for k,v in cs.items() if k != "inverseBindMatrices"}, "Skin joint order and skeleton preserved")
        require(np.array_equal(source.array(ss["inverseBindMatrices"]), candidate.array(cs["inverseBindMatrices"])), "Exact inverse-bind matrices")
    require(len(s.get("animations", [])) == len(c.get("animations", [])), "Animation count preserved")
    for sa, ca in zip(s.get("animations", []), c.get("animations", [])):
        require({k:v for k,v in sa.items() if k != "samplers"} == {k:v for k,v in ca.items() if k != "samplers"}, "Animation names/channels preserved")
        require(len(sa["samplers"]) == len(ca["samplers"]), "Animation sampler count preserved")
        for ss, cs in zip(sa["samplers"], ca["samplers"]):
            require(ss.get("interpolation", "LINEAR") == cs.get("interpolation", "LINEAR"), "Animation interpolation preserved")
            for key in ("input", "output"):
                require(np.array_equal(source.array(ss[key]), candidate.array(cs[key])), f"Exact animation {key}")
    require(len(s.get("images", [])) == len(c.get("images", [])), "Image count preserved")
    for si, ci in zip(s.get("images", []), c.get("images", [])):
        require(source.image(si) == candidate.image(ci), "Exact embedded image payload")
    require(len(list(source.primitives())) == len(list(candidate.primitives())), "Primitive/material partition count preserved")
    require(len(s.get("meshes", [])) == len(c.get("meshes", [])), "Mesh count preserved")
    for sm, cm in zip(s.get("meshes", []), c.get("meshes", [])):
        require({k:v for k,v in sm.items() if k != "primitives"} == {k:v for k,v in cm.items() if k != "primitives"}, "Mesh names/morph weights preserved")
    for (mi, pi, sp), (_, _, cp) in zip(source.primitives(), candidate.primitives()):
        require(sp.get("material") == cp.get("material") and cp.get("mode", 4) == 4, f"Primitive {mi}/{pi} material/triangle mode")
        require({k:v for k,v in sp.items() if k not in ("attributes", "indices", "targets")} == {k:v for k,v in cp.items() if k not in ("attributes", "indices", "targets")}, "Primitive metadata preserved")
        require(set(sp["attributes"]) == set(cp["attributes"]), f"Primitive {mi}/{pi} all channels preserved")
        require(len(sp.get("targets", [])) == len(cp.get("targets", [])), f"Primitive {mi}/{pi} morph count")
        channels = sorted(sp["attributes"])
        source_arrays = [source.array(sp["attributes"][k]) for k in channels]
        candidate_arrays = [candidate.array(cp["attributes"][k]) for k in channels]
        for st, ct in zip(sp.get("targets", []), cp.get("targets", [])):
            require(set(st) == set(ct), "All morph channels preserved")
            source_arrays += [source.array(st[k]) for k in sorted(st)]
            candidate_arrays += [candidate.array(ct[k]) for k in sorted(ct)]
        # Byte records include skin IDs, weights, normals, UVs, tangents, COLOR_0
        # and every morph delta, preventing accidentally paired different rows.
        def records(arrays):
            rows = [np.ascontiguousarray(a).view(np.uint8).reshape(len(a), -1) for a in arrays]
            packed = np.concatenate(rows, axis=1)
            return {row.tobytes() for row in packed}
        require(records(candidate_arrays) <= records(source_arrays), f"Primitive {mi}/{pi} exact source vertex records")
        pos = candidate.array(cp["attributes"]["POSITION"])
        idx = candidate.array(cp["indices"]).reshape(-1)
        require(len(idx) % 3 == 0 and len(idx) > 0 and int(idx.max()) < len(pos), f"Primitive {mi}/{pi} bounded complete indices")
        for k, ai in cp["attributes"].items():
            a = candidate.array(ai, normalized=True)
            require(np.isfinite(a).all(), f"Primitive {mi}/{pi} finite {k}")
            if k.startswith("WEIGHTS"):
                require(float(a.min()) >= 0, "Nonnegative skin weights")
            if k.startswith("JOINTS"):
                require(float(a.min()) >= 0 and float(a.max()) < min(len(x["joints"]) for x in c["skins"]), "Bounded skin joint indices")
            if k == "COLOR_0":
                require(float(a.min()) >= 0 and float(a.max()) <= 1, "Bounded vertex color/secondary masks")
        weight_arrays = [candidate.array(ai, normalized=True) for k, ai in cp["attributes"].items() if k.startswith("WEIGHTS_")]
        require(bool(weight_arrays) and float(np.abs(sum(a.sum(axis=1) for a in weight_arrays) - 1).max()) < .0002, "Normalized total skin weights")
        normals = candidate.array(cp["attributes"]["NORMAL"], normalized=True)
        require(float(np.abs(np.linalg.norm(normals, axis=1) - 1).max()) < .002, "Unit normals")
        if "normalTexture" in c["materials"][cp["material"]]:
            require("TANGENT" in cp["attributes"], "Normal-mapped primitive keeps tangents")
            tangents = candidate.array(cp["attributes"]["TANGENT"], normalized=True)
            require(float(np.abs(np.linalg.norm(tangents[:, :3], axis=1) - 1).max()) < .002 and bool(np.all(np.abs(tangents[:, 3]) == 1)), "Unit tangent axes and signed handedness")
    require(candidate.measure()["triangles"] <= source.measure()["triangles"], "Triangle count never increases")
    return {"passed": True, "checks": checks, "sourceSha256": digest(source.raw), "candidateSha256": digest(candidate.raw),
            "limits": ["Exact rest/vertex/animation preservation is structural; posed LOD silhouette and switch review remain required."]}
