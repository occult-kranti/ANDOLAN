# G2 motion — actual idle support plane

**Bounded candidate frozen; rendered support and continuous motion acceptance pending.** Only `scripts/rama_motion.gd` changed. G1's arm-entry blend remains a candidate; its original accepted controller and failed attempts remain intact. No capsule, player root, teleport rule, flight rule, authority, clock, material, UI or LOD interface source changed.

## Diagnosis from actual evidence

Opened [G1 title day](motion/reference-g1-01-title-day.png) at original resolution (byte-exact original from `/tmp/yuga-g1-native-r1`). Its [receipt](motion/reference-g1-01-title-day.json) reports inactive title player root `y=0.050000000745`, physically ungrounded, yet both motion foot locks true with submicrometre endpoint error. The existing player passes its own root height as `floor_y` and treats inactive title presentation as grounded. Thus the solver can hold its ankle target accurately while that target's plane is 50 mm above the real floor.

The [fresh baseline probe](motion/support-r1-baseline.json) loaded the actual courtyard and found the real collision ray at `[0,0,12]`, normal `[0,1,0]`, while root/floor input remained 0.05. Its controlled same-state imported soles measured approximately **50.571 mm** above that plane at all three LODs and 30/60/120 Hz. The raised-deck case reproduced the same offset with root 0.49 and actual plane 0.44. This is a ground-input/acquisition error; an accurate lock boolean was insufficient evidence of visible contact. The old R4 probe's initial locked 50.570-mm gap is consistent but retains its separate source identity.

## Change and exact scope

The existing physics-driven `update_motion` now attempts a nearby ground-plane sample for each **unlocked idle** foot. It requires a physics frame, a rig inside the tree, an available World3D, grounded ground traversal, a hit within ±80 mm of the supplied plane, and an almost-flat upward normal (`dot > .9999`). Queries use the existing environment collision layer and exclude ancestor collision objects. A miss, distant hit or rejected slope completes admission and preserves the supplied-plane fallback. No query occurs inside the modifier callback or off-tree/off-physics path.

Before an actor's first safe physics attempt, the original fallback IK pose is preserved but its target is provisional, not marked as a fixed ground anchor. This handles the actual first-modifier-before-physics order without permanently locking the elevated fallback. Once acquired, the target remains fixed; normal gait targets, existing teleport replant semantics, the four-segment leg solver and 140-mm pelvic compression bound remain unchanged. No new advancing clock or skeleton writer was added. Standalone/manual rigs retain the original fallback behavior.

Sources:

- G1 candidate baseline: `e64c3752b79b2a27faced459becbdc04170cd6ba487ee6bf3c404eeba31c0f34`, [exact copy](motion/baseline-g1.gd).
- G2 frozen candidate: `35a9e58e6c720c67cd6e77fb812900bc05dec9d2fbd255b7bd8aa40b39e20fb3`, [exact copy](motion/candidate-final.gd).
- Near/mid/far raw R7 identities remain `8b6cf0f4…3384d5c`, `d95a061e…85beed`, `ee2e3527…c6317c`. [Final report](motion/support-r4-candidate.json) pins exact raw/import/cache/library/caller bytes before and after execution. The [manifest](motion/artifact-manifest.json) pins all raw results, fixtures and retained failed candidates.

## Same-state sole results

Distances below are the lowest selected **skinned** sole vertex per side above the measured flat plane, in millimetres. Selection sums all same-side foot/toe weights above 0.5 and includes low source vertices; it does not use a single dominant-influence shortcut. This is CPU skin reconstruction from actual imported arrays and inverse binds, not a GPU or image measurement.

| Hz | Asset | Condition | G1 left / right | G2 left / right |
|---:|---|---|---:|---:|
| 30 | rama-hero.glb | idle | 50.571132 / 50.571192 | 0.571962 / 0.571728 |
| 60 | rama-hero.glb | idle | 50.571129 / 50.571192 | 0.571948 / 0.571728 |
| 60 | rama-hero.glb | elevated | 50.571171 / 50.571141 | 0.571964 / 0.571815 |
| 60 | rama-hero-mid.glb | idle | 50.571129 / 50.571192 | 0.571948 / 0.571728 |
| 60 | rama-hero-far.glb | idle | 50.571129 / 50.571192 | 0.571948 / 0.571728 |
| 120 | rama-hero.glb | idle | 50.571162 / 50.571065 | 0.571869 / 0.571847 |

[Final support suite](motion/support-r4-candidate.json): **12/12 gates**, 16 baseline/candidate pairs. The actual native title path also passes: visible mid-LOD left/right minima are **0.571918 / 0.571690 mm**, root remains **0.05 m**, and the actual plane remains **0 m**. Witnesses are `RamaHeroLOD1`, surface 11, vertex 31784 left and 20082 right. The native title metric uses the controller's last final-modifier pose cache and actual visible imported skin; the forthcoming capture observer will bind final pose/body/draw counters and pixels independently.

All sampled corrected idle/deck sole vertices stay above the plane; no sampled vertices penetrate below −5 mm. Acquired world anchors have **zero drift within each lock episode**. Steady idle/deck sampled skin drift is at most **1.924 µm**, versus roughly 0.51–0.55 mm in the baseline, under the unchanged 10-µm nonregression allowance. Reset/flight transitions are not counted as steady planted-skin drift. Ordinary walk, flight, grapple, airborne, absent-plane, out-of-range and rejected-slope final poses remain baseline-equal within 10 µm. Supplied-plane fallback locks complete normally. Direct reset/teleport to the actual 0.44-m deck and flight→landing→idle reach the corrected idle plane; these are controlled presentation scenarios, not new authoritative gameplay claims.

[Initial frozen-pose adversary](motion/initial-r2.json): **2/2**. Before the first physics attempt, all body-joint origins match the baseline within 10 µm; ten reevaluations without an update hold the pose. Safe-query misses, configure/reset before first physics, detached/no-world calls and teardown while admission is pending pass with clean engine logs. [Existing motion suite](motion/existing-motion-r1.json): **39/39**, including rig/library, sampled contact, bow/string, cancellation and invalid-state/reset guards. Existing source semantics preserve combat timing; actual cast/pause/release observation is still delegated to the continuous capture.

## Failed candidates and checks retained

- [Baseline r1](motion/support-r1-baseline.json) intentionally fails the corrected-support assertion: 50.571-mm gap confirmed, with no candidate change.
- [Candidate r2](motion/candidate-r2-native-miss.gd), hash `4f9cf7a2…813a3`, passed ten controlled gates but **failed actual native title support**. Its raw report still contains native soles at 50.571 mm: initial modifier evaluation had already locked the fallback before physics could query. The omitted native assertion is explicitly recorded as a failure in [native disposition](motion/support-r2-native-disposition.json); no original result was overwritten. The final fixture has an explicit actual-native-sole gate.
- [Candidate r3](motion/candidate-r3.gd) fixed native acquisition and passed twelve support gates, but [initial-pose adversary r1](motion/initial-r1.json) found a **2.378-mm body-joint difference** when support IK was skipped before physics. The final candidate retains provisional fallback IK while deferring only the lock. The unchanged initial-pose adversary then passes. Both exact candidate and fixture are preserved.

## Capture handoff and limits

[Capture request](motion/capture-request.json): two short actual anchors—title and settled training—with same-callback skinned soles, support ray, world-space targets, actor/capsule transforms, active LOD and clocks. Acceptance owns the separate 60-frame real Piercing cancel→Kodanda release tape for G1's arm entry. Combined G2 art/environment changes require their own full source freeze; do not attribute unrelated pixels to this motion change.

This corrects a bounded nearby flat support-plane error. It does not repair R4 moving stop/landing release gaps, deep unreachable support, slopes, whole-body triangle collision, or the separate player-owned cast-root turn. First acquisition can change the provisional target by up to 80 mm; this is **not** a C1 release treatment or proof that an initial visual pop is absent. Normal-speed pixels remain necessary. No rejected R4 lowering/release/IK candidate was restored.

All final tests exited 0, with no engine errors/warnings, on CPU2 using Godot 4.6.3, one engine thread and LP/OMP/BLAS=1. Main command:

```sh
env LP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  XDG_DATA_HOME=/tmp/yuga-g2-support-r4 taskset -c 2 timeout 180s \
  godot --headless --max-threads 1 --path games/yuga-native \
  --script res://tests/graphics_g2_support_cases.gd -- \
  --report=/workspace/ANDOLAN/games/yuga-native/docs/evidence/graphics-six/G2/motion/support-r4-candidate.json
```

The two other final scripts are `graphics_g2_initial_pose_cases.gd` and `rama_motion_cases.gd`, with fresh XDG directories `/tmp/yuga-g2-initial-r2` and `/tmp/yuga-g2-motion-regression-r1` and reports named above. No import, heavy render, commit or shared-ledger edit was performed. G2 runtime/tests are frozen pending actual support/cast review; the worker stops at this subgoal.
