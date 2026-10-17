#!/usr/bin/env python3
"""Independent adversarial PCK-directory fixtures; never execute a fixture pack.

These tiny v2 containers exercise packaging acceptance, not Godot scene validity.
The explicit resource names describe the expected native feature bundle. No
fixture contains a genuine credential or writes outside its temporary directory.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import tempfile

ROOT = Path(__file__).resolve().parents[1]
PACKAGER = ROOT / "tools/package-native.py"
NAMES = [
    "assets/audio/siege/provenance.json", "project.binary", "scenes/courtyard.tscn", "scenes/confluence_world.tscn",
    "scenes/combat_film.tscn", "assets/world/confluence-map.json",
    "assets/cinematics/confluence-duel.json", "shaders/production_water.gdshader",
    "shaders/world_water.gdshader", "shaders/world_ground.gdshader",
    "shaders/world_ground_common.gdshaderinc", "shaders/duel_energy.gdshader",
    "scripts/traversal_stone.gdshader",
    *[f".godot/imported/{name}-fixture.scn" for name in (
        "rama.glb", "rama-production.glb", "lanka_courtyard.glb",
        "architecture.glb", "nature.glb", "ravana-sentinel.glb")],
    "assets/cinematics/duel-motion-rama.tres", "assets/cinematics/duel-motion-ravana.tres",
    ".godot/imported/confluence-duel-mix.wav-fixture.sample",
    ".godot/imported/lane-procession-loop.wav-fixture.sample",
    *[f".godot/imported/{name}.wav-fixture.sample" for name in (
        "grapple_lock", "grapple_release", "flight_start", "flight_exhaust",
        "flight_recharge", "minion_hit", "coin", "cannon_windup", "cannon_impact", "chariot_windup", "chariot_impact")],
    *[f"scripts/{name}.gd" for name in (
        "input_bindings", "controls_overlay", "player_traversal", "traversal_pose", "traversal_landmarks",
        "lane_army", "lane_minion", "lane_unit_art", "traversal_audio", "lane_vehicle_art", "siege_effects")],
]


def pack(entries: list[tuple[str, bytes]], *, flags: int = 0, version: int = 2,
         count: int | None = None, entry_flags: int = 0) -> tuple[bytes, list[int]]:
    """Godot documented v2 header, padded directory names, absolute payload offsets."""
    encoded = []
    for name, payload in entries:
        raw = ("res://" + name).encode()
        raw += b"\0" * ((-len(raw)) % 4)
        encoded.append((raw, payload))
    start = 100 + sum(4 + len(name) + 36 for name, _ in encoded)
    start += (-start) % 16
    output = bytearray(struct.pack("<4s5IQ", b"GDPC", version, 4, 6, 3, flags, 0))
    output += bytes(64) + struct.pack("<I", len(entries) if count is None else count)
    positions = []
    payloads = bytearray()
    for name, payload in encoded:
        positions.append(len(output))
        output += struct.pack("<I", len(name)) + name
        output += struct.pack("<QQ", start + len(payloads), len(payload))
        output += hashlib.md5(payload).digest() + struct.pack("<I", entry_flags)
        payloads += payload
    output += bytes(start - len(output)) + payloads
    return bytes(output), positions


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    before = hashlib.sha256(PACKAGER.read_bytes()).hexdigest()
    spec = importlib.util.spec_from_file_location("native_packager_tested", PACKAGER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    entries = [(name, ("benign fixture for " + name).encode()) for name in NAMES]
    baseline, directory_positions = pack(entries)
    checks = []
    with tempfile.TemporaryDirectory(prefix="yuga-pack-security-") as temporary:
        target = Path(temporary) / "fixture.pck"

        def evaluate(name: str, data: bytes, accept: bool = False) -> None:
            target.write_bytes(data)
            try:
                result = module.inspect_pack(target)
                accepted = True
                detail = {"entry_count": result["entry_count"]}
            except (ValueError, struct.error, UnicodeDecodeError) as error:
                accepted = False
                detail = {"rejection": type(error).__name__ + ": " + str(error)}
            checks.append({"name": name, "passed": accepted == accept,
                           "expected": "accept" if accept else "reject", **detail})

        evaluate("structurally valid explicit native resource bundle", baseline, True)
        evaluate("magic rejected", b"NOPE" + baseline[4:])
        evaluate("truncated header rejected", baseline[:80])
        evaluate("encrypted pack rejected", pack(entries, flags=1)[0])
        evaluate("unknown pack version rejected", pack(entries, version=99)[0])
        evaluate("resource count above 10000 rejected", pack(entries, count=10001)[0])
        evaluate("zero resource count rejected", pack(entries, count=0)[0])
        evaluate("encrypted entry rejected", pack(entries, entry_flags=1)[0])
        evaluate("duplicate entry rejected", pack(entries + [entries[0]])[0])
        for name, bad_name in [
            ("parent path", "scripts/../escape.gd"),
            ("absolute path", "/scripts/escape.gd"),
            ("backslash path", "scripts\\escape.gd"),
            ("unapproved directory", "tools/escape.py"),
            ("unapproved Godot cache directory", ".godot/editor/config.cfg"),
            ("credential filename", "scripts/access-token.txt"),
            ("dotenv filename", "assets/.env"),
            ("overlong resource path", "scripts/" + "a" * 4096),
        ]:
            evaluate(name + " rejected", pack(entries + [(bad_name, b"benign")])[0])
        evaluate("synthetic credential marker rejected", pack(entries + [
            ("assets/marker.txt", b"ghp_" + b"A" * 40)])[0])
        evaluate("private-key header marker rejected", pack(entries + [
            ("assets/marker.txt", b"-----BEGIN PRIVATE KEY-----\nfixture")])[0])
        evaluate("missing essential army resource rejected", pack([
            entry for entry in entries if entry[0] != "scripts/lane_army.gd"])[0])
        evaluate("missing native platform stone shader rejected", pack([
            entry for entry in entries if entry[0] != "scripts/traversal_stone.gdshader"])[0])
        for missing in ("assets/audio/siege/provenance.json", "scripts/lane_vehicle_art.gd", "scripts/siege_effects.gd", ".godot/imported/cannon_windup.wav-fixture.sample", ".godot/imported/cannon_impact.wav-fixture.sample", ".godot/imported/chariot_windup.wav-fixture.sample", ".godot/imported/chariot_impact.wav-fixture.sample"):
            evaluate("missing siege resource rejected: " + missing, pack([entry for entry in entries if entry[0] != missing])[0])
        corrupt = bytearray(baseline)
        corrupt[-1] ^= 1
        evaluate("payload checksum corruption rejected", bytes(corrupt))
        corrupt = bytearray(baseline)
        first = directory_positions[0]
        name_length = struct.unpack_from("<I", corrupt, first)[0]
        struct.pack_into("<Q", corrupt, first + 4 + name_length, len(corrupt) + 1)
        evaluate("payload offset beyond file rejected", bytes(corrupt))
        corrupt = bytearray(baseline)
        struct.pack_into("<Q", corrupt, first + 12 + name_length, 2**63)
        evaluate("oversize payload length rejected", bytes(corrupt))
        evaluate("truncated directory rejected", baseline[:103])
        evaluate("canonical fixture remains accepted after mutations", baseline, True)
    after = hashlib.sha256(PACKAGER.read_bytes()).hexdigest()
    checks.append({"name": "tested packager unchanged", "passed": before == after})
    report = {"passed": all(c["passed"] for c in checks), "checks": checks,
              "sources": {"tools/package-native.py": before,
                          "tests/traversal_security_cases.py": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
              "scope": "Bounded structural PCK acceptance fixtures only. No pack execution, extraction, production secrets, runtime security certificate, online security or full parser fuzzing claim."}
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"passed": report["passed"], "checks": len(checks),
                      "failed": [c for c in checks if not c["passed"]]}, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
