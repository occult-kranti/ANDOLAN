import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import publish_site as publisher


class AdditivePublicationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.site = self.root / "assembled"
        self.web = self.root / "web"
        self.site.mkdir()
        self.web.mkdir()
        for name in publisher.REQUIRED_BASELINE:
            path = self.site / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("preserve exactly: " + name)
        (self.site / "asset.js").write_bytes(b"baseline binary\x00payload")
        for name in ("index.html", "styles.css", "app.js"):
            (self.web / name).write_text("current dashboard: " + name)
        (self.web / "media/licenses").mkdir(parents=True)
        (self.web / "media/rama.glb").write_bytes(b"fixture asset")
        (self.web / "media/licenses/OFL-1.1.txt").write_text("retained license")
        self.data = {"schema_version": 1, "mode": "snapshot", "collected_at": "2026-10-23T20:00:00+00:00",
                     "jobs": [{"id": "render", "outputs": [{"url": "media/rama.glb", "path": "games/yuga-native/art/source.glb"}]}],
                     "assets": [], "milestones": [],
                     "sources": [{"url": "https://github.com/occult-kranti/ANDOLAN"}]}
        self.write_snapshot()
        self.before = self.baseline_bytes()

    def write_snapshot(self):
        (self.web / "status.json").write_text(json.dumps(self.data))

    def baseline_bytes(self):
        return {p.relative_to(self.site).as_posix(): p.read_bytes() for p in self.site.rglob("*") if p.is_file() and not p.is_relative_to(self.site / "production")}

    def publish(self):
        return publisher.publish(self.site, self.web, "a" * 40, "b" * 40)

    def assert_refused_untouched(self):
        with self.assertRaises(ValueError):
            self.publish()
        self.assertEqual(self.baseline_bytes(), self.before)
        self.assertFalse((self.site / "production").exists())

    def test_adds_snapshot_and_assets_while_preserving_every_baseline_byte(self):
        result = self.publish()
        self.assertEqual(self.baseline_bytes(), self.before)
        self.assertEqual(result["data_mode"], "snapshot")
        self.assertEqual(result["baseline_files"], len(self.before))
        published = json.loads((self.site / "production/status.json").read_text())
        self.assertEqual(published, self.data)
        self.assertEqual((self.site / "production/media/rama.glb").read_bytes(), b"fixture asset")
        self.assertTrue((self.site / "production/media/licenses/OFL-1.1.txt").exists())
        self.assertEqual(result["dashboard_files"]["app.js"]["sha256"], hashlib.sha256((self.web / "app.js").read_bytes()).hexdigest())
        self.assertIn("historical deployed byte equality unverified", result["scope"])

    def test_never_copies_python_design_documents_source_maps_or_extra_root_js(self):
        for name in ("verify_ui.py", "DESIGN.md", "source.js.map", "arbitrary.js", "package.json"):
            (self.web / name).write_text("not a deployment artifact")
        self.publish()
        for name in ("verify_ui.py", "DESIGN.md", "source.js.map", "arbitrary.js", "package.json"):
            self.assertFalse((self.site / "production" / name).exists())

    def test_publishes_compiled_viewer_and_not_its_source_or_dependency_tree(self):
        for name in ("viewer/index.html", "viewer/assets/viewer-abc.js", "viewer/NOTICE.txt", "viewer/PLAYCANVAS-LICENSE.txt", "viewer/favicon.svg",
                     "viewer/src/main.js", "viewer/node_modules/three/index.js", "viewer/assets/viewer.js.map"):
            p = self.web / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(name)
        self.data["assets"] = [{"model_url": "viewer/"}]
        self.write_snapshot()
        self.publish()
        for name in ("viewer/index.html", "viewer/assets/viewer-abc.js", "viewer/NOTICE.txt", "viewer/PLAYCANVAS-LICENSE.txt", "viewer/favicon.svg"):
            self.assertTrue((self.site / "production" / name).exists())
        for name in ("viewer/src/main.js", "viewer/node_modules/three/index.js", "viewer/assets/viewer.js.map"):
            self.assertFalse((self.site / "production" / name).exists())

    def test_compiled_viewer_without_required_notice_is_not_published(self):
        (self.web / "viewer").mkdir()
        (self.web / "viewer/index.html").write_text("compiled viewer")
        (self.web / "viewer/NOTICE.txt").write_text("source notice")
        self.assert_refused_untouched()

    def test_live_input_is_refused_instead_of_publishing_fake_live_telemetry(self):
        self.data["mode"] = "live"
        self.write_snapshot()
        self.assert_refused_untouched()

    def test_snapshot_schema_and_observation_timestamp_are_required(self):
        original = copy.deepcopy(self.data)
        for key, value in (("schema_version", True), ("collected_at", "2026-10-23T20:00:00"),
                           ("collected_at", "invalid"), ("jobs", {})):
            with self.subTest(key=key, value=value):
                self.data = copy.deepcopy(original)
                self.data[key] = value
                self.write_snapshot()
                self.assert_refused_untouched()

    def test_missing_artifact_and_missing_viewer_are_rejected(self):
        for value in ("media/missing.glb", "viewer/"):
            with self.subTest(value=value):
                self.data["jobs"][0]["outputs"][0]["url"] = value
                self.write_snapshot()
                self.assert_refused_untouched()

    def test_artifact_paths_and_credential_urls_cannot_escape(self):
        values = ("../secret.glb", "/media/rama.glb", "media/%2e%2e/secret", "media/../secret", "javascript:alert(1)",
                  "https://user:password@example.com/art.glb", "https://example.com/art?token=secret",
                  "https://127.0.0.1/art.glb", "https://localhost/art.glb", "https://internal.local/art.glb")
        for value in values:
            with self.subTest(value=value):
                self.data["jobs"][0]["outputs"][0]["url"] = value
                self.write_snapshot()
                self.assert_refused_untouched()

    def test_repo_display_paths_and_private_process_records_are_rejected(self):
        original = copy.deepcopy(self.data)
        for record in ({"path": "../../secret"}, {"path": "/private/file"}, {"pid": 123},
                       {"boot_id": "private"}, {"api_key": "private"},
                       {"_tracking": {"kind": "heartbeat", "expires_at": "private deadline"}}):
            with self.subTest(record=record):
                self.data = copy.deepcopy(original)
                self.data["jobs"][0].update(record)
                self.write_snapshot()
                self.assert_refused_untouched()

    def test_symlink_file_and_directory_are_refused_even_if_not_allowlisted(self):
        for name, target in (("link.py", self.web / "app.js"), ("linked-dir", self.site / "yuga")):
            with self.subTest(name=name):
                link = self.web / name
                link.symlink_to(target, target_is_directory=target.is_dir())
                self.assert_refused_untouched()
                link.unlink()

    def test_symlink_root_component_and_baseline_symlink_are_refused(self):
        link = self.root / "site-link"
        link.symlink_to(self.site, target_is_directory=True)
        with self.assertRaises(ValueError):
            publisher.publish(link, self.web, "a" * 40, "b" * 40)
        (self.site / "linked-asset.js").symlink_to(self.web / "app.js")
        with self.assertRaises(ValueError):
            self.publish()
        self.assertFalse((self.site / "production").exists())

    def test_each_baseline_entrypoint_is_mandatory(self):
        for name in publisher.REQUIRED_BASELINE:
            with self.subTest(name=name):
                path = self.site / name
                contents = path.read_bytes()
                path.unlink()
                with self.assertRaises(ValueError):
                    self.publish()
                self.assertFalse((self.site / "production").exists())
                path.write_bytes(contents)
        self.assertEqual(self.baseline_bytes(), self.before)

    def test_existing_production_is_not_deleted_or_merged(self):
        (self.site / "production").mkdir()
        (self.site / "production/keep.txt").write_text("existing unique output")
        with self.assertRaises(ValueError):
            self.publish()
        self.assertEqual((self.site / "production/keep.txt").read_text(), "existing unique output")
        self.assertEqual(self.baseline_bytes(), self.before)

    def test_full_commits_disjoint_roots_and_bounded_payloads_required(self):
        with self.assertRaises(ValueError):
            publisher.publish(self.site, self.web, "main", "b" * 40)
        with self.assertRaises(ValueError):
            publisher.publish(self.site, self.site, "a" * 40, "b" * 40)
        with patch.object(publisher, "MAX_FILE", 1):
            self.assert_refused_untouched()

    def test_source_mutation_during_copy_aborts_without_installing_dashboard(self):
        real_copy = publisher.shutil.copyfile

        def changed(source, target, **kwargs):
            result = real_copy(source, target, **kwargs)
            if Path(source).name == "app.js":
                Path(target).write_text("unexpected changed bytes")
            return result

        with patch.object(publisher.shutil, "copyfile", side_effect=changed):
            self.assert_refused_untouched()
        self.assertFalse(any(p.name.startswith(".production-") for p in self.site.iterdir()))

    def test_unreadable_baseline_directory_blocks_census_instead_of_disappearing(self):
        blocked = self.site / "not-readable"
        blocked.mkdir()
        (blocked / "keep.bin").write_bytes(b"must remain in baseline census")
        real_scandir = publisher.os.scandir

        def denied(path):
            if Path(path) == blocked:
                raise PermissionError("simulated unreadable baseline directory")
            return real_scandir(path)

        with patch.object(publisher.os, "scandir", side_effect=denied):
            with self.assertRaisesRegex(ValueError, "Cannot complete"):
                self.publish()
        self.assertFalse((self.site / "production").exists())
        self.assertEqual((blocked / "keep.bin").read_bytes(), b"must remain in baseline census")


if __name__ == "__main__":
    unittest.main()
