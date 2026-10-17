#!/usr/bin/env python3
"""Conservative, append-only offline GLB triangle repair; never promotes assets.

Original YUGA authoring code. NumPy and the existing lossless GLB reader only.
Area/UV tolerances are diagnostic: removal always requires an exact persistent
coincident-pair proof under the selected, explicitly bounded deformation policy.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import sys
import numpy as np

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[1]
READER = HERE.parent / "hero-rama-lod/glb_lod.py"
SHADER = PROJECT / "shaders/rama_secondary_cloth.gdshader"
YUGA_SOURCE = "de61dc4c470920eab6f3265bc5467da7f9fb33d6fae2129a9353e7ca6d24d3f5"
YUGA_SHADER = "c1712f075af34b0e57dd7f70e5494c2060703e7f1ee68ff87c8a645cff95c6d7"
POLICIES = ("strict", "yuga-secondary-v1")
spec = importlib.util.spec_from_file_location("yuga_repair_glb_reader", READER)
reader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reader)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def integer(value, label, minimum=0, maximum=100_000_000):
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f"Invalid {label}")
    return value


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key")
        result[key] = value
    return result


def reject_constant(value):
    raise ValueError("Nonfinite JSON number")


def read_checked(path):
    """Bound allocations/storage before invoking the shared sparse-aware reader.

    This is a deliberately narrow GLB subset, not a full glTF validator.
    """
    path = Path(path)
    if not 28 <= path.stat().st_size <= 256 * 1024 * 1024:
        raise ValueError("GLB size outside bounded subset")
    raw = path.read_bytes()
    if struct.unpack_from("<4sII", raw) != (b"glTF", 2, len(raw)):
        raise ValueError("Invalid GLB header")
    jlen, jtype = struct.unpack_from("<II", raw, 12)
    end = 20 + jlen
    if jtype != 0x4E4F534A or jlen % 4 or jlen > 16 * 1024 * 1024 or end + 8 > len(raw):
        raise ValueError("Invalid JSON chunk")
    blen, btype = struct.unpack_from("<II", raw, end)
    if btype != 0x004E4942 or blen % 4 or end + 8 + blen != len(raw):
        raise ValueError("Invalid BIN chunk")
    doc = json.loads(raw[20:end], object_pairs_hook=unique_object,
                     parse_constant=reject_constant)
    if not isinstance(doc, dict) or doc.get("asset", {}).get("version") != "2.0":
        raise ValueError("Expected glTF2 asset")
    # Material-only extensions are position-independent. Unknown geometry,
    # instancing, animation or vertex-deforming contracts must be decoded first.
    allowed = {"KHR_materials_specular", "KHR_materials_sheen"}
    def extensions(value):
        if isinstance(value, dict):
            for name in value.get("extensions", {}):
                if name not in allowed:
                    raise ValueError(f"Unsupported extension {name}")
            for item in value.values():
                extensions(item)
        elif isinstance(value, list):
            for item in value:
                extensions(item)
    extensions(doc)
    if set(doc.get("extensionsUsed", [])) - allowed or set(doc.get("extensionsRequired", [])) - allowed:
        raise ValueError("Unknown extension contract")
    buffers = doc.get("buffers", [])
    if len(buffers) != 1 or "uri" in buffers[0]:
        raise ValueError("Expected one embedded buffer")
    logical = integer(buffers[0].get("byteLength"), "buffer length", 1)
    binary = raw[end + 8:]
    if not 0 <= len(binary) - logical <= 3 or any(binary[logical:]):
        raise ValueError("Invalid buffer length or padding")
    views, accessors = doc.get("bufferViews", []), doc.get("accessors", [])
    if not isinstance(views, list) or not isinstance(accessors, list) or len(views) > 100_000 or len(accessors) > 100_000:
        raise ValueError("Invalid/bounded storage lists")
    def view_at(index):
        return views[integer(index, "bufferView index", 0, len(views) - 1)]
    for v in views:
        if v.get("buffer") != 0:
            raise ValueError("External view buffer")
        off = integer(v.get("byteOffset", 0), "view offset")
        size = integer(v.get("byteLength"), "view length", 1)
        if off + size > logical:
            raise ValueError("View exceeds logical buffer")
        if "byteStride" in v:
            stride = integer(v["byteStride"], "stride", 4, 252)
            if stride % 4:
                raise ValueError("Unaligned stride")
    expanded_bytes = 0
    for a in accessors:
        count = integer(a.get("count"), "accessor count", 1, 6_000_000)
        ct, shape = a.get("componentType"), a.get("type")
        if ct not in reader.DTYPES or shape not in reader.WIDTHS:
            raise ValueError("Unsupported accessor type")
        size = reader.DTYPES[ct].itemsize
        width = reader.WIDTHS[shape]
        expanded_bytes += count * size * width
        if expanded_bytes > 512 * 1024 * 1024:
            raise ValueError("Expanded accessor budget exceeded")
        offset = integer(a.get("byteOffset", 0), "accessor offset")
        if type(a.get("normalized", False)) is not bool or (a.get("normalized") and ct not in (5120, 5121, 5122, 5123)):
            raise ValueError("Invalid normalization")
        if "bufferView" in a:
            v = view_at(a["bufferView"])
            stride = v.get("byteStride", size * width)
            if (offset + v.get("byteOffset", 0)) % size or stride < size * width or stride % size or offset + (count - 1) * stride + size * width > v["byteLength"]:
                raise ValueError("Invalid accessor layout")
        elif offset or "sparse" not in a:
            raise ValueError("Accessor without storage")
        if "sparse" in a:
            s = a["sparse"]
            n = integer(s.get("count"), "sparse count", 1, count)
            sc = s["indices"].get("componentType")
            if sc not in (5121, 5123, 5125):
                raise ValueError("Invalid sparse index type")
            for item, step in ((s["indices"], reader.DTYPES[sc].itemsize), (s["values"], size * width)):
                v = view_at(item.get("bufferView"))
                off = integer(item.get("byteOffset", 0), "sparse offset")
                align = reader.DTYPES[sc].itemsize if item is s["indices"] else size
                if "byteStride" in v or (v.get("byteOffset", 0) + off) % align or off + n * step > v["byteLength"]:
                    raise ValueError("Invalid sparse layout")
    for image in doc.get("images", []):
        if "uri" in image or "bufferView" not in image:
            raise ValueError("External/unsupported image")
        view_at(image["bufferView"])
    glb = reader.GLB(path)
    if glb.doc != doc:
        raise ValueError("Parser disagreement")
    return glb


def equal_rows(array, left, right):
    data = np.ascontiguousarray(array).view(np.uint8).reshape(len(array), -1)
    return np.all(data[left] == data[right], axis=1)


def coincident_proof(indices, attributes, targets, policy):
    """Exact pair proof. Numeric tolerance is never a removal criterion.

    Strict includes every record. YUGA includes every position-driving channel
    of the pinned core skin/morph + COLOR-driven shader contract.
    """
    if policy not in POLICIES:
        raise ValueError("Unknown deformation policy")
    repeated = (indices[:, 0] == indices[:, 1]) | (indices[:, 1] == indices[:, 2]) | (indices[:, 0] == indices[:, 2])
    keys = sorted(attributes) if policy == "strict" else [k for k in sorted(attributes) if k == "POSITION" or k.startswith(("JOINTS_", "WEIGHTS_", "COLOR_"))]
    arrays = [attributes[k] for k in keys]
    arrays += [target[k] for target in targets for k in sorted(target) if policy == "strict" or k == "POSITION"]
    proven = repeated.copy()
    for a, b in ((0, 1), (1, 2), (2, 0)):
        pair = np.ones(len(indices), dtype=bool)
        for array in arrays:
            pair &= equal_rows(array, indices[:, a], indices[:, b])
        proven |= pair
    return proven, repeated


def area_diagnostic(points):
    """Dimensionless local-edge-scale criterion; diagnostic only."""
    p = points.astype(np.float64)
    a, b, c = p[:, 1] - p[:, 0], p[:, 2] - p[:, 0], p[:, 2] - p[:, 1]
    scale = np.maximum.reduce([np.einsum("ij,ij->i", e, e) for e in (a, b, c)])
    if p.shape[2] == 3:
        cross = np.cross(a, b)
        area = np.linalg.norm(cross, axis=1)
    else:
        area = np.abs(a[:, 0] * b[:, 1] - a[:, 1] * b[:, 0])
    exact = area == 0
    near = area <= (64 * np.finfo(np.float64).eps) * scale
    return {"float64ExactlyZero": int(exact.sum()), "scaleRelativeNearZero": int(near.sum()), "positiveNearZeroRetainedUnlessPairProven": int((near & ~exact).sum())}


def inspect(glb, policy):
    results, selections = [], {}
    accessors = glb.doc["accessors"]
    def array(index):
        index = integer(index, "accessor reference", 0, len(accessors) - 1)
        value = glb.array(index)
        if not np.isfinite(value).all():
            raise ValueError("Nonfinite accessor data")
        return value
    # Validate even currently unreferenced sparse/animation data without a large
    # cache. Its bytes will be preserved, not re-encoded.
    for i in range(len(accessors)):
        array(i)
    for mi, pi, primitive in glb.primitives():
        if primitive.get("mode", 4) != 4 or "indices" not in primitive:
            raise ValueError("Only indexed TRIANGLES supported")
        attrs = primitive.get("attributes", {})
        if "POSITION" not in attrs:
            raise ValueError("Missing POSITION")
        arrays = {k: array(v) for k, v in attrs.items()}
        pos = arrays["POSITION"]
        pa = accessors[attrs["POSITION"]]
        if pa["type"] != "VEC3" or pa["componentType"] != 5126 or len(pos) > 2_000_000:
            raise ValueError("Expected bounded float32 POSITION")
        if any(len(v) != len(pos) for v in arrays.values()):
            raise ValueError("Attribute count mismatch")
        for k in attrs:
            if k.startswith(("JOINTS_", "WEIGHTS_")):
                partner = ("WEIGHTS_" if k.startswith("JOINTS_") else "JOINTS_") + k.split("_", 1)[1]
                if partner not in attrs or arrays[k].shape[1] != 4:
                    raise ValueError("Unpaired/invalid skin attributes")
        if "material" in primitive:
            integer(primitive["material"], "material reference", 0, len(glb.doc.get("materials", [])) - 1)
        ia = accessors[integer(primitive["indices"], "index accessor", 0, len(accessors) - 1)]
        if ia["type"] != "SCALAR" or ia["componentType"] not in (5121, 5123, 5125) or ia.get("normalized"):
            raise ValueError("Expected unsigned scalar indices")
        idx = array(primitive["indices"]).reshape(-1)
        if not len(idx) or len(idx) % 3 or int(idx.max()) >= len(pos):
            raise ValueError("Invalid triangle indices")
        idx = idx.reshape(-1, 3)
        targets = []
        for target in primitive.get("targets", []):
            values = {k: array(v) for k, v in target.items()}
            if set(values) - {"POSITION", "NORMAL", "TANGENT"}:
                raise ValueError("Unknown morph semantics")
            for key, value in values.items():
                a = accessors[target[key]]
                if len(value) != len(pos) or a["type"] != "VEC3" or a["componentType"] != 5126:
                    raise ValueError("Invalid morph data")
            targets.append(values)
        proof, repeated = coincident_proof(idx, arrays, targets, policy)
        strict, _ = coincident_proof(idx, arrays, targets, "strict")
        core_attrs = {k: v for k, v in arrays.items() if not k.startswith("COLOR_")}
        core, _ = coincident_proof(idx, core_attrs, targets, "yuga-secondary-v1")
        geometry = area_diagnostic(pos[idx])
        uv = {k: area_diagnostic(v[idx]) for k, v in arrays.items() if k.startswith("TEXCOORD_") and v.shape[1] == 2}
        kept = idx[~proof]
        selections[(mi, pi)] = kept
        results.append({"mesh": mi, "primitive": pi, "meshName": glb.doc["meshes"][mi].get("name"), "material": primitive.get("material"), "trianglesBefore": len(idx), "trianglesAfter": len(kept), "removedPairProven": int(proof.sum()), "repeatedIndex": int(repeated.sum()), "strictAllRecordProof": int(strict.sum()), "coreSkinMorphOnlyProofNotSufficient": int(core.sum()), "excludedByColorContract": int((core & ~proof).sum()) if policy != "strict" else None, "geometryDiagnostic": geometry, "uvDiagnostic": uv, "removedFaceOrdinals": np.flatnonzero(proof).tolist(), "blockedEmptyPrimitive": not bool(len(kept))})
    if not results:
        raise ValueError("No mesh primitives")
    return results, selections


def encode_candidate(glb, selections):
    doc = copy.deepcopy(glb.doc)
    binary = bytearray(glb.binary)  # Keep every old byte, including padding.
    changed = 0
    for mi, pi, primitive in glb.primitives():
        kept = selections[(mi, pi)]
        if not len(kept):
            raise ValueError("Refuse empty primitive; author review required")
        old = glb.array(primitive["indices"]).reshape(-1)
        if kept.size == old.size:
            continue
        changed += 1
        a = copy.deepcopy(doc["accessors"][primitive["indices"]])
        for key in ("bufferView", "byteOffset", "sparse", "normalized"):
            a.pop(key, None)
        while len(binary) % 4:
            binary.append(0)
        payload = kept.astype(reader.DTYPES[a["componentType"]], copy=False).reshape(-1)
        vi = len(doc["bufferViews"])
        doc["bufferViews"].append({"buffer": 0, "byteOffset": len(binary), "byteLength": payload.nbytes, "target": 34963})
        binary.extend(payload.tobytes())
        a.update(bufferView=vi, count=int(payload.size), min=[int(payload.min())], max=[int(payload.max())])
        ai = len(doc["accessors"])
        doc["accessors"].append(a)
        doc["meshes"][mi]["primitives"][pi]["indices"] = ai
    if not changed:
        return glb.raw
    doc["buffers"][0]["byteLength"] = len(binary)
    js = json.dumps(doc, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()
    js += b" " * (-len(js) % 4)
    binary += b"\0" * (-len(binary) % 4)
    return struct.pack("<4sII", b"glTF", 2, 28 + len(js) + len(binary)) + struct.pack("<II", len(js), 0x4E4F534A) + js + struct.pack("<II", len(binary), 0x004E4942) + binary


def verify_preservation(source, candidate, selections):
    """Reject ANY metadata change other than appendices, buffer length, indices."""
    s, c = source.doc, candidate.doc
    if not candidate.binary.startswith(source.binary):
        raise ValueError("Old binary bytes changed")
    expected = copy.deepcopy(s)
    for key in ("accessors", "bufferViews"):
        if c[key][:len(s[key])] != s[key]:
            raise ValueError(f"Old {key} metadata changed")
        expected[key] = copy.deepcopy(c[key])
    expected["buffers"][0]["byteLength"] = c["buffers"][0]["byteLength"]
    for mi, pi, p in source.primitives():
        cp = c["meshes"][mi]["primitives"][pi]
        expected["meshes"][mi]["primitives"][pi]["indices"] = cp["indices"]
        if not np.array_equal(candidate.array(cp["indices"]).reshape(-1), selections[(mi, pi)].reshape(-1)):
            raise ValueError("Candidate triangle selection differs")
    if expected != c:
        raise ValueError("Non-index document metadata changed")
    return {"passed": True, "oldBinaryPrefixExact": True, "allOldAccessorsAndViewsExact": True, "allNonIndexDocumentMetadataExact": True, "selectedIndicesExact": True, "sourceUnchanged": digest(source.path.read_bytes()) == digest(source.raw)}


def fresh_paths(source, candidate, report):
    resolved = [Path(x).resolve() for x in (source, candidate, report)]
    if len(set(resolved)) != 3:
        raise ValueError("Source/output aliases")
    for original, path in zip((candidate, report), resolved[1:]):
        if Path(original).is_symlink() or path.exists():
            raise ValueError("Outputs must be fresh, never overwritten")
    if PROJECT == resolved[1] or PROJECT in resolved[1].parents:
        raise ValueError("Candidate must remain outside native project")
    return resolved


def repair(source, candidate, report, policy="strict"):
    source, candidate, report = fresh_paths(source, candidate, report)
    if policy not in POLICIES:
        raise ValueError("Unknown deformation policy")
    glb = read_checked(source)
    if policy == "yuga-secondary-v1" and (digest(glb.raw) != YUGA_SOURCE or digest(SHADER.read_bytes()) != YUGA_SHADER):
        raise ValueError("Experimental YUGA policy requires exact pinned source and shader")
    domains, selections = inspect(glb, policy)
    blocked = any(d["blockedEmptyPrimitive"] for d in domains)
    result = {"schema": 1, "kind": "offline-persistent-pair-mesh-repair", "source": str(source), "sourceSha256": digest(glb.raw), "sourceBytes": len(glb.raw), "policy": policy, "candidatePath": str(candidate), "candidateWritten": False, "promoted": False, "blockedEmptyPrimitive": blocked, "domains": domains, "trianglesBefore": sum(d["trianglesBefore"] for d in domains), "trianglesAfter": sum(d["trianglesAfter"] for d in domains), "removedPairProven": sum(d["removedPairProven"] for d in domains), "sourcePins": {"repairMeshSha256": digest(Path(__file__).read_bytes()), "readerSha256": digest(READER.read_bytes()), "secondaryShaderSha256": digest(SHADER.read_bytes()) if policy == "yuga-secondary-v1" else None}, "limits": ["No runtime asset promotion or renderer/pose/shading acceptance.", "Scale-relative geometry and UV degeneracy are diagnosis only; no tolerance removes geometry.", "Strict proof retains seam duplicates; YUGA opt-in is restricted to exact source and known core skin/morph + COLOR shader.", "No guarantee for vertex-ID-dependent, unknown custom shader, procedural or external deformation.", "Appending indices retains old unused index storage; this is not file-size optimization."]}
    if not blocked:
        payload = encode_candidate(glb, selections)
        candidate.parent.mkdir(parents=True, exist_ok=True)
        with candidate.open("xb") as stream:
            stream.write(payload)
        checked = read_checked(candidate)
        result["preservation"] = verify_preservation(glb, checked, selections)
        if not result["preservation"]["sourceUnchanged"]:
            raise ValueError("Source changed during operation")
        after, _ = inspect(checked, policy)
        if any(d["removedPairProven"] for d in after):
            raise ValueError("Pair-proven faces remain after repair")
        result.update(candidateWritten=True, candidateSha256=digest(payload), candidateBytes=len(payload), noOpExactCopy=(payload == glb.raw), afterDomains=after)
    report.parent.mkdir(parents=True, exist_ok=True)
    with report.open("x") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--deformation-policy", choices=POLICIES, default="strict")
    args = parser.parse_args()
    try:
        report = repair(args.source, args.candidate, args.report, args.deformation_policy)
    except (ValueError, KeyError, IndexError, TypeError, OSError, struct.error, UnicodeError) as exc:
        print(f"Refused: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({k: report.get(k) for k in ("candidateWritten", "removedPairProven", "trianglesBefore", "trianglesAfter", "candidateSha256", "noOpExactCopy", "blockedEmptyPrimitive")}))
    return 2 if report["blockedEmptyPrimitive"] else 0


if __name__ == "__main__":
    sys.exit(main())
