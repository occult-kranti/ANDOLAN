# Rama visual production campaign

Requested 17 October 2026: ten rounds, fifteen specialist assignments per round,
aimed at the visual quality of Deadlock rather than another prototype game.
Baseline: `38d11148fe69b184e981164c8a71387c91dc64c5` on
`game/yuga-native-production`. This is native YUGA; current play remains offline.

The campaign keeps the existing authored Rama, rig, controls and combat. The
first visual diagnosis is glossy, insufficiently differentiated surfaces, a
sparse title backdrop, hard locomotion thresholds and limited ability ornament.
Actual game captures, rather than concept pictures, judge the changes.

## Capacity and roles

Six workers run concurrently alongside the moderator. Fifteen named specialists
rotate through those slots. An assignment is only executed when its worker has
returned an artifact or review; a planned slot is not a completed agent run.
The machine-readable ledger retains all 150 requested role/round slots and their
individual state. The completion of a bounded round does not establish AAA
quality, human art acceptance or physical-GPU performance.

| Role | Ownership |
| --- | --- |
| 01 Hero surface artist | Skin, gold, hair, cloth material separation |
| 02 District artist | Original courtyard architecture, ornament, foliage |
| 03 Lighting artist | Day/night form, practical light, atmosphere |
| 04 Ability artist | Five accepted-event effects and impact language |
| 05 Animator | Gait transitions and preserved contacts |
| 06 Capture engineer | Source-bound matched actual-engine images |
| 07 Reuse researcher | Pinned open resources and reusable implementations |
| 08 Character detail artist | Inspect hair/face silhouette and feasible corrections |
| 09 Material reviewer | Ownership, texture channels, lifecycle and image defects |
| 10 Motion reviewer | Independent gait, contact and cancellation checks |
| 11 Effect reviewer | Threat readability, timing, bounded resources, options |
| 12 Environment reviewer | Navigation, silhouettes, day/night visibility |
| 13 Performance engineer | Actual geometry/material costs and resource bounds |
| 14 Build engineer | Imports, integration, export and reproducible checks |
| 15 Independent art reviewer | Inspect raw images, reject visible regressions |

## Round sequence

The [latest reuse consultation](research/community-reuse/README.md) refines the
next goals without advancing round completion. The published Round 1 runtime
baseline is `09dac7220544374a471a11d953b67de20ab99d7d`; face/skin remains next.
Existing Godot/Blender tooling and owned art stay on the critical path. Source-
derived mesh/key optimizers are optional Round 9 tools. Six mythology briefs
inform later motion, troop and district work, with explicit source/invention limits.

| Round | Production goal | Required outcome |
| --- | --- | --- |
| 1 | Integrated look development and corrections | Baseline and revised actual-engine views; sourced surface treatment, architecture, light, effects and motion; independent rejection of regressions. |
| 2 | Face and skin | Diagnose visible shading patches; improve principal facial forms with editable art and reviewed deformation. |
| 3 | Hair and cloth | Authored silhouette, asymmetry, thickness and folds; no detached strands, intersections or lost ornament. |
| 4 | Motion transitions | Continuous start, stop, turn, land and action recordings; retained contact and accepted event timing. |
| 5 | Combat effect hierarchy | Distinct actions and exact threats remain readable in actual day/night fights and reduced options. |
| 6 | District composition | Coherent architecture and swamp near/middle/distance, detailed soldier/minion forms, material scale and usable routes. |
| 7 | Light and environment | Controlled day/night practicals, water, atmosphere and motion with stated rendering costs. |
| 8 | Complete presentation flow | Consistent title, controls, training, HUD, outcomes and sound; actual input and listening review. |
| 9 | Optimization and stress | Stated-hardware frame time and memory, resource bounds, quality tiers and sustained play. |
| 10 | Independent acceptance and delivery | Exact-source package and launch checks; judge the target again and retain unresolved production gates. |

Every round assigns all fifteen roles, with one owner for each artifact. The
ledger separates these cycles from workstream progress. Its initial version
used production topics as round headings; schema 2 removes that ambiguity.
Capture names **R1/R2/R3 are revisions inside the first round**, not three
completed fifteen-role cycles. Corrective follow-ups do not count as 150 runs.
Future assignments remain planned until a worker returns their actual work.

After each completed round, update its source and evidence links, accepted and
rejected changes, remaining defects and the following round's tasks. Do not
advance a numerical pass into art acceptance. The production gates in
[DEADLOCK_QUALITY_TARGET.md](DEADLOCK_QUALITY_TARGET.md) stay authoritative.

Current cut: the first fifteen-role implementation/review cycle is complete,
with bounded LIMITED art acceptance. Nine rounds and 135 assignments remain
planned. Final film review covers 25 stills, 31 selected animation frames and
three ordinary default-source anchors. Twelve
visual suites pass 727 assertions; sixteen existing quality suites pass 777
assertions and fifteen PCM checks; the resource/effect census passes 51 checks;
additional world-presentation and lighting suites pass 32 and 30 checks.
The overall art decision remains **LIMITED**. These suites overlap component
checks and are not additive measures of finished-game coverage.

## Evidence and integration

The baseline renderer uses a committed-source snapshot so parallel edits cannot
contaminate the comparison. Candidate captures use fresh source pins, the same
camera modes and actual Godot Forward+. Screenshots are not retouched. Software
Vulkan timing is recorded as software execution, never consumer GPU performance.

Each component has one owner. Root owns `player.gd`, `courtyard.gd`, roadmap and
final integration. Shared imports and heavy renders are serialized. Existing
REA/Ghidra and MikkTSpace remain analysis/authoring tools; this work does not claim
commercial-game binaries or assets were recovered. Source reuse is credited at
the actual code or asset boundary.

Status and per-round decisions: [VISUAL_CAMPAIGN.json](VISUAL_CAMPAIGN.json).
