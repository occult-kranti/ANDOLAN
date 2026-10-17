#!/usr/bin/env python3
"""Offline repair counterexamples, including independent deformation oracles."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest
import numpy as np

NATIVE = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("rama_mesh_repair", NATIVE / "art/hero-rama-repair/repair_mesh.py")
repair = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(repair)


class Fixture:
    def __init__(self):
        self.binary = bytearray()
        self.doc = {"asset": {"version": "2.0", "generator": "mesh-repair-counterexamples"}, "buffers": [{"byteLength": 0}], "bufferViews": [], "accessors": [], "materials": [{"name": "red"}, {"name": "blue"}], "nodes": [{"name": "hero", "mesh": 0, "skin": 0}, {"name": "joint"}], "skins": [{"joints": [1]}], "scenes": [{"nodes": [0]}], "scene": 0, "meshes": []}

    def view(self, payload, **extra):
        self.binary += b"\0" * (-len(self.binary) % 4)
        i = len(self.doc["bufferViews"])
        self.doc["bufferViews"].append({"buffer": 0, "byteOffset": len(self.binary), "byteLength": len(payload), **extra})
        self.binary.extend(payload)
        return i

    def array(self, values, ct=5126, shape="VEC3", **extra):
        a = np.array(values, dtype=repair.reader.DTYPES[ct]).reshape(-1, repair.reader.WIDTHS[shape])
        i = len(self.doc["accessors"])
        self.doc["accessors"].append({"bufferView": self.view(a.tobytes()), "componentType": ct, "type": shape, "count": len(a), **extra})
        return i

    def mesh(self, positions=None, faces=None, ct=5123, attr_changes=None, morph_changes=None):
        # face0 real; face1 repeated; face2 identical-record pair 0/3;
        # face3 collinear distinct positions; face4 tiny real geometry.
        positions = positions if positions is not None else [[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 0], [2, 0, 0], [1, 1e-16, 0]]
        n = len(positions)
        attrs = {"POSITION": (positions, 5126, "VEC3"), "NORMAL": ([[0, 0, 1]] * n, 5126, "VEC3"), "TANGENT": ([[1, 0, 0, 1]] * n, 5126, "VEC4"), "TEXCOORD_0": ([[0, 0]] * n, 5126, "VEC2"), "COLOR_0": ([[1, 1, 1, 0]] * n, 5126, "VEC4"), "JOINTS_0": ([[0, 0, 0, 0]] * n, 5121, "VEC4"), "WEIGHTS_0": ([[1, 0, 0, 0]] * n, 5126, "VEC4")}
        attrs.update(attr_changes or {})
        attributes = {k: self.array(v[0], v[1], v[2]) for k, v in attrs.items()}
        targets = {"POSITION": [[0, 0, 0]] * n, "NORMAL": [[0, 0, 0]] * n, "TANGENT": [[0, 0, 0]] * n}
        targets.update(morph_changes or {})
        p = {"attributes": attributes, "indices": self.array(faces if faces is not None else [0, 1, 2, 0, 0, 1, 0, 3, 2, 0, 1, 4, 0, 1, 5], ct, "SCALAR", min=[0], max=[n - 1], extras={"authored": "retained"}), "material": 0, "targets": [{k: self.array(v) for k, v in targets.items()}]}
        self.doc["meshes"].append({"name": "fixture", "weights": [0.3], "primitives": [p]})
        return p

    def write(self, path):
        self.doc["buffers"][0]["byteLength"] = len(self.binary)
        binary = self.binary + b"\0" * (-len(self.binary) % 4)
        js = json.dumps(self.doc, separators=(",", ":")).encode()
        js += b" " * (-len(js) % 4)
        path.write_bytes(struct.pack("<4sII", b"glTF", 2, 28 + len(js) + len(binary)) + struct.pack("<II", len(js), 0x4E4F534A) + js + struct.pack("<II", len(binary), 0x004E4942) + binary)
        return path


class RepairCases(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="yuga-mesh-repair-")
        self.root = Path(self.temp.name)
        self.source = self.root / "source.glb"
        self.candidate = self.root / "candidate.glb"
        self.report = self.root / "report.json"

    def tearDown(self):
        self.temp.cleanup()

    def run_fixture(self, f):
        f.write(self.source)
        return repair.repair(self.source, self.candidate, self.report)

    def inspect_fixture(self, f, policy="strict"):
        f.write(self.source)
        return repair.inspect(repair.read_checked(self.source), policy)[0][0]

    def rejected(self, f):
        f.write(self.source)
        with self.assertRaises((ValueError, KeyError, IndexError, TypeError)):
            repair.repair(self.source, self.candidate, self.report)
        self.assertFalse(self.candidate.exists())
        self.assertFalse(self.report.exists())

    def test_exact_proof_keeps_collinear_and_tiny_positive_faces(self):
        f = Fixture(); f.mesh()
        r = self.run_fixture(f)
        self.assertEqual(r["removedPairProven"], 2)
        self.assertEqual(r["trianglesBefore"], 5)
        self.assertEqual(r["trianglesAfter"], 3)
        self.assertEqual(r["domains"][0]["removedFaceOrdinals"], [1, 2])
        self.assertEqual(r["domains"][0]["geometryDiagnostic"]["positiveNearZeroRetainedUnlessPairProven"], 1)
        candidate = repair.read_checked(self.candidate)
        self.assertEqual(candidate.array(candidate.doc["meshes"][0]["primitives"][0]["indices"]).reshape(-1).tolist(), [0, 1, 2, 0, 1, 4, 0, 1, 5])

    def test_all_non_index_bytes_metadata_skin_morph_animation_images_exact(self):
        f = Fixture(); f.mesh()
        ibm = f.array(np.eye(4).reshape(1, 16), 5126, "MAT4")
        f.doc["skins"][0]["inverseBindMatrices"] = ibm
        f.doc["animations"] = [{"name": "bow", "samplers": [{"input": f.array([0, 1], 5126, "SCALAR"), "output": f.array([[0, 0, 0], [1, 2, 3]])}], "channels": [{"sampler": 0, "target": {"node": 1, "path": "translation"}}]}]
        f.doc["images"] = [{"bufferView": f.view(b"opaque-image-payload"), "mimeType": "image/png", "name": "retained"}]
        r = self.run_fixture(f)
        s, c = repair.read_checked(self.source), repair.read_checked(self.candidate)
        self.assertTrue(all(r["preservation"].values()))
        self.assertEqual(c.binary[:len(s.binary)], s.binary)
        self.assertEqual(c.doc["skins"], s.doc["skins"])
        self.assertEqual(c.doc["animations"], s.doc["animations"])
        self.assertEqual(c.doc["images"], s.doc["images"])
        self.assertEqual(c.doc["accessors"][:len(s.doc["accessors"])], s.doc["accessors"])
        self.assertEqual(c.doc["bufferViews"][:len(s.doc["bufferViews"])], s.doc["bufferViews"])
        self.assertEqual(s.raw, self.source.read_bytes())

    def test_unsigned_index_types_and_minmax(self):
        for ct in (5121, 5123, 5125):
            with self.subTest(component=ct):
                f = Fixture(); p = f.mesh(faces=[0, 1, 2, 5, 5, 5], ct=ct)
                f.write(self.source)
                g = repair.read_checked(self.source)
                _, selection = repair.inspect(g, "strict")
                raw = repair.encode_candidate(g, selection)
                path = self.root / f"type-{ct}.glb"; path.write_bytes(raw)
                c = repair.read_checked(path)
                a = c.doc["accessors"][c.doc["meshes"][0]["primitives"][0]["indices"]]
                self.assertEqual(a["componentType"], ct)
                self.assertEqual((a["count"], a["min"], a["max"]), (3, [0], [2]))
                self.assertEqual(a["extras"], {"authored": "retained"})

    def test_shared_index_accessor_material_boundaries_are_preserved(self):
        f = Fixture(); p = f.mesh()
        other = copy.deepcopy(p); other["material"] = 1
        # Different deformation on source vertex3: only repeated face removable.
        pos = [[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1], [2, 0, 0], [1, 1e-16, 0]]
        other["attributes"]["POSITION"] = f.array(pos)
        f.doc["meshes"][0]["primitives"].append(other)
        old_index = p["indices"]
        r = self.run_fixture(f)
        c = repair.read_checked(self.candidate)
        ps = c.doc["meshes"][0]["primitives"]
        self.assertEqual([d["removedPairProven"] for d in r["domains"]], [2, 1])
        self.assertEqual([p["material"] for p in ps], [0, 1])
        self.assertNotEqual(ps[0]["indices"], ps[1]["indices"])
        self.assertEqual(c.doc["accessors"][old_index], f.doc["accessors"][old_index])

    def test_joint_weight_color_morph_and_seam_counterexamples(self):
        cases = [("JOINTS_0", [1, 0, 0, 0], 5121, "VEC4"), ("WEIGHTS_0", [.5, .5, 0, 0], 5126, "VEC4"), ("COLOR_0", [1, 1, 1, .5], 5126, "VEC4"), ("NORMAL", [0, 1, 0], 5126, "VEC3"), ("TANGENT", [0, 1, 0, 1], 5126, "VEC4"), ("TEXCOORD_0", [1, 0], 5126, "VEC2")]
        for semantic, value, ct, shape in cases:
            with self.subTest(semantic=semantic):
                f = Fixture(); p = f.mesh()
                base = repair.reader.GLB(f.write(self.source)).array(p["attributes"][semantic]).tolist()
                base[3] = value
                p["attributes"][semantic] = f.array(base, ct, shape)
                strict = self.inspect_fixture(f)
                bounded = self.inspect_fixture(f, "yuga-secondary-v1")
                self.assertEqual(strict["removedPairProven"], 1)
                self.assertEqual(bounded["removedPairProven"], 1 if semantic.startswith(("JOINTS", "WEIGHTS", "COLOR")) else 2)
        for semantic in ("POSITION", "NORMAL", "TANGENT"):
            with self.subTest(morph=semantic):
                values = [[0, 0, 0] for _ in range(6)]; values[3] = [0, 0, 1]
                f = Fixture(); f.mesh(morph_changes={semantic: values})
                self.assertEqual(self.inspect_fixture(f)["removedPairProven"], 1)
                self.assertEqual(self.inspect_fixture(f, "yuga-secondary-v1")["removedPairProven"], 1 if semantic == "POSITION" else 2)

    def test_additional_skin_and_color_sets_not_ignored(self):
        f = Fixture(); p = f.mesh()
        p["attributes"]["JOINTS_1"] = f.array([[0, 0, 0, 0]] * 6, 5121, "VEC4")
        weights = [[0, 0, 0, 0] for _ in range(6)]; weights[3] = [1, 0, 0, 0]
        p["attributes"]["WEIGHTS_1"] = f.array(weights, 5126, "VEC4")
        self.assertEqual(self.inspect_fixture(f, "yuga-secondary-v1")["removedPairProven"], 1)
        p["attributes"]["WEIGHTS_1"] = f.array([[0, 0, 0, 0]] * 6, 5126, "VEC4")
        colors = [[1, 1, 1, 0] for _ in range(6)]; colors[3] = [1, 1, 1, 1]
        p["attributes"]["COLOR_1"] = f.array(colors, 5126, "VEC4")
        self.assertEqual(self.inspect_fixture(f, "yuga-secondary-v1")["removedPairProven"], 1)
        p["attributes"].pop("WEIGHTS_1")
        self.rejected(f)

    def test_normalized_integer_weights_preserved(self):
        f = Fixture(); p = f.mesh()
        p["attributes"]["WEIGHTS_0"] = f.array([[255, 0, 0, 0]] * 6, 5121, "VEC4", normalized=True)
        r = self.run_fixture(f)
        self.assertEqual(r["removedPairProven"], 2)
        self.assertTrue(r["preservation"]["oldBinaryPrefixExact"])

    def test_sparse_position_morph_prevents_removal(self):
        f = Fixture(); p = f.mesh()
        si = f.view(bytes([3])); sv = f.view(np.array([[0, 0, 1]], dtype="<f4").tobytes())
        ai = len(f.doc["accessors"])
        f.doc["accessors"].append({"componentType": 5126, "type": "VEC3", "count": 6, "sparse": {"count": 1, "indices": {"bufferView": si, "componentType": 5121}, "values": {"bufferView": sv}}})
        p["targets"][0]["POSITION"] = ai
        r = self.run_fixture(f)
        self.assertEqual(r["removedPairProven"], 1)
        self.assertTrue(r["preservation"]["allOldAccessorsAndViewsExact"])

    def test_interleaved_position_storage_exact(self):
        f = Fixture(); p = f.mesh()
        pos = repair.reader.GLB(f.write(self.source)).array(p["attributes"]["POSITION"])
        packed = np.column_stack([pos, np.arange(len(pos), dtype="<f4")]).astype("<f4")
        a = f.doc["accessors"][p["attributes"]["POSITION"]]
        a["bufferView"] = f.view(packed.tobytes(), byteStride=16)
        self.assertEqual(self.run_fixture(f)["removedPairProven"], 2)

    def test_scale_invariance_does_not_delete_skinny_real_faces(self):
        for scale in (1e-20, 1, 1e20):
            with self.subTest(scale=scale):
                f = Fixture(); f.mesh(positions=(np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 0], [2, 0, 0], [1, 1e-16, 0]]) * scale).tolist())
                d = self.inspect_fixture(f)
                self.assertEqual(d["removedFaceOrdinals"], [1, 2])
                self.assertEqual(d["geometryDiagnostic"]["positiveNearZeroRetainedUnlessPairProven"], 1)

    def test_uv_zero_area_is_report_only(self):
        f = Fixture(); f.mesh(faces=[0, 1, 2])
        r = self.run_fixture(f)
        self.assertEqual(r["removedPairProven"], 0)
        self.assertEqual(r["domains"][0]["uvDiagnostic"]["TEXCOORD_0"]["float64ExactlyZero"], 1)
        self.assertTrue(r["noOpExactCopy"])
        self.assertEqual(self.source.read_bytes(), self.candidate.read_bytes())

    def test_idempotent_candidate_second_pass_exact_copy(self):
        f = Fixture(); f.mesh(); first = self.run_fixture(f)
        second_path, second_report = self.root / "second.glb", self.root / "second.json"
        second = repair.repair(self.candidate, second_path, second_report)
        self.assertEqual(first["removedPairProven"], 2)
        self.assertEqual(second["removedPairProven"], 0)
        self.assertTrue(second["noOpExactCopy"])

    def test_all_degenerate_primitive_blocks_entire_candidate(self):
        f = Fixture(); f.mesh(faces=[0, 0, 1, 0, 3, 2])
        r = self.run_fixture(f)
        self.assertTrue(r["blockedEmptyPrimitive"])
        self.assertFalse(r["candidateWritten"])
        self.assertFalse(self.candidate.exists())
        self.assertTrue(self.report.exists())

    def test_independent_morph_and_skin_visibility_oracles(self):
        # A bind-pose coincidence becomes nonzero area when only one endpoint
        # has a position morph or a different translated skin joint.
        rest = np.array([[0., 0, 0], [0, 0, 0], [1, 0, 0]])
        morph = np.array([[0., 0, 0], [0, 1, 0], [0, 0, 0]])
        deformed = rest + morph * .7
        self.assertGreater(np.linalg.norm(np.cross(deformed[1] - deformed[0], deformed[2] - deformed[0])), .6)
        joints = np.array([[0, 0, 0, 0], [1, 0, 0, 0], [0, 0, 0, 0]], dtype=np.uint8)
        mats = np.repeat(np.eye(4)[None], 2, axis=0); mats[1, 1, 3] = 2
        posed = np.array([(mats[joints[i, 0]] @ np.append(p, 1))[:3] for i, p in enumerate(rest)])
        self.assertEqual(np.linalg.norm(np.cross(posed[1] - posed[0], posed[2] - posed[0])), 2)
        idx = np.array([[0, 1, 2]])
        attrs = {"POSITION": rest, "JOINTS_0": joints, "WEIGHTS_0": np.array([[1., 0, 0, 0]] * 3)}
        self.assertFalse(repair.coincident_proof(idx, attrs, [], "yuga-secondary-v1")[0][0])
        self.assertFalse(repair.coincident_proof(idx, {"POSITION": rest}, [{"POSITION": morph}], "yuga-secondary-v1")[0][0])

    def test_independent_secondary_mask_visibility_oracle(self):
        rest = np.array([[0., 0, 0], [0, 0, 0], [1, 0, 0]])
        colors = np.array([[1., 1, 1, 0], [1, 1, 1, 1], [1, 1, 1, 0]])
        # Independently execute the inspected vertex shader's clamp(alpha)^2.
        deformed = rest + np.clip(colors[:, 3:4], 0, 1) ** 2 * np.array([0, 2, 0])
        self.assertEqual(np.linalg.norm(np.cross(deformed[1] - deformed[0], deformed[2] - deformed[0])), 2)
        idx = np.array([[0, 1, 2]])
        self.assertFalse(repair.coincident_proof(idx, {"POSITION": rest, "COLOR_0": colors}, [], "yuga-secondary-v1")[0][0])
        self.assertTrue(repair.coincident_proof(idx, {"POSITION": rest}, [], "yuga-secondary-v1")[0][0])

    def test_experimental_policy_cannot_run_on_unpinned_fixture(self):
        f = Fixture(); f.mesh(); f.write(self.source)
        with self.assertRaisesRegex(ValueError, "exact pinned source"):
            repair.repair(self.source, self.candidate, self.report, "yuga-secondary-v1")
        self.assertFalse(self.candidate.exists())

    def test_existing_alias_symlink_and_runtime_outputs_refused(self):
        f = Fixture(); f.mesh(); f.write(self.source)
        self.candidate.write_bytes(b"keep")
        with self.assertRaises(ValueError): repair.repair(self.source, self.candidate, self.report)
        self.assertEqual(self.candidate.read_bytes(), b"keep")
        self.candidate.unlink(); self.candidate.symlink_to(self.source)
        with self.assertRaises(ValueError): repair.repair(self.source, self.candidate, self.report)
        self.candidate.unlink()
        with self.assertRaises(ValueError): repair.repair(self.source, self.source, self.report)
        with self.assertRaises(ValueError): repair.repair(self.source, self.candidate, self.candidate)
        with self.assertRaises(ValueError): repair.repair(self.source, NATIVE / "must-not-create.glb", self.report)

    def test_hardlink_and_existing_report_refused(self):
        f = Fixture(); f.mesh(); f.write(self.source)
        self.candidate.hardlink_to(self.source)
        with self.assertRaises(ValueError): repair.repair(self.source, self.candidate, self.report)
        self.candidate.unlink(); self.report.write_text("keep")
        with self.assertRaises(ValueError): repair.repair(self.source, self.candidate, self.report)
        self.assertEqual(self.report.read_text(), "keep")

    def test_corrupt_header_truncation_and_chunk_lengths(self):
        f = Fixture(); f.mesh(); good = f.write(self.source).read_bytes()
        variants = [good[:10], b"xxxx" + good[4:], good[:-1], good[:12] + struct.pack("<I", 0xfffffff0) + good[16:], good[:16] + b"BAD!" + good[20:]]
        for raw in variants:
            with self.subTest(bytes=len(raw)):
                self.source.write_bytes(raw)
                with self.assertRaises((ValueError, struct.error)): repair.repair(self.source, self.candidate, self.report)
                self.assertFalse(self.candidate.exists())

    def test_duplicate_json_keys_and_nonfinite_metadata_refused(self):
        f = Fixture(); f.mesh(); raw = f.write(self.source).read_bytes()
        jlen = struct.unpack_from("<I", raw, 12)[0]
        original = raw[20:20 + jlen].rstrip()
        for replacement in (b'{"asset":{},' + original[1:], original[:-1] + b',"bad":NaN}'):
            js = replacement + b" " * (-len(replacement) % 4)
            rest = raw[20 + jlen:]
            self.source.write_bytes(struct.pack("<4sII", b"glTF", 2, 20 + len(js) + len(rest)) + struct.pack("<II", len(js), 0x4E4F534A) + js + rest)
            with self.assertRaises(ValueError): repair.repair(self.source, self.candidate, self.report)
            self.assertFalse(self.candidate.exists())
            self.assertFalse(self.report.exists())

    def test_source_shader_contract_and_unknown_policy_fail_closed(self):
        f = Fixture(); f.mesh(); f.write(self.source)
        # Isolate the shader pin without relying on a 34MB test fixture. Only
        # the test's in-memory source-pin dependency is temporarily replaced.
        old_source, old_shader = repair.YUGA_SOURCE, repair.SHADER
        try:
            repair.YUGA_SOURCE = repair.digest(self.source.read_bytes())
            altered = self.root / "other-shader.gdshader"; altered.write_text("void vertex(){VERTEX.x+=UV.x;}")
            repair.SHADER = altered
            with self.assertRaisesRegex(ValueError, "exact pinned source and shader"):
                repair.repair(self.source, self.candidate, self.report, "yuga-secondary-v1")
        finally:
            repair.YUGA_SOURCE, repair.SHADER = old_source, old_shader
        with self.assertRaises(ValueError): repair.repair(self.source, self.candidate, self.report, "unknown")
        self.assertFalse(self.candidate.exists())

    def test_bad_accessor_count_bounds_type_and_nonfinite_data(self):
        mutations = [lambda f, p: f.doc["accessors"][p["attributes"]["POSITION"]].update(count=99_000_000), lambda f, p: f.doc["accessors"][p["attributes"]["POSITION"]].update(count=True), lambda f, p: f.doc["accessors"][p["indices"]].update(componentType=5122), lambda f, p: f.doc["accessors"][p["indices"]].update(count=14), lambda f, p: p.update(indices=99999), lambda f, p: p.update(mode=1), lambda f, p: p.pop("indices"), lambda f, p: f.doc["accessors"][p["attributes"]["POSITION"]].update(byteOffset=99999), lambda f, p: f.doc["buffers"][0].update(uri="outside.bin")]
        for mutate in mutations:
            with self.subTest(mutation=mutations.index(mutate)):
                f = Fixture(); p = f.mesh(); mutate(f, p); self.rejected(f)
        f = Fixture(); p = f.mesh(); p["attributes"]["POSITION"] = f.array([[float("nan"), 0, 0]] * 6)
        self.rejected(f)
        f = Fixture(); p = f.mesh(); p["indices"] = f.array([0, 1, 99], 5123, "SCALAR"); self.rejected(f)

    def test_unknown_extensions_external_images_sparse_corruption(self):
        for extension in ("KHR_draco_mesh_compression", "EXT_meshopt_compression", "CUSTOM_position_deformer"):
            with self.subTest(extension=extension):
                f = Fixture(); p = f.mesh(); p["extensions"] = {extension: {}}; self.rejected(f)
        f = Fixture(); f.mesh(); f.doc["images"] = [{"uri": "outside.png"}]; self.rejected(f)
        f = Fixture(); p = f.mesh()
        a = f.doc["accessors"][p["targets"][0]["POSITION"]]
        a.pop("bufferView")
        a["sparse"] = {"count": 2, "indices": {"bufferView": f.view(bytes([3, 3])), "componentType": 5121}, "values": {"bufferView": f.view(bytes(24))}}
        self.rejected(f)

    def test_preservation_verifier_rejects_non_index_metadata_and_binary_changes(self):
        f = Fixture(); f.mesh(); self.run_fixture(f)
        s, c = repair.read_checked(self.source), repair.read_checked(self.candidate)
        _, selection = repair.inspect(s, "strict")
        c.doc["materials"][0]["name"] = "changed"
        with self.assertRaisesRegex(ValueError, "Non-index"): repair.verify_preservation(s, c, selection)
        c = repair.read_checked(self.candidate); c.binary = b"X" + c.binary[1:]
        with self.assertRaisesRegex(ValueError, "binary"): repair.verify_preservation(s, c, selection)


if __name__ == "__main__":
    unittest.main(verbosity=2)
