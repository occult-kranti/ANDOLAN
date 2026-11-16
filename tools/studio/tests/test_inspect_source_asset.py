"""Lightweight geometry/preflight/failure tests; no Blender render required."""
import contextlib
import hashlib
import importlib.util
import io
import itertools
import json
from pathlib import Path
import struct
import tempfile
import unittest
import zlib
from unittest import mock

TOOL = Path(__file__).resolve().parents[1] / "inspect-source-asset.py"
spec = importlib.util.spec_from_file_location("source_asset_inspector", TOOL)
inspector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(inspector)


def fixture_glb(path, **updates):
    model = {"asset": {"version": "2.0"}, "meshes": [{"primitives": []}], "nodes": []}
    model.update(updates)
    payload = json.dumps(model).encode()
    payload += b" " * ((-len(payload)) % 4)
    path.write_bytes(struct.pack("<4sII", b"glTF", 2, 20 + len(payload)) + struct.pack("<II", len(payload), 0x4E4F534A) + payload)
    return path


class GeometryTests(unittest.TestCase):
    def test_all_eight_corners_survive_mirror_nonuniform_scale_and_translation(self):
        corners = list(itertools.product((-1, 1), (-2, 2), (-3, 3)))
        matrix = [[0, -3, 0, 10], [-2, 0, 0, -5], [0, 0, .5, 7], [0, 0, 0, 1]]
        transformed = inspector.transformed_corners(corners, matrix)
        result = inspector.bounds(transformed)
        self.assertEqual(len(set(transformed)), 8)
        self.assertEqual(result["min"], [4, -7, 5.5])
        self.assertEqual(result["max"], [16, -3, 8.5])
        self.assertEqual(result["size"], [12, 4, 3])

    def test_rotated_box_cannot_use_only_min_and_max_corner(self):
        corners = list(itertools.product((-1, 1), repeat=3))
        matrix = [[1, -1, 0, 0], [1, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]
        result = inspector.bounds(inspector.transformed_corners(corners, matrix))
        self.assertEqual(result["size"], [4, 4, 2])

    def test_rejects_nonfinite_corner(self):
        with self.assertRaises(ValueError): inspector.bounds([(float("nan"), 0, 0)])

    def test_rejects_zero_size_geometry(self):
        with self.assertRaises(ValueError): inspector.bounds([(1, 1, 1)])

    def test_rejects_singular_projection(self):
        with self.assertRaises(ValueError): inspector.transformed_corners([(0, 0, 0)], [[1, 0, 0, 0]] * 4)

    def test_measured_landscape_camera_fit(self):
        self.assertAlmostEqual(inspector.fit_scale([(-2, -1), (2, 1)], 1, .75), 4.8)

    def test_measured_portrait_camera_fit(self):
        self.assertAlmostEqual(inspector.fit_scale([(-1, -2), (1, 2)], .75, 1), 4.8)

    def test_asymmetric_geometry_center_preserves_larger_edge(self):
        self.assertAlmostEqual(inspector.fit_scale([(-4, -1), (1, 2)], 1, 1), 9.6)

    def test_rejects_invalid_camera_frame(self):
        for width, height, margin in ((0, 1, 1.2), (1, -1, 1.2), (1, 1, float("nan")), (1, float("nan"), 1.2), (1, 1, .5)):
            with self.subTest(width=width, height=height, margin=margin), self.assertRaises(ValueError):
                inspector.fit_scale([(0, 0), (1, 1)], width, height, margin)


class PreflightTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.glb = fixture_glb(self.root / "owned.glb")

    def tearDown(self): self.temp.cleanup()

    def test_valid_container_and_embedded_data_uri(self):
        fixture_glb(self.glb, images=[{"uri": "data:image/png;base64,AA=="}])
        self.assertEqual(inspector.read_glb(self.glb)["asset"]["version"], "2.0")

    def test_rejects_truncated_container(self):
        self.glb.write_bytes(self.glb.read_bytes()[:-1])
        with self.assertRaises(ValueError): inspector.read_glb(self.glb)

    def test_rejects_wrong_extension(self):
        renamed = self.glb.rename(self.root / "model.bin")
        with self.assertRaises(ValueError): inspector.read_glb(renamed)

    def test_rejects_glb_header_version(self):
        raw = bytearray(self.glb.read_bytes()); struct.pack_into("<I", raw, 4, 1); self.glb.write_bytes(raw)
        with self.assertRaises(ValueError): inspector.read_glb(self.glb)

    def test_rejects_invalid_chunk_alignment(self):
        raw = bytearray(self.glb.read_bytes()); struct.pack_into("<I", raw, 12, len(raw) - 21); self.glb.write_bytes(raw)
        with self.assertRaises(ValueError): inspector.read_glb(self.glb)

    def test_rejects_external_image_and_buffer_dependencies(self):
        for collection, uri in (("images", "../../secret.png"), ("images", "https://example.invalid/image.png"), ("buffers", "geometry.bin")):
            fixture_glb(self.glb, **{collection: [{"uri": uri}]})
            with self.subTest(collection=collection, uri=uri), self.assertRaises(ValueError): inspector.read_glb(self.glb)

    def test_rejects_missing_mesh_and_malformed_asset(self):
        for update in ({"meshes": []}, {"asset": 1}, {"nodes": 4}, {"images": [7]}):
            fixture_glb(self.glb, **update)
            with self.subTest(update=update), self.assertRaises(ValueError): inspector.read_glb(self.glb)

    def test_rejects_too_many_nodes(self):
        fixture_glb(self.glb, nodes=[{}] * 4097)
        with self.assertRaises(ValueError): inspector.read_glb(self.glb)

    def test_existing_output_and_symlink_never_overwritten(self):
        existing = self.root / "evidence"; existing.mkdir(); evidence = existing / "receipt.json"; evidence.write_text("retain")
        alias = self.root / "alias"; alias.symlink_to(existing, target_is_directory=True)
        for path in (existing, alias):
            with self.subTest(path=path), self.assertRaises(FileExistsError): inspector.reserve_output(path)
        self.assertEqual(evidence.read_text(), "retain")

    def test_blender_zero_exit_without_inspection_is_not_success(self):
        output = self.root / "failed-run"
        before = inspector.digest(self.glb)
        with mock.patch.object(inspector.shutil, "which", return_value="fake-blender"), mock.patch.object(inspector.subprocess, "run", return_value=mock.Mock(returncode=0)), contextlib.redirect_stdout(io.StringIO()):
            status = inspector.main(["--input", str(self.glb), "--output", str(output)])
        receipt = json.loads((output / "receipt.json").read_text())
        self.assertEqual(status, 1)
        self.assertFalse(receipt["passed"])
        self.assertEqual(before, inspector.digest(self.glb))
        self.assertTrue((output / "blender.log").exists())

    def test_retains_worker_failure_log_and_exit(self):
        output = self.root / "worker-failure"
        def fail(command, stdout, **kwargs):
            stdout.write("owned fixture worker failed\n")
            return mock.Mock(returncode=17)
        with mock.patch.object(inspector.shutil, "which", return_value="fake-blender"), mock.patch.object(inspector.subprocess, "run", side_effect=fail), contextlib.redirect_stdout(io.StringIO()):
            status = inspector.main(["--input", str(self.glb), "--output", str(output)])
        self.assertEqual(status, 1)
        self.assertEqual(json.loads((output / "receipt.json").read_text())["blender_exit_code"], 17)
        self.assertIn("worker failed", (output / "blender.log").read_text())

    def test_retained_license_matches_exact_upstream_notice(self):
        notice = TOOL.parent / "NOTICE/universal-modder-MIT.txt"
        self.assertEqual(hashlib.sha256(notice.read_bytes()).hexdigest(), inspector.UPSTREAM["files"]["LICENSE"])

    def test_glb_identity_is_hash_of_the_exact_validated_bytes(self):
        model, validated = inspector.read_glb(self.glb, with_bytes=True)
        before = hashlib.sha256(validated).hexdigest()
        fixture_glb(self.glb, nodes=[{"name": "changed"}])
        self.assertNotEqual(before, inspector.digest(self.glb))
        self.assertEqual(model["nodes"], [])

    def test_actual_read_length_rechecked_after_stale_stat(self):
        stale = mock.Mock(suffix=".glb")
        stale.is_file.return_value = True
        stale.stat.return_value.st_size = 20
        stale.read_bytes.return_value = self.glb.read_bytes()
        with mock.patch.object(inspector, "MAX_BYTES", 64), self.assertRaises(ValueError):
            inspector.read_glb(stale)

    def test_png_requires_real_pixels_crc_and_end(self):
        def chunk(kind, data):
            return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
        header = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 6, 0, 0, 0))
        image = self.root / "test.png"
        valid = header + chunk(b"IDAT", zlib.compress(b"\0\xff\0\0\xff")) + chunk(b"IEND", b"")
        image.write_bytes(valid)
        self.assertEqual(inspector.png_dimensions(image), (1, 1))
        for invalid in (header, valid[:-1], valid[:-5] + b"error", header + chunk(b"IDAT", zlib.compress(b"")) + chunk(b"IEND", b"")):
            image.write_bytes(invalid)
            with self.subTest(bytes=len(invalid)), self.assertRaises(ValueError): inspector.png_dimensions(image)

    def test_oversized_integer_cannot_pass_finite_camera_validation(self):
        self.assertFalse(inspector.finite_sequence([10 ** 1000, 1, 1], 3))

    def test_empty_worker_json_cannot_forge_render_success(self):
        output = self.root / "empty-worker-evidence"
        def empty_evidence(command, **kwargs):
            (output / "inspection.json").write_text("{}")
            return mock.Mock(returncode=0)
        with mock.patch.object(inspector.shutil, "which", return_value="fake-blender"), mock.patch.object(inspector.subprocess, "run", side_effect=empty_evidence), contextlib.redirect_stdout(io.StringIO()):
            status = inspector.main(["--input", str(self.glb), "--output", str(output), "--render"])
        self.assertEqual(status, 1)
        self.assertFalse(json.loads((output / "receipt.json").read_text())["passed"])

    def test_three_camera_identity_and_margin_are_required(self):
        output = self.root / "three-views"; output.mkdir()
        cfg = {"render": False, "input_sha256": "owned", "threads": 8, "samples": 8, "width": 480, "height": 360}
        view = {"target": [0, 0, 0], "location": [0, -10, 5], "matrix_world": [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]], "near": .01, "far": 100, "ortho_scale": 10, "projected_corner_min": [.1, .1, 5], "projected_corner_max": [.9, .9, 15], "all_corners_inside_5pct_margin": True}
        result = {"schema_version": 1, "input_sha256_after": "owned", "blender_version": "fixture", "geometry": {"min": [-1, -1, -1], "max": [1, 1, 1], "center": [0, 0, 0], "size": [2, 2, 2]}, "census": {"mesh_objects": 1, "evaluated_vertices": 8}, "mesh_objects": [{}], "render": {"requested": False, "engine": "Cycles", "device": "CPU", "threads": 8, "samples": 8, "dimensions": [480, 360]}, "views": [dict(view, id=entry[0]) for entry in inspector.VIEWS]}
        path = output / "inspection.json"; path.write_text(json.dumps(result))
        self.assertEqual(len(inspector.validate_inspection(output, cfg)["views"]), 3)
        result["views"].pop(); path.write_text(json.dumps(result))
        with self.assertRaises(ValueError): inspector.validate_inspection(output, cfg)
        result["views"].append(dict(view, id="top", projected_corner_max=[1.1, .9, 15])); path.write_text(json.dumps(result))
        with self.assertRaises(ValueError): inspector.validate_inspection(output, cfg)
        result["views"] = [dict(view, id=entry[0]) for entry in inspector.VIEWS]
        cfg["render"] = True; result["render"]["requested"] = True; path.write_text(json.dumps(result))
        with self.assertRaises(ValueError): inspector.validate_inspection(output, cfg)

    def test_timeout_retains_failure_receipt(self):
        output = self.root / "timeout"
        with mock.patch.object(inspector.shutil, "which", return_value="fake-blender"), mock.patch.object(inspector.subprocess, "run", side_effect=inspector.subprocess.TimeoutExpired("fake-blender", 1)), contextlib.redirect_stdout(io.StringIO()):
            status = inspector.main(["--input", str(self.glb), "--output", str(output), "--timeout", "1"])
        receipt = json.loads((output / "receipt.json").read_text())
        self.assertEqual(status, 1)
        self.assertIsNone(receipt["blender_exit_code"])
        self.assertIn("wall limit", receipt["failure"])
        self.assertTrue(receipt["input"]["unchanged"])


if __name__ == "__main__": unittest.main(verbosity=2)
