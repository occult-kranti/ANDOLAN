# Mythic release and CI gates

The final focus fix changes the runtime source set. The MYTHIC-only routes now require `docs/evidence/mythic-ultimates-render-r3` and `docs/evidence/mythic-traversal-render-r2`. The two MYTHIC capture constants select the final archives. A subsequent release-note correction makes MYTHIC tags require `docs/RELEASE_MYTHIC_INVOCATIONS.md` and use the title “YUGA mythic invocations — native preview”. It prevents reuse of Triad notes that describe videos absent from this release. Historical film, generic traversal, siege and Triad routes remain unchanged.

Current checks pass: 155 mythic release cases (all prior 154 plus missing-note rejection), 169 traversal cases, 78 siege cases and 106 Triad cases. The valid stage fixture also checks that the distinct MYTHIC body was selected. Five mocked publication cases confirm MYTHIC, traversal, siege, Triad and duel title selection; no network calls were made. All three declared source pins in the new mythic report match the current checkout. The exact new report also replaces `../setup/mythic-release-gates.json`; that setup report's predecessor is preserved under `../setup/pre-focus-correction/`.

The prior sources, reports and handoff for the release-note change are preserved under `pre-release-notes-correction/`; its manifest describes paths retained in the wider owner archive. The complete earlier release archive, sources, manifest and current-at-the-time r2 source-snapshot checks are preserved under `pre-focus-correction/`. Earlier pre-HUD evidence remains there and under `pre-hud-correction/`. Those snapshots do not establish the final focus-fixed runtime. The render owner declared the final sources frozen. The r3 ultimate archive now passes source validation and a fresh ffprobe decode against `package.source_state()`: 120 frames, 240 physics ticks and 293 source pins. All 16 canonical setup reports pass, including the current 113-case pause/focus integration gate. See `current-source-snapshot-check.json` and its input ledger. The final traversal r2 archive is now frozen. Both capture validators passed again with fresh decoding against the actual r3 `native-export-manifest.json`: traversal 180 frames/360 physics ticks/292 source pins; ultimate 120 frames/240 ticks/293 source pins. All 16 canonical MYTHIC reports match that actual export and the current checkout. See `actual-final-export-capture-verification.json`, also written to `../export-capture-verification.json`. The actual export contains 290 source records with signature `5ea4f17fd1ca27d23ef9e107a83a8efbffd83cea54ef807e3c88186e82c1f427`. The previous pre-focus top-level export receipt is preserved under `pre-focus-correction/previous-export-capture-verification.json`. These checks do not replace root’s OS/input review or immutable commit/package and downloaded-artifact checks.

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

1. Complete: final archives are frozen; both movies were freshly decoded; their sources and all 16 reports match the actual local r3 export. Earlier source identities and failed runs remain preserved.
2. Root completes the top evidence manifest and immutable commit/package identity checks. If final build inputs change, repeat source-bound validation.
3. Stage the new `yuga-traversal-armies-2026-10-17-mythic` tag using the existing strict release workflow or `release-native.py stage`, then `verify`. Root owns authorized branch/tag publication and downloaded-release verification.
