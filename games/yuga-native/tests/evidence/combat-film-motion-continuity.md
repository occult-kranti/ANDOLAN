# Independent film motion continuity

The loaded revision 4 film passes the numerical continuity gates with no frame-speed
review alerts. The guard-reset alert in revision 3 was repaired and rechecked against
unchanged thresholds. This analysis does not approve animation
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
these; they are review alerts rather than failure gates. Revision 3 exceeded them
during Ravana's guard-to-ready reset: 0.2662726 m fingertip travel, 50.2016337 degrees
forearm rotation, and 49.6559901 degrees local wrist rotation in one frame. The
planner extended only that action's blend from 0.12 to 0.32 seconds. Revision 4's
reset peaks at 0.1064850 m, 19.4095335 degrees, and 19.1736188 degrees respectively,
at 5.625–5.6666667 seconds. No frame-speed alerts remain anywhere in the film.
The film-wide maxima are now 0.1739273 m and 44.8082375 degrees during Rama's first
release at 4.2083333–4.25 seconds. The actual rendering still requires visual judgment.
The probe changed no runtime or art resources.

The screenplay and full native integration suites were also rerun once on revision
4: all 20 and 42 checks passed. Receipt times remain 4.75, 8.9, and 15.85 seconds.
The lowest sampled planted sole is 6.7588 mm above the floor; greatest horizontal
sole-centroid drift is 0.5637 mm. Both remain within the original contact gates.
Revision 3 geometry was 7.2811 mm / 0.3983 mm; the slightly different interpolation
does not cause penetration or a failed contact gate. UI, replay, backward seeks,
resource stability, and malformed input rejection pass unchanged.

The report contains every frame interval's maxima, both sides of each boundary,
exact worst actor/bone/action/times, and hashes of all sampled actor resources,
director, adapter, scene, screenplay, and test. They were unchanged during the run.
The report's five checks pass and the final headless log has no errors or warnings.

- Final report: `combat-film-motion-continuity-final.json`
- Report SHA-256: `4e54fddd377249740cc032f235126753a7ee9d5456c08359d221678805fa8dec`
- Manifest revision 4: `6ec07cb86aa645ba23c4eec51e652bbe89ad42d0558225583f6a8dd54248af6b`
- Godot: `4.6.3.stable.official.7d41c59c4`

The retained first run also passed, but used acos-based quaternion differences.
That formulation amplified near-zero float rounding to roughly 0.056 degrees.
The final probe uses atan2 of the relative quaternion vector length and absolute
scalar component, which remains stable near zero and handles quaternion sign
equivalence. This changed measurement precision, not thresholds or game assets.
Revision 3 reports, logs, and notes are retained under explicit `revision3` names.
