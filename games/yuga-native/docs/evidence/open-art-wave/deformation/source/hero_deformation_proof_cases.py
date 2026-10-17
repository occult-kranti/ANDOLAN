#!/usr/bin/env python3
"""Independent offline deformation and complete-row lineage proof.

The numerical oracle, GLB reader, record selector and conservation checks here
do not call the authoring modules' corresponding readers/validators. Only the
production pair predicate is exercised as the subject under test. No renderer,
native Mikk execution, runtime promotion or whole-animation coverage is implied.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import traceback
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
REPAIR = ROOT / "art/hero-rama-repair/repair_mesh.py"
SPLIT = ROOT / "art/hero-rama-repair/split_seams.py"
SHADER = ROOT / "shaders/rama_secondary_cloth.gdshader"
SOURCE_SHA = "de61dc4c470920eab6f3265bc5467da7f9fb33d6fae2129a9353e7ca6d24d3f5"
SHADER_SHA = "c1712f075af34b0e57dd7f70e5494c2060703e7f1ee68ff87c8a645cff95c6d7"
DT = {5120: np.dtype("i1"), 5121: np.dtype("u1"), 5122: np.dtype("<i2"),
      5123: np.dtype("<u2"), 5125: np.dtype("<u4"), 5126: np.dtype("<f4")}
WIDTH = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(value, message):
    if not value:
        raise AssertionError(message)


class IndependentGLB:
    """Small independent dense/sparse/interleaved decoder for reviewed GLBs."""
    def __init__(self, path):
        self.path = Path(path)
        self.raw = self.path.read_bytes()
        require(struct.unpack_from("<4sII", self.raw) == (b"glTF", 2, len(self.raw)), "GLB header")
        size, kind = struct.unpack_from("<II", self.raw, 12)
        require(kind == 0x4E4F534A, "JSON chunk")
        self.doc = json.loads(self.raw[20:20 + size])
        start = 20 + size
        size, kind = struct.unpack_from("<II", self.raw, start)
        require(kind == 0x004E4942 and start + 8 + size == len(self.raw), "BIN chunk")
        self.binary = self.raw[start + 8:]
        require(len(self.doc["buffers"]) == 1 and "uri" not in self.doc["buffers"][0], "embedded buffer")

    def view(self, index):
        spec = self.doc["bufferViews"][index]
        off = spec.get("byteOffset", 0)
        return self.binary[off:off + spec["byteLength"]]

    def array(self, index):
        spec = self.doc["accessors"][index]
        dtype, width = DT[spec["componentType"]], WIDTH[spec["type"]]
        count = spec["count"]
        require(type(count) is int and 0 <= count <= 6_000_000, "bounded accessor count")
        value = np.zeros((count, width), dtype=dtype)
        if "bufferView" in spec:
            view = self.doc["bufferViews"][spec["bufferView"]]
            payload = self.view(spec["bufferView"])
            stride, off = view.get("byteStride", dtype.itemsize * width), spec.get("byteOffset", 0)
            require(count == 0 or off + (count - 1) * stride + width * dtype.itemsize <= len(payload), "accessor bounds")
            value = np.ndarray((count, width), dtype=dtype, buffer=payload,
                               offset=off, strides=(stride, dtype.itemsize)).copy()
        if "sparse" in spec:
            sparse = spec["sparse"]
            si, sv, n = sparse["indices"], sparse["values"], sparse["count"]
            indices = np.frombuffer(self.view(si["bufferView"]), dtype=DT[si["componentType"]],
                                    count=n, offset=si.get("byteOffset", 0))
            values = np.frombuffer(self.view(sv["bufferView"]), dtype=dtype,
                                   count=n * width, offset=sv.get("byteOffset", 0)).reshape(n, width)
            require(len(indices) and indices[-1] < count and np.all(indices[1:] > indices[:-1]), "sparse bounds/order")
            value[indices] = values
        return value

    def primitives(self):
        return [(mi, pi, p) for mi, mesh in enumerate(self.doc["meshes"])
                for pi, p in enumerate(mesh["primitives"])]


def rows_key(arrays):
    packed = np.concatenate([np.ascontiguousarray(a).view(np.uint8).reshape(len(a), -1)
                             for a in arrays], axis=1)
    return np.ascontiguousarray(packed).view(np.dtype((np.void, packed.shape[1]))).reshape(-1)


def independent_selection(attrs, targets, indices, strict=False):
    keys = sorted(attrs) if strict else [k for k in sorted(attrs)
                                            if k == "POSITION" or k.startswith(("JOINTS_", "WEIGHTS_", "COLOR_"))]
    values = [attrs[k] for k in keys]
    values += [target[k] for target in targets for k in sorted(target) if strict or k == "POSITION"]
    records = rows_key(values)
    triangle = indices.reshape(-1, 3)
    equal = (records[triangle[:, 0]] == records[triangle[:, 1]])
    equal |= (records[triangle[:, 0]] == records[triangle[:, 2]])
    equal |= (records[triangle[:, 1]] == records[triangle[:, 2]])
    return triangle[~equal], equal


def evaluate(attrs, targets, weights, transforms, offset):
    """Independent glTF position morph, linear skin blend, then pinned warp."""
    position = attrs["POSITION"].astype(np.float64).copy()
    for influence, target in zip(weights, targets):
        if "POSITION" in target:
            position += float(influence) * target["POSITION"]
    sets = sorted(k[7:] for k in attrs if k.startswith("JOINTS_"))
    if sets:
        homogeneous = np.column_stack([position, np.ones(len(position))])
        posed = np.zeros((len(position), 4))
        for suffix in sets:
            joint, amount = attrs["JOINTS_" + suffix], attrs["WEIGHTS_" + suffix]
            for lane in range(4):
                posed += amount[:, lane:lane + 1] * np.einsum("nij,nj->ni", transforms[joint[:, lane]], homogeneous)
        position = posed[:, :3]
    if "COLOR_0" in attrs:
        position += np.asarray(offset) * np.clip(attrs["COLOR_0"][:, 3:4], 0, 1) ** 2
    return position


def double_area(position):
    return float(np.linalg.norm(np.cross(position[1] - position[0], position[2] - position[0])))


def metadata_preserved(source, candidate, seam):
    require(candidate.binary.startswith(source.binary), "original BIN prefix changed")
    require(len(source.doc["buffers"]) == len(candidate.doc["buffers"]) == 1, "buffer count changed")
    require({k: v for k, v in source.doc["buffers"][0].items() if k != "byteLength"} ==
            {k: v for k, v in candidate.doc["buffers"][0].items() if k != "byteLength"}, "buffer metadata changed")
    for key in ("accessors", "bufferViews"):
        require(candidate.doc[key][:len(source.doc[key])] == source.doc[key], "original " + key + " changed")
    for key in set(source.doc) | set(candidate.doc):
        if key not in ("buffers", "bufferViews", "accessors", "meshes"):
            require(source.doc.get(key) == candidate.doc.get(key), "metadata changed: " + key)
    require(len(source.doc["meshes"]) == len(candidate.doc["meshes"]), "mesh count changed")
    for sm, cm in zip(source.doc["meshes"], candidate.doc["meshes"]):
        require({k: v for k, v in sm.items() if k != "primitives"} ==
                {k: v for k, v in cm.items() if k != "primitives"}, "mesh metadata changed")
        require(len(sm["primitives"]) == len(cm["primitives"]), "primitive count changed")
        for sp, cp in zip(sm["primitives"], cm["primitives"]):
            excluded = {"indices", "attributes", "targets"} if seam else {"indices"}
            require({k: v for k, v in sp.items() if k not in excluded} ==
                    {k: v for k, v in cp.items() if k not in excluded}, "primitive metadata changed")
            require(set(sp["attributes"]) == set(cp["attributes"]), "attribute set changed")
            require(len(sp.get("targets", [])) == len(cp.get("targets", [])), "morph count changed")
            for st, ct in zip(sp.get("targets", []), cp.get("targets", [])):
                require(set(st) == set(ct), "morph channel set changed")
            if seam:
                pairs = [(sp["attributes"][k], cp["attributes"][k]) for k in sp["attributes"]]
                pairs += [(st[k], ct[k]) for st, ct in zip(sp.get("targets", []), cp.get("targets", [])) for k in st]
                for original, appended in pairs:
                    excluded = {"bufferView", "byteOffset", "sparse", "count"}
                    require({k: v for k, v in source.doc["accessors"][original].items() if k not in excluded} ==
                            {k: v for k, v in candidate.doc["accessors"][appended].items() if k not in excluded}, "attribute/morph interpretation metadata changed")
    for animation in source.doc.get("animations", []):
        for sampler in animation["samplers"]:
            for key in ("input", "output"):
                require(source.array(sampler[key]).tobytes() == candidate.array(sampler[key]).tobytes(), "animation payload changed")
    for skin in source.doc.get("skins", []):
        if "inverseBindMatrices" in skin:
            ai = skin["inverseBindMatrices"]
            require(source.array(ai).tobytes() == candidate.array(ai).tobytes(), "inverse bind changed")
    for image in source.doc.get("images", []):
        require(source.view(image["bufferView"]) == candidate.view(image["bufferView"]), "image changed")


def verify_repair(source, candidate):
    metadata_preserved(source, candidate, False)
    totals = {"removed": 0, "retained": 0, "domains": 0, "attributeChannels": 0, "morphChannels": 0}
    for mi, pi, sp in source.primitives():
        cp = candidate.doc["meshes"][mi]["primitives"][pi]
        attrs = {k: source.array(ai) for k, ai in sp["attributes"].items()}
        targets = [{k: source.array(ai) for k, ai in t.items()} for t in sp.get("targets", [])]
        expected, removed = independent_selection(attrs, targets, source.array(sp["indices"]).reshape(-1))
        require(expected.reshape(-1).tobytes() == candidate.array(cp["indices"]).reshape(-1).tobytes(), "independent retained index/order mismatch")
        for key, ai in sp["attributes"].items():
            require(attrs[key].tobytes() == candidate.array(cp["attributes"][key]).tobytes(), "repair attribute changed")
        for st, ct in zip(sp.get("targets", []), cp.get("targets", [])):
            for key, ai in st.items():
                require(source.array(ai).tobytes() == candidate.array(ct[key]).tobytes(), "repair morph changed")
        totals["removed"] += int(removed.sum())
        totals["retained"] += len(expected)
        totals["domains"] += 1
        totals["attributeChannels"] += len(attrs)
        totals["morphChannels"] += sum(len(t) for t in targets)
    return totals


def verify_seams(source, candidate):
    metadata_preserved(source, candidate, True)
    totals = {"clones": 0, "triangles": 0, "domains": 0, "attributeChannels": 0, "morphChannels": 0, "clonedMorphChannels": 0}
    for mi, pi, sp in source.primitives():
        cp = candidate.doc["meshes"][mi]["primitives"][pi]
        old = source.array(sp["indices"]).reshape(-1)
        new = candidate.array(cp["indices"]).reshape(-1)
        n = len(source.array(sp["attributes"]["POSITION"]))
        count = len(candidate.array(cp["attributes"]["POSITION"]))
        require(len(old) == len(new) and count >= n and np.all(new < count), "seam index/count bounds")
        mapping = np.arange(count, dtype=np.uint32)
        for clone in range(n, count):
            lineage = np.unique(old[new == clone])
            require(len(lineage) == 1, "clone missing/ambiguous corner lineage")
            mapping[clone] = lineage[0]
        require(np.array_equal(mapping[new], old), "seam ordered corner lineage changed")
        for key, ai in sp["attributes"].items():
            require(source.array(ai)[mapping].tobytes() == candidate.array(cp["attributes"][key]).tobytes(), "seam attribute row corruption: " + key)
        for st, ct in zip(sp.get("targets", []), cp.get("targets", [])):
            for key, ai in st.items():
                require(source.array(ai)[mapping].tobytes() == candidate.array(ct[key]).tobytes(), "seam morph row corruption: " + key)
        totals["clones"] += count - n
        totals["triangles"] += len(new) // 3
        totals["domains"] += 1
        totals["attributeChannels"] += len(sp["attributes"])
        totals["morphChannels"] += sum(len(t) for t in sp.get("targets", []))
        if count > n:
            totals["clonedMorphChannels"] += sum(len(t) for t in sp.get("targets", []))
    return totals


def decoded_seam_fixture():
    """Explicit decoded-data fixture, not a produced or rendered GLB asset."""
    class Decoded:
        def array(self, index):
            return self.arrays[index]
        def primitives(self):
            return [(0, 0, self.doc["meshes"][0]["primitives"][0])]
    source = Decoded()
    source.binary = b"unchanged-fixture-prefix"
    source.arrays = []
    source.doc = {"asset": {"version": "2.0"}, "buffers": [{"byteLength": len(source.binary)}],
                  "bufferViews": [], "accessors": [], "meshes": [{"primitives": []}]}
    def add(value):
        ai = len(source.arrays)
        value = np.asarray(value, dtype=np.float32)
        source.arrays.append(value)
        source.doc["accessors"].append({"count": len(value), "type": "fixture", "normalized": False})
        return ai
    attrs = {"POSITION": add([[0, 0, 0], [1, 0, 0], [0, 1, 0]]),
             "COLOR_0": add([[1, 1, 1, .4]] * 3),
             "WEIGHTS_0": add([[1, 0, 0, 0]] * 3)}
    target = {k: add(np.arange(9).reshape(3, 3) / 10) for k in ("POSITION", "NORMAL", "TANGENT")}
    ii = add(np.array([0, 1, 2, 0, 2, 1], dtype=np.uint32).reshape(-1, 1))
    source.arrays[ii] = source.arrays[ii].astype(np.uint32)
    source.doc["meshes"][0]["primitives"].append({"attributes": attrs, "indices": ii, "targets": [target]})
    candidate = copy.deepcopy(source)
    primitive = candidate.doc["meshes"][0]["primitives"][0]
    mapping = np.array([0, 1, 2, 0])
    def append(ai, values):
        index = len(candidate.arrays)
        candidate.arrays.append(values)
        candidate.doc["accessors"].append({"count": len(values), "type": "fixture", "normalized": False})
        return index
    for key, ai in attrs.items():
        primitive["attributes"][key] = append(ai, source.array(ai)[mapping])
    for key, ai in target.items():
        primitive["targets"][0][key] = append(ai, source.array(ai)[mapping])
    primitive["indices"] = append(ii, np.array([0, 1, 2, 3, 2, 1], dtype=np.uint32).reshape(-1, 1))
    return source, candidate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--repair-candidate", type=Path)
    parser.add_argument("--seam-candidate", type=Path)
    args = parser.parse_args()
    if not args.report.is_absolute() or args.report.exists() or args.report.is_symlink():
        parser.error("--report must be fresh and absolute")
    if bool(args.source) != bool(args.repair_candidate) or (args.seam_candidate and not args.source):
        parser.error("actual audit requires --source and --repair-candidate")
    spec = importlib.util.spec_from_file_location("deformation_subject", REPAIR)
    subject = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(subject)
    checks, actual = [], {}
    def check(name, fn):
        try:
            detail = fn()
            checks.append({"name": name, "passed": True, "detail": detail})
        except Exception as exc:
            checks.append({"name": name, "passed": False, "error": str(exc), "traceback": traceback.format_exc()})
    def rejects(fn):
        try:
            fn()
        except (AssertionError, ValueError):
            return
        raise AssertionError("expected explicit refusal")
    triangle = np.array([[0, 1, 2]], dtype=np.uint32)
    rest = np.array([[0, 0, 0], [0, 0, 0], [1, 0, 0]], dtype=np.float32)
    base = {"POSITION": rest, "JOINTS_0": np.zeros((3, 4), dtype=np.uint8),
            "WEIGHTS_0": np.tile([1, 0, 0, 0], (3, 1)).astype(np.float32),
            "COLOR_0": np.tile([1, 1, 1, 0], (3, 1)).astype(np.float32)}
    transforms = np.repeat(np.eye(4)[None], 3, axis=0)
    transforms[1, 1, 3] = 2
    transforms[2, 2, 3] = 3
    def retained(attrs, targets=(), morph_weights=(), offset=(0, 0, 0), opens=True):
        posed = evaluate(attrs, targets, morph_weights, transforms, offset)
        if opens:
            require(double_area(posed) > 0.01, "independent counterexample did not open")
        require(not bool(subject.coincident_proof(triangle, attrs, targets, "yuga-secondary-v1")[0][0]), "visible/potentially driven face incorrectly removable")
        require(len(independent_selection(attrs, targets, triangle)[0]) == 1, "independent selection disagrees")
        return {"doubleArea": double_area(posed)}
    attrs = copy.deepcopy(base); attrs["JOINTS_0"][1, 0] = 1
    check("bind coincidence opens under different first skin joint", lambda: retained(attrs))
    attrs_weight = copy.deepcopy(base); attrs_weight["JOINTS_0"][:] = [0, 1, 0, 0]; attrs_weight["WEIGHTS_0"][1] = [.5, .5, 0, 0]
    check("same joint IDs but different blend amounts open face", lambda: retained(attrs_weight))
    attrs_extra = copy.deepcopy(base); attrs_extra["WEIGHTS_0"][:] = [0, 0, 0, 0]
    attrs_extra["JOINTS_1"] = np.zeros((3, 4), dtype=np.uint8); attrs_extra["JOINTS_1"][1, 0] = 2
    attrs_extra["WEIGHTS_1"] = np.tile([1, 0, 0, 0], (3, 1)).astype(np.float32)
    check("second skin set is a position driver", lambda: retained(attrs_extra))
    attrs_extra_weight = copy.deepcopy(attrs_extra)
    attrs_extra_weight["JOINTS_1"][:] = [0, 2, 0, 0]
    attrs_extra_weight["WEIGHTS_1"][1] = [.5, .5, 0, 0]
    check("second skin-set blend weights are a position driver", lambda: retained(attrs_extra_weight))
    for index in range(3):
        targets = [{"POSITION": np.zeros_like(rest)} for _ in range(3)]
        targets[index]["POSITION"][1, 1] = 2
        check("position morph target %d opens face" % index,
              lambda targets=targets: retained(base, targets, [.7, .8, .9]))
    attrs_color = copy.deepcopy(base); attrs_color["COLOR_0"][1, 3] = .5
    check("post-skin alpha-squared secondary warp opens face", lambda: retained(attrs_color, offset=(0, 4, 0)))
    attrs_rgb = copy.deepcopy(base); attrs_rgb["COLOR_0"][1, 0] = .5
    check("full COLOR RGB remains conservatively significant", lambda: retained(attrs_rgb, opens=False))
    attrs_color1 = copy.deepcopy(base); attrs_color1["COLOR_1"] = attrs_rgb["COLOR_0"]
    check("additional full COLOR set remains conservatively significant", lambda: retained(attrs_color1, opens=False))
    collinear = copy.deepcopy(base); collinear["POSITION"] = np.array([[0, 0, 0], [1, 0, 0], [2, 0, 0]], dtype=np.float32)
    collinear["COLOR_0"][1, 3] = 1
    check("three distinct collinear positions may open under the exact warp", lambda: retained(collinear, offset=(0, 1, 0)))
    near = copy.deepcopy(base); near["POSITION"][1, 1] = 1e-30
    check("nonzero tiny geometry never becomes equal-pair proof", lambda: retained(near, opens=False))
    uv = {**copy.deepcopy(base), "POSITION": np.array([[0, 0, 0], [0, 1, 0], [1, 0, 0]], dtype=np.float32), "TEXCOORD_0": np.zeros((3, 2), dtype=np.float32)}
    check("UV-degenerate face with real geometry remains", lambda: retained(uv))
    for semantic, width in (("NORMAL", 3), ("TANGENT", 4), ("TEXCOORD_0", 2), ("_UNKNOWN_DISPLACE", 1)):
        attrs_seam = copy.deepcopy(base); attrs_seam[semantic] = np.zeros((3, width), dtype=np.float32); attrs_seam[semantic][1, 0] = 1
        check("strict policy keeps unequal " + semantic,
              lambda attrs_seam=attrs_seam: require(not subject.coincident_proof(triangle, attrs_seam, [], "strict")[0][0], "strict omitted a channel"))
    def safe_pair():
        rng = np.random.default_rng(7321)
        attrs = copy.deepcopy(base)
        attrs["JOINTS_0"][:] = [0, 1, 2, 0]
        attrs["WEIGHTS_0"][:] = [.2, .3, .5, 0]
        attrs["COLOR_0"][:] = [1, .4, .2, .7]
        attrs["NORMAL"] = np.array([[1, 0, 0], [0, 1, 0], [0, 0, 1]], dtype=np.float32)
        attrs["TEXCOORD_0"] = rng.normal(size=(3, 2)).astype(np.float32)
        target = {"POSITION": np.array([[.2, -.3, .7], [.2, -.3, .7], [0, 0, 0]], dtype=np.float32), "NORMAL": rng.normal(size=(3, 3)).astype(np.float32)}
        require(subject.coincident_proof(triangle, attrs, [target], "yuga-secondary-v1")[0][0], "bounded proof rejected identical drivers")
        require(not subject.coincident_proof(triangle, attrs, [target], "strict")[0][0], "strict ignored shading seam")
        for _ in range(64):
            matrices = rng.normal(size=(3, 4, 4)); matrices[:, 3] = [0, 0, 0, 1]
            posed = evaluate(attrs, [target], [rng.normal()], matrices, rng.normal(size=3))
            require(np.array_equal(posed[0], posed[1]), "equal drivers diverged")
        return {"randomAffinePoses": 64, "seed": 7321, "claim": "finite sampled corroboration of identical-driver invariant"}
    check("identical complete drivers stay coincident under 64 mixed poses", safe_pair)
    check("unknown deformation policy rejects", lambda: rejects(lambda: subject.coincident_proof(triangle, base, [], "unknown")))
    check("exact source and shader policy constants match", lambda: require(subject.YUGA_SOURCE == SOURCE_SHA and subject.YUGA_SHADER == SHADER_SHA and sha(SHADER) == SHADER_SHA, "policy pins mismatch"))
    def public_gate():
        # A complete small indexed fixture, not an approved de61 input. The
        # custom channel must never enter the source-bound reduced signature.
        with tempfile.TemporaryDirectory(prefix="deformation-source-gate-") as directory:
            folder = Path(directory)
            payload = rest.tobytes() + triangle.astype("<u4").tobytes() + np.zeros((3, 1), dtype="<f4").tobytes()
            doc = {"asset": {"version": "2.0"}, "buffers": [{"byteLength": len(payload)}],
                   "bufferViews": [{"buffer": 0, "byteOffset": 0, "byteLength": 36},
                                   {"buffer": 0, "byteOffset": 36, "byteLength": 12},
                                   {"buffer": 0, "byteOffset": 48, "byteLength": 12}],
                   "accessors": [{"bufferView": 0, "componentType": 5126, "type": "VEC3", "count": 3},
                                 {"bufferView": 1, "componentType": 5125, "type": "SCALAR", "count": 3},
                                 {"bufferView": 2, "componentType": 5126, "type": "SCALAR", "count": 3}],
                   "meshes": [{"primitives": [{"attributes": {"POSITION": 0, "_UNKNOWN_DISPLACE": 2}, "indices": 1}]}]}
            js = json.dumps(doc).encode(); js += b" " * (-len(js) % 4)
            source = folder / "unknown.glb"
            source.write_bytes(struct.pack("<4sII", b"glTF", 2, 28 + len(js) + len(payload)) +
                               struct.pack("<II", len(js), 0x4E4F534A) + js +
                               struct.pack("<II", len(payload), 0x004E4942) + payload)
            try:
                subject.repair(source, folder / "candidate.glb", folder / "report.json", "yuga-secondary-v1")
            except ValueError as exc:
                require("exact pinned source and shader" in str(exc), "wrong rejection reason")
            else:
                raise AssertionError("unapproved source reached reduced proof")
            require(not (folder / "candidate.glb").exists() and not (folder / "report.json").exists(), "source refusal wrote output")
    check("public source-bound policy refuses unknown shader-driving input", public_gate)
    synthetic_source, synthetic_seam = decoded_seam_fixture()
    check("synthetic decoded seam preserves all three cloned morph semantics",
          lambda: require(verify_seams(synthetic_source, synthetic_seam)["clonedMorphChannels"] == 3, "fixture clone channels"))
    for semantic in ("POSITION", "NORMAL", "TANGENT"):
        def bad_morph(semantic=semantic):
            corrupted = copy.deepcopy(synthetic_seam)
            ai = corrupted.doc["meshes"][0]["primitives"][0]["targets"][0][semantic]
            corrupted.arrays[ai][3, 0] += 1
            rejects(lambda: verify_seams(synthetic_source, corrupted))
        check("independent decoded verifier rejects cloned " + semantic + " morph corruption", bad_morph)
    def bad_interpretation():
        corrupted = copy.deepcopy(synthetic_seam)
        ai = corrupted.doc["meshes"][0]["primitives"][0]["attributes"]["WEIGHTS_0"]
        corrupted.doc["accessors"][ai]["normalized"] = True
        rejects(lambda: verify_seams(synthetic_source, corrupted))
    check("same bytes with changed accessor normalization are rejected", bad_interpretation)
    if args.source:
        source, repaired = IndependentGLB(args.source), IndependentGLB(args.repair_candidate)
        actual = {"source": str(args.source.resolve()), "sourceSha256": sha(args.source),
                  "repairCandidate": str(args.repair_candidate.resolve()), "repairCandidateSha256": sha(args.repair_candidate),
                  "embeddedAnimationCount": len(source.doc.get("animations", [])),
                  "skinJointCounts": [len(s["joints"]) for s in source.doc.get("skins", [])],
                  "imageCount": len(source.doc.get("images", [])), "runtimeMotionStateCountClaim": "not inferred from this GLB"}
        check("actual source is exact reviewed de61", lambda: require(actual["sourceSha256"] == SOURCE_SHA, "wrong source"))
        check("actual nine embedded animations and one164-joint skin", lambda: require(actual["embeddedAnimationCount"] == 9 and actual["skinJointCounts"] == [164], "actual rig/embedded clip count"))
        def actual_repair():
            actual["repair"] = verify_repair(source, repaired)
            return actual["repair"]
        check("actual repair independent face selection and all-channel conservation", actual_repair)
        changed = copy.copy(repaired); changed.doc = copy.deepcopy(repaired.doc); changed.doc["nodes"][0]["name"] = "corrupt-independent-fixture"
        check("independent conservation rejects altered rig node", lambda: rejects(lambda: verify_repair(source, changed)))
        changed_animation = copy.copy(repaired); changed_animation.doc = copy.deepcopy(repaired.doc)
        changed_animation.doc["animations"][0]["samplers"][0]["interpolation"] = "CORRUPT"
        check("independent conservation rejects altered embedded animation contract", lambda: rejects(lambda: verify_repair(source, changed_animation)))
        changed_image = copy.copy(repaired); buf = bytearray(repaired.binary); vi = source.doc["images"][0]["bufferView"]; off = source.doc["bufferViews"][vi].get("byteOffset", 0); buf[off] ^= 1; changed_image.binary = bytes(buf)
        check("independent conservation rejects changed image byte", lambda: rejects(lambda: verify_repair(source, changed_image)))
        if args.seam_candidate:
            seam = IndependentGLB(args.seam_candidate)
            actual.update(seamCandidate=str(args.seam_candidate.resolve()), seamCandidateSha256=sha(args.seam_candidate))
            def actual_seam():
                actual["seam"] = verify_seams(repaired, seam)
                return actual["seam"]
            check("actual seam independent ordered-corner and all-row conservation", actual_seam)
            corrupt = copy.copy(seam); corrupt.doc = copy.deepcopy(seam.doc)
            for mi, pi, sp in repaired.primitives():
                cp = seam.doc["meshes"][mi]["primitives"][pi]
                if cp["attributes"]["POSITION"] != sp["attributes"]["POSITION"]:
                    ai = cp["attributes"]["POSITION"]
                    view = corrupt.doc["bufferViews"][corrupt.doc["accessors"][ai]["bufferView"]]
                    buf = bytearray(corrupt.binary); buf[view.get("byteOffset", 0)] ^= 1; corrupt.binary = bytes(buf)
                    break
            check("independent seam verifier rejects appended position corruption", lambda: rejects(lambda: verify_seams(repaired, corrupt)))
            def appended_corruption(kind, semantic):
                altered = copy.copy(seam)
                for mi, pi, sp in repaired.primitives():
                    cp = seam.doc["meshes"][mi]["primitives"][pi]
                    n = len(repaired.array(sp["attributes"]["POSITION"]))
                    if len(seam.array(cp["attributes"]["POSITION"])) <= n:
                        continue
                    if kind == "attribute" and semantic in cp["attributes"]:
                        ai = cp["attributes"][semantic]
                    elif kind == "morph" and cp.get("targets") and semantic in cp["targets"][0]:
                        ai = cp["targets"][0][semantic]
                    else:
                        continue
                    spec = seam.doc["accessors"][ai]
                    view = seam.doc["bufferViews"][spec["bufferView"]]
                    off = view.get("byteOffset", 0) + spec.get("byteOffset", 0) + n * DT[spec["componentType"]].itemsize * WIDTH[spec["type"]]
                    buf = bytearray(seam.binary); buf[off] ^= 1; altered.binary = bytes(buf)
                    rejects(lambda: verify_seams(repaired, altered))
                    return
                raise AssertionError("required cloned channel not found for counterexample")
            check("independent seam verifier rejects appended cloned weights corruption", lambda: appended_corruption("attribute", "WEIGHTS_0"))
            check("independent seam verifier rejects appended cloned original tangent corruption", lambda: appended_corruption("attribute", "TANGENT"))
            check("actual seam accurately reports no clones in morph-bearing domains",
                  lambda: require(actual["seam"]["clonedMorphChannels"] == 0, "actual morph clone coverage changed; review fixture expectation"))
        check("actual source and candidates remain unchanged on disk", lambda: require(sha(args.source) == actual["sourceSha256"] and sha(args.repair_candidate) == actual["repairCandidateSha256"] and (not args.seam_candidate or sha(args.seam_candidate) == actual["seamCandidateSha256"]), "input changed"))
    result = {"schema": 1, "kind": "independent-deformation-and-lineage-proof", "passed": all(c["passed"] for c in checks),
              "count": len(checks), "checks": checks, "actual": actual,
              "sourcePins": {str(p.relative_to(ROOT)): sha(p) for p in (Path(__file__), REPAIR, SPLIT, SHADER)},
              "limits": ["Analytical CPU data tests, not a Godot/Blender import, frame render or animation playthrough.",
                         "64 sampled affine poses corroborate the pair invariant; the invariant depends on identical complete driving channels and the exact pinned shader/core glTF contract.",
                         "No generic safety for vertex-ID-dependent/custom displacement, unknown external deformation or different source/shader.",
                         "Nine embedded GLB animations are distinct from the separate runtime motion library; no runtime state/clip count is inferred here.",
                         "Conservation does not repair remaining UV/tangent defects, optimize file size or establish commercial art/GPU/netplay acceptance."]}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    with args.report.open("x") as stream:
        stream.write(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"passed": result["passed"], "count": result["count"], "failed": [c["name"] for c in checks if not c["passed"]], "report": str(args.report)}, indent=2))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
