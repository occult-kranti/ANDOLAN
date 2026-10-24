# Bounded systems reuse: typed poses, bone damping and Valorant tooling

Reviewed 24 October 2026 against YUGA source `3497197745beb8e0fd22a9b67efe505700dec469`. This packet adds two MIT Godot component candidates and one authentic Valorant tooling source. Thirteen small primary files (licenses, documentation and selected code) are retained with immutable commits, exact URLs, byte counts and SHA-256 hashes in [source-manifest.json](source-manifest.json).

**Decision:** retain the current protocol-2 transport and guarded pose buffer. Reuse only an explicitly typed quaternion helper in a scratch presentation experiment; reject wholesale netfox adoption for this slice. Bone damping is a second bounded candidate before foot/string constraints, not a reason to replace Rama's 164-bone/23-clip animation system. Valorant endpoint tooling supplies schema examples, not gameplay/animation/server code.

## Inventory checked before new retrieval

The existing [map/code reuse packet](../../map-code-reuse-oct23/README.md), [systems study](../../REUSABLE_GAME_SYSTEMS.md), [research brief](../../RESEARCH_BRIEF.md) and their REA inventory were checked. They already cover Godot TPS/demo projects/Jolt, Clarity/OpenDota, Source SDK, ioquake3/OpenArena, REA/Ghidra and commercial-format tooling. The existing REA source pin is `300905c11be1c25b98fda9e2b71dfa899fc2831c`; ten sampled forks previously supplied no relevant adoption delta. This packet neither repeats that fork census nor claims to have recovered commercial game source.

## New source decisions

| Source | Pin and rights | Actual component examined | Adoption boundary / counterexample |
| --- | --- | --- | --- |
| [foxssake/netfox](https://github.com/foxssake/netfox/tree/cf5189d18e98766022c8c1c5e637a6a30c4c3703) | `cf5189d18e98766022c8c1c5e637a6a30c4c3703`, MIT, Copyright 2023 Gálffy Tamás | Complete `addons/netfox/interpolators.gd` and `tick-interpolator.gd`; README/license | Exact typed helper ran in Godot 4.6.3. Quaternion/vector operations work, but generic scalar yaw is wrong across ±179°, an unsupported dictionary fallback has an invalid callable on this runtime, and the fraction is not clamped. `TickInterpolator` depends on `InterpolationServer`, `_PropertyPool`, `PropertyEntry` and editor helpers; it is not a single-file replacement. README separately licenses bundled assets. |
| [GuilhermeGSousa/godot-motion-matching](https://github.com/GuilhermeGSousa/godot-motion-matching/tree/5fe36ad06fbd203df52e3ecb8e5c01b0363f81d5) | `5fe36ad06fbd203df52e3ecb8e5c01b0363f81d5`, MIT, Copyright 2024 Guilherme Sousa | Complete damping modifier and XML interface; `spring.hpp` lines 1–240; README/license | The modifier is already a `SkeletonModifier3D`, matching Rama's existing extension point. Its all-nonroot-bone loop would also damp support feet, wrists and string, potentially undoing current constraints. The README targets Godot 4.4, requires root motion and a foot-level root for the full motion-matching system, and names external O3DE demo data. No extension build, compatibility claim, motion database or demo-art import. |
| [techchrism/valorant-api-docs](https://github.com/techchrism/valorant-api-docs/tree/f473c59ff47d66b4a2cd1d935acbb137dfb702c6) | `f473c59ff47d66b4a2cd1d935acbb137dfb702c6`, MIT, Copyright 2021 Techdoodle | README/license; complete current `valorant-api-types/src/endpoints/currentgame/CurrentGameMatch.ts`; older generated markdown retained as a stale-source counterexample | Authentic community documentation/types for endpoints the Valorant client uses. Current source has a Zod response schema, match/map/mode IDs, reconnectability, connections and player metadata. It has no movement tick, position, animation or hit simulation in this inspected endpoint. It requires Riot token/entitlement/platform/version for requests. No endpoint called and no account/client data acquired. MIT tool rights do not transfer Riot maps, models, audio, client binaries or server implementation. |

The retained old Valorant markdown explicitly says it is deprecated. Its two listed headers omit requirements represented in the current TypeScript source. Use the pinned TypeScript as the evidence for current source structure; neither file proves that the live service still matches it. The type itself retains `State: IN_PROGRESS // TODO verify`.

## Actual execution and failures

[experiment-result.json](experiment-result.json) records **6/6 passed assertions** in official Godot 4.6.3. These are two valid-operation checks and four counterexample checks, not six production features. [netfox_cases.gd](netfox_cases.gd) runs the unchanged MIT source with a byte-for-byte copy of YUGA's current `arena_interpolator.gd`:

- Vector interpolation preserves the Y component; quaternion slerp uses the short path across ±179°.
- Float interpolation returns 0° for the same yaw pair, proving that generic float dispatch cannot replace `lerp_angle`.
- The unsupported dictionary fallback's callable is invalid on this runtime. An initial attempt to invoke it raised a script error; [failed-first-run.txt](failed-first-run.txt) retains the observed output and exit 130 after stopping the stalled harness. The final harness checks callable validity; upstream code was not patched.
- A fraction of 2 extrapolates without clamping. A 20 m change is blended halfway by the upstream helper while the existing YUGA `_discontinuity()` correctly returns `teleport`.

The likely fallback mechanism is visible in the source: `DEFAULT_INTERPOLATOR` captures `default_apply` before the latter's static assignment. The failure is an observation on this engine, not a claim about all Godot versions or normal netfox usage. No bug report was sent.

Reproduction uses a fresh scratch Godot project containing the retained upstream `interpolators.gd`, unchanged current `scripts/arena_interpolator.gd`, and the retained harness. [experiment-preparation.json](experiment-preparation.json) binds these exact bytes and the actual scratch path. Executed command:

```sh
timeout 25s godot --headless --path /tmp/yuga-reuse-systems-tlv08ns3 --script res://netfox_cases.gd
```

Final command exited 0 with `{"checks":6,"passed":true}`. No renderer, online match, network-delay simulation, motion-matching extension or character asset was run. The current [native authority pilot](../../../../tools/arena-bridge-pilot/README.md) remains separate evidence.

## One concrete next experiment

**Adopt/reject experiment: remote aim orientation without replacing the buffer.** In a fresh scratch copy of `tools/arena-bridge-pilot`, retain its unchanged `scripts/arena_client.gd`, protocol-2 Node transport and authority. Continue feeding received snapshots through `arena_interpolator.gd.push_snapshot()` and its existing time/identity/death/speed guards. Add one presentation-only aim orientation, using the retained MIT helper's explicitly selected quaternion callable on normalized quaternions made from the pilot actor's yaw and positive-up pitch. Define that axis conversion against the pilot's metres/+Y-up/+Z-forward contract before interpolation. Use actor `bridgeEpoch`/snapshot epoch as a discontinuity boundary; validate finite pitch in the existing ±1.35 input range and never interpolate across epochs. Do not interpolate the entire actor dictionary or use scalar interpolation for yaw.

Test the pilot's high/low aim stage, a ±179° yaw seam, malformed/nonfinite pitch, a staged teleport, reordered snapshots and a delayed packet spanning an epoch. Adopt only if accepted actor positions/acks/authority output remain byte-equivalent, invalid input never reaches the helper, epoch changes hold or snap, and the presentation direction crosses the yaw seam through 180°. Run the two real native clients, then capture a rendered aim-marker pair before calling it a visible improvement. If that direction merely duplicates existing presentation, reject it and retain the present buffer. This is a small MIT component reuse, with no alternate transport, rollback framework or match engine.

A later animation experiment can adapt only the MIT spring update into a scratch copy of `rama_motion.gd.evaluate_pose()`, before `_apply_contact()` and bowstring attachment, restricted to a named torso/shoulder mask. Keep `update_motion(delta, state)`, `request_action`/`release_action`/`cancel_action` event timing and the 23-clip library. Compare existing cast-entry displacement, maximum foot/string error and release count against the same fixed clips; reset spring state on cancel/teleport/death. Reject if contact or release timing regresses. Full motion matching first needs a verified root-motion corpus, which this study did not establish.

## Handoff

Goal: systems reuse advisory for native YUGA. Files changed: this directory only. Source baseline: `3497197745beb8e0fd22a9b67efe505700dec469`. Validation: immutable source retrieval, retained license inspection, six exact-source Godot checks with a retained failed run, local helper/source hash comparison. Actual visuals/input reviewed: none; synthetic headless pose values only. Remaining owner: native networking worker for the bounded aim-orientation experiment; motion worker for any later spring candidate. Neither candidate is integrated into canonical gameplay and no production gate is closed here.
