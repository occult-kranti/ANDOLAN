# U4-05 — Corrupt preferences, reset and capability lifetime

Native YUGA. Began after U4-04 completed its 51-check checkpoint. Changed only `scripts/rama_hero_panel.gd`, added `tests/ui_preferences_edge_cases.gd`, and wrote this evidence. Controls and shared settings sources were exercised without modifying their implementation. Exact final source/commit pins are in `source-hashes.json`.

The retained first run found four failures: a mixed valid/invalid effect-preference pair partially changed active options; read errors lacked the expected visible error state; successful recovery retained a stale warning color; and freeing the effect receiver left enabled controls offering an unavailable capability. The correction validates the entire preference pair before adopting it, centralizes truthful message/color updates, and disables capability controls when their receiver disappears. Failed writes still preserve active values and original settings bytes.

The compact Bow-heading correction follows the actual U3 960×540 screenshot, directly inspected in the prior role. After native container/focus scrolling settles, the guide reveals the heading only when Kodanda still owns focus. It does not override a newer selection or a different focused control. The baseline headless initial-opening case already passed, so it is not presented as reproduction of that OS-rendered defect; the final fixture adds reopening from a previously scrolled list. Independent current pixels were requested at the frozen source.

## Executed checks

All final Godot 4.6.3 headless commands use CPU 2, one worker thread and LP/BLAS/OMP thread limits of 1, following root's resource-lane update. Each suite has its own XDG data directory. Exact commands/statuses are recorded in `execution.json`; no import or renderer ran here.

| Suite | Passed |
|---|---:|
| ui_preferences_edge_cases | 10 |
| ui_guide_capability_cases | 18 |
| ui_controls_state_cases | 19 |
| input_binding_cases | 44 |

**91/91 checks pass**, all final processes exit 0 and final logs contain no engine errors or warnings. The new suite verifies transactional typed-preference rejection; unsupported data and failed-write byte preservation; explicit corrupt reset with an exact original backup; eight conflict/cancel cycles without saving or closing; default recovery; normal key reset preserving sound, fullscreen and ability-effect values; compact list focus; and disposed receiver availability. Existing suites preserve real native input, saved key labels, pause/focus ownership, ordinary remapping and save-failure behavior.

`preferences-edges-rejected-r1` and its command receipt preserve the failed run. `rejected-r1-source/` retains the exact original guide and fixture for that run. All corruption and missing-path cases use isolated test settings, with no user-save mutation. The implementation keeps the separate `rama_effects` namespace and makes no claim to global camera or graphics accessibility.

Final guide: `b4dca2a54617ab5798ee60522eb103fc50a87f82c73c214d15f8d28df981fdc3`. Controls remain `3ee995c889c6dbd658d4d3dceba649970a61f5cacf848676c7f1b23847a8ceb9`.

Sources were handed to U4-06 before further assignments. Current actual Bow-heading/active-toggle pixels, integrated 3D, 2× UI scale, OS file-system dialogs, physical GPU and Windows behavior remain outside this role's checks. UI06 owns the current bounded capture and independent acceptance; U4-01 owns courtyard settings layout, and no shared-theme changes were made here.

## Independent current pixels

UI06 completed six original native 2D 960×540 captures at the frozen guide source, including actual enabled receiver toggles and saved preferences. This role directly viewed the initial Bow/Kodanda original and focused Still ornamental motion original; compact copies and source image hashes are under `reviewed-independent-pixels/`. The Bow heading is visible, effect labels and saved state are readable, the focused ring is contained and the Back footer remains visible. UI06 independently records native mouse/Tab/Space events and actual receiver/config values in U4-06. These bounded current pixels close the compact Bow-heading observation for this size; integrated 3D and wider acceptance remain separate.
