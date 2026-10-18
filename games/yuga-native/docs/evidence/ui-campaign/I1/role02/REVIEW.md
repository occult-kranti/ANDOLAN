# I1-02 — shared UI across world and hero backgrounds

Product: YUGA native. Independent reviewer: `ui_06_acceptance`. No runtime changes or new render performed by this role. Status: bounded day/night/hero-background integration review complete; compact HUD text remains a readability limit.

This is a distinct integration review of shared surface opacity, source color contrast and actual scene composition. It reuses exact U5 originals as input and does not count them as newly rendered screens or repeat the U5 catalog count as new work. Source identity is the original combined freeze manifest `720d124a51d3c31b95424889a1047360720c078cda1480405f4e705442cd5ecb`; per-file hashes are in [source-surface-analysis.json](source-surface-analysis.json).

The executable read-only [analysis script](analyze-shared-surfaces.py) was run as:

```sh
python3 games/yuga-native/docs/evidence/ui-campaign/I1/role02/analyze-shared-surfaces.py \
  --project /tmp/yuga-u5-source-r1/ANDOLAN/games/yuga-native \
  --report /workspace/ANDOLAN/games/yuga-native/docs/evidence/ui-campaign/I1/role02/source-surface-analysis.json
```

It computes 14 actual source color pairs with the sRGB relative-luminance formula, records logical-to-framebuffer sizing and distinguishes opaque surfaces from the title scrim. These are diagnostic values, not a rendered accessibility certification.

| Integrated element | Source finding | Actual original review |
| --- | --- | --- |
| Title beside Rama | Empty card uses gradient scrim; opaque controls sit on it. At the original 1280 logical-width column edge, the modeled worst-white background still gives 8.21:1 MIST text contrast. This bound is specific to the source interpolation/layout. | `01-final-title.png`: bright courtyard floor and the hero remain visible to the right; title/body text and focus remain legible on the left. No heading/control collision with Rama. |
| World cards and atlas | INK/DEEP backgrounds have alpha 1. Caption text on INK is 10.73:1; cream text is 13.87:1. Map teams also use triangle/square shapes. | `10-world-live-hud.png`: sky, bright paving, armies and hero stay behind the contained HUD. Map, live health and slots remain distinct from the environment. |
| Pause actions | Strong panel and native button states are opaque. Primary dark text/focus on gold is 10.29:1; secondary cream on normal surface is 11.90:1. | `15-world-pause-header.png`: full heading and Continue focus remain visible against the street and buildings. Paused HUD uses dashes truthfully. |
| Focus/selection/disabled state | Focus stays inside controls; selected rows have a wider gold left mark. Weakest reviewed focus pair, gold on pressed blue, is 5.31:1. Disabled text is 8.10:1 on its actual source surface. | U5 controls `06`/`07` distinguish disabled/active capture; guide `02` distinguishes selected row from focus. These input-state originals are used for integration context, not new captures. |
| Training and terminal context | Shared cards and focus semantics remain the same across those callers. | `31-training-pause.png` and `21-STAGED-sun-outcome.png` retain clear actions over their actual backgrounds; terminal state is explicitly staged, not a native playthrough. |

The original native window is 960×600 with a 960×540 framebuffer and 1280×720 logical canvas. Body 17 becomes 12.75 framebuffer pixels; caption 14 becomes 10.5. The compact world HUD's 11–12 logical pixels become 8.25–9, preserving the small-text limitation. The 44 logical control minimum and 2 logical focus ring become 33 and 1.5 framebuffer pixels in this presentation. Source contrast does not remove those sizing limits or establish readability at every scale.

The original 39-view plan has no Day/night or Moonlit activation; source starts the world at phase 0 and originals show Golden hour. Night coverage was therefore explicitly rejected as absent. UI03 has added one native `N` transition before fixture hold, waits for `night=true` and `phase=1.0`, then opens pause with Continue focus. Its [original and phase receipt review](night-original-review.json) now confirms `07-night-world-pause.png` at `night=true`, `phase=1.0`, Continue focus, zero completed stages and no simulation hold. Shared panels, text and focus remain contained over the actual blue night plaza. The same-night staged respawn original 08 also shows the hero and health/slots clearly, with its staging limitation retained. Darkness is not inferred from a dimming overlay or historical U2 image. The exact derivative manifest is `0f4871dd0b09cca7f240454f33016bbe154567f0840fc15d6e7f164c3871666f`; shared theme bytes are unchanged.

U5's retained Help-entry clipping, guide save-feedback visibility and staged respawn-location findings are tracked in [U5-02](../../U5/role02/REVIEW.md). This integration role does not erase those findings. No hero-art, physical-GPU speed, online, other-platform or package acceptance is inferred.
