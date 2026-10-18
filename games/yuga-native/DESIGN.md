# YUGA native design context

Refine the existing indigo, ivory and worked-gold identity. This document records the implemented system at `1b2e6f5`; it does not replace the game’s art direction or accept pending models.

## Surface intent

| Surface | Intent | Design consequence |
| --- | --- | --- |
| Play, Rama portrait and scripted duel | Experience | The actual character and world lead. Keep the view legible; interface decoration must earn its space. |
| Practice selection, settings, loading and combat controls | Operate | Make selection, state and the next action clear. Preserve familiar native keyboard/mouse behavior. |
| Help and ability explanations | Read | Use short, source-correct explanations, current bindings and a clear return path. |

The title combines a live Rama portrait with a left-hand decision area. Preserve **Confluence / Bow training**, one gold primary launch action, and quieter **Rama’s abilities / Watch duel / Help / Settings / Quit**. Keep the selected practice distinct from keyboard focus. At enlarged text sizes, allow deliberate vertical scrolling and reveal the focused control; do not shrink text or conceal the wordmark to fit.

## Shared vocabulary

[hero_ui_theme.gd](scripts/hero_ui_theme.gd) owns reusable tokens and native control styles. Read its current values before changing a component.

| Role | Baseline |
| --- | --- |
| Deep / ink / surface | `#0c1222` / `#172039` / `#202c49` |
| Primary accent / primary text | Gold `#e2bb70` / deep indigo |
| Main / secondary text | Ivory `#f6eddc` / mist `#ccd3e1` |
| Display / body fonts | Bundled Noto Serif Regular / Noto Sans Regular |
| Symbol fallback | Bundled DejaVu Sans; system fallback disabled |
| Spacing | 4, 8, 12, 20, 32 logical units |
| Controls | 44-unit minimum target, 2-unit visible focus rule, 3-unit corners |

Use Noto Serif for identity and major headings, Noto Sans for controls and explanations. Baseline body/caption/action sizes are 17/14/18; launch wordmark/practice headings have their own compact sizes. Preserve shared font resources and [font attribution](NOTICE/Noto-fonts/). Keep panels restrained, with thin rules and small corners. Gold identifies the primary action, selection and meaningful emphasis; it should not turn every boundary into an ornament.

## Behavior and evidence

Use native Button, scroll and focus semantics. Cover hover, pressed, selected, disabled, error and keyboard-focus states without changing their ownership. [The launch shell](scripts/launch_shell.gd) emits intent; its host controls navigation. [Loading presentation](scripts/loading_presentation.gd) displays controller state; it does not invent progress, complete navigation or claim shader/first-frame readiness. Keep recovery actions stable while text wraps.

Combat text needs stable contrast over sun, shadow and effects. Preserve the opaque HUD surfaces and actual binding labels. State changes should be immediate and understandable; do not add decorative choreography or simulated loading progress.

The [accepted title pair](docs/evidence/desktop-finish/D01/W1-title-fill-day-r1/REVIEW.md) and [enlarged-text/night pair](docs/evidence/desktop-finish/D01/W1-title-fill-night-200-r1/REVIEW.md) establish the visual starting point, not proof of this new pass. Inspect actual matched originals after the bounded theme/title/loading edits, then make one combined correction if needed. Focus and text measurements complement those images. Hero hair, cloth, feet/contact and map richness remain separate open art problems; cleaner panels cannot close them.

The pinned [Impeccable application contract](docs/research/impeccable/README.md) records source/license verification and the bounded desktop review. Upstream web and mobile examples guide judgment only; Godot controls, logical units and the existing desktop input contract remain authoritative.
