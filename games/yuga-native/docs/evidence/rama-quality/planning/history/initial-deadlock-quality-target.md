# YUGA quality target and completion gates

17 October 2026. Owner: role 15, production/research desk. Baseline inspected:
`1ab1f5e330d256a6ffb6a5706a07f2ff8c3bbb0e` on
`game/yuga-native-production`.

The production goal is an original mythology-inspired, third-person **6v6,
fourteen-hero, three-lane, eighteen-minute** competitive game. The visual and
motion ambition is the quality associated with Deadlock, Overwatch and Dota 2.
The immediate deliverable is **one accepted Rama hero in a finished arena
slice**, using the supplied Rama painting as the identity reference. Expanding
the roster or publishing more low-detail variants does not advance this gate.

“3D/4D/5D” is not a testable quality level. Evaluate modeled form, PBR materials,
deformation, timed animation, secondary motion, effects, camera, responsiveness
and achieved hardware performance. Reference-game mechanics can inform original
work. No commercial client models, maps, audio or executable implementation have
been recovered for this project. Tool installation and generated concept images
do not establish finished playable art.

Read [the current acceptance record](RAMA_HERO_ACCEPTANCE.md) for the released
preview's exact evidence. It is a functional offline milestone with production
art **LIMITED**. These gates extend that record; they do not retroactively revoke
its bounded functional passes or promote its art result.

## What must change now

The current source has a smooth-skinned hero, authored full-body actions and a
working five-action kit. The remaining critical art gaps are sculpted hair,
costume volume and fabric response, stiff secondary motion, face/expression,
material richness, and actual gameplay-camera presentation. R7's 450,084
triangles, thirteen materials and eighteen maps are inventory, not a quality
score. There is no accepted authored-LOD chain or twelve-player physical-GPU
budget. CPU/software-Vulkan rendering can review correctness and appearance;
this environment has no physical GPU and cannot establish consumer performance.

The first six active roles are art geometry (01), animation/secondary motion
(03), world look development (06), performance/LOD (11), independent QA (14) and
build/research/tools/production (15). Nine specialist packets are queued in
[the squad plan](PRODUCTION_SQUADS.md). The art path is geometry → face/rig if
required → LOD generation and shared export. Dependent asset editing and heavy
renders are serialized; code, source review and independent QA can overlap.

## Perceptual review contract

1. Freeze source, asset and import hashes. Record engine, renderer, resolution,
   camera/FOV, lighting phase, settings and elapsed simulation time.
2. Review the current imported game asset from front, rear, both three-quarter
   views, face close-up and the normal third-person camera. A studio turntable
   supplements the game view. Match hero image height and camera when comparing
   revisions; do not conceal a defect by changing framing or exposure.
3. Show neutral light and the actual day/night scene. Inspect silhouette,
   cloth/hair surfaces, gold/skin/ivory separation and effects together. Painted
   concept detail does not count as modeled or shaded detail in the game.
4. Review uninterrupted normal-speed sequences and inspect the relevant adjacent
   frames. Include start, stop, strafe, jump/landing, draw/release, every ability,
   hit, defeat, respawn, flight/grapple, cancellation and rapid retriggers.
5. A reviewer other than the implementer records PASS, FAIL, LIMITED or UNRUN
   with exact files/frames and a concrete finding. A visible failure returns to
   its owner; a larger mesh, numerical test count or checklist cannot override it.
   Human art-direction and player-feel review remain separate unrun production
   evidence until people actually perform them.

## Quality gates

| Gate | Evidence required before acceptance | Current gap / rejection rule |
| --- | --- | --- |
| Q01 Geometry and identity | Editable source; final imported mesh; reference-matched views; believable face/eyes/hands; layered hair and drape; readable bow/quiver/gold; independent actual-image review. | LIMITED. Reject primitive-looking anatomy, helmet-like hair, empty grip, dominant rectangular strips, disconnected trim or a trouser silhouette that contradicts the approved art direction. |
| Q02 Materials and lighting | Correct base-color versus linear data maps, normals/tangents and channel mapping; controlled material comparison; actual neutral/day/night views at the same exposure/camera; skin, metal and cloth remain distinct. | LIMITED. Reject clipped blue skin/gold, flat plastic cloth, metallic skin, texture seams, lost shadow contact or lighting that hides the hero's form. More saturation/bloom is not acceptance. |
| Q03 Continuous animation | Source-bound normal-speed sequences, contacts and transition review; preserved pause/reset/death behavior; sample-rate checks at 30/60/120 Hz; coherent anticipation, release, recovery and locomotion. | Bounded authored motion passes exist, but production facial/secondary polish is open. Reject snaps, bow/string/hand separation, skating, drape tearing or ornamental motion detached from body acceleration. |
| Q04 Secondary motion and face | Hair, sash and cloth react plausibly without changing gameplay authority; bounded response to movement/teleport/pause/reset; no persistent penetration in reviewed poses; readable restrained expressions for ready/effort/hit/defeat. | Open. An effect shader or bone count alone does not prove convincing motion. Preserve exact feature limitations of converted PBR materials. |
| Q05 Combat feel and clarity | Actual input → accepted action → release → contact → receiver → HUD/sound evidence; all five actions and counters; camera/reticle readable during the densest accepted effect; human comprehension/feel session recorded separately. | Deterministic offline function passes; human feel/balance remains UNRUN. Reject early cosmetic authority, stale HUD, invisible commitment, duplicate payload or an effect concealing a threat. |
| Q06 Arena and world | A finished coherent district with original architecture, collision/navigation agreement, day/night and wet-area material tests, landmarks and tactical sight lines; gameplay-scale review with hero/effects/minions. | Current world is supporting practice, not final art. New environment work must improve the same hero slice; no unrelated lower-quality map track. |
| Q07 Authority and synchronization | Two rendered native clients and one real authority on the same versioned 3D map; movement/shot/hit/death/respawn/results/reconnect agree; measured live impairment cases and duplicate/stale/reordered command handling. | Open. Current native preview is offline. Headless transport or browser authority alone does not close native integration/elevation. |
| Q08 Complete player journey | Install → title → settings/remap → training → queue/room → draft → match → reconnect/result → rematch/exit; readable keyboard focus, scalable text, supported input and accessibility options at declared displays. | Offline bounded flows pass. Exact Settings/Help opener restoration, native online journey, controller/device behavior and broader production UX remain open. |
| Q09 Audio | Original/cleared assets; distinct action/contact/threat/ally cues; pooled bounded voices; volume/mute/pause/device behavior; actual listening and dense-fight intelligibility review. | Existing synthesis and logic checks are supporting evidence. Dummy audio cannot establish sound quality. Avoid untested claims about raga authenticity, psychology or retention. |
| Q10 Performance and scalability | Authored or validated generated LODs; stable rig/animation/contact; actual twelve-actor/effects/minion scene; named physical GPU/CPU/driver, resolution, quality, CPU/GPU frame-time distributions, memory/VRAM and warm-up/capture method. | UNRUN on physical GPU. A desired 1080p/60 Hz target is provisional until minimum hardware and settings are declared. Fixed-rate video, headless cost, triangle reduction and llvmpipe are not achieved consumer FPS. |
| Q11 Competitive design | Six accepted distinct heroes before a duplicate-free six-person production team; fourteen for full roster; counters, economy/objective readability, full matches and recorded novice/experienced human review. | Open. Repeated Rama actors may be labeled engineering load fixtures; they are not six finished heroes or balanced team compositions. |
| Q12 Build, security and operation | Frozen source/content/rules, successful focused + complete required CI, actual supported-platform runs, fresh-download hashes/payload verification, authority/account isolation, hostile-input bounds, rollback and service/support ownership. | Linux preview evidence exists; Windows execution, operated online services and production capacity remain open. A ZIP or GitHub Pages site does not run a persistent authoritative server. |

## Delivery order for the whole game

| Stage | Deliverable | Exit rule / next dependency |
| --- | --- | --- |
| P0 Current quality correction | Improve Rama's geometry, material presentation, secondary motion and scene readability; generate safe LOD candidates. | Actual asset and motion review closes the concrete critical findings. Keep rejected evidence. No roster multiplication. |
| P1 Hero quality slice | One complete final-looking Rama, coherent arena district, all five actions, full offline screen flow and measured declared hardware profile. | Q01–Q06, relevant Q08–Q10 and platform-build checks accepted; human art/feel review explicitly recorded. This is the visual replication template for other original heroes. |
| P2 Native authority slice | Same hero/arena with two rendered clients, elevation/collision agreement, prediction/interpolation and real receipts, reconnect and result. | Q07 plus actual network impairment and lifecycle review. A mirror matchup here is a labeled integration fixture. |
| P3 Team core | Six distinct accepted heroes, full three-lane objective/economy/minion/boss rules, 6v6 bots and human closed tests, complete join/rematch flow. | Full-match and six-person composition gates; no substitution of catalogue entries for finished heroes. |
| P4 Full content | Fourteen independently accepted hero sets, complete original map districts, minion/boss/vehicle motion and complete counter/effect/audio libraries. | Every content item has Q01–Q06/Q09 evidence at gameplay scale, and all team combinations fit accepted scene budgets. |
| P5 Production alpha | Operated native authority/services, profiles, match finding, moderation/reporting/support, reconnect/leaver behavior, replay/diagnostic receipts and update/rollback. | Complete player journey and declared capacity/security evidence; no unverified ranked or anti-cheat claim. |
| P6 Beta and release | Human balance/accessibility sessions, hardware/platform matrix, long soaks, external installation, monitored live trial and release candidate. | Q01–Q12 accepted for the declared launch scope. Publish only the exact accepted source/package; maintain known lower-severity issues with owners. |

Stages are dependent gates, not a claim that the full game exists. Continue
independent design/authority/tool work where it does not consume the art critical
path, but do not ship a cheaper visual target as the requested finished game.

The existing backlog remains authoritative. Proposed mapping for root's next
backlog update: P0/P1 support FG01–FG03, FG05 and FG13; P2 supports FG04; the
existing three-hero 3v3 FG06 is an intermediate integration gate before P3's
six-hero FG07 / armies FG08 / production 6v6 FG09; P4 covers FG10/FG11; P5 covers
FG12/FG13; P6 closes FG14/FG15. This mapping changes no task status or dependency
and does not turn the intermediate 3v3 experiment into the final 6v6 design.

## How long

There is no evidence-backed completion date yet: the project lacks an accepted
final-quality hero, physical-GPU measurements, a measured content-production
rate and an operated native multiplayer slice. The earlier **3–6 months for a
tightly scoped hero/arena slice with 15–30 experienced production people**, and
**2–4+ years for the full competitive game**, are conditional planning ranges,
not measured estimates or promises. Confidence is low; the complete game can
take longer with changing scope, original character production or service needs.

Fifteen specialist agent roles are work ownership, not fifteen full-time human
artists/engineers or a guarantee of linear acceleration. This workspace permits
six active worker agents plus the lead; nine roles rotate through the same
capacity. Budget, actual artists/animators, human review, GPU workstations,
server operation and supported-platform access materially change the schedule.
Unlimited requested tokens do not remove those dependencies.

Replace those ranges with a forecast after P1: record accepted art/animation
revision time, reviewer turnaround, actual hardware cost and two-client
integration time; estimate remaining work by accepted hero/district/system,
including rework and platform/operations time. Report the next accepted gate and
its concrete remaining defects instead of a misleading completion percentage.

Technical decisions and exact accessible sources are in
[the quality study](research/RAMA_QUALITY_TECH_STUDY.md). Team dispatch and
round-by-round evidence rules are in [the squad plan](PRODUCTION_SQUADS.md).
