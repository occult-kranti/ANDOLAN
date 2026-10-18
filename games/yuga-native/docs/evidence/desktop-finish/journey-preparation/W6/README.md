# Current desktop journey preparation

The existing UI campaign runner is prepared for D02/D03/D05/D08/D10 screen review. The same-plan headless preflight passed **65/65** in **19.77 seconds**, covering 23 named checkpoints and all 932 recorded source/import/helper identities unchanged, with no engine errors or warnings. The tool checks passed **10/10**. This is source, engine-dispatch and readiness evidence; actual native XTest, framebuffers, recovery pixels and Quit remain unexecuted for this source.

Base checkpoint is `4c9e0adf26dfb5f766a1e2140204ef08597bd94a`, plus the separately sealed title `794266aa…a31a858e`, world `7570abd0…01dc36bb` and effects `119353e7…43db66` source. Loader `a5d236a4…061b483` and boot `c54ecd52…19ab5f5` are unchanged. [Capture inputs](capture-inputs.json) enumerate the complete intended runtime, observer, plan and import-cache inputs; the prior b03/a02 ten-shot children remain separate. No runtime file was edited for this preparation.

The [journey plan](../../../../../tools/ui-campaign/desktop-journey-plan.json) uses native keyboard focus/actions for title, Help, settings, controls, guide, training, pause, film, world, overview, return and Quit. It changes sensitivity/volume and the Piercing Dawn key in the run's isolated preferences. It checks retained values after actual scene replacement. A fresh-process persistence acceptance remains the separate completed D05 fixture; this journey does not silently claim another process relaunch.

Three terminal outcomes use the existing `authority_stage.gd`: actual core inputs and simulation steps, observed outcome signals, recorded before/after reports and an explicit callback hold/release. Four originals are named `STAGED` (three outcome menus and one terminal HUD hint). They are arranged rule results, not victories achieved by native play. Restart uses actual F5 or the focused Restart action; no winner, clock, readiness flag, focus or UI label is assigned by the native observer.

Initial loader frames are captured only if the real phase is observed; the sidecar's actual phase owns the interpretation. Resource progress covers ResourceLoader only. Construction and first rendering are distinct, without an invented full-game percentage. Missing-scene Retry/Back/Quit coverage uses the existing separate `boot-recovery-plan.json` in the tiny boot fixture: its absent courtyard is an explicit fixture condition, not a claimed failure of the intact product.

The source audit found one missing capture-fixture dependency: `loading_presentation.gd`. [The retained original runner and audit](tool-source-findings.json) record that static counterexample. The runner now includes that helper, accepts an explicit hashed engine, removes unsupported `--max-threads`, separately copies/hashes Godot shader caches, and applies its existing pointer-settlement guard to integrated mode. [Tool checks](tool-checks.json) test explicit engine rejection/selection, stage opt-in, exact private cache copy, preference/symlink/custom-directory rejection and script closure. The observer adds only logical viewport/scale and visible compact-copy telemetry.

Reproduce the headless plan with fresh report/user directories, after coordinating CPU4:

```sh
XDG_DATA_HOME=/absolute/fresh-user/data XDG_CONFIG_HOME=/absolute/fresh-user/config \
XDG_CACHE_HOME=/absolute/fresh-user/cache OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
taskset -c 4 godot --headless --path games/yuga-native --audio-driver Dummy \
  --script res://tools/ui-campaign/preflight_journey.gd -- \
  --report=/absolute/fresh-report/report.json
```

The executed [command/log receipt](preflight-r1/execution.json), [report](preflight-r1/report.json) and [raw log](preflight-r1/godot.log) preserve the source-bound result. The final preflight assertion verifies the real focused Quit target; it intentionally does not press Quit. No editor import was run.

W1 prepared `/tmp/yuga-desktop-journey-r1/project` with the existing `freeze.py`, without starting an engine. Its `ui-source-freeze.json` SHA is `002c09a53820ddfaf3997bf906cfd82145eacf784b78f031c68c88094bc2f719`; all **959/959** declared inputs (601 source/tool/test and 358 cache/support files) matched before and after. W1 owns the staging receipt in that child's parent. The later native take still requires the lead's raster-lane grant. Run this exact child's runner with no source changes during the take:

```sh
taskset -c 0,1 python3 /tmp/yuga-desktop-journey-r1/project/tools/ui-campaign/run.py \
  --project /tmp/yuga-desktop-journey-r1/project --mode integrated --allow-authority-staging \
  --plan /tmp/yuga-desktop-journey-r1/project/tools/ui-campaign/desktop-journey-plan.json \
  --engine /workspace/tooling/godot-public-4.6.3/binaries/godot-4.6.3-public-template-debug-unmodified \
  --renderer forward_plus --render-threads 2 --width 960 --height 600 --display 188 \
  --shader-cache-seed /tmp/yuga-public463-template-baseline-cold-600-r1-logs/user/cache/mesa \
  --godot-shader-cache-seed '/tmp/yuga-public463-template-baseline-cold-600-r1-logs/user/data/godot/app_userdata/YUGA • Confluence/shader_cache' \
  --timeout 120 --output /workspace/scratch/desktop-journey-native-r1
```

The proposed unmodified public-template engine and separate 112-member Godot/101-member Mesa seeds come from the sealed G0 baseline600 control. [The read-only warm-input receipt](warm-inputs.json) verifies all 213 current seed members against that archive and pins engine `dce0422d…cf730f`; it incorporates the owner's scope-wording correction. The capture owner must recheck those paths/hashes and reserve the lane. This is a warm-cache take, not a cold-start or hardware-performance claim. The existing 120-second per-observation bound is unchanged. A timeout is retained rather than silently retried or extended. Window size is 960×600; actual PNG dimensions must be read from the image and recorded separately (the content framebuffer may be 960×540).

For boot recovery, use the same runner with `--mode boot_recovery --renderer gl_compatibility --render-threads 1 --plan /absolute/frozen-project/tools/ui-campaign/boot-recovery-plan.json`, a distinct output/display and the installed engine. The fixture now includes the current loading presentation and bundled fonts. Do not pass warm world caches to this differently named tiny project. Review each original and loader sidecar before closing D02.

After native completion, run `tests/ui_independent_capture_cases.py --capture OUTPUT --freeze FROZEN_PROJECT --report FRESH_REPORT` and directly inspect the original images. Keep raw logs, event journals, stage receipts, config hashes, all PNG/JSON pairs and source/cache identities. Native failure/cancel frames are distinct from the ordinary successful route; no forced progress or mock readiness state has been added.

Exact checkpoint Actions [39103541592](https://github.com/occult-kranti/ANDOLAN/actions/runs/39103541592) completed **success** on `4c9e0ad`, including screen and package-export steps. [Credential-free metadata](ci-39103541592.json) and [assessment](ci-assessment.json) retain that observation. Later title/effects and this tooling preparation are not relabeled as that CI run's inputs. No remote test artifacts or exports were downloaded.
