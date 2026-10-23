# Render-resources CI regression: test-only correction

The unchanged product reproduced 21 of 23 passing assertions. The two failures were exact public-report equality and the reused-builder predicate's report-equality clause. Default builder geometry remains identical to the retained oracle: 238 mesh instances, 13 shared primitive resources, equal material/transform/topology state, independent build material/mesh pools, and the original corruption, parameter and teardown controls all pass.

The sole reviewed public-report addition is `wind_court_pilot: {enabled: false}`. The default builder does not enable the court or add collision. Two report predicates now compare against the entire retained dictionary plus that exact known schema addition. The marker must be a one-key dictionary containing a boolean false; missing values, true, numeric zero, string false, null, non-dictionaries and unknown marker keys are rejected. Every other field and unknown report key remains subject to full dictionary equality. No generic filtering, unknown-field tolerance, geometry/material budget change or product-source change was made.

Four added checks exercise a corrupt report count, altered scope, unknown report field, and enabled/missing/malformed marker variants. This focused schema version passed 27 checks.

The parent-requested opt-in pilot resource phase adds 13 checks, adapted from the independently passing 14-case probe (the common source-identity check already existed). It exercises exact 588/444 triangle, 221 instance and three-surface budgets; null whole-mesh and per-surface overrides; a shared near/mid palette with separate meshes; disjoint resources across builds; mutation and restoration; identical-value duplication and cross-build alias negative controls; builder reuse; weak-reference release; and surviving-peer stability. The legacy ban on embedded primitive materials and the 238/13 budgets remain unchanged. The final native fixture passes all 40 checks.

The retained-builder `--baseline` control was run with both the original and updated tests. It still fails the same three original sharing, reuse and retention predicates. Its report-schema check remains correct for the original builder. This proves the correction does not mask those negative controls.

No raster, performance, physics or art acceptance is claimed. Root owns the full CI rerun after this focused verification. Product-source hashes are identical between the original failing and final passing runs.
