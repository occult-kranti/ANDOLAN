# Mythic release and CI gates

The final focus fix changes the runtime source set. The MYTHIC-only routes now require `docs/evidence/mythic-ultimates-render-r3` and `docs/evidence/mythic-traversal-render-r2`. These two constants are the only validator changes since the preserved pre-focus source. Historical film, generic traversal, siege and Triad routes remain unchanged.

Current checks pass: 154 mythic release cases, 169 traversal cases, 78 siege cases and 106 Triad cases. All three declared source pins in the new mythic report match the current checkout. The exact new report also replaces `../setup/mythic-release-gates.json`; that setup report's predecessor is preserved under `../setup/pre-focus-correction/`.

The complete earlier release archive, sources, manifest and current-at-the-time r2 source-snapshot checks are preserved under `pre-focus-correction/`. Earlier pre-HUD evidence remains there and under `pre-hud-correction/`. Those snapshots do not establish the final focus-fixed runtime. The render owner declared the final sources frozen. The r3 ultimate archive now passes source validation and a fresh ffprobe decode against `package.source_state()`: 120 frames, 240 physics ticks and 293 source pins. All 16 canonical setup reports pass, including the current 113-case pause/focus integration gate. See `current-source-snapshot-check.json` and its input ledger. The final traversal capture is still rendering. Root must subsequently repeat capture/report validation against the actual `native-export-manifest.json`.

The existing strict gates are unchanged: all 16 typed MYTHIC reports must contain successful measured checks and current declared source pins; the full traversal take requires 180 frames and shader coverage; the ultimate take requires 120 frames, 240 physics ticks, 14 hero studies, three variants, six retained frames, exact event chronology, source inventory/import proof and a fresh movie decode. These are staged original VFX studies. Actual gameplay, input, package execution and GPU performance require their separate evidence.

## Reproduction

```sh
python3 games/yuga-native/tests/release_mythic_cases.py --report=/tmp/mythic-release-cases.json
python3 games/yuga-native/tests/release_traversal_cases.py --report=/tmp/traversal-release-cases.json
python3 games/yuga-native/tests/release_siege_cases.py --report=/tmp/siege-release-cases.json
python3 games/yuga-native/tests/release_triad_cases.py --report=/tmp/triad-release-cases.json
```

The setup script includes a project import, so root coordinates it with render ownership. This worker ran no imports, heavy renders, exports, commits, tags or publication.

## Final release sequence

1. Freeze the runtime and render helpers, complete both final capture archives, and run their validators with fresh decoding plus all 16 required report provenance checks.
2. Build packages and repeat validation against the actual export manifest. Preserve failed and earlier captures with their original source identities.
3. Commit the verified runtime, evidence, tools and tests. Build at the intended immutable commit; check that archives and export sources still match.
4. Stage the new `yuga-traversal-armies-2026-10-17-mythic` tag using the existing strict release workflow or `release-native.py stage`, then `verify`. Root owns authorized branch/tag publication and downloaded-release verification.
