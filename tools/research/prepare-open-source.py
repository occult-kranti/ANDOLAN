#!/usr/bin/env python3
"""Fetch reviewed, pinned source references; never run upstream installers.

The catalogue is evidence, not executable configuration. Source checkouts and
receipts live in the ignored .local-tools/research directory. Existing checkouts
must match their receipt and remain clean; this tool never resets or deletes them.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import resource
import subprocess
import sys
import tempfile
import time


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CATALOG = REPO_ROOT / "tools/research/opensource-catalog.json"
OUTPUT_ROOT = REPO_ROOT / ".local-tools/research"
ID_PATTERN = re.compile(r"[a-z0-9][a-z0-9-]{0,63}\Z")
URL_PATTERN = re.compile(r"https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:\.git)?\Z")
SHA_PATTERN = re.compile(r"[0-9a-fA-F]{40}\Z")
MAX_BYTES = 256 * 1024 * 1024


class PreparationError(Exception):
    """A failed preparation leaves existing source checkouts untouched."""


def safe_relative(value: str) -> str:
    if not isinstance(value, str) or not value or "\\" in value:
        raise PreparationError(f"Invalid source path: {value!r}")
    path = PurePosixPath(value)
    if not path.parts or path.is_absolute() or any(p in ("..", ".git") for p in path.parts):
        raise PreparationError(f"Unsafe source path: {value!r}")
    if any(c in value for c in ("\n", "\r", "\0", "*", "?", "[", "]")):
        raise PreparationError(f"Source paths must be literal: {value!r}")
    return str(path)


def load_catalog(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("schema_version") != 1 or not isinstance(data.get("entries"), list):
        raise PreparationError("Expected catalog schema_version 1 and entries array")
    entries = data["entries"]
    seen: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            raise PreparationError("Catalog entries must be objects")
        identifier = entry.get("id", "")
        if not isinstance(identifier, str) or not ID_PATTERN.fullmatch(identifier) or identifier in seen:
            raise PreparationError(f"Invalid or duplicate catalog ID: {identifier!r}")
        seen.add(identifier)
        for field in ("source", "install", "reuse"):
            if not isinstance(entry.get(field), dict):
                raise PreparationError(f"{identifier}: {field} must be an object")
        if not isinstance(entry.get("licenses"), list) or not all(isinstance(item, dict) for item in entry["licenses"]):
            raise PreparationError(f"{identifier}: licenses must be an array of objects")
    return entries


def selected_contract(entry: dict) -> tuple[str, str, list[str], list[str], int]:
    install = entry.get("install", {})
    reuse = entry.get("reuse", {})
    if (install.get("decision") != "source_only" or install.get("source_only") is not True
            or install.get("approval_required") is not False):
        raise PreparationError(f"{entry['id']}: not approved for source-only preparation")
    if (reuse.get("proprietary_assets_required") is not False
            or reuse.get("product_import") is not False):
        raise PreparationError(f"{entry['id']}: requires a separate asset/import decision")
    source = entry.get("source", {})
    url, revision = source.get("repository", ""), source.get("revision", "")
    if not isinstance(url, str) or not URL_PATTERN.fullmatch(url):
        raise PreparationError(f"{entry['id']}: expected a canonical HTTPS GitHub URL")
    if not isinstance(revision, str) or not SHA_PATTERN.fullmatch(revision):
        raise PreparationError(f"{entry['id']}: expected a full 40-character commit SHA")
    if url.rstrip("/").removesuffix(".git").split("/")[-1] in (".", ".."):
        raise PreparationError(f"{entry['id']}: unsafe repository name")
    paths = install.get("sparse_paths")
    if not isinstance(paths, list) or not paths:
        raise PreparationError(f"{entry['id']}: explicit sparse_paths are required")
    paths = [safe_relative(p) for p in paths]
    licenses = entry.get("licenses", [])
    license_paths = sorted({safe_relative(item["path"]) for item in licenses if item.get("path")})
    if not license_paths:
        raise PreparationError(f"{entry['id']}: license source path is required")
    paths = sorted(set(paths + license_paths))
    limit = install.get("max_checkout_bytes")
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= MAX_BYTES:
        raise PreparationError(f"{entry['id']}: max_checkout_bytes must be 1..{MAX_BYTES}")
    return url, revision.lower(), paths, license_paths, limit


def git(args: list[str], cwd: Path, limit: int, input_text: str | None = None) -> str:
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    env.update({"GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
                "GIT_ATTR_NOSYSTEM": "1", "GIT_TERMINAL_PROMPT": "0",
                "GIT_LFS_SKIP_SMUDGE": "1"})

    def file_limit() -> None:
        resource.setrlimit(resource.RLIMIT_FSIZE, (limit, limit))

    command = ["git", "-c", "core.hooksPath=" + os.devnull, "-c", "core.fsmonitor=false",
               "-c", "core.symlinks=false", "-c", "submodule.recurse=false",
               "-c", "protocol.file.allow=never", *args]
    result = subprocess.run(command, cwd=cwd, env=env, input=input_text, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            timeout=120, preexec_fn=file_limit, check=False)
    if result.returncode:
        raise PreparationError(f"git {args[0]} failed ({result.returncode}): {result.stderr[-1800:].strip()}")
    return result.stdout.strip()


def ensure_directory(path: Path) -> None:
    for parent in reversed((path, *path.parents)):
        if parent.is_symlink():
            raise PreparationError(f"Refusing symlinked output directory: {parent}")
    path.mkdir(parents=True, exist_ok=True)


def inventory(path: Path, limit: int) -> dict:
    count, total, git_bytes = 0, 0, 0
    for item in path.rglob("*"):
        if item.is_symlink():
            raise PreparationError(f"Unexpected symlink in prepared source: {item}")
        if item.is_file():
            size = item.stat().st_size
            if ".git" in item.relative_to(path).parts:
                git_bytes += size
            else:
                total += size
                count += 1
            if total + git_bytes > limit:
                raise PreparationError(f"Checkout exceeds {limit} byte budget; staging is retained")
    return {"source_files": count, "source_bytes": total, "git_bytes": git_bytes,
            "total_bytes": total + git_bytes}


def license_hashes(path: Path, names: list[str]) -> list[dict]:
    result = []
    for name in names:
        file = path / name
        if not file.is_file() or file.is_symlink():
            raise PreparationError(f"Required license missing: {name}")
        data = file.read_bytes()
        result.append({"path": name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()})
    return result


def check_reviewed_licenses(entry: dict, hashes: list[dict]) -> None:
    expected = {item["path"]: item["sha256"] for item in entry.get("licenses", [])
                if item.get("path") and item.get("sha256")}
    for item in hashes:
        if item["path"] in expected and item["sha256"] != expected[item["path"]]:
            raise PreparationError(f"Reviewed license hash differs: {item['path']}")


def check_source_paths(path: Path, names: list[str]) -> None:
    for name in names:
        item = path / name
        if item.is_symlink() or not item.exists():
            raise PreparationError(f"Selected source path missing or symlinked: {name}")


def prepare(entry: dict, catalog_hash: str) -> dict:
    url, revision, paths, licenses, limit = selected_contract(entry)
    sources, receipts = OUTPUT_ROOT / "sources", OUTPUT_ROOT / "receipts"
    ensure_directory(sources)
    ensure_directory(receipts)
    target, receipt_path = sources / entry["id"], receipts / (entry["id"] + ".json")
    if receipt_path.is_symlink() or target.is_symlink():
        raise PreparationError("Refusing a symlinked source or receipt")
    started = time.monotonic()
    if target.exists():
        if not target.is_dir() or not receipt_path.is_file():
            raise PreparationError(f"Existing {target} has no trusted receipt; preserve and inspect manually")
        receipt = json.loads(receipt_path.read_text())
        if (receipt.get("repository") != url or receipt.get("revision") != revision
                or receipt.get("sparse_paths") != paths):
            raise PreparationError(f"Existing {target} differs from requested contract; left untouched")
        sizes = inventory(target, limit)
        if git(["rev-parse", "HEAD"], target, limit) != revision:
            raise PreparationError(f"Existing {target} HEAD differs; left untouched")
        if git(["remote", "get-url", "origin"], target, limit) != url:
            raise PreparationError(f"Existing {target} origin differs; left untouched")
        if git(["status", "--porcelain", "--untracked-files=all"], target, limit):
            raise PreparationError(f"Existing {target} has local changes; left untouched")
        check_source_paths(target, paths)
        hashes = license_hashes(target, licenses)
        if receipt.get("license_files") != hashes:
            raise PreparationError(f"Existing {target} license bytes differ; left untouched")
        check_reviewed_licenses(entry, hashes)
        return {"id": entry["id"], "status": "existing_verified", "revision": revision,
                "path": str(target), **sizes}

    if receipt_path.exists():
        raise PreparationError(f"Receipt already exists without source: {receipt_path}; preserve and inspect manually")
    staging = Path(tempfile.mkdtemp(prefix=".pending-" + entry["id"] + "-", dir=sources))
    try:
        git(["init", "--template=", "."], staging, limit)
        git(["remote", "add", "origin", url], staging, limit)
        git(["config", "remote.origin.promisor", "true"], staging, limit)
        git(["config", "remote.origin.partialclonefilter", "blob:none"], staging, limit)
        git(["fetch", "--depth=1", "--filter=blob:none", "--no-tags", "origin", revision], staging, limit)
        inventory(staging, limit)
        git(["sparse-checkout", "init", "--no-cone"], staging, limit)
        # Literal directory/file prefixes, never catalogue-provided patterns.
        patterns = "\n".join("/" + name for name in paths) + "\n"
        git(["sparse-checkout", "set", "--no-cone", "--stdin"], staging, limit, patterns)
        git(["checkout", "--detach", revision], staging, limit)
        if git(["rev-parse", "HEAD"], staging, limit) != revision:
            raise PreparationError("Fetched source does not match the exact requested SHA")
        if git(["status", "--porcelain", "--untracked-files=all"], staging, limit):
            raise PreparationError("New source checkout is unexpectedly modified")
        check_source_paths(staging, paths)
        hashes = license_hashes(staging, licenses)
        check_reviewed_licenses(entry, hashes)
        sizes = inventory(staging, limit)
        receipt = {"schema_version": 1, "id": entry["id"], "repository": url,
                   "revision": revision, "sparse_paths": paths, "catalog_sha256": catalog_hash,
                   "prepared_at": datetime.now(timezone.utc).isoformat(),
                   "elapsed_seconds": round(time.monotonic() - started, 3),
                   "source_only": True, "upstream_scripts_executed": False,
                   "submodules_fetched": False, "license_files": hashes, **sizes}
        staging.rename(target)
        # Exclusive creation also prevents quietly replacing someone else's receipt.
        with receipt_path.open("x", encoding="utf-8") as stream:
            json.dump(receipt, stream, indent=2)
            stream.write("\n")
        return {"id": entry["id"], "status": "prepared", "revision": revision,
                "path": str(target), "receipt": str(receipt_path), **sizes}
    except Exception as error:
        raise PreparationError(f"{entry['id']}: {error}; retained staging: {staging}") from error


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG,
                        help="Reviewed schema-v1 catalogue (default: tools/research/opensource-catalog.json)")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--list", action="store_true", help="List catalog decisions without fetching")
    mode.add_argument("--fetch", nargs="+", metavar="ID", help="Prepare explicitly approved pinned source IDs")
    args = parser.parse_args()
    try:
        entries = load_catalog(args.catalog)
        if args.list:
            for entry in entries:
                print(json.dumps({"id": entry["id"], "name": entry.get("name"),
                                  "decision": entry.get("install", {}).get("decision"),
                                  "revision": entry.get("source", {}).get("revision")}, sort_keys=True))
            return 0
        by_id = {entry["id"]: entry for entry in entries}
        unknown = sorted(set(args.fetch) - by_id.keys())
        if unknown:
            raise PreparationError("Unknown catalog IDs: " + ", ".join(unknown))
        selected = [by_id[identifier] for identifier in dict.fromkeys(args.fetch)]
        # Validate the complete requested batch before making any network request.
        for entry in selected:
            selected_contract(entry)
        digest = hashlib.sha256(args.catalog.read_bytes()).hexdigest()
        for entry in selected:
            print(json.dumps(prepare(entry, digest), sort_keys=True), flush=True)
        return 0
    except (PreparationError, OSError, ValueError, KeyError, TypeError, subprocess.TimeoutExpired) as error:
        print(json.dumps({"status": "error", "error": str(error)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
