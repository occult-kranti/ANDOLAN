# G1 · Screens

The screen runtime is frozen in the shared G1 capture. Critical HUD text is larger, the shared surfaces have a restrained gold/indigo/marsh hierarchy, and the existing title composition and interaction flow remain intact. **216/216 targeted headless checks pass with clean accepted logs. Four G1 originals were directly reviewed below.**

The [published title original](../../ui-campaign/I3/role03/native-r1/01-package-title-idle-a.png) already gives the selected mode and primary action a clear hierarchy. The [published world original](../../ui-campaign/I3/role03/native-r1/08-package-world-live.png) shows the concrete problem: small auxiliary/map/ability captions and competing peripheral cards at the 960×540 framebuffer. Both originals were opened directly; their hashes and observations are in [baseline-review.json](screens/baseline-review.json). The `.design/brief.md` direction and design skill informed this bounded refinement.

## Changes and ownership

- `hero_ui_theme.gd`: semantic HUD typography, marsh health and Sun/Moon colors, and one shared opaque HUD surface with a small shadow and selective gold rule. Primary action text is 18 px. Existing focus/disabled styles and public helpers remain available; each surface is privately owned.
- `rama_hero_hud.gd`: stock, cooldown, ability names and health values use 16 px text; the notice uses 14 px. The 820×112 logical-pixel HUD reserves room for long supported key labels and reload text. Ready/cooling/unavailable surfaces follow existing state, and unchanged states reuse their surface. Text still communicates readiness independently of color.
- `launch_shell.gd`: uses shared color, spacing and type tokens. The decision column, selected-mode treatment, signals, focus order and 54 px primary target retain their existing structure.
- `world_atlas.gd`: uses shared surface/team/health colors and 14 px core names. Map projection, heading and distinct marker shapes are preserved.
- `confluence_world.gd`: root adopted the semantic type tokens in `_build_ui`. This worker owns only `_card` and `_layout_world_hud`: the shared surface replaces a duplicate card style; below 1100 logical pixels, optional phase/population lines yield room to the location, core state and objective. The omitted lines return when widened.
- `tests/graphics_g1_screen_cases.gd`: 18 source-bound checks against the actual world, current kit and vitals. It includes compact/wide geometry, a supported long remap/reload fixture, a real accepted cooldown, pause availability, state-surface reuse and contrast.

No changes were needed in controls, guide, outcome, loader or boot code. No gameplay timing, damage or route authority was changed by this screen work.

## Verification

| Suite | Passing checks |
| --- | ---: |
| Shared theme | 88 |
| Launch shell | 35 |
| New G1 screen checks | 18 |
| HUD layout | 9 |
| Dense HUD edges | 12 |
| Theme and map consistency | 17 |
| Guide capabilities | 18 |
| Controls state | 19 |
| **Total** | **216** |

The six final world/modal suites ran after root's serialized material import. All eight accepted logs are free of `ERROR`, `SCRIPT ERROR` and `WARNING`. Runs used Godot 4.6.3, CPU 3 and one-thread settings, without editor imports or rendering. Geometry covers actual logical sizes 960×540, 1280×720 and 1366×768, plus long objective/relay labels, defeat/respawn and terminal states in the existing suites. The nominal 0.75-scale text calculation is explicitly not a rasterized glyph measurement.

[Source pins, commands and immutable reports](screens/source-pins-and-checks.json) identify the exact source and eight runs; [source copies](screens/source/) preserve this checkpoint before later rounds. The final new test pins the theme, launch, HUD, atlas, integrated world caller and test itself. Base commit: `f81ee18c90547b60fdcc26fb4b1a185ac9ad2b9c`.

Two concrete findings were fixed and retained in [rejected evidence](screens/rejected/README.md): larger text initially made RelayStatus overlap ControlsCard at 960×540; the long `Space` plus `RELOADING` state then exceeded the narrower HUD. Compact secondary-copy omission and the final 820 px width correct those failures. The earliest diagnostic runs also encountered the concurrently introduced gold-map import before root completed the serialized import; those logs are retained and excluded from clean acceptance.

## Original-image review and next gate

Opened `/tmp/yuga-g1-native-r1/01-title-day.png`, `02-title-night.png`, `03-world-day.png` and `04-world-night.png` at their original 960×540 framebuffer size (960×600 native window). Image hashes match the completed JSON receipts; [the review](screens/g1-original-review.json) records identity and per-image observations. Title selection and primary/Settings focus remain clear. The world objective, health and stock text are easier to read in day and night, the torso stays clear and the bottom HUD is contained. Map legend and peripheral auxiliary copy remain compact; relay/traversal helper wrapping is visible. The generic text-only ability row is a concrete G2 art-direction target; shared glyphs can reinforce recognition while retaining the key and name.

Root owns the heavy capture and its central archive. These four static software-rendered frames do not establish every state or resolution. Moving/landing clearance remains a later capture gate because the ability bar sits close beneath the neutral hero's feet. No hardware GPU performance, Windows visual, listening, screen-reader or full art-quality acceptance is claimed here. There are no new dependencies or open implementation questions for this G1 checkpoint.
