# Tactical publication continuation evidence

Task **YUGA-TACTICAL-CASUAL-13**, YUGA native local Casual. Source base
`7162b5d0b666e4422b0bc73100e1fba947d3323f`, branch `work/yuga-studio`, with
preserved working changes. Root owns final source identity, imports, exports,
publication and this packet's execution records. The delivery writer owns this
README and [DELIVERY.md](../../DELIVERY.md); this packet does not alter another
worker's runtime or render outputs.

`runtime-sources-before.json` is a path/byte/SHA-256 inventory taken before the
continuation's fixes. It is **not** a final-source or package manifest. Individual
JSON receipts pin the sources they actually exercised. Later changes require
their own relevant evidence; historical receipts are retained unchanged.

| Receipt | Observed result |
| --- | --- |
| [early-checks.json](early-checks.json) | Exact argv, timing, exit and engine-error observations for rules, bot and UI suites. All three exited zero without detected engine errors. |
| [round_rules.json](round_rules.json), [round_rules.txt](round_rules.txt) | 53 passing offline-authority/adverse-state checks. |
| [bot.json](bot.json), [bot.txt](bot.txt) | 21 passing bot/rules checks against the transparent synthetic host. |
| [ui.json](ui.json), [ui.txt](ui.txt) | Earlier 36-check native UI run, retained with its own source identity. |
| [ci-integration/tactical-ui.json](ci-integration/tactical-ui.json) | Successor 37 passing native structural/settings/receipt/layout checks. No pixel or ordinary-input acceptance is inferred. |
| [ci-integration/ui_end_to_end.json](ci-integration/ui_end_to_end.json), [ui_s3_loading_readiness.json](ci-integration/ui_s3_loading_readiness.json), [ui_transition_lifecycle.json](ci-integration/ui_transition_lifecycle.json) | Three classic-screen suites passed 25, 18 and 20 checks. Together with tactical UI, the integration owner reports 100 passing checks. |
| [scene-checks.json](scene-checks.json) | Exact argv and process results for physical map and integrated world. Map had no detected engine error; world did. |
| [map.json](map.json), [map.txt](map.txt) | 335 passing physical-map/source/route checks. Geometry census is not a hardware-performance measurement. |
| [world.txt](world.txt), [world-verbose.txt](world-verbose.txt) | Accelerated fixed-FPS run: 27 assertions passed, but exit leaked AudioStreamWAV/AudioStreamPlaybackWAV instances and retained three audio resources. Exit zero is not clean-engine acceptance. |
| [world-realtime.txt](world-realtime.txt) | Successor normal-clock execution passed all 27 assertions without the audio-exit diagnostic. The accelerated harness limitation remains documented. |
| [contracts.json](contracts.json) | 83 classic native source-pin/schema checks passed. No tactical online, collision or renderer qualification follows. |
| [snapshot-tests.json](snapshot-tests.json) | 22 source-snapshot boundary checks passed; not an executable export. |
| [full_match.json](full_match.json) | Six checks passed on the current map: 24 naturally resolved simulated rounds, Moon 13–Sun 11, eight plants, one defuse, 153 eliminations, one side swap, and no reported engine warnings/errors. Tick acceleration and automated play preclude human-balance or performance acceptance. |
| [visual-r2/review.json](visual-r2/review.json) | 19 actual Forward+ native captures, no source drift. Root inspected home menu, A approach, Ward/veil and shop originals. Staged objective/results are art fixtures, not ordinary player input. |
| [preexisting-world-failure.txt](preexisting-world-failure.txt) | Preserved earlier scene-initialization failure during a concurrent helper edit, resolved by its owner. No additional root repair is claimed. |

Reproduce the focused suites from the repository root, substituting a fresh
absolute report path. The recorded `early-checks.json` and `scene-checks.json`
retain the exact original invocations:

```sh
godot --headless --path games/yuga-native \
  --script res://tests/tactical/round_rules_cases.gd -- --report=/absolute/fresh/rules.json
godot --headless --path games/yuga-native \
  --script res://tests/tactical/bot_cases.gd -- --report=/absolute/fresh/bots.json
godot --headless --path games/yuga-native \
  --script res://tests/tactical/ui_cases.gd -- --report=/absolute/fresh/ui.json
godot --headless --audio-driver Dummy --disable-render-loop --fixed-fps 60 \
  --path games/yuga-native --script res://tests/tactical/map_cases.gd \
  -- --report=/absolute/fresh/map.json
godot --headless --audio-driver Dummy --disable-render-loop --fixed-fps 60 \
  --path games/yuga-native --script res://tests/tactical/world_cases.gd \
  -- --report=/absolute/fresh/world.json
godot --headless --audio-driver Dummy --path games/yuga-native \
  --script res://tests/tactical/world_cases.gd
```

The world test currently reports its assertion summary on stdout; absence of a
`world.json` file must not be described as a saved JSON result. Review stderr and
engine warnings/errors as well as process exit.

Prior [18-shot native art capture](../visual-r1/review.json) and
[actual-scene full match](../../combat/full-match-r1.json) have separate source
identities and explicit fixture limits. The documentation worker read receipts;
root performed the successor original-image review listed above. Ordinary packaged input and archive checks are now recorded in `ordinary-input-r2/` and `package-r2/`. Source push and public-byte verification have separate receipts. This directory's name alone does not establish publication.

The source checkpoint retains original native evidence, failed-run diagnostics,
authoring sources and notices. Raw supplied reference videos and their bulk
images/audio/transcripts, capture caches and user state remain local, with source
hashes, analytical reports and reproducible extraction receipts preserved.
Local retention is not remote backup. No files were deleted by the staging audit.

Remaining dependencies: final runtime source
identity, relevant CI checks, current-source ordinary-input/package evidence and
verified public deployment. Root/release is the next owner. Art, human balance,
audio listening, Windows execution, physical hardware and online/Ranked remain
independent acceptance gates.

Additional packaging guards: 22 snapshot provenance cases and 45 native contract/package cases passed. The current verification summary records 717 scoped passing assertions. The first export generated three missing Godot metadata sidecars; the source guard rejected that export. Those metadata files are retained and a fresh independent successor snapshot is used for packaging. Runtime code and asset bytes did not change.

Verified runtime source commit: `789dd1268bbac63208d0d49ec77635dff9ce7567`. The package source set in `packaged-source.json` matches 700 of that commit's 704 runtime files; four later map/minimap/objective-hint source changes are explicitly separated in `source-commit-match.json`; three generated Godot sidecars were added after the visual/source checks without changing code or asset bytes. Package successor `package-r2` passed complete ZIP CRC/payload and PCK resource checks for Linux and Windows. The current extracted Linux ordinary-input route is recorded separately. New concurrent weapon-art changes in the live checkout are preserved outside this verified commit. The final dashboard export samples a clean copy of the committed checkpoint, never relabeling the active dirty checkout as clean.

Use [the publication handoff](../../PUBLICATION_2026-11-15.md) for the source/package distinction and actual bounded Linux input. The active development DELIVERY.md may describe a later concurrent weapon-art pass.
