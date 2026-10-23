"""Mocked boundary tests only; these do not establish real model inference."""

import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

SCRIPT = Path(__file__).with_name("cpu_llama.py")
spec = importlib.util.spec_from_file_location("cpu_llama_boundary", SCRIPT)
cpu = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cpu)


class BoundaryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "cache"
        (self.root / "evidence").mkdir(parents=True)
        (self.root / "models").mkdir()
        self.target = self.root / "models/model.gguf"
        self.partial = self.target.with_name(self.target.name + ".part")
        self.payload = b"verified test fixture, not weights"
        self.sha = hashlib.sha256(self.payload).hexdigest()

    def download(self):
        return cpu.download(self.root, "https://example.invalid/model.gguf", self.target,
                            len(self.payload), self.sha, "fixture")

    def fake_curl(self, args, **kwargs):
        self.assertEqual(args[:2], ["curl", "--disable"])
        self.assertEqual(args[args.index("--output") + 1], "-")
        os.write(kwargs["stdout"].fileno(), self.payload)
        return subprocess.CompletedProcess(args, 0, stderr="CURL_METRICS:200,33,0.01")

    def test_dangling_partial_symlink_never_starts_curl(self):
        outside = Path(self.temp.name) / "outside"
        self.partial.symlink_to(outside)
        with mock.patch.object(cpu.subprocess, "run") as run, self.assertRaises(RuntimeError):
            self.download()
        run.assert_not_called()
        self.assertFalse(outside.exists())
        self.assertFalse(self.target.exists())

    def test_existing_artifact_symlink_is_not_verified(self):
        outside = Path(self.temp.name) / "outside"
        outside.write_bytes(self.payload)
        self.target.symlink_to(outside)
        with mock.patch.object(cpu.subprocess, "run") as run, self.assertRaises(RuntimeError):
            self.download()
        run.assert_not_called()
        self.assertEqual(outside.read_bytes(), self.payload)

    def test_cache_root_and_parent_component_symlinks_are_rejected(self):
        alias = Path(self.temp.name) / "alias"
        alias.symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(RuntimeError):
            cpu.download(alias, "https://example.invalid/x", alias / "models/x", 1, "unused", "fixture")
        result = subprocess.run([sys.executable, str(SCRIPT), "qualify", "--cache-dir", str(alias)],
                                capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, 2)
        self.assertIn("symlink", result.stderr)

    def test_exclusive_fd_download_ignores_curlrc_and_verifies(self):
        with mock.patch.object(cpu.subprocess, "run", side_effect=self.fake_curl):
            result = self.download()
        self.assertEqual(result["status"], "VERIFIED")
        self.assertEqual(self.target.read_bytes(), self.payload)
        self.assertFalse(self.target.is_symlink())
        self.assertFalse(self.partial.exists())

    def test_regular_partial_is_preserved_without_network(self):
        self.partial.write_bytes(b"previous interrupted attempt")
        with mock.patch.object(cpu.subprocess, "run") as run, self.assertRaises(RuntimeError):
            self.download()
        run.assert_not_called()
        self.assertEqual(self.partial.read_bytes(), b"previous interrupted attempt")

    def test_wrong_hash_is_not_promoted_or_marked_verified(self):
        self.sha = "0" * 64
        with mock.patch.object(cpu.subprocess, "run", side_effect=self.fake_curl), self.assertRaises(RuntimeError):
            self.download()
        self.assertFalse(self.target.exists())
        self.assertEqual(json.loads((self.root / "evidence/fixture-transfer.json").read_text())["status"], "FAILED")

    def test_partial_replacement_cannot_promote_an_outside_symlink(self):
        outside = Path(self.temp.name) / "outside"
        outside.write_bytes(b"unchanged")
        def replace_partial(args, **kwargs):
            result = self.fake_curl(args, **kwargs)
            self.partial.unlink()
            self.partial.symlink_to(outside)
            return result
        with mock.patch.object(cpu.subprocess, "run", side_effect=replace_partial), self.assertRaises(RuntimeError):
            self.download()
        self.assertFalse(self.target.exists())
        self.assertEqual(outside.read_bytes(), b"unchanged")

    def process(self):
        process = mock.Mock(pid=123456, returncode=None)
        process.poll.side_effect = lambda: process.returncode
        def stop(*args, **kwargs):
            process.returncode = 0
            return 0
        process.terminate.side_effect = stop
        process.kill.side_effect = stop
        process.wait.side_effect = stop
        return process

    def test_build_budget_failure_overwrites_prior_success(self):
        path = self.root / "evidence/build-test.json"
        path.write_text('{"status":"PASSED","exit":0}')
        with mock.patch.object(cpu.subprocess, "Popen", return_value=self.process()), \
                mock.patch.object(cpu, "check_budget", side_effect=RuntimeError("budget")), \
                mock.patch.object(cpu.os, "killpg") as kill, self.assertRaises(RuntimeError):
            cpu.run_logged(self.root, ["fake-build"], "build-test")
        result = json.loads(path.read_text())
        self.assertEqual(result["status"], "FAILED")
        self.assertIn("budget", result["error"])
        kill.assert_called_once()

    def test_build_timeout_overwrites_prior_success(self):
        path = self.root / "evidence/build-test.json"
        path.write_text('{"status":"PASSED","exit":0}')
        with mock.patch.object(cpu.subprocess, "Popen", return_value=self.process()), \
                mock.patch.object(cpu.os, "killpg"), self.assertRaises(RuntimeError):
            cpu.run_logged(self.root, ["fake-build"], "build-test", timeout=-1)
        self.assertEqual(json.loads(path.read_text())["status"], "FAILED")

    def fixture_manifest(self):
        self.target.write_bytes(self.payload)
        binary = self.root / "build/bin/llama-server"
        binary.parent.mkdir(parents=True)
        binary.write_bytes(b"fake server fixture, never executed")
        source = cpu.MANIFEST["source"]["commit"]
        (self.root / "evidence/build-receipt.json").write_text(json.dumps({
            "source_commit": source, "binary_sha256": hashlib.sha256(binary.read_bytes()).hexdigest()}))
        model = {**cpu.MANIFEST["model"], "filename": self.target.name, "bytes": len(self.payload), "sha256": self.sha}
        return mock.patch.dict(cpu.MANIFEST, {"model": model})

    def completion(self, alias):
        return {"model": alias, "usage": {"completion_tokens": 5, "prompt_tokens": 4},
                "choices": [{"message": {"content": '{"case":"blocked","steps":"try move","expected":"remain at (2,2)"}'}}]}

    def test_wrong_listed_model_never_reaches_completion(self):
        with self.fixture_manifest(), mock.patch.object(cpu.subprocess, "Popen", return_value=self.process()) as start, \
                mock.patch.object(cpu.socket, "socket"), \
                mock.patch.object(cpu, "local_json", side_effect=[{"status": "ok"}, {"data": [{"id": "wrong"}]}]) as request:
            result = cpu.qualify(self.root, 8093)
        self.assertEqual(result["status"], "QUALIFICATION_FAILED")
        self.assertFalse(result["real_inference_performed"])
        self.assertEqual(request.call_count, 2)
        key = start.call_args.kwargs["env"]["LLAMA_API_KEY"]
        self.assertTrue(key)
        self.assertNotIn(key, json.dumps(result))
        self.assertTrue(all(call.kwargs["api_key"] == key for call in request.call_args_list))

    def test_wrong_completion_model_is_not_operational_success(self):
        alias = cpu.MANIFEST["server_alias"]
        with self.fixture_manifest(), mock.patch.object(cpu.subprocess, "Popen", return_value=self.process()), \
                mock.patch.object(cpu.socket, "socket"), \
                mock.patch.object(cpu, "local_json", side_effect=[{"status": "ok"}, {"data": [{"id": alias}]}, self.completion("wrong")]):
            result = cpu.qualify(self.root, 8093)
        self.assertEqual(result["status"], "QUALIFICATION_FAILED")
        self.assertFalse(result["real_inference_performed"])

    def test_final_budget_failure_still_saves_failure_receipt(self):
        alias = cpu.MANIFEST["server_alias"]
        with self.fixture_manifest(), mock.patch.object(cpu.subprocess, "Popen", return_value=self.process()), \
                mock.patch.object(cpu.socket, "socket"), \
                mock.patch.object(cpu, "check_budget", side_effect=RuntimeError("post-run budget")), \
                mock.patch.object(cpu, "local_json", side_effect=[{"status": "ok"}, {"data": [{"id": alias}]}, self.completion(alias)]):
            result = cpu.qualify(self.root, 8093)
        saved = json.loads((self.root / "evidence/qualification.json").read_text())
        self.assertEqual(result["status"], "QUALIFICATION_FAILED")
        self.assertEqual(saved["status"], "QUALIFICATION_FAILED")
        self.assertIn("post-run budget", saved["budget_error"])
        self.assertTrue(saved["server_stopped"])

    def assert_main_preflight_failure_replaces_success(self):
        path = self.root / "evidence/qualification.json"
        path.write_text('{"status":"REAL_INFERENCE_VERIFIED","real_inference_performed":true}')
        with mock.patch.object(sys, "argv", [str(SCRIPT), "qualify", "--cache-dir", str(self.root)]), \
                mock.patch.object(sys, "stdout", new_callable=io.StringIO), \
                mock.patch.object(cpu.subprocess, "Popen") as start:
            self.assertEqual(cpu.main(), 1)
        start.assert_not_called()
        saved = json.loads(path.read_text())
        self.assertEqual(saved["status"], "QUALIFICATION_FAILED")
        self.assertFalse(saved["real_inference_performed"])
        self.assertEqual(saved["stage"], "preflight_or_execution_error")
        return saved

    def test_binary_hash_preflight_failure_replaces_prior_success(self):
        with self.fixture_manifest():
            (self.root / "build/bin/llama-server").write_bytes(b"altered binary fixture")
            result = self.assert_main_preflight_failure_replaces_success()
        self.assertIn("does not match", result["error"])

    def test_occupied_port_preflight_failure_replaces_prior_success(self):
        with self.fixture_manifest(), mock.patch.object(cpu.socket, "socket") as connection:
            connection.return_value.__enter__.return_value.bind.side_effect = OSError("Address already in use")
            result = self.assert_main_preflight_failure_replaces_success()
        self.assertIn("Address already in use", result["error"])


if __name__ == "__main__":
    unittest.main()
