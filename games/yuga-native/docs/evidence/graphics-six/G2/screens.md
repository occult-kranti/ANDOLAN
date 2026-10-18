# G2 · Ability recognition and status

The G2 screen candidate is frozen for central capture. Five original line emblems now reinforce the bow and four abilities across the combat HUD and guide, while the key, ability name and live status remain explicit. **202/202 targeted headless checks pass with clean logs. G2 rendered appearance remains pending.**

## Evidence-led direction

All four G1 title/world day/night originals were directly opened at the 960×540 framebuffer size; [G1's source-bound review](../G1/screens/g1-original-review.json) records their hashes and receipts. The larger combat values are readable and contained, and the title focus remains clear. The ability row still looked generic and needed recognition cues. Auxiliary relay/traversal copy wraps, and the neutral hero's feet sit close above the bar, so this round preserves the accepted **820×112 HUD footprint**. The design skill's refine/tokenize guidance applies; no new cards or modal architecture were introduced.

## Changes

- `rama_ability_glyph.gd` supplies five original SVG line drawings: strung bow, piercing ray, paired directional steps, protective ward and three diverging arrows. Five cached textures serve both HUD and guide. The emblems are static, ignore pointer input and have no focus stop, processing callback or simulation access.
- `rama_hero_hud.gd` places each emblem in measured space beside the existing second-line name. The native text readout remains intact for keys, names, stock, reload and cooldown. Gold means ready; quiet blue marks cooldown/reload; muted ivory marks unavailable. State words/numbers remain the source of meaning. A real bow reload now uses the same waiting hierarchy as an ability cooldown.
- `rama_hero_panel.gd` uses the same cached emblem in each selection button and beside the selected detail heading. Existing focus, paging, Back, saved key labels and transactional effect settings remain intact.
- `hero_ui_theme.gd` gives the shared cooling surface a blue top rule. Ready and unavailable surface semantics remain shared.
- `tests/graphics_g2_glyph_cases.gd` adds 13 actual-world/guide checks for distinct bounded glyph content, cache sharing, contrast, compact/wide fit, name separation, focus exclusion, real reload/cooldown, pause availability and reduced/absent effect capabilities.

Confluence, courtyard, controls, loader, gameplay rules and asset contracts were not edited in G2. There are no new dependencies. Full source copies and hashes are in [the checkpoint receipt](screens/source-pins-and-checks.json).

## Checks

| Suite | Passing checks |
| --- | ---: |
| New G2 glyph/state checks | 13 |
| G1 readability regression | 18 |
| Guide capability and persistence | 18 |
| HUD edges, defeat and terminal state | 12 |
| Shared theme | 88 |
| HUD layout and torso clearance | 9 |
| Independent modal isolation/paging | 36 |
| Effect save/error feedback | 8 |
| **Total** | **202** |

Accepted runs used Godot 4.6.3 on CPU 3 with one-thread settings; every process exited 0 and every accepted log is free of `ERROR`, `SCRIPT ERROR` and `WARNING`. Inline glyph geometry and guide text were checked at 960×540 and 1280×720 logical sizes. The existing layout suite also covers 960×600 and 1920×1080. The source hashes in the new focused run still match the frozen candidate.

The initial parse failure from an inferred Boolean on a dynamically typed reload field is retained in [rejected evidence](screens/rejected/README.md). It was corrected with an explicit Boolean type and is excluded from passing totals. There was no test weakening or runtime authority change.

## Remaining gate

The centralized G2 capture should include the ordinary combat HUD, a real cooldown/reload and a selected guide ability. Inspect the small emblems at native size, name spacing, focused button icon/text fit and the status colors over the world. The headless raster-content check proves distinct nonempty generated images, not recognizable rendered art. Reduced options retain static symbols; motion, actual OS input and rendering remain separate evidence. No hardware GPU performance or Windows execution is claimed.
