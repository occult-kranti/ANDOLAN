# Six further graphics rounds

This campaign starts at `f81ee18c90547b60fdcc26fb4b1a185ac9ad2b9c`, after the
published UI preview. It is six **new** rounds with six worker assignments per
round (36 assignments), not a recount of the completed U1–U5/I1–I3 campaign.
The product remains the original Godot Rama/Confluence hero slice. The target is
the visual and motion standard in [DEADLOCK_QUALITY_TARGET.md](DEADLOCK_QUALITY_TARGET.md).
Finishing the assignments does not automatically pass that target.

## Ownership and working method

| Worker | Owned product area | Review responsibility |
| --- | --- | --- |
| Hero artist | Reversible hero surface finish and original attached details | Skin/metal/cloth/hair separation in matched views |
| Environment artist | Lighting, ground/water shading, shared architecture finish | Day/night readability, coherent district, bounded resources |
| Animator | Hero motion, facial and secondary presentation | Continuous transitions, support, pause/reset and timing |
| Screen designer | Shared theme, launch, HUD, atlas and modal screens | Legibility, focus, state, layout and duplication |
| Unit artist | Shared infantry/vehicle/relay presentation | Soldier silhouette, weapon motion, reuse and army limits |
| Independent reviewer | Capture tooling, acceptance and adversarial checks | Original framebuffer review and independent verification |

The lead integrates shared callers and versioned source contracts, moderates
accept/reject decisions, runs the single heavy rendering lane, and updates this
roadmap. Each worker stops at a round subgoal and receives a new assignment for
the next round. Raw failures and rejected candidates remain available.

## Round plan

| Round | Implementation goal | Exit evidence |
| --- | --- | --- |
| G1 | Hero finish, scene depth, cast entry, readable screens, sculpted infantry; establish capture workflow | Focused checks and first integrated actual-render review |
| G2 | Correct G1 findings; unify courtyard/world light and character presentation | Matched hero/day/night and gameplay-scale comparisons |
| G3 | District and equipment detail, clear ability presentation, shared-resource reuse | Camera/pose sweeps and resource/allocation checks |
| G4 | Continuous action and travel polish; complete affected screen flows | Actual motion/input review, cancellation and modal edge cases |
| G5 | Stress loaded scene and repeated routes; repair regressions | Bounded stress/edge results plus visible final corrections |
| G6 | Independent final acceptance, repairs and handoff | Source-bound final views, required suites, exact package and publication evidence |

Per-round reports live in `evidence/graphics-six/G1` through `G6`. The machine
ledger is [GRAPHICS_SIX_ROUNDS.json](GRAPHICS_SIX_ROUNDS.json). A round's status
records its bounded result; open visual findings carry forward with an owner.

## Starting findings

The published `I3/role03/native-r1/08-package-world-live.png` shows pale, flat
street lighting and terrain, primitive infantry silhouettes, and small HUD
text. The accepted hero anchor at
`visual-campaign/capture-final-anchors-r4/02-hero-near-day.png` shows a rigged,
textured character but simple hair mass, limited facial richness and visible
support/contact issues. Earlier R4 motion proposals were rejected; those
outcomes are preserved rather than promoted by this campaign.

Use source-pinned images to judge silhouette and material improvement. Use
continuous, declared-rate motion to judge transitions. Headless assertions
cannot establish those visual results. The available renderer is software
Vulkan; physical-GPU performance, Windows execution, human feel/art review and
native online play remain separate production gates.

## Acceptance rule

Implement the six bounded rounds and integrate useful changes. Promote only
changes that pass their actual applicable checks; preserve rejected proposals.
Record the remaining hero/map/screen issues candidly, update the production
queue, and publish only a qualified preview. Do not label this a finished
commercial-quality hero or full game unless the referenced quality gates are
actually closed.
