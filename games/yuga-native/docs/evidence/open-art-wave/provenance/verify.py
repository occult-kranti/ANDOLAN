#!/usr/bin/env python3
"""Bounded source/license audit. Writes only a fresh --report; no exports/network."""
from __future__ import annotations
import argparse
import configparser
import datetime
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys

REPO = Path(__file__).resolve().parents[6]
PROJECT = REPO / "games/yuga-native"
OWN = Path(__file__).resolve().parent
checks = []
pins = {}

def check(name, ok, **details):
    checks.append({"name": name, "passed": bool(ok), **details})

def safe(root, relative):
    if not isinstance(relative, str) or not relative or "\\" in relative:
        raise ValueError("Invalid repository relative path")
    parts = PurePosixPath(relative)
    if parts.is_absolute() or ".." in parts.parts:
        raise ValueError("Path escapes selected repository root")
    p = root / relative
    if p.is_symlink() or not p.resolve().is_relative_to(root.resolve()) or not p.is_file():
        raise ValueError("Missing or unsafe source file: " + relative)
    return p

def record(p):
    h = hashlib.sha256()
    with p.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    result = {"bytes": p.stat().st_size, "sha256": h.hexdigest()}
    pins[str(p.relative_to(REPO))] = result
    return result

def exact(p, expected, size=None):
    r = record(p)
    check("exact source identity: " + str(p.relative_to(REPO)),
          r["sha256"] == expected and (size is None or r["bytes"] == size))

def git(*args):
    return subprocess.check_output(["git", "-C", str(REPO), *args])

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    out = args.report
    if not out.is_absolute() or out.exists() or out.is_symlink() or not out.parent.is_dir():
        parser.error("--report needs an absolute fresh file with an existing parent")
    if out.resolve().is_relative_to(REPO) and not out.resolve().is_relative_to(OWN):
        parser.error("Repository output is restricted to this review directory")

    art = PROJECT / "art/open-art-wave"
    manifest = json.loads(safe(art, "source-manifest.json").read_text())
    check("pinned source revision", manifest["revision"] == "edc7c9e67c639d230715049ee31f9a96a6babbbe")
    check("separate image and metadata licenses", manifest["asset_license"] == "CC0-1.0" and manifest["metadata_license"] == "CC-BY-4.0")
    for item in manifest["files"]:
        exact(safe(art / "source/microsoft-sheen-cloth", item["file"]), item["sha256"], item["bytes"])
        check("source URL pinned: " + item["file"], "/" + manifest["revision"] + "/" in item["url"])
        expected = "CC0-1.0" if item["file"].endswith(".png") else "CC-BY-4.0 metadocumentation"
        check("file license: " + item["file"], item["license"] == expected)
    license_text = safe(art / "source/microsoft-sheen-cloth", "LICENSE.md").read_text()
    check("explicit metadata exception retained", 'This file and all other metadocumentation' in license_text and 'CC-BY-4.0' in license_text)
    notice = safe(PROJECT, "NOTICE/OPEN-ART-WAVE.md").read_text()
    check("notice credits and change disclosure", all(s in notice for s in ["Microsoft", "2020", "CC-BY-4.0", "CC0-1.0", "2026", manifest["revision"]]))
    root_licenses = [p for p in REPO.iterdir() if p.is_file() and p.name.lower().startswith("license")]
    root_mit = any("Permission is hereby granted" in p.read_text(errors="replace") for p in root_licenses)
    check("repository-wide MIT claim substantiated or absent", "repository's MIT license" not in notice or root_mit, repository_root_license_files=len(root_licenses))
    built = json.loads(safe(art, "build-manifest.json").read_text())
    exact(safe(art, "source-manifest.json"), built["source_manifest_sha256"])
    for item in built["outputs"]:
        exact(safe(PROJECT, item["path"]), item["sha256"], item["bytes"])
    regen = subprocess.run([sys.executable, str(PROJECT / "tools/build-open-art-materials.py"), "--check"], capture_output=True, text=True, timeout=60)
    regen_result = json.loads(regen.stdout) if regen.returncode == 0 else {"exit_code": regen.returncode}
    check("deterministic generator --check", regen.returncode == 0, result=regen_result)

    vendor = PROJECT / "art/hero-rama-tangents/vendor"
    mikk = json.loads(safe(vendor, "upstream.json").read_text())
    check("Mikk upstream revision", mikk["commit"] == "3e895b49d05ea07e4c2133156cfa94369e19e409")
    for filename, expected in mikk["files"].items():
        exact(safe(vendor, filename), expected)
    for filename in ["mikktspace.c", "mikktspace.h"]:
        s = safe(vendor, filename).read_text()
        check("Mikk intact permissive notice: " + filename, all(t in s for t in ["Morten S. Mikkelsen", "This notice may not be removed", "Altered source versions must be plainly marked"]))
    check("separate original CC0 adapter", "Original YUGA authoring adapter, CC0-1.0" in safe(PROJECT, "art/hero-rama-tangents/bridge.c").read_text())

    pool = PROJECT / "docs/evidence/reuse-study/games/module-check"
    openmw = json.loads(safe(pool, "input-manifest.json").read_text())
    check("OpenMW explicitly isolated", openmw["runtime_integration"] is False and openmw["commit"] == "fa732a1551a696f8cb52a65c9896b8b4b92eb3dd")
    for filename, item in openmw["files"].items():
        exact(safe(pool, filename), item["sha256"], item["bytes"])
    check("GPL source/harness notice retained", "GPL-3.0-only" in safe(pool, "NOTICE.md").read_text() and "GNU GENERAL PUBLIC LICENSE" in safe(pool, "vendor/openmw/COPYING").read_text())

    exact(safe(PROJECT, "assets/heroes/rama-hero.glb"), "de61dc4c470920eab6f3265bc5467da7f9fb33d6fae2129a9353e7ca6d24d3f5", 34322216)
    runtime_assets = []
    for p in sorted((PROJECT / "assets").rglob("*")):
        if not p.is_file() or p.suffix == ".import":
            continue
        relative = str(p.relative_to(REPO))
        runtime_assets.append(relative)
        # git diff checks the full tracked runtime asset set against the source commit.
    asset_changes = git("diff", "HEAD", "--name-only", "--", "games/yuga-native/assets").decode().splitlines()
    new_assets = git("ls-files", "--others", "--exclude-standard", "--", "games/yuga-native/assets").decode().splitlines()
    check("runtime asset set unchanged from HEAD", not asset_changes and not new_assets, runtime_asset_count=len(runtime_assets), changed_paths=asset_changes, new_paths=new_assets)
    for name in ["rama-hero-mid.glb", "rama-hero-far.glb"]:
        record(safe(PROJECT, "assets/heroes/" + name))
    runtime_hits = []
    for area in ["scripts", "scenes", "shaders", "assets"]:
        for p in (PROJECT / area).rglob("*"):
            if p.is_file() and p.suffix in [".gd", ".tscn", ".tres", ".gdshader", ".json"]:
                if re.search(r"(?:res://art/open-art-wave|rea-agents|objectpool\.hpp|mikktspace\.[ch])", p.read_text(errors="replace")):
                    runtime_hits.append(str(p.relative_to(REPO)))
    check("new authoring inputs absent from runtime references", not runtime_hits, paths=runtime_hits)
    cfg = configparser.ConfigParser(interpolation=None)
    cfg.read(PROJECT / "export_presets.cfg")
    filters = {}
    for section in ["preset.0", "preset.1"]:
        filters[section] = cfg[section]["exclude_filter"].strip('"')
        check("authoring/evidence export exclusions: " + section, all(s in filters[section].split(",") for s in ["art/*", "tools/*", "docs/*", "source/*"]))

    rea_dir = PROJECT / "tools/native-analysis/rea-runtime"
    lock = json.loads(safe(rea_dir, "package-lock.json").read_text())
    pkg = json.loads(safe(rea_dir, "package.json").read_text())
    rea = lock["packages"]["node_modules/rea-agents"]
    check("REA exact development dependency", pkg["dependencies"] == {"rea-agents": "6.5.0"} and rea["version"] == "6.5.0" and rea["license"] == "MIT" and lock["lockfileVersion"] == 3)
    locked = [p for k,p in lock["packages"].items() if k]
    check("npm archive resolutions and integrity retained", all(p.get("resolved", "").startswith("https://registry.npmjs.org/") and p.get("integrity", "").startswith("sha512-") for p in locked), entries=len(locked))
    summary_path = PROJECT / "docs/evidence/open-art-wave/toolchain/summary.json"
    if summary_path.exists():
        summary = json.loads(summary_path.read_text())
        for relative, item in summary["source_files"].items():
            exact(safe(REPO, relative), item["sha256"], item["bytes"])
        check("saved fresh-install receipt matches final lock", summary["exact_lock_sha256"] == record(safe(rea_dir, "package-lock.json"))["sha256"] and summary["actual_install"]["all_three_steps_exit0"])

    # Inspect changed/untracked source and evidence without printing candidate bytes.
    changed = set(git("diff", "HEAD", "--name-only", "-z").decode().split("\0"))
    changed.update(git("ls-files", "--others", "--exclude-standard", "-z").decode().split("\0"))
    patterns = {
        "github": rb"(?:github_pat_[A-Za-z0-9_]{30,}|gh[pousr]_[A-Za-z0-9]{30,})",
        "private_key": rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
        "aws_access_id": rb"(?:AKIA|ASIA)[A-Z0-9]{16}",
        "slack": rb"xox[baprs]-[0-9A-Za-z-]{20,}",
        "openai": rb"sk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{40,}",
        "url_userinfo": rb"https?://[^\s/@:]+:[^\s/@]+@",
    }
    counts = {k: 0 for k in patterns}
    files_scanned = 0
    for relative in sorted(changed - {""}):
        p = REPO / relative
        if not p.is_file() or p.is_symlink() or p.stat().st_size > 4_000_000:
            continue
        b = p.read_bytes()
        if b"\0" in b[:8192]:
            continue
        files_scanned += 1
        for name, regex in patterns.items():
            counts[name] += len(re.findall(regex, b))
    check("bounded sensitive-pattern scan", not any(counts.values()), files_scanned=files_scanned, counts_only=counts, scope="Changed/untracked nonbinary files <=4MB. SHA256 values and npm sha512 integrity are ordinary hashes, excluded from token patterns. No credential contents or matching lines retained.")

    for area in ["art/open-art-wave", "art/hero-rama-repair", "art/hero-rama-tangents", "tools/native-analysis/rea-runtime"]:
        for p in sorted((PROJECT / area).rglob("*")):
            if p.is_file() and not p.is_symlink() and p.suffix not in [".pyc", ".import"]:
                record(p)
    for relative in ["NOTICE/OPEN-ART-WAVE.md", "NOTICE/MIKKTSPACE-AUTHORING.md", "NOTICE/RAMA-HERO-PROVENANCE.json", "tools/build-open-art-materials.py", "tools/native-analysis/setup-rea.sh", "export_presets.cfg", "tools/package-native.py", "docs/evidence/open-art-wave/toolchain/summary.json"]:
        record(safe(PROJECT, relative))
    record(Path(__file__))
    if (REPO / "LICENSE").is_file():
        record(REPO / "LICENSE")
    failures = [c["name"] for c in checks if not c["passed"]]
    report = {"schema": 1, "role": "NEXT15-13", "source_commit": git("rev-parse", "HEAD").decode().strip(), "generated_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "command": ["python3", str(Path(__file__).relative_to(REPO)), "--report", str(out)], "status": "PASS" if not failures else "FAIL", "checks": checks, "failed_checks": failures, "file_pins": pins, "export_filters_observed": filters, "limits": ["Source identity/license/boundary checks only; not game quality or art acceptance.", "No network retrieval, REA reinstall, Godot package export, archive inspection, package execution, visual review or GPU test performed by this review.", "Scratch mesh candidate is identified by its retained mesh report; no GLB candidate is promoted or copied into runtime.", "Whole-wave final archive and any later seam implementation require their own freeze/inventory. This receipt pins only files observed here."]}
    with out.open("x") as f:
        json.dump(report, f, indent=2)
        f.write("\n")
    print(json.dumps({"status": report["status"], "checks": len(checks), "failed_checks": failures, "report": str(out)}))
    return bool(failures)

if __name__ == "__main__":
    raise SystemExit(main())
