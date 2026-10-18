# S2 W5 — bounded initial support admission

Disposition: numerical candidate accepted for the next integrated source freeze; continuous rendered motion, first-draw visibility, physical-GPU performance and play feel remain open. This is not a claim that support is solved. Runtime is frozen at `119db2e65a40c148725813137340bc109f057d98ea82ef777ab7735c999c661c`.

## Fresh defect and exact scope

The starting checkpoint was `98e10cc5184ba1b51b42113496a529d8cc8f62b0`. Its exact S1 controller (`a1042ea9cca9cf010817bdcaef282c9a33ffcfb66a2f9d330482d36ac4950c13`) is retained in `W5/baseline/rama_motion.gd`. The real imported courtyard scene was observed from before its first native `SkeletonModifier3D.modification_processed` callback. There were no direct animation-clock or evaluate-pose calls in this new fixture.

`lifecycle-r2.json` retains the first complete witness: at physics1/process0, two initial modifier samples had sole minima about +50.571mm and support not ready. At physics2/process1, the actual safe physics support admission produced +0.572mm soles and a 50.378mm maximum adjacent joint-origin step. Native cache/global-pose agreement was exact for164bones. Whether both callbacks would become visible frames is unproven: this was a headless observer, not a render.

The fixed cohort is13,580 foot/toe-dominated vertices from the initially visible imported mesh, using combined foot/toe weights>.5 and every qualifying vertex, not a source-order subsample. The cohort is retained across callbacks and CPU-skinned through the real running rig. This does not establish pixel coverage or every active LOD's visible geometry. Exact GLB, animation library, import descriptor and imported resource hashes are in each raw report.

## Bounded change

Only `scripts/rama_motion.gd` changes runtime behavior. On actor-bound configure/reset idle admission, a nearby downward correction eases for120ms from the previously evaluated ankle height to the measured support anchor. The actual world anchor is acquired once and stays fixed; only the solver's temporary vertical destination changes. Corrections outside the existing80mm probe range and upward corrections do not acquire this blend. Movement, landing and action updates end the special admission state. Root/capsule movement, ground query phase, animation writer, ability events and combat clocks are unchanged.

This deliberately trades immediate initial contact for a short descent. Boolean foot locks mean an anchor is held; they do **not** mean the sole has reached the floor during admission. At60Hz the initial maximum anchor endpoint error is50.000459mm during the blend, versus approximately0.000278mm baseline. This error is retained in raw diagnostics. No threshold or support count was relabelled to hide it.

## Same-sequence comparison

Final raw candidate reports are `candidate-{30,60,120}-r3.json`; exact baseline reports are `baseline-30-r2.json`, `baseline-60.json`, `baseline-120-r2.json`. Each executes15 lifecycle assertions on an actual courtyard scene. The separate comparator passes39/39 source-bound gates. These are repeated rate evaluations, not45 distinct scenarios. Six existing S1 release assertions were rerun and passed unchanged; they are regression checks, not new S2 acceptance claims.

Maximum joint-origin step within the admission window, millimetres:

| Window |30Hz before→after|60Hz before→after|120Hz before→after|
|---|---:|---:|---:|
|Initial title|50.378→19.991|50.378→10.864|50.378→8.036|
|Title return from fullbody recovery|51.836→18.622|50.555→10.408|50.632→5.642|
|Title return after public cancel|50.567→20.119|50.640→10.556|50.635→5.715|

The complete fullbody-return window still contains the separate reset boundary (38.746mm at60Hz); the table isolates support admission and does not suppress the other raw samples. Admission completed in4/8/15 native updates at30/60/120Hz, respectively (133.3/133.3/125ms). Tree freeze held the age and pose; the first resumed age increment was at most one normal physics delta. No wall-time catch-up occurred.

All compared root positions, velocities, complete kit reports, authority events, army clocks and action/gait clocks match baseline exactly. Outside the three intentional idle-entry windows, all sampled joint positions and quaternions match baseline. No sampled sole penetration is new or deeper. Acquired world-anchor drift is0 in all nine admission windows; final sole gaps return to baseline within1micrometre. This is not a C1/angular-velocity or skin-surface continuity certificate.

Initial title side-callback samples (eligible / locked / actually within±5mm of floor):

|Rate|Idle eligible, both versions|Locked, before→after|Actual floor contact, before→after|
|---|---:|---:|---:|
|30Hz|22|18→18|18→12|
|60Hz|42|38→38|38→26|
|120Hz|82|78→78|78→54|

Eligibility here is the observed idle/no-action phase after the existing transition interval. It includes the provisional callbacks; it is not inferred from lock count. Per-phase counts for every baseline/candidate, including both title returns and moving entry, are in `comparison-final.json`. At60Hz each title-return admission also loses12 actual floor side-samples while retaining its fixed anchors. Ordinary stance coverage remains equal.

## Retained failures and residual defects

The first fixture attempt (`lifecycle-fixture-r1.gd`, `lifecycle-r1-output.txt`) used a nonexistent direct kit property and was stopped after its script error. Its unfixed source/log remain. The corrected original witness fixture is `lifecycle-fixture-r2.gd`, hash-verified against `lifecycle-r2.json`. Fixed-rate scheduling was added for controlled rate comparisons; headless observer cost is not performance evidence.

W6's first catalog attempt also exposed the S1 fixture's obsolete inherited G1 scratch baseline and oversized pretty JSON. The fixture now defaults to the tracked S1 baseline and accepts `--compact-report`. All four full164-bone snapshots per trial and all six assertions remain; compact output is about4.23MB, below the unchanged8MiB runner cap.

After correcting that baseline, a real S2 scope leak remained: bare imported-preview reset at30Hz changed `lowerleg01.L` by3.835956mm at recovery frame4. `s1-release-scope-before.json` and `rejected-preview-reset/rama_motion.gd` preserve it. Reset admission now requires the same actor collision ancestry as configure. `s1-release-scope-after.json` passes6/6. All actual-actor rows, moments and events at all three rates are exactly data-equal before/after that scope fix (`actor-scope-fix-comparison.json`). No assertion tolerance changed.

Existing transition/contact failures remain exactly equal in both versions:

|Minimum signed sole height|30Hz|60Hz|120Hz|
|---|---:|---:|---:|
|Training entry|−34.318mm|−25.952mm|−11.350mm|
|Moving reset entry|−48.115mm|−49.233mm|−49.384mm|
|Stop after moving entry|−7.180mm|−7.428mm|−18.433mm|

These are candidates for the next motion investigation. Initial idle blending does not repair them. Player root/collision and gameplay clocks remain outside this worker's edit scope.

## Reproduction and capture handoff

`execution-r3.json` records final engine argv, exit0 and durations. Environment: `LP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1`, unique `XDG_DATA_HOME`, CPU2, Godot4.6.3 official7d41c59c4, `--headless --max-threads 1 --fixed-fps HZ`. Use `res://tests/desktop_s2_motion_lifecycle_cases.gd -- --hz=HZ --report=...`. Baseline replay uses the preserved exact controller in a scripts-only isolated project view, with the same existing imported assets; no editor/import was run. Final analysis command:

```sh
python games/yuga-native/tests/desktop_s2_motion_compare.py --evidence games/yuga-native/docs/evidence/desktop-finish/S2/W5 --report /tmp/s2-motion-comparison.json
```

Root/W1 should capture the first drawable frame onward, without settled preroll, and map final-modifier samples to drawn frame counters. Minimal controlled tape: initial title0–12, actual start_training13, accepted Measured Step30, return_to_menu36 during recovery, observe through60. Record exact action event times, active LOD, rig/root/camera and the new `idle_support_age` alongside support readiness, fixed anchors, real skinned soles and actual floor ray. Pair baseline/candidate camera/light/source controls. The existing settled G0 support anchors and S1 captures do not certify this first-acquisition seam. Pause/reset timing and moving penetration need separate continuous follow-up if not naturally covered by the integrated take.

W6 independently accepted the corrected six-release-check catalog and selected182checks on finalmotion119db2e6 (`../W6/selected-visual-final`). This adds regression/integration evidence, not rendered motion acceptance. HUD stays at its S1 source in this packet; S3 HUD ownership passes to W2. No mobile changes, imports, new renders or commits were performed by W5.
