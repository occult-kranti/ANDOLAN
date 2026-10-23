"""Adverse behavior checks for explicit progress recording and local read-only serving."""
import contextlib
import copy
import datetime as dt
import http.client
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest import mock

HERE = Path(__file__).parent
spec = importlib.util.spec_from_file_location("observatory", HERE / "observatory.py")
obs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(obs)


class ObservatoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = tempfile.TemporaryDirectory(prefix="yuga-observatory-")
        cls.workspace = Path(cls.fixture.name)
        subprocess.run(["git", "init", "-q", str(cls.workspace)], check=True)

    @classmethod
    def tearDownClass(cls):
        cls.fixture.cleanup()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=self.workspace)
        self.addCleanup(self.temp.cleanup)
        self.directory = obs.state_directory(self.workspace, Path(self.temp.name) / "state")
        obs.update_state(self.directory, initialize=("test-run", "Test production"))

    def job(self, job_id="artist", **extra):
        record = {"id": job_id, "title": "Artist pass", "status": "queued", "owner": "W3", "device": "cpu", "summary": "Queued"}
        record.update(extra)
        return record

    def test_init_rejects_overwrite_and_requires_git_root(self):
        with self.assertRaises(ValueError):
            obs.update_state(self.directory, initialize=("other", "Other"))
        self.assertEqual(obs.workspace_path(self.workspace), self.workspace)
        with self.assertRaises(ValueError):
            obs.workspace_path(self.directory)

    def test_record_validation_rejects_unknown_status_identifier_fields(self):
        for record in (self.job(status="magic"), self.job(job_id="../secret"), self.job(secret="hidden"), self.job(summary=12)):
            with self.subTest(record=record), self.assertRaises(ValueError):
                obs.update_state(self.directory, record)

    def test_running_requires_owned_process_or_bounded_heartbeat(self):
        for record in (self.job(status="running"), self.job(status="running", pid=-1),
                       self.job(status="running", heartbeat_ttl_seconds=True), self.job(status="running", heartbeat_ttl_seconds=301)):
            with self.subTest(record=record), self.assertRaises(ValueError):
                obs.update_state(self.directory, record)
        state = obs.update_state(self.directory, self.job(status="running", heartbeat_ttl_seconds=5))
        public = obs.public_job(state["jobs"][0], obs.now())
        self.assertEqual(public["status"], "running")
        self.assertNotIn("_tracking", public)
        self.assertNotIn("pid", json.dumps(public))

    def test_expired_heartbeat_is_stale_and_never_complete(self):
        state = obs.update_state(self.directory, self.job(status="running", heartbeat_ttl_seconds=5))
        later = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(seconds=10)).isoformat()
        self.assertEqual(obs.public_job(state["jobs"][0], later)["status"], "stale")
        self.assertEqual(state["jobs"][0]["status"], "running")

    @unittest.skipUnless(Path("/proc/self/stat").exists(), "Linux identity test")
    def test_actual_child_birth_and_exit_then_reused_pid_are_stale(self):
        child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(20)"])
        self.addCleanup(lambda: child.poll() is None and child.kill())
        state = obs.update_state(self.directory, self.job(status="running", pid=child.pid))
        job = state["jobs"][0]
        self.assertEqual(obs.public_job(job, obs.now())["status"], "running")
        changed = copy.deepcopy(job)
        changed["_tracking"]["identity"]["start_ticks"] = "different-birth"
        self.assertEqual(obs.public_job(changed, obs.now())["status"], "stale")
        child.terminate()
        child.wait(timeout=5)
        self.assertEqual(obs.public_job(job, obs.now())["status"], "stale")

    def test_complete_needs_evidence_and_is_explicit(self):
        with self.assertRaises(ValueError):
            obs.update_state(self.directory, self.job(status="complete"))
        with self.assertRaises(ValueError):
            obs.update_state(self.directory, self.job(status="complete", outputs=[{}]))
        state = obs.update_state(self.directory, self.job(status="complete", outputs=[{"label": "Receipt", "path": "docs/review.json"}]))
        self.assertEqual(state["jobs"][0]["status"], "complete")
        self.assertIsNotNone(state["jobs"][0]["finished_at"])

    def test_no_absolute_sensitive_or_javascript_urls(self):
        for output in ({"path": "/private/credentials"}, {"path": "a/../b"}, {"path": ".ssh/id_rsa"},
                       {"url": "javascript:alert(1)"}, {"url": "https://name:password@example.com/file"},
                       {"url": "//example.com/file"}, {"url": "http://example.com/file"}, {"url": "viewer/../secret"}):
            with self.subTest(output=output), self.assertRaises(ValueError):
                obs.update_state(self.directory, self.job(outputs=[output]))
        obs.update_state(self.directory, self.job(outputs=[{"url": "media/diya.png"}, {"url": "viewer/"}, {"url": "https://github.com/owner/repo"}]))

    def test_context_validation_and_payload_limits(self):
        for record in ({"secrets": []}, {"assets": ["bad"]}, {"sources": [{"name": "Source"}]}, {"milestones": [{}]},
                       {"assets": [{"id": "one", "title": "One", "status": "review", "image_url": "file:///etc/passwd"}]}):
            with self.subTest(record=record), self.assertRaises(ValueError):
                obs.update_state(self.directory, record, context=True)
        oversized = self.directory / "large.json"
        oversized.write_bytes(b" " * (obs.MAX_BYTES + 1))
        with self.assertRaises(ValueError):
            obs.read_json(oversized)
        before = (self.directory / "state.json").read_bytes()
        with self.assertRaises(ValueError):
            obs.atomic_json(self.directory / "state.json", {"large": "x" * obs.MAX_BYTES})
        self.assertEqual(before, (self.directory / "state.json").read_bytes())

    def test_state_schema_and_tracking_are_validated(self):
        state = obs.update_state(self.directory, self.job(status="running", heartbeat_ttl_seconds=5))
        state["jobs"][0]["_tracking"]["ttl_seconds"] = 50000
        with self.assertRaises(ValueError):
            obs.validate_state(state)
        state = obs.new_state("test", "Test")
        state["schema_version"] = 90
        with self.assertRaises(ValueError):
            obs.validate_state(state)

    def test_atomic_concurrent_process_updates_preserve_all_jobs(self):
        children = []
        for index in range(8):
            record = self.directory / f"input-{index}.json"
            record.write_text(json.dumps(self.job(f"job-{index}")))
            children.append(subprocess.Popen([sys.executable, str(HERE / "observatory.py"), "emit", "--workspace", str(self.workspace),
                                             "--state-dir", str(self.directory), "--record", str(record)], stdout=subprocess.PIPE, stderr=subprocess.PIPE))
        for child in children:
            stdout, stderr = child.communicate(timeout=10)
            self.assertEqual(child.returncode, 0, (stdout, stderr))
        self.assertEqual(len(obs.read_json(self.directory / "state.json")["jobs"]), 8)

    @unittest.skipUnless(hasattr(os, "symlink"), "symlinks unavailable")
    def test_symlink_records_state_parent_and_static_escape_rejected(self):
        outside = self.directory / "outside.json"
        outside.write_text('{"secret":"private"}')
        link = self.directory / "link.json"
        link.symlink_to(outside)
        with self.assertRaises(ValueError):
            obs.read_json(link)
        with self.assertRaises(ValueError):
            obs.atomic_json(link, {})
        folder_link = self.directory / "linked"
        folder_link.symlink_to(self.directory, target_is_directory=True)
        with self.assertRaises(ValueError):
            obs.state_directory(self.workspace, folder_link / "nested")
        web = self.directory / "web"
        web.mkdir()
        (web / "media").symlink_to(self.directory, target_is_directory=True)
        with self.assertRaises(ValueError):
            obs.static_path(web, "/media/outside.json")
        (web / "image.png").symlink_to(outside)
        with self.assertRaises(ValueError):
            obs.static_path(web, "/image.png")

    def test_static_traversal_encoded_slashes_and_double_encoding_rejected(self):
        web = self.directory / "web"
        web.mkdir()
        (web / "index.html").write_text("ready")
        self.assertEqual(obs.static_path(web, "/"), web / "index.html")
        (web / "viewer").mkdir()
        (web / "viewer/index.html").write_text("viewer fixture")
        self.assertEqual(obs.static_path(web, "/viewer/"), web / "viewer/index.html")
        for value in ("/../state.json", "/%2e%2e/state.json", "/%252e%252e/state.json", "/a%5cb.png", "//evil", "/%00.png"):
            with self.subTest(value=value), self.assertRaises((ValueError, FileNotFoundError)):
                obs.static_path(web, value)

    def test_snapshot_mode_and_actual_sample_time_preserved_on_export(self):
        observatory = obs.Observatory(self.workspace, self.directory)
        with mock.patch.object(obs, "now", return_value="2026-10-23T20:00:00+00:00"), mock.patch.object(obs, "host_info", return_value={}), mock.patch.object(obs, "source_info", return_value={}):
            snapshot = observatory.snapshot("snapshot")
        target = self.directory / "export.json"
        obs.atomic_json(target, snapshot)
        saved = obs.read_json(target)
        self.assertEqual(saved["mode"], "snapshot")
        self.assertEqual(saved["collected_at"], "2026-10-23T20:00:00+00:00")

    def test_gpu_telemetry_is_bounded_explicit_and_has_no_network_calls(self):
        with mock.patch.object(obs.shutil, "which", return_value="/safe/nvidia-smi"), mock.patch.object(obs, "command", return_value="GPU name, 8192, 1024, 10") as run:
            gpu = obs.host_info()["gpu"]
        self.assertTrue(gpu["available"])
        self.assertEqual(gpu["devices"][0]["memory_total_bytes"], 8192 * 1048576)
        self.assertEqual(run.call_args.args[1], 2)
        with mock.patch.object(obs.shutil, "which", return_value=None):
            self.assertFalse(obs.host_info()["gpu"]["available"])

    def test_unknown_git_status_does_not_claim_clean(self):
        with mock.patch.object(obs, "command", return_value=None):
            self.assertIsNone(obs.source_info(self.workspace)["dirty"])

    def test_real_http_is_read_only_local_and_returns_bounded_errors(self):
        observer = obs.Observatory(self.workspace, self.directory)
        observer.web = self.directory / "web"
        observer.web.mkdir()
        (observer.web / "index.html").write_text("<h1>Actual file</h1>")
        (observer.web / "font.ttf").write_bytes(b"font fixture")
        (observer.web / "NOTICE.txt").write_text("License fixture")
        (observer.web / "effect.mp4").write_bytes(b"temporal witness fixture")
        with mock.patch.object(obs, "host_info", return_value={}), mock.patch.object(obs, "source_info", return_value={}):
            server = obs.make_server(observer, 0)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            self.addCleanup(server.server_close)
            self.addCleanup(server.shutdown)
            def get(path, method="GET", host=None):
                connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=3)
                connection.request(method, path, headers={"Host": host} if host else {})
                response = connection.getresponse()
                body = response.read()
                status = response.status
                connection.close()
                return status, body
            status, body = get("/api/status")
            self.assertEqual(status, 200)
            self.assertEqual(json.loads(body)["mode"], "live")
            self.assertEqual(get("/")[0], 200)
            self.assertEqual(get("/font.ttf")[0], 200)
            self.assertEqual(get("/NOTICE.txt")[0], 200)
            connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=3)
            connection.request("GET", "/effect.mp4")
            response = connection.getresponse()
            self.assertEqual(response.status, 200)
            self.assertEqual(response.getheader("Content-Type"), "video/mp4")
            self.assertEqual(response.read(), b"temporal witness fixture")
            connection.close()
            self.assertEqual(get("/api/health")[0], 200)
            self.assertEqual(get("/api/status", "POST")[0], 405)
            self.assertEqual(get("/api/status", host="attacker.example")[0], 400)
            for path in ("/%2e%2e/state.json", "/missing.png", "/api/nope"):
                status, body = get(path)
                self.assertIn(status, {404, 422})
                self.assertNotIn(str(self.directory).encode(), body)
                self.assertLess(len(body), 200)


if __name__ == "__main__":
    unittest.main()
