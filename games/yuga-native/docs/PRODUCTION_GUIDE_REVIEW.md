# Independent production-guide review

Reviewed 17 October 2026 by the production/world reviewer. This review evaluates
whether the design and execution guide can direct implementation honestly and
in the right order. It does not accept the finished game's art, animation,
multiplayer service, performance or release.

**Review state: accepted as a production guide after revisions.** The master
design, roadmap and research decisions give implementation an actionable
contract. This accepts the guide; the complete native competitive game and its
visual-quality target remain open. Source changes are owned by their
implementation agents; this reviewer changes only this document.

## Baseline and evidence boundary

The shared branch was restored at `bd6740fbf36ad4c25920b53f2c73a9d5e98c86f9`
after a worker reset. The current native foundation is the offline Rama
training courtyard. The existing TypeScript/browser game supplies protocol 2,
3v3/480-second rules and fourteen hero kits; it is not the planned native
6v6/1,080-second game.

The restored production Rama is SHA-256
`6657f4bf2fdb41b1f8b1bbd64777b35b5b4acfe00b3e3e22e4bc793fd4df3e8e`;
the courtyard is
`1454e03627e9a7708557f64122cf8f170d0f8365256e69fa7689e94cd3585c33`.
The later uncommitted M2/M3 art corrections and their final render evidence were
lost. They must be recovered or reproduced and recaptured before being called
current or accepted. For example, the restored lighting still has sun shadow
bias `0.035`, not the later diagnostic correction. This review does not restore
that change or accept historical screenshots for different current bytes.

I inspected the freshly generated recovery reports and verified the report
hashes in [the recovery manifest](../tests/evidence/recovered-baseline/manifest.json):
18 native acceptance cases and seven projectile boundary cases pass. These
assertions concern the restored preview. The independent
[glTF format report](research/gltf-validator-restored-preview.json) has zero
errors for both restored assets, retaining one Rama warning. Those results do
not prove finished visual quality, convincing continuous motion, Windows
execution or physical-GPU performance.

The later network reconstruction now has fresh durable evidence in the
[network archive](../tests/evidence/native-network-final/manifest.json). I
verified all 33 archived file hashes/sizes and all 12 current source pins.
The report distinguishes 27 deterministic sampler checks, an actual
two-client headless match with reconnect, separate live sampling, recorded-data
impairment and six deliberately defective copies. This establishes tested
transport/interpolation prerequisites; no rendered native scene consumes the
libraries yet. The [transport](NATIVE_NETWORK_ADAPTER.md) and
[interpolation](NATIVE_INTERPOLATION.md) contracts make that limit explicit.

The [motion reconstruction](research/MOTION_RETARGET_IMPLEMENTATION.md) now
provides library `95ffda72…1554f` on the restored Rama. Its 12 bake and 35
reconstructed numerical checks are implementation-agent evidence, explicitly
not independent art approval. The actual carry review keeps it experimental:
open fingers and rigid arms remain. The all-sole diagnostic finds supported
samples near 5 mm but also a 221.906 mm maximum simultaneous foot clearance;
it does not prove planted-foot locking or plausible running flight. No runtime
promotion is claimed.

## Review findings and disposition

| Finding | Requested correction and owner | Disposition |
| --- | --- | --- |
| Earlier uncommitted art/network/motion evidence was described as a verified starting point. | Roadmap author must distinguish restored files, historical leads and newly reproduced evidence. Keep later art recovery open. | Corrected. Fresh network reconstruction now has a verified durable archive; it does not restore lost art or prove rendered online gameplay. Reconstructed motion still requires its own acceptance. |
| Duplicate-free 6v6 could pass before six distinct heroes existed. | Roadmap author must require six-hero FG07 acceptance before production draft/FG09 acceptance. | Corrected in milestone graph and task dependencies. Placeholder repetition remains suitable only for explicitly synthetic load tests. |
| Model approval depended on a later animation gate that itself depended on the model gate. | Roadmap author must separate model/rig/LOD acceptance from complete motion/kit acceptance. | Corrected: FG02-T05 accepts model/rig/LOD; FG03-T04 accepts continuous motion and combat feel. |
| Milestone overview omitted several complete-gate dependencies. | Roadmap author must add FG08→FG09, FG09→FG10 and FG10→FG11, while retaining specific cross-discipline task dependencies. | Corrected. Task DAG is explicitly authoritative for packet readiness; the overview is not a substitute. |
| Immediate queue included blocked tasks and absent prerequisites. | Roadmap author and validator owner must separate dependency-ready `next_packets` from the future horizon and reject unresolved ready-list dependencies. Completed evidence must pin hashes. | Corrected. Independently executed the validator and all 12 positive/negative ledger fixtures; dependency readiness, blocked packets and required completion hashes are enforced. |
| Research and production documents used different grip/foot acceptance tolerances. | Research desk must align or explicitly distinguish exploratory solver tests from production contact acceptance. | Corrected to grip ≤1.5 cm and planted-foot drift ≤2 cm during declared contact/support windows. The desk additionally proposes orientation error ≤5 degrees. These are targets, not achieved hero measurements. |
| Aim input has pitch, but the authority/client integration lacks a complete axis, remote-pitch and elevation contract. | Design and network/physics owners must define conversions and versioned entity semantics before elevated native gameplay. | Accepted as a specified implementation requirement. Master §9 contains the explicit conversion, inverse and elevation fixture; current runtime integration remains open. |
| Shared authority discarded the last projectile lifetime interval before collision queries, unlike the native final-interval sweep. | Research desk received the reviewer's bounded repair request and root assigned implementation ownership. | Resolved within scope. Reviewed the function-only repair and nine boundary tests; verified source/report/dependency hashes in the evidence manifest. Seven of nine failed before; nine of nine pass after; full suite 225/225 and typecheck exit 0 are recorded. Full collision parity remains open. |
| Master design and roadmap named different sixth beta heroes. | Root/design must align the six-hero content rollout with FG07's owned tasks. | Corrected to Rama, Hanuman, Sita, Ravana, Arjuna and Duryodhana. Ulupi remains a later roster task. |
| Three-hero slice acceptance ambiguously mentioned a 42-slot subset; simultaneous-core outcome needed an ordering rule. | Root/design must state nine selected-hero slots and evaluate both cores after one authority-tick damage batch. | Corrected. The new draw/outcome rule is explicitly a production migration, not current first-core-finish behavior. |

## Code-level contract that implementation must preserve

The relevant inspected sources are native `scripts/player.gd` and
`scripts/projectile.gd`, plus browser/shared `types.ts`, `map.ts`,
`simulation.ts` and server timing/capacity settings.

- Shared `aim(yaw,pitch)` uses
  `(sin(yaw) cos(pitch), sin(pitch), cos(yaw) cos(pitch))`: yaw zero faces +Z.
  Native camera/dash forward is `-pivot.global_basis.z`: native camera yaw zero
  faces −Z. The imported hero visual faces +Z. Raw yaw reuse is therefore not a
  valid integration contract. With the current pivot convention, the proposed
  bridge is `server_yaw = wrap(native_yaw + PI)` and
  `server_pitch = native_pitch`, without flipping world positions. Define the
  inverse explicitly and test cardinal headings, upward/downward aim and
  encode/decode round trips. Rig-local bone axes need their own calibration;
  this mapping is not yet integrated runtime behavior.
- `ArenaInput` already includes pitch, and projectiles carry `y` and `vy`.
  `Actor` has yaw but no continuous remote pitch; `CastState.pitch` does not
  substitute for an ordinary remote weapon/aim pose. Add only the necessary
  versioned fields, then test local and remote aim independently.
- `blocked(x,z)` and `lineClear()` use planar boxes, and gravity lands at y=0.
  `Vec`, structures, zones and event positions have no general elevation
  contract. Projectile collision already checks height and three-dimensional
  target distance. The current authority is mixed 2.5D; calling it wholly
  two-dimensional would hide both existing behavior and the remaining gaps.
- The shared ramp/stair/ledge/low-ceiling/stacked-deck fixture must give both
  clients and the authority the same units, axis convention, collider/support
  IDs, layers, map version and hash. A bridge and a road at the same x/z must
  remain independently traversable and independently hittable. A single
  heightfield cannot represent that requirement.
- Native projectile collision uses a swept ray; shared authority uses sampled
  radius checks. Repairing lifetime accounting does not make their hit volumes
  equivalent. Choose and version the production weapon contract; test cover,
  range, target volume and elevated shots before claiming parity.

The research desk's `NET-GEO-01` experiment is correctly placed before the
production multi-level city. It compares bounded extensions of the current
authority with a headless Godot authority using the same fixture and input
trace. No second authority should independently award damage, rewards or a
winner during that comparison.

The [projectile repair manifest](research/projectile-lifetime-evidence.json)
records the actual review→research→implementation request. I compared its
before-source hash to the restored Git blob and its after-source, unchanged
test, three result reports and dependency hashes to current files. The bounded
fix advances exactly `min(dt, remaining_life)` through the existing collision
loop before expiration. Tests cover exact/partial expiry, bounded range,
partitioned ticks, already-expired shots, cover, single gold credit and ordinary
three-dimensional travel. I reviewed the code and evidence; I did not rerun the
225-test game suite a second time after its recorded successful run.

## Quality and release gates

The roadmap correctly makes art, continuous animation, integrated matches,
platform execution and physical hardware separate acceptance layers.

I also inspected the existing published-preview
[training frame](evidence/window-release-079cc0a/release-training.png), not a
new render. Its repeated courtyard masses, broad empty paving, dark gallery
recesses and simple rear costume forms support keeping the production art
gate open. The image is useful baseline evidence; it cannot accept the missing
later corrections or establish continuous movement quality.

| Gate | Evidence needed to close it | What does not close it |
| --- | --- | --- |
| Hero/world quality | Same-source actual neutral/dusk/night views, portrait and normal gameplay distance, independent anatomy/material/silhouette/readability review; populated walkthroughs. | Concept paintings, polygon counts, asset import, lost earlier captures, an extra bloom/exposure setting. |
| Animation | Continuous locomotion/aim/fire/cast/jump/hit/death and transitions; socket/stance traces; release/impact/audio timing; cancel, retrigger, pause, death and respawn cases. | Static pose sheets, finite quaternions or a synthetic three-bone IK pass. |
| Native multiplayer | Two rendered clients first, then full 3v3 and 6v6 matches; shared hits/outcomes; reconnect/sequence/event deduplication; tested delay/jitter/loss behavior. | Headless transport lifecycle alone, local training or interpolation-only tests. |
| Scale and performance | Declared physical Windows/Linux hardware, source/replay/settings pins, p50/p95/p99 frame and server-step traces; retained memory and reconnect/capacity results. | Software Vulkan frame rate or a scheduled but unexecuted soak. |
| Public release | Exact frozen packages, real Windows/Linux execution, fresh external install→join→finish→rematch, hosted authority/TLS, support/rollback/recovery ownership. | A GitHub Pages page, downloadable ZIP or successful export alone. |

Initial 60 FPS/p95≤16.7 ms rendering, 20 Hz authority/p95≤25 ms work and
eight-hour soak requirements are explicitly proposed qualification gates.
They are not current measurements. Art defects and physical hardware gaps
must remain visible even when lower-level correctness tests pass.

## Research decision review

The [BRUTAL assessment](research/BRUTAL_STACK_DECISION.md) is an appropriately
bounded source/package decision. It distinguishes the public repository's
missing renderer/editor/build definitions from usable low-level components,
records its custom license, attributes the RimWorld/Waylith performance claim
to maintainers, and states that no C# build or BRUTAL render was executed.
Retaining the current Godot/Blender pipeline is justified until a representative
measured bottleneck supports a comparison. More downloads would not establish
finished character production.

The recreated package-audit and five-case synthetic IK reports now exist in
this worker. Their scopes remain narrow. The source documentation tag and
installed Godot binary have different recorded commit identities; execution
establishes the tested API behavior without pretending those source pins match.
The research desk correctly keeps the existing external Jolt extension's
maintenance status separate from testing the engine's built-in backend.

## Next owned work

The executable backlog, not this prose list, determines the current ready
queue. Baseline recovery FG00-T01 has fresh evidence; FG00-T02 design acceptance
is ready for the integrator to record against this review. Ready reconstruction
and registry packets can run in parallel within the available worker slots:

1. **Design/root:** record guide acceptance and recompute the ready queue.
   Establish versioned rules/map/replay contracts FG00-T04.
2. **Research-engineering:** retain the exact source/reuse registry and accepted
   projectile repair evidence; service the named elevation experiment.
3. **Animation/QA:** revise the reconstructed bow carry's hand grip, arm gesture
   and support/flight behavior, then inspect continuous actual movement. Its
   numerical passes do not close FG03-T01 or authorize runtime promotion.
4. **Network/QA:** retain the freshly verified hardened transport/interpolation
   baseline, then integrate rendered entities after version/elevation
   prerequisites. Its headless evidence does not close rendered integration.
5. **Character/world owners:** reconstruct lost bounded art corrections with
   actual source-pinned review. These packets do not close production hero or
   full-city gates.

After design/version prerequisites, entity/aim/elevation work becomes ready.
Physical-GPU qualification remains a separately blocked gate until declared
hardware and a representative trace fixture exist. Continue independent
content and correctness work while preserving that release limit.

## Final review record

Independently executed `tools/check-roadmap.py`: 16 milestones, 70 tasks and
eight linked evidence files passed the final pre-promotion structural gate.
Independently executed `tests/roadmap_cases.py`: all 12 fixtures passed,
including a positive hashed
completion that unlocks its dependent packet and negative cases for unmet
dependencies, blocked ready packets, absent hashes, cycles and stale evidence.
Verified the restored native source hashes and the final projectile repair
manifest as described above.

Read the complete master design, then inspected its final corrections. All
relative source/document links resolve. Crosschecked the fourteen current hero
definitions and GLBs, health/speed/nominal-DPS ranges, upgrade formulas,
minion/camp/map constants, current outcome code, and the coordinate/elevation
sources described above. The guide distinguishes current shared-kind abilities
from three timed signatures, projectile attacks from melee-looking weapons,
and native training reload/dash experiments from competitive rules. The six-hero
rollout, production objectives and contact thresholds now agree across documents.

The accepted document bytes are:

| Document | SHA-256 |
| --- | --- |
| `GAME_DESIGN_MASTER.md` | `bc51f4befc524ba9fecc44e45ee3b0faa4ae4508a64976980a73106245fba310` |
| `FULL_GAME_PRODUCTION_ROADMAP.md` | `97d92fcd0344ee4cdcb341a01e58538a4b257762504d8f28306ad6c91d1a7769` |

The backlog hash is deliberately not embedded here: recording this review as
design-task evidence changes the backlog. The integrator should record the
review's hash, update task readiness and rerun the validator. Future material
design changes require corresponding review and dependency updates.

**Final disposition: accept the production guide; continue implementation.**
The current art, experimental motion, rendered native multiplayer, vertical
authority, physical-GPU qualification, Windows execution and public service
gates remain open. Their absence is explicit production work, not an omitted
guide requirement or an accepted release.
