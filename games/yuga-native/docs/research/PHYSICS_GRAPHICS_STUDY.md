# Native physics and graphics: source-led implementation study

This pass read four specific documents/source files from three upstream projects.
The sources inform an original Godot implementation; they are not evidence that
Deadlock or Overwatch binaries, assets, animation systems, or source code were
reconstructed. This is a bounded engineering study, not an all-books survey.

## Sources actually inspected

Each linked commit was resolved from the upstream repository, then its raw file
was fetched again and byte-compared with the document that was read. These are
upstream source snapshots; the native runtime tested here is Godot 4.6.3.

| Source and exact scope read | Concrete finding | Application here |
| --- | --- | --- |
| [Godot: physics interpolation introduction](https://github.com/godotengine/godot-docs/blob/5b865984bb5f52d526f1185685c6f1be4a08ac02/tutorials/physics/interpolation/physics_interpolation_introduction.rst). Entire introduction: physics ticks vs rendered frames, fixed tick rate, interpolation fraction, one-tick delay, prediction errors, multiplayer qualification. | Fixed simulation ticks and rendered frames have different jobs. Interpolation smooths presentation but introduces delay; extrapolation can display impossible positions at collisions. | Preserve the existing 60 Hz simulation. Do not change movement/collision timing to compensate for software-rendered frame rate. Plan a separate camera/interpolation experiment with explicit reset/teleport and collision gates. No interpolation switch was enabled by this pass. |
| [Godot: ray-casting](https://github.com/godotengine/godot-docs/blob/5b865984bb5f52d526f1185685c6f1be4a08ac02/tutorials/physics/ray-casting.rst). Entire document, especially Accessing space, Raycast query, Collision exceptions, Collision Mask, and screen-to-world projection. | Query physics space during `_physics_process`; supply global endpoints, collision masks and exclusions deliberately. A ray returns the first eligible hit along its segment. | Keep the existing swept segment against world/target masks and shooter RID exclusion. Repair only the segment's lifetime boundary. New regression queries execute in a real physics callback against isolated Godot collision bodies. |
| [LearnOpenGL: PBR lighting fragment shader](https://github.com/JoeyDeVries/LearnOpenGL/blob/a545a703f95893258d16dbe32f5ccbb6400fd213/src/6.pbr/1.1.lighting/1.1.pbr.fs). Entire 4,038-byte shader: GGX distribution, Schlick geometry/Fresnel, metalness interpolation, diffuse energy conservation, inverse-square attenuation, tone mapping and gamma conversion. | Metalness changes the balance between diffuse and specular response; roughness changes the microfacet distribution. Brightness alone does not produce convincing material separation. The example's simple ambient term is explicitly transitional to environment lighting. | Retain the existing Godot PBR pipeline and separate stone/cloth from brass. The production water remains dielectric. Next validation should inspect albedo/normal/roughness imports and material response under the same controlled light, rather than adding a second tone-map/gamma transform in a custom shader. No shader code was copied in this pass. |
| [Jolt: `PhysicsSystem.h`](https://github.com/jrouwe/JoltPhysics/blob/6d7ba5d8af603648ccc0c639f54ad282d185e1b6/Jolt/Physics/PhysicsSystem.h). Selected API documentation: `Init` capacity/filter contract, `OptimizeBroadPhase`, `Update` and its collision substeps, state recording, linear-cast debug option, body/constraint statistics. | Collision capacity and filter configuration are correctness constraints. Update divides an explicit duration into collision/integration steps; broadphase maintenance should not be redundantly forced every frame. A backend offers mechanisms, not automatic game/network determinism. | Keep explicit swept projectile collision instead of assuming a physics engine upgrade solves weapon reliability. Before any backend change or crowd scale-up, record active-body/pair/contact limits and replay the same collision fixtures. Jolt was studied as an open-source implementation resource; this study did not install it or establish which backend the current project selects. |

### Retrieval fingerprints

| Inspected file | Bytes | SHA-256 |
| --- | ---: | --- |
| Godot interpolation introduction | 11,411 | `a9af4172edd092f884cebf46f85603f1122d09a33e8ca013d647771ad66943eb` |
| Godot ray-casting | 10,675 | `85fd673b0308dc52f8139a63614b254b8c453af5ca1071ec82f2300c7b030799` |
| LearnOpenGL PBR fragment shader | 4,038 | `be035d242066eb7a72336bd5e6887b33df70286c33b993d1163fe7a8d5c599ea` |
| Jolt PhysicsSystem header | 25,971 | `fcb6f9500c59535c86d8823c4b9f31863e272df5d4646e33e4d745d171986bd4` |

The upstream bytes were stored temporarily under `/tmp/yuga-physics-sources/`
for inspection and pin verification. They were not vendored into the game. The
implementation change below is original code; linking a source does not grant
permission to redistribute all of its prose, code or assets.

The canonical [Gaffer on Games: Fix Your Timestep!](https://gafferongames.com/post/fix_your_timestep/)
request was blocked by the managed HTTPS proxy with HTTP 403. A guessed GitHub
mirror path returned 404. That article was **not read in this pass** and is not
used as evidence for the implementation. Godot's accessible primary documentation
provided the timing source. No network bypass was attempted.

## One implemented reliability improvement

`scripts/projectile.gd` previously subtracted a full tick from remaining lifetime
and deleted the projectile before checking collision when the result reached zero.
That omitted the last valid segment of its trajectory. A projectile with 0.05 s
left at 54 m/s should still travel and collide along 2.7 m, even when the supplied
tick is 0.10 s. The old code travelled zero metres in that case.

The repair computes `travel_delta = min(delta, life)`, sweeps that bounded segment,
and expires after resolving it. An already expired projectile still has no travel
or damage. Speed, configured lifetime, damage, target/world masks, shooter
exclusions, rendering, input, abilities and other combat rules are unchanged.
For a unit direction, the intended maximum path remains `speed × lifetime`.

This deliberately does not introduce ballistic gravity, a larger hit volume,
penetration, aim assistance, lag compensation or a new physics backend.

## Reproducible regression evidence

Run from the repository root after the normal Godot import:

```sh
godot --headless --path games/yuga-native --script res://tests/projectile_cases.gd -- --report=/tmp/yuga-projectile-cases.json
```

In this managed environment, use the writable XDG directories from the native
setup instructions. The runner builds isolated labelled fixtures, injects explicit
physics deltas, and performs real Godot ray queries inside a physics callback.
It is deterministic scripted QA, not a rendered frame-rate measurement, human
input recording, online session or commercial-game comparison.

| Check | Before repair | After repair |
| --- | --- | --- |
| Target in last partial lifetime receives exactly one hit | Failed: 0 hits | Passed: 1 hit at 2.29 m surface |
| Expiry reaches 2.7 m and cannot hit a surface at 2.71 m | Failed: 0 m travelled | Passed: 2.70000005 m, no hit |
| 600 m/s sweep sees a 2 cm world wall before a farther target | Passed | Passed |
| Shooter RID exclusion still allows the intended target hit | Passed | Passed |
| Five 0.01 s steps preserve the same 2.7 m lifetime range | Failed: 2.15999985 m | Passed: 2.69999981 m |
| Already expired projectile causes no movement or damage | Passed | Passed |
| Runtime source unchanged during scenarios | Passed | Passed |

Godot 4.6.3 completed the final run with **7/7 checks passed**, exit code 0. The
pre-fix run failed the three targeted lifetime checks and exited 1; those assertions
were kept unchanged. Reports were written to `/tmp/yuga-projectile-before.json`
and `/tmp/yuga-projectile-after.json` for the acceptance owner to archive.

Tested runtime SHA-256:
`39b651bf014b91352e3cd62d15ec22966e5de4707a6dd1b9bcfb2dddd438695a`.
The full native acceptance run is owned separately and must use this final source.

## Next reading and implementation gates

1. **Camera and motion:** read the Godot CharacterBody3D, SpringArm3D and advanced
   interpolation contracts, then compare fixed camera paths at 30/60/120 rendered
   frames with fixed 60 Hz simulation. Gate on wall avoidance, aiming latency and
   teleport/reset behavior before enabling interpolation globally.
2. **Projectile volume and spawn:** test muzzle origins at/inside thin walls,
   moving targets and large world coordinates. The current ray is a zero-radius
   segment even though the arrow mesh has thickness; choosing a shape cast would
   be an explicit combat-design change, not a hidden reliability fix.
3. **Materials and light:** use *Physically Based Rendering: From Theory to
   Implementation*, fourth edition, reflection/material chapters, and *Real-Time
   Rendering*, fourth edition, material/shading chapters as a planned reading
   sequence. Those book chapters were not read in this pass. First implement a
   controlled material turntable and verify texture colour-space and tangent data.
4. **Scale and backend selection:** profile Godot's existing backend on a fixed
   reproducible scene before evaluating Jolt. Preserve the same fixture geometry,
   masks and scenario assertions; measure CPU simulation cost separately from GPU
   rendering and software-rendered cloud capture speed.
5. **Online authority:** specify tick ownership, snapshots, interpolation buffer,
   reconciliation and accepted shot time before adding client prediction. Visual
   interpolation, rigid-body replay and fair network hit registration are separate
   contracts and require separate tests.

These resources support a native production workflow, but no small code change,
engine selection or reading list establishes Deadlock/Overwatch graphics parity.
That target still needs authored hero topology and rigging, convincing animation,
environment composition, material discipline, lighting, effects and measured
performance on representative hardware.
