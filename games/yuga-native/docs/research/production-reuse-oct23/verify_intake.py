#!/usr/bin/env python3
"""Recheck the retained source kit and receipts; never fetch or render."""
import hashlib
import json
from pathlib import Path
import struct


DOCS = Path(__file__).resolve().parent
REPO = DOCS.parents[4]
KIT = REPO / "games/yuga-native/art/source-kits/production-reuse-oct23/sandstone-blocks-05"


def checked_file(root, relative):
    candidate = root / relative
    assert not candidate.is_symlink(), f"Symlink source refused: {relative}"
    resolved = candidate.resolve(strict=True)
    assert resolved.is_relative_to(root.resolve()), f"Source leaves retained root: {relative}"
    assert resolved.is_file(), f"Expected regular file: {relative}"
    return resolved


def main():
    manifest_path = KIT / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    receipt = json.loads((DOCS / "evidence/godot-intake.json").read_text())
    assert hashlib.sha256(manifest_path.read_bytes()).hexdigest() == receipt["texture_manifest_sha256"]
    assert manifest["asset_license"] == "CC0-1.0" and manifest["runtime_promoted"] is False
    assert manifest["asset_id"] == "sandstone_blocks_05" and manifest["dimensions_m"] == [3, 3]
    assert {entry["role"] for entry in manifest["files"]} == {"Diffuse", "nor_gl", "Rough"}
    total = 0
    for entry in manifest["files"]:
        blob = checked_file(KIT, entry["file"]).read_bytes()
        assert len(blob) == entry["bytes"] == entry["expected_bytes"]
        assert hashlib.sha256(blob).hexdigest() == entry["sha256"]
        assert hashlib.md5(blob).hexdigest() == entry["md5"] == entry["publisher_md5"]
        assert blob[:8] == b"\x89PNG\r\n\x1a\n" and struct.unpack(">II", blob[16:24]) == (1024, 1024)
        total += len(blob)
    assert total == 6_220_633 and total < 15_000_000
    license_bytes = checked_file(KIT, "LICENSES/CC0-1.0.txt").read_bytes()
    assert hashlib.sha256(license_bytes).hexdigest() == "a2010f343487d3f7618affe54f789f5487602331c0a8d03f49e9a7c547cf0499"
    for name, expected in receipt["fixture_hashes"].items():
        assert hashlib.sha256(checked_file(KIT, name).read_bytes()).hexdigest() == expected
    assert len(receipt["checks"]) == 2 and all(c["exit_code"] == 0 for c in receipt["checks"])
    result = json.loads((DOCS / "evidence/godot-material.stdout.txt").read_text().splitlines()[-1])
    assert result["status"] == "PASS" and result["textures"] == 3 and result["rendered"] is False
    retained_checks = 0
    ledger = json.loads((DOCS / "source-ledger.json").read_text())
    for source in ledger["sources"]:
        if "retained_file" not in source:
            continue
        blob = checked_file(DOCS, source["retained_file"]).read_bytes()
        assert len(blob) == source["bytes"] and hashlib.sha256(blob).hexdigest() == source["sha256"]
        retained_checks += 1
    optimizer = json.loads((DOCS / "evidence/diya-static-preflight-qualified.json").read_text())
    assert optimizer["exit_code"] == 1 and optimizer["candidate_created"] is False
    assert optimizer["stderr"].strip() == "Unsupported extension: EXT_texture_webp"
    assert optimizer["input_sha256_before"] == optimizer["input_sha256_after"]
    print(json.dumps({"status": "PASS", "maps": 3, "bytes": total, "fixture_files": 3,
                      "retained_source_hashes": retained_checks, "actual_godot_checks": 2,
                      "optimizer_result": "expected unsupported-extension refusal",
                      "scope": "Retained bytes and receipts only; no new engine/render or visual acceptance"}))


if __name__ == "__main__":
    main()
