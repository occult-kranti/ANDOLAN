# U1-04 · Combat HUD and map information

Native YUGA, source base `0437ea91edf6989ff78c1eeadb3661f4825b60f2`. Bounded result: one confirmed readability defect repaired in `scripts/rama_hero_hud.gd`; current headless regression checks pass. Post-change rendered review remains with role06. This report does not complete U3, online integration, a release, or the rendered screen gate.

## Actual originals inspected

Opened with `view_image`, without resizing, editing, or substituting mockups:

- `docs/evidence/visual-rounds/round2/role06/candidate/courtyard/courtyard-gameplay-day.png`
- `docs/evidence/visual-rounds/round2/role06/candidate/courtyard/courtyard-gameplay-night.png`
- `docs/evidence/rama-hero/window/1280x720-r1/09-confluence-hud-live.png`

Hashes are in `source-hashes.json`. The first two show the actual R2 candidate courtyard; the third is explicitly historical world evidence, supplemented by current source inspection. None is an after-change capture.

## Findings and current correction

1. **Confirmed readability defect, repaired:** the notice above the health bar and the numeric health value were cream text directly over bright paving in both courtyard captures. The world frame shows the same weak separation. Ability names below already have dark backing, so the more urgent health/defeat information had weaker protection from the scene. A shared `UI.panel_style(true, UI.SPACE_SM)` surface now groups the existing notice and health row. It has no extra vertical padding, retains the 600 × 103 HUD bounds, and uses the shared deep/cream palette. Long notices show an ellipsis instead of disappearing at an unexplained hard clip. Computed text/surface contrast is 16.05:1; rendered contrast still requires the role06 capture.
2. **Information priority, deferred to U3:** the historical world frame spreads useful but competing information among title/score, relay status, minimap, traversal instructions and combat HUD. Current `_update_practice_hud()` combines traversal guidance, lane objective and winner text in `goal_label`. A tether candidate or an optional landing hint can therefore dominate the same region used for the lane objective. The winner branch intentionally takes priority and must remain authoritative.
3. **Duplication and controls:** the five bottom cards are readouts, not clickable cast buttons; keyboard/mouse action labels remain sourced from `InputBindings.label()`. Health has both a bar and number, and relay ownership has both text and map markers: these are useful redundant cues. There is no reason to delete them as duplication. F2/F3/Escape hints explain help and pause. The live world control card does not expose F1 overview, despite `set_overview()` being available; discoverability needs a later source-owned fix. No inert clickable controls were added.
4. **Whole-map context:** the atlas already draws manifest lanes, collision boxes, camps, objectives, anchors, actual army units and actual relay ownership/contest. Its legend explains several shapes but lacks explicit core labels and lane names. `Atlas.project()` maps world −Z to the top; the top core is Sun. The 3D F1 overview changes camera and suspends simulation, but provides no dedicated overview instruction or explicit paused-state caption. These are source-backed next-round opportunities, not claims that a full tactical map exists.

The correction changes no runtime/vitals/kit/army authority code. `_refresh_vitals()` remains per rendered frame; slot formatting retains the existing 80 ms throttle. Public `note`, `life`, `life_text`, `slots`, and `slot_cards` contracts and existing ability strings remain available.

## Executed checks

Commands, isolated settings directories, exit codes and log paths are in `execution.json`. Godot 4.6.3 headless, actual existing imported assets; no import or heavy render performed.

| Suite | Passed assertions | Coverage |
| --- | ---: | --- |
| `rama_hud_expiry_cases.gd` | 9 | Real Guardian expiry, next-frame shield/status retirement, damage, defeat and reset |
| `rama_hud_layout_cases.gd` | 9 | 960×600, 1280×720, 1920×1080; surface separation, neutral torso clearance, five ability labels |
| `rama_hero_integration_cases.gd` | 138 | Existing real-world hero, combat and lifecycle integration |
| `ui_hud_information_cases.gd` | 8 | Opaque text backing and contrast; long, unbroken and empty notices; three viewport sizes; 180 refreshes without node growth or clock advancement; real low/zero/max life |

All four processes exited 0; **164/164 assertions passed**, with no engine error/warning lines. Reports pin their actual source hashes. Long status strings are synthetic presentation stress inputs; low health/defeat/reset use the real runtime receiver. Tests make no OS-input, screenshot, translated-text, arbitrary-size, or platform-font claim.

## U3 source-owned plan

When ownership is assigned for `scripts/confluence_world.gd` (and only then):

1. Keep a persistent real lane goal and core outcome separate from temporary traversal instructions, with winner/defeat/contested state taking priority. Read `army.report().winner`, `.cores`, `.gold`, `.waves`, and existing relay reports; do not invent match clocks, network participants, or availability.
2. Label the two actual cores and the three manifest lanes on an expanded atlas/overview surface, retaining the current spatial transform and shape legend. Add a discoverable F1 action and an explicit overview-paused/return instruction. Test north/south core identity against manifest coordinates, hero movement projection, resize containment and resume behavior.
3. Keep relay status linked to `relays.sites()` and existing pressure/contest/height/range logic. Distinguish owned-but-pressured from held-and-supplying using the current text branches. Test siege drill and ended-round states so no inactive supplies appear available.
4. Show the army's existing final winner/draw and real core values in a clear result region; use the already implemented restart/return actions owned by the round's navigation owner. Verify winner priority and paused authority, then capture gameplay, overview, contested relay, siege drill, defeat and ended-round states.

Next owners: role06 for actual current training/world screenshots and independent visual acceptance; U3-04 for world/map/goal work after U2. Existing whole-world layout below the supported 960-pixel width and arbitrary long remapped action names remain later edge-case scope.
