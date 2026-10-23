"""Behavior tests for the cooperative lock; no model or GPU is required."""

from __future__ import annotations

import ctypes
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest


SCRIPT = Path(__file__).resolve().with_name("gpu_job.py")


@unittest.skipUnless(sys.platform.startswith("linux"), "Linux/WSL flock tests")
class GpuJobTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Lifecycle tests intentionally orphan a command. Adopt it here, so this
        # test process can reap it instead of leaving that obligation to PID 1.
        cls.libc = ctypes.CDLL(None, use_errno=True)
        previous = ctypes.c_int()
        if cls.libc.prctl(37, ctypes.byref(previous), 0, 0, 0) != 0:
            raise OSError(ctypes.get_errno(), "PR_GET_CHILD_SUBREAPER failed")
        if cls.libc.prctl(36, 1, 0, 0, 0) != 0:
            raise OSError(ctypes.get_errno(), "PR_SET_CHILD_SUBREAPER failed")
        cls.addClassCleanup(cls.restore_subreaper, previous.value)

    @classmethod
    def restore_subreaper(cls, previous):
        if cls.libc.prctl(36, previous, 0, 0, 0) != 0:
            raise OSError(ctypes.get_errno(), "restoring child-subreaper flag failed")

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.lock = self.root / "gpu.lock"
        self.jobs = []
        self.owned_groups = set()
        self.owned_pids = set()
        self.release_paths = []
        self.addCleanup(self.cleanup_jobs)

    def start_job(self, *command, capture=True):
        process = subprocess.Popen(
            [sys.executable, str(SCRIPT), "--lock", str(self.lock), "--", *command],
            stdout=subprocess.PIPE if capture else subprocess.DEVNULL,
            stderr=subprocess.PIPE if capture else subprocess.DEVNULL,
            text=True, start_new_session=True,
        )
        self.jobs.append(process)
        self.owned_groups.add(process.pid)
        self.owned_pids.add(process.pid)
        return process

    def run_job(self, *command):
        process = self.start_job(*command)
        stdout, stderr = process.communicate(timeout=10)
        return subprocess.CompletedProcess(process.args, process.returncode, stdout, stderr)

    def blocking_child(self, release):
        self.release_paths.append(release)
        return (
            "from pathlib import Path; import os,sys,time; "
            "ready,release=map(Path,sys.argv[1:]); ready.write_text(str(os.getpid())); "
            "deadline=time.monotonic()+8\n"
            "while not release.exists():\n"
            " if time.monotonic()>deadline: raise SystemExit(9)\n"
            " time.sleep(0.01)\n"
        )

    def await_ready(self, ready):
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            try:
                pid = int(ready.read_text())
            except (FileNotFoundError, ValueError):
                time.sleep(0.01)
                continue
            self.owned_pids.add(pid)
            return pid
        self.fail("test child did not record its PID/start")

    def harvest_and_reap(self):
        # Each job owns a distinct process group. Subreaper adoption makes its
        # orphaned descendants waitable here; never reap unrelated children.
        wrappers = {process.pid: process for process in self.jobs}
        for process in self.jobs:
            process.poll()
        active_groups = set()
        for group in self.owned_groups:
            while True:
                try:
                    pid, status = os.waitpid(-group, os.WNOHANG)
                except ChildProcessError:
                    break
                if pid == 0:
                    active_groups.add(group)
                    break
                self.owned_pids.add(pid)
                if pid in wrappers:
                    wrappers[pid].returncode = os.waitstatus_to_exitcode(status)
        return active_groups

    def cleanup_jobs(self):
        for release in self.release_paths:
            release.touch()
        remaining = set()
        try:
            # Let released commands finish, then signal only sessions created
            # by these tests. Reap adopted descendants after wrapper death too.
            for termination, duration in ((None, 0.5), (signal.SIGTERM, 1), (signal.SIGKILL, 1)):
                deadline = time.monotonic() + duration
                while True:
                    remaining = self.harvest_and_reap()
                    if not remaining:
                        return
                    if termination is not None:
                        for group in remaining:
                            try:
                                os.killpg(group, termination)
                            except ProcessLookupError:
                                pass
                    if time.monotonic() >= deadline:
                        break
                    time.sleep(0.01)
            self.fail(f"test-owned groups were not reaped: {sorted(remaining)}")
        finally:
            for process in self.jobs:
                for stream in (process.stdout, process.stderr):
                    if stream is not None:
                        stream.close()

    def test_second_concurrent_child_does_not_run(self):
        ready = self.root / "ready"
        release = self.root / "release"
        second_marker = self.root / "second-ran"
        child = self.blocking_child(release)
        first = self.start_job(sys.executable, "-c", child, str(ready), str(release))
        try:
            self.await_ready(ready)
            second = self.run_job(
                sys.executable, "-c",
                "from pathlib import Path; import sys; Path(sys.argv[1]).write_text('ran')",
                str(second_marker),
            )
            self.assertEqual(second.returncode, 75, second.stderr)
            self.assertIn("command was not started", second.stderr)
            self.assertFalse(second_marker.exists())
            self.assertIsNone(first.poll(), "first command should still hold lock")
            release.write_text("release")
            stdout, stderr = first.communicate(timeout=5)
            self.assertEqual(first.returncode, 0, stdout + stderr)
            self.assertTrue(self.lock.exists(), "lock file must never be unlinked")
        finally:
            release.touch()

    def test_failed_child_exit_is_preserved_and_releases_lock(self):
        failed = self.run_job(sys.executable, "-c", "raise SystemExit(37)")
        self.assertEqual(failed.returncode, 37, failed.stderr)
        succeeded = self.run_job(sys.executable, "-c", "print('next command ran')")
        self.assertEqual(succeeded.returncode, 0, succeeded.stderr)
        self.assertEqual(succeeded.stdout.strip(), "next command ran")

    def test_killed_wrapper_keeps_lock_until_child_finishes(self):
        ready = self.root / "surviving-child-ready"
        release = self.root / "surviving-child-release"
        marker = self.root / "second-child-ran"
        child = self.blocking_child(release)
        first = self.start_job(
            sys.executable, "-c", child, str(ready), str(release), capture=False
        )
        try:
            self.await_ready(ready)
            first.kill()  # SIGKILL only the wrapper; its command stays alive.
            self.assertEqual(first.wait(timeout=5), -signal.SIGKILL)
            second = self.run_job(
                sys.executable, "-c",
                "from pathlib import Path; import sys; Path(sys.argv[1]).touch()",
                str(marker),
            )
            self.assertEqual(second.returncode, 75, second.stderr)
            self.assertFalse(marker.exists())
            release.write_text("release")
            deadline = time.monotonic() + 5
            while True:
                next_result = self.run_job(sys.executable, "-c", "raise SystemExit(0)")
                if next_result.returncode != 75 or time.monotonic() >= deadline:
                    break
                time.sleep(0.01)
            self.assertEqual(next_result.returncode, 0, next_result.stderr)
        finally:
            release.touch()

    def test_inheriting_descendant_keeps_lock_after_command_exits(self):
        ready = self.root / "descendant-ready"
        release = self.root / "descendant-release"
        child = self.blocking_child(release)
        spawner = (
            "import subprocess,sys; "
            "subprocess.Popen([sys.executable,'-c',*sys.argv[1:]], "
            "close_fds=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)"
        )
        try:
            first = self.run_job(sys.executable, "-c", spawner, child, str(ready), str(release))
            self.assertEqual(first.returncode, 0, first.stderr)
            self.await_ready(ready)
            second = self.run_job(sys.executable, "-c", "raise SystemExit(99)")
            self.assertEqual(second.returncode, 75, second.stderr)
            release.write_text("release")
            deadline = time.monotonic() + 5
            while True:
                next_result = self.run_job(sys.executable, "-c", "raise SystemExit(0)")
                if next_result.returncode != 75 or time.monotonic() >= deadline:
                    break
                time.sleep(0.01)
            self.assertEqual(next_result.returncode, 0, next_result.stderr)
        finally:
            release.touch()

    def test_arguments_remain_literal_without_shell_execution(self):
        marker = self.root / "unexpected-shell-execution"
        arguments = [
            "space separated argument",
            f"$(touch {marker})",
            f"`touch {marker}`",
            f"; touch {marker}",
            "$HOME",
            "*.txt",
            "--",
        ]
        result = self.run_job(
            sys.executable, "-c", "import json,sys; print(json.dumps(sys.argv[1:]))",
            *arguments,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), arguments)
        self.assertFalse(marker.exists())

    def test_missing_command_is_rejected(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--lock", str(self.lock), "--"],
            capture_output=True, text=True, timeout=5,
        )
        self.assertEqual(result.returncode, 2)
        self.assertFalse(self.lock.exists())

    def test_separator_is_required(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--lock", str(self.lock), sys.executable],
            capture_output=True, text=True, timeout=5,
        )
        self.assertEqual(result.returncode, 2)
        self.assertFalse(self.lock.exists())

    def test_relative_lock_is_rejected(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--lock", "relative.lock", "--",
             sys.executable, "-c", "raise SystemExit(99)"],
            capture_output=True, text=True, timeout=5, cwd=self.root,
        )
        self.assertEqual(result.returncode, 2)
        self.assertFalse((self.root / "relative.lock").exists())

    def test_missing_executable_releases_lock(self):
        result = self.run_job(str(self.root / "nonexistent-executable"))
        self.assertEqual(result.returncode, 127)
        next_result = self.run_job(sys.executable, "-c", "raise SystemExit(0)")
        self.assertEqual(next_result.returncode, 0, next_result.stderr)

    def test_signal_exit_uses_conventional_status(self):
        result = self.run_job(
            sys.executable, "-c", "import os,signal; os.kill(os.getpid(), signal.SIGTERM)"
        )
        self.assertEqual(result.returncode, 143, result.stderr)
        next_result = self.run_job(sys.executable, "-c", "raise SystemExit(0)")
        self.assertEqual(next_result.returncode, 0, next_result.stderr)

    def test_symlink_lock_is_rejected_without_touching_target(self):
        target = self.root / "target"
        target.write_text("untouched")
        self.lock.symlink_to(target)
        result = self.run_job(sys.executable, "-c", "raise SystemExit(99)")
        self.assertEqual(result.returncode, 73, result.stderr)
        self.assertEqual(target.read_text(), "untouched")

    def test_missing_parent_is_reported_without_creating_it(self):
        self.lock = self.root / "missing-parent" / "gpu.lock"
        result = self.run_job(sys.executable, "-c", "raise SystemExit(99)")
        self.assertEqual(result.returncode, 73, result.stderr)
        self.assertFalse(self.lock.parent.exists())


if __name__ == "__main__":
    unittest.main()
