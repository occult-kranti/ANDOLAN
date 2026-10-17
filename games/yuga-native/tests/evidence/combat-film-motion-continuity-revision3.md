# Independent film motion continuity

The loaded final film passes the numerical continuity gates. One fast guard-reset
transition remains a visual-review alert. This analysis does not approve animation
beauty, character art, gameplay physics, or combat balance.

Run from the repository root:

```sh
godot --headless --path games/yuga-native --script res://tests/combat_motion_continuity.gd -- --report=/tmp/combat-motion.json
```

The probe samples the actual imported actors through the actual director at 24 Hz
(577 samples, including both endpoints). It also samples 10 microseconds before,
at, and after each of the 17 internal actor action boundaries. Each actor has 164
bones; the unweighted root and intentionally deforming bowstring are excluded.
The fixed skeleton-to-actor transform retains model metres and removes external
actor trajectory and yaw. Camera cuts therefore cannot inflate the measurements.
Both accumulated joint orientation and parent-relative joint rotation are measured.
The coordinated pelvis/spine crouch controls remain included in continuity checks.

All 203,472 measured bone poses are finite. All boundary checks pass the thresholds
fixed before sampling: 1 mm position and 0.5 degrees rotation across a maximum of
20 microseconds. There are no declared actor-pose cuts. Those tolerances are above
floating-point pose noise and below a visible animation jump. The largest boundary
position delta is 0.0000125935 m at Rama's right finger3-2, just before 7.95 seconds.
The largest actor-space angular delta is 0.0013895 degrees at left upperleg02; the
largest parent-relative delta is 0.0027090 degrees at left lowerleg01. Both occur
at the same evade-to-ready boundary.

The separate 24 Hz review thresholds are 0.25 m joint travel or 45 degrees rotation
per frame (6 m/s or 1080 degrees/s). Fast combat actions may legitimately exceed
these; they are review alerts rather than failure gates. One interval exceeds them:
Ravana's guard-to-ready reset at 5.5416667–5.5833333 seconds. His left finger3-3
travels 0.2662726 m, left lowerarm01 rotates 50.2016337 degrees, and left wrist local
rotation changes 49.6559901 degrees. The action boundary itself is continuous; the
motion occurs inside the 0.12-second blend. The rendered result needs judgment for
perceived speed or snapping. No runtime or art change was made by this probe.

The report contains every frame interval's maxima, both sides of each boundary,
exact worst actor/bone/action/times, and hashes of all sampled actor resources,
director, adapter, scene, screenplay, and test. They were unchanged during the run.
The report's five checks pass and the final headless log has no errors or warnings.

- Final report: `combat-film-motion-continuity-final.json`
- Report SHA-256: `0cbea926d36a632317c18ac6c44bb06514caebba3f2642d5216bdf767660a885`
- Manifest revision 3: `a7f9c8263f0117fa322f5a51ff765710bfe619026c076eda32d207aaf8be5826`
- Godot: `4.6.3.stable.official.7d41c59c4`

The retained first run also passed, but used acos-based quaternion differences.
That formulation amplified near-zero float rounding to roughly 0.056 degrees.
The final probe uses atan2 of the relative quaternion vector length and absolute
scalar component, which remains stable near zero and handles quaternion sign
equivalence. This changed measurement precision, not thresholds or game assets.
