# Full native game target and current boundaries

The user has removed browser compatibility as a requirement and requests an
original Indian-mythology game at Deadlock/Overwatch visual quality. Their latest
direction is to create our own assets in the cloud. Community code and observed
mechanics inform development; commercial internals remain unverified. Delivering
a training scene does not close the target. “4D/5D” is interpreted here as
animated 3D, temporal effects and cinematic
presentation; it is not a separate rendering format.

| Requirement | Current evidence | Next gate |
| --- | --- | --- |
| Actual native reverse engineering | REA + Ghidra decompilation and function relationships verified on an original compiled fixture | Use original build-identified binaries for further verification; commercial-file analysis remains conditional on independently available inputs and does not block original development |
| Complete Deadlock/Overwatch understanding | Selected community-source studies and exact intake/tool audits | Per-build module, resource, animation, input, combat and networking coverage; retain unknowns and server-only gaps |
| Native production renderer | Godot 4.6.3 Forward+ project and original PBR courtyard | Inspect actual frames and motion; profile on a specified physical GPU before performance claims |
| Character quality comparable to the visual brief | Revised Rama costume/materials imported; 164 bones/nine inherited clips; actual studio frames expose remaining anatomy/cloth/pose gaps | Approve a new hero sculpt, retopology, texture/skin/hair treatment, weapon grip, deformation and animation set before expanding all fourteen |
| Full competitive game | Existing browser authority and protocol 2 remain available; native courtyard is offline | Implement native network adapter against the existing server; two-client input/state/reconnect agreement before public online claims |
| All fourteen hero kits | Browser implementation retains fourteen heroes/42 abilities | Native content bridge, telegraphs, counters and animation-to-authority timing; repeat native checks per hero |
| Three-lane city and jungle | Existing browser map/economy available; new scene is a training courtyard | Port collision and navigation with the server's map coordinates, wave/camp/core rules and clear objective routes |
| Production art and motion | Courtyard v2, day/night lighting and revised Rama; 18 native acceptance cases pass; staged frames are reviewable | Continuous motion/contact/grip/blending review, readable VFX and sound, LODs and texture budgets |
| Operated multiplayer | No public native arena service provisioned | Hosted TLS/WSS, real external-client tests, monitoring, capacity/recovery evidence and operational ownership |
| Full release | Native source/package pipeline is being validated | Signed/verified platform packages, actual Windows/Linux execution, hardware performance, accessibility and complete match journeys |

## Analysis sequence

1. Identify the exact game build and accessible files. Do not treat a community
   parser or Workshop compiler as the complete game implementation.
2. Keep source files read-only. Record module/resource hashes and the precise
   analysis question; start with inventory before expensive decompilation.
3. Run the relevant native or replay provider. Preserve errors, coverage,
   unresolved calls and optimization uncertainty. A successful command is not
   evidence of semantic equivalence.
4. Check recovered behavior against versioned observations where available.
   Client files cannot establish hidden server rules or current matchmaking.
5. Implement original YUGA systems and assets, then test them independently.
   Reverse engineering does not automatically produce production character art.

## Rendering and implementation order

First verify this native foundation's actual output and control flow. Then keep
one hero and a small playable lane as the quality target: readable silhouette,
grip/contact, layered animation, terrain/architecture detail, lighting and
effects under a measured frame budget. Expand the roster and three-lane map
after those standards are demonstrated. Integrate the existing authority using
protocol 2; keep transport, gameplay and presentation responsibilities explicit.

No score or percentage is assigned to “complete reverse engineering”: target
inputs are missing, and the extent of recoverable client/server behavior is not
yet known. No full-game, commercial-graphics, hardware-performance or hosted
multiplayer claim follows from this foundation.

## Parallel squads and review gates

Each squad owns distinct files and hands off a revision plus evidence. More
workers do not bypass dependencies: render the frozen asset, inspect it, then
test and package that exact revision. CPU renders are serialized on this worker.

| Squad | Completed in this pass | Next concrete delivery | Acceptance gate |
| --- | --- | --- | --- |
| Source research + REA fork scout | Pinned source/license reads for Godot examples, Dota tools and REA forks; no benefit demonstrated by the sampled forks | Native movement/animation adaptation design based on inspected TPS code and the current protocol-2 contract | Exact version, reusable scope, license and source-to-test mapping; no downloaded-tool-as-game claim |
| Hero artist + art director | Revised Rama materials/costume/grip, preserved rig/curves, actual multi-angle pose review | Sculpted face/shoulders, fitted cloth and an archery animation set with distinct idle/run/draw/release/recovery | Concept comparison, grip/contact and full-motion turntable review before roster expansion |
| World artist + environment builder | Courtyard paving, arch depth, dusk/night lighting and water shader | One detailed lane with readable landmarks, cover, collision and navigation | Walkable routes, camera clearance, silhouette contrast in both lighting states and measured rendering budget |
| Physics + QA | Final-lifetime projectile correction with three reproduced failures; 7 regression checks and 18 acceptance checks pass | Camera interpolation/teleport reset, then native client prediction/reconciliation against the existing server | Frame-step independence, collision/occlusion, reset continuity and two-client disagreement/reconnect tests |
| Integration + release | Native asset import, capture tools, package inspection and CI extensions | Native protocol-2 adapter; one complete match with bots before public service operation | Join/play/reconnect/end/rematch, authority agreement, Linux/Windows execution and hardware profiling |

The next wider-game stages remain: one production-quality hero/lane; two-client
authority integration; wave/camp/economy objectives; full three-lane match flow;
roster rollout with per-hero counters and animation events; external multiplayer
operations; platform/accessibility/performance release checks. Art and transport
research can proceed together, but the rejected visual target is not considered
resolved by adding more mechanics or decorative geometry.

Use [the reusable-systems source index](research/REUSABLE_GAME_SYSTEMS.md) and
[physics/graphics reading notes](research/PHYSICS_GRAPHICS_STUDY.md) as bounded
references. Dota replay parsers require actual compatible replays; they do not
supply the engine, production art or hidden server code. Existing Godot Jolt
integration should be evaluated before adding a redundant external extension.
