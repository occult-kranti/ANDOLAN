# R4-07 native four-segment IK experiment

**Reject the bounded unconstrained FABRIK3D and CCDIK3D candidates. No production motion change.** The actual imported R2 rig exposes the required five joints/four segments. Both native algorithms preserve those lengths but produce large foot rotation and worse sampled sole penetration. Endpoint reach alone does not solve the support/release defect.

The native API/source contract is also not a synchronous replacement for the current `_solve_leg`. Godot4.6.3 `Skeleton3D.advance()` schedules the modifier phase; the solved pose is observable inside `modification_processed`, then the skeleton restores the unmodified pose. The native virtual method cannot be invoked through `call()`. Any future integration must preserve one skeleton writer and explicitly fit this phase, rather than attaching a competing native modifier to the current controller.

## Exact executed comparison

The frozen project `/workspace/scratch/visual-round3/capture-baseline-project-r1` retains approved R2 raw near140f8ff…351a and imported SCN75f6ed79…9a28. Controller4c72fd24…458c1 and clip library1d997aed…c9ae8 are unchanged. The final run binds all raw/import/controller/library/fixture/probe hashes before and after execution. This is separate from the older role05 seal-time identity mismatch and from newly promoted R7.

The recorder uses the old scenario/acceleration fixture, executes the incumbent controller, and records selected last per-side `_solve_leg` calls after the existing allowed pelvis correction. It keeps every local prepose, target and incumbent global postpose. Selection is every0.2s plus the frame before0.8s, over1.6s at30/60/120Hz. The eight scenarios are ordinary38m/s² acceleration reversal, adversarial reversal, strafe, backpedal, stationary aim, bounded hitch, reset and action cancel. Only frames that actually invoke the leg solver produce queries:279 queries total.

Each query is replayed with exactly one active native solver, the incumbent freed, five joints from upperleg01 through foot,32 iterations, angular iteration limitπ, and no end extension. Native settings/internal state reset for every query. No anatomical hinge/pole or foot-orientation constraint is supplied in this bounded experiment. The previous persistent-setting run gives exactly identical metrics. Native results are captured inside the modifier signal, producing558 outputs. All chain transforms are finite, every query emits one active callback, segment length error stays below0.8µm, and origins outside that leg differ by less than0.84µm from the incumbent result.

Sampled floor checks use849 actual bound vertices across meshes, every16th source vertex with **combined** same-side foot/toe influence>.5. These are not all sole vertices. The static imported rig global transform is identity, independently checked; scenario movement only changes horizontal translation. Worst sampled vertex IDs, material surface indices and exact positions are recorded. Query-local minima are not comparable to full-controller per-frame extrema from role05.

| Query fixture / rate | Incumbent minimum foot sample (mm) | FABRIK (mm) | CCD (mm) |
| --- | ---: | ---: | ---: |
| Ordinary30Hz | +1.406 | −64.321 | −72.143 |
| Ordinary60Hz | −11.042 | −97.149 | −109.173 |
| Ordinary120Hz | −10.006 | −21.851 | −23.987 |
| Adversarial30Hz | +1.447 | −122.489 | −129.552 |
| Adversarial60Hz | +1.427 | −103.804 | −118.984 |
| Adversarial120Hz | +1.420 | −93.294 | −111.597 |

Across ordinary queries, maximum endpoint error is1.730mm incumbent,3.782mm FABRIK and9.720mm CCD; maximum foot orientation deviation is144.09°/152.35°. Adversarial queries reach165.14°/178.83° deviation. Strafe and backpedal also worsen sampled penetration. A concrete ordinary60Hz frame36 left-foot witness is RamaHero surface11 vertex42800, combined foot/toe weight1: FABRIK position(0.175082,−0.097149,−0.016179)m and CCD(0.187405,−0.109173,−0.040108)m. Small endpoint error can coexist with an upside-down or badly rolled sole.

## Preserved evidence and limits

`summary.json` records every solver/rate/scenario group, selected planted-query counts, endpoint error and source-bound worst-floor witnesses. `native-study.zip` retains full probes, executed logs, official engine source extracts and full exact Godot Variant pose tapes. The final tape contains164 named/rest bones, every prepose/incumbent result/target/clock, native outputs and sampled skin bindings. It is read with `FileAccess.get_var(false)`. The archive also retains the unavailable-native-call experiment, initial parse failure and initial side reassignment errors. The final run is clean;15/15 integrity checks pass. These checks validate the experiment, not motion acceptance.

This is a local solver experiment, not an integrated replacement. It does not establish improved joint/skin continuity, fixed-anchor release, support coverage, C0/C1 release, pause behavior, weapon/string contact, combat event timing or normal-speed visuals. Native replay has no authoritative controller to advance; recorded upstream clocks are preserved as inputs, not counted as a new gameplay timing test. Existing queries for reset/hitch/cancel do not change that limit. No character movement, rules, clips, timing or production sources changed. No new engine, import or render ran.

A constrained native design might behave differently, but that is a new implementation requiring its own source-bound contact and continuous evidence. These unconstrained candidates must remain rejected. Next owner: root and the independent R4 contact/motion reviewers, using the integrated R7 tape for current acceptance; UI launch/integration review resumes when U5 originals arrive.
