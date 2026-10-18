# U4-04 — Dense HUD copy, contested relays and live limits

Native YUGA. Began after the combined U3 source was frozen and U3-06 returned its independent review. This assignment completed before U4-05. Changed the owned world HUD construction/practice/relay presentation, `rama_hero_hud.gd`, added `ui_hud_edge_cases.gd`, and adapted the existing objective test to the separated lane-information label. Exact files/commit are pinned in `source-hashes.json`.

The first edge run retained five failures: long relay names expanded the card to 659px and crossed the crosshair; multiline notices grew the health/status panel beyond its 103px HUD; contested captions were missing. The initial bounded-text correction exposed the last defect clearly: the neutral/zero-progress branch overwrote a valid Contested state with Open. Final tests create simultaneous Sun/Moon contributors through the real relay rules to prove that case rather than relying on a UI-only flag.

Relay names now occupy a clipped first line with their complete state on a separate second line. A long route/population caption has its own clipped line, preserving the separate lane action. Core/gold metadata and bounded relay guidance cannot grow the card without limit. Combat notices are one visible line, preserving health and all five action slots even when the underlying runtime notice contains multiple lines. Full source strings remain available to the component; simulation notices, troop counts, health and rule clocks are not rewritten by the UI.

## Executed checks

Final Godot 4.6.3 headless commands ran with one worker thread, CPU 0 and isolated XDG directories before root's later CPU-lane reassignment. Exact commands and statuses are in `execution.json`. No import or renderer was run.

| Suite | Passed |
|---|---:|
| ui_hud_edge_cases | 12 |
| ui_world_objective_cases | 21 |
| rama_hud_layout_cases | 9 |
| rama_hud_expiry_cases | 9 |

**51/51 final checks pass**, all processes exit 0, with no engine errors or warnings. The edge suite covers long route/relay labels, three contested relays, dense multiline notices at 960×540 and 1280×720, valid maximum health/shield, zero-health defeat, paused return-clock preservation, ordinary army-tick respawn, full and zero cores, and actual draw outcome. Existing tests retain first-frame Guardian expiry, neutral torso clearance, peer bounds and regular objective/reset behavior.

`*-rejected-r1` preserves the initial failures; `*-intermediate-r2` preserves the remaining contested-state failures and the passing intermediate regressions. Long strings are explicit layout fixtures, not newly authored map names. Health/shield limits use the real vitals constants and APIs; respawn and outcomes use the ordinary army clock. No gameplay authority was altered.

Final HUD hash: `4531ec0cb22f6aaa5ef1466f2a98b88967b077df6af1039f90450dd3ab24b760`. World checkpoint: `7f041a62d888353664f2a00e60c7fd082eb95e0718fc2ff267389df419ed0502`.

The historical HUD image directly reviewed in U3 remains baseline evidence. These U4 changes have logical geometry/state verification, not current rendered acceptance. Integrated pixels, OS input, arbitrary resolutions, 2× UI scaling, physical GPU and Windows remain with independent acceptance. Root and U4-01 retain ownership of other shared-world/courtyard functions.

## Independent detached-world follow-up

U4-06's unchanged `ui_independent_lifecycle_cases.gd` reproduced errors when a HUD settle coroutine resumed after its world left the SceneTree. The original failed report/log/source copies remain at `/tmp/yuga-u4-independent-lifecycle-r1` and in role06's evidence. The authorized narrow repair makes `_layout_world_hud` require live tree membership and valid HUD nodes, and checks membership before each settle await plus the same tree after it. No pause route or gameplay method changed.

UI06 independently reran the exact witness: **4/4 checks, zero engine/script errors, source stable** at world SHA256 `1ab344c5d5532184ccd22c014c4e7b0186853302c6c111b7952e2c3633bf10df`. Its current receipt is `/tmp/yuga-u4-independent-lifecycle-r2`; copied available receipt files are in `independent-detach-followup/`. This follow-up supersedes the earlier world source pin only for the two lifetime guards; the original 51-check receipts retain their exact source identity.
