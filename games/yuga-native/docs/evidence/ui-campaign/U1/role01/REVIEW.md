# U1 / role01 — native launch shell

Product: YUGA native. Starting commit: `0437ea91edf6989ff78c1eeadb3661f4825b60f2`. Goal: implement a reusable, native launch decision surface with actual offline mode descriptions and one primary action. No shared scene wiring, imports, hero assets or heavy renders were changed by this role.

## Observed baseline

Viewed the actual native image `docs/evidence/visual-campaign/capture-final-anchors-r4/01-title-day.png` with the image viewer. SHA-256: `7aeaa88811879504e7cbca7ca420fcf208eab9d8f3d1a96e86ad181911999cb2`.

The current composition preserves Rama’s full silhouette on the right. The left column has clear YUGA/Rama identity and one gold Explore action, but little explanation of the two playable modes. The Bow training and Watch duel row mixes play and observation. Utilities occupy a scattered lower row. These are composition/content findings from the existing pixels, not a claim about the new shell’s appearance.

## Implemented

- `scripts/launch_shell.gd`: full-rect native Control with left indigo portrait scrim; YUGA wordmark; selectable Confluence/Bow training; real mode descriptions; one gold launch action; secondary guide/film actions; quiet Help, Settings and Quit.
- Uses the shared theme owner’s existing API plus new `button_variant` for selected/secondary mode states. No new fonts, assets, plugins or dependencies.
- Keeps current offline modes fixed. No unavailable roster, network selector, fabricated progress or matchmaking controls.
- Host-driven ready/loading/error states preserve the chosen mode, block repeated launch, show a recoverable failure and keep utility intent in signals.
- Button geometry, explicit focus order, host opener restoration, compact window reflow and shorter-window focus-follow scrolling are covered.
- `.design/brief.md` records product direction and constraints for the remaining screen rounds.

## Executed verification

```sh
godot --headless --path games/yuga-native --script res://tests/launch_shell_cases.gd -- --report=/workspace/ANDOLAN/games/yuga-native/docs/evidence/ui-campaign/U1/role01/launch-shell-cases.json
```

Godot 4.6.3: **35 passed, 0 failed**. Native Control geometry and description wrapping verified at 960×600, 1280×720, 1366×768 and 1920×1080. 800×400 checks utility reachability by focus-follow scrolling. Tests exercise both mode intents, rejected unavailable modes, loading lockout, retry, all seven launch/utility signals, hidden-state guards, Tab cycling and focus restoration. Final source hashes are in `source-hashes.json`.

**No new pixels have been accepted.** Baseline image inspection and native headless geometry do not establish integrated appearance, human keyboard usability, screen-reader accessibility, packaged execution, hardware performance or commercial-game parity. Capture owner retains the heavy rendering lane.

## Integration contract / next owner

Root owns U2 scene wiring; no wiring edits were made here.

1. Preload `res://scripts/launch_shell.gd`, instantiate under the existing UI root, and use it as `main_panel`.
2. Connect `world_requested` → `enter_confluence`, `train_requested` → `start_training`, `guide_requested` → `_open_hero`, `film_requested` → `enter_combat_film`, `help_requested` → `_open_help`, `settings_requested` → `_open_settings(true)` and `quit_requested` → `_quit`.
3. Preserve legacy aliases if existing callers require them: `start_button = main_panel.primary_button`, `hero_button = main_panel.guide_button`, `title_wordmark = main_panel.title_wordmark`, `menu_hint = main_panel.menu_hint`. `start_button` is the selected-mode CTA, not an always-training button.
4. Replace old `Card/Scroll/Content/ExploreConfluence` lookup sites with `main_panel.primary_button` or `main_panel.focus_primary()`; paths `Card/Scroll/Content` remain for generic inspection, but old action names/placement deliberately differ.
5. Skip the launch shell in the host’s generic `_layout_interface` card/wordmark sizing. It owns its responsive card layout. Host modal focus scans can still recurse through it normally.
6. API: `set_mode("world"|"train") -> bool`, `set_launch_state("ready"|"loading"|"error", message="") -> bool`, `focus_primary()`, `snapshot()`. The host retains scene loading and dialog behavior; call error state on failure and ready state on title return. Showing the shell defaults focus only if the host has not already restored a child opener.
7. Capture both modes and keyboard focus in the actual scene at 960×600 / 1280×720 / 1366×768, then inspect the images before acceptance.
