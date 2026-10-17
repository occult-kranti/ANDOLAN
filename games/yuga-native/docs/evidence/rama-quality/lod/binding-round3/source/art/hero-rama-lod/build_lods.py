"""Create compact, source-pinned automatic LOD candidates, never runtime assets.

The index simplifier chooses existing vertices. Near face/contact vertices and
all nonzero morph-delta vertices are locked. Every original per-vertex channel
is copied for selected vertices; inverse binds, actions, nodes, materials and
textures remain exact. Actual posed/switch review is still an acceptance gate.
"""
from __future__ import annotations
import argparse
import ctypes as ct
import hashlib
import json
import math
from pathlib import Path
import sys
import time
import numpy as np
from glb_lod import GLB, digest, validate_pair, write_compacted

LEVELS = {
    "mid": {"ratio": .40, "errorM": .003, "faceLock": True, "bowRatio": .80},
    "far": {"ratio": .16, "errorM": .006, "faceLock": True, "bowRatio": .45},
}

def simplify(lib, source: GLB, mesh: int, primitive: dict, profile: dict) -> tuple[np.ndarray, dict]:
    attributes = primitive["attributes"]
    positions = np.ascontiguousarray(source.array(attributes["POSITION"]), dtype=np.float32)
    indices = np.ascontiguousarray(source.array(primitive["indices"]).reshape(-1), dtype=np.uint32)
    material = source.doc["materials"][primitive["material"]].get("name", "")
    attrs, attr_weights = [], []
    # Normals, UVs, masks and skin records inform the error metric; all output
    # data is nevertheless copied exactly, never interpolated by this tool.
    for name, weight in (("NORMAL", .02), ("TEXCOORD_0", .015), ("COLOR_0", .01),
                         ("JOINTS_0", .001), ("WEIGHTS_0", .02),
                         ("JOINTS_1", .001), ("WEIGHTS_1", .02)):
        if name not in attributes: continue
        a = np.asarray(source.array(attributes[name], normalized=True), dtype=np.float32)
        if name.startswith("JOINTS_"): a /= max(1, len(source.doc["skins"][0]["joints"]) - 1)
        attrs.append(a); attr_weights += [weight] * a.shape[1]
    packed = np.ascontiguousarray(np.concatenate(attrs, axis=1), dtype=np.float32)
    weights = np.ascontiguousarray(attr_weights, dtype=np.float32)
    if packed.shape[1] > 32: raise ValueError("meshoptimizer v0.24 maximum32 attributes exceeded")
    locked = np.zeros(len(positions), dtype=np.uint8)
    if material in ("Natural lips", "Warm sclera", "Deep brown iris", "Pupil"):
        locked[:] = 1
    if material == "Rama warm skin" and profile["faceLock"]:
        # GLB rig-space bounds are measured before generation. These preserve
        # face, exposed hand/grip and sole contact, rather than hiding defects
        # behind triangle totals. Any new rig/units must explicitly reprofile.
        if not (1.7 < float(positions[:, 1].max()) < 2.1):
            raise ValueError("Unknown anatomy units/bounds; contact lock profile must be reviewed")
        locked[(positions[:, 1] > 1.58) | (positions[:, 1] < .075) |
               ((np.abs(positions[:, 0]) > .42) & (positions[:, 1] > .90) & (positions[:, 1] < 1.30))] = 1
    for target in primitive.get("targets", []):
        # Any facial/other morph is carried exactly and never simplified where
        # it moves. An unchanged row does not establish an accepted expression.
        for ai in target.values(): locked[np.any(source.array(ai) != 0, axis=1)] = 1
    bow_meshes = {node["mesh"] for node in source.doc["nodes"] if node.get("name") == "RamaBow" and "mesh" in node}
    if len(bow_meshes) != 1:
        raise ValueError("Expected one named RamaBow mesh; do not guess bow mesh order")
    ratio = profile["bowRatio"] if mesh in bow_meshes else profile["ratio"]
    target = max(3, int(len(indices) * ratio) // 3 * 3)
    destination = np.empty(len(indices), dtype=np.uint32)
    result_error = ct.c_float()
    count = lib.meshopt_simplifyWithAttributes(
        destination.ctypes.data_as(ct.POINTER(ct.c_uint)), indices.ctypes.data_as(ct.POINTER(ct.c_uint)), len(indices),
        positions.ctypes.data_as(ct.POINTER(ct.c_float)), len(positions), positions.strides[0],
        packed.ctypes.data_as(ct.POINTER(ct.c_float)), packed.strides[0], weights.ctypes.data_as(ct.POINTER(ct.c_float)),
        packed.shape[1], locked.ctypes.data_as(ct.POINTER(ct.c_ubyte)), target, profile["errorM"],
        1 | 4, ct.byref(result_error))  # LockBorder | ErrorAbsolute
    if count == 0 or count % 3: raise ValueError("Simplifier returned incomplete/empty result")
    return destination[:count].copy(), {"sourceTriangles": len(indices)//3, "requestedTriangles": target//3,
        "actualTriangles": count//3, "lockedVertices": int(locked.sum()), "errorMetric": float(result_error.value),
        "errorMetricScope": "meshoptimizer position-plus-weighted-attributes metric; not a measured Hausdorff distance",
        "attributes": {name: weight for name, weight in (("NORMAL", .02), ("TEXCOORD_0", .015), ("COLOR_0", .01),
                        ("JOINTS_0", .001), ("WEIGHTS_0", .02), ("JOINTS_1", .001), ("WEIGHTS_1", .02)) if name in attributes}}

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source", type=Path, required=True)
    ap.add_argument("--library", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--source-provenance", type=Path)
    args = ap.parse_args()
    if args.output.exists(): raise ValueError("Use a fresh output directory; never overwrite an accepted candidate")
    source = GLB(args.source)
    validate_pair(source, source)
    args.output.mkdir(parents=True)
    lib = ct.CDLL(str(args.library.resolve()))
    f = lib.meshopt_simplifyWithAttributes
    f.restype = ct.c_size_t
    f.argtypes = [ct.POINTER(ct.c_uint), ct.POINTER(ct.c_uint), ct.c_size_t, ct.POINTER(ct.c_float), ct.c_size_t,
        ct.c_size_t, ct.POINTER(ct.c_float), ct.c_size_t, ct.POINTER(ct.c_float), ct.c_size_t,
        ct.POINTER(ct.c_ubyte), ct.c_size_t, ct.c_float, ct.c_uint, ct.POINTER(ct.c_float)]
    report = {"schema": 1, "status": "automatic candidates; no runtime promotion", "source": str(args.source),
        "sourceSha256": digest(source.raw), "sourceMeasurement": source.measure(), "levels": {},
        "meshoptimizerCommit": "7b2d4f4c817aea55d74dcd65d9763ac2ca608026", "meshoptimizerLicense": "MIT",
        "librarySha256": digest(args.library.read_bytes()), "generatorSha256": digest(Path(__file__).read_bytes()),
        "plumbingSha256": digest(Path(__file__).with_name("glb_lod.py").read_bytes()),
        "command": sys.argv,
        "limitations": ["Automatic constrained simplification is not hand-authored or production-accepted art.",
            "No source texture reduction, material consolidation or skeleton reduction is performed.",
            "Each candidate contains an identical source rig only as an interchange artifact. Runtime must bind meshes to ONE existing rig.",
            "Near/mid/far pose silhouette, contact and transitions need actual native same-camera review.",
            "No physical-GPU profiling or12-player resource acceptance is implied."]}
    if args.source_provenance:
        report["sourceProvenance"] = str(args.source_provenance)
        report["sourceProvenanceSha256"] = digest(args.source_provenance.read_bytes())
    for name, profile in LEVELS.items():
        start = time.monotonic()
        selected, details = {}, []
        for mi, pi, primitive in source.primitives():
            indices, stats = simplify(lib, source, mi, primitive, profile)
            selected[(mi, pi)] = indices
            details.append({"mesh": mi, "primitive": pi, **stats})
        output = args.output / f"rama-hero-{name}.glb"
        write_compacted(source, selected, output, {"sourceSha256": digest(source.raw), "level": name,
            "profile": profile, "status": "unaccepted automatic candidate"})
        candidate = GLB(output)
        validation = validate_pair(source, candidate)
        (args.output / f"{name}-validation.json").write_text(json.dumps(validation, indent=2) + "\n")
        report["levels"][name] = {"file": output.name, "profile": profile, "measurement": candidate.measure(),
            "primitives": details, "elapsedBuildAndValidationSeconds": time.monotonic() - start,
            "validationSha256": digest((args.output / f"{name}-validation.json").read_bytes())}
    (args.output / "lod-report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"sourceSha256": report["sourceSha256"], "levels": {n:{k:v for k,v in d["measurement"].items()
          if k in ("sha256", "fileBytes", "vertices", "triangles", "vertexBytes", "indexBytes", "primitiveDrawsPerViewPass")} for n,d in report["levels"].items()}}, indent=2))

if __name__ == "__main__":
    main()
