# Landing support catalog integration

The promoted `5023b301` motion now has two permanent visual-catalog entries: `desktop-landing-support-boundary` (30 checks) and `desktop-landing-pause` (4 checks). The existing catalog self-check passed34/34; the selected native run passed30/30 and4/4 with clean logs and exact source identity before/after. No other native suites were rerun.

Only `tools/run-visual-checks.py` and `tests/visual_catalog_cases.py` changed. The catalog pins the inherited `graphics_g2_support_cases.gd`; pause additionally pins the tracked S3/W5 baseline that its fixture explicitly selects. The boundary fixture never invokes the inherited scratch-baseline path. Actual runtime scripts, assets and import descriptors are covered by the catalog source closure; the pause receipt additionally retains the imported-resource pins it reads.

The two new entries use120 fixed process frames per second, matching their existing120 Hz physics setup and sealed invocations. This preserves the pause fixture's exact one-physics-tick resume premise. Every existing catalog entry retains its60 fixed-frame setting. No fixture assertion, tolerance, report cap, runtime source or imported resource changed in this integration task.

The actual run used standard Godot4.6.3 `7d41c59c4`, CPU4 affinity, the catalog's existing LP2 setting and OMP/BLAS/MKL1. `--single-threaded-scene` is the existing catalog option; the engine worker pool is not capped. Boundary took10.506 s and pause2.877 s. Both processes exited0 without logged errors. The complete boundary report is4,937,943 bytes and pause92,649 bytes, under the unchanged8 MiB cap.

[receipt.json](receipt.json) binds the exact source, commands, results and parent promotion receipt. [native/summary.json](native/summary.json) retains the original runner output. The larger boundary JSON is stored losslessly with deterministic gzip; [storage.json](storage.json) maps its original name and uncompressed hash. The original summary paths/hashes were not rewritten. [verify.py](verify.py) replays report/log/source binding without an engine or `/tmp` dependency.

These are focused current-integration regressions. They do not change the earlier strict **26/27** disposition, its inherited60 Hz +0.228262/+0.219039 mm unplanted-step increases, or the small airborne residual. The separate [actual motion report](../W5-landing-successor-actual-r1/REVIEW.md) owns bounded sampled-image acceptance; these headless tests add no pixels, hardware performance or human-feel claim.
