# Hero and map finishing · CPU Raea / distributed implementation

Task `YUGA-TACTICAL-FINISH2`, product YUGA native. User request: “use Raea on cpu and completely build the hero and map with all resources and agent swarm parallel sub sub sub shared code with dedicated roadmap and distributed work, code build actual game”. Preserve the prior [delivered art build](../ART_DELIVERY.md), confirmed5v5 first-to13 mythic firearms, Casual local bots, Ranked planned and browser deferred.

## Shared architecture and exclusive ownership

| Owner | Exclusive files / work | Shared contract |
| --- | --- | --- |
| Root / integration + renderer | `tactical_world.gd`, `tactical_effects.gd`, veil/ward shaders, Raea tooling/composition, manifests, imports, captures, packaging and this roadmap | Godot remains gameplay authority. Call `weapon.present_ability(slot)` only after authority accepts use; call `reset_presentation()` at round reset/death. Raea CPU output is a separate presentation artifact; no video substitutes for implemented gameplay. |
| hero_combat / hero lead | `tactical_weapon.gd`, focused hero checks, `finish2/hero/` | Presentation hooks never spend resources, change shot timing or cause damage. Paused match delta advances all poses. |
| hero_combat/cast_motion / nested specialist | New `tactical_cast_motion.gd` only | Original articulated hand poses and bounded offsets for Q/C/E/X; independent of authority and original imported gun. Parent integrates and reviews. |
| reference_panel / world artist | `tactical_map.gd`, new architecture shader/detail helper, `finish2/map/` | Shared original material/prop kit. Preserve exact map collision/routes/sites; new decoration stays in occupied solids or nonblocking overhead/exterior space. |
| hero_ui / hero inspection | `tactical_frontend.gd`, new `tactical_hero_showcase.gd`, focused showcase checks, `finish2/ui/` | Reuse accepted Rama asset/material/rig adapters and actual SURYA in a separate native SubViewport. No gameplay authority or old bow; front/back and drag controls. |

Four active agent slots permit root, two leads and one nested specialist. Workers share code/resources, not copied projects or separate loaded engines. Code work runs in parallel; imports, heavy renders and package exports are serialized. No uncontrolled recursive process spawning.

## Work sequence

1. Preserve completed `sanctum-art-r1` packages and exact normal-input evidence.
2. Hero: visible Q throw, C open-palm ward, E bracing and X charge/release/return; preserve reload and death/reset boundaries.
3. Map: improve material depth/roughness/variation and covered approach/solid-cover ornament with a reusable kit.
4. Effects: polish veil onset, dash ring and ultimate release readability without changing authority ranges/timers.
5. Raea: install a pinned official Linux release, select CPU software Vulkan explicitly, render a bounded original composition using YUGA assets; retain actual result or exact failure. No claimed performance from upstream timing examples.
6. Integrate, run only focused changed-behavior checks, inspect actual native motion/views, correct observed defects, freeze and deliver a successor native build plus editable source and render outputs.

Current status: hero/map implementation, native captures and Linux/Windows packages are complete. Hero presentation passed 94 focused checks; world integration passed 33. The map retains all 62 original physics signatures, with 42,700 relief vertices inside the allowed solid envelope. All 22 combined native stills were reviewed; the corrected cast film contains 180 original frames and passes 18 behavior checks. The gallery loads 25 stills and both separate videos. The exact packaged Linux input route passed with 37 events, 14 reviewed originals and native Quit 0. The source/art archive is generated from the frozen closure with a separate manifest and CRC receipt.

Raea produced the original SURYA turntable on CPU software Vulkan. The frozen game runtime remains Godot. See [exact source, artifacts and limits](DELIVERY.md).

The cast specialist was a real nested child assignment; the hero, map and interface leads worked on exclusive modules in the same checkout. Shared imports, heavy rendering and exports were serialized. Code and focused reviews ran in parallel.

## Six panel passes completed for this checkpoint

| Pass | Concrete work | Record |
| --- | --- | --- |
| 1 · Contract | Preserve confirmed first-to-13 Casual, shop/HUD stream, ownership and presentation-only APIs | This ownership table; subsystem baseline files |
| 2 · Build | New articulated casts, material/relief kit, native hero inspection and CPU Raea composition | Hero/map/UI source freeze records; Raea sources |
| 3 · Focused checks | Hand continuity, lifecycle, world integration, exact collision preservation | Hero 94; world 33; map authority-preservation-r2; UI checks |
| 4 · Actual probes | Inspect initial native hand, map close-ups and hero screen | Preserved rejected/limited probes in hero/map/UI |
| 5 · Correction | Off-screen hand return, Lotus lobes/bevel, quiver removal and contact shadows | Final immutable source snapshot and final native review records |
| 6 · Delivery | Combined screens/movie, actual CPU turntable, native packages, source/art and resumable docs | [Delivery](DELIVERY.md), package manifest and input receipt |

These are six successive working passes, not six independent commercial-quality certifications. Full-body tactical locomotion/contact, face/hair, richer bot art, online and hardware qualification remain separate production work.
