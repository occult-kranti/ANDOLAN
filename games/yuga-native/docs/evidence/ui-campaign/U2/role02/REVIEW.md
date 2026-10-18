# U2 role 02 — focus inside clipping containers

Goal: correct the four-sided keyboard focus indicator in the native shared theme. Source commit remains `0437ea91edf6989ff78c1eeadb3661f4825b60f2`; this review concerns the explicit working-source hashes below.

## Observed defect and correction

Actually viewed `/tmp/ui-u1-component-r3/01-launch.png` and `/tmp/ui-u1-component-960-r1/01-launch.png`: the focused Enter Confluence action has horizontal gold lines above/below it, while the vertical focus sides disappear at the full-width ScrollContainer boundary. The U1 style expanded four pixels beyond the button, so the clip is consistent with the actual image.

Focus now draws a complete 2px ring four pixels **inside** each control. Gold primary actions use a dark indigo ring; dark secondary, utility and selected roles use gold. There is no shadow or external focus expansion. The change is used by both theme type variations and the `button_variant` per-control helper, including controls that change role in place.

An executed keyboard test found that Godot keeps focus when a primary Button is disabled. The disabled primary therefore uses muted gold `b4aa94` with dark text/ring; it stays distinct from active gold while retaining contrast. Disabled activation remains rejected by the native Button. Other disabled roles retain their readable muted text on indigo.

Reviewed current API usage in `launch_shell.gd`, `controls_overlay.gd`, `rama_hero_hud.gd`, and `scene_transition.gd`. Their existing shared API signatures remain valid. Within this role's owned theme file, repeated label-role inventories and active font-state lists now each have one constant; role-dependent text color is shared by theme and per-control configuration. No production consumers were edited.

## Verification

Run from `/workspace/ANDOLAN`:

```sh
godot --headless --path games/yuga-native --script res://tests/ui_theme_cases.gd -- --report=res://docs/evidence/ui-campaign/U2/role02/theme-checks.json
git diff --check -- games/yuga-native/scripts/hero_ui_theme.gd games/yuga-native/tests/ui_theme_cases.gd
```

Godot 4.6.3: **88/88 checks pass**, and whitespace check passes. Tests now cover all four minimum 2px ring sides, inside-bound geometry at 44×44/240×48/438×54, no external shadow, focus contrast against every native surface including disabled, and role reassignment. Existing native keyboard enable/disable, slider, mirrored options, toggle-state and independent-resource checks remain passing. Minimum measured focus/surface contrast is **5.312:1**; text/surface contrast is **8.011:1**.

`rejected-initial-checks.json` preserves the unsuccessful initial test run. That run incorrectly assumed native disabling releases focus and attempted a StyleBox method not exposed in GDScript. It is not accepted evidence. The final check uses public expansion margins and standard Rect2 geometry, then validates actual native focus retention and disabled input rejection.

## Source identity

- `scripts/hero_ui_theme.gd`: `4a8d1c96b15092f3f35770ef6b2df706608dcea5779db7707ea88567c3f4d756`
- `tests/ui_theme_cases.gd`: `392b680efe030f6f2f0aa274bda596773faf377bbbd2cd478f64b9c0a86523bd`

## Actual capture review

Reviewed all seven unmodified framebuffers archived here:

- `1280x720/01-primary-focus.png` and `960x600/01-primary-focus.png`: the complete dark inset ring is visible on all four sides of the full-width gold primary button, fixing the observed clipped vertical sides.
- Both `02-selected-focus.png` mouse-click frames retain the mode's gold selected edge; mouse focus metadata alone does not establish a visible keyboard focus ring.
- `960x600-keyboard/01-utility-keyboard-focus.png`, `02-selected-keyboard-focus.png`, and `03-secondary-keyboard-focus.png`: actual native Tab navigation produces complete gold inset rings on utility, selected and secondary roles. Focus metadata names the intended control in each frame.

The parent produced the first two captures. This role then used the existing isolated runner on CPU 0 with one llvmpipe thread and unique display 187:

```sh
taskset -c 0 python3 games/yuga-native/tools/ui-campaign/run.py \
  --output /tmp/yuga-ui-u2-dark-focus-960-r1 --display 187 \
  --width 960 --height 600 \
  --plan games/yuga-native/docs/evidence/ui-campaign/U2/role02/keyboard-focus-plan.json
```

The runner's current NativeInput API emits single keys, so seven actual Tab events reached the three dark roles through the native focus order. No direct focus/navigation method was invoked by the capture plan. All three receipts report complete runs and unchanged frozen sources matching the theme hash above. Each archived PNG hash matches its capture JSON. `capture-archive.json` records original directories and archive hashes; each subfolder retains run/shot JSON, source pins and engine/Xvfb logs.

`rendered-focus-pixels.json` checks eight pixels per focused control: two adjacent pixels on each of the four sides. All **40/40 sampled ring pixels** exactly match the intended dark or gold color in the five keyboard-focused originals, corroborating the image review and 2px thickness inside the actual control bounds.

The engine logs contain the existing llvmpipe V-Sync unsupported warning and no engine errors. This is native OpenGL Compatibility 2D fixture evidence at 1280×720 and **960×600**; 960×540 was not captured. Disabled-primary focus has headless input/contrast coverage but no separate rendered frame. Integrated hero/world UI, 2× UI scaling, physical GPU performance, Windows appearance and screen-reader support remain outside this bounded correction.

Only the shared theme, its focused test and this role's U2 evidence folder were changed. No commit, imports or heavy render performed.
