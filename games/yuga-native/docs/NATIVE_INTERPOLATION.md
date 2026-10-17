# Native actor snapshot interpolation

`scripts/arena_interpolator.gd` is a presentation-only `RefCounted` library for accepted protocol-2 authority snapshots. It produces actor poses with a configurable 100 ms render delay and bounded projection during brief loss. It has been tested with deterministic fixtures and real two-client recordings. No rendered native scene consumes it yet.

## Use and timing

Create one instance per active transport. Call `reset(expected_room)` before opening a new connection, including a reconnect to the same room. Feed accepted snapshots from `arena_client.snapshot_received` into `push_snapshot`. Call `sample` each presentation frame. Read gameplay state from the authority snapshot; sampling does not award damage, move server entities or predict ability outcomes.

```gdscript
var sampler = preload("res://scripts/arena_interpolator.gd").new()

# Before each new transport, including same-room reconnect:
sampler.reset(room_code)

# On accepted transport snapshots:
sampler.push_snapshot(snapshot)

# During presentation:
var frame: Dictionary = sampler.sample()
# The future scene integration maps frame.actors IDs to render nodes.
```

`configure(delay_seconds=0.1, extrapolation_seconds=0.1, teleport_distance=6.0, maximum_gap_seconds=0.5, maximum_speed=35.0)` returns a Godot `Error`. Delay accepts 0–1 second; extrapolation accepts 0–0.25 second. Set extrapolation to zero to hold exact authority poses after the last snapshot. `room_code()`, `buffered_snapshot_count()` and `settings()` expose the active configuration. Diagnostic counters track accepted/rejected/stale snapshots, local clock regressions and rejected computations.

`push_snapshot(snapshot, received_at_seconds=-1)` and `sample(at_seconds=-1)` normally use monotonic `Time.get_ticks_usec() / 1e6`. Optional timestamps support deterministic tests and recorded replay; callers must use one time basis. A rolling set of 32 receive-minus-server offsets estimates the earliest observed arrival. Clock offset correction is limited to five milliseconds per accepted packet, and local/render time never moves backward. This is a bounded arrival estimate, not measured network RTT or server clock synchronization.

The library retains at most 32 copied actor snapshots. Equal server time with a newer tick replaces that timestamp's entry. Duplicate/older ticks, decreasing server time, foreign rooms without reset and a finished-to-playing regression are rejected. The first pose is available immediately in `warming` mode. The finished snapshot freezes its exact final pose immediately.

## Pose rules

Positions interpolate linearly between authoritative endpoints; yaw follows the shortest angular arc. After the latest snapshot, velocity derived from the last pair may project for at most the configured extrapolation window, then holds. Default speed limit 35 m/s and projection limit 0.1 second cap continuous projected displacement at 3.5 m. Projection affects presentation only and never updates the server or source dictionaries.

Discontinuous transitions stay at the earlier pose until the later authority timestamp, then snap. These include displacement over six metres, derived speed over 35 m/s, a snapshot gap over 0.5 second, death/respawn, connection changes and actor identity/team/kind changes. Spawn, despawn and other discrete fields follow source timestamps. No interpolation bridges a teleport or a death transition.

The sampled frame includes `room`, `mode`, `phase`, `actors`, `render_time`, `source_time`, `source_tick`, `latest_tick` and `buffered_snapshots` when available. An empty frame has no actors. Every actor adds `presentation_mode`: `held`, `interpolated`, `extrapolated` or `projection_held`, with `presentation_discontinuity` when applicable. A monotonic render clock may advance beyond held source time; use the source time and actor flags when diagnosing a gap. Returned dictionaries are copies.

This library interpolates actor positions and yaw. Animation-state blending, local-camera response, server reconciliation, projectile paths, neutral units, VFX timing and map alignment require scene-level integration and separate evidence.

## Numerical review and regression protection

Independent review found that checking `is_finite` on JSON doubles alone was insufficient. Interpolating literal yaw `+1e308` to `-1e308` overflowed subtraction inside `lerp_angle`. An interval of `1e-50`, although positive as a JSON double, became zero during float32 vector division and yielded a nonfinite position even for a stationary pose.

The restored implementation bounds input yaw to ±`TAU` and normalizes it before storing or subtracting angles. It rejects positive absolute server times and positive nonterminal intervals below one microsecond. The continuity check independently enforces a finite, usable interval before deriving velocity. A tiny final remainder can freeze the exact final pose without division. Duration is bounded to 4,800 seconds and coordinates to ±10,000.

Every computed position and yaw must pass a final finite check before any pose field is changed. Failure keeps the prior valid authority pose, marks `presentation_discontinuity="nonfinite_computation"` and increments `rejected_computations`. This guards the output independently of input validation.

The original pre-replacement local probe and failing logs were lost when the execution environment was replaced. Current evidence is a fresh execution on reconstructed files. The test named `reconstructed_prior_formulas_reproduce_nan` recreates the unsafe expressions on Godot 4.6.3 and confirms both NaNs; it does not assert that the historical probe file survived. Corrected regression cases test literal inputs, a tiny delta at a normal timestamp, a terminal remainder, yaw normalization and atomic finite-output rejection.

## Four rounds and verification evidence

1. Audited the protocol, source coordinate conventions, snapshot timestamps and reconnect boundary.
2. Implemented bounded history, monotonic sampling, shortest yaw interpolation, discrete transitions and optional limited projection.
3. Added failure-capable deterministic cases and captured actual two-client authority snapshots. Independent numerical review supplied the two failing edge cases above.
4. Reconstructed after the workspace reset, fixed those cases, reran live transport plus recording/replay tests and checked six deliberately defective copies.

Run the complete isolated verification from the repository root:

```sh
python3 games/yuga-native/tools/check-native-arena.py --output /tmp/yuga-native-network-new-run
```

The output path must be new. See [transport setup](NATIVE_NETWORK_ADAPTER.md) for dependencies. The [durable aggregate report](../tests/evidence/native-network-final/integration-report.json) includes source hashes and all results; the [manifest](../tests/evidence/native-network-final/manifest.json) pins the preserved evidence bytes. The [deterministic report](../tests/evidence/native-network-final/deterministic-report.json) has 27 passing cases covering jitter, loss, out-of-order delivery, reconnect, teleport, death/respawn, spawn/despawn, empty rooms, terminal state, copies, bounds and numerical defects.

The two real native clients recorded 42 and 41 accepted snapshots in a separate four-second loopback match. Both sampled finite, monotonic actor frames while connected. Each recording subsequently passed 29 replay checks under original delivery and synthetic impairment. The impairment schedules delays of 0/140/20/90/0 ms cyclically, drops selected seventh packets except the final snapshot, adds delayed duplicates and sorts delivery order. These are replay impairments; they do not emulate operating-system packet loss on a live connection.

| Recording | Original replay | Impaired replay |
| --- | --- | --- |
| Host, 42 recorded snapshots | 42 accepted; 529 sampled frames; maximum projection 0.05993 m | 30 accepted; 11 stale; 546 frames; maximum projection 0.72001 m |
| Guest, 41 recorded snapshots | 41 accepted; 522 sampled frames; maximum projection 0.04320 m | 29 accepted; 11 stale; 522 frames; maximum projection 0.72001 m |

These sample counts measure headless test iterations, not rendered FPS. Full recordings and replay reports are archived under [the interpolation evidence directory](../tests/evidence/native-network-final/interpolation/).

Six isolated code variants deliberately removed bounded projection, shortest yaw, discrete teleport handling, yaw bounds, the interval epsilon or finite-output rejection. Each compiled and then failed its expected behavioral assertion. Their separate reports are preserved beside the aggregate report; the correct source remained unchanged throughout execution.

Final sampler SHA-256: `563b2097e5180cbba285e57bdebc3dafe07c919cabeec1d89d5a8d4b021e0619`.

Aggregate report SHA-256: `7a06cb1e770919e1323adc5ab4d1e67cb6b06e554cfe2db62510527041abe237`.

This establishes a tested interpolation prerequisite. Rendered multiplayer integration, perceptual camera smoothness, full-duration match soak, remote-network conditions and production graphics remain separate milestones.
