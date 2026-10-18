# U2 / role01 — courtyard launch integration

Product: YUGA native. Starting commit: `0437ea91edf6989ff78c1eeadb3661f4825b60f2`. This role owns courtyard integration, the launch shell, its existing test, and the new integration test. No camera, hero asset, loader implementation, theme, other production scene or shared ledger was changed by this role.

## Integrated behavior

The actual courtyard mounts `LaunchShell` as `main_panel`. Confluence and Bow training select a real offline mode and the single primary action launches that selection. Abilities, Watch duel, Help, Settings and Quit connect to their existing scene callbacks; menu audio is retained. Guide context follows the selected mode. Training and pause remain in the current scene. Dialogs restore the exact opener, and returning from practice restores the selected mode and primary focus.

The primary Button retains the stable `ExploreConfluence` automation ID even when training is selected. Existing `start_button`, `hero_button`, `title_wordmark` and `menu_hint` references alias actual controls. Internal courtyard code uses the shell's `primary_button` reference instead of the old path. The shell owns title layout; generic modal layout no longer overrides it.

Confluence and film exits now use the actual threaded loader through `/root/YugaSceneTransitionLayer/SceneTransition`. The persistent CanvasLayer has layer 100 and ALWAYS processing; it is lazily created and reused across scene round trips. There is no synchronous `change_scene_to_file` exit or console-only load failure in courtyard. The loader's recovery surface retains Retry/Back; the shell remains disabled behind it. Back restores caller, world and UI processing and the exact opener. Explicit child process modes require separate isolation beyond disabling the courtyard root; both `world` and `ui` are disabled until cancellation or replacement. Duplicate launch, training and title-shortcut input cannot override a pending transition.

Final training copy says “Practice Rama’s bow and four abilities…” to distinguish the primary bow action from the four additional abilities. The final copy-only change was followed by another 35/35 launch-shell run.

## Executed checks

All commands used existing imports and `taskset -c 0,1 godot --headless --path games/yuga-native --script res://tests/<suite>.gd -- --report=<absolute JSON path>`.

| Suite | Evidence | Result |
| --- | --- | --- |
| `rama_screen_cases` | `rama-screen-final.json` | 36 passed, 0 failed |
| `world_flow_cases` | `world-flow-first.json` | 13 passed, 0 failed; three real courtyard/world round trips |
| `ui_launch_integration_cases` | `integration-r2.json` | 26 passed, 0 failed |
| `launch_shell_cases` | `launch-shell-copy-final.json` | 35 passed, 0 failed after final wording correction |
| `rama_screen_quality_cases` | `legacy-screen-quality.json` | 49 passed, 0 failed |

The five suites cover 159 assertions. The existing quality suite was independently updated by another owner to require the exact eight controls; this role did not edit it. The integration suite exercises actual imported courtyard and film nodes, real threaded resource loading, missing-resource recovery, retry into the real film, world/UI isolation, duplicate input rejection, exact Settings/Help/guide/film opener restoration, three viewport sizes and singleton reuse. The missing-resource injection changes only the loader instance's test path; no production scene or allowlist is modified.

The first new integration test failed to parse because `weakref()` needed an explicit `WeakRef` declaration under warnings-as-errors. `integration-first.log` retains that failure. The corrected test passes in `integration-r2.json` and its log. `courtyard-before.gd.txt` retains the starting owned source. Final hashes are in `source-hashes.json`; full integration reports precede only the final training-copy correction, which has its own final shell run. `git diff --check` passed.

## Remaining review / next owner

Functional native integration is verified; **U2 rendered acceptance remains pending**. No import, heavy render or screenshot capture was started by this role. The parent reviewed the separate actual U1 component board and reported focus-ring vertical-edge clipping by ScrollContainer; the theme owner is assigned the inset correction. Do not treat this role's headless checks as a visual fix or as U1/U2 pixel acceptance.

The next screen capture should show both modes, the actual title portrait, keyboard focus, loading and recovery at 960×600 / 1280×720 / 1366×768. Shared return-path owners should reuse the same persistent layer/loader convention. Initial cold startup before the title, world/film return implementation, packaged execution, OS-input review and hardware performance are outside this role's changes. The title camera and underlying Rama 3D scene remain untouched.
