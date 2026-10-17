# Three-dimensional physics authority: bounded experiment

MYTH-07 / supporting FG05-T02 packet, 17 October 2026. **Use one headless Godot physics authority for the next native online prototype.** Keep the TypeScript implementation here as a comparison oracle for the declared convex queries. Do not run the two solvers as interchangeable authoritative simulations or migrate the browser's protocol 2 in place.

This is an executed architecture experiment, not the completed production collision/server milestone. The current native game remains offline. No player/world/browser runtime, live protocol, production contract or map was changed by this packet.

## What was built and run

- `assets/contracts/physics-fixture-v1.json`: versioned, original collision fixture; metres, +Y up, +Z shared yaw zero, positive pitch up, feet-origin actor positions; world/actor/target bits 1/2/4. Fifteen solid bodies and one excluded visual-only canopy represent a bridge over road, two stacked decks, a convex ramp, four stairs, a ledge, low ceiling, elevated actors and two target heights. Stable collider and support IDs are separate from visual geometry.
- `tools/physics/reference.ts`: original TypeScript convex half-space rays and swept axis-aligned box queries using separating axes, plus explicit overlap queries. It does **not** import or replace `games/yuga/shared/simulation.ts`. The existing browser movement uses `blocked(x,z)` and cannot be relabelled as this multilevel solver.
- `tests/physics_authority_cases.gd`: independently builds actual Godot StaticBody3D/BoxShape3D/ConvexPolygonShape3D collision objects from the same fixture. It executes `intersect_ray`, `intersect_shape` and `cast_motion` in a headless world after physics synchronization.
- `tools/physics/compare.py`: verifies fixture and implementation SHA-256 pins, identities, rays, overlap sets, conservative sweep brackets and paired command samples. Differences are retained as structured records, not rounded into equality.
- `tools/physics/run.py`: runs the owner tests, strict TypeScript check, both implementations and comparison in a fresh evidence directory. No editor import or renderer is needed.

The paired input stream drives two **logical actors** for 240 ticks at 60 Hz: one below the bridge and one above at the same x/z. Each command checks initial overlap, applies a bounded swept translation, then probes support. An actor already embedded in a solid receives `invalid_initial_overlap`, zero movement and the collider IDs; the valid peer can continue. Stationary actors retain support without issuing a zero-length sweep. There are no sockets, gravity, step-up, sliding, capsule movement, prediction or reconciliation in this harness.

The fixture has 34 static queries and 480 actor samples. The final normal stream performs 1,440 shape/ray calls; together there are **1,474 queries per implementation**. Additional negative Godot runs test initial overlap and stationary input. Owner acceptance is **48 TypeScript tests, strict typecheck, 24 Godot checks and 1,586 comparison checks**. The comparison passing means the declared experiment ran, agreed within its stated checks and recorded the known divergences. Its report explicitly sets `cross_engine_equivalence: false`.

## Measured behavior and consequences

| Observation | Evidence | Consequence |
| --- | --- | --- |
| Same x/z has road, lower deck and upper deck support | Actual downward rays return y = 0, 3.2 and 6.2 m with distinct collider IDs | A single height value per x/z cannot represent the map. Carry support identity and elevation explicitly. |
| Rays and elevated aim agree on the bounded fixture | Maximum ray hit-position difference about 0.000000405 m; aim-direction difference about 0.00000000583 | The shared yaw/pitch convention works for these inputs. Protocol-2 remote pitch remains unavailable; do not infer it from the local camera. |
| Godot swept motion is conservative, not identical to exact TS SAT | Four sweeps differ beyond the declared position/fraction threshold; up to 7.5 cm on a deliberately extreme 100 m sweep. The exact TS contact lies within each Godot safe/unsafe interval. | Shared gameplay should use one physics authority. These are query-level differences, not evidence that the game normally moves 100 m per tick. |
| Float accumulation can change support selection | At tick 219, TS z = 7.999999999999978 m is just inside the bridge; Godot z = 8.00001049041748 m is just outside. One sample chooses bridge versus road. Rays 1 mm inside/outside agree. | Tiny position error can produce a large support-height difference. Support IDs, discontinuities and authoritative correction need tests, not a loose position-only parity claim. |
| `cast_motion` ignores preexisting overlap | A body embedded in the ceiling receives fraction 1 from the raw sweep. The separate overlap query detects it. | A clear sweep is not proof of a valid start. The paired harness now rejects that input before movement. Spawn/teleport/penetration recovery still needs production design. |
| Ramp and stairs block a horizontal box sweep | The reference does not invent uphill sliding or step-up | Choose/test the actual character shape, floor snap, maximum slope, stair height and flight/grapple collision policy before migration. |
| Visual canopy and collision masks behave separately | Canopy is excluded; layer 1 ignores targets; layer 2 distinguishes actor height; layer 4 hits the intended target | Map export must preserve collision layers and visual-only tags rather than treating every mesh as gameplay authority. |

The fixture actor is an axis-aligned **box**, not the production character controller/capsule. Convexes are closed, planar-face hulls; the reference rejects degenerate/open/nonplanar geometry and unsupported shapes. Dynamic-body contacts, angular sweeps, meshes, moving platforms, CCD, concave geometry, friction and arbitrary rotations remain outside this experiment. Imported assets and the current playable map were not collision-certified here.

The recorded engine is Godot 4.6.3 standard. The project reports physics setting `DEFAULT`; this harness does not claim to have identified the resolved internal backend. Before a server rollout, select and pin the backend explicitly with the engine and collision artifact. Profile records contain observed single-process query wall time only, including harness allocations. They are not GPU frame rate, online server capacity, latency or a cross-language benchmark.

## Migration sequence and acceptance gates

1. Add a **new experimental profile**, with an explicitly selected Godot backend/version, map collision digest, actor shape/controller parameters, rule/content versions and authority tick. Do not edit the existing browser-p2 profile to imply compatibility. The existing `native-contracts-v1.json` production selection remains pending until this proposal is adopted through that versioned change.
2. Export stable collision/support IDs, transforms, layers, closed hulls and visual-only tags from the real map. Hash the collision artifact itself. Expand fixtures to rotated geometry, changing platforms, steep slopes, narrow ledges, ceiling transitions, spawn volumes and flight/grapple entry/cancellation.
3. Version the entity schema for authoritative velocity, movement mode, nullable support ID/generation and controller state. Keep feet-origin position, required remote pitch, input acknowledgement and monotonic discontinuity. Current v1 pose-only entity presentation cannot silently supply these missing fields.
4. Run authenticated inputs on the server; clients submit bounded commands, never authoritative position, support, hits or rewards. Use the existing room/epoch/generation guards. Cold reconnect/bootstrap, contact recovery, prediction/reconciliation and replay tick clocks need explicit implementations.
5. Execute **two actual native clients** against that authority. Verify bridge/road separation, stairs/slope policy, remote pitch/projectile hits and spawn/teleport recovery with latency, jitter, loss, reorder, reconnect and corrections. Compare accepted input IDs and authority outcomes, not just rendered positions.
6. Measure engine tick time, allocations, bandwidth and authoritative state under the intended roster/minion population. Run sustained tests and real hardware/render checks separately. Only then promote the profile and close the parent roadmap gates.

## Reproduction and retained review

From repository root, with locked Node dependencies and Godot 4.6.3 on PATH:

```sh
python3 games/yuga-native/tools/physics/run.py \
  --output /tmp/yuga-physics-new-review
```

The output directory must not exist. `receipt.json` pins inputs and source files; numbered logs retain exact commands/results. `typescript.json`, `godot.json` and `comparison.json` contain raw samples, observed timings and all divergences. A report from changed fixture/implementation bytes is rejected by the comparator.

Working final evidence is `/workspace/scratch/yuga-physics-authority/r6-final/`. Earlier runs stay under the same parent. R1 retained an invalid ceiling clearance and a typed JSON dictionary comparison mistake. R2 discovered the real bridge-edge support switch; the final comparator reports it explicitly and limits that exception to the identified submillimetre edge case. No query tolerance was enlarged to hide it.

Independent bridge-owner review confirmed the aim convention and found the missing initial-overlap guard in the paired harness. The original and closure probes are `/workspace/scratch/yuga-bridge/physics-independent-probe.json` and `physics-independent-probe-r2.json`; both remain preserved. That feedback produced matching TS/Godot guards and negative tests. A separate cross-review found and corrected a pitched-projectile visualization defect in the entity bridge; its own owner records that proof.

Root owns durable evidence archival, roadmap status, integration and release. This packet owns a reproducible collision experiment and a supported next-prototype decision; it does not close FG05-T02's complete shared-world/network/controller acceptance.
