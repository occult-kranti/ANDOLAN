# Research and implementation desk

This desk accepts specific bottlenecks from the game, engine, art and networking
agents, turns them into bounded experiments, and returns code or a testable
implementation decision. It is part of the current coordinated work session;
it is not a claim that agents run unattended after the session ends.

**Current production recommendation:** retain Godot, Blender, portable glTF and
the existing match authority while proving motion and vertical-world contracts.
The [BRUTAL decision](research/BRUTAL_STACK_DECISION.md) records actual source,
package and licensing findings. BRUTAL does not provide the missing renderer,
editor or hero-animation pipeline.

## Request queue

| ID / requester | Question | Artifact / required test | Current status |
| --- | --- | --- | --- |
| RE-01 · user / root | Does BRUTAL help us reach the visual/game target sooner? | Pinned primary-source review, two-package integrity/notice audit, independent stack countercheck; decision in `research/BRUTAL_STACK_DECISION.md`. | Source decision complete: keep production engine; defer custom-engine rewrite. Package audit regenerated and passed in the restored worker. No C# compile or BRUTAL rendering claim. |
| RE-02 · root → native engine | How should Rama's bow grip and future foot support use installed animation tools? | `tools/research/probe-skeleton-ik.gd`, `research/skeleton-ik-probe.json`; named-chain implementation ticket below. | Five synthetic two-bone cases passed in the first worker and were rerun after reset. Actual Rama integration remains open. |
| RE-03 · full-game roadmap + game-design lead | How can native ramps, stairs and bridges agree with the TypeScript authority? | Source contract audit and two-client comparison ticket below. | Current planar authority limitation confirmed. Prototype and migration decision are pending; no live authority changed. |
| RE-04 · root, from independent countercheck | Add independent glTF format validation without changing live dependency locks. | `tools/research/prepare-gltf-validator.py`, `tools/research/check-gltf.mjs`, `research/gltf-validator-restored-preview.json`. | Implemented and run on restored published assets: Rama 0 errors/1 warning; courtyard 0 errors/0 warnings. Valid and invalid synthetic fixtures confirmed exit-status behavior. |
| RE-05 · independent production-guide reviewer → root | Does the authority still drop the last projectile-lifetime interval? | `shared/simulation.ts` final-interval fix, `tests/projectile-lifetime.test.ts`, source-pinned before/after evidence below. | Reproduced 7 failures among 9 cases before; 9/9 after. Full YUGA suite 225/225; typecheck passed; independent code/test review accepted the bounded fix. |

After each handoff, the requesting agent records whether the result resolves its
question, needs one specific follow-up, or is deferred. A new request must name
a failing behavior or unmet requirement, the file owner, the intended result,
the evidence needed and the change boundary. “Research more tools” is not an
implementation ticket.

## Five-round request protocol

1. **Frame the request.** Name the exact source/asset hash and observable defect.
   Define one success condition and one counterexample. Assign an exclusive file
   owner; ask another agent for one independent check when it saves work.
2. **Check sources and reuse.** Read primary documentation/source and the relevant
   code and asset licenses separately. Record pins, exact reading scope, unknowns
   and inaccessible sources. A marketing claim remains attributed until tested.
3. **Build a bounded experiment.** Produce the smallest real implementation that
   answers the question. Keep external dependencies in isolated tooling until
   accepted. Record inputs and tool versions. One actual renderer runs at a time.
4. **Challenge the result.** Run a meaningful negative/boundary case, compare
   actual outputs and obtain an independent review. Do not turn successful
   import, file counts or a finite transform test into a visual-quality pass.
5. **Handoff and integrate.** Return artifact paths, reproduced commands, measured
   result, limitations and one next dependency. Integrator reviews the frozen
   revision. Do not create another tool study when the experiment already points
   to a concrete content or gameplay task.

These rounds are evidence stages, not a quota of cosmetic revisions. A rejected
motion or render returns to its implementation stage. No report calls a milestone
complete solely because several agents have written notes about it.

## RE-02: actionable bow-motion ticket

The installed binary reported Godot `4.6.3.stable.official.7d41c59c4`. A real
ClassDB inspection found `SkeletonModifier3D`, `IKModifier3D`, `TwoBoneIK3D`,
`FABRIK3D`, `CCDIK3D`, `LookAtModifier3D` and `AnimationNodeOneShot`. The synthetic
fixture then exercised reachable, out-of-plane, near-full-extension,
unreachable-without-stretch and zero-influence cases. It sampled poses during
`modification_processed`, while the modified result is available.

All five first-worker cases passed: reachable endpoint errors were below
0.001 m; both synthetic 1 m segments stayed within 0.0001 m of their lengths;
an unreachable target at 3 m reached 2 m without stretching; zero influence
restored the tip at its rest location. This establishes a usable API path,
not correct human elbow anatomy or Rama's bow contact.

After the worker reset, the probe was recreated and all five cases passed again.
The current [saved report](research/skeleton-ik-probe.json) includes the actual
binary and script SHA-256. Reproduce without loading the game scene:

```sh
godot --headless --path /tmp \
  --script /workspace/ANDOLAN/games/yuga-native/tools/research/probe-skeleton-ik.gd \
  -- --report=/workspace/ANDOLAN/games/yuga-native/docs/research/skeleton-ik-probe.json
```

Use the environment's writable task-local XDG directories as in native setup.

Primary documentation was read at the separately resolved upstream
[`4.6.3-stable` source pin `35e80b3a`](https://github.com/godotengine/godot/tree/35e80b3a8822a9df9be390814b62f44c0a9c69e8):

- [`SkeletonModifier3D.xml`](https://github.com/godotengine/godot/blob/35e80b3a8822a9df9be390814b62f44c0a9c69e8/doc/classes/SkeletonModifier3D.xml): a modifier runs after AnimationMixer; custom modifiers implement `_process_modification_with_delta`, may receive zero delta, and must not apply influence a second time.
- [`TwoBoneIK3D.xml`](https://github.com/godotengine/godot/blob/35e80b3a8822a9df9be390814b62f44c0a9c69e8/doc/classes/TwoBoneIK3D.xml): a pole target defines the joint plane; intervening bones become two virtual segments whose intermediate rotations are ignored by this solve.
- [`IKModifier3D.xml`](https://github.com/godotengine/godot/blob/35e80b3a8822a9df9be390814b62f44c0a9c69e8/doc/classes/IKModifier3D.xml): mutable axes use current pose each frame; cached rest axes ignore position changes before the modifier.
- [`two_bone_ik_3d.cpp`, lines 815–834](https://github.com/godotengine/godot/blob/35e80b3a8822a9df9be390814b62f44c0a9c69e8/scene/3d/two_bone_ik_3d.cpp#L815): the solver writes root and middle rotations; it does not independently align wrist orientation.

The live upstream tag pin differs from the installed binary's reported commit.
The source documentation is cited as its own retrieved snapshot; installed API
compatibility is established by execution, not by claiming those hashes match.
The older `SkeletonIK3D` class still exists but its source documentation marks it
deprecated; use the newer modifier path for new work.

**ENG-IK-01 — original Rama action and contact layer.** Owner: native motion
engineer; independent reviewer: animation QA/art director. Do not edit the
production rest pose or change the authoritative movement/damage rules.

1. Author original bow-carry, draw, release and recovery poses/clips on the
   existing rig. Source firearm/no-gun clips can inform lower-body timing;
   they cannot supply the bow's gesture and release intent automatically.
2. Use a locomotion layer and a filtered upper-body action layer with explicit
   entry, release, recovery and cancel transitions. Server-accepted shot timing
   controls gameplay; animation markers control presentation and must not award
   a second projectile or hit.
3. Inspect the actual chain before configuring IK. Original Rama GLB
   `a366dc927cb34208742e5617decefb2580e1cdab97f946ed4eb14687dc7abfbc`
   contains `upperarm01 → upperarm02 → lowerarm01 → lowerarm02 → wrist` on each
   side. Candidate solver joints are `upperarm01`, `lowerarm01`, `wrist`;
   `.02` bones require explicit twist/deformation review.
4. Add a TwoBoneIK3D child under Skeleton3D with one setting per desired arm,
   calibrated root/middle/end names and a non-collinear elbow pole. Keep the
   driving grip target outside the driven arm hierarchy. A bow parented to a
   wrist cannot simultaneously drive that same wrist without a dependency loop.
5. Preserve authored wrist/finger orientation, or apply a calibrated
   rotation-only modifier after the arm solve. Do not copy grip-target position
   into the wrist and stretch the chain. Blend influence down during release,
   casts and any action that intentionally breaks contact.
6. For a later foot-support pass, use stance metadata and ground queries,
   limited pelvis correction and an ankle target. Disable/reset locks on jump,
   death, teleport and respawn. This is not implemented by the arm fixture.

Proposed acceptance: continuous idle/run/strafe/draw/release/cast/jump/landing
recording; source/rest hashes preserved; no bone stretch; grip error at or below
1.5 cm and orientation error at or below 5 degrees during declared contact
windows; planted-foot drift at or below 2 cm during declared stance windows,
aligned with the canonical full-game production roadmap.
Those are proposed art/engineering gates, not results already achieved. Test
cancel/retrigger, pause/resume, death, missing target and near-full extension;
review elbows, wrists, bow string and clothing in the real renderer.

## RE-03: authority and traversable elevation

The inspected existing code is
[`shared/map.ts`](../../yuga/shared/map.ts),
[`shared/simulation.ts`](../../yuga/shared/simulation.ts),
[`shared/types.ts`](../../yuga/shared/types.ts) and
[`server/server.ts`](../../yuga/server/server.ts).
The important distinction is **not that aim pitch is wholly missing**:
`ArenaInput` already carries pitch, `aim()` uses it, and projectiles carry `vy`.
Actor snapshots expose yaw but not general remote aim pitch.

Confirmed gaps:

- `blocked(x,z)` expands 2D boxes; `lineClear()` samples the same x/z map.
- Ground aim intersects an implicit ground plane, and jump gravity clamps `y`
  to zero. There is no authoritative support-surface identity or stacked floor.
- `Vec` is x/z; zones, event positions, structures and pickups do not have a
  general elevation contract. Several ability/visibility distances are planar.
- A heightfield with one height per x/z cannot represent a bridge above a road
  that remains traversable underneath. Visual bridge geometry alone would
  disagree with movement, cover, zones and AI.

**NET-GEO-01 — shared collision fixture before an engine decision.** Keep the
current public room/identity/token/sequence behavior. Prototype behind an
explicit simulation/map version or separate test endpoint; do not silently send
new vertical semantics to old protocol-2 clients.

| Option | Feasible scope | Main cost / experiment trigger |
| --- | --- | --- |
| Extend TypeScript authority with exported analytic primitives | Small fixed world made of boxes, ramp planes/convex pieces and explicit layered supports. Reuses current simulation and room rules. | Capsule sweep, slope/step handling, ceiling contacts, edge transitions, projectile volumes and 3D ability visibility all need correct implementation. Matching mesh data does not make independently written solvers deterministic. |
| Headless Godot match authority | Can use the native collision scene and engine query/body APIs; existing headless physics fixtures already establish that rendering is not required for those queries. | Current TypeScript economy/abilities/AI/match logic must be ported or cleanly delegated without creating two authorities. Engine physics is not automatically cross-platform lockstep deterministic. |
| Shared collision module in both runtimes | Potential long-term way to reduce query divergence if the same implementation can be embedded. | ABI/WASM/native packaging and engine integration add work. No such module was built or benchmarked in this pass; do not select one from its feature list alone. |

Start with one exported collision artifact containing metre units, Y-up axes,
baked transforms, stable collider/support IDs, collision layers, shape data,
spawn anchors, navigation links, schema version and SHA-256. Keep decorative
meshes separate. The authoritative process loads that artifact; the client
verifies the same map hash. Navigation is another consumer of this contract,
not permission to move through collision geometry.

The smallest useful scene has a flat lane, a 20-degree ramp, a stair flight,
a ledge, a low ceiling and a 2.5 m bridge over an independently traversable road.
Numbers are proposed fixture dimensions, not accepted gameplay tuning. Run two
actual native clients against one authority and replay the same bounded inputs:

1. Walk up/down ramp and stairs; stop on their edges; jump into the low ceiling;
   leave the ledge and land. Assert finite positions, no wall/floor penetration,
   no extra jump while airborne, and preserved speed/step/slope rules.
2. Put clients above and below the same x/z on the bridge. Their support surfaces,
   projectile hits and occlusion must remain distinct. Fire up/down; a floor
   should block a shot when the declared weapon collision rule requires it.
3. Test dash/leap/pull and one area skill across floors with explicit 3D targeting
   rules. Do not retain planar distance or ground placement accidentally.
4. Disconnect/rejoin on an elevated support; expire old input; reject a wrong
   map hash and stale sequence. No floor-zero snap or client-awarded damage.
5. Run initially at zero added latency, then a controlled 100 ms round trip with
   20 ms jitter. Proposed presentation gate: p95 local correction below 10 cm
   outside intentional teleport/respawn transitions, with no persistent drift.

Record authoritative trajectories, support IDs, hit receipts, map hash, engine/
backend version, server-step time and client corrections. Compare the two
implementations using those same inputs. Only then choose whether the existing
authority can be extended economically or whether native match simulation
should become the new sole authority. Preserve existing game-rule regressions
and reject mixed-version clients explicitly. No migration or prototype run is
claimed by this design ticket.

## RE-04: adopted glTF format gate

The independent reviewer inspected
[`KhronosGroup/glTF-Validator@602c5404`](https://github.com/KhronosGroup/glTF-Validator/tree/602c54043ba66856b2e68c40fdf2bced975cdb8a),
Apache-2.0: full README/license/Node API and relevant animation, accessor,
skin and node issue sections. The executed package is separately pinned to
`gltf-validator@2.0.0-dev.3.10` with registry SHA-512 integrity. It has no runtime
dependencies. Acquisition verifies the archive before bounded extraction;
execution checks the pinned JavaScript/package hashes before loading it.

```sh
python3 games/yuga-native/tools/research/prepare-gltf-validator.py \
  --destination /workspace/tooling/research/gltf-validator/2.0.0-dev.3.10
node games/yuga-native/tools/research/check-gltf.mjs \
  --validator-dir /workspace/tooling/research/gltf-validator/2.0.0-dev.3.10 \
  --report games/yuga-native/docs/research/gltf-validator-restored-preview.json \
  --asset games/yuga-native/assets/heroes/rama-production.glb \
  --asset games/yuga-native/assets/environment/lanka_courtyard.glb
```

The fresh-worker report validates **restored published-preview bytes**, not the
later uncommitted assets lost during the worker reset:

| Asset SHA-256 | Errors | Warnings | Informational issues |
| --- | ---: | ---: | ---: |
| Rama `6657f4bf2fdb41b1f8b1bbd64777b35b5b4acfe00b3e3e22e4bc793fd4df3e8e` | 0 | 1 | 10 |
| Courtyard `1454e03627e9a7708557f64122cf8f170d0f8365256e69fa7689e94cd3585c33` | 0 | 0 | 16 |

Rama's retained warning is `NODE_SKINNED_MESH_NON_ROOT` at `/nodes/164`: parent
transforms do not affect a skinned mesh in the ordinary unskinned way. Review
the authored/imported transform contract before attempting a hierarchy fix.
The informational issues are unused tangents or UV data on untextured materials;
they suggest optional export cleanup, not automatic geometry deletion.

The wrapper fails on any validator error, truncated issue output, or source
mutation during validation. A valid empty GLB returned exit 0; an intentionally
invalid glTF 1.0 payload returned one error and exit 1. Full warning/info detail
is retained. No `package.json`, lockfile, runtime code, GLB, or shipped dependency
was modified by this gate. CI adoption is an integrator ticket; format success
does not certify convincing animation, rendering or a complete game.

## RE-05: implemented authority projectile correction

The production-guide reviewer found that the TypeScript authority still
subtracted a full simulation step from projectile life and discarded an expired
projectile before checking its final travel. For example, a shot moving at
54 m/s with 0.05 s left lost all of its remaining 2.7 m when the next step was
0.05 or 0.10 s. Native `projectile.gd` had already corrected this timing boundary.

The new authority implementation computes `travelTime = min(dt, life)`, uses
that duration for the existing sampled movement/collision loop, and retains a
projectile only if it has remaining life and has not hit. An already expired
projectile cannot move or deal damage. No weapon speed, radius, damage, world
bound, building rule, gold-credit rule or sampling-distance limit changed.

The new [public-simulation regression test](../../yuga/tests/projectile-lifetime.test.ts)
failed **7 of 9 cases before the fix** and passed **9 of 9 after**. It covers
exact and partial expiration, total range, partitioned ticks, already-expired
shots, building cover, final-segment gold interception without duplicate credit,
ordinary damage and three-dimensional velocity. The complete YUGA unit suite
then passed **225 of 225**, and `npm run yuga:typecheck` exited 0.

The independent reviewer inspected the function-only diff and all nine cases.
The [evidence manifest](research/projectile-lifetime-evidence.json) pins the
unchanged test, source before/after, full reports and dependency hashes. Source
SHA-256 changed from
`7237870be3f88537b67121f07211da0e61c05ef0205177d392fe4b4f9350b242`
to `e3fa766b06333eb00b5b9b8b03d938b22d5595bdef98b0ae07c0733d0e41a260`.
The test SHA-256 for both runs is
`c66ac90084dda5a77aa1cc73c04ae4c3839584fbca2d1ae410f9af4a2fd31ae4`.

```sh
node_modules/.bin/vitest run --config vitest.yuga.config.ts \
  games/yuga/tests/projectile-lifetime.test.ts
npm run yuga:typecheck
npm run yuga:test
```

This resolves a shared timing defect, **not full collision parity**. The native
projectile uses a zero-radius swept ray; the current authority uses discrete
samples with projectile/target radii and its own cover representation. Those
differences belong to the separate collision-authority milestone. The intended
end-of-lifetime range is now honored; human balance evaluation remains separate.

## Worker-reset evidence boundary

During this research session the executor disconnected and returned with a new
workspace. Root restored `game/yuga-native-production` at `bd6740f` centrally.
First-worker source observations remain attributed to their exact pins, while
newly executed reports identify their actual current input hashes. Rebuild lost
uncommitted art/motion from source before reusing its old acceptance claim.
Never label the restored v4 preview as the later uncommitted art revision.
