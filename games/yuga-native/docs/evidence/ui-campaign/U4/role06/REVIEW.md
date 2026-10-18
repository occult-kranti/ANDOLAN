# U4-06 independent lifecycle and guide acceptance

The independent detach probe rejected five deferred UI helpers: launch focus reveal, courtyard settings settle and modal reveal, world pause reveal, and world HUD settle. Scheduling or starting them, then removing their scene before the next frame, produced **six script errors**. All four focus assertions still passed, so the acceptance gate explicitly combines assertion results, stable source hashes and clean engine logs. The original report's `passed: true` alone is insufficient; `rejected-lifecycle-r1/gate.json` records the rejection.

The owning workers added lifetime guards. The identical witness then passed **4/4 with no engine errors**. A separate expanded run passed **9/9 with no engine errors**, covering queued and already-suspended helpers, queued deletion, newer focus ownership, settings Done at 2× content scale, and guide-open resize followed by return to the exact lower pause opener. Sources stayed unchanged within each run. This role changed independent tests and evidence; the owners made the production repairs.

## Native guide pixels

`guide-pixels/` contains **six original 960×540 PNGs**, all opened and inspected, with five native XTest events and six completed plan steps. The guide is the production file attached to a real idle `RamaAbilityEffects` receiver. No casts, meshes, GLBs or game scenes are present in this fixture.

1. `01-bow-initial.png`: Bow heading and the selected Kodanda focus ring are fully visible. The lower ability is intentionally reached by scrolling.
2. `02-options-enabled.png`: End reveals both enabled effect options and their explanatory scope.
3. `03-fewer-layers-saved.png`: a mouse click checks the first toggle, changes the actual receiver and saves the preference.
4. `04-motion-focus.png`: Tab moves to the motion option; its complete focus ring is visible.
5. `05-motion-saved.png`: Space checks that option, changes the receiver and saves it.
6. `06-bow-return.png`: Home returns to the ability details while both saved values remain true; the receiver still reports zero casts and zero meshes.

Each PNG has its raw observer JSON and hash. `run.json` retains native event coordinates, observed focus and expected states. The observer extension only reads the guide, receiver and ConfigFile; it dispatches no product actions. The final engine log has no errors; its sole warning is the software driver's unsupported V-Sync change. The fixture uses Compatibility/llvmpipe, CPU 3 and one rendering/BLAS/OpenMP thread.

## Retained rejected fixtures

The first two pixel attempts had reviewer fixture errors: calling the receiver's nonexistent `snapshot()` rather than `report()`, then reading `detail_scroll` rather than `details_scroll`. Their logs and exact fixture source are retained in `rejected-fixture-r1/` and `rejected-fixture-r2/`. No product source was changed for either. The corrected runner performs a bounded headless preflight before native capture.

## Reproduction and source

Run from `/workspace/ANDOLAN`:

```sh
env XDG_DATA_HOME=/tmp/yuga-u4-independent-lifecycle-r3/user OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 taskset -c 2 timeout 120s godot --headless --path games/yuga-native --fixed-fps 60 --script res://tests/ui_independent_lifecycle_cases.gd -- --report=/tmp/yuga-u4-independent-lifecycle-r3/report.json
env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 LP_NUM_THREADS=1 taskset -c 3 python3 games/yuga-native/tests/ui_independent_options_capture.py --output /tmp/yuga-u4-independent-options-960-r3 --display 179 --width 960 --height 540
```

Use fresh output/user directories for a repeat. `execution.json` records the exact original commands, source pins, counts and gates. The checkout commit at evidence sealing is `a43d5d8e71fc16363fb6163ce856ccf325dd437f`. Concurrent integration commits can move HEAD; acceptance is tied to the per-file hashes recorded at each run, not an inferred launch-time commit. Final lifecycle hashes:

| File | SHA-256 |
|---|---|
| `launch_shell.gd` | `6ee0c9a6d5abae28745d9e064ee127959fdf3b2bcc459138b5aacb9b14e09de2` |
| `courtyard.gd` | `90da271f43218165c063ef3376d249a90148829892437828197b3266c3370d92` |
| `confluence_world.gd` | `1ab344c5d5532184ccd22c014c4e7b0186853302c6c111b7952e2c3633bf10df` |
| `rama_hero_panel.gd` | `b4dca2a54617ab5798ee60522eb103fc50a87f82c73c214d15f8d28df981fdc3` |
| `rama_hero_hud.gd` | `4531ec0cb22f6aaa5ef1466f2a98b88967b077df6af1039f90450dd3ab24b760` |
| `ui_independent_lifecycle_cases.gd` | `620a716002355af3ebc0875fcd824cdad9f8f6e5825686c7fe0e32979c47593f` |

Guide captures use theme `b1d630e9087f939ba6a68a5bbfac6f126064d417393786380c324317ac5d39a6`. Baseline source copies, final relevant source copies and complete source-hash receipts remain beside each result.

## Open limits and next bounded roles

The 2× cases inspect headless Window geometry and focus; they do not establish OS DPI behavior or rasterized 2× readability. The six guide originals establish one compact production screen in an isolated host. Current integrated world/HUD/outcome pixels, full-screen native transitions and final scene composition remain with the central capture worker. Historical U2 or art-only R3 HUD screenshots cannot certify those current UI sources. No GPU FPS, online match, commercial visual parity or whole-campaign completion is claimed.

For the next six screen roles: (1) retain the repaired resize/transition lifetime guards in the final integration freeze; (2) compare the consolidated theme against final production originals; (3) complete the native cancel/reentry burst evidence; (4) review final HUD/outcome pixels at the supported scales; (5) exercise effect-preference recovery and keyboard return in that same freeze; (6) independently reject any engine-error run even when its assertion report says it passed. These are bounded acceptance gaps, not additional passes counted from this role.
