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
    check("per_profile_content_revisions", [p.get("content_revision") for p in data["profiles"]] == [1, 8, 1])
    check("wire_versions_unchanged", data["envelope_versions"] == {key: 1 for key in ["contract", "rules", "map", "content", "replay", "input", "event", "entity"]})
    # Preserve the exact previously accepted catalog and its Godot-derived
    # descriptor. Revision 8 changes only army/status presentation identities;
    # it does not redefine browser/production or claim all art is wire-pinned.
    old_catalog_path = NATIVE / "tests/fixtures/contracts/native-content4-catalog.json"
    old_descriptor_path = NATIVE / "tests/fixtures/contracts/native-content4-descriptor.json"
    check("preserved_revision4_catalog_exact_bytes", digest(old_catalog_path) == "f28949365043db23b379f68aadee4be8bfccd7c4fce5cd53322dd66882d51371")
    check("preserved_revision4_descriptor_exact_bytes", digest(old_descriptor_path) == "2edd08196bb789a1ac2b4c095297513e719a113d0796bcb83bf949714f8a3d82")
    old_catalog = json.loads(old_catalog_path.read_text())
    revision5_catalog_path = NATIVE / "tests/fixtures/contracts/native-content5-catalog.json"
    revision5_descriptor_path = NATIVE / "tests/fixtures/contracts/native-content5-descriptor.json"
    check("preserved_revision5_catalog_exact_bytes", digest(revision5_catalog_path) == "509ef9860dfc32ed0c9dd064bdd011feef01d9b6c90db755aa9c5e37bf29aae2")
    check("preserved_revision5_descriptor_exact_bytes", digest(revision5_descriptor_path) == "f220b47c699754590d6415f500c6b5ff9793343a2e506d1a55af080497dd33a0")
    revision5_catalog = json.loads(revision5_catalog_path.read_text())
    check("other_profiles_unchanged_from_revision5", all(data["profiles"][i] == revision5_catalog["profiles"][i] for i in (0, 2)))
    check("top_level_wire_coordinates_limits_unchanged_from_revision5", {k:v for k,v in data.items() if k != "profiles"} == {k:v for k,v in revision5_catalog.items() if k != "profiles"})
    old_native = old_catalog["profiles"][1]
    revision5_native = revision5_catalog["profiles"][1]
    historical_changed_paths = {path for path in revision5_native["content_sources"] if revision5_native["content_sources"][path] != old_native["content_sources"].get(path)}
    check("preserved_revision4_to5_changes_only_player_source_pin", set(revision5_native["content_sources"]) == set(old_native["content_sources"]) and historical_changed_paths == {"games/yuga-native/scripts/player.gd"})
    revision6_catalog_path = NATIVE / "tests/fixtures/contracts/native-content6-catalog.json"
    revision6_descriptor_path = NATIVE / "tests/fixtures/contracts/native-content6-descriptor.json"
    check("preserved_revision6_catalog_exact_bytes", digest(revision6_catalog_path) == "865039f65c0128919fb140b4c5564ba8c56c6877ecb6446f899aaac80c25f819")
    check("preserved_revision6_descriptor_exact_bytes", digest(revision6_descriptor_path) == "9893004eca892223140ecee3a06f504460875d71cd890846729e9cb4370707bf")
    revision6_catalog = json.loads(revision6_catalog_path.read_text())
    revision6_native = revision6_catalog["profiles"][1]
    historical_changed_paths6 = {path for path in revision6_native["content_sources"] if revision6_native["content_sources"][path] != revision5_native["content_sources"].get(path)}
    check("preserved_revision5_to6_changes_only_player_source_pin", set(revision6_native["content_sources"]) == set(revision5_native["content_sources"]) and historical_changed_paths6 == {"games/yuga-native/scripts/player.gd"})
    revision7_catalog_path = NATIVE / "tests/fixtures/contracts/native-content7-catalog.json"
    revision7_descriptor_path = NATIVE / "tests/fixtures/contracts/native-content7-descriptor.json"
    check("preserved_revision7_catalog_exact_bytes", digest(revision7_catalog_path) == "cfb956462042a867f6ac1a51d7be77fc98310acfae8d15d112456fc2a19eb191")
    check("preserved_revision7_descriptor_exact_bytes", digest(revision7_descriptor_path) == "7ea8e560742081487df9d8b15b25e122b2f2a363fa6bead4f569559dd63354ef")
    revision7_native = json.loads(revision7_catalog_path.read_text())["profiles"][1]
    changed_paths7 = {path for path in revision7_native["content_sources"] if revision7_native["content_sources"][path] != revision6_native["content_sources"].get(path)}
    check("revision7_changes_only_minion_source_pin", set(revision7_native["content_sources"]) == set(revision6_native["content_sources"]) and changed_paths7 == {"games/yuga-native/scripts/lane_minion.gd"})
    check("revision7_preserves_noncontent_native_rules", all(revision7_native[key] == value for key, value in revision6_native.items() if key not in ("content_sources", "content_revision", "content_sha256")))
    current_native = data["profiles"][1]
    changed_paths = {path for path in current_native["content_sources"] if current_native["content_sources"][path] != revision7_native["content_sources"].get(path)}
    check("revision8_changes_only_army_and_minion_source_pins", set(current_native["content_sources"]) == set(revision7_native["content_sources"]) and changed_paths == {"games/yuga-native/scripts/lane_army.gd", "games/yuga-native/scripts/lane_minion.gd"})
    check("revision8_preserves_noncontent_native_rules", all(current_native[key] == value for key, value in revision7_native.items() if key not in ("content_sources", "content_revision", "content_sha256")))

    required_native = {"games/yuga-native/" + path for path in ["scripts/lane_army.gd", "scripts/lane_minion.gd", "scripts/relay_control.gd", "scripts/player_traversal.gd", "scripts/ultimate_rules.gd", "scripts/ultimate_session.gd", "assets/design/native-ultimate-rules.json", "scripts/player.gd", "scripts/rama_ability_kit.gd", "scripts/rama_hero_runtime.gd", "scripts/rama_vitals.gd", "scripts/rama_practice_army.gd", "scripts/rama_practice_target.gd", "assets/design/rama-ability-kit.json", "scripts/rama_action_buffer.gd"]}
    check("native_revision8_retains_existing_authority_sources", set(data["profiles"][1]["content_sources"]) == required_native)
    check("native_hero_health_declared_and_vitals_pinned", data["profiles"][1]["features"]["hero_health"] is True and "scripts/rama_vitals.gd" in " ".join(required_native))
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
