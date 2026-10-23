#!/usr/bin/env python3
"""Explicit job execution and recoverable generated-output quarantine.

Path ownership is a declaration, not an OS sandbox for arbitrary child programs.
No model, cloud provider, download or SSH target is selected automatically.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import shlex
import shutil
import signal
import stat
import subprocess
import sys
import threading
import time
import uuid

ROLES = {"W1": "QA", "W2": "UI", "W3": "hero", "W4": "world", "W5": "motion", "W6": "models"}
PROTECTED = {".git", ".ssh", ".gnupg", ".aws", ".azure", ".agents", ".claude", ".kimi", ".codex", ".kimi-code", ".config", ".local"}
PROTECTED_FILES = {"auth.json", "credentials", "credentials.json", "id_rsa", "id_ed25519", "token", "tokens.json"}
SOURCE_SUFFIXES = {".py", ".gd", ".gdshader", ".ts", ".tsx", ".js", ".cs", ".c", ".cpp", ".h", ".blend", ".blend1", ".md", ".toml", ".yml", ".yaml"}
SOURCE_ROOTS = {"games", "apps", "packages", "docs", "tools", "src", "source", "assets", "art", "models", "resources"}
LOG_LIMIT = 64 * 1024
HELPER_PATH = "games/yuga-native/tools/local-swarm/control.py"
GPU_HELPER = "games/yuga-native/tools/local-swarm/gpu_job.py"


class ControlError(ValueError):
    pass


def relative_path(value, allow_root=False):
    if allow_root and value == ".":
        return "."
    if not isinstance(value, str) or not value or "\\" in value or "\x00" in value:
        raise ControlError("path must be a literal relative POSIX path")
    parts = value.split("/")
    if value.startswith("/") or any(p in ("", ".", "..") for p in parts):
        raise ControlError("absolute paths, empty components and traversal are forbidden")
    if any(c in value for c in "*?[]:"):
        raise ControlError("globs and drive syntax are forbidden")
    if any(p.casefold() in PROTECTED or p.casefold() in PROTECTED_FILES or p.casefold() == ".env" or p.casefold().startswith(".env.") for p in parts):
        raise ControlError("protected path")
    return value


def inside(root, value, allow_root=False):
    value = relative_path(value, allow_root)
    candidate = root if value == "." else root / value
    current = root
    for part in (() if value == "." else PurePosixPath(value).parts):
        current = current / part
        if current.is_symlink():
            raise ControlError("symlinks are not allowed in controlled paths")
    if not candidate.resolve().is_relative_to(root):
        raise ControlError("path escapes workspace")
    return candidate


def workspace(value):
    p = Path(value).expanduser().resolve(strict=True)
    if not p.is_dir() or p == Path(p.anchor):
        raise ControlError("workspace must be an existing non-root directory")
    return p


def timeout_value(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ControlError("timeout must be numeric")
    if not math.isfinite(value) or not 0.05 <= value <= 3600:
        raise ControlError("timeout must be between 0.05 and 3600 seconds")
    return float(value)


def checked_argv(value):
    if not isinstance(value, list) or not value or not all(isinstance(x, str) and "\x00" not in x for x in value):
        raise ControlError("argv must be a nonempty list of literal strings")
    if not value[0] or sum(len(x.encode()) for x in value) > 32768:
        raise ControlError("empty executable or argv exceeds 32 KiB")
    return value


def overlaps(a, b):
    # Conservatively reject case-only aliases even on case-sensitive hosts.
    a, b = a.casefold(), b.casefold()
    return a == b or a.startswith(b + "/") or b.startswith(a + "/")


def validate_manifest(data, root):
    if not isinstance(data, dict) or type(data.get("schema_version")) is not int or data["schema_version"] != 1 or "fallback" not in data or data["fallback"] is not None:
        raise ControlError("schema_version 1 and fallback:null are required")
    workers = data.get("workers")
    if not isinstance(workers, list) or len(workers) != 6:
        raise ControlError("exactly six worker declarations are required")
    owners, seen = [], set()
    for worker in workers:
        if not isinstance(worker, dict):
            raise ControlError("each worker must be an object")
        who = worker.get("id")
        if not isinstance(who, str) or who in seen or who not in ROLES or worker.get("role") != ROLES[who]:
            raise ControlError("worker IDs and roles must match W1 through W6")
        seen.add(who)
        paths = worker.get("allowed_paths")
        if not isinstance(paths, list) or not paths:
            raise ControlError("each worker needs explicit allowed_paths")
        for value in paths:
            value = relative_path(value)
            if value.split("/")[0].casefold() == ".local-swarm":
                raise ControlError("worker ownership must not include runner control state")
            inside(root, value)
            if any(overlaps(value, prior) for prior, _ in owners):
                raise ControlError("overlapping ownership declarations")
            owners.append((value, who))
    targets = data.get("ssh_targets", {})
    if not isinstance(targets, dict):
        raise ControlError("ssh_targets must be an object")
    for name, target in targets.items():
        if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}", name) or name == "local":
            raise ControlError("SSH target must be a named config alias")
        if not isinstance(target, dict):
            raise ControlError("each SSH target must be an object")
        remote_root = target.get("workspace")
        if not isinstance(remote_root, str) or not remote_root.startswith("/") or remote_root == "/" or ".." in remote_root.split("/") or "\x00" in remote_root:
            raise ControlError("SSH workspace must be an explicit absolute non-root POSIX path")
    jobs = data.get("jobs")
    if not isinstance(jobs, list) or not jobs:
        raise ControlError("jobs must be a nonempty list")
    ids = set()
    for job in jobs:
        if not isinstance(job, dict):
            raise ControlError("each job must be an object")
        name = job.get("id")
        if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9_.-]{1,80}", name) or name in ids:
            raise ControlError("jobs need unique simple IDs")
        ids.add(name)
        if not isinstance(job.get("worker"), str) or job["worker"] not in ROLES:
            raise ControlError("job needs a declared worker")
        writes = job.get("writes")
        if not isinstance(writes, list):
            raise ControlError("job needs an explicit writes list; use [] for read-only work")
        for value in writes:
            value = relative_path(value)
            inside(root, value)
            if not any(who == job["worker"] and (value == prior or value.startswith(prior + "/")) for prior, who in owners):
                raise ControlError("job writes must be within its worker's exclusive paths")
        checked_argv(job.get("argv"))
        timeout_value(job.get("timeout_seconds"))
        cwd = relative_path(job.get("cwd"), allow_root=True)
        if type(job.get("gpu", False)) is not bool:
            raise ControlError("gpu must be boolean")
        target = job.get("target", "local")
        if not isinstance(target, str) or (target != "local" and target not in targets):
            raise ControlError("unknown SSH target; no implicit target is allowed")
        if target == "local":
            if not inside(root, cwd, True).is_dir():
                raise ControlError("local cwd does not exist")
        elif job.get("gpu"):
            raise ControlError("SSH targets are CPU workers; remote GPU jobs are not implemented")
    return data


def run_process(argv, cwd, timeout, input_bytes=None, output_limit=LOG_LIMIT):
    """Bound retained output; terminate the foreground process group on POSIX timeout."""
    started = time.monotonic()
    kwargs = {"shell": False, "cwd": str(cwd), "stdout": subprocess.PIPE,
              "stderr": subprocess.PIPE, "stdin": subprocess.PIPE if input_bytes is not None else subprocess.DEVNULL}
    if os.name == "posix":
        kwargs["start_new_session"] = True
    try:
        child = subprocess.Popen(argv, **kwargs)
    except OSError as error:
        return {"status": "launch_failed", "exit_code": 127 if isinstance(error, FileNotFoundError) else 126,
                "error_type": type(error).__name__, "elapsed_seconds": time.monotonic() - started}
    streams = {}
    def drain(label, stream):
        kept = bytearray(); count = 0
        while chunk := stream.read(8192):
            count += len(chunk)
            kept.extend(chunk[:max(0, output_limit - len(kept))])
        streams[label] = {"text": kept.decode("utf-8", errors="replace"), "bytes_seen": count,
                          "truncated": count > output_limit}
        stream.close()
    readers = [threading.Thread(target=drain, args=(label, stream), daemon=True)
               for label, stream in [("stdout", child.stdout), ("stderr", child.stderr)]]
    for reader in readers:
        reader.start()
    if input_bytes is not None:
        def write_input():
            try:
                child.stdin.write(input_bytes); child.stdin.close()
            except (OSError, ValueError):
                pass
        threading.Thread(target=write_input, daemon=True).start()
    timed_out = interrupted = False
    try:
        child.wait(timeout=timeout)
    except (subprocess.TimeoutExpired, KeyboardInterrupt) as error:
        timed_out = isinstance(error, subprocess.TimeoutExpired)
        interrupted = not timed_out
        if os.name == "posix":
            try:
                os.killpg(child.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        else:
            child.kill()
        child.wait()
    for reader in readers:
        reader.join(timeout=2)
    exit_code = 124 if timed_out else (130 if interrupted else (child.returncode if child.returncode >= 0 else 128 - child.returncode))
    return {"status": "timed_out" if timed_out else ("interrupted" if interrupted else ("passed" if exit_code == 0 else "failed")),
            "exit_code": exit_code, "child_returncode": child.returncode,
            "elapsed_seconds": time.monotonic() - started,
            "output": {key: streams.get(key, {"text": "", "incomplete": True}) for key in ["stdout", "stderr"]}}


def execute_local(job, root):
    cwd = inside(root, job["cwd"], True)
    if not cwd.is_dir():
        raise ControlError("cwd no longer exists")
    for path in job.get("writes", []):
        inside(root, path)
    argv = checked_argv(job["argv"])
    if job.get("gpu"):
        helper = inside(root, GPU_HELPER)
        if not helper.is_file():
            raise ControlError("existing gpu_job.py is required for GPU jobs")
        lock_parent = inside(root, ".local-swarm")
        lock_parent.mkdir(exist_ok=True)
        argv = [sys.executable, str(helper), "--lock", str(lock_parent / "gpu.lock"), "--", *argv]
    return run_process(argv, cwd, timeout_value(job["timeout_seconds"]))


REMOTE_BOOTSTRAP = """import hashlib,importlib.util,json,os,pathlib,sys
if os.geteuid()==0:
 raise SystemExit('use a normal remote user, not root')
p=json.load(sys.stdin)
r=pathlib.Path(p['workspace']).resolve(strict=True)
h=r/p['helper']
if r==pathlib.Path('/') or not h.resolve().is_relative_to(r):
 raise SystemExit('invalid remote helper path')
current=r
for part in pathlib.PurePosixPath(p['helper']).parts:
 current=current/part
 if current.is_symlink():
  raise SystemExit('remote helper symlink is forbidden')
if hashlib.sha256(h.read_bytes()).hexdigest()!=p['sha256']:
 raise SystemExit('remote helper does not match the local source')
s=importlib.util.spec_from_file_location('qualified_yuga_control',h)
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
result=m.execute_local(p['job'],m.workspace(str(r)))
print(json.dumps(result,allow_nan=False))
"""


def execute_ssh(job, target, allow_ssh):
    if not allow_ssh:
        raise ControlError("SSH execution requires explicit --allow-ssh")
    if shutil.which("ssh") is None:
        raise ControlError("OS ssh client is unavailable")
    payload = {"workspace": target["workspace"], "helper": HELPER_PATH,
               "sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), "job": job}
    # SSH uses a remote shell for this fixed bootstrap. Job argv/cwd never enter that string.
    command = ["ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=yes",
               "-o", "ConnectTimeout=10", "-o", "ServerAliveInterval=10",
               "-o", "ServerAliveCountMax=1", job["target"],
               "python3 -c " + shlex.quote(REMOTE_BOOTSTRAP)]
    transport = run_process(command, Path.cwd(), timeout_value(job["timeout_seconds"]) + 20,
                            json.dumps(payload).encode(), output_limit=2 * 1024 * 1024)
    if transport["exit_code"] != 0:
        return {"status": "ssh_transport_failed", "exit_code": transport["exit_code"],
                "remote_outcome": "unknown_inspect_before_retry", "transport": transport}
    try:
        remote = json.loads(transport["output"]["stdout"]["text"])
        if not isinstance(remote, dict) or type(remote.get("exit_code")) is not int:
            raise ValueError("invalid result")
    except (KeyError, ValueError):
        return {"status": "ssh_result_invalid", "exit_code": 70,
                "remote_outcome": "unknown_inspect_before_retry", "transport": transport}
    return {"status": remote.get("status", "unknown"), "exit_code": remote["exit_code"], "remote": remote}


def execute_jobs(data, root, selected, allow_ssh=False):
    known = {job["id"]: job for job in data["jobs"]}
    if not selected or len(selected) != len(set(selected)) or any(x not in known for x in selected):
        raise ControlError("select one or more unique existing job IDs")
    jobs = [known[name] for name in selected]
    if any(j.get("target", "local") != "local" for j in jobs) and not allow_ssh:
        raise ControlError("SSH jobs require --allow-ssh before any batch execution")
    results = []
    workers = {worker["id"]: worker for worker in data["workers"]}
    for job in jobs:
        if job.get("target", "local") == "local":
            result = execute_local(job, root)
        else:
            result = execute_ssh(job, data["ssh_targets"][job["target"]], allow_ssh)
        results.append({"id": job["id"], "worker": job["worker"], "argv": job["argv"],
                        "cwd": job["cwd"], "target": job.get("target", "local"),
                        "allowed_paths": workers[job["worker"]]["allowed_paths"], "writes": job["writes"], **result})
        if result["exit_code"] != 0:
            break
    return {"status": "passed" if all(x["exit_code"] == 0 for x in results) else "failed",
            "results": results, "not_started": selected[len(results):]}


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def tracked_paths(root):
    try:
        top = subprocess.check_output(["git", "-C", str(root), "rev-parse", "--show-toplevel"], stderr=subprocess.PIPE, text=True, timeout=10).strip()
        if Path(top).resolve() != root:
            raise ControlError("cleanup workspace must be the Git root")
        raw = subprocess.check_output(["git", "-C", str(root), "ls-files", "-z", "--cached"], stderr=subprocess.PIPE, timeout=10)
    except (OSError, subprocess.SubprocessError) as error:
        raise ControlError("Git tracking state is unavailable; cleanup is blocked") from error
    return set(raw.decode("utf-8", errors="strict").split("\x00"))


def plan_cleanup(data, root):
    if not isinstance(data, dict) or type(data.get("schema_version")) is not int or data["schema_version"] != 1 or data.get("operation") != "quarantine":
        raise ControlError("only schema_version 1 quarantine is implemented")
    roots = data.get("generated_roots")
    if not isinstance(roots, list) or not roots:
        raise ControlError("explicit generated_roots required")
    for value in roots:
        relative_path(value); inside(root, value)
        if value.split("/")[0].casefold() in SOURCE_ROOTS or value.casefold().startswith(".local-swarm"):
            raise ControlError("source trees, control receipts, locks and quarantine are protected")
    tracked = {item.casefold() for item in tracked_paths(root) if item}
    files = data.get("files")
    if not isinstance(files, list) or not files:
        raise ControlError("explicit file inventory required")
    plan = []; seen = set()
    for entry in files:
        if not isinstance(entry, dict):
            raise ControlError("each cleanup file must be an object")
        name = relative_path(entry.get("path"))
        if name in seen or not any(name.startswith(prefix + "/") for prefix in roots):
            raise ControlError("duplicate file or file outside generated roots")
        seen.add(name)
        p = inside(root, name)
        folded_name = name.casefold()
        if any(folded_name == item or folded_name.startswith(item + "/") for item in tracked) or p.suffix.lower() in SOURCE_SUFFIXES or entry.get("classification") != "generated":
            raise ControlError("tracked/source/unclassified file is protected")
        # The outer index only records a submodule's gitlink, and does not index
        # an untracked nested repository. Neither makes inner source disposable.
        for parent in p.parents:
            if parent == root:
                break
            git_marker = parent / ".git"
            if git_marker.exists() or git_marker.is_symlink():
                raise ControlError("files inside nested repositories are protected")
        if not p.is_file() or not stat.S_ISREG(p.lstat().st_mode):
            raise ControlError("cleanup accepts existing regular files only")
        if not re.fullmatch(r"[0-9a-f]{64}", str(entry.get("sha256"))) or type(entry.get("bytes")) is not int:
            raise ControlError("each file needs exact SHA-256 and integer byte size")
        if p.stat().st_size != entry["bytes"] or sha256(p) != entry["sha256"]:
            raise ControlError("cleanup source changed or manifest identity is wrong")
        plan.append({"path": name, "bytes": entry["bytes"], "sha256": entry["sha256"]})
    return plan


def quarantine(data, root):
    plan = plan_cleanup(data, root)
    base = inside(root, ".local-swarm/quarantine")
    base.mkdir(parents=True, exist_ok=True)
    run = base / uuid.uuid4().hex
    run.mkdir(mode=0o700)
    moved = []
    result = {"operation": "quarantine", "quarantine_root": str(run.relative_to(root)),
              "status": "passed", "moved": moved, "freed_bytes": 0}
    try:
        for item in plan:
            source = inside(root, item["path"])
            if source.stat().st_size != item["bytes"] or sha256(source) != item["sha256"]:
                raise ControlError("file changed before move")
            destination = run / item["path"]
            destination.parent.mkdir(parents=True, exist_ok=True)
            source.rename(destination)
            moved.append({**item, "quarantine_path": str(destination.relative_to(root))})
    except (OSError, ControlError) as error:
        result.update(status="partial", error_type=type(error).__name__, error=str(error))
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("operation", choices=["jobs", "cleanup"])
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--job", action="append", default=[])
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--allow-ssh", action="store_true")
    parser.add_argument("--receipt", help="new relative receipt path within .local-swarm/receipts/")
    args = parser.parse_args(argv)
    receipt_stream = None
    try:
        root = workspace(args.workspace)
        manifest_bytes = args.manifest.read_bytes()
        data = json.loads(manifest_bytes)
        if args.operation == "jobs":
            validate_manifest(data, root)
            selected = args.job or [job["id"] for job in data["jobs"]]
            by_id = {job["id"]: job for job in data["jobs"]}
            if any(name not in by_id for name in selected) or len(selected) != len(set(selected)):
                raise ControlError("unknown or repeated job ID")
            report = {"operation": "jobs", "status": "dry_run", "selected_jobs": [by_id[name] for name in selected],
                      "ownership_enforcement": "declaration_only_not_a_sandbox", "gpu_jobs": "cooperative_wrapper_only"}
            if args.execute and not args.job:
                raise ControlError("execution requires explicit --job selections")
            if args.execute and any(by_id[name].get("target", "local") != "local" for name in selected) and not args.allow_ssh:
                raise ControlError("execution of remote jobs requires --allow-ssh")
        else:
            if args.job or args.allow_ssh:
                raise ControlError("cleanup is local-only and has no job selections")
            report = {"operation": "quarantine", "status": "dry_run", "files": plan_cleanup(data, root), "freed_bytes": 0}
        if args.execute:
            if not args.receipt or not args.receipt.startswith(".local-swarm/receipts/"):
                raise ControlError("execution requires a new receipt under .local-swarm/receipts/")
            receipt = inside(root, args.receipt)
            receipt.parent.mkdir(parents=True, exist_ok=True)
            receipt_stream = receipt.open("x", encoding="utf-8")
            if args.operation == "jobs":
                report = {"operation": "jobs", "ownership_enforcement": "declaration_only_not_a_sandbox",
                          "gpu_jobs": "cooperative_wrapper_only", **execute_jobs(data, root, args.job, args.allow_ssh)}
            else:
                report = quarantine(data, root)
        report.update(schema_version=1, recorded_at_utc=datetime.now(timezone.utc).isoformat(),
                      workspace=str(root), executed=args.execute,
                      manifest_sha256=hashlib.sha256(manifest_bytes).hexdigest(),
                      runner_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
        serialized = json.dumps(report, indent=2, allow_nan=False) + "\n"
        if receipt_stream:
            receipt_stream.write(serialized); receipt_stream.flush(); os.fsync(receipt_stream.fileno())
        print(serialized, end="")
        return 0 if report["status"] in ("passed", "dry_run") else 1
    except (ControlError, OSError, ValueError) as error:
        report = {"status": "blocked", "error_type": type(error).__name__, "error": str(error)}
        serialized = json.dumps(report, indent=2) + "\n"
        if receipt_stream:
            receipt_stream.write(serialized); receipt_stream.flush()
        print(serialized, end="")
        return 2
    finally:
        if receipt_stream:
            receipt_stream.close()


if __name__ == "__main__":
    raise SystemExit(main())
