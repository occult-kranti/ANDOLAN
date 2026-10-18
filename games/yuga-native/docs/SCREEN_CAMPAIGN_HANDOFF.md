# Native screen campaign handoff

The five screen rounds and three integration rounds are complete within their recorded scope: 48 bounded assignments, including actual Linux package review. The [ledger](SCREEN_CAMPAIGN.json) owns disposition; the [visual ledger](VISUAL_ROUNDS_2_4_EXECUTION.json) separately records the three fifteen-role art/motion rounds. Use the remaining gates below when assigning follow-up work.

## Qualified package and publication

The final qualified runtime/source is `9e81a7c849837dea477ddb5a8c93f43665774573`, content contract 6. [Build provenance](evidence/ui-campaign/I3/role06/REVIEW.md) pins the Linux ZIP `56a435f9…`, Windows ZIP `16f6e210…` and common PCK `d387d34a…`. Linux was executed from the actual extracted ELF/PCK; Windows has archive validation only.

**Published preview:** [yuga-native-ui-2026-10-18](https://github.com/occult-kranti/ANDOLAN/releases/tag/yuga-native-ui-2026-10-18), at 02:10:32 UTC on 18 October 2026. [Upload run 39089069718](https://github.com/occult-kranti/ANDOLAN/actions/runs/39089069718) succeeded. All five assets were independently downloaded and hash-verified; both archives match the qualified packages and pass payload checks. The [publication receipt](evidence/ui-campaign/I3/published/REVIEW.md) links the audit. Byte identity connects the download to prior Linux execution; the download audit did not run either platform. The [previous Rama preview](https://github.com/occult-kranti/ANDOLAN/releases/tag/yuga-rama-hero-2026-10-17) remains historical.

## What changed

The title uses one shared launch component with explicit Confluence/Bow training selection, a primary action, guide, film, Help, Settings and Quit. Selection survives the film round trip. Boot and transitions use the persistent allowlisted loader with actual progress, cancellation, retry and caller restoration. Shared theme/fonts, button states and reusable modal entry logic replace duplicated styling and scrolling behavior.

Pause, Help, guide and settings now have reviewed entry focus, reachable exit actions, compact/scaled layouts and safe deferred callbacks. Guide save feedback is revealed without stealing focus. The world displays current map/relay goals, respawn and outcome information; siege counts refer to enemy engines consistently. Overview explicitly holds hero presentation along with combat, while title idle continues to animate.

## Ownership and commands

| Surface | Files |
| --- | --- |
| Boot / asynchronous transition | `scripts/boot.gd`, `scripts/scene_transition.gd` |
| Launch / title / training / modal entry | `scripts/launch_shell.gd`, `scripts/courtyard.gd` |
| Shared styles / fonts | `scripts/hero_ui_theme.gd`, `assets/fonts/` |
| World / map / result | `scripts/confluence_world.gd`, `scripts/world_atlas.gd`, `scripts/world_outcome_summary.gd` |
| Guide / preferences / keys | `scripts/rama_hero_panel.gd`, `scripts/controls_overlay.gd`, `scripts/input_bindings.gd` |
| Overview presentation hold | `scripts/player.gd`, world `set_overview()` |
| Package / source identity | `tools/package-native.py`, `assets/contracts/`, `scripts/native_contracts.gd` |

Run from the repository root, with a fresh absolute output directory:

```sh
python3 games/yuga-native/tools/run-visual-checks.py --catalog screens --engine godot --output /tmp/yuga-new-screen-check
python3 games/yuga-native/tools/check-native-contracts.py
python3 games/yuga-native/tools/check-evidence.py --git-ref HEAD
```

The screen catalog contains 23 suites. Separate I2 checks cover ten complete real scene cycles, 64 seeded loader scenarios, theme/material ownership and action/preferences sequences. Their exact commands, source pins and rejected fixture assumptions are under `docs/evidence/ui-campaign/I2/`. Do not run the isolated transition fixture directly inside the product: use its `tools/ui-campaign/check-transition*.py` wrapper.

## Evidence to reuse

U5 retains 39 planned + 15 automatic first-pass originals and 15 + 15 correction originals. The final I2 screen catalog passes 459 assertions; scene loops 43, loader stress 70, shared-resource probe 184 and action/preferences 82 are separate scopes. The subsequent content-6 correction passes its own 51 source and 259 admission checks; that is not another full screen-catalog run.

The [I3 central execution report](evidence/ui-campaign/I3/role03/REVIEW.md) links all 57 unmodified originals: main run 17 planned + 15 automatic, fresh-process relaunch 4 + 3, and explicitly staged supplement 9 + 9. All three processes exited through native Quit with code 0. [Preference review](evidence/ui-campaign/I3/role05/REVIEW.md) verifies 31 checks, including identical saved bytes across relaunch. The staged lane/relay/defeat/respawn/Sun/Moon/draw views use actual rule methods and recorded holds; they are not naturally won playthroughs.

The first process needed two recorded native capture-tool recoveries. A click made before pause layout settled hit Restart instead of the guide; a later title Settings click also missed. Exact hit analysis, original driver bytes and corrective native input remain archived. Relaunch and supplement used a stable-geometry pointer check and needed no recovery. Product runtime bytes did not change for that harness correction.

The earlier I1 runtime snapshot `9919dccb…` and its I2 stress results retain their identity. Export UID additions and the content-6 contract migration are explicit overlays in the final build receipt. Package evidence binds source `9e81a7c`; do not silently relabel prior results as a fresh full-suite run.

## Remaining gates

Small HUD text, foot support/penetration, garment contact, abrupt cast-entry motion and broader visual richness remain open. The continuous R4 record is a seven-second baseline at source `7087eb5`; the later overview hold/resume has its own actual I3 package witness. Captures used warm-cache software Vulkan/llvmpipe and Dummy audio, establishing neither hardware FPS, cold-start timing nor listening quality. Native online matches, a full hero roster, ordinary human playtesting, physical-GPU profiling, Windows execution and Deadlock-level quality remain production gates.

Keep six worker slots plus one integrator. Give each worker exclusive files and bounded evidence. Serialize imports, exports and heavy captures; this cloud uses software Vulkan and a four-core CPU quota. Preserve original failed runs. A content-pinned source change needs a revisioned contract update before exporting; do not update an old identity in place or assume the package gate has run because CI has run.
