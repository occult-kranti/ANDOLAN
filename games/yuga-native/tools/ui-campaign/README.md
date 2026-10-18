# UI campaign native verification

`run.py` owns a fresh Xvfb display and Godot process. XTest sends actual native clicks and keys; `observer.gd` only reports existing engine state, focus, mouse mode and visible controls and captures unmodified framebuffers. It does not call product navigation methods. Readiness waits use observed state instead of labels supplied by the input script. Every shot has a PNG hash, render-frame counter, window focus, GUI focus and state snapshot. Source files are hashed and checked again on completion. Failures and logs remain in the fresh output directory.

Component mode copies exact production launch/theme/transition scripts into a minimal isolated project. No scene assets are copied, so selecting a mode and launching causes the real loader's missing-file recovery path. `board.gd` connects the selected mode to its correct allowlisted destination. The board is a component fixture, with no hero portrait, training simulation, world, settings or help integrations. Its empty right side is not an approved product composition. Automatic transition PNGs record the phase observed when that framebuffer completed; they do not establish that threaded progress or scene construction occurred.

```sh
taskset -c 0 python3 games/yuga-native/tools/ui-campaign/run.py \
  --output /tmp/ui-campaign-fresh --display 176 --width 1280 --height 720
```

This uses the existing prepared runtime and Compatibility llvmpipe with one worker thread. Reserve rendering capacity before executing. Full integrated Forward+ capture must be serialized with the visual campaign.

`--mode integrated --project /absolute/frozen/project --plan /absolute/plan.json --renderer forward_plus` starts the project's configured main scene, including the lightweight boot. A plan is a JSON list of steps. Steps can contain `key`, `click_name` or `click_text`, `expect` dotted state predicates, and `capture`. `tab_to_text` sends real Tab events until the observed GUI focus reaches that text; it never calls a product focus method. `repeat` repeats an ordinary native event up to 40 times. Controls are located from actual current geometry transformed into X screen coordinates; noninteractive controls are excluded, and offscreen controls fail instead of fabricated clicking. Example: `{"key":"Escape","expect":{"paused":true},"capture":"training-pause"}`. The runner requires unique enabled click targets. Capture names must be ordinary basenames when authoring plans; plans are trusted local review instructions.

Freeze stable source before integrated capture:

```sh
python3 games/yuga-native/tools/ui-campaign/freeze.py --output /tmp/yuga-ui-frozen-NEW
taskset -c 0 python3 games/yuga-native/tools/ui-campaign/run.py \
  --mode integrated --project /tmp/yuga-ui-frozen-NEW \
  --plan /tmp/yuga-ui-frozen-NEW/tools/ui-campaign/integrated-plan.json \
  --renderer forward_plus --width 960 --height 600 --display 188 \
  --output /tmp/yuga-ui-integrated-NEW
```

The freeze copies runtime scripts, scenes, shaders, assets (including bundled fonts), notices, export settings, source tests, observer tools and the existing imported cache. It hashes both source and cache and fails if source changes during copying. It runs no import/render and does **not** assert cache freshness for modified raw assets. Coordinate any required frozen-project import with the sole heavy-render owner. The runner pins sources, notices, its plan and observer code and checks those bytes again after capture. Keep source freeze receipts with the resulting archive.

The integrated plan covers configured boot/title, Confluence, pause, keyboard-scrolled return, training, settings, controls and nested Back to title. The observer recursively locates the persistent loader under its CanvasLayer, so automatically captured loading/construction frames retain their actual phase/state instead of silently missing that owner.

Integrations must add mode-specific predicates (world readiness, model loaded, panels, live outcomes), actual keyboard scrolling, nested overlays, persistent configuration and native resize tests. A component capture does not close those gates. `tests/ui_campaign_flow_cases.gd` verifies four real engine-dispatch behaviors headlessly; it explicitly does not establish native XTest or visual behavior.

`--mode transition_fixture --plan tools/ui-campaign/transition-plan.json` creates two real tiny PackedScenes, plus a deliberately missing third allowlisted scene. Its eleven native frames cover queued duplicate activation/cancellation, paused caller restoration, cancellation after observed threaded loading, four scene replacements using one persistent loader, Retry and Back. It does not load a hero or world. The observer writes `transition-events.json` from actual loader signals; this bridge remains read-only. `burst` sends an ordered list of native events together, and an event's `immediate: true` skips the input harness delay so short loading phases can be exercised. Neither option holds a product phase. Validate this CPU 2, one-thread capture with `tests/ui_native_transition_cases.py --capture DIR --report FILE`.

The display-free CI counterpart is `python3 tools/ui-campaign/check-transition.py --engine /absolute/godot --report /absolute/report.json`. It copies the exact loader/theme, bundled fonts with existing imports, and the signal cases into a temporary tiny project. It performs no editor import and rejects source changes, timeouts, engine diagnostics and failed assertions. Its report uses a boolean `passed` field. Native input/pixel evidence remains a separate gate.

`--render-threads 1` is the default; the only other accepted value is `2`. It sets both `LP_NUM_THREADS` and the engine worker bound. OpenMP/BLAS remain one thread. Use the affinity assigned by the campaign owner (currently CPU 2 for this role's tiny 2D fixture), and reserve the heavy lane before integrated rendering. `run.json` records the actual affinity and all thread settings.

`--shader-cache-seed /absolute/cache` copies an existing Mesa cache into the run's private cache directory, verifies the copy, records each seed file hash and checks that the source seed remains unchanged. It never shares or mutates the seed directory. A seeded capture is a warm-cache visual/input run; it does not establish cold startup or hardware performance. The runner records that scope alongside the seed provenance. For a prior run that set `MESA_SHADER_CACHE_DIR`, pass its `user/cache/mesa` directory; for older runs without that override, pass the directory containing the Mesa cache directly.

The U5 plan uses `--mode integrated --allow-authority-staging --plan tools/ui-campaign/u5-integrated-plan.json`. This opt-in selects `integrated_capture.gd`, an explicit fixture driver extending the unchanged read-only responsibilities of the base observer. Its `stage` steps call `authority_stage.gd`; screenshots named `STAGED` and their receipts distinguish arranged rule inputs from native playthrough. The fixture temporarily holds the world/player/army process callbacks, records those modes, stages relay actors or core/vitals inputs through the actual rules, then explicitly restores the saved callbacks. Winners and UI labels are never assigned. Real terminal signals and before/after authority reports are retained; normal presentation callbacks update the staged atlas/location without advancing army/relay authority. `stage-history.json`, each screenshot's staging metadata and the run's stage list disclose these operations. Navigation and preferences remain actual XTest input. `tests/ui_capture_authority_cases.gd` verifies this helper against the existing world headlessly. The runner also checks expectations again against each completed captured frame.
