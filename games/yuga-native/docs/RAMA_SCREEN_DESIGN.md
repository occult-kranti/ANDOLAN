# Rama screen design

Native YUGA · 17 October 2026 · baseline source `e765a23264cf3c3c38fab1ded677832a24fdd64e`.

## Intent and evidence

The title is an **Experience** surface: Rama’s actual 3D actor and the coastal courtyard lead. Pause, preferences, remapping and ability details are **Operate** surfaces. They help the player make one choice and return to play.

The inspected baseline was `docs/evidence/mythic-published/window/01-title.png`, `03-public-pause.png`, plus the supplied `../yuga/art/references/rama-hanuman-sita.png`. The old title covered the actor with a scrolling block of equal-weight actions. The reference establishes the full-body blue-and-gold archer silhouette; it is concept art, not a runtime screenshot or imported model. Root `PRODUCT.md` and `DESIGN.md` describe the separate browser ANDOLAN product, so this note scopes the native surface without overwriting that context.

The impeccable launcher was attempted once from the repository and was absent. The supplied skill’s reference resources were also unavailable. Implementation continued from the skill’s main guidance, the repository instructions, the actual screenshots and current code. The root review owns the actual rendered pass and any one consolidated visual correction.

## Screen inventory

| Surface | Presentation and behavior |
| --- | --- |
| Title | An open scene with the real Rama actor framed on the right by `RamaTitleCamera`. A dark edge wash supports the left action area. Explore Confluence is the primary action; Bow training and Watch duel are secondary. Ability information, Help, Settings and Quit remain visible at 960 × 600. |
| Training | World and aim remain open. The shared `RamaHeroHUD` shows all five abilities, their actual resources/cooldowns and runtime vitals. The upper-left readout shows training outcomes and help shortcuts. The same accepted kit runs against the courtyard target adapter. |
| Pause | Continue is the first, emphasized action. The gameplay HUD recedes while the modal is open. Runtime clocks, accepted steps and cooldowns suspend; resume respects the actual alive/dead state. |
| Rama abilities | Five selectable abilities on the left, one readable detail on the right. Names, descriptions, cooldowns, preparation and ranges come from `rama-ability-kit.json`; key labels come from saved bindings. The guide never casts. Its Back action remains visible. |
| Settings | Numeric sensitivity and sound values are visible. Local save results appear near the heading. Native sliders, checks and buttons retain keyboard focus. Remapping returns to the controls button. |
| Help | Current bindings and fixed shortcuts, with a return action at the top. Page Up/Down and Home/End scroll long help using the keyboard. |
| Controls | Existing capture, conflict, cancellation and persistence behavior remains in `controls_overlay.gd`; shared theme integration is owned by the root. |

## Shared interface contract

`hero_ui_theme.gd` owns the deep blue ink, ivory text, muted blue secondary text, gold primary/focus treatment and native control styles. Its title serif uses an explicit system-font fallback list; body text uses Godot’s native theme font. It introduces no external font downloads or texture dependencies.

```gdscript
var theme := HeroUITheme.create()
var surface := HeroUITheme.panel_style(true, 24)
HeroUITheme.button(button, true) # emphasized primary action
HeroUITheme.button(button, false, true) # quiet utility action
var label := HeroUITheme.label("Text", 17, HeroUITheme.CREAM)
```

`RamaHeroPanel` exposes `open(context, return_focus)`, `close()`, `closed`, `select_ability(id)`, `refresh_bindings()`, `set_action_map(map)`, `card`, `close_button`, `ability_buttons` and `selected_id`. Context is `courtyard` or `confluence`. Tab/Shift+Tab and Up/Down stay inside the guide; Enter/Space select an ability; Escape/F3 close it. The caller owns simulation suspension and previous-screen restoration. The panel returns focus when the previous control still exists and is visible.

Courtyard keeps the existing `Card/Scroll/Content` modal paths and the searchable `ExploreConfluence` / `WatchConfluenceDuel` button names. It adds `RamaAbilities`, `BowTraining`, `rama_panel`, `rama_kit`, `rama_effects`, `rama_runtime`, `rama_hud`, `practice_army` and `cast_rama_ability(id)`. The original actor and gameplay camera remain in use; opening training restores the player camera, and returning to title restores the portrait camera.

## Validation and limits

`tests/rama_screen_cases.gd` checks layout at 960 × 600, 1280 × 720 and 1920 × 1080, title action visibility, actor projection clear of the menu, ability details sourced from actual tuning, focus wrapping, modal returns, pause/resume and camera restoration. `tests/input_binding_cases.gd` retains the remap and settings fixtures and adds version-2 C-key conflict migration to Guardian Circle with every existing binding preserved.

The initial 960 × 600 guide test caught a wrapped-label minimum-height problem on its first opening. The bounded correction gives its footer a readable minimum width and reapplies the card’s viewport bounds after the native container layout settles.

At the initial interface handoff, all 29 layout/state/focus checks passed; the separate actual-model-presence check was blocked because the new `rama-hero.glb` was still being staged by the art owner. All 44 input/settings assertions passed, with that same missing-model engine error. Those interim reports remain diagnostic, not clean final acceptance. A later world-layout test also caught an initial oversized RelayStatus before native containers settled; the root corrected startup layout and the HUD suite now begins at the default 1280 × 720 size before checking the other sizes.

The final frozen R7 repeat after the hero import passes **135/135 assertions**: screens 30, input/settings 44, HUD layout 9, world scene 27 and siege UI 25. All five sequential Godot 4.6.3 runs exited 0 with no engine errors or warnings. [The archived reports and logs](evidence/rama-hero/ui/REVIEW.md) include exact commands, forty source hashes and the tested hero asset hash. These checks cover live ability receipts, pause/focus ownership, shared training state, visible HUD separation and projected actor clearance at the tested sizes. Actual native-window input and rendered review remain with the root reviewer. A headless projection check does not establish visual quality, motion quality or physical-GPU performance. Windows and platform-specific font rendering remain unexecuted here.
