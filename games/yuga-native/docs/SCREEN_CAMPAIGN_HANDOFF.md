# Native screen campaign handoff

This is the short continuation guide for the five screen rounds and three integration rounds. The [ledger](SCREEN_CAMPAIGN.json) owns completion; the [visual ledger](VISUAL_ROUNDS_2_4_EXECUTION.json) separately records the three fifteen-role art/motion rounds. Read these before assigning another batch.

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

The screen catalog contains23 suites. Separate I2 checks cover ten complete real scene cycles,64 seeded loader scenarios, theme/material ownership and action/preferences sequences. Their exact commands, source pins and rejected fixture assumptions are under `docs/evidence/ui-campaign/I2/`. Do not run the isolated transition fixture directly inside the product: use its `tools/ui-campaign/check-transition*.py` wrapper.

## Evidence and remaining work

U5 retains39 planned+15 automatic first-pass originals and15+15 correction originals. Independent final I2 screen checks pass459 assertions; scene loops43, loader stress70, shared-resource probe184 and action/preferences82 are separate scopes. These totals do not substitute for image or package acceptance.

The final I1 runtime snapshot is `9919dccbd3fd18446abf2ff435be55696e913ad8d5cb7874e7e641f9fd13f088`; subsequent export metadata and contract migration have explicit overlays. I3 owns the new portable package, actual Linux inputs/images, persistence across process restart, source hashes and publication. Read its final receipts before using a download as an accepted baseline.

Small HUD text, foot support/penetration, garment contact, abrupt cast-entry motion and broader visual richness remain open. The continuous R4 record is a seven-second baseline at source7087eb5, not evidence of the later overview patch. Native online matches, a full hero roster, ordinary human playtesting, physical-GPU profiling and Windows execution remain production gates.

Keep six worker slots plus one integrator. Give each worker exclusive files and bounded evidence. Serialize imports, exports and heavy captures; this cloud uses software Vulkan and a four-core CPU quota. Preserve original failed runs. A content-pinned source change needs a revisioned contract update before exporting; do not update an old identity in place or assume the package gate has run because CI has run.
