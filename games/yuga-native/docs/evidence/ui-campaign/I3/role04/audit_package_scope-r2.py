#!/usr/bin/env python3
"""Read-only I3-04 package identity and scoped compiled HUD/authority payload audit."""
import argparse
import hashlib
import json
import struct
from pathlib import Path


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    manifest_path = args.package / "native-package-manifest.json"
    export_path = args.package / "native-export-manifest.json"
    manifest = json.loads(manifest_path.read_text())
    exported = json.loads(export_path.read_text())
    linux = manifest["packages"]["linux"]
    folder = args.package / "yuga-native-linux-x86_64"
    pack = (folder / "yuga-native.pck").read_bytes()
    checks = {
        "expected_commit": manifest["git"]["head"] == exported["git"]["head"] == "83f88f840c59934155aec19d95b41d920d15c6c1",
        "archive_sha256": digest((args.package / linux["filename"]).read_bytes()) == linux["sha256"],
        "pck_sha256": digest(pack) == linux["pck"]["sha256"] == exported["packs"]["linux"]["sha256"],
        "bundled_engine_sha256": digest((folder / "godot").read_bytes()) == linux["engine"]["sha256"],
    }
    assert pack[:4] == b"GDPC"
    version, major, minor, patch, flags = struct.unpack_from("<5I", pack, 4)
    assert version in (2, 3) and (major, minor, patch) == (4, 6, 3) and not flags & ~2
    base = struct.unpack_from("<Q", pack, 24)[0]
    cursor = struct.unpack_from("<Q", pack, 32)[0] if version == 3 else 96
    count = struct.unpack_from("<I", pack, cursor)[0]
    cursor += 4
    payloads = {}
    for _ in range(count):
        length = struct.unpack_from("<I", pack, cursor)[0]
        cursor += 4
        name = pack[cursor:cursor + length].rstrip(b"\0").decode().removeprefix("res://")
        cursor += length
        offset, size = struct.unpack_from("<QQ", pack, cursor)
        stored_md5 = pack[cursor + 16:cursor + 32]
        entry_flags = struct.unpack_from("<I", pack, cursor + 32)[0]
        cursor += 36
        assert not entry_flags and name not in payloads and base + offset + size <= len(pack)
        payloads[name] = (pack[base + offset:base + offset + size], stored_md5)
    expected = {x["path"].removeprefix("res://"): x for x in exported["packs"]["linux"]["entries"]}
    stems = ["rama_hero_hud", "world_atlas", "world_outcome_summary", "confluence_world", "player", "rama_motion", "rama_hero_runtime", "rama_ability_kit", "lane_army", "relay_control", "relay_session", "rama_vitals", "hero_ui_theme"]
    rows = []
    for stem in stems:
        for suffix in (".gdc", ".gd.remap"):
            name = "scripts/" + stem + suffix
            payload, stored_md5 = payloads[name]
            row = {"path": name, "bytes": len(payload), "sha256": digest(payload), "md5_valid": hashlib.md5(payload).digest() == stored_md5, "matches_export_receipt": digest(payload) == expected[name]["sha256"]}
            rows.append(row)
    checks["all_scoped_compiled_and_remap_payloads"] = all(x["md5_valid"] and x["matches_export_receipt"] for x in rows)
    checks["entry_count_matches_export"] = count == 519 == exported["packs"]["linux"]["entry_count"]
    result = {"task": "I3-04", "passed": all(checks.values()), "checks": checks, "source_commit": manifest["git"]["head"], "runtime_source_signature": manifest["runtime_source_sha256"], "package": linux, "manifest_sha256": digest(manifest_path.read_bytes()), "export_receipt_sha256": digest(export_path.read_bytes()), "scoped_payloads": rows, "scope": "Actual archive/executable/PCK hash audit and 26 compiled/remap payloads against same-export receipt. No decompilation, native execution, visual or clock acceptance; centralized package capture remains a separate gate."}
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"passed": result["passed"], "checks": len(checks), "scoped_payloads": len(rows)}))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
