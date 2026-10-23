#!/usr/bin/env python3
"""Run one command under a nonblocking, cooperative Linux/WSL file lock.

This is not a GPU reservation: unrelated commands, requests sent directly to a
model daemon, and resident model weights are outside the lock's control. Every
participating client must use the same lock file on a filesystem with flock
support. The command inherits the locked descriptor so wrapper death does not
release its lock. Inheriting descendants retain it too, until they close that
descriptor; commands must preserve it and wait for their GPU work to finish.
Daemonization or closing inherited descriptors breaks that lifecycle guarantee.
The lock file is deliberately never removed.
"""

from __future__ import annotations

import argparse
import errno
import os
import stat
import subprocess
import sys

try:
    import fcntl
except ImportError:  # The supported platforms are Linux and WSL.
    fcntl = None


BUSY_EXIT = 75


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    parser = argparse.ArgumentParser(
        description=(
            "Run a command under a cooperative, nonblocking file lock. "
            "This does not reserve a GPU or control a model daemon."
        ),
        usage="%(prog)s --lock ABSOLUTE_PATH -- command [argument ...]",
    )
    parser.add_argument("--lock", required=True, help="shared absolute lock-file path")
    if "--" not in argv:
        # Retain argparse's standard --help behavior.
        if "--help" in argv or "-h" in argv:
            parser.parse_args(argv)
        parser.error("a command after the literal -- separator is required")
    separator = argv.index("--")
    options = parser.parse_args(argv[:separator])
    command = argv[separator + 1 :]
    if not command or not command[0]:
        parser.error("a nonempty command after -- is required")
    if not os.path.isabs(options.lock):
        parser.error("--lock must be an absolute path")
    if fcntl is None:
        print("gpu_job: fcntl is unavailable; use Linux or WSL", file=sys.stderr)
        return 69

    flags = os.O_RDWR | os.O_CREAT | os.O_CLOEXEC | os.O_NOFOLLOW
    try:
        descriptor = os.open(options.lock, flags, 0o600)
    except OSError as error:
        print(f"gpu_job: cannot open lock file: {error}", file=sys.stderr)
        return 73

    try:
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            print("gpu_job: lock path must be a regular file", file=sys.stderr)
            return 73
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as error:
            if error.errno in (errno.EACCES, errno.EAGAIN):
                print("gpu_job: lock is busy; command was not started", file=sys.stderr)
                return BUSY_EXIT
            print(f"gpu_job: cannot acquire lock: {error}", file=sys.stderr)
            return 73

        try:
            result = subprocess.run(
                command, shell=False, check=False, pass_fds=(descriptor,)
            )
        except FileNotFoundError as error:
            print(f"gpu_job: command not found: {error}", file=sys.stderr)
            return 127
        except OSError as error:
            print(f"gpu_job: cannot start command: {error}", file=sys.stderr)
            return 126
        # subprocess uses a negative code for signals; the CLI exposes the
        # conventional shell exit status without invoking a shell.
        return result.returncode if result.returncode >= 0 else 128 - result.returncode
    finally:
        # flock ownership follows the shared open-file description. Never issue
        # LOCK_UN: it would also unlock a still-running inheriting descendant.
        # Closing our copy releases ownership only after every copy is closed.
        os.close(descriptor)


if __name__ == "__main__":
    raise SystemExit(main())
