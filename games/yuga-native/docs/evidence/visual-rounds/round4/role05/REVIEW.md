# R4-05: continuous support/release study — all candidates rejected

Product: YUGA native. Source commit `0437ea91edf6989ff78c1eeadb3661f4825b60f2`.
No runtime controller, movement law, rules, assets, import, renderer, ledger or
commit changed. The accepted runtime controller remains
`4c72fd247704896bbf8b720658efff1388d850912f7aed6a916950538aa458c1`.

## Decision

**Do not promote either staged controller.** The bounded study reduces the
original reversal discontinuities without moving active plant anchors or
changing event clocks, but broader skin and release checks find new defects.
The current 39-check motion suite passes both r3a and r4 and does not detect
these transient regressions. Their explicit failed metrics govern this review.

`rama_motion.release-r3a.gd` is the more useful continuation study. It preserves
fixed world plants, labels stance/reach exits as release, carries a 100 ms
quintic position/velocity residual, bounds presentation heading at 10 rad/s and
reuses the existing four-segment leg solver. Pose reapplication holds history
without another update. It does not change velocity, gait phase or action timing.
`rama_motion.release-r4.gd` is a rejected diagnostic correction that removes the
pelvis tail and clamps released targets to the existing ankle plane. Its worse
release derivatives demonstrate that ankle clamping alone is insufficient.

## Unchanged archived fixtures

The original ordinary fixture applies 38 m/s² per-axis acceleration; the stress
fixture instantaneously changes cardinal direction. The same imported 164-bone
hero, library and archived probe were executed. Values below are maximum local
joint-origin steps in millimetres. They are measurements, not acceptance bounds.

| Fixture | Hz | Baseline | r3a | r4 | Eligible / r3a planted / r4 planted frames |
| --- | ---: | ---: | ---: | ---: | --- |
| Ordinary |30|339.283|286.256|286.256|15 /15 /15|
| Ordinary |60|309.803|156.361|156.361|26 /26 /26|
| Ordinary |120|161.919|97.096|97.096|50 /50 /50|
| Adversarial |30|949.560|501.033|501.032|23 /22 /22|
| Adversarial |60|927.054|271.561|271.561|46 /41 /41|
| Adversarial |120|912.671|158.207|153.887|96 /83 /83|

Active plant anchors have zero measured drift in every original fixture.
Planted solver errors remain below 2 mm. The ordinary stance coverage is retained;
stress coverage falls because unreachable plants are released honestly. r1 had
reduced ordinary 120 Hz coverage from 50 to 4 frames and was rejected. r2 restored
coverage but caused a 491.897 mm ordinary 120 Hz reacquisition snap and was rejected.
Every candidate, parse failure, raw report and log is retained in the archive.
The earlier angular/projection candidates remain rejected in their original packet.

## Broader evidence and unresolved defects

The expanded probe executes 11 scenarios at 30/60/120 Hz: ordinary/stress reversal,
start/stop, traversal/jump/land, aimed strafe/backpedal, gradual steering,
stationary aim, action cancel, reset and 80 ms hitch. Every trial also reapplies
its pose without advancing time. Both r3a and r4 pass 66 finite-input/event-clock
checks; both pass the existing 39-check actual-rig motion suite, including its
sole/finger/string tests. These are 105 executed assertions per candidate, not
motion acceptance. Event-clock equivalence concerns the controller and explicit
request/release tape; it does not execute the full 20 Hz combat integration.

The expanded probe CPU-skins every 96th imported vertex per surface. See the
summary for its exact sample count. This samples real imported skin, not joints
or proxy geometry; it is not exhaustive mesh penetration or rendered evidence.
The separate existing suite collects its full selected sole/finger populations.

At 120 Hz, r3a changes ordinary sampled-skin maximum step from183.044 to102.081mm,
but sampled minimum world height worsens from−31.584 to−47.123mm. Start/stop
maximum joint step worsens from89.431 to118.628mm and sampled skin step from
129.712 to161.744mm. r4 retains both failures. Aimed strafe/backpedal also retain
transient sampled floor regressions. Actual near-floor sample coverage is
reported separately from eligible and planted frame counts; a true lock boolean
is not used as proof of actual floor contact.

The event probe records immutable plant IDs, original anchors, release reason,
outgoing corrected point/velocity and each sample's state, clock, input/root,
foot positions and contact errors. The release residual's algebraic boundary
matching does **not** guarantee final constrained IK continuity. r4's ordinary
120 Hz release differs from the outgoing extrapolated point by up to 26.257 mm;
stress reaches 136.762 mm. r3a also retains constrained boundary error. Finite-
difference release velocity changes and acceleration are in the raw continuity
reports. **C0/C1 release acceptance remains failed/open.** Reach saturation and
pelvis/target coupling must be solved together, not hidden by moving anchors.
Reset deliberately teleports: its large world-space deltas are recorded but
are not interpreted as ordinary gait failures. No normal-speed capture or art
acceptance was performed.

## Reproduce and hand off

`source-pins.json` hashes the controller, source GLB, actual imported SCN, import
settings, clip library, player, existing test and original rejection archive.
`summary.json` separates all failed candidates, full 30/60/120 comparisons,
coverage, sampled skin, actual release-boundary errors and test limitations.
`test-receipt.json` records successful executions and the two parse-timeout
failures plus a deliberately terminated denser diagnostic. The replacement's
sampling is declared; no thresholds or old fixture values were changed.

Verify the sealed packet:

```sh
python3 games/yuga-native/docs/evidence/visual-rounds/round4/role05/verify.py
```

Run an original differential fixture from repository root, substituting a fresh
absolute output path:

```sh
taskset -c 0,1 timeout 30s godot --headless --path games/yuga-native \
  --script /workspace/ANDOLAN/scratch/visual-round4/role-05/archived/probe-acceleration.gd -- \
  --candidate-script=/workspace/ANDOLAN/scratch/visual-round4/role-05/rama_motion.release-r3a.gd \
  --baseline-script=/workspace/ANDOLAN/scratch/visual-round4/role-05/rama_motion.baseline.gd \
  --report=/tmp/r4-motion-fresh.json
```

Use `probe-continuity.gd` with `timeout 180s` for the expanded 33-trial skin run,
and `probe-events.gd` for original-anchor/release tracing. Exact source/hash
identity is embedded in each output. The archive retains all required scripts
and reports. The existing-suite wrappers reference this workspace's staged
controller paths; update only that preload path after extracting elsewhere.

Next owner: root's independent R4 motion/review roles. Preserve the broad
counterexamples, design a coupled reachable release with predictive margin,
and require both ordinary transient floor and boundary-continuity checks before
another promotion proposal. Final integrated R3 source and continuous captures
remain a later acceptance dependency. The existing environment/tools were
sufficient; no install/start configuration changes were needed.
