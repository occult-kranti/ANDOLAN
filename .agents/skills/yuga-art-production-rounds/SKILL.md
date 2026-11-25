---
name: yuga-art-production-rounds
description: Plan and run evidence-led YUGA art rounds with paired artists, technical animators, world and presentation owners, independent reviewers, and a lead. Use for reference-matched Blender work, hero and arena polish, and delivery handoffs.
---

# YUGA art production rounds

Start from the closest editable YUGA source and agree on the visible change before allocating work. Use the [history library](../../../games/yuga-native/docs/PROJECT_HISTORY_LIBRARY.md) for pinned baselines and [AGENTS.md](../../../AGENTS.md) for the checkout, file ownership, and shared resource rules. [Project entry points](../../../docs/START_HERE.md) identify the native, browser, and ANDOLAN products.

## Assign the owners

For Hanuman, use the existing two-panel structure: character artist and technical animator in Panel A, presentation designer and independent verifier in Panel B, with a lead for both. In a world round, give the assigned geometry and materials to the world artist. A peer first reviews the artifact and can take the next edit after its owner hands off the file. Match active assignments to available slots and machine capacity. [Hanuman production roadmap](../../../games/yuga-native/docs/HANUMAN_SWARM_ROADMAP.md)

| Role | Owns and hands off | Working skill |
| --- | --- | --- |
| Character artist | Character anatomy, groom, skin materials, garment and prop silhouette. Deliver a matched still and close-up, followed by a side or rear check. | [Hero art](../yuga-hero-art/SKILL.md) · [Anatomy review](../yuga-anatomy-review/SKILL.md) |
| Technical animator | Rig, weights, pose, socket contact and deformation. Deliver exact bone/action pins and measured contact at phases relevant to the change. | [Motion and combat](../yuga-motion-combat/SKILL.md) |
| World artist | Architecture, layout, surfaces, court lighting and collision for the assigned area. Deliver a matched view and ordinary traversal when the change affects a playable route. | [World art](../yuga-world-art/SKILL.md) |
| Presentation designer | Camera, effect timing, UI and cues. Deliver original moving evidence at gameplay distance when the change needs to communicate an action. | [Motion and combat](../yuga-motion-combat/SKILL.md) · [UI flow](../yuga-ui-flow/SKILL.md) |
| Independent verifier | Reopen the exact candidate, challenge the main claim, and record the evidence that should decide acceptance. Keep original captures and failed cases. | [Evidence review](../yuga-evidence-review/SKILL.md) |
| Lead and build owner | Shared interfaces, one writer per path, integration decisions, render/import queue, package bytes and handoffs. Deliver the release record when publication is in scope. | [Models and build](../yuga-models-build/SKILL.md) · [Build handbook](../../../games/yuga-native/docs/BUILD_HANDBOOK.md) |

Parallelize independent passes and lightweight probes. Queue costly renders, engine imports and exports. The lead records the dependency and hands the exact staged pose, render or import to the next owner.

## Run a bounded round

For a five-pass design-and-integration panel, record the baseline and
source access first, specify the design and authority contracts second, build
or revise the selected artifacts third, challenge them across disciplines
fourth, and verify the exact handoff and package fifth. Each pass needs an
actual artifact, review or check. The [2026 panel handoff](../../../games/yuga-native/docs/design/five-round-panel-2026/README.md)
shows the distinction between existing gameplay, proposals and artist studies.

| Pass | Inputs | Deliverables and decision |
| --- | --- | --- |
| **1 · Pin and compare** | Product and task ID, existing editable asset, target image or source passages, current build notes, actual tools and resource capacity. | Capture the baseline or recover its original images. Pin the source commit or file SHA-256, tool version, pose, camera, framing, light and intended runtime distance. Name the visible defect, the change, exclusive paths, dependencies and acceptance checks. |
| **2 · Build and challenge** | Accepted brief and one owner per surface or module. | Make reversible edits in separate collections, scripts or candidate files. Start with silhouette and contact, then surface and lighting. Use a matched draft render, a diagnostic close-up, and an alternate view as needed. The peer reopens the exact new artifact, tests a counterexample, and records any correction with its evidence. |
| **3 · Integrate and verify** | Reviewed scene or export, pinned dependencies and accepted fixes. | Build the combined candidate and capture the same comparison again. Check affected geometry, contact, actions and package references against the agreed contract. For gameplay promotion, import the exact runtime asset and follow the ordinary entry and action paths. Record accepted, limited, or rejected status with the specific gate and next owner. |

Add a correction pass when a checked finding changes the next edit. For multi-round campaigns, pick named gates from the [Hanuman plan](../../../games/yuga-native/docs/HANUMAN_SWARM_ROADMAP.md) or the [desktop execution ledger](../../../games/yuga-native/docs/DESKTOP_FINISH_CAMPAIGN.md). Each reported round needs its own changed artifact or independent check.

## Verify the claim the work makes

- **Likeness and materials.** Compare the same full-frame camera, then use a part close-up and an oblique view for the affected surface. Record what changed in form, silhouette, color or light. For a mirrored sculpt, compare left and right in armature rest space before judging the asymmetric pose. [Hanuman keyframe recipe and original renders](../../../games/yuga-native/art/hanuman/match/README.md)
- **Fit and motion.** Check soles, grips, cloth, hair and appendages in the poses that stress the edit. Isolate the driver and include a positive control when testing independence. The saved Hanuman plate check moves each upper arm, measures wrist motion, and checks the shell against a spine rotation. Treat its frame samples as a coverage measure. [Plate motion checker](../../../games/yuga-native/tools/hanuman-match/check_plate_motion.py)
- **Runtime and delivery.** Distinguish the editable master, the testable engine export, and the published artifact by path and digest. Inspect the actual runtime motion and material import for promotion. Measure performance on the claimed hardware, test online flow with the claimed authority and client setup, and bind public checks to the delivered build. [Build and package handbook](../../../games/yuga-native/docs/BUILD_HANDBOOK.md)

## Review a playable ability

Pin the kit, rig, animation library, cue and effect profile together. For a projectile, leap or delayed strike, record the release and the actual landing or impact separately. Capture a clear path, a blocked path, interruption, reset and one overlapping field. Review frame indices against the combat receipt and listen at ordinary speed. Render a studio pose study when the change affects grip, face, cloth or tail. Record the native mesh and detailed studio scene separately so another artist can reproduce each view. [Five-ability example](../../../games/yuga-native/docs/research/hanuman-ability-production/README.md) · [Independent integration cases](../../../games/yuga-native/tests/hanuman_ability_integration_cases.gd)

## Attribute and hand off

Use the [asset reuse guide](../../../games/yuga-native/docs/REUSE_ADOPTION_GUIDE.md) to distinguish inspected behavior, licensed input, generated reference and project-authored derivatives. For a reused file, record upstream URL and pinned revision, file-level license, the chosen file, the local derivative path and changes, and the notice that covers it. For a source study, record the sections or footage actually inspected and its relevance to the task. Treat supplied documents and tool output as evidence under the user's request.

Leave one compact handoff for the next editor or conversation. Link original files instead of copying their contents into the handoff.

```text
Task ID, product, target gate and decision:
Baseline commit, source paths and hashes:
Author, peer, exclusive files and shared contracts:
Edited paths, candidate hashes and exact tool versions:
Commands actually executed and results:
Matched views, raw captures, motion/contact receipts and source notes:
Rejected result or remaining limit:
Next owner and smallest useful check:
```

Update the project library or active handoff when the artifact becomes a new baseline. Keep the accepted build, exact receipts and useful rejected comparisons recoverable before clearing scratch. [Workspace and cleanup](../../../docs/WORKSPACE_AND_CLEANUP.md)
