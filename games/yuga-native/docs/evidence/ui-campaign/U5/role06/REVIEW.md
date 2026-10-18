# U5-06 — independent screen acceptance

Product: YUGA native. Reviewer: `ui_06_acceptance`. No runtime writes. Status: bounded U5 independent acceptance complete for r1 plus the exact r2 correction overlay. Later I1 runtime changes and the final I2 catalog remain separate. UI03 owns centralized original capture; runtime correction owners are root/courtyard and UI02/guide.

Executed identity is the immutable `/tmp/yuga-u5-source-r1/ANDOLAN/games/yuga-native`, manifest SHA-256 `720d124a51d3c31b95424889a1047360720c078cda1480405f4e705442cd5ecb`: 748 source files and 350 imported-cache files. Source review began at checkout HEAD `495fae3aad59bfcce22506cc27f9d042741cd4ab`; exact file hashes, not a later shared-workspace HEAD, identify the tested bytes.

## Screen catalog

The full frozen 22-suite catalog ran with Godot 4.6.3, CPU2 and one BLAS/OpenMP thread:

```sh
env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 taskset -c 2 \
python3 /tmp/yuga-u5-source-r1/ANDOLAN/games/yuga-native/tools/run-visual-checks.py \
  --catalog screens --max-cpus 1 --timeout 120 \
  --output /tmp/yuga-u5-independent-screen-catalog-r1
```

The original result was **21/22 suites, 443/445 checks**, with the complete rejected [summary](catalog-r1/summary.json), reports and logs retained. The launch fixture's 240/180-frame deadlines elapsed before asynchronous film loading completed in the fast headless run; teardown then produced preload/compile and leaked-object diagnostics. Existing shader source bytes were present. Root corrected only the test waits to a 30-second elapsed deadline, with an early explicit loader-error exit.

The exact external corrected test (`f77d85aaa249d1ee8b9191a21ca7db9ac4f3b3edd4c3897f72837d78c1a0d1b4`) then ran against the **same immutable runtime**:

```sh
godot --headless --single-threaded-scene --audio-driver Dummy \
  --path /tmp/yuga-u5-source-r1/ANDOLAN/games/yuga-native --fixed-fps 60 \
  --script /workspace/ANDOLAN/games/yuga-native/tests/ui_launch_integration_cases.gd \
  -- --report=/tmp/yuga-u5-independent-launch-integration-r2/report.json
```

The [rerun receipt](launch-wait-r2/receipt.json) records **26/26**, exit 0, no error/warning diagnostics and 8.49 seconds. All 748 source and 350 cache hashes matched before and after. [Reconciliation](catalog-r1/reconciled-summary.json) therefore accepts **22/22 suites and 447/447 checks**: 21 original passing suites plus this corrected fixture. This is not represented as a second full-catalog run. These catalog counts remain scoped to the original runtime, not later Help/guide changes.

The separate [runner-path rejection](runner-path-rejection/) preserves an executed preflight counterexample: placing the freeze directly below `/tmp` made the runner infer repository root `/` and reject all output directories. Using the nested ANDOLAN/games/yuga-native path resolved that fixture arrangement; it was not a product fix.

## Native receipts and pixels

The independent read-only validator [source](capture-r1/ui_independent_capture_cases.py), SHA-256 `4d575ad45abd142388fa274f7b9ef7f3d85b5b9941c68609775dc892105b8ae2`, checked the completed `/tmp/yuga-u5-integrated-window-r1`:

```sh
python3 /workspace/ANDOLAN/games/yuga-native/tests/ui_independent_capture_cases.py \
  --capture /tmp/yuga-u5-integrated-window-r1 \
  --freeze /tmp/yuga-u5-source-r1/ANDOLAN/games/yuga-native \
  --report /tmp/yuga-u5-independent-capture-validation-r1.json
```

[Validation](capture-r1/validation.json) passes **101/101 receipt checks**: all 39 planned and 15 automatic original hashes/JSON agree; expected state holds in each captured frame; 82 native-input event records identify the owned window; explicit authority stages are successful and ordered; native Quit exits 0; captured source matches the freeze; no engine errors/leaks appear. The current validator adds an explicit planned-Quit check to the variant included in the original freeze; this external read-only test change is not a runtime overlay. The validator's altered-PNG rejection is retained in [validator-selfcheck](validator-selfcheck/) using historical U4 input, not counted as U5 screen evidence.

All **54 original images were directly opened** and reviewed, recorded with exact hashes in [U5-02 original review](../role02/original-review-r1.json). Native window 960×600, framebuffer 960×540, logical canvas 1280×720. Passing receipt checks do not accept visual defects. Fresh Help entry hides its heading, guide save confirmation is below the viewport, and the held respawn fixture leaves location text stale. Each is retained and routed for targeted correction; see [U5-02 review](../role02/REVIEW.md).

The actual native navigation, focus/scroll, selection, fixed footer, disabled capture state, pause/return, reset, restart and film routes are bounded accepted observations. Defeat, relay and terminal states are explicitly staged through actual rules with simulation held; they are not a native combat playthrough. Compact world text remains a readability limit. No claim is made about physical-GPU FPS, current hero art, online play, other platforms, packaged release or completion of all campaign assignments.

## Exact targeted overlay acceptance

The completed r2 capture uses manifest `0f4871dd0b09cca7f240454f33016bbe154567f0840fc15d6e7f164c3871666f`. Its [explicit overlay](../role03/repair-overlay.json) contains three runtime files plus test/capture changes. The same independent validator ran against `/tmp/yuga-u5-integrated-window-r2` and `/tmp/yuga-u5-source-r2/ANDOLAN/games/yuga-native`; exact command is in [capture-r2](capture-r2/command.txt).

[Validation](capture-r2/validation.json) passes **53/53**, covering 15 planned plus 15 automatic originals, 43 native event records, exact frozen runtime hashes, native Quit 0 and clean engine logs. Final independent [byte verification](capture-r2/post-verification.json) matches all **750 source and 350 cache files**. All 30 r2 originals were directly opened and reviewed in [paired findings](../role02/original-review-r2.json).

Help entry/reopening and native reading scroll, visible guide saved feedback, exact staged respawn/outcome location+atlas, enemy-only siege wording and selected training after the actual film round trip are bounded accepted in those original pixels. The actual native night toggle before staging also passes direct review. Owner feedback/lifetime and objective tests are linked from U5 roles04/05; they are not added to this role's independently executed catalog count.

The accepted 22-suite **447/447** reconciliation remains scoped to original r1 runtime. r2 has targeted receipt/pixel acceptance here; a new final 23-suite catalog belongs to I2 after the separately discovered I1 overview-motion fix is frozen. No old pass is relabeled as that future run. Small compact-world text, staged-versus-native playthrough limits, and unqualified art/GPU/platform/online/package scope remain open as above.
