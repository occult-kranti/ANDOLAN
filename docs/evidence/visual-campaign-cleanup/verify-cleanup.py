#!/usr/bin/env python3
"""Verify the fixed visual-campaign cleanup plan; removal requires --execute.

Default: read-only dry-run. Exact pushed checkpoint, backup blobs, inventory and
process gates are required before removal. Only the nine frozen paths qualify.
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import sys
from urllib.parse import urlsplit

REPO = Path("/workspace/ANDOLAN")
SCRATCH = Path("/workspace/scratch")
PLAN = SCRATCH / "visual-campaign-cleanup-plan.json"
PLAN_SHA = "b1b45cb0c25f53d8193d80bd7c9a5f8ba72956859fd974ffe5575446c3bda37a"
BASE = "38d11148fe69b184e981164c8a71387c91dc64c5"
REMOTE_REF = "refs/heads/game/yuga-native-production"
CLONES = ("visual-campaign-baseline-project-r2",
          "visual-campaign-candidate-project-r1",
          "visual-campaign-candidate-project-r2")
USERS = ("visual-campaign-baseline-r1-user",
         "visual-campaign-candidate-r1-user",
         "visual-campaign-candidate-r2-user")
ALLOWED = {str(SCRATCH / name) for name in CLONES}
for _name in USERS:
    ALLOWED.add(str(SCRATCH / _name / "cache"))
    ALLOWED.add(str(SCRATCH / _name / "data/godot/app_userdata/YUGA • Confluence/shader_cache"))
# Worker ownership is intentionally broader than removal: a process using an
# old profile's parent/data/log directory might create cache entries shortly.
# These profile parents are never themselves deletion candidates.
PROCESS_OWNERS = ALLOWED | {str(SCRATCH / name) for name in USERS}
# Independently inspected persistent platform daemons. An identity change or
# any other unreadable live process fails closed. Their visibility gap is
# reported, never described as complete open-file visibility.
PLATFORM_DAEMONS = {
    205: ("dockerd", "/usr/local/bin/dockerd", "1636", "0\t0\t0\t0", "1"),
    256: ("containerd", "containerd", "1657", "0\t0\t0\t0", "205"),
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_regular(path):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode):
            raise ValueError("not a regular file: " + str(path))
        with os.fdopen(fd, "rb", closefd=False) as stream:
            return stream.read()
    finally:
        os.close(fd)


def git(*args, timeout=30):
    result = subprocess.run(["git", *args], cwd=REPO, capture_output=True,
                            timeout=timeout, check=False)
    if result.returncode:
        # Do not echo Git stderr or credential-bearing remote URLs.
        raise RuntimeError("Git read failed (exit %d): %s" % (result.returncode, args[0]))
    return result.stdout


def fingerprint(rows):
    values = sorted([r["relative"], r["bytes"], r["mtime_ns"], r["device"], r["inode"]]
                    for r in rows)
    return sha(json.dumps(values, separators=(",", ":")).encode())


def expected_rows(path, inventory):
    for name, source in inventory["inventories"].items():
        owner = SCRATCH / name
        if path == owner or path.is_relative_to(owner):
            result = []
            for old in source["files"]:
                item = Path(old["path"])
                if item.is_relative_to(path):
                    row = dict(old)
                    row["relative"] = str(item.relative_to(path))
                    result.append(row)
            return result
    raise ValueError("path absent from frozen inventory")


def scan_directory(path, expected):
    if str(path) not in ALLOWED or path.resolve() != path:
        raise ValueError("path is outside the exact allowlist or has a symlink parent")
    initial = path.lstat()
    if not stat.S_ISDIR(initial.st_mode) or path.is_symlink():
        raise ValueError("candidate is not a real directory")
    wanted = {r["relative"]: r for r in expected}
    actual = []
    directory_bytes = 0
    for current, dirs, files in os.walk(path, followlinks=False):
        directory = Path(current)
        if directory.is_symlink() or os.path.ismount(directory):
            raise ValueError("symlink or mount point inside candidate")
        directory_bytes += directory.lstat().st_blocks * 512
        for name in dirs + files:
            item = directory / name
            info = item.lstat()
            if stat.S_ISLNK(info.st_mode):
                raise ValueError("new symlink inside candidate")
            if stat.S_ISDIR(info.st_mode):
                continue
            relative = str(item.relative_to(path))
            if not stat.S_ISREG(info.st_mode) or relative not in wanted or info.st_nlink != 1:
                raise ValueError("new/special/hardlinked file inside candidate: " + relative)
            old = wanted[relative]
            row = {"relative": relative, "bytes": info.st_size,
                   "mtime_ns": info.st_mtime_ns, "device": info.st_dev,
                   "inode": info.st_ino, "allocated_bytes": info.st_blocks * 512}
            for key in ("bytes", "mtime_ns", "device", "inode", "allocated_bytes"):
                if row[key] != old[key]:
                    raise ValueError("changed file metadata: " + relative)
            if "sha256" in old and sha(read_regular(item)) != old["sha256"]:
                raise ValueError("changed non-cache contents: " + relative)
            actual.append(row)
    if set(wanted) != {r["relative"] for r in actual}:
        raise ValueError("missing files in candidate")
    return {"file_count": len(actual), "logical_bytes": sum(r["bytes"] for r in actual),
            "regular_allocated_bytes": sum(r["allocated_bytes"] for r in actual),
            "directory_allocated_bytes": directory_bytes,
            "snapshot_fingerprint_sha256": fingerprint(actual),
            "root_device": initial.st_dev, "root_inode": initial.st_ino}


def references_candidate(value):
    value = value.removesuffix(" (deleted)")
    return any(value == root or value.startswith(root + "/") for root in PROCESS_OWNERS)


def inspect_processes():
    result = {"examined": 0, "zombies_skipped": 0, "references": [],
              "unreadable_workers": [], "platform_visibility_gaps": []}
    for process in Path("/proc").glob("[0-9]*"):
        try:
            status = {line.partition(":")[0]: line.partition(":")[2].strip()
                      for line in (process / "status").read_text().splitlines() if ":" in line}
            if status["State"].startswith("Z"):
                result["zombies_skipped"] += 1
                continue
            result["examined"] += 1
            args = (process / "cmdline").read_bytes().split(b"\0")
            pid = int(process.name)
            stat_text = (process / "stat").read_text()
            start = stat_text[stat_text.rfind(")") + 2:].split()[19]
            identity = (status["Name"], args[0].decode(errors="replace"), start,
                        status["Uid"], status["PPid"])
            known_platform = PLATFORM_DAEMONS.get(pid) == identity
            gaps = []
            refs = []
            for arg in args:
                text = arg.decode(errors="replace")
                value = text.partition("=")[2] if text.startswith("--") and "=" in text else text
                if references_candidate(value):
                    refs.append("command argument")
            for key in ("cwd", "root"):
                try:
                    if references_candidate(os.readlink(process / key)):
                        refs.append(key)
                except FileNotFoundError:
                    pass
                except PermissionError:
                    gaps.append(key)
            try:
                for fd in (process / "fd").iterdir():
                    try:
                        if references_candidate(os.readlink(fd)):
                            refs.append("open descriptor")
                    except FileNotFoundError:
                        pass
            except PermissionError:
                gaps.append("fd")
            try:
                for line in (process / "maps").read_text().splitlines():
                    fields = line.split(maxsplit=5)
                    if len(fields) == 6 and references_candidate(fields[5]):
                        refs.append("memory mapping")
            except PermissionError:
                gaps.append("maps")
            try:
                for item in (process / "environ").read_bytes().split(b"\0"):
                    key, _, value = item.partition(b"=")
                    if key in (b"XDG_CACHE_HOME", b"XDG_DATA_HOME", b"XDG_CONFIG_HOME"):
                        if references_candidate(value.decode(errors="replace")):
                            refs.append(key.decode())
            except PermissionError:
                gaps.append("environment")
            if refs:
                result["references"].append({"pid": pid, "name": status["Name"],
                                              "kinds": sorted(set(refs))})
            if gaps:
                item = {"pid": pid, "name": status["Name"], "fields": sorted(set(gaps))}
                if known_platform:
                    item.update(argv0=identity[1], start_ticks=start, uid=status["Uid"],
                                parent_pid=status["PPid"], identity_exact=True)
                    result["platform_visibility_gaps"].append(item)
                else:
                    result["unreadable_workers"].append(item)
        except (FileNotFoundError, ProcessLookupError):
            continue
        except (PermissionError, OSError) as error:
            result["unreadable_workers"].append({"pid": int(process.name),
                                                  "error": type(error).__name__})
    return result


def verify_remote(commit):
    url = git("remote", "get-url", "origin").decode().strip()
    if url.startswith("git@github.com:"):
        host, project = "github.com", url.split(":", 1)[1]
    else:
        parsed = urlsplit(url)
        host, project = parsed.hostname, parsed.path.lstrip("/")
    if host != "github.com" or project.removesuffix(".git") != "occult-kranti/ANDOLAN":
        raise ValueError("origin does not identify the expected repository")
    rows = git("ls-remote", "--exit-code", "origin", REMOTE_REF).decode().splitlines()
    if rows != [commit + "\t" + REMOTE_REF]:
        raise ValueError("remote branch does not equal the exact supplied checkpoint")
    return {"verified": True, "repository": "occult-kranti/ANDOLAN",
            "ref": REMOTE_REF, "commit": commit}


def save_report(path, report):
    with path.open("x", encoding="utf-8") as output:
        json.dump(report, output, indent=2)
        output.write("\n")
        output.flush()
        os.fsync(output.fileno())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--commit", required=True, help="Exact 40-character intended pushed commit")
    parser.add_argument("--execute", action="store_true", help="Remove only after every gate succeeds")
    parser.add_argument("--skip-remote", action="store_true", help="Local dry-run only; never permits removal")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    if not re.fullmatch(r"[0-9a-f]{40}", args.commit):
        parser.error("--commit must be a full lowercase SHA-1; symbolic refs are refused")
    if args.execute and args.skip_remote:
        parser.error("--execute cannot skip independent remote verification")
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    report_path = args.report or SCRATCH / ("visual-campaign-cleanup-" + stamp + ".json")
    if (not report_path.is_absolute() or report_path.parent != SCRATCH or
            os.path.lexists(report_path)):
        parser.error("report must be a fresh file directly under /workspace/scratch")
    report = {"mode": "execute" if args.execute else "dry_run", "commit": args.commit,
              "started_utc": stamp, "deletions": [], "errors": [], "checks": {}}
    plan_data = read_regular(PLAN)
    if sha(plan_data) != PLAN_SHA:
        raise ValueError("cleanup plan changed; independently review a new plan")
    plan = json.loads(plan_data)
    inventory_data = read_regular(Path(plan["inventory"]["path"]))
    if sha(inventory_data) != plan["inventory"]["sha256"]:
        raise ValueError("frozen inventory hash mismatch")
    inventory = json.loads(inventory_data)
    if ({row["path"] for row in plan["allowlist"]} != ALLOWED or len(plan["allowlist"]) != 9
            or len(plan["required_pending_push_repository_files"]) != 43):
        raise ValueError("unexpected cleanup scope")
    report["plan_sha256"] = PLAN_SHA
    report["inventory_sha256"] = plan["inventory"]["sha256"]
    report["checks"]["immutable_plan_and_inventory"] = True
    try:
        if git("cat-file", "-t", args.commit).strip() != b"commit":
            raise ValueError("checkpoint is not a commit")
        git("merge-base", "--is-ancestor", BASE, args.commit)
        report["checks"]["base_is_ancestor"] = True
    except (RuntimeError, ValueError, subprocess.TimeoutExpired) as error:
        report["errors"].append({"check": "checkpoint", "error": str(error)})
    missing = []
    for row in plan["required_pending_push_repository_files"]:
        relative = PurePosixPath(row["path"])
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("invalid recovery path")
        try:
            data = git("cat-file", "blob", args.commit + ":" + row["path"])
            if len(data) != row["bytes"] or sha(data) != row["sha256"]:
                raise ValueError("backup bytes mismatch")
        except (RuntimeError, ValueError, subprocess.TimeoutExpired) as error:
            missing.append({"path": row["path"], "error": str(error)})
    report["checks"]["recovery_files"] = {"required": 43, "matched": 43 - len(missing), "failures": missing}
    if missing:
        report["errors"].append({"check": "recovery_files", "failed": len(missing)})
    snapshots = {}
    for row in plan["allowlist"]:
        try:
            snapshot = scan_directory(Path(row["path"]), expected_rows(Path(row["path"]), inventory))
            for key in ("file_count", "logical_bytes", "regular_allocated_bytes",
                        "directory_allocated_bytes", "snapshot_fingerprint_sha256"):
                if snapshot[key] != row[key]:
                    raise ValueError("directory inventory mismatch: " + key)
            snapshots[row["path"]] = snapshot
        except (OSError, ValueError) as error:
            report["errors"].append({"check": "inventory", "path": row["path"], "error": str(error)})
    report["checks"]["candidate_inventories"] = snapshots
    processes = inspect_processes()
    report["checks"]["processes"] = processes
    if processes["references"] or processes["unreadable_workers"]:
        report["errors"].append({"check": "processes", "error": "active references or unreadable non-platform processes"})
    if args.skip_remote:
        report["checks"]["remote"] = {"verified": False, "skipped_for_local_dry_run": True}
    else:
        try:
            report["checks"]["remote"] = verify_remote(args.commit)
        except (RuntimeError, ValueError, subprocess.TimeoutExpired) as error:
            report["errors"].append({"check": "remote", "error": str(error)})
    report["ready_for_execution"] = not report["errors"] and not args.skip_remote
    report["visibility_limit"] = "Exact persistent platform dockerd/containerd identities may have unreadable metadata; listed separately. Any unreadable worker/game process blocks."
    save_report(report_path, report)
    if args.execute and report["ready_for_execution"]:
        if not shutil.rmtree.avoids_symlink_attacks:
            raise RuntimeError("safe fd-based rmtree is unavailable; nothing removed")
        # Validate the whole allowlist and processes again immediately before any
        # removal; this is deliberate repetition at a destructive boundary.
        for row in plan["allowlist"]:
            repeated = scan_directory(Path(row["path"]), expected_rows(Path(row["path"]), inventory))
            if repeated != snapshots[row["path"]]:
                raise RuntimeError("inventory changed after preflight; nothing removed")
        current = inspect_processes()
        if current["references"] or current["unreadable_workers"]:
            raise RuntimeError("process ownership changed; nothing removed")
        verify_remote(args.commit)
        journal = report_path.with_suffix(".deletions.jsonl")
        with journal.open("x", encoding="utf-8") as receipt:
            for row in plan["allowlist"]:
                path = Path(row["path"])
                if path.parent.resolve() != path.parent:
                    raise RuntimeError("parent became a symlink; remaining paths preserved")
                parent_fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
                try:
                    info = os.stat(path.name, dir_fd=parent_fd, follow_symlinks=False)
                    expected = snapshots[str(path)]
                    if (not stat.S_ISDIR(info.st_mode) or info.st_dev != expected["root_device"]
                            or info.st_ino != expected["root_inode"]):
                        raise RuntimeError("directory identity changed; remaining paths preserved")
                    shutil.rmtree(path.name, dir_fd=parent_fd)
                finally:
                    os.close(parent_fd)
                removed = {"path": str(path), "logical_bytes": row["logical_bytes"],
                           "regular_allocated_bytes": row["regular_allocated_bytes"],
                           "directory_allocated_bytes": row["directory_allocated_bytes"],
                           "verified_backup_commit": args.commit, "removed": not path.exists()}
                receipt.write(json.dumps(removed) + "\n")
                receipt.flush()
                os.fsync(receipt.fileno())
                report["deletions"].append(removed)
        report["deletion_journal"] = str(journal)
        final = report_path.with_suffix(".completed.json")
        save_report(final, report)
        report_path = final
    print(json.dumps({"report": str(report_path), "mode": report["mode"],
                      "ready_for_execution": report["ready_for_execution"],
                      "backup_files_matched": report["checks"]["recovery_files"]["matched"],
                      "inventories_matched": len(snapshots), "errors": len(report["errors"]),
                      "platform_visibility_gaps": len(processes["platform_visibility_gaps"]),
                      "deleted_paths": len(report["deletions"])}))
    return 0 if not report["errors"] else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as failure:
        print(json.dumps({"failed": True, "error": str(failure),
                          "note": "Inspect any preflight report/deletion journal before retrying."}), file=sys.stderr)
        sys.exit(2)
