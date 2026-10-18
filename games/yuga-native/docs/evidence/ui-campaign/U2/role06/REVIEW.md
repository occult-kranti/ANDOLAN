# U2-06 — independent integrated flow verification

Source base: `0437ea91edf6989ff78c1eeadb3661f4825b60f2`; frozen capture preparation occurred at repository HEAD `bc1a3dceaddc11f5c0745e73ad1f25f2ca77a0fb` with the exact working-source overlays below. **87 refreshed CPU assertions, 13 integrated native-input frames, and final-font native boot recovery pass.** Compact world pause has one observed clipped heading, retained as a U2 defect and handed to the U3 navigation owner. This is scoped UI/flow evidence; hero/world art quality, Windows execution and physical-GPU performance remain unaccepted here.

Read U2 roles 01/02/04/05 contracts and retained their ownership. Completed the missing Confluence/film `return_to_courtyard()` routes through the persistent scene loader. Confluence snapshots and disables all explicitly processing descendants while navigation owns the scene, preserves prior pause/gameplay state, and restores those modes on cancellation. Film pauses playback and restores its prior playing state on cancellation. Both reject duplicate return actions. Existing synchronous returns, premature unpause and destructive pre-return presentation clearing were removed from those two functions. Focus loss during return remains governed by the existing scene focus handlers.

Independent `tests/ui_end_to_end_cases.gd` starts the configured boot without preloading a scene script. Navigation primarily uses actual `Input.parse_input_event` Tab/Enter/Escape dispatch through native controls, including the scrollable world pause menu. Its private missing-path injection is explicitly confined to the test loader instance; no production allowlist or scene file is changed. Specific film lifecycle actions are called directly and labeled in the test. The test is functional input evidence, not OS-window evidence.

Final existing-import CPU result: **25 passed, 0 failed**, exit 0, with no errors/warnings. Exact command, source hashes and before/after source stability are in `final-cpu-receipt.json`. Coverage: configured boot, actual title/world entry, pause, real failed return and Back, isolated explicit modes, duplicate prevention, world disposal and singleton reuse, training, pause/settings/controls with three nested Escape actions, selected-mode title return, film entry/cancel/focus loss/return, and one final transition layer. The first exploratory report preserves a test-timing failure; fault injection was moved to the real queued-phase callback before rerunning. The separately assigned U3 lifecycle suite passes 20/20 on the same source set and documents its concrete reset/disposal repairs.

## Actual native recovery capture

Executed on CPU 0 with one llvmpipe thread, Compatibility renderer, an owned Xvfb display and actual XTest keys/clicks:

```sh
taskset -c 0 python3 games/yuga-native/tools/ui-campaign/run.py \
  --mode boot_recovery --output /tmp/yuga-u2-boot-recovery-window-r2 \
  --display 188 --width 960 --height 600 \
  --plan games/yuga-native/tools/ui-campaign/boot-recovery-plan.json \
  --renderer gl_compatibility
```

The isolated fixture copies the real boot/loader/theme plus bundled fonts and their imports; it deliberately omits the courtyard scene to exercise the actual missing-resource path. It contains no hero/world. The run completed with five manual original PNGs and three automatic queued-state PNGs, exact source/hash verification and actual Quit exit 0. Native keyboard Retry, Escape Back, clicking Retry on the boot recovery page, another Back and clicking Quit all executed. The only engine warning is the known llvmpipe inability to change V-Sync.

Actually inspected the original error/retry/recovery frames and initial queued frame. At 960×600, headings, full status copy, Retry/Back, Open YUGA/Retry and Quit fit; full inset keyboard focus rings are visible. Back restores a usable boot page, not a blank viewport. The first image review caught an incorrect “Bow training” destination label during initial startup. The loader's courtyard destination now displays “YUGA”; rejected-copy run `boot-recovery-r1` is retained and `boot-recovery-r2` shows that label correction. Its queued image shows an unnumbered preparation message; this missing-resource fixture does not establish threaded percentage or world construction behavior.

## Verification tooling and frozen capture source

The previous integrated observer bypassed configured boot by hardcoding courtyard. It now starts `application/run/main_scene`, recursively finds the persistent loader under its CanvasLayer, and reports scene path, real readiness/player state and explicit panel visibility. Native click coordinates use the viewport-to-screen transform, avoiding incorrect clicks when window pixels differ from layout coordinates. Input-ineligible controls behind an isolated caller are excluded. `tab_to_text` uses actual repeated Tab events and observed focus, rather than product focus/navigation methods. The plan and runner/observer sources are pinned alongside runtime files.

The first `tools/ui-campaign/freeze.py` snapshot copied 549 exact source files and 348 existing imported-cache files. Root’s dependency review caught omitted runtime shaders before any engine run on that copy. The incomplete `/tmp/yuga-ui-u2-integrated-source-r1` and `source-freeze.json` remain preserved. The corrected freeze tool includes shaders, export settings, the fallback world map, all top-level source tests and the shared strict test runner. `run.py` also pins the shaders, export settings and fallback map.

`source-supplement.json` records the exact additions to that frozen source plus the three corrected observer-tool files; every original gameplay/UI/asset source remained unchanged, so later U3 changes did not enter U2. `/tmp/yuga-ui-u2-integrated-source-r2` contains 716 source files and the same 348 imported-cache files, pinned by `source-freeze-r2.json`. A literal runtime-resource dependency audit found no remaining omitted files. The original source-r2 is preserved; import and execution use its separate runtime-r2 copy. A freshness audit of 174 imported assets found three stale raw-to-cache MD5s: `rama-hero.glb`, `rama-hero-mid.glb`, and `rama-hero-far.glb`; all other checked imports matched and none were missing. Before capture, root identified excessive line metrics in the Noto Symbols fallback. `font-overlay.json` pins the authorized font-only correction to bundled DejaVu Sans, its license/cache, the updated font metric test and generic fixture font-cache copying. `source-freeze-r3.json` pins the resulting 720-file U2 source; no U3 UI hierarchy changes were included.

The reserved-lane `run-refreshed-cpu.py` executed on `/tmp/yuga-ui-u2-integrated-runtime-r3`. Import exited 0 in 18 seconds, changed only six hero scene/cache-MD5 files, added 31 generated UID files and changed no existing authored source. All **175** imported raw-asset MD5s match afterward. Exact source/cache pins, freshness audits and raw logs are archived in `refreshed-cpu-r1/`. Font metrics/glyph checks pass **7/7**, launch geometry **35/35**, independent flow **25/25**, and lifecycle **20/20**: **87/87**, clean exits and unchanged source during tests. `hero-import-sync.json` pins the three raw GLBs, matching import metadata and six refreshed cache files for safe canonical cache synchronization.

## Completed original-window review

Executed the frozen `tools/ui-campaign/integrated-plan.json` with actual XTest keys/clicks, CPU 0, one llvmpipe thread, Forward+, a 960×600 native window, and the configured boot. Exact engine command, 30 native event records, source hashes and every frame state are in `integrated-r2/run.json`; `integrated-r2/index.html` displays the untouched originals and links their metadata. Project aspect/stretch produces a **960×540 framebuffer** inside that window; click coordinates include the viewport-to-screen transform.

```sh
taskset -c 0 python3 /tmp/yuga-ui-u2-integrated-runtime-r3/tools/ui-campaign/run.py \
  --mode integrated --project /tmp/yuga-ui-u2-integrated-runtime-r3 \
  --plan /tmp/yuga-ui-u2-integrated-runtime-r3/tools/ui-campaign/integrated-plan.json \
  --renderer forward_plus --width 960 --height 600 --display 188 --timeout 600 \
  --output /tmp/yuga-ui-u2-integrated-window-r2
```

The completed run has **13 manual + 9 automatic originals**, verified PNG hashes, `source_unchanged: true`, all manual snapshots window-focused, and no engine errors or warnings. The harness terminates the final title process intentionally (`cleanup_exit: -15`); this is not a game-Quit test. The separate final-font `boot-recovery-r3` run completes five manual + three automatic originals, source unchanged, and an actual Quit exit 0. Its only warning is the Compatibility/llvmpipe V-Sync limitation. Final recovery text/buttons/focus were inspected after the DejaVu correction; earlier font snapshots remain separately labeled.

Actually inspected all 13 manual integrated originals, all five final recovery originals, and representative original queue/loading/construction frames. Findings:

- Title launch and returned title fit, show selected Confluence/training modes and the actual hero/courtyard, and restore primary focus. Selecting training changes its description/action and the final title retains that selection.
- Actual world, map, relay/status cards and combat HUD fit the compact framebuffer. Auxiliary labels remain small; this is not final typography/art acceptance. Native Escape opens pause and repeated real Tab scrolls to Return; its complete focus ring is visible. **Initial world pause clips the “OFFLINE LANE PRACTICE” eyebrow at the scroll viewport top** (`03-world-pause.png`). U3-01 received that exact original and reports a later-source correction; U2 has not been relabeled as containing it.
- Training pause fits with its full header and actions. Settings uses a scroll viewport; its lower Back action is below the initial view, while native Tab reaches keyboard customization. Controls preserve the fixed footer, button focus and scrollable list. Escape restores customization focus in Settings, then Settings focus in pause. Return to title preserves training selection and primary focus.
- Boot has an actual visible queued frame before heavy work. Resource-loading frames display the real queried zero-progress sample; scene-construction frames remove the percentage and state that preparation may take a moment. These are separate phases, not a full-game percentage. `auto-loading-3.png` completed after the phase advanced to **constructing**, accurately recorded in its JSON; filenames are not phase evidence by themselves.

`integrated-r1` preserves the first attempt's 120-second cold first-draw readiness timeout, three loader originals and raw logs. The unchanged source succeeded with a 600-second per-condition allowance; total run duration was 429 seconds on this software renderer. This does not establish responsiveness on a physical GPU, real-time FPS, or asynchronous scene instantiation. The loader makes preparation visible, but construction and first render can still block. CPU tests cover film return, injected failure/cancel and lifecycle disposal; this 13-frame OS-input plan does not add rendered film, defeat/outcome, guide, OS focus-loss or repeated-cancel acceptance.

All owned 3D processes stopped and the heavy lane was explicitly returned to `r2_06_capture`. The next approved U4-03 work is isolated 2D native queued cancellation/reentry and recovery with observed phase/focus ownership. No shared ledger or commit was changed by this role.
