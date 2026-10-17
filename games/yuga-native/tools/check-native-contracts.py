#!/usr/bin/env python3
"""Check contract source pins and separation without importing/rendering the game."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
NATIVE = ROOT / "games/yuga-native"
CATALOG = NATIVE / "assets/contracts/native-contracts-v1.json"
SCHEMA = NATIVE / "assets/contracts/native-envelope-v1.schema.json"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    checks = []

    def check(name, value, evidence=None):
        checks.append({"name": name, "passed": bool(value), "evidence": evidence or {}})

    data = json.loads(CATALOG.read_text())
    schema = json.loads(SCHEMA.read_text())
    check("three_exact_profiles", [p["id"] for p in data["profiles"]] == ["browser-p2-3v3", "native-offline-triad", "production-6v6"])
    map_sources = ["games/yuga/shared/map.ts", "games/yuga-native/assets/world/confluence-map.json", "games/yuga-native/docs/GAME_DESIGN_MASTER.md"]
    for profile, source in zip(data["profiles"], map_sources):
        check(profile["id"] + "_map_pin", digest(ROOT / source) == profile["map_sha256"], {"source": source, "scope": profile["map_digest_scope"]})
        for path, sha in profile["content_sources"].items():
            resolved = (ROOT / path).resolve()
            valid_path = resolved.is_relative_to(ROOT) and resolved.is_file()
            check(profile["id"] + "_content_" + path, valid_path and digest(resolved) == sha)
        canonical = json.dumps(profile["content_sources"], sort_keys=True, separators=(",", ":")).encode()
        check(profile["id"] + "_content_aggregate", hashlib.sha256(canonical).hexdigest() == profile["content_sha256"])
        check(profile["id"] + "_no_live_handshake_claim", profile["live_handshake"] is False)
    types = (ROOT / "games/yuga/shared/types.ts").read_text()
    map_text = (ROOT / "games/yuga/shared/map.ts").read_text()
    check("actual_browser_protocol_still_two", "export const YUGA_PROTOCOL = 2;" in types)
    check("actual_browser_default_geometry_time", "width: 140, depth: 170" in map_text and "duration: 480" in map_text)
    actor_type = types.split("export interface Actor ", 1)[1].split("export interface Neutral ", 1)[0]
    check("actor_remote_pitch_still_missing_not_fabricated", "pitch:" not in actor_type)
    native_map = json.loads((ROOT / map_sources[1]).read_text())
    check("native_map_dimensions_match_profile", native_map["bounds"]["nominal_size_xz"] == [140, 260])
    relay_source = (NATIVE / "scripts/relay_control.gd").read_text()
    check("triad_sites_are_pinned_rules_not_invented_map_fields", 'const SITE_X := [-40.0, 0.0, 40.0]' in relay_source and 'const LABELS := ["Reed Relay", "Lotus Relay", "Sky Relay"]' in relay_source)
    definitions = schema["$defs"]
    check("schema_v1_contains_all_streams", set(definitions) == {"descriptor", "input", "event", "entity", "snapshot", "replay_header", "replay_record"})
    check("schema_pose_requires_pitch_and_lifetimes", all(k in definitions["entity"]["required"] for k in ["generation", "pitch", "discontinuity", "ack_input"]))
    check("schema_v1_closed_records", all(d.get("additionalProperties") is False for k, d in definitions.items() if k != "replay_record"))
    check("schema_no_external_resource_loading", "http" not in json.dumps(definitions))
    report = {"passed": all(c["passed"] for c in checks), "checks": checks, "source_sha256": {str(p.relative_to(ROOT)): digest(p) for p in [CATALOG, SCHEMA, Path(__file__).resolve(), NATIVE / "scripts/native_contracts.gd"]}, "scope": "Source pin and contract/schema consistency. No runtime migration, network, render or collision authority evidence."}
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"passed": report["passed"], "checks": len(checks), "failures": [c for c in checks if not c["passed"]]}, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
