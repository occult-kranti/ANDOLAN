# G1 motion — bounded bow-entry correction

Disposition: **candidate frozen for integrated continuous capture; motion-quality acceptance pending**. The runtime change is only `scripts/rama_motion.gd`. No support/IK candidate, player movement, authoritative clocks, secondary motion, facial performance, materials, UI or contract source was changed by this worker.

The existing bow action pose already enters over 100 ms, but its shoulder aim layer immediately jumped to full weight when `request_action` set `action_blend=1`. With relaxed aiming and retained yaw/pitch, the actual imported rig showed a same-time body-joint step of 374.972–384.234 mm. The candidate starts this layer at its previous weight and uses the existing action elapsed time and existing 100-ms entry interval. It stores the current aim contribution on cancellation and fades it using the existing fade age. This adds no advancing clock or skeleton writer. Short action durations cap the entry interval at the existing windup duration.

## Exact scope and sources

- Baseline controller: `4c72fd247704896bbf8b720658efff1388d850912f7aed6a916950538aa458c1`; byte-exact copy [baseline.gd](motion/baseline.gd).
- Frozen candidate: `e64c3752b79b2a27faced459becbdc04170cd6ba487ee6bf3c404eeba31c0f34`; [candidate-r4.gd](motion/candidate-r4.gd).
- Actual imported 164-bone R7 hero: raw GLB `8b6cf0f4c5520696d1d843e5bdebb2454c1dbd4341e17171c5b6d20353384d5c`; imported SCN `af7d25ff9df29624b9557501772b9739a9fb21c399078a25fa13139a4d3af705`.
- Authored animation library: `1d997aed90f71dae3d0f9e38d02485dbf202d8425e61c77d8de7108fa63a9ae8`.
- The final differential records hashes before and after execution, including actual import destination bytes, and requires equality. [Artifact manifest](motion/artifact-manifest.json) pins final fixtures, raw reports, logs and retained failures. These CPU measurements precede any combined G1 hero/material capture changes; that later freeze must carry its own identity.

## Measured result

[Final differential](motion/differential-r4.json): **9/9 gates pass**, 27 baseline/candidate scenario pairs across 30/60/120 Hz. Nine conditions cover cold Piercing/Volley/Kodanda, early cancel, cancel/retrigger, warm retrigger, already-aimed entry, an 80-ms hitch, and ordinary forward/back/strafe/start/stop controls. The following distances are millimetres; maxima are body-joint origins, excluding the deliberately reattached bowstring, and are not skin/floor measurements.

| Hz | Condition | Same-time entry, old → new | First 100 ms maximum step, old → new | Whole 1.2 s maximum, old → new |
|---:|---|---:|---:|---:|
| 30 | cold_piercing_plus | 374.972 → 0.000 | 374.972 → 177.181 | 523.256 → 523.256 |
| 30 | cold_volley_minus | 384.234 → 0.000 | 384.234 → 192.722 | 389.434 → 389.434 |
| 30 | cold_kodanda_plus | 374.972 → 0.000 | 374.972 → 253.514 | 507.988 → 507.988 |
| 60 | cold_piercing_plus | 374.972 → 0.000 | 374.972 → 91.652 | 512.003 → 512.003 |
| 60 | cold_volley_minus | 384.234 → 0.000 | 384.234 → 98.907 | 384.234 → 232.601 |
| 60 | cold_kodanda_plus | 374.972 → 0.000 | 374.972 → 142.705 | 376.475 → 376.475 |
| 120 | cold_piercing_plus | 374.972 → 0.000 | 374.972 → 46.630 | 426.379 → 426.379 |
| 120 | cold_volley_minus | 384.234 → 0.000 | 384.234 → 50.336 | 384.234 → 124.476 |
| 120 | cold_kodanda_plus | 374.972 → 0.000 | 374.972 → 72.646 | 374.972 → 222.157 |

All foot endpoints, fixed targets and lock flags remain equal within the fixture's 10-µm numerical guard; measured maximum endpoint difference is zero. No-action pose origins are also exactly equal in the sampled controls. Action/stage/age, release and cancel counts, nock state, fade, phase and locomotion age are exactly equal per sampled frame. Duplicate release remains rejected. Repeated pose evaluation without an update holds the clock and pose; reset remains finite. These direct presentation calls do **not** independently prove actual SceneTree pause or gameplay authority; the independent acceptance worker and native capture must verify those paths.

The large later maxima remain: e.g. 30-Hz Piercing has a 523.256-mm `lowerarm01.L` step around 0.4 s in both versions; Kodanda has 507.988 mm around 0.133 s. The entry correction does not repair these authored intermediate pose changes. Warm retrigger does not add a boundary. Cancel→retrigger retains the exact baseline lower-leg shift (0.117–0.223 mm), while the measured upper-body boundary remains under 10 µm.

[Existing motion suite](motion/existing-motion-r1.json): **39/39 checks pass**, covering the existing rig/library contract, selected sole contact, bow hands/string, gait, cancellation and invalid-state/reset guards. This older suite's sampled geometry and point checks are bounded regression evidence, not full mesh-contact or rendered-motion acceptance.

## Failed attempts retained

1. [Initial parser log](motion/differential-r1.log) and [exact fixture](motion/fixture-r1-parse-failure.gd): inferred Variant type rejected for `pre_reset`; fixed with explicit `int`.
2. [Differential r2](motion/differential-r2.json), [exact fixture](motion/fixture-r2-broad-assertions.gd): 5/7 gates passed. An assertion incorrectly required the whole-sequence maximum to improve although unchanged later authored jumps dominate it; another required every body joint to stay under 10 µm on cancel/retrigger despite the baseline's lower-leg shift. Final gates retain both whole-sequence and whole-body values, require nonregression, and separately measure the targeted first-100-ms and upper-body boundaries. No contact or timing thresholds were loosened.
3. Source review found a real new repeated-cancel regression in [candidate r2](motion/candidate-r2.gd): storing current aim weight then multiplying the stale `action_blend` scaled it twice. [Unchanged adversary r1](motion/repeated-cancel-r1.json) measured 9.814 mm versus baseline 0.195 mm. The final change uses the existing reset fade age. [Adversary r2](motion/repeated-cancel-r2.json) passes **3/3**; residual 0.198 mm versus 0.195 mm is within the existing 10-µm numerical guard. Counter and fade-reset semantics stay exact.

## Rendering handoff and remaining defects

[Capture request](motion/capture-request.json) contains exact source identities, controls and action windows. Review normal-speed adjacent frames of cold cast entry, early cancel/retrigger and warm draw; verify the improvement does not look delayed, weak or disconnected from the bow hand/string. The real native route must show kit/presentation hold and resume during overview and continued inactive courtyard title idle. Observe final poses during `modification_processed` and retain callback/draw/physics identity; no second pose writer.

R4's exact 7087/R7 baseline tape remains the visual/contact reference, not the identity of this later source. Its zero-drift fixed anchors coexist with real stop/landing gaps and penetration: seven grounded side-samples below −5 mm, worst −20.174 mm; stationary both-feet-above-floor windows; and a separate player-owned roughly 42.7° cast-root turn. No new contact improvement is claimed. All rejected R4 release/projection/native-IK candidates remain rejected. Historical de61dc/R2 source-binding limits remain explicit in their original reports.

All executions used CPU2, Godot 4.6.3, one engine thread and LP/OMP/BLAS=1 with fresh XDG namespaces. Commands follow:

```sh
env LP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  XDG_DATA_HOME=/tmp/yuga-g1-motion-r4 taskset -c 2 timeout 150s \
  godot --headless --max-threads 1 --path games/yuga-native \
  --script res://tests/graphics_g1_motion_cases.gd -- \
  --report=/workspace/ANDOLAN/games/yuga-native/docs/evidence/graphics-six/G1/motion/differential-r4.json
```

The repeated-cancel and existing-suite runs use the corresponding test filenames, `repeated-cancel-r2.json` / `existing-motion-r1.json`, and XDG directories `/tmp/yuga-g1-motion-repeat-r2` / `/tmp/yuga-g1-motion-regression-r1`. All three final runs exited 0 with clean engine logs. No import, render, shared ledger update or commit was performed. G1 runtime is frozen; G2 starts from independent actual capture review.
