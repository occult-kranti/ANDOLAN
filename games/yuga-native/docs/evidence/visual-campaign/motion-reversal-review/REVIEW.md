# Rapid reversal: rejected motion candidates

**MOTION-RAPID-REVERSAL-01 remains OPEN.** Every prototype in this packet was
rejected. The accepted gait and braking correction remains at runtime SHA-256
`4c72fd247704896bbf8b720658efff1388d850912f7aed6a916950538aa458c1`.
This investigation changed no canonical runtime or test files.

The source checkout was based on `38d11148fe69b184e981164c8a71387c91dc64c5`;
the newer working-tree motion source has its own exact pin. The earlier accepted
correction and independent 58-check review are documented in
[motion-review](../motion-review/REVIEW.md). This packet contains **no accepted
reversal fix**.

## Finding and decision

With the actual imported 164-bone hero, an instantaneous aimed change from
6 m/s forward to 6 m/s backward causes the local heading to jump from zero to
pi while the gait remains `run`. The directional leg pass mirrors the stride
without a new gait transition. The supplied repeated cardinal-direction stress
case measured a **912.671 mm** maximum joint-origin step at 120 Hz.

That input is an adversarial discontinuity. Ordinary player movement applies
38 m/s² per-axis acceleration. A second fixture reconstructed that exact
`move_toward` velocity law, held each desired direction for 0.4 seconds and
retained fixed aimed facing. It did not execute CharacterBody collision or the
complete interactive player.

| Scratch prototype | Largest 120 Hz stress joint step | Decision |
| --- | ---: | --- |
| Bounded angular response | 409.311 mm | Rejected: substantial remaining jump |
| Blended planar stride components | 357.353 mm | Rejected: hard support-target relocation remains |
| Preserve reachable support anchors | 534.475 mm | Rejected: delayed unreachable-target replant is worse |
| Nearest reachable floor projection | 416.430 mm | Rejected: support-release jump, anchor slip and ordinary-case regression |

The projection prototype retained sub-2 mm numerical contact, but it moved the
contact target itself. The explicit measurement was **46.299 mm maximum anchor
drift in one 120 Hz frame**, and **211.694 mm accumulated drift** in that stress
take. These movements are not no-slip contact acceptance.

More decisively, the ordinary accelerated 120 Hz fixture worsened from
**161.919 mm** maximum joint step in the accepted source to **265.532 mm** in
the projection prototype. Both sources had zero anchor drift in that ordinary
fixture. Exact event clocks, finite transforms and numerical contact therefore
did not justify promotion.

No render or human-feel review was performed. The ordinary baseline measurement
is recorded as a remaining motion concern, not as evidence that current motion
meets the final graphics target. The next investigation should address support
release and inertial transitions with continuous rendered skin/contact review.

## Evidence and verification

- [summary.json](summary.json) contains source pins and all comparison metrics.
- [handoff.json](handoff.json) preserves the original scratch handoff and the
  hashes of every raw input/report.
- [reversal-study.zip](reversal-study.zip) stores 22 verified members: the pinned
  canonical source, rejected candidates, two probe scripts, player source,
  complete raw traces and logs. Its SHA-256 is
  `b455770a0a3762a06c5fb9492d8c721f68eacd1d382a18e006667ecbf3a4cf61`.
- The failed first projection script/log is preserved. A duplicate local
  variable caused a parse error; that owned process was terminated. Only the
  corrected scratch `vector-projection-r2` produced the reported measurements.

From the repository root, verify the archive and optional current source match:

```sh
python3 games/yuga-native/docs/evidence/visual-campaign/motion-reversal-review/verify.py --native games/yuga-native
```

The default invocation without `--native` verifies immutable archive integrity
even after later runtime work changes those source files.

To reproduce the final ordinary/stress comparison with Godot 4.6.3 and the
pinned native hero/library already imported, extract into a fresh directory:

```sh
reversal_dir="$(mktemp -d /tmp/yuga-reversal-review.XXXXXX)"
python3 -m zipfile -e games/yuga-native/docs/evidence/visual-campaign/motion-reversal-review/reversal-study.zip "$reversal_dir"
timeout 90s godot --headless --path games/yuga-native --script "$reversal_dir/probe-acceleration.gd" -- --candidate-script="$reversal_dir/rama_motion.vector-projection-r2.gd" --baseline-script="$reversal_dir/rama_motion.before.gd" --report="$reversal_dir/repeated-comparison.json"
```

This command reproduces rejected evidence; it does not replace the runtime
controller. The probe's `passed` field covers finite transforms and event-clock
equality only. The explicit joint-step and anchor-drift measurements determine
the rejection recorded above.
