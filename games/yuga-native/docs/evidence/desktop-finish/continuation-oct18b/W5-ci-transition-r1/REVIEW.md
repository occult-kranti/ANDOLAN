# CI transition-guard regression repair

The exact unchanged local test reproduced **56/57** on accepted canonical d555. Its only failure was `never-grounded actual imported actor remains baseline-equal for18 updates`. That compared the whole falling pose with the old S3 motion source, so the accepted authored leg descent intentionally violated it. All 54 direct imported guard cases passed. This is a stale test oracle, not evidence that floor protection changed runtime authority.

Only `tests/desktop_s3_transition_guard_cases.gd` changed. A small inline subclass inherits the current canonical motion and disables only `_protect_transition_floor`. The never-grounded test runs 18 full updates through both current implementations, comparing all 164 bone transforms with the original `is_equal_approx` predicate and root, clocks, anchors, locks and support dictionaries exactly. It explicitly requires no measured support or airborne anchors. The retained historical comparison still checks all 126 non-leg transforms and authority fields.

Copied control records then receive a 1 mm lowerleg correction or a 1/60 s clock mutation; each must be rejected by the same comparator. Live motion and original records are untouched. All preexisting helper/direct-case code through `one_asset`, all 54 direct guard cases and thresholds, and their first 55 report records remain byte/value-identical. The old S3 source and failure stay preserved.

The repaired gate passed **59/59**, exit 0, with empty stderr and exact before/after source manifests. Comparing the two source manifests shows only the fixture changed; canonical runtime and catalog are exact. Each invocation used official Godot 4.6.3, headless, CPU4, a 60 s bound, no editor/import, cache copy or raster. No other suites were rerun.

This qualification is for the catalog’s default canonical `candidate_path`. The inline control extends `res://scripts/rama_motion.gd`; an optional external `--candidate-script` override is not qualified as a same-current control by this repair.

W6 independently accepted the source and raw before/after records without an engine rerun: `../W6-integration-r1/ci-transition-guard-review-r1/receipt.json`, SHA256 `8ef9e39ca30d2586d2064d4a3e5070b1ef8f00e26098bc94850c4ddaa00df5a7`. Root owns the test-only checkpoint and full CI restart. No additional visual, gameplay or performance acceptance is claimed here.
