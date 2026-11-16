#!/usr/bin/env python3
"""Copy the finite native packaging closure into a fresh, verified source snapshot.

No import, renderer, export, git mutation, source mutation, symlink or hardlink.
The lead runs this only after final district/contract pins are stable. The copy
retains failed destinations for inspection; use a new destination on failure.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import sys

sys.dont_write_bytecode = True
REPOSITORY = Path(__file__).resolve().parents[2]
NATIVE_RELATIVE = Path("games/yuga-native")
PROJECT = REPOSITORY / NATIVE_RELATIVE
SKIP_DIRECTORIES = {"__pycache__", ".git", "node_modules", ".venv"}
SKIP_SUFFIXES = {".pyc", ".pyo"}


def safe_file(relative: str, repository: Path = REPOSITORY) -> Path:
    parsed = PurePosixPath(relative)
    if (not parsed.parts or parsed.is_absolute() or ".." in parsed.parts
            or "\\" in relative or parsed.as_posix() != relative):
        raise ValueError("Unsafe relative snapshot input: " + relative)
    path = repository / relative
    for index in range(1, len(parsed.parts) + 1):
        if repository.joinpath(*parsed.parts[:index]).is_symlink():
            raise ValueError("Snapshot input has a symlink: " + relative)
    if not path.is_file() or not path.resolve().is_relative_to(repository):
        raise ValueError("Missing regular snapshot input: " + relative)
    return path


def stamp(path: Path) -> tuple:
    info = path.stat(follow_symlinks=False)
    if not stat.S_ISREG(info.st_mode):
        raise ValueError("Expected regular file: " + str(path))
    return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns


def file_record(path: Path) -> dict:
    before = stamp(path)
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    if stamp(path) != before:
        raise ValueError("Source changed while hashing: " + str(path))
    return {"bytes": before[2], "sha256": digest.hexdigest()}


def tree_files(relative: str) -> set[str]:
    base = REPOSITORY / relative
    if not base.is_dir() or base.is_symlink():
        raise ValueError("Missing regular snapshot directory: " + relative)
    result = set()
    for directory, names, files in os.walk(base, followlinks=False):
        for name in names:
            if (Path(directory) / name).is_symlink():
                raise ValueError("Symlink in snapshot directory: " + str(Path(directory) / name))
        names[:] = sorted(name for name in names if name not in SKIP_DIRECTORIES)
        for name in sorted(files):
            path = Path(directory) / name
            if path.suffix not in SKIP_SUFFIXES:
                relative_path = path.relative_to(REPOSITORY).as_posix()
                safe_file(relative_path)
                result.add(relative_path)
    return result


def load_packaging():
    source = PROJECT / "tools/package-native.py"
    spec = importlib.util.spec_from_file_location("frozen_native_packaging_closure", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def collect(module, args) -> tuple[dict, dict]:
    paths = set()
    groups = {}

    def add_group(name: str, selected):
        selected = set(selected)
        groups[name] = sorted(selected)
        paths.update(selected)

    runtime = module.source_state()
    add_group("runtime", [f"{NATIVE_RELATIVE}/{path}" for path in runtime["files"]])
    for directory in ("NOTICE", "tools", "tests"):
        add_group(directory, tree_files(f"{NATIVE_RELATIVE}/{directory}"))
    hero = module.validate_rama_hero_notice()
    add_group("hero_provenance", [f"{NATIVE_RELATIVE}/{path}" for path in hero["sources"]])
    contracts = module._native_contract_inputs(PROJECT)
    add_group("contract_proof", contracts)
    catalog = json.loads((PROJECT / "assets/contracts/native-contracts-v1.json").read_text())
    for profile in catalog["profiles"]:
        for path, expected in profile["content_sources"].items():
            if contracts[path]["sha256"] != expected:
                raise ValueError("Contract pin is not final: " + path)
    district = json.loads((PROJECT / "assets/world/sangam-district.json").read_text())
    for relative, expected in [
        ("games/yuga-native/assets/world/sangam-district.glb", district["asset_sha256"]),
        (district["finish_shader"], district["finish_shader_sha256"]),
        ("games/yuga-native/assets/world/confluence-map.json", district["source_map_sha256"]),
    ]:
        if file_record(safe_file(relative))["sha256"] != expected:
            raise ValueError("District transitive pin is not final: " + relative)
    required = {
        "games/yuga/client/assets/heroes/rama.glb",
        "games/yuga-native/art/world/confluence-map.json",
        "games/yuga-native/art/.gdignore", "games/yuga-native/docs/.gdignore",
        "tools/studio/freeze-sangam-source.py",
    }
    if (REPOSITORY / ".gitignore").is_file():
        required.add(".gitignore")
    add_group("build_support", required)
    if args.runtime_evidence != "none":
        evidence = (module.PATCHED_RUNTIME_EVIDENCE if args.runtime_evidence == "pipeline-low-priority"
                    else module.PUBLIC_RUNTIME_EVIDENCE)
        add_group("optional_engine_provenance", [f"{NATIVE_RELATIVE}/{path}" for path in evidence])
    if not args.no_import_cache:
        add_group("import_cache", tree_files("games/yuga-native/.godot"))
    add_group("explicit_additional_files", args.include)
    records = {relative: file_record(safe_file(relative)) for relative in sorted(paths)}
    for relative, record in runtime["files"].items():
        if records[f"{NATIVE_RELATIVE}/{relative}"] != record:
            raise ValueError("Runtime changed during closure discovery: " + relative)
    for relative, record in contracts.items():
        if records[relative] != record:
            raise ValueError("Contract source changed during closure discovery: " + relative)
    for relative, record in hero["sources"].items():
        if records[f"{NATIVE_RELATIVE}/{relative}"] != record:
            raise ValueError("Hero provenance changed during closure discovery: " + relative)
    return records, {"groups": groups, "runtime_source": runtime, "runtime_source_sha256": runtime["sha256"],
                     "runtime_file_count": len(runtime["files"]), "hero_provenance_file_count": len(hero["sources"]),
                     "contract_input_count": len(contracts)}


def write_json_new(path: Path, data: dict):
    with path.open("x", encoding="utf-8") as output:
        json.dump(data, output, indent=2, sort_keys=True)
        output.write("\n")


def copy_one(relative: str, expected: dict, destination: Path):
    source = safe_file(relative)
    before = stamp(source)
    target = destination / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256()
    size = 0
    with source.open("rb") as reader, target.open("xb") as writer:
        for block in iter(lambda: reader.read(1024 * 1024), b""):
            writer.write(block)
            digest.update(block)
            size += len(block)
    if stamp(source) != before or {"bytes": size, "sha256": digest.hexdigest()} != expected:
        raise ValueError("Source changed during copy: " + relative)
    shutil.copystat(source, target, follow_symlinks=False)
    if file_record(target) != expected or target.stat().st_ino == source.stat().st_ino:
        raise ValueError("Independent snapshot copy does not match: " + relative)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--no-import-cache", action="store_true")
    parser.add_argument("--runtime-evidence", choices=["none", "unmodified-public", "pipeline-low-priority"], default="none")
    parser.add_argument("--include", action="append", default=[], metavar="REPO_RELATIVE_FILE")
    parser.add_argument("--expect", action="append", default=[], metavar="REPO_RELATIVE_FILE=SHA256",
                        help="Optional final freeze pins; mismatch fails before creating destination")
    args = parser.parse_args()
    allowed = REPOSITORY / ".local-tools/review"
    destination = args.destination
    if not destination.is_absolute() or destination.exists() or destination.is_symlink():
        parser.error("Choose a new absolute destination; existing and failed snapshots are never overwritten")
    if not destination.resolve().is_relative_to(allowed.resolve()) or destination.resolve() == allowed.resolve():
        parser.error("Destination must be a new child of .local-tools/review")
    for parent in destination.parents:
        if parent.is_symlink():
            parser.error("Destination parents must not be symlinks")
    module = load_packaging()
    source_git = module.git_context()
    before, closure = collect(module, args)
    for pin in args.expect:
        relative, separator, expected = pin.partition("=")
        if not separator or len(expected) != 64 or before.get(relative, {}).get("sha256") != expected:
            raise ValueError("Requested freeze pin does not match closure: " + relative)
    destination.mkdir(parents=True, exist_ok=False)
    receipt = {"schema": 1, "complete": False, "created_utc": datetime.now(timezone.utc).isoformat(),
               "source_repository": str(REPOSITORY), "snapshot_repository": str(destination),
               "source_git_at_freeze": source_git, "closure": closure, "files": before,
               "file_count": len(before), "total_bytes": sum(row["bytes"] for row in before.values()),
               "scope": "Exact copied packaging inputs. Original files untouched; no git initialization/config copy, symlinks, hardlinks, import, renderer or export. Base git commit comes from nearest original repository; recorded hashes own dirty snapshot bytes. Optional historical test archives and platform binaries remain separate."}
    write_json_new(destination / "SNAPSHOT-PENDING.json", receipt)
    try:
        for relative, expected in before.items():
            copy_one(relative, expected, destination)
        # Rediscovery catches added/removed files and changed dependency lists,
        # not only edits to the initially enumerated runtime files.
        after, after_closure = collect(module, args)
        if before != after or closure != after_closure:
            changed = sorted(set(before) ^ set(after) | {key for key in before.keys() & after.keys() if before[key] != after[key]})
            raise ValueError("Live input closure changed during snapshot: " + ", ".join(changed[:20]))
        copied = {relative: file_record(safe_file(relative, destination)) for relative in before}
        if copied != before:
            raise ValueError("Snapshot changed during final verification")
        receipt.update(complete=True, source_files_unchanged=True, snapshot_matches_source=True,
                       source_git_after_copy=module.git_context(),
                       source_records_sha256=hashlib.sha256(json.dumps(before, sort_keys=True).encode()).hexdigest())
        write_json_new(destination / "SNAPSHOT-MANIFEST.json", receipt)
        write_json_new(destination / "SOURCE_SNAPSHOT.json", {
            "schema": 1, "kind": "yuga-native-source-snapshot", "complete": True,
            "source_repository": str(REPOSITORY), "snapshot_repository": str(destination),
            "git": source_git, "runtime_source": closure["runtime_source"],
            "snapshot_manifest": file_record(destination / "SNAPSHOT-MANIFEST.json"),
            "packaging_script": before["games/yuga-native/tools/package-native.py"],
            "scope": "Original repository git context captured before an unchanged verified source copy. Runtime hashes identify dirty snapshot bytes; nearest-parent git status is not the snapshot's source status."})
        print(json.dumps({key: receipt[key] for key in ["complete", "snapshot_repository", "file_count", "total_bytes", "source_records_sha256"]}))
        return 0
    except Exception as error:
        write_json_new(destination / "SNAPSHOT-FAILED.json", {"complete": False, "error": str(error),
                       "scope": "Partial snapshot preserved. Do not import/export it; use a fresh successor destination."})
        raise


if __name__ == "__main__":
    raise SystemExit(main())
