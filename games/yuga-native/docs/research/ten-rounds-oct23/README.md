# Ten reuse-first production stages — 23 October

Continue from `067ad5d5e12b4de71d75b658aa511beb8f175fc9` on
`game/yuga-native-production`. This is a bounded art/engineering campaign with
six concurrent specialists, followed by integration and publication. The
[machine-readable ledger](rounds.json) records each stage's actual outcome.
It is not ten completed game-development rounds or sixty separate assignments.

## Reuse contracts

Keep the existing Godot game, player, army, authority, traversal, UI and input
systems. Reuse the existing Rama skeleton and nine actions, Blender/Cycles,
PlayCanvas source viewer, glTF-Transform/meshoptimizer oracle, world material
and effects systems, and the already audited source kits. Do not replace the
engine or download a bulk library to solve a small missing component.

Commercial-game references guide readability, movement and production quality.
This campaign has no supplied Deadlock/Overwatch client binaries or replays;
it does not claim binary reconstruction or reuse of their proprietary art.
The [earlier source study](../production-reuse-oct23/README.md) retains REA and
open-engine findings. Tool availability is separate from actual analysis.

## Six exclusive owners

| Owner | Files | Acceptance |
| --- | --- | --- |
| Hero cleanup | `tools/hero-source-cleanup/`, `art/ten-rounds-oct23/cleanup/` | Protected body/UV/images, actual matched front/rear views, meaningful artistic improvement |
| Hero rig | `tools/hero-reuse-rig/`, `art/ten-rounds-oct23/rig/` | Same skeleton/actions, source-space fit, actual deformation and export/reimport checks |
| World | `scripts/traversal_landmarks.gd`, `tools/wind-court-pilot/`, world art packet | One court, truthful collision, unchanged roof/routes/anchors, matched day/night views |
| Effects | `tools/reuse-vfx-stage/`, effects art packet | Actual temporal sequence, lifecycle/pause/pool/culling controls, source identity |
| Reuse tools | `tools/reuse-art-next/`, `reuse/` | Exact embedded-WebP/UV/material semantics; adverse inputs fail closed |
| Independent reviewer | `review/` | Inspect originals, inject counterexamples, retain failures, review integration |

Root owns runtime composition, CI, this ledger, the dashboard snapshot and Git
publication. Heavy Blender/Godot captures run sequentially on the four-CPU
cloud; data-only work can proceed alongside them. This is software rendering,
not physical-GPU performance qualification.

## Current decisions

The conservative rear-hair micro-edit is rejected: source preservation passed,
but matched images still show the pitted/melted form. The initial nearest-surface
rig transfer is rejected: normalized weights still connect forearm vertices to
leg/cloth regions and create severe triangular stretching. Neither candidate
replaces the generated source or current playable hero. A corrected anatomical
transfer must earn its own outcome.

The WebP adapter is compatibility tooling. Actual Rama and diya outputs save
only 292 and 336 bytes; triangle/vertex counts are unchanged. These results
justify no frame-rate, memory or meaningful mesh-reduction claim.

The world pilot replaces only `sun-lift-west`, keeping its 8 m envelope and
roof height, other seven courts and the existing signals. Its author fixture
and independent triangle/physics probes precede native visual review. Any
runtime promotion must remove the old full-box collider, then verify the
actual integrated scene.

## Quality and continuation

The desktop campaign remains **17/78 accepted packets, 0/13 complete rounds**.
Android remains deferred at **0/108**. Those ledgers require their own accepted
packets; a successful asset tool, concept, render or source viewer is not a
finished hero or commercial-quality game.

Use actual view/hash/report links in the adjacent packets when continuing.
Preserve rejected evidence and original assets. Next priorities are an
artist-controlled reusable hair substrate, anatomically correct binding,
continuous action/contact qualification, and the next world pilot only after
this one's integrated visual/physics gate. Native online 3v3 authority still
precedes roster or team-size expansion.
