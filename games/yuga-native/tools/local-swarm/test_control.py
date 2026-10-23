"""Behavior checks using temporary workspaces; never contact a real SSH host."""

import contextlib
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

import control


def manifest():
    return {
        "schema_version": 1,
        "fallback": None,
        "workers": [{"id": worker, "role": role, "allowed_paths": [f"work/{worker}"]}
                    for worker, role in control.ROLES.items()],
        "ssh_targets": {},
        "jobs": [{"id": "check", "worker": "W1", "cwd": ".", "writes": [],
                  "argv": [sys.executable, "-c", "print('checked')"], "timeout_seconds": 3}],
    }


class TemporaryWorkspace(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="yuga-control-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()

    def invoke(self, data, operation="jobs", *options):
        source = self.root / "manifest.json"
        source.write_text(json.dumps(data), encoding="utf-8")
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            status = control.main([operation, str(source), "--workspace", str(self.root), *options])
        return status, json.loads(output.getvalue())


class ManifestTests(TemporaryWorkspace):
    def test_six_role_manifest_and_write_binding(self):
        data = manifest()
        data["jobs"][0]["writes"] = ["work/W1/report.json"]
        self.assertIs(control.validate_manifest(data, self.root), data)
        data["jobs"][0]["writes"] = ["work/W2/report.json"]
        with self.assertRaisesRegex(control.ControlError, "exclusive"):
            control.validate_manifest(data, self.root)

    def test_ownership_overlap_and_missing_role(self):
        data = manifest()
        data["workers"][1]["allowed_paths"] = ["work/W1/child"]
        with self.assertRaisesRegex(control.ControlError, "overlapping"):
            control.validate_manifest(data, self.root)
        data = manifest()
        data["workers"].pop()
        with self.assertRaisesRegex(control.ControlError, "six"):
            control.validate_manifest(data, self.root)
        data = manifest(); data["workers"][0]["allowed_paths"] = [".local-swarm"]
        with self.assertRaisesRegex(control.ControlError, "control state"):
            control.validate_manifest(data, self.root)

    def test_case_only_ownership_aliases_rejected_on_all_platforms(self):
        for alias in ["WORK/w1", "WORK/w1/Child"]:
            data = manifest(); data["workers"][1]["allowed_paths"] = [alias]
            with self.subTest(alias=alias), self.assertRaisesRegex(control.ControlError, "overlapping"):
                control.validate_manifest(data, self.root)

    def test_absolute_traversal_glob_and_protected_paths(self):
        for value in ["../outside", "/tmp/outside", "a/../../b", "a//b", "a/./b", "*.png",
                      "C:/outside", "a\\b", ".git/config", "work/.env", "work/.ssh/key",
                      ".codex/auth.json", ".kimi-code/credentials", ".config/client", ".local/client",
                      "scratch/.CODEX/data", "scratch/generated/auth.json"]:
            with self.subTest(value=value), self.assertRaises(control.ControlError):
                control.inside(self.root, value)

    @unittest.skipUnless(hasattr(os, "symlink"), "requires symlinks")
    def test_symlink_escape_and_internal_symlink_rejected(self):
        (self.root / "link").symlink_to(self.root.parent, target_is_directory=True)
        with self.assertRaisesRegex(control.ControlError, "symlink"):
            control.inside(self.root, "link/outside")
        (self.root / "real").mkdir()
        (self.root / "internal").symlink_to(self.root / "real", target_is_directory=True)
        with self.assertRaises(control.ControlError):
            control.inside(self.root, "internal/file")

    def test_missing_cwd_and_invalid_timeouts(self):
        data = manifest()
        data["jobs"][0]["cwd"] = "absent"
        with self.assertRaisesRegex(control.ControlError, "cwd"):
            control.validate_manifest(data, self.root)
        for value in [True, 0, -2, 3601, float("inf"), float("nan"), "10"]:
            with self.subTest(timeout=value), self.assertRaises(control.ControlError):
                control.timeout_value(value)

    def test_malformed_records_return_blocked(self):
        candidates = [[], None, "bad"]
        for field, value in [("workers", [None] * 6), ("workers", [{"id": []}] * 6),
                             ("jobs", [None]), ("ssh_targets", {"remote": None})]:
            data = manifest(); data[field] = value; candidates.append(data)
        for field in ["worker", "target"]:
            data = manifest(); data["jobs"][0][field] = []; candidates.append(data)
        for data in candidates:
            with self.subTest(data=data):
                code, report = self.invoke(data)
                self.assertEqual(code, 2)
                self.assertEqual(report["status"], "blocked")

    def test_no_fallback_or_unbounded_argv(self):
        data = manifest(); data["fallback"] = "paid-cloud"
        with self.assertRaises(control.ControlError):
            control.validate_manifest(data, self.root)
        for value in ["echo hi", [], [""], ["echo", "bad\0argument"], ["echo", "x" * 32768]]:
            with self.subTest(argv=str(value)[:40]), self.assertRaises(control.ControlError):
                control.checked_argv(value)

    def test_boolean_schema_is_not_integer_version(self):
        data = manifest(); data["schema_version"] = True
        with self.assertRaisesRegex(control.ControlError, "schema_version"):
            control.validate_manifest(data, self.root)

    def test_no_implicit_ssh_target(self):
        data = manifest(); data["jobs"][0]["target"] = "unknown-host"
        with self.assertRaisesRegex(control.ControlError, "unknown SSH"):
            control.validate_manifest(data, self.root)
        data["ssh_targets"]["unknown-host"] = {"workspace": "/home/worker/yuga"}
        data["jobs"][0]["gpu"] = True
        with self.assertRaisesRegex(control.ControlError, "CPU workers"):
            control.validate_manifest(data, self.root)


class ExecutionTests(TemporaryWorkspace):
    def test_real_cli_process_dry_run_and_execution_receipt(self):
        source = self.root / "manifest.json"
        source.write_text(json.dumps(manifest()), encoding="utf-8")
        argv = [sys.executable, "-B", str(Path(control.__file__).resolve()), "jobs", str(source), "--workspace", str(self.root)]
        dry = subprocess.run(argv, capture_output=True, text=True, timeout=5)
        self.assertEqual(dry.returncode, 0, dry.stderr)
        self.assertEqual(json.loads(dry.stdout)["status"], "dry_run")
        receipt = ".local-swarm/receipts/real-cli.json"
        actual = subprocess.run([*argv, "--execute", "--job", "check", "--receipt", receipt], capture_output=True, text=True, timeout=5)
        self.assertEqual(actual.returncode, 0, actual.stderr)
        report = json.loads(actual.stdout)
        self.assertEqual(report["results"][0]["output"]["stdout"]["text"], "checked\n")
        self.assertEqual(report, json.loads((self.root / receipt).read_text()))

    def test_literal_argv_never_executes_shell_metacharacters(self):
        literals = ["$(touch INJECTED)", "; touch ALSO_INJECTED", "`id`", "space value", "a'b\"c", "x\ny", ""]
        job = manifest()["jobs"][0]
        job["argv"] = [sys.executable, "-c", "import json,sys; print(json.dumps(sys.argv[1:]))", *literals]
        result = control.execute_local(job, self.root)
        self.assertEqual(result["exit_code"], 0)
        self.assertEqual(json.loads(result["output"]["stdout"]["text"]), literals)
        self.assertFalse((self.root / "INJECTED").exists())
        self.assertFalse((self.root / "ALSO_INJECTED").exists())

    def test_failure_stops_batch_and_keeps_exit_status(self):
        data = manifest()
        data["jobs"][0]["argv"] = [sys.executable, "-c", "raise SystemExit(7)"]
        second = copy.deepcopy(data["jobs"][0]); second["id"] = "second"
        second["argv"] = [sys.executable, "-c", "open('SHOULD_NOT_EXIST','w').write('bad')"]
        data["jobs"].append(second)
        result = control.execute_jobs(data, self.root, ["check", "second"])
        self.assertEqual(result["results"][0]["exit_code"], 7)
        self.assertEqual(result["not_started"], ["second"])
        self.assertFalse((self.root / "SHOULD_NOT_EXIST").exists())

    def test_timeout_is_bounded_and_records_timeout(self):
        result = control.run_process([sys.executable, "-c", "import time; time.sleep(30)"], self.root, 0.1)
        self.assertEqual(result["exit_code"], 124)
        self.assertEqual(result["status"], "timed_out")
        self.assertLess(result["elapsed_seconds"], 3)

    def test_missing_executable_and_bounded_output(self):
        result = control.run_process([str(self.root / "missing-executable")], self.root, 1)
        self.assertEqual(result["exit_code"], 127)
        result = control.run_process([sys.executable, "-c", "import sys; sys.stdout.write('x'*100000)"], self.root, 3)
        output = result["output"]["stdout"]
        self.assertEqual(len(output["text"]), control.LOG_LIMIT)
        self.assertEqual(output["bytes_seen"], 100000)
        self.assertTrue(output["truncated"])

    def test_gpu_wrapper_only_when_explicit(self):
        job = manifest()["jobs"][0]
        helper = self.root / control.GPU_HELPER
        helper.parent.mkdir(parents=True); helper.write_text("# fixture only\n")
        with mock.patch.object(control, "run_process", return_value={"exit_code": 0}) as run:
            control.execute_local(job, self.root)
            self.assertEqual(run.call_args.args[0], job["argv"])
            job["gpu"] = True
            control.execute_local(job, self.root)
            self.assertEqual(run.call_args.args[0][:4], [sys.executable, str(helper), "--lock", str(self.root / ".local-swarm/gpu.lock")])
            self.assertEqual(run.call_args.args[0][4:], ["--", *job["argv"]])

    def test_remote_permission_blocks_entire_batch_before_execution(self):
        data = manifest()
        data["ssh_targets"]["ps4-cpu"] = {"workspace": "/home/worker/yuga"}
        remote = copy.deepcopy(data["jobs"][0]); remote.update(id="remote", target="ps4-cpu")
        data["jobs"].append(remote)
        with mock.patch.object(control, "execute_local") as local:
            with self.assertRaisesRegex(control.ControlError, "before any batch"):
                control.execute_jobs(data, self.root, ["check", "remote"])
            local.assert_not_called()

    def test_ssh_json_transport_and_host_verification(self):
        job = manifest()["jobs"][0]
        job.update(target="ps4-cpu", argv=["echo", "$(touch remote-injection)", "'; exit 9 #"])
        target = {"workspace": "/home/worker/space ' quoted"}
        response = {"exit_code": 0, "output": {"stdout": {"text": json.dumps({"status": "passed", "exit_code": 0})}}}
        with mock.patch.object(control.shutil, "which", return_value="/usr/bin/ssh"), mock.patch.object(control, "run_process", return_value=response) as run:
            result = control.execute_ssh(job, target, True)
        self.assertEqual(result["exit_code"], 0)
        command, _, timeout, payload = run.call_args.args
        self.assertIn("BatchMode=yes", command)
        self.assertIn("StrictHostKeyChecking=yes", command)
        self.assertEqual(command[-2], "ps4-cpu")
        self.assertNotIn("remote-injection", command[-1])
        self.assertNotIn(target["workspace"], command[-1])
        packet = json.loads(payload)
        self.assertEqual(packet["job"]["argv"], job["argv"])
        self.assertEqual(packet["workspace"], target["workspace"])
        self.assertEqual(packet["sha256"], control.sha256(Path(control.__file__)))
        self.assertEqual(timeout, job["timeout_seconds"] + 20)
        self.assertGreater(run.call_args.kwargs["output_limit"], 2 * control.LOG_LIMIT)

    def test_ssh_failure_missing_client_and_malformed_response(self):
        job = manifest()["jobs"][0]; job["target"] = "ps4-cpu"
        target = {"workspace": "/home/worker/yuga"}
        with mock.patch.object(control.shutil, "which", return_value=None):
            with self.assertRaisesRegex(control.ControlError, "unavailable"):
                control.execute_ssh(job, target, True)
        with mock.patch.object(control.shutil, "which", return_value="ssh"):
            with mock.patch.object(control, "run_process", return_value={"exit_code": 255}):
                result = control.execute_ssh(job, target, True)
                self.assertEqual(result["status"], "ssh_transport_failed")
                self.assertEqual(result["remote_outcome"], "unknown_inspect_before_retry")
            response = {"exit_code": 0, "output": {"stdout": {"text": "not json"}}}
            with mock.patch.object(control, "run_process", return_value=response):
                self.assertEqual(control.execute_ssh(job, target, True)["exit_code"], 70)

    @unittest.skipUnless(hasattr(os, "geteuid"), "remote bootstrap is POSIX-only")
    def test_installed_remote_bootstrap_with_simulated_normal_user(self):
        helper = self.root / control.HELPER_PATH
        helper.parent.mkdir(parents=True)
        helper.write_bytes(Path(control.__file__).read_bytes())
        job = manifest()["jobs"][0]
        literals = ["$(touch injected)", "single ' and double \"", "space path"]
        job["argv"] = [sys.executable, "-c", "import json,sys; print(json.dumps(sys.argv[1:]))", *literals]
        packet = {"workspace": str(self.root), "helper": control.HELPER_PATH,
                  "sha256": control.sha256(helper), "job": job}
        output = io.StringIO()
        with mock.patch.object(control.os, "geteuid", return_value=1000), mock.patch.object(sys, "stdin", io.StringIO(json.dumps(packet))), contextlib.redirect_stdout(output):
            exec(compile(control.REMOTE_BOOTSTRAP, "<remote-bootstrap-test>", "exec"), {})
        result = json.loads(output.getvalue())
        self.assertEqual(result["exit_code"], 0)
        self.assertEqual(json.loads(result["output"]["stdout"]["text"]), literals)
        self.assertFalse((self.root / "injected").exists())
        packet["sha256"] = "0" * 64
        with mock.patch.object(control.os, "geteuid", return_value=1000), mock.patch.object(sys, "stdin", io.StringIO(json.dumps(packet))):
            with self.assertRaisesRegex(SystemExit, "does not match"):
                exec(compile(control.REMOTE_BOOTSTRAP, "<remote-bootstrap-test>", "exec"), {})

    @unittest.skipUnless(hasattr(os, "geteuid") and hasattr(os, "symlink"), "requires POSIX")
    def test_remote_bootstrap_rejects_root_and_parent_symlink(self):
        with mock.patch.object(control.os, "geteuid", return_value=0):
            with self.assertRaisesRegex(SystemExit, "normal remote user"):
                exec(compile(control.REMOTE_BOOTSTRAP, "<remote-bootstrap-test>", "exec"), {})
        helper = self.root / control.HELPER_PATH
        helper.parent.mkdir(parents=True)
        helper.write_bytes(Path(control.__file__).read_bytes())
        (self.root / "games").rename(self.root / "real-games")
        (self.root / "games").symlink_to(self.root / "real-games", target_is_directory=True)
        packet = {"workspace": str(self.root), "helper": control.HELPER_PATH,
                  "sha256": control.sha256(helper), "job": manifest()["jobs"][0]}
        with mock.patch.object(control.os, "geteuid", return_value=1000), mock.patch.object(sys, "stdin", io.StringIO(json.dumps(packet))):
            with self.assertRaisesRegex(SystemExit, "symlink"):
                exec(compile(control.REMOTE_BOOTSTRAP, "<remote-bootstrap-test>", "exec"), {})

    def test_dry_run_has_no_mutation_and_execution_requires_receipt(self):
        data = manifest()
        data["jobs"][0]["argv"] = [sys.executable, "-c", "open('marker','w').write('executed')"]
        data["jobs"][0]["writes"] = ["work/W1/marker"]
        code, report = self.invoke(data)
        self.assertEqual(code, 0); self.assertEqual(report["status"], "dry_run")
        self.assertFalse((self.root / "marker").exists())
        self.assertFalse((self.root / ".local-swarm").exists())
        code, _ = self.invoke(data, "jobs", "--execute", "--job", "check")
        self.assertEqual(code, 2); self.assertFalse((self.root / "marker").exists())

    def test_execute_receipt_binds_manifest_and_is_not_overwritten(self):
        data = manifest()
        receipt = ".local-swarm/receipts/test.json"
        code, report = self.invoke(data, "jobs", "--execute", "--job", "check", "--receipt", receipt)
        self.assertEqual(code, 0)
        self.assertEqual(json.loads((self.root / receipt).read_text()), report)
        self.assertEqual(report["manifest_sha256"], control.sha256(self.root / "manifest.json"))
        self.assertEqual(report["results"][0]["allowed_paths"], ["work/W1"])
        self.assertEqual(report["results"][0]["writes"], [])
        self.assertEqual(report["ownership_enforcement"], "declaration_only_not_a_sandbox")
        original = (self.root / receipt).read_bytes()
        code, _ = self.invoke(data, "jobs", "--execute", "--job", "check", "--receipt", receipt)
        self.assertEqual(code, 2)
        self.assertEqual((self.root / receipt).read_bytes(), original)

    def test_execution_requires_explicit_unique_job_selection(self):
        data = manifest()
        for options in [["--execute", "--receipt", ".local-swarm/receipts/no-selection.json"],
                        ["--job", "unknown"], ["--job", "check", "--job", "check"]]:
            with self.subTest(options=options):
                code, report = self.invoke(data, "jobs", *options)
                self.assertEqual(code, 2)
                self.assertEqual(report["status"], "blocked")


class CleanupTests(TemporaryWorkspace):
    def setUp(self):
        super().setUp()
        subprocess.run(["git", "init", "--quiet", str(self.root)], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (self.root / "scratch/generated").mkdir(parents=True)

    def cleanup_manifest(self, name="scratch/generated/cache.bin", content=b"generated-cache"):
        file = self.root / name
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(content)
        return {"schema_version": 1, "operation": "quarantine", "generated_roots": ["scratch/generated"],
                "files": [{"path": name, "classification": "generated", "bytes": len(content),
                           "sha256": hashlib.sha256(content).hexdigest()}]}

    def test_dry_run_preserves_files_then_quarantine_receipt_restores_identity(self):
        data = self.cleanup_manifest()
        source = self.root / data["files"][0]["path"]
        code, report = self.invoke(data, "cleanup")
        self.assertEqual(code, 0); self.assertTrue(source.exists())
        self.assertFalse((self.root / ".local-swarm").exists())
        receipt = ".local-swarm/receipts/quarantine.json"
        code, report = self.invoke(data, "cleanup", "--execute", "--receipt", receipt)
        self.assertEqual(code, 0); self.assertFalse(source.exists())
        self.assertEqual(report["freed_bytes"], 0)
        self.assertEqual(len(report["moved"]), 1)
        moved = report["moved"][0]
        saved = self.root / moved["quarantine_path"]
        self.assertEqual(control.sha256(saved), data["files"][0]["sha256"])
        self.assertEqual(json.loads((self.root / receipt).read_text()), report)
        saved.rename(source)
        self.assertEqual(source.read_bytes(), b"generated-cache")

    def test_tracked_and_untracked_source_files_are_protected(self):
        data = self.cleanup_manifest()
        subprocess.run(["git", "-C", str(self.root), "add", data["files"][0]["path"]], check=True)
        with self.assertRaisesRegex(control.ControlError, "protected"):
            control.plan_cleanup(data, self.root)
        data = self.cleanup_manifest("scratch/generated/source.py", b"print('retain')")
        with self.assertRaisesRegex(control.ControlError, "protected"):
            control.plan_cleanup(data, self.root)

    def test_source_trees_protected_even_for_untracked_binary(self):
        data = self.cleanup_manifest("games/yuga-native/assets/original.glb")
        data["generated_roots"] = ["games/yuga-native/assets"]
        with self.assertRaisesRegex(control.ControlError, "source trees"):
            control.plan_cleanup(data, self.root)
        data = self.cleanup_manifest("GaMeS/yuga-native/assets/original.glb")
        data["generated_roots"] = ["GaMeS/yuga-native/assets"]
        with self.assertRaisesRegex(control.ControlError, "source trees"):
            control.plan_cleanup(data, self.root)

    def test_case_variant_of_tracked_binary_is_never_quarantined(self):
        original = self.cleanup_manifest("scratch/generated/asset.bin", b"tracked-source")
        original_path = self.root / original["files"][0]["path"]
        subprocess.run(["git", "-C", str(self.root), "add", original["files"][0]["path"]], check=True)
        variant = self.cleanup_manifest("scratch/generated/ASSET.BIN", b"tracked-source")
        with self.assertRaisesRegex(control.ControlError, "tracked/source"):
            control.quarantine(variant, self.root)
        self.assertEqual(original_path.read_bytes(), b"tracked-source")
        self.assertTrue((self.root / variant["files"][0]["path"]).exists())
        self.assertFalse((self.root / ".local-swarm").exists())

    def test_case_variant_of_gitlink_ancestry_is_protected(self):
        data = self.cleanup_manifest("scratch/generated/MODULE/source.bin", b"source")
        with mock.patch.object(control, "tracked_paths", return_value={"scratch/generated/module"}):
            with self.assertRaisesRegex(control.ControlError, "tracked/source"):
                control.quarantine(data, self.root)
        self.assertTrue((self.root / data["files"][0]["path"]).exists())
        self.assertFalse((self.root / ".local-swarm").exists())

    def test_nested_git_tracked_binary_is_protected(self):
        nested = self.root / "scratch/generated/nested"
        subprocess.run(["git", "init", "--quiet", str(nested)], check=True, capture_output=True)
        data = self.cleanup_manifest("scratch/generated/nested/source.bin")
        subprocess.run(["git", "-C", str(nested), "add", "source.bin"], check=True)
        self.assertNotIn(data["files"][0]["path"], control.tracked_paths(self.root))
        with self.assertRaisesRegex(control.ControlError, "nested repositories"):
            control.quarantine(data, self.root)
        self.assertTrue((self.root / data["files"][0]["path"]).exists())
        self.assertFalse((self.root / ".local-swarm").exists())

    def test_actual_submodule_gitlink_and_gitfile_protect_inner_binary(self):
        origin = self.root / "source-origin"
        subprocess.run(["git", "init", "--quiet", str(origin)], check=True, capture_output=True)
        (origin / "source.bin").write_bytes(b"submodule-source")
        subprocess.run(["git", "-C", str(origin), "add", "source.bin"], check=True)
        subprocess.run(["git", "-C", str(origin), "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "--quiet", "-m", "test fixture"], check=True, capture_output=True)
        module = "scratch/generated/module"
        subprocess.run(["git", "-C", str(self.root), "-c", "protocol.file.allow=always", "submodule", "add", "--quiet", str(origin), module], check=True, capture_output=True)
        data = self.cleanup_manifest(module + "/source.bin", b"submodule-source")
        self.assertIn(module, control.tracked_paths(self.root))
        self.assertTrue((self.root / module / ".git").is_file())
        with self.assertRaisesRegex(control.ControlError, "tracked/source"):
            control.quarantine(data, self.root)
        with mock.patch.object(control, "tracked_paths", return_value=set()):
            with self.assertRaisesRegex(control.ControlError, "nested repositories"):
                control.plan_cleanup(data, self.root)
        self.assertTrue((self.root / data["files"][0]["path"]).exists())
        self.assertFalse((self.root / ".local-swarm").exists())

    def test_control_state_protected_and_no_broad_roots(self):
        for root in [".", "..", "/tmp", ".git", ".local-swarm/receipts", "scratch/*"]:
            data = self.cleanup_manifest(); data["generated_roots"] = [root]
            with self.subTest(root=root), self.assertRaises(control.ControlError):
                control.plan_cleanup(data, self.root)

    def test_outside_inventory_duplicate_directory_and_unclassified_rejected(self):
        base = self.cleanup_manifest()
        candidates = []
        data = copy.deepcopy(base); data["files"][0]["path"] = "scratch/other.bin"; candidates.append(data)
        data = copy.deepcopy(base); data["files"] *= 2; candidates.append(data)
        data = copy.deepcopy(base); data["files"][0]["classification"] = "original-art"; candidates.append(data)
        data = copy.deepcopy(base); data["files"][0]["path"] = "scratch/generated/subdir"; candidates.append(data)
        (self.root / "scratch/generated/subdir").mkdir()
        for data in candidates:
            with self.subTest(data=data), self.assertRaises(control.ControlError):
                control.plan_cleanup(data, self.root)

    def test_identity_change_blocks_all_moves(self):
        data = self.cleanup_manifest()
        source = self.root / data["files"][0]["path"]
        source.write_bytes(b"changed")
        with self.assertRaisesRegex(control.ControlError, "changed"):
            control.quarantine(data, self.root)
        self.assertTrue(source.exists())
        self.assertFalse((self.root / ".local-swarm").exists())

    @unittest.skipUnless(hasattr(os, "symlink"), "requires symlinks")
    def test_cleanup_rejects_symlink_file_and_receipt_parent(self):
        data = self.cleanup_manifest()
        source = self.root / data["files"][0]["path"]
        original = self.root / "original.bin"; source.rename(original)
        source.symlink_to(original)
        with self.assertRaisesRegex(control.ControlError, "symlink"):
            control.plan_cleanup(data, self.root)
        (self.root / ".local-swarm").symlink_to(self.root / "scratch", target_is_directory=True)
        code, report = self.invoke(manifest(), "jobs", "--execute", "--job", "check", "--receipt", ".local-swarm/receipts/bad.json")
        self.assertEqual(code, 2)
        self.assertEqual(report["status"], "blocked")

    def test_cleanup_requires_git_root_and_valid_record_types(self):
        data = self.cleanup_manifest()
        with self.assertRaisesRegex(control.ControlError, "Git root"):
            control.tracked_paths(self.root / "scratch")
        for changed in [None, [], {**data, "files": [None]}, {**data, "schema_version": True}]:
            with self.subTest(data=changed):
                code, report = self.invoke(changed, "cleanup")
                self.assertEqual(code, 2)
                self.assertEqual(report["status"], "blocked")


if __name__ == "__main__":
    unittest.main()
