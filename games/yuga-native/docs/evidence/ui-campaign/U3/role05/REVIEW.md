# U3-05 — Guide, grouped controls and real effect preferences

Native YUGA. This assignment began after U3-04 completed its 55-check checkpoint. Campaign base is `0437ea91edf6989ff78c1eeadb3661f4825b60f2`; `source-hashes.json` records the exact final files and repository commit at freeze.

Owned `rama_hero_panel.gd` and `controls_overlay.gd`, adding focused guide/capability and HUD-detachment tests. Root explicitly authorized two caller lines that connect each scene's guide to its actual `rama_effects` node, plus the detached-tree guard in `rama_hero_hud.gd`. No gameplay authority or shared theme was changed. U3-01 owns pause navigation and U3-02 owns the independent map-heading correction.

Actually viewed the historical `docs/evidence/rama-hero/window/1280x720-r1/04-training-ability-guide.png`. Its five choices, description and timing established the baseline. The new guide labels the bow separately from four abilities, uses the shared semantic selected/focus states, and scrolls the ability list as needed. Recovery and active duration now come from the existing ability JSON alongside cooldown, preparation and range. Saved key labels update in both list and detail.

Page Up/Down, Home and End reach long detail content while retaining the selected ability. Disabled capabilities are excluded from the keyboard loop. Effective ancestor visibility and explicit disabled-owner checks prevent the ALWAYS guide from handling Escape or stealing recovery focus behind the loader. Caller pause behavior remains authoritative. Independent verification reproduced these missing paths before the correction and retains its rejected source/report under U3/role06/rejected-r1.

Two preferences connect to the actual Rama ability-effects implementation: fewer decorative layers and still ornamental motion. Their explanatory text explicitly limits scope to Rama's ability effects and preserves warnings/timing. They are disabled when no effect receiver exists. Changes merge transactionally into the separate `rama_effects` settings section, preserving sound/display/key preferences; a write failure restores the visible toggle to the active value and explains that current effects are unchanged. Both live scenes apply saved values when constructing the guide. No global camera-motion or graphics capability is implied.

Controls are grouped into movement, flight/tether and bow/abilities. Every current remappable action appears exactly once using canonical names. Fixed controls and truthful routes to existing sound/display preferences share the scrolling body; Page Up/Down/Home/End reach that information even during key capture without treating those navigation keys as remaps. The existing always-visible capture/reset/Done footer and caller-owned pause/focus contract remain.

The narrow HUD lifetime repair returns unavailable before accessing a missing SceneTree when teardown removes the HUD before its still-valid runtime. It retires READY/full-life text and supports reattachment without touching simulation state.

## Executed checks

`execution.json` records exact Godot 4.6.3 headless commands on CPU 0 with one worker thread and isolated XDG directories. No asset import or 3D rendering was run by this role.

| Suite | Passed |
|---|---:|
| ui_guide_capability_cases | 18 |
| ui_hud_detach_cases | 5 |
| ui_controls_lifecycle_cases | 14 |
| ui_controls_state_cases | 19 |
| input_binding_cases | 44 |

**100/100 checks pass**, all final processes exit 0 and final logs contain no engine errors or warnings. Checks include viewport-dispatched native keys, 960×540/1280×720 guide paging and list reachability, actual effect receivers in both scenes, persistence rollback, retained unrelated settings, pause/focus isolation, every control mapping and real detached-HUD lifetime.

An initial settings-route assertion sent End before the newly created controls container finished its first sort. `guide-capabilities-rejected-r1` and `execution-rejected-r1.json` preserve this fixture-timing failure. Waiting for the native container to settle before interacting resolved it without changing production code or weakening the geometry assertion.

Independent UI06 subsequently reported **36/36 native modal/integration checks**, clean logs and stable source identity. Its actual isolated 2D guide captures are recorded separately in U3/role06. This role directly viewed four of those original images at 960×540 and 1280×720: timing/context/effect rows and the footer were reachable with actual mouse/keyboard input, and focus rings were contained. The standalone board accurately disables effect preferences because it has no receiver; actual connected behavior is covered by native scene tests. A minor initial-scroll issue hides the compact Bow section heading; that observation is explicitly carried to U4 rather than declared accepted. `actual-image-observations.json` pins the four originals viewed. No integrated 3D, 2× scale, physical-GPU or Windows acceptance is claimed.

Frozen production hashes:

- Guide: `60d1cd7d90a23309839a5a2f87647b1480fdd56b2a7d7049ea756d75c79adf10`
- Controls: `3ee995c889c6dbd658d4d3dceba649970a61f5cacf848676c7f1b23847a8ceb9`
- HUD lifetime guard: `dbd71a1eaf5b2a2601a936a5f559fe2ddc94c2c9f40c33d1e3fb099f096b6184`

Root copied the combined U3 candidate to `/tmp/yuga-ui-u3-combined-source-r1` before releasing U4 work. That source snapshot supports later verification; it is not rendered acceptance.
