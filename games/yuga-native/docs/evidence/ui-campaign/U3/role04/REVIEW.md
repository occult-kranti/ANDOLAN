# U3-04 — Live lane goals, relay supply and terminal outcomes

Native YUGA; campaign base `0437ea91edf6989ff78c1eeadb3661f4825b60f2`. Implemented before the separate U3-05 guide/controls assignment. Final source identity and the repository commit at freeze are in `source-hashes.json`.

Changed only the assigned UI construction/layout/practice/relay methods and their declarations in `scripts/confluence_world.gd`; added the read-only `scripts/world_outcome_summary.gd` and focused `tests/ui_world_objective_cases.gd`. Return/loading functions remained with UI03; pause navigation remains with U3-01. Root's existing Atlas extraction, Sun/Moon labels and hero heading were reviewed and retained without editing `world_atlas.gd`.

Actually inspected the historical `docs/evidence/rama-hero/window/1280x720-r1/09-confluence-hud-live.png`. It shows numerical core values without a persistent lane goal, no overview shortcut beside the map, and traversal guidance in the only goal surface. It is baseline evidence, not a current-source rendering.

The upper-left status now explicitly identifies core health, the nearest route from the actual manifest, that lane's live troop count, wave and the goal of escorting Sun troops to the Moon core. The map legend exposes the current F1 overview action. The existing fixed orientation and distinct army/relay symbols remain intact; towers retain their existing marker-only semantics.

Relay progress, distance and supply guidance use the existing rule constants. A held nearby relay displays the remaining time from its real supply clock; contested, pressured, airborne, drill and terminal conditions replace that countdown with the corresponding instruction. UI formatting does not advance or modify any rule, clock, core, actor or supply receipt. Text ownership labels remain explicit alongside color, and label color now uses one shared-theme override instead of multiplying two colors.

An actual army winner reveals a prominent terminal summary in the pause menu with final core values and the existing restart route. The lane goal changes to the same outcome. This component owns no input, winner calculation, pause transition or restart authority. The existing army outcome signal still owns automatic pause. Restart hides the terminal summary; siege mode describes the actual drill and inactive relays.

The compact left column keeps the neutral hero torso clear. Title/control/traversal resize signals settle layout after native text shaping; traversal stays above the existing combat HUD, and the atlas uses its measured legend height. Bounds are derived from actual native controls rather than assuming a particular font line height.

## Executed verification

All final commands are recorded in `execution.json`, using Godot 4.6.3 headless on CPU 0 with one worker thread and separate XDG data directories. No asset import, 3D renderer or OS input was run by this role.

| Suite | Passed | Scope |
|---|---:|---|
| ui_world_objective_cases | 21 | Real nearest routes/populations/core values, read-only clocks, overview/orientation, actual relay-rule capture and contest, all three actual terminal outcomes, reset/drill, 960×540/960×600/1280×720 containment and non-overlap |
| rama_hud_layout_cases | 9 | Existing peer separation, neutral hero torso clearance and complete live ability text at 960×600/1280×720/1920×1080 |
| siege_ui_cases | 25 | Existing pause focus/scrolling, actual drill entry, rejected entry, role counts, mute/pause and reset integration |

**55/55 checks pass**, all final processes exit 0, and final logs contain no engine errors or warnings. Relay actors are staged through the existing fixed-step rules. Terminal tests stage core-health boundaries and let the normal army tick compute Sun, Moon and draw outcomes; the presentation does not invent outcomes.

Early results are retained under `*-rejected-r1`, `*-rejected-r2` and `*-pre-font-r3`. They exposed startup minimum-size settling, compact torso obstruction and the root-owned Noto Symbols fallback's excessive line metrics. Root corrected the shared fallback to bundled DejaVu Sans; final tests use theme `562a6658f7a64acb11ba183904ef8e62814d913825f98f678e4a9c3eef2b883c`. Earlier evidence retains its own source pins rather than being relabeled as current.

Current screenshots, actual OS keyboard paths, 2× UI scaling, physical GPU and Windows behavior remain unverified by this role. UI03 owns capture after the complete U3 source freeze. U3-01 may subsequently change shared-file pause functions, so the full-file hash here identifies this role's completed checkpoint, not every later U3 edit.
