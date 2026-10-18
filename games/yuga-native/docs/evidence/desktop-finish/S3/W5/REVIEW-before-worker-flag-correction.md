# S3 W5 — grounded transition floor protection

Disposition: **bounded contact candidate; continuous visual acceptance remains open**. The preserved strict comparison is **25/27**, not an all-pass motion result. Root accepted this candidate for matched visual review, explicitly retaining the measured swing and landing tradeoffs. No player, collision, authority, action clock, weapon socket, HUD, material or asset source changed in this packet.

Source checkpoint before this change: `31ca18948c691c31719c92afd3245e75cea8c8d1`. Exact S2 baseline motion: `119db2e65a40c148725813137340bc109f057d98ea82ef777ab7735c999c661c`, preserved in [baseline/rama_motion.gd](W5/baseline/rama_motion.gd). Candidate motion: `8c3771a343a0538d749147393d0c407b1fb377d774a91b4cf99734e4852520f8`, preserved in [candidate/rama_motion.gd](W5/candidate/rama_motion.gd). Canonical motion remains this frozen candidate.

## Finding and bounded change

A real actor drops from its inactive title root height to the physical floor while the locomotion crossfade still carries the prior contact-compressed legs. Existing planting deliberately waits for that transition to finish; walk→run can restart the wait. The fresh native baseline reproduced grounded sole penetration at training entry and forward/back/side moving resets. The retained [native failure pose](W5/guard-witness.json) includes all164 bone globals and the exact source trace identity.

The candidate adds one leg-only guard immediately before existing contact processing. During an actor-bound, active grounded crossfade, it asks the existing four-segment leg solver to raise an ankle below the supplied support plane plus its original rest offset. It preserves horizontal target coordinates and never assigns a plant anchor. The correction is bounded by the existing80mm support range and1mm trigger. Idle uses the measured support plane; age0 and completed transitions stay unchanged. Air, flight, grapple, jump/fall/dash, death and active Measured Step are excluded. Standalone model previews without a collision ancestor are excluded. The ordinary contact solver and its later acquisition timing remain intact.

The guard can affect the next transition's leg snapshot. It does not establish perfect reach, C1 velocity continuity or fully solved gait. Actual skinned geometry, rather than ankle height alone, supplies the contact result below.

## Executed evidence

- Fresh native courtyard fixture, Godot4.6.3 official7d41c59c4, fixed30/60/120Hz, real scene/player callbacks and public scene/kit controls: baseline **7/11** at every rate; candidate **11/11** at every rate. The same four contact assertions fail in each baseline. Candidate observes all qualifying source foot/toe vertices of each active visible LOD: near13,580 and mid11,131; no source-order sample subset.
- [Actual imported near/mid/far guard boundaries](W5/guard-r3.json): **57/57**, clean engine log.54 declared skin/pose trials cover age0/end/after,1mm threshold,80mm bound, all listed exclusions, unchanged preview, frozen repeated application and nonleg/root/anchor/clock ownership. A separate never-grounded actor begins with airborne state and stays baseline-equal for18 updates. These are explicitly injected component boundaries, not native rendered controls.
- [Cross-tape comparison](W5/comparison-r2.json): **25/27**. At every rate all recorded roots/rig transforms, velocity, kit reports, army clocks, action/transition diagnostics, complete combat events, four weapon sockets, plant targets and all nonleg global poses are exact. Public bow cancel and protected Measured Step full poses are exact. No recorded phase has a deeper minimum sole penetration. The two strict step-size failures remain below.
- W6 independently executed the final portable scene fixture **11/11** and guard fixture **57/57**; its archive is [S3/W6/motion-final](W6/motion-final). The runner validates adjacent gzip identity, full row/bone census, and equality of all non-pose summary fields to the trace. These independent passes do not supersede the25/27 result.
- The optional capture overlay received **parse-only** validation, clean exit0. It has not received preflight or rendered execution in this packet.

Commands use one Godot worker and LP/OMP/BLAS1 on coordinatedCPU2; no import or render was performed here. Exact commands, engine logs and exit classifications are adjacent execution receipts. Large native traces were stored as lossless gzip immediately, with mtime0 and exact raw/compressed SHA256 and sizes. The [artifact manifest](W5/artifact-manifest.json) inventories every retained file.

## Actual grounded sole results

Distances are millimetres from the test's real courtyard floor plane. Actual contact is a side/callback whose minimum skinned sole lies within±5mm; it is distinct from a boolean foot lock. Counts use the first authority generation of each declared phase, separating the subsequent return-to-menu reset. A negative value is penetration, even when inside the existing−5mm acceptance gate.

| Hz | Native phase | Minimum sole, baseline → candidate (mm) | Actual floor-contact side samples / grounded eligible samples | Boolean lock side samples, baseline → candidate |
| --- | --- | ---: | ---: | ---: |
| 30 | training_entry | -34.318 → 0.572 | 18 → 22 / 22 | 12 → 12 |
| 30 | reset_move_forward | -47.833 → 0.572 | 4 → 9 / 14 | 2 → 2 |
| 30 | reset_move_back | -38.322 → 0.572 | 4 → 9 / 14 | 2 → 2 |
| 30 | reset_move_left | -43.323 → 0.572 | 3 → 9 / 14 | 2 → 2 |
| 60 | training_entry | -25.952 → 0.572 | 34 → 42 / 42 | 18 → 18 |
| 60 | reset_move_forward | -52.441 → 0.572 | 3 → 16 / 28 | 2 → 2 |
| 60 | reset_move_back | -46.502 → 0.572 | 4 → 14 / 28 | 2 → 2 |
| 60 | reset_move_left | -45.621 → 0.521 | 4 → 16 / 28 | 2 → 2 |
| 120 | training_entry | -11.350 → 0.016 | 68 → 80 / 80 | 32 → 32 |
| 120 | reset_move_forward | -49.144 → 0.077 | 6 → 34 / 56 | 2 → 2 |
| 120 | reset_move_back | -47.923 → -0.134 | 7 → 29 / 56 | 2 → 2 |
| 120 | reset_move_left | -47.374 → 0.227 | 10 → 33 / 56 | 2 → 2 |

The slightly negative120Hz backpedal minimum (−0.134mm) is retained, not rounded to zero. Training airborne samples remain −9.623/−7.772/−6.636mm at30/60/120Hz, outside this grounded guard. Protected Measured Step remains −19.995/−24.129/−24.150mm. These are unresolved scope boundaries, not passing contact claims. Fixed plant-target arrays and lock states are exact across the paired native tapes; apparent sliding is still a visual-review question.

## Retained tradeoffs and correction to evidence grouping

The first comparator was26/27. A fixture label continued through return_to_menu, allowing a reset teleport to dominate the training maximum ankle step. That raw report remains [comparison-r1.json](W5/comparison-r1.json). The corrected comparator separates authority generations without altering raw rows, and the final fixture assigns a distinct return label before the public call. This reveals a second real failed strict check:

| Witness | Baseline → candidate adjacent world ankle displacement | Interpretation |
| --- | --- | --- |
|60Hz forward run swing, physics76→77, right foot, both unlocked |178.083→178.311mm (+0.228mm) |Candidate delta XYZ = (−0.185,+5.549,−178.225)mm. Horizontal motion dominates.|
|60Hz strafe run swing, physics208→209, right foot, both unlocked |183.106→183.325mm (+0.219mm) |Candidate delta XYZ = (−183.246,+5.394,−0.126)mm.|
|120Hz first landing lift, physics49→50, right foot, both unlocked |4.889→7.324mm (+2.435mm) |Candidate delta XYZ = (+0.006,+7.324,+0.010)mm; almost entirely vertical.|

At30/60Hz, the same isolated training-entry maximum instead falls24.711→10.371mm and18.338→8.480mm. No thresholds were relaxed and no extra ankle distortion was added to force the strict no-increase check green. The new landing lift trades a faster upward correction for avoiding existing below-floor geometry. A30fps capture alone cannot resolve the120Hz one-physics-frame peak; its full callback evidence must remain alongside any pixels. This headless fixture does not record a camera, so no screen-space number is inferred.

Early harness failures are retained: [guard-r1-output.txt](W5/guard-r1-output.txt) is a GDScript inferred-type parse failure; [guard-r2-output.txt](W5/guard-r2-output.txt) has typed-array runtime errors and ran only2 checks despite exit0. That run is explicitly invalid in its execution receipt. The corrected fixture enforces all54 boundary cases executed, then the never-grounded and source-stability checks, yielding57 clean checks. No early report is substituted for final evidence.

## Capture handoff and remaining gate

[The optional overlay](W5/capture-transition.gd) reuses the existing final-modifier observer, actual imported skin/rays and source-seal checks. Its120 consecutive frames use one declared camera and public start/reset plus input strengths: frame0 start_training;15 analog walk;30 full run;45 reset while moving;65 stop;70 jump;71 jump release; then land/settle. It deliberately starts after title preroll, so earliest drawable support acquisition remains open. Root owns both staged snapshots, preflight, software/GPU capture lane and independent original-image review.

Create matched snapshots with every runtime/import/camera/light byte identical except the two exact motion scripts above. Do not use the temporary baseline headless project as an art freeze: it was a scripts-only comparison view. Seal each intended snapshot identity independently. Use this overlay unchanged in both, run preflight first, and require actual observed walk/run/land and matching camera/source receipts before rendering. The controls are fixture API/Input calls, not native XTest or physical-device play.

Example root-owned preflight command (replace the two absolute placeholders with a sealed snapshot and a fresh output; the existing snapshot descriptor is required):

```sh
env LP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1   taskset -c 3 godot --headless --max-threads 1 --fixed-fps 30   --path /ABS/SEALED_PROJECT   --script res://docs/evidence/desktop-finish/S3/W5/capture-transition.gd --   --output=/ABS/FRESH_PREFLIGHT --preflight
```

Actual capture uses the same script/controls with X11 Forward+, the established isolated display/cache/watchdog runner, and no --preflight. The existing run_focus.py case whitelist does not yet dispatch this optional overlay; do not silently relabel it as the60-frame cast case. Review contact, the start of upward landing correction, walk→run swing continuity, moving reset and final settling against the exact baseline. Preserve original full framebuffers and all callback data. Physical-GPU performance, human feel, first-visible title acquisition and overall motion quality remain open.

No commits, shared ledgers or previous-round reports were changed. Next owners: root/W1 for paired continuous evidence; W6 for source-bound catalog closure. W3's optional fletching proof is separately pinned and has no motion ownership implication.
