#!/usr/bin/env python3
"""Add a reviewed observatory snapshot at /production without replacing games.

Build the separately pinned browser source with its existing assembler first.
Then run this script with --site <baseline>/dist/site --web <current>/web and
full --baseline-ref/--source-ref SHAs. The source must contain status.json in
snapshot mode. Only approved static entry files, media, compiled viewer assets
and their notices are copied. Python, design briefs and source maps stay private.

The destination must be a fresh assembled site without production/. A baseline
file census is compared before/after and bound into production/publication.json.
Rebuilding a source revision does not establish equality to previously deployed
bytes; this receipt proves preservation of the supplied assembled baseline only.
No deployment, account access or network request is performed by this script.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import ipaddress
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import tempfile
from urllib.parse import urlsplit


REQUIRED_BASELINE = ("index.html", "yuga/index.html", "yuga/lab/index.html",
                     "yuga/lane-lab/index.html", "yuga/control-lab/index.html")
REQUIRED_WEB = {"index.html", "styles.css", "app.js", "status.json"}
ROOT_FILES = REQUIRED_WEB | {"viewer.html", "viewer.js", "viewer.css"}
MEDIA_TYPES = {".png", ".jpg", ".jpeg", ".webp", ".avif", ".gif", ".svg",
               ".glb", ".gltf", ".bin", ".ttf", ".otf", ".woff", ".woff2"}
NOTICE_TYPES = {".txt", ".md", ".json"}
VIEWER_TYPES = {".js", ".css", ".wasm", ".bin", ".woff", ".woff2", ".png", ".svg"}
VIEWER_NOTICES = {"viewer/NOTICE.txt", "viewer/PLAYCANVAS-LICENSE.txt"}
SHA = re.compile(r"[0-9a-f]{40}\Z")
PRIVATE_KEYS = {"pid", "boot_id", "start_ticks", "_liveness", "_tracking", "process_identity",
                "api_key", "access_token", "password", "secret"}
MAX_JSON = 2 * 1024 * 1024
MAX_FILE = 64 * 1024 * 1024
MAX_WEB_TOTAL = 256 * 1024 * 1024


def relative(value):
    if not isinstance(value, str) or not value or len(value) > 1500:
        raise ValueError("Expected bounded relative path")
    if any(c.isspace() or ord(c) < 32 for c in value) or any(c in value for c in "\\%:?#"):
        raise ValueError("Unsafe relative path")
    p = PurePosixPath(value)
    if p.is_absolute() or any(x in {"", ".", ".."} or x.startswith(".") for x in value.split("/")):
        raise ValueError("Path traversal or hidden path refused")
    return p


def safe_root(value):
    path = Path(os.path.abspath(value))
    for entry in [*reversed(path.parents), path]:
        if entry.is_symlink():
            raise ValueError("Symlink path components refused")
    if not path.is_dir():
        raise ValueError("Expected existing directory")
    return path


def files_under(root):
    found = {}
    def fail(error):
        raise ValueError("Cannot complete the source/baseline file census") from error

    for folder, dirs, files in os.walk(root, followlinks=False, onerror=fail):
        for name in dirs + files:
            entry = Path(folder) / name
            if entry.is_symlink():
                raise ValueError("Symlinks refused in source or assembled baseline")
        for name in files:
            entry = Path(folder) / name
            if not entry.is_file():
                raise ValueError("Only regular files are supported")
            found[entry.relative_to(root).as_posix()] = entry
            if len(found) > 50000:
                raise ValueError("File census exceeds bound")
    return found


def approved(name):
    p = relative(name)
    if name in ROOT_FILES:
        return True
    if p.parts[0] == "media":
        return (len(p.parts) > 2 and p.parts[1] == "licenses" and p.suffix.lower() in NOTICE_TYPES
                or p.suffix.lower() in MEDIA_TYPES)
    if p.parts[0] == "viewer":
        if name in {"viewer/index.html", "viewer/favicon.svg"} or name in VIEWER_NOTICES:
            return True
        if len(p.parts) > 2 and p.parts[1] == "assets":
            return p.suffix.lower() in VIEWER_TYPES
        if len(p.parts) > 2 and p.parts[1] == "licenses":
            return p.suffix.lower() in NOTICE_TYPES
        return False
    return False


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return {"bytes": path.stat().st_size, "sha256": h.hexdigest()}


def census(files):
    return {name: digest(path) for name, path in sorted(files.items())}


def artifact_url(value, selected):
    if not isinstance(value, str) or not value or any(ord(c) <= 32 or ord(c) == 127 for c in value) or "\\" in value:
        raise ValueError("Unsafe artifact URL")
    if value.startswith("https://"):
        u = urlsplit(value)
        if not u.hostname or u.username is not None or u.password is not None or u.query or u.fragment:
            raise ValueError("Unsafe HTTPS artifact URL")
        if u.hostname.casefold() == "localhost" or u.hostname.casefold().endswith(".local"):
            raise ValueError("Private host URL refused")
        try:
            if not ipaddress.ip_address(u.hostname).is_global:
                raise ValueError("Private IP URL refused")
        except ValueError as exc:
            if str(exc) == "Private IP URL refused":
                raise
        return
    if value in {"viewer/", "viewer/index.html"}:
        if "viewer/index.html" not in selected:
            raise ValueError("Referenced viewer is absent")
        return
    p = relative(value)
    if p.parts[0] != "media" or value not in selected:
        raise ValueError("Artifact must reference an approved existing media file")


def validate_snapshot(path, selected):
    if path.stat().st_size > MAX_JSON:
        raise ValueError("Snapshot exceeds 2 MiB")
    data = json.loads(path.read_text(), parse_constant=lambda x: (_ for _ in ()).throw(ValueError("Nonfinite JSON")))
    if not isinstance(data, dict) or type(data.get("schema_version")) is not int or data.get("schema_version") != 1:
        raise ValueError("Expected schema_version 1 snapshot object")
    if data.get("mode") != "snapshot":
        raise ValueError("Published data must be an explicitly labelled saved snapshot")
    stamp = data.get("collected_at")
    if not isinstance(stamp, str) or dt.datetime.fromisoformat(stamp.replace("Z", "+00:00")).tzinfo is None:
        raise ValueError("Snapshot needs a timezone-aware observation timestamp")
    for key in ("jobs", "milestones", "assets", "sources"):
        if not isinstance(data.get(key), list) or len(data[key]) > 256 or not all(isinstance(x, dict) for x in data[key]):
            raise ValueError("Malformed or oversized snapshot records")

    def walk(value):
        if isinstance(value, dict):
            for key, child in value.items():
                if key.casefold() in PRIVATE_KEYS:
                    raise ValueError("Private state key in public snapshot")
                if (key == "url" or key.endswith("_url")) and child is not None:
                    artifact_url(child, selected)
                if key == "path" and child is not None:
                    relative(child)
                walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)
    walk(data)
    return data


def publish(site, web, baseline_ref, source_ref):
    if not SHA.fullmatch(baseline_ref) or not SHA.fullmatch(source_ref):
        raise ValueError("Full lowercase source commits are required")
    site, web = safe_root(site), safe_root(web)
    if site == web or site.is_relative_to(web) or web.is_relative_to(site):
        raise ValueError("Source and destination roots must be disjoint")
    baseline_files = files_under(site)
    if any(name not in baseline_files for name in REQUIRED_BASELINE):
        raise ValueError("Assembled baseline is missing root, YUGA or lab entry points")
    destination = site / "production"
    if destination.exists():
        raise ValueError("production/ already exists; assemble a fresh baseline")
    source_files = files_under(web)
    selected = {name: path for name, path in source_files.items() if approved(name)}
    if not REQUIRED_WEB.issubset(selected):
        raise ValueError("Dashboard entry files or status snapshot are missing")
    if "viewer/index.html" in selected and not VIEWER_NOTICES.issubset(selected):
        raise ValueError("Compiled PlayCanvas viewer requires its retained notices")
    if any(p.stat().st_size > MAX_FILE for p in selected.values()) or sum(p.stat().st_size for p in selected.values()) > MAX_WEB_TOTAL:
        raise ValueError("Dashboard payload exceeds bound")
    snapshot = validate_snapshot(selected["status.json"], selected)
    before = census(baseline_files)
    copied = census(selected)
    staging = Path(tempfile.mkdtemp(prefix=".production-", dir=site))
    installed = False
    try:
        for name, source in selected.items():
            target = staging / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target, follow_symlinks=False)
        if census(files_under(staging)) != copied:
            raise ValueError("Dashboard source changed during copy")
        record = {"schema_version": 1, "baseline_source": baseline_ref, "dashboard_source": source_ref,
                  "observation_time": snapshot["collected_at"], "data_mode": "snapshot",
                  "baseline_files": len(before), "baseline_census_sha256": hashlib.sha256(json.dumps(before, sort_keys=True).encode()).hexdigest(),
                  "dashboard_files": copied, "scope": "Additive preservation of this assembled baseline; historical deployed byte equality unverified."}
        (staging / "publication.json").write_text(json.dumps(record, indent=2) + "\n")
        if census({name: path for name, path in files_under(site).items() if not name.startswith(staging.name + "/")}) != before:
            raise ValueError("Baseline changed during staging")
        staging.rename(destination)
        installed = True
        if census({name: path for name, path in files_under(site).items() if not name.startswith("production/")}) != before:
            raise ValueError("Baseline changed after additive installation")
        return record
    finally:
        if not installed:
            shutil.rmtree(staging)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--site", type=Path, required=True)
    parser.add_argument("--web", type=Path, required=True)
    parser.add_argument("--baseline-ref", required=True)
    parser.add_argument("--source-ref", required=True)
    args = parser.parse_args()
    try:
        result = publish(args.site, args.web, args.baseline_ref, args.source_ref)
    except (ValueError, OSError) as exc:
        parser.exit(1, f"Observatory publication refused: {exc}\n")
    print(json.dumps({"status": "ready_for_pages_artifact", "baseline_files": result["baseline_files"],
                      "dashboard_files": len(result["dashboard_files"]), "data_mode": result["data_mode"]}))


if __name__ == "__main__":
    main()
