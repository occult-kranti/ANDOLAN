# Actual landing review — bounded acceptance recommendation

**Recommend accepting the private d555 landing presentation change for this matched jump/landing scope. No canonical file was changed by this review.** The candidate reaches the collision floor on the first observed grounded frame, and the adjacent originals show coherent knee compression without a new visible foot snap, leg inversion or whole-body displacement. This is a modest contact improvement, not completion of character animation quality.

I directly opened all **32 candidate original PNGs** (225–255 and 269), plus retained canonical originals 235, 237, 240, 248–252. These are sequential still-image inspections, not real-time human playback. The full 270-frame final-modifier trace was compared with the retained baseline by `analyze.py`; `pose-review-durable.json` preserves the comparison, hashes and compact adjacent metrics. No engine, import, raster, performance test or gameplay execution was run for this review.

## Contact and compression

At first observed ground contact, frame 249 / physics 587 / process 293, the candidate's imported skinned sole gaps are **1.082585 mm left and 1.082910 mm right**, within the 5 mm target. The retained canonical gaps at the identical root/clock sample are **111.421786 mm and 75.347401 mm**. Frames 250–255 remain approximately 1.41 mm above the measured floor. No selected landing-window sole vertex is below the −5 mm limit. Normal foot anchors remain unlocked through 251 and lock at 252, exactly as before.

Frames 235–240 spread the change from the rising pose into a straighter descent. Frames 241–248 retain that extended leg pose while the root continues descending; they are not world-locked feet. Frames 249–254 show contact followed by knee compression, then recovery at 255. Compared with the old raised-foot fall and delayed lowering, contact reads more coherently. The longer straight-leg descent remains relatively stiff and is an explicit art limitation.

The prior **25.168° per-step component result at 30 Hz physics remains retained**, not replaced by an easier statistic. This actual run uses **60 Hz physics and 30 Hz observations**. Reconstructed local left-knee steps across actual 248→249→250→251→252 are **1.359°, 22.049°, 21.944°, 4.403°** at adjacent 33.333 ms observation intervals. The large compression is visible but progresses across multiple frames while the soles stay near the floor. At first contact the ankle moves about 120.822 mm in world space, almost entirely following the root; its root-relative movement is only 0.824 mm. This supports contact continuity in the reviewed take, not a bound on all possible joint accelerations.

An **inherited 26.812° knee recovery step at 254→255** is numerically identical in both branches. It remains a motion-quality limitation. Every global pose is identical again from frame 252 onward; the candidate does not repair that recovery or the wider authored landing style.

## Exact controls and source scope

All 270 `final_modifier_body` dictionaries are exactly equal, including root/rig transforms, capsule state, velocity, input, floor state, kit/army clocks, actions, transition ages, anchor positions and locks. Camera, render settings, lighting, materials, face, secondary motion, input sequence and physics/process counters also match exactly. All **126 non-leg global bone transforms** match at every frame. Only 38 leg/toe global transforms differ, only in frames 235–251. Both traces retain 164 finite bone transforms per observation.

The 1,030 capture source records differ only in the expected snapshot marker, `rama_motion.gd` and image-filter leaf helper. Candidate motion is `d5550b25044ea97c9ce482a130ac73f012c313e96f2029a555abb590e1375b0e`; baseline is `5023b301ff4c4585e3b6a22827f55f4696045bb0206374ee1656a5b4bad6e4a5`. The helper preserves all 270 draws/observations and emits only the declared 32 PNGs. Every emitted PNG was rehashed against its raw observation. The run exited 0, its ten coverage predicates passed, before/after sources and both cache seeds remained unchanged, and the run report binds the exact pair, stage and rendering inputs.

This is the deliberately retained matched courtyard context, not a new production-world or package qualification. The engine is the explicitly patched e69 template, with Forward+ on llvmpipe; no hardware FPS, native performance, audio listening or human game-feel conclusion follows. Slow/high-speed falls, support loss and 30/60/120 Hz safety remain component evidence, not additional actual-image takes. Prior rejected mechanisms and the inherited 26/27 support tradeoff remain historical and unmodified.

## Integration handoff

Root owns any atomic canonical promotion after W1's run/provenance seal. Minimum affected existing gates are `desktop-landing-support-boundary` and `desktop-landing-pause`. A compact maintained regression should cover missing-`land` rejection and imported-skin jump/fall first contact at 30/60/120 Hz, retaining root/non-leg/clock/anchor controls; it should load the canonical motion script and emit a compact result rather than another large pose archive. This recommendation is not a claim that those post-promotion checks have run.

Raw candidate originals and trace remain [W1-owned](../../W1-actual-r1/motion-candidate-r1/receipt.json), owner receipt SHA256 `bc8d344e78b2b048c25f425da155adf158ed7f258efd51ed4b2de1bdb2528fee`. The durable replay rehashes every owner artifact and verifies the gzip decodes to the original 16,703,321-byte trace. The initial scratch-path comparison is retained as `pose-review.json`; the durable comparison has identical pose/control results. This review adds no PNG or full-trace copy.
