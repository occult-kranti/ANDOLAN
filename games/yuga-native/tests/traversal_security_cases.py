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
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
PACKAGER = ROOT / "tools/package-native.py"
INVOCATION_NAMES = [
    "assets/design/hero-codex.json", "assets/design/native-ultimate-rules.json",
    "assets/audio/invocations/manifest.json",
    *[f"scripts/{name}.gd" for name in (
        "ultimate_rules", "ultimate_session", "ultimate_effects", "invocation_panel", "invocation_audio")],
    *[f".godot/imported/{name}.wav-fixture.sample" for name in (
        "windup", "cancel", "rama-release", "ravana-release", "arjuna-release",
        "duryodhana-release", "hanuman-release", "karna-release", "bhima-release",
        "meghnad-release", "sita-release", "draupadi-release", "subhadra-release",
        "hidimbi-release", "chitrangada-release", "ulupi-release")],
]
RAMA_NAMES = [
    ".godot/imported/rama-hero.glb-fixture.scn",
    "assets/animations/rama_hero_motion.tres", "assets/design/rama-ability-kit.json",
    "shaders/rama_ribbon.gdshader",
    *[f"scripts/{name}.gd" for name in (
        "rama_ability_kit", "rama_ability_effects", "rama_hero_runtime", "rama_vitals",
        "rama_motion", "rama_hero_hud", "rama_hero_panel", "hero_ui_theme",
        "rama_practice_army", "rama_practice_target")],
]
FIRST_LOAD_NAMES = ['scenes/boot.tscn', 'scripts/boot.gd',
                    'scripts/scene_transition.gd', 'scripts/loading_presentation.gd', 'scripts/launch_shell.gd',
                    'scripts/hero_ui_theme.gd', 'scripts/ui_scroll_focus.gd']
GRAPHICS_NAMES = [
    'scripts/lane_infantry_art.gd', 'scripts/environment_surface_finish.gd',
    'scripts/rama_ability_glyph.gd', 'scripts/rama_surface_finish.gd',
    'scripts/world_roof_loggia.gd', 'scripts/world_lane_frontage.gd', 'scripts/world_render_resources.gd',
    'assets/environment-finish/masonry.gdshader', 'assets/hero-finish/g1-manifest.json',
    'assets/hero-finish/s1-manifest.json', 'assets/world/block2-frontage.json',
]
GRAPHICS_TEXTURE_FIXTURES = {
    'assets/hero-finish/hair-bundle-roughness.png':
        '.godot/imported/hair-bundle-roughness.png-72ae2ebe2b8005e106f441ea2c4cfa15.ctex',
    'assets/hero-finish/forged-gold-roughness.png':
        '.godot/imported/forged-gold-roughness.png-80aebbe05d54ced6709fe5d72aaa378a.ctex',
    'assets/hero-finish/s1-hammered-gold-roughness.png':
        '.godot/imported/s1-hammered-gold-roughness.png-c93c92f35fe086748d0140298caef508.ctex',
}
NAMES = [
    *GRAPHICS_NAMES,
    *INVOCATION_NAMES,
    *RAMA_NAMES,
    *[name for name in FIRST_LOAD_NAMES if name not in RAMA_NAMES],
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
        "lane_army", "lane_minion", "lane_unit_art", "traversal_audio", "lane_vehicle_art", "siege_effects",
        "relay_control", "relay_session", "relay_art")],
]


def pack(entries: list[tuple[str, bytes]], *, flags: int = 0, version: int = 2,
         count: int | None = None, entry_flags: int = 0,
         prefix_names: bool = True) -> tuple[bytes, list[int]]:
    """Godot documented v2 header, padded directory names, absolute payload offsets."""
    encoded = []
    for name, payload in entries:
        raw = (("res://" if prefix_names else "") + name).encode()
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
    for source, target in GRAPHICS_TEXTURE_FIXTURES.items():
        entries.extend([(source + '.import', f'[remap]\npath="res://{target}"\n'.encode()),
                        (target, b'benign structural texture fixture; not engine-decodable')])
    baseline, directory_positions = pack(entries)
    checks = []
    with tempfile.TemporaryDirectory(prefix="yuga-pack-security-") as temporary:
        target = Path(temporary) / "fixture.pck"

        def evaluate(name: str, data: bytes, accept: bool = False,
                     rejection_contains: str | None = None) -> None:
            target.write_bytes(data)
            try:
                result = module.inspect_pack(target)
                accepted = True
                detail = {"entry_count": result["entry_count"]}
            except (ValueError, struct.error, UnicodeDecodeError) as error:
                accepted = False
                detail = {"rejection": type(error).__name__ + ": " + str(error)}
            correct_reason = rejection_contains is None or rejection_contains in detail.get("rejection", "")
            checks.append({"name": name, "passed": accepted == accept and correct_reason,
                           "expected": "accept" if accept else "reject", **detail,
                           **({"required_rejection": rejection_contains} if rejection_contains else {})})

        evaluate("structurally valid explicit native resource bundle", baseline, True)
        evaluate("magic rejected", b"NOPE" + baseline[4:])
        evaluate("truncated header rejected", baseline[:80])
        evaluate("encrypted pack rejected", pack(entries, flags=1)[0])
        evaluate("unknown pack version rejected", pack(entries, version=99)[0])
        evaluate("resource count above 10000 rejected", pack(entries, count=10001)[0])
        evaluate("zero resource count rejected", pack(entries, count=0)[0])
        evaluate("encrypted entry rejected", pack(entries, entry_flags=1)[0])
        evaluate("duplicate entry rejected", pack(entries + [entries[0]])[0])
        evaluate("canonical bare paths remain accepted", pack(entries, prefix_names=False)[0], True)
        for alias in ("scripts/./boot.gd", "scripts//boot.gd", "scripts/boot.gd/",
                      "./scripts/boot.gd", "scripts/./boot.gd.remap"):
            evaluate("noncanonical first-load alias rejected: " + alias,
                     pack(entries + [(alias, b'conflicting structural fixture')])[0],
                     rejection_contains='Unsafe or duplicate pack path: ')
        for duplicate in ('scripts/boot.gd', 'scripts/relay_control.gd'):
            mixed = [('res://' + name, value) for name, value in entries] + [(duplicate, b'alias')]
            evaluate('bare/res duplicate identity rejected: ' + duplicate,
                     pack(mixed, prefix_names=False)[0], rejection_contains='Unsafe or duplicate pack path: ')
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
        for missing in ("scripts/relay_control.gd", "scripts/relay_session.gd", "scripts/relay_art.gd", "assets/audio/siege/provenance.json", "scripts/lane_vehicle_art.gd", "scripts/siege_effects.gd", ".godot/imported/cannon_windup.wav-fixture.sample", ".godot/imported/cannon_impact.wav-fixture.sample", ".godot/imported/chariot_windup.wav-fixture.sample", ".godot/imported/chariot_impact.wav-fixture.sample"):
            evaluate("missing siege resource rejected: " + missing, pack([entry for entry in entries if entry[0] != missing])[0])
        for missing in INVOCATION_NAMES:
            evaluate("missing invocation resource rejected: " + missing, pack([entry for entry in entries if entry[0] != missing])[0])
        for missing in RAMA_NAMES:
            token = "rama-hero.glb-" if missing.startswith(".godot/imported/") else missing
            evaluate("missing Rama resource rejected: " + missing,
                     pack([entry for entry in entries if entry[0] != missing])[0],
                     rejection_contains="Required runtime resource missing: " + token)
        for missing in FIRST_LOAD_NAMES:
            # hero_ui_theme is also an older mandatory Rama dependency.
            reason = 'Required runtime resource missing: ' if missing in RAMA_NAMES else 'Required first-load resource missing or ambiguous: '
            evaluate('missing first-load dependency rejected: ' + missing,
                     pack([entry for entry in entries if entry[0] != missing])[0],
                     rejection_contains=reason + missing)
            renamed = [(name + '-extra' if name == missing else name, value) for name, value in entries]
            evaluate('first-load substring substitution rejected: ' + missing, pack(renamed)[0],
                     rejection_contains='Required first-load resource missing or ambiguous: ' + missing)
        remapped = [entry for entry in entries if entry[0] not in FIRST_LOAD_NAMES]
        targets = {}
        for source in FIRST_LOAD_NAMES:
            compiled_path = source + 'c' if source.endswith('.gd') else '.godot/exported/123/export-' + 'a' * 32 + '-boot.scn'
            targets[source] = compiled_path
            remapped += [(source + '.remap', ('[remap]\n\npath="res://' + compiled_path + '"\n').encode()),
                         (compiled_path, ('structural compiled fixture ' + source).encode())]
        evaluate('current Godot compiled-script and scene remap layout accepts', pack(remapped)[0], True)
        evaluate('compiled target noncanonical alias rejected',
                 pack(remapped + [('scripts/./boot.gdc', b'compiled alias')])[0],
                 rejection_contains='Unsafe or duplicate pack path: ')
        for source, compiled_path in targets.items():
            evaluate('missing first-load remap destination rejected: ' + source,
                     pack([entry for entry in remapped if entry[0] != compiled_path])[0],
                     rejection_contains='First-load remap destination missing or ambiguous: ' + source)
        source = 'scripts/boot.gd'
        for label, replacement in (
                ('wrong section', b'[deps]\npath="res://scripts/boot.gdc"\n'),
                ('default section injection', b'[DEFAULT]\npath="res://scripts/boot.gdc"\n[remap]\n'),
                ('duplicate key', b'[remap]\npath="res://scripts/boot.gdc"\npath="res://scripts/boot.gdc"\n'),
                ('other script substitution', b'[remap]\npath="res://scripts/launch_shell.gdc"\n'),
                ('parent traversal', b'[remap]\npath="res://scripts/../boot.gdc"\n'),
                ('self-remap cycle', b'[remap]\npath="res://scripts/boot.gd.remap"\n')):
            changed = [(name, replacement if name == source + '.remap' else value) for name, value in remapped]
            evaluate('first-load remap ' + label + ' rejected', pack(changed)[0])
        changed = [(name, value.replace(b'-boot.scn', b'-courtyard.scn') if name == 'scenes/boot.tscn.remap' else value)
                   for name, value in remapped]
        evaluate('first-load scene remapped to other scene rejects', pack(changed)[0])
        evaluate('ambiguous direct and remapped first-load source rejects', pack(remapped + [(source, b'direct fixture')])[0])
        roof = 'scripts/world_roof_loggia.gd'
        evaluate('missing active world roof dependency rejects',
                 pack([entry for entry in entries if entry[0] != roof])[0],
                 rejection_contains='Required first-load resource missing or ambiguous: ' + roof)
        evaluate('world roof filename substitution rejects',
                 pack([(name + '-extra' if name == roof else name, value) for name, value in entries])[0],
                 rejection_contains='Required first-load resource missing or ambiguous: ' + roof)
        compiled_roof = [entry for entry in entries if entry[0] != roof] + [
            (roof + '.remap', b'[remap]\npath="res://scripts/world_roof_loggia.gdc"\n'),
            (roof + 'c', b'benign compiled roof fixture')]
        evaluate('compiled world roof remap accepts', pack(compiled_roof)[0], True)
        evaluate('orphan world roof remap rejects',
                 pack([entry for entry in compiled_roof if entry[0] != roof + 'c'])[0],
                 rejection_contains='First-load remap destination missing or ambiguous: ' + roof)
        resource_pool = 'scripts/world_render_resources.gd'
        evaluate('missing world primitive pool rejects',
                 pack([entry for entry in entries if entry[0] != resource_pool])[0],
                 rejection_contains='Required first-load resource missing or ambiguous: ' + resource_pool)
        compiled_pool = [entry for entry in entries if entry[0] != resource_pool] + [
            (resource_pool + '.remap', b'[remap]\npath="res://scripts/world_render_resources.gdc"\n'),
            (resource_pool + 'c', b'benign compiled primitive pool fixture')]
        evaluate('compiled world primitive pool remap accepts', pack(compiled_pool)[0], True)
        evaluate('orphan world primitive pool remap rejects',
                 pack([entry for entry in compiled_pool if entry[0] != resource_pool + 'c'])[0],
                 rejection_contains='First-load remap destination missing or ambiguous: ' + resource_pool)
        frontage = 'scripts/world_lane_frontage.gd'
        frontage_data = 'assets/world/block2-frontage.json'
        for resource, reason in (
                (frontage, 'Required first-load resource missing or ambiguous: '),
                (frontage_data, 'Required graphics resource missing: ')):
            evaluate('missing frontage dependency rejects: ' + resource,
                     pack([entry for entry in entries if entry[0] != resource])[0],
                     rejection_contains=reason + resource)
            evaluate('frontage filename substitution rejects: ' + resource,
                     pack([(name + '-extra' if name == resource else name, value)
                           for name, value in entries])[0], rejection_contains=reason + resource)
        compiled_frontage = [entry for entry in entries if entry[0] != frontage] + [
            (frontage + '.remap', b'[remap]\npath="res://scripts/world_lane_frontage.gdc"\n'),
            (frontage + 'c', b'benign compiled frontage fixture')]
        evaluate('compiled frontage remap accepts', pack(compiled_frontage)[0], True)
        evaluate('orphan frontage remap rejects',
                 pack([entry for entry in compiled_frontage if entry[0] != frontage + 'c'])[0],
                 rejection_contains='First-load remap destination missing or ambiguous: ' + frontage)
        evaluate('frontage remap to another script rejects',
                 pack([(name, value.replace(b'world_lane_frontage.gdc', b'world_roof_loggia.gdc')
                        if name == frontage + '.remap' else value)
                       for name, value in compiled_frontage])[0],
                 rejection_contains='First-load resource remaps to an unexpected target: ' + frontage)
        source_payload = dict(entries)[frontage_data]
        source_files = {frontage_data: {'bytes': len(source_payload),
                                      'sha256': hashlib.sha256(source_payload).hexdigest()}}
        for label, fixture, sources, accept in (
                ('exact frontage JSON source binding accepts', entries, source_files, True),
                ('same-name substituted frontage JSON rejects',
                 [(name, source_payload[:-1] + b'?' if name == frontage_data else value)
                  for name, value in entries], source_files, False),
                ('missing frontage source record rejects', entries, {}, False)):
            target.write_bytes(pack(fixture)[0])
            failure = None
            try:
                module.qualify_world_frontage_package(module.inspect_pack(target), sources)
            except ValueError as error:
                failure = str(error)
            checks.append({'name': label, 'passed': (failure is None) == accept
                           and (accept or 'Frontage PCK data differs from runtime source snapshot' in failure),
                           'rejection': failure})
        live_source = {'sha256': 'unchanged-source-signature', 'files': source_files}
        forged_source = {'sha256': live_source['sha256'], 'files': {
            frontage_data: {**source_files[frontage_data], 'sha256': '0' * 64}}}
        exported = {'engine_selection': {}, 'godot_version': 'fixture',
                    'native_contracts': {}, 'source': forged_source}
        with patch.object(module, 'linux_engine_selection', return_value={'exporter': {'version': 'fixture'}}), \
                patch.object(module, 'prove_native_contract_sources', return_value={}), \
                patch.object(module, 'source_state', return_value=live_source):
            failure = None
            try:
                module.package_all(argparse.Namespace(), Path(temporary), exported)
            except ValueError as error:
                failure = str(error)
        checks.append({'name': 'package rejects forged source files despite unchanged signature',
                       'passed': failure == 'Runtime sources changed since PCK export; export again before packaging',
                       'rejection': failure})
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
              "scope": "Bounded structural PCK acceptance and exact frontage JSON source-binding fixtures only. No pack execution, extraction, production secrets, runtime security certificate, online security or full parser fuzzing claim."}
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"passed": report["passed"], "checks": len(checks),
                      "failed": [c for c in checks if not c["passed"]]}, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
