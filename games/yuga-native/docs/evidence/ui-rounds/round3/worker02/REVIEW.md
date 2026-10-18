# U3-02 shared theme, map and outcome consistency

**17/17 focused checks pass after one narrow map correction.** The shared
Noto/DejaVu font work belongs to root; this worker did not edit theme or fonts.
Tests instantiate the real launch shell and world, measure actual engine layout
and applied colors, and preserve the army as the sole outcome authority.

The title's two modes fit at960×540,1280×720 and1920×1080, with all action text
inside its controls, targets at least44px and active text contrast at least4.5:1.
The actual four-line tactical legend fits its measured footer at each size,
with at least4.5:1 contrast. Title/relay/controls/traversal/map/combat HUD panels
remain separate. These checks use the final bundled font metrics, including
tactical glyph fallback. They do not replace rasterized visual review.

The independent counterexample was map heading: roads/objectives use unequal
x/z projection scales, but the player arrow normalized raw world x/z. A diagonal
therefore differed from its mapped direction by19.379° in compact layout and
12.039° at the larger sizes. `world_atlas.gd` now computes facing from the same
projected point difference, then normalizes it. Nonfinite/zero directions yield
no directional arrow. Marker position, camera orientation and gameplay remain
unchanged. Three previously failing projection checks now pass across cardinal
and diagonal directions. Baseline14/17 and candidate17/17 reports are retained.

An actual simultaneous core defeat, staged only at the terminal health boundary
then processed by the existing army tick, produces “Draw · both cores destroyed”
with readable shared styling. Repeated outcome/map refresh preserves the entire
army report. No UI synthesizes winner state or changes simulation clocks.

Executed Godot4.6.3 headless on CPUs0,1:

```sh
taskset -c 0,1 timeout 90s godot --headless --path games/yuga-native \
  --script res://tests/ui_theme_map_consistency_cases.gd -- \
  --report=/tmp/ui-theme-map-consistency.json
```

Changed runtime file: `scripts/world_atlas.gd` projected-heading helper only
(file ownership released by U3-04). New focused test:
`tests/ui_theme_map_consistency_cases.gd`. Exact observed shared-source pins are
in each report; unrelated font/HUD work is attributed to its owners. Source
commit0437ea91… with shared authorized edits. No import, render, route, camera,
physics or authority edit. Next owner: independent UI acceptance/capture for
actual pixels and root for integration.
