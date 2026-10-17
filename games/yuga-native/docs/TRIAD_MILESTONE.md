# Triad relays: original map interaction milestone

17 October 2026. This supporting milestone adds three capture-and-supply objectives to **offline native Confluence lane practice**, with original civic landmarks and clearer troop-attack markers. It builds on the published [siege preview](SIEGE_MILESTONE.md); it is not a new native multiplayer release or completion of the final visual target.

**Current checkpoint:** source and implementation are committed at `d835d7d57565f4b4bd00c97cf71a41e64137967a`. The independent 37-case relay integration gate and affected world/UI/stress suites pass. The first actual render completed capture and supply but was rejected for an inherited bright floor ring; that decoration is hidden in the committed correction. The fresh complete setup passes 31 reports plus 225 browser-authority tests; corrected relay, siege and traversal captures have completed and selected actual views were reviewed. Package flow and public-release evidence are still pending. The previous siege release remains the verified downloadable build until publication is confirmed.

## Five bounded workstreams

| Packet / owner | Deliverable | Current status | Acceptance gate |
| --- | --- | --- | --- |
| TRIAD-01 · source research | Pinned official TF2 capture/payload/dispenser/HUD study; three community tools; original transfer rules and counterarguments | **Complete, research only** | Exact source/license/read-scope ledger; failed paper/Reddit requests recorded; independent source check; no copied game code or assets |
| TRIAD-02 · native rules and supply | Deterministic capture state, eligible occupants, contested/abandoned behavior, bounded supply and epoch/ID receipts | **Complete for bounded offline behavior** |42 rule cases/one-hour soak and37 actual-world cases; exact state transitions, duplicate/order/invalid-input cases, LOS/height/team/resource limits, replayed/stale receipt rejection and pause/reset checks |
| TRIAD-03 · world art | Reed, Lotus and Sky relay landmarks, angular ground inlays, owner shapes and matching physical plinths | **Prototype views verified; art refinement open** | Real geometry/collision agreement and route clearance; actual day/night close and lane-distance views; ownership readable without relying on color |
| TRIAD-04 · UI and effects | Three-site status, minimap, nearby action hint, immediate relay visit, accurate reset help and revised siege markers | **Capture reviewed; package input pending** | Actual 960×600 and 1280×720 layout, focus/input flow, distinct capture/supply/danger cues, muted and overlapping effects, no hero-damage implication |
| TRIAD-05 · independent QA and release | Adversarial integrated tests, current-source render, extracted package flow and public download verification | **In progress; proof pending** | Source-matched reports and actual views; package source inventory; exact public Linux repeat if released; explicit Windows/performance/audio limits |

These five `supporting_packets` in [ROADMAP_BACKLOG.json](ROADMAP_BACKLOG.json) do not change the 70 production-task statuses. “Implemented” means the relevant source exists, not that independent acceptance is complete. Research completion does not establish gameplay, balance, accessibility or art quality.

## Concrete gameplay contract

The native world remains in metres with Y up and XZ traversal. The three relay centres are **Reed `(-40, 0, 0)`, Lotus `(0, 0, 0)` and Sky `(40, 0, 0)`**. Their capture radius is **5 m**, supply radius **8 m**, and eligibility height tolerance **±2.5 m** relative to the centre. The player participates for Sun; living valid army units participate for their team. Duplicate IDs are deduplicated, while conflicting rows for one ID are excluded. No separate hero health system is implied by the player's active eligibility.

Capture uses **eight contributor-seconds**, with at most **two contributors per team**. A lone uncontested actor secures a neutral relay in **8 s**; two take **4 s**. Taking an enemy-owned relay first consumes the same amount to neutralize it, then another capture stage: **16 s solo or 8 s with two**, assuming uninterrupted presence. Opposing eligible presence contests the point and makes no capture progress. Mode/source flags from TF2 were studied, but these values and rules are original YUGA tuning.

Empty partial progress returns toward the current owner's stable value at **0.5 progress units/s**: neutral points return toward zero; owned points recover toward their owner's full value. An owned relay does not automatically become neutral because nobody stands on it. The session advances the rules in **0.1 s steps**; the rules reject nonfinite/negative steps, steps above 0.25 s, or more than 97 actor rows. This is separate from the army's existing simulation cadence.

Every **5 s** of uninterrupted owned supply cadence, eligible nearby friendly troops can receive **up to 6 health**, and the Sun hero can receive **up to 3 arrows**, capped at **12 arrows**. Troop grants clamp to each unit's maximum health. The service adapter rechecks team, living/valid troop state, distance, height and line of sight at application time; actual accepted amounts are counted. Full recipients gain zero. Hero health is absent, so there is **no hero healing**. No traversal energy or ability-cooldown grant is part of this implementation.

Contest or opposing capture pressure stops supply and resets its cadence; ownership changes do not grant supply on the change tick. A request carries a reset **epoch** and monotonic **ID**. The session must reject stale, repeated, invalid or mismatched requests before granting resources. Rules produce requests; the adapter owns validated mutation of actual actors. Tests must prove this boundary rather than infer safety from the presence of those fields.

Relays stop when the local round ends and are inactive during the six-unit Siege practice drill. Ordinary round reset clears relay ownership/progress, starts a new epoch and clears service counters. Pause, focus/settings handling and overview must not continue capture or supply. Returning to the title disposes of the session. The 37-case actual-world integration suite verifies these lifecycle conditions on the frozen build.

## Player flow and original visual language

In Confluence, use **Escape → Visit Lotus relay** to reach the centre approach, then enter the marked zone with friendly soldiers. Nearby hints explain capture, enemy neutralization, contest, landing within the height band and supply. All three sites show ownership/progress; the minimap shows relay state. F5 keeps its established **ordinary round reset** behavior rather than being described as a simple respawn.

The three landmarks use original Reed, Lotus and Sky motifs, layered stone/brass stations, angular inlaid paving and separate ownership geometry. Neutral, Sun and Moon use different symbols as well as palette. Their physical plinths match visible solid geometry at x−34/−6/+34,z4, clear of both lane and cross-mid rotation routes; authored station offsets do not move the gameplay relay centres.

Persistent capture inlays must remain quieter than imminent danger. The effects revision replaces full bright siege rings with segmented blast boundaries, a source-facing pointer and different team-shaped ticks. Exact attack radius, position and timing remain authoritative. They indicate **attacks on troops** in this prototype; the hero still has no damage/death receiver. Actual overlapping day/night fights must establish whether the revised hierarchy works.

## Source and reuse evidence

[TF2_REUSE_STUDY.md](research/TF2_REUSE_STUDY.md) and [tf2-reuse-sources.json](research/tf2-reuse-sources.json) pin the current official Valve source and selected capture, payload, dispenser and HUD code. The study goes beyond the previous camera-only inspection. BSPSource, mastercomfig and TrenchBroom are compared for specific capabilities and code/content terms. This supports behavior and failure-case research; no TF2 source port, map, model, sound or texture was imported.

The ledger contains 25 records: 20 successfully fetched source/doc files, repository metadata and explicit access failures. All 23 saved response payloads were checked by length and SHA-256; recorded line ranges and source references validate. The independent reviewer checked all 12 community records and the saved payloads. The ordinary Reddit request returned 403 HTML, and the official rendering paper/publications hosts were blocked: no new Reddit corpus or paper-reading claim is made.

Current source/owner checks are retained in [triad-integration](evidence/triad-integration/REVIEW.md), independent behavior/collision checks in [triad-qa](evidence/triad-qa/REVIEW.md), and the rejected first actual view in [triad-render-r1-rejected](evidence/triad-render-r1-rejected/REVIEW.md). The [fresh setup archive](evidence/triad-setup/summary.json) records 31 passed reports and 225 browser tests. Corrected [relay views](evidence/triad-relay-render-r1/TRIAD-RENDER-REVIEW.md), [siege views](evidence/triad-siege-render-r1/SIEGE-RENDER-REVIEW.md) and [traversal views](evidence/triad-traversal-render-r1/REVIEW.md) are archived with source/image/video hashes. The relay take shows Lotus capture and three applied arrows. Neutral inlay contrast, distinct site silhouettes and Moon/contested visual proof remain open; dense troops still obscure small siege directional marks. Existing siege evidence proves its historical source; it must not be relabeled as proof of the new relay behavior.

## Three review rounds and release gates

1. **Contract/source review:** agree coordinates, occupancy, contested/empty transitions, supply receipts, presentation responsibilities and file ownership. Record source lessons and counterarguments; keep the native/browser authority boundary explicit.
2. **Implementation and counterexamples:** independent workers implement rules, resource service, original landmarks and UI/effects. Challenge same-tick opposing arrivals, duplicate/conflicting IDs, invalid values, boundary/height/LOS cases, exact resource caps, receipt replay, reset epochs and disabled modes. Test multiple actor orders and advancing simulation, not only stub calls.
3. **Frozen integration and actual review:** run targeted and affected existing suites on one source checkpoint; inspect actual moving fights and compact-screen input; export and run the extracted Linux package. Compare staged/public assets with the tagged source before changing download claims. A defect gets a bounded correction and a new affected test/capture; failed evidence is retained.

Acceptance requires both machine checks and human-visible evidence. Headless geometry is not an art review; a software-rendered capture is not a target-GPU frame-time measurement. A silent capture or Dummy-audio window is not listening acceptance. Windows export validation is not Windows execution. Final reports must retain these distinctions.

## What this means for the graphics timeline

Relays improve the map's purpose and readability. They do not resolve the gap between the generated hero concept and the current character/world presentation. The [siege milestone's conditional planning estimate](SIEGE_MILESTONE.md#how-long-to-the-concept-target) remains the relevant guide: roughly **3–6 months for an accepted visual slice** with a funded, experienced core team of about 8–12 plus specialist support, and **18–36+ months with a larger team for the full competitive roster/operations scope**. These are planning ranges, not this project's measured velocity or a delivery promise; no staffing or budget was established here.

The next useful proof is an accepted hero and encounter at gameplay distance: editable source, anatomy/face/hair/costume, clean materials, grip/foot contact, continuous aim/attack/ability motion and readable crowded effects. Freeze that visual benchmark before multiplying heroes and maps. Agent parallelism helps independent implementation and review, but does not replace this approval or physical-GPU testing. Full native online matches, player health/death, production economy/balance, the complete roster and Deadlock/Overwatch-level graphics remain open.

## Five next production packets for future agents

After the relay acceptance gate, select these existing tasks with their declared dependencies; do not create a competing full-game roadmap.

| Existing task | Next bounded deliverable | Evidence before moving on |
| --- | --- | --- |
| **FG03-T01 — bow-carry/motion** | Correct closed bow grip and natural carry; review moving-ground contact and substantial flight phases on the exact candidate | Continuous actual attack/carry/movement capture plus numerical continuity/contact checks; retain failures |
| **FG02-T01 — first-hero corrections** | Recover editable Rama source or explicitly reconstruct owned corrections; agree one hero quality benchmark against the concept | Source/provenance, structural checks and same-camera actual close/gameplay-distance review |
| **FG05-T01 — world corrections** | Refine one representative relay encounter's materials, lighting, route silhouettes and crowd readability before expanding dressing | Actual day/night views and continuous encounter; collision/navigation checks; visible target comparison |
| **FG00-T04 — versioned contracts** | Version native rules, map/elevation, entity/receipt and replay contracts, including relay epochs and stage transitions | Written schema/migration plus malformed, stale, reset and compatibility fixtures; browser 3v3/protocol-2 remains explicit |
| **FG04-T02 + FG05-T02 → FG04-T03 — online dependency chain** | After FG00-T04, define the entity/authority bridge and shared 3D collision, then integrate two rendered native clients | Two-client positions/aim/hits/objectives agree under latency, reconnect and stacked-height fixtures; local armies do not satisfy online acceptance |

Read [START_HERE](../../../docs/START_HERE.md) and [BUILD_HANDBOOK.md](BUILD_HANDBOOK.md) for current commands and ownership. Give each worker exclusive files, a common contract and a report with source hashes, executed checks, actual views, limitations and the next owner. Keep the canonical [full roadmap](FULL_GAME_PRODUCTION_ROADMAP.md) and [backlog](ROADMAP_BACKLOG.json) as the source of production completion.
