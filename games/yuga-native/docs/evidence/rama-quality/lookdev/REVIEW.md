# Lighting component checkpoint

Source base: `1ab1f5e330d256a6ffb6a5706a07f2ff8c3bbb0e`.

The current lighting scripts pass 108/108 new resource checks and 30/30 existing
world-lighting checks on Godot 4.6.3, with no parser/runtime errors. The same new
test against the saved pre-change scripts passes 48/108 and intentionally fails
60/108. Those baseline failures are retained in
`before-counterexample-complete.json`; they are not engine/import failures.

`summary.json` pins exact source/report hashes, commands, exit codes and scope.
The isolated baseline project copied the old lighting scripts, unchanged
`mythic_environment.gd`, water shader/include and the new test. No shared runtime
file was reverted, and no global import or render was executed.

The concrete repaired behaviour is that Settings/day/night application no longer
overwrites the existing neutral portrait fill with orange lantern settings.
Repeated apply/configure, finite/clamped phase, shadow controls, sky/fill and
practical budgets are covered. Scene clock pause/reset is owned by the existing
controller; this helper does not advance time and does not claim those gameplay
tests were repeated.

QA has reviewed the property-only test scope. **Actual final-art same-camera
A/B remains pending** and must inspect skin/eyes/hair, blue/gold materials,
contact shadows and effect readability at day/dusk/night. Until then the profile
is a candidate art calibration, not accepted visual improvement. Physical-GPU
performance, absolute radiance, listening and commercial-game parity are unrun.

Capture instructions and exact official-doc sources are in
`art/lookdev/README.md`.

Later actual R1 captures identified a floor self-shadow artifact. The finite
eight-image probe in `floor-artifact/probe-r1/` isolated the cause, and the
targeted policy now disables casting only on seven known flat ground meshes,
preserving their receipt of hero/building shadows. See `ground-fix-r3/summary.json`
for the current clean **146/146 + 30/30** resource/actual-scene checks. The
original 108-check checkpoint and rejected first render remain historical;
the corrected runtime still awaits root's source-matched R2 visual review.

The early lighting-properties and eight-image floor-probe logs include an
ObjectDB exit warning; they must not be described as warning-free. Verbose
diagnosis found retiring Dummy audio WAV/playback references. The current
**146/146** fixture now explicitly frees audio and allows mixer retirement;
`harness-cleanup-r3/` records zero warnings/errors in its verbose rerun. This
changes only the test/probe shutdown harness, with no product or authoritative
gameplay content change. The probe's cleanup was parse-checked without repeating
the eight-image render.
