# G1 — Environment art

Implemented a Confluence environment candidate against source `f81ee18c90547b60fdcc26fb4b1a185ac9ad2b9c`. The [published baseline original](../../ui-campaign/I3/role03/native-r1/08-package-world-live.png) was opened directly: pale near-uniform paving, similar facade values and weak skyline separation flatten the view. New pixels remain **UNRUN**; this is a source/resource handoff to the centralized capture lane, not visual acceptance.

The candidate separates cool, darker travel routes from warm arrival stone. Individual paving slabs now have bounded mineral hue/value variation and stronger, distance-filtered joints; broad roughness variation adds dry wear. The opaque swamp border uses the same paving color and roughness function, preserving the transition rather than exposing a rectangular material seam. Coast water gains broad current-color variation without displacement, refraction or extra geometry.

`world_lighting.gd` now gives the sky a clearer blue day / indigo night palette and uses explicit depth haze beginning at 42 m, ending at 235 m by day and 205 m by night. This makes atmosphere address distant facade repetition while leaving the nearby combat space clear. Exposure, key/fill energy bounds, ambient visibility floor, zero-angular sun, reviewed .2/.35 shadow offsets, shadow range and existing light budgets remain unchanged. Volumetric fog, SSR and extra lights remain off. This is a change from exponential to depth fog, not merely a new fog color.

The new `environment_surface_finish.gd` binds only explicitly named opaque architecture materials beneath the existing `CityArt` subtree, from `world_lighting.configure()` after props are built. Its original `assets/environment-finish/masonry.gdshader` retains the imported albedo/normal textures and UV transforms, uses broader mineral/plinth variation and separates honey stone, pale limestone, ceramic and indigo surfaces. The existing sparse warm-window surfaces receive a cached day/night emission parameter. It adds no meshes, collisions or lights, makes no imported/shared material mutation and refuses unsupported maps, transparency, existing overrides and lookalike names. All source paths and hashes are in [environment-source.json](environment-source.json); original-work notice is [NOTICE.md](../../../../assets/environment-finish/NOTICE.md).

Executed checks (CPU 2, headless, existing imports only):

- `tests/world_lighting_cases.gd`: **30/30**, clean log.
- `docs/evidence/graphics-six/G1/environment_cases.gd`: **17/17**, clean log. Actual imported architecture binds 28 kit surfaces through seven shared materials and one cached window material; mesh/material identity, texture/UV transport, idempotence, rejection cases and phase/resource bounds pass. The first fixture used exact equality against float32 shadow properties; that failed receipt is retained, and only the fixture comparison was corrected to `is_equal_approx`.
- `tests/production_lighting_quality_cases.gd`: reports **146/146 assertions**, but **not a clean integration pass**. Eight engine errors arise from the parallel hero candidate's pending `forged-gold-roughness.png` import and failed hero-finish binding. The complete log is retained. Actual Confluence construction nevertheless reports 84 bound architecture surfaces / seven materials / one cached window; this does not clear the missing hero import.
- `git diff --check` passed for the four modified tracked rendering files. No editor import, GPU render, asset export or runtime-contract update was run by this worker.

Logs and JSON are preserved in [environment-checks](environment-checks/). Exact commands used:

```bash
taskset -c 2 env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 godot --headless --path /workspace/ANDOLAN/games/yuga-native --script res://tests/world_lighting_cases.gd -- --report=/workspace/scratch/graphics-six/G1/environment/world-lighting.json
taskset -c 2 env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 godot --headless --path /workspace/ANDOLAN/games/yuga-native --script res://docs/evidence/graphics-six/G1/environment_cases.gd -- --report=/workspace/scratch/graphics-six/G1/environment/imported-surface-r2.json
taskset -c 2 env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 godot --headless --path /workspace/ANDOLAN/games/yuga-native --script res://tests/production_lighting_quality_cases.gd -- --report=/workspace/scratch/graphics-six/G1/environment/lighting-quality.json
```

Next owner is root/capture and independent graphics review. Freeze the coherent candidate and verify actual Forward+ shader compilation, then compare the ordinary arrival gameplay camera in day and night with populated armies. Inspect nearby hero/foe readability, facade recess versus stone separation, distant skyline haze, warm-window restraint, slab-joint shimmer during motion and wet-border continuity. The darker route must remain visually walkable; haze must not erase long-range silhouettes. No GPU performance claim follows from these resource checks.

Collision/lane geometry, hero, UI, army, scene scripts, courtyard lighting and contracts are untouched by this worker. `mythic_environment.gd` also remains unchanged. Root has reserved `production_lighting.gd` for this worker's possible G2 courtyard treatment after the actual comparison. G1 stops here; no further render, import or art iteration is queued by this worker.
