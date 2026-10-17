# Fifteen specialist roles and executable queue

17 October 2026. Owner: role 15. This is the staffing/dispatch guide for the
[quality target](DEADLOCK_QUALITY_TARGET.md), complementing the existing
[production roadmap](FULL_GAME_PRODUCTION_ROADMAP.md) and
[build handbook](BUILD_HANDBOOK.md). It does not change production backlog status
without root integration and evidence.

The user requested fifteen subagents and permission for bounded child agents.
The runtime permits **seven simultaneous agents including the lead**. Therefore
there are fifteen exclusive specialist roles, **six active workers** and nine
queued packets. The lead owns integration, dispatch, shared manifests and
acceptance decisions. A queued role is not described as a running process.
The tables record the initial dispatch snapshot; root's current queue/messages
own subsequent rotation as workers finish and slots become available.
Workers may spawn a child only after the lead confirms a free slot and assigns
exclusive files; nested delegation consumes the same capacity.

## Squad A — hero art and performance

| Role | Specialist / first packet | State | Ownership and dependency |
| --- | --- | --- | --- |
| 01 | Hero geometry/art director: correct Rama's readable form, costume volume and modeled detail against the supplied reference. | Active: `hero_art_quality` | Assigned art source/generator/geometry; maintain rig/socket contract. Do not overwrite face or material edits once roles 02/04 receive asset ownership. |
| 02 | Hero PBR/materials: skin, cloth, gold, hair, normal/roughness/channel and color-space review at gameplay distance. | Queued | Separate material experiments and comparison report first; final asset merge only after 01/04 freeze. No beauty-lighting-only pass. |
| 03 | Animation/secondary motion: bounded hair/sash/drape response; maintain full-body contact, timing and lifecycle. | Active: `secondary_motion` | Assigned motion/shader/component/test paths. Agree imported vertex masks/material assumptions with 01/02; no gameplay-authority changes. |
| 04 | Facial performance/rig: inspect existing face/rig limits, author restrained expression and eye/eyelid corrections if the asset needs them. | Queued next | Receives exclusive copied/frozen asset after 01. Preserve body skeleton, skin, actions and sockets; demonstrate actual imported neutral/effort/hit/defeat. Hand off before LOD export. |
| 05 | Combat VFX: author original bow/ability anticipation, travel/contact and counters with clear team/priority hierarchy. | Queued | Assigned FX/shader candidate paths; wait for accepted 03 motion and 06 lighting contract. Preserve release authority and boundary/HUD expiry regressions. |

## Squad B — world and competitive systems

| Role | Specialist / first packet | State | Ownership and dependency |
| --- | --- | --- | --- |
| 06 | World look development: hero-readable day/night lighting, PBR separation, shadow contact and coherent arena presentation. | Active: `world_lookdev` | Assigned shared lookdev/presentation paths. No authority/collision edits. Actual same-camera neutral/day/night comparison; coordinate heavy render slot. |
| 07 | Level architecture: original Lanka/Pampā/Indian-city district, tactical landmarks, circular routes and legible playable surfaces. | Queued | Design and one accepted district kit; exact mythology/history source IDs. Wait for 06 material/lighting kit; collision contract belongs jointly to 08/09 before implementation. |
| 08 | Game feel/ability design: input/aim/camera, readable commitment, counters and numerical tradeoffs for Rama. | Queued | Exact runtime/kit/controller files assigned by lead; respect existing 20 Hz kit authority and passing lifecycle behavior. First output is one bounded measured feel defect, not a new game. |
| 09 | Native network/services: versioned 3D map/entity bridge, two rendered clients, real authority, reconnect/result and later operated services. | Queued | Shared authority changes require root contract freeze. Preserve browser/native product boundary; no “online” claim from transport-only or headless tests. |
| 10 | AI/economy: lane soldiers/police/king/cannon roles, jungle entities and objectives/economy with actual counters and bounded life cycles. | Queued | Assigned army/rules fixtures after 08/09 contract. Synthetic repeated-hero load fixtures stay explicitly labeled; human balance is separate evidence. |

## Squad C — experience, verification and production

| Role | Specialist / first packet | State | Ownership and dependency |
| --- | --- | --- | --- |
| 11 | Performance/LOD: skinned-mesh preservation, measured geometry/texture cost and validated LOD candidates. | Active: `hero_performance` | Candidate export/validation tooling and independent copied assets first. Final decimation/export waits for 01 → 04 asset freeze. No FPS claim without physical-GPU profiling. |
| 12 | UI/accessibility: full screen journey, scale/focus/remapping, exact modal-opener restoration and player-readable status/counter explanations. | Queued | Exclusive UI/controller paths assigned when activated. Review actual screenshots first for a design audit; test real package input at declared displays. |
| 13 | Audio: original Indian-instrument-inspired/electronic action, contact, threat and ambience composition. | Queued | Audio source/runtime/tests with cleared provenance; fixed voice/priority budget and alternatives. Requires actual listening review; avoid claiming cultural authenticity from a scale formula. |
| 14 | Independent QA/acceptance: challenge every claimed source, visual, motion, gameplay, lifecycle and package result. | Active: `quality_qa` | Assigned QA/harness/evidence paths; do not alter owner output to make a test pass. Reject concrete visible defects; numerical checks cannot certify finished art. |
| 15 | Build/research/tools/production: answer exact implementation questions, source/license ledger, reproducibility, release/security/operations and whole-team coordination records. | Active: `quality_desk` | Owns this plan, quality target, technical study/source ledger and planning evidence. Root owns shared backlog/notices/source pins and final release mutations unless explicitly delegated. |

## Nine queued packets and release dependencies

These are bounded work orders, not nine additional simultaneous processes.

| Dispatch order | Role | First concrete artifact and acceptance | Prerequisite / reviewer |
| --- | --- | --- | --- |
| N01 | 04 Face/rig | Source-bound face/rig audit; if needed editable correction plus imported neutral/effort/hit/defeat views. Preserve rest binds/actions and no new grip/eyelid artifact. | 01 freezes geometry and hands over its asset. Reviewer 14; 03 checks motion compatibility. |
| N02 | 02 PBR/materials | Same-camera old/new skin/cloth/gold/hair material comparisons, correct channels/color space and a provenance/modification record. | 01/04 freeze edited surfaces; 06 lighting contract. Reviewer 14. |
| N03 | 05 VFX | One complete five-action readability reel with synchronized windup/release/contact/expiry and crowded-scene counter visibility. | Stable 03 motion and 06 lookdev; integration regression unchanged. Reviewer 14/08. |
| N04 | 12 UI/accessibility | Exact Settings/Help opener-focus correction and actual keyboard/mouse journey at 960×600 and 1280×720. | Source-owned UI packet after current render freeze. Reviewer 14; actual package input required. |
| N05 | 08 Game feel | One identified input/camera/aim or commitment problem, bounded correction, normal-speed footage and actual input receipts. | Current hero art/motion stable; shared timing contract. Reviewer 14 plus human feel review when available. |
| N06 | 13 Audio | One original Rama action/counter suite and dense-fight priority mix with mute/pause/lifecycle evidence. | Stable gameplay event contract. Reviewer 14 and actual listener. |
| N07 | 07 Level architecture | One finished slice district with original history-informed forms, routes/sight lines and matching collision/navigation. | 06 accepted presentation kit; 08/09 geometry contract. Reviewer 14/06. |
| N08 | 09 Native network/services | Two actual rendered native clients against authority: movement, shot/hit, death/respawn, reconnect and result with version-mismatch rejection. | Stable 3D map/entity/rules contract; full production dependencies remain open. Reviewer 14; 15 checks build/security scope. |
| N09 | 10 AI/economy | One lane encounter with soldier/cannon/king roles, readable attacks, rewards and reset/soak bounds. | Stable 08/09 authority/economy contract and accepted world district. Reviewer 14; human balance remains separate. |

The lead may reorder independent packets after reporting a concrete dependency
change. Do not activate five shared-asset editors simultaneously. The first
handover is **01 → 04 → 11 heavy export**, with 02 scheduled around an explicit
surface/material freeze. Tooling, code analysis and test design may proceed
before the heavy slot is available. More parallelism must not produce asset
races, stale imports or unreviewed placeholder content.

## Three required checkpoints, then integration

1. **Scope and source contract.** State one observable outcome, current commit,
   exclusive files, shared interfaces, exact sources/terms read and finite
   acceptance. Name what has not been read or executed. Role 15 resolves one
   blocking technical question rather than conducting an endless survey.
2. **Implementation and counterexample.** Deliver actual source art/code and a
   candidate import/run. Preserve a reproducer for meaningful prior failures;
   exercise malformed data, pause/reset/death, zero/large delta, stale imports,
   weight/bind corruption and capacity boundaries where relevant.
3. **Independent actual-output review.** Role 14 or a non-author reviews exact
   source-bound images/sequences/inputs. Record concrete findings and limitations.
   A failing artifact returns to its owner; LIMITED/UNRUN is not PASS.

An additional correction round is justified by a specific finding. Integration
then freezes sources, serializes imports, updates notices/pins, runs affected
checks and archives exact evidence. Release adds actual package input, complete
required CI, declared hardware/platform qualification and fresh public-download
verification. Roster/full-game production gates remain open until their own
evidence exists.

## Copyable work packet and report

```text
Role / task / round:
Product: YUGA native; branch and source commit:
Observable outcome and prerequisite:
Exclusive files; shared interface; next asset owner:
Sources read / tools actually executed / license or attribution:
Acceptance; negative counterexample; actual render/input requirement:
Heavy render/export/import slot:
Result: PASS | FAIL | LIMITED | UNRUN; exact commands and exit codes:
Artifacts, source hashes, image/frame ranges and evidence paths:
Remaining defect or hardware/human dependency; next owner:
```

Use existing tools when they solve the packet: Godot 4.6.3, Blender 4.3.2,
portable glTF, existing authority code and validators. REA/Ghidra is useful only
with a legal accessible binary/input and a bounded analysis question; it does
not supply commercial artwork or production quality. A new plugin/repository is
adopted only after a named need, exact license/file review and useful experiment.
Do not install unrelated bundles to increase a tool count. Skills apply to their
actual workflow: cloud setup/runtime for environment work; design/audit skills
for interfaces with captured evidence; research/source rules for the desk.
