# Siege practice: integration and UX packet

SIEGE-04 owns `scripts/confluence_world.gd`, `tests/siege_ui_cases.gd`, the focused scroll-menu update in `tests/world_scene_cases.gd`, and this record. The minimap is the inline `Atlas` class in the world script; there is no separate minimap file. Army gameplay, vehicle art and siege presentation have separate owners. This is an offline practice extension, not native multiplayer or production hero combat.

## Entry, purpose and exit

Pause Confluence and choose **Siege practice · enter drill**. The army validates its six-unit centre encounter before replacing the current round. A successful start places Rama at `(7, 0.05, -15)`, looking toward the central approach, and resumes practice. The drill has mirrored cannon cart, royal chariot and spearman groups around z=±15; normal waves are suspended by the army controller.

The goal is to identify marked troop attacks and destroy enemy siege engines before their impacts. The hero has no implemented health damage in this mode. The menu states that explicitly; the HUD does not advertise damage avoidance or player invulnerability as a competitive mechanic.

**Siege practice · restart drill** restarts this encounter. **Restart lane practice**, or F5 during live practice, restores the ordinary lane round and arrival spawn. Returning to the courtyard disposes of the world. A failed drill configuration leaves the current army unchanged and keeps its failure message visible across HUD refreshes. A successful drill or regular reset clears that message.

## Presentation contract

- `lane_army.gd` remains the only owner of attack timing, collision/damage, rewards and drill state. `start_siege_drill() -> bool` is an atomic configuration/entry API; `reset()` returns to ordinary practice.
- `siege_event` carries `reset`, `windup` and `impact` receipts. Role IDs are `cannon_cart` and `royal_chariot`; world-space `origin`/`target` are finite `Vector3` values. Presentation consumes these receipts and never applies damage.
- The world creates one `SiegeEffects` child under its pausable world, configures the saved master volume, and connects the army signal before army configuration. The module owns bounded effects/audio pools. `set_suspended()` handles overview as well as pause, because overview freezes army simulation without pausing the entire SceneTree.
- Reset/drill entry clears old effects and projectiles; regular reset also resets the army. Focus loss cancels traversal and pauses. Menu/help captures keep input neutral. World disposal frees the presentation child rather than retaining a global pool.
- Changing volume updates traversal audio and siege audio together. Zero volume keeps visual telegraphs available. Suspended voices do not create damage or replay old impact events on resume.

The compact HUD labels **OFFLINE SIEGE DRILL**, shows enemy siege remaining and total cannon/chariot counts, and retains gold. The context text explains cancellation by destroying the source. The minimap keeps Sun triangles and Moon squares; an additional ring marks a siege engine. These shapes complement team colors. Existing tether and player marks remain distinct, and the legend stays inside its dark backing.

## Input and layout

The pause panel uses a scroll container bounded to the viewport, with a maximum 480 × 600 logical-pixel panel and 16-pixel outer clearance. Its action column includes Continue, Siege practice, exploration/settings actions, regular restart, volume, return and quit. Focus order is explicit, includes the slider, wraps between first/last controls, and scrolls the focused action into view. Buttons retain visible gold focus outlines against dark teal. Escape key-repeat is ignored so a held key cannot alternate pause/resume.

The panel must fit 960 × 600 and 1280 × 720. Keyboard access and actual clicks are separate checks: a headless focus/layout test does not establish OS-input acceptance. The ordinary gameplay HUD keeps short contextual hints; the complete key map stays in Help/remapping.

## Review rounds and acceptance

1. **Inspect/contract:** reviewed the existing world menu, inline Atlas, pause/overview lifecycle, audio settings and actual player movement APIs. Agreed the drill and presentation APIs with their owners; identified that prior F5 behavior only respawned the hero despite round-reset wording.
2. **Implement/integrate:** add instant drill entry, regular reset, siege counts/legend, event routing, common volume/suspension and bounded scroll/focus behavior. Test against the real delivered army/effects modules, not a stub.
3. **Independent review:** run focused configuration/lifecycle/layout cases, existing world scene/flow checks and the siege integration suite. Then inspect actual 960 × 600 and 1280 × 720 screens and exercise entry/restart/mute/pause/return through the packaged window. Record exact reports below; no visual acceptance is implied before those checks exist.

Acceptance checks: entry creates the expected six-unit drill; a rejected configuration preserves the existing round; restart/F5 restores ordinary waves; counts and team/role minimap marks match living units; windup/impact receipts reach bounded presentation; pause/overview freezes presentation and simulation consistently; mute preserves warnings; reset/return leave no stale effects; keyboard focus reaches every menu action; the panel stays within both viewports; no copy implies player-health damage.

## Verification record

The integration is implemented. A focused real-scene run passes **25 checks**, including injected Tab and Shift+Tab navigation, the six-unit drill, both team-role counts, minimap data, preserved state after a rejected drill, persistent failure copy, receipt routing, mute, pause/overview, reset and F5. The menu rectangle is 480 × 568 at `(240, 16)` in a 960 × 600 logical viewport and 480 × 600 at `(400, 60)` in a 1280 × 720 viewport. Every focused control scrolls completely inside the panel. These are headless checks, not evidence of OS mouse input or rendered aesthetics.

The existing world-scene suite was updated to require fully visible focused controls inside the scroll viewport. Minimum button heights, separation, HUD bounds, physics and input lifecycle checks remain. Its final revised run passes **27 checks**. The unchanged world-flow suite passes **13 checks**, exercising three complete courtyard → world → pause → courtyard cycles and disposal of the previous instances.

All three final runs used the delivered army and effects modules, returned exit code 0, and produced no engine warnings or errors. The source pin for `confluence_world.gd` is `840e2c2d6483d31ebe8663069c76512e9852e9ff4a74028d6cc67714b2256bcf`; the UI report also pins army `da777328…` and effects `35c950bd…`.

| Maintained test | Final report | Checks | Report SHA-256 |
| --- | --- | --- | --- |
| [`siege_ui_cases.gd`](../tests/siege_ui_cases.gd) | [UI report](evidence/siege-integration/ui.json) | 25 / 25 | `924e5e964b8c007dd1fda57a087b16e215068f44d9f16fcbcdedd2dba68c0ab4` |
| [`world_scene_cases.gd`](../tests/world_scene_cases.gd) | [World-scene report](evidence/siege-integration/world-scene.json) | 27 / 27 | `f4fe6c535620637b6c69f8574b8bb097b36047c57d3543c03dbfabacba4b7b5e` |
| [`world_flow_cases.gd`](../tests/world_flow_cases.gd) | [World-flow report](evidence/siege-integration/world-flow.json) | 13 / 13 | `c77042b548fad0e72f1ffc1ffa3e4f39601a852817e974773c42320cda9c6694` |

The reports are permanently archived with the [integration evidence manifest](evidence/siege-integration/archive-manifest.json). The separate [actual Linux window review](evidence/siege-window-r2/REVIEW.md) accepts the bounded local practice flow from the extracted package built at `9520d616c88d058cc6943ddc3017303eba68c026`. Its [input trace](evidence/siege-window-r2/input-review.json) pins the executable, PCK, thirteen screenshots and OS keyboard/mouse events.

At 960 × 600, mouse Explore entered Confluence; Escape opened pause; Tab then Return entered Siege practice; mouse selection restarted the drill after volume was saved at 0.0; F5 restored ordinary practice; F2 opened Help and Escape dismissed it. Ten Tab presses returned focus to Continue after the renderer settled, and mouse Return to courtyard restored the title. Intermediate focus captures are retained without treating them as final focus states. The log contains no engine/script errors.

The compact Help footer still says “F5 respawn”; correcting it to the actual round-reset behavior is the next copy task. Overlapping warning rings and detailed continuous vehicle art remain separate follow-ups. Dummy audio means this window test verifies saved mute state, not listening quality. Movement/fire events were delivered but their outcomes were not isolated by these screenshots. Windows execution, physical-GPU performance, native multiplayer and public-download verification remain open. Render and release status are tracked in the [siege milestone](SIEGE_MILESTONE.md#evidence-and-current-status).
