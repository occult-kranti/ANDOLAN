# U1-05 · Keyboard controls foundation

Product: YUGA native. Source base: `0437ea91edf6989ff78c1eeadb3661f4825b60f2`.
Scope: `scripts/controls_overlay.gd`, new `tests/ui_controls_state_cases.gd`, and this evidence directory. No settings host, binding persistence, assets, imports, or render changes.

## Native baseline inspected

- `docs/evidence/traversal-armies-window-r2/03-controls.png`: actual archived native keyboard modal, teal panel, tightly packed mapping buttons and footer. The controls surface has its own styling, separate from the current indigo theme. It is historical evidence, not a capture of the new source.
- `docs/evidence/rama-hero/window/1280x720-r2/02-settings-first-entry.png`: actual native Settings screen, clear preference labels, gold focused control, scrollable settings body. Customize controls sits above Back. No Settings host rewrite was needed for this assignment.

The archived controls labels include an earlier hero kit. Binding titles remain owned by `input_bindings.gd` and were not copied from the screenshot. Image/source SHA-256 values are in `source-hashes.json`.

## Confirmed defects and correction

`before.json` and `before.log` preserve the rejected regression run against the original controls source. Native engine dispatch demonstrated that Tab was consumed as an invalid binding during capture, and Enter on focused Cancel, Reset, or Done was also consumed. The footer existed but was inaccessible through this keyboard path. A deliberately long mapping label also forced the requested 680px card to 799px rather than wrapping.

The overlay now handles Tab/Shift Tab before key capture and permits Enter to activate another focused mapping or footer action. Esc still cancels active capture first; another Esc closes. Space remains a captured binding key. The caller still owns `closed` and focus return; the actual courtyard return-to-Settings contract passes its existing integration suite.

The duplicate panel/button Theme was removed in favor of `hero_ui_theme.gd`: shared body/title/caption styles, spacing, minimum targets, secondary mapping buttons, utility Cancel, primary Done, indigo surface, gold status and focus. Mapping descriptions wrap in their allocated row width, keeping long labels inside the existing scroll region. Save errors remain visible; failed operations preserve bindings and do not emit a successful change event.

## Executed validation

Commands run from `/workspace/ANDOLAN/games/yuga-native`, using independent XDG directories:

```sh
XDG_DATA_HOME=/tmp/yuga-ui-controls-u1-before godot --headless --path . --fixed-fps 60 --script res://tests/ui_controls_state_cases.gd -- --report=/workspace/ANDOLAN/games/yuga-native/docs/evidence/ui-campaign/U1/role05/before.json
XDG_DATA_HOME=/tmp/yuga-ui-controls-u1-after godot --headless --path . --fixed-fps 60 --script res://tests/ui_controls_state_cases.gd -- --report=/workspace/ANDOLAN/games/yuga-native/docs/evidence/ui-campaign/U1/role05/controls-state.json
XDG_DATA_HOME=/tmp/yuga-ui-controls-u1-bindings godot --headless --path . --fixed-fps 60 --script res://tests/input_binding_cases.gd -- --report=/workspace/ANDOLAN/games/yuga-native/docs/evidence/ui-campaign/U1/role05/input-bindings.json
git diff --check -- scripts/controls_overlay.gd tests/ui_controls_state_cases.gd
```

The new suite passes 19/19 checks using viewport-dispatched native key press/release events. It covers complete idle focus wrapping, capture navigation, conflict rejection, Cancel/Reset/Done activation, two-stage Esc, hidden-input exclusion, immediate persistence, failed save/reset behavior, host focus restoration, and long-label/error layout at 960×540 and 1280×720. The original input suite also passes; its report includes the real courtyard settings return, focus-loss cancellation, persistence preservation and defaults recovery checks. Diff whitespace validation passes.

The rejected run's later persistence assertions also failed because its preceding keyboard Reset/Done did not execute; those failures are not a separate claim of a persistence defect. Report source hashes distinguish the before and after runs.

## Remaining gate and next owner

U1-06 owns actual window input and serialized rendering. Inspect the current controls surface at 960×540 and 1280×720, including focused mapping/footer, captured-key status, long mapping descriptions and save-failure status. Headless layout and native dispatch establish functional state; they do not establish rendered quality or OS-window input acceptance. U2-05 and later own broader settings/help/guide integration.
