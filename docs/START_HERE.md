# Start here: project and agent handoff

Updated 17 October 2026. This is the short entry point for a new chat, contributor or subagent. Start here and open only the subsystem assigned to your task; the repository contains several games and historical experiments.

## The current build in one minute

The active track is **YUGA native**, an original mythology-inspired third-person game under `games/yuga-native/`, on `game/yuga-native-production`. The [single Rama milestone](../games/yuga-native/docs/RAMA_HERO_MILESTONE.md) replaces the active avatar with `rama-hero.glb`: an editable skinned character, 23 authored clips, one primary attack and four abilities shared by training and lane practice. [Independent acceptance](../games/yuga-native/docs/RAMA_HERO_ACCEPTANCE.md) distinguishes passed functional checks from the still-limited art target.

**Download:** [Rama hero preview](https://github.com/occult-kranti/ANDOLAN/releases/tag/yuga-rama-hero-2026-10-17) for Linux or Windows. Public file hashes, ZIP contents and both videos are verified in the [publication receipt](../games/yuga-native/docs/evidence/rama-hero/published/REVIEW.md). Linux execution was reviewed; Windows remains unexecuted.

**Play:** choose **Bow training** or **Explore Confluence**. LMB draws/shoots; Q pierces, E steps, C places a protective field and X fires three paced arrows. R reloads; F/G fly and grapple. F3 opens Rama’s guide, F2 opens Help/remapping, Escape pauses, and F5 resets practice. Enemy siege blasts damage Rama; defeat respawns him after three simulation seconds. Ordinary troops target other troops. Ground casts still use planar receivers.

Confluence is an offline 140 × 260 m world with three lanes, five army roles including siege vehicles, three capture/contest/supply relays, gold/core outcomes, day/night lighting and saved controls. The older fourteen-invocation catalogue is a separate study accessible from its pause menu. It is not the active Rama kit or fourteen finished native heroes. The 24-second duel film retains its separately authored older characters.

The portable package manifests record their exact source commit and runtime hashes. Current actual Linux input evidence, final gameplay capture and public-release status belong in the [Rama evidence archive](../games/yuga-native/docs/evidence/rama-hero/). Packaged reviews caught and corrected a Settings entry-scroll defect. Later rendered review caught a Guardian boundary/HUD timing defect; the normal-update regression and focused rendered expiry probe now pass. The archive preserves rejected candidates separately from the current package and accepted captures. Do not reuse historical Mythic results as acceptance of this character.

The intended production game remains **6v6, fourteen heroes, three lanes and an 18-minute match**. Native online matches, elevation authority, the full roster, concept-quality sculpt/materials/secondary motion, authored LODs and physical-GPU profiling remain open. Windows is packaged but unexecuted. This is animated 3D, and fixed-rate captured video is not achieved real-time performance. No Deadlock/Overwatch/Dota 2 client binaries or commercial models were recovered here.

Historical immutable releases: [Mythic](https://github.com/occult-kranti/ANDOLAN/releases/tag/yuga-traversal-armies-2026-10-17-mythic) at `e2dc0ecd3f6903e0c8af68b2c5717ba5947108ed`, and [Triad/siege](https://github.com/occult-kranti/ANDOLAN/releases/tag/yuga-traversal-armies-2026-10-17-triad-siege) at `ae33db4520bd14fe7b38aed173b764de7a7424d5`. Their [Mythic](../games/yuga-native/docs/evidence/mythic-published/REVIEW.md) and [Triad](../games/yuga-native/docs/evidence/triad-published/REVIEW.md) evidence keeps its original scope. The [TF2 source study](../games/yuga-native/docs/research/TF2_REUSE_STUDY.md) informed behavior; no TF2 code or assets were imported.

## Read by purpose

| Need | Start with | Then open only if relevant |
| --- | --- | --- |
| Build, change or test native YUGA | [Build handbook](../games/yuga-native/docs/BUILD_HANDBOOK.md) | Its task-to-file and test matrices |
| Choose the next milestone | [Production roadmap](../games/yuga-native/docs/FULL_GAME_PRODUCTION_ROADMAP.md) | [Dependency/status ledger](../games/yuga-native/docs/ROADMAP_BACKLOG.json), [design master](../games/yuga-native/docs/GAME_DESIGN_MASTER.md) |
| Use criticism, mythology, books or open-source references | [Research brief](../games/yuga-native/docs/research/RESEARCH_BRIEF.md) | The exact source/report linked in the relevant row |
| Verify the current hero milestone | [Rama milestone](../games/yuga-native/docs/RAMA_HERO_MILESTONE.md) | [Independent acceptance](../games/yuga-native/docs/RAMA_HERO_ACCEPTANCE.md), [evidence archive](../games/yuga-native/docs/evidence/rama-hero/); earlier release evidence remains historical |
| Work on browser YUGA | [Browser README](../games/yuga/README.md) | `games/yuga/shared/`, `client/`, `server/` and its own QA |
| Work on the ANDOLAN protest game | [Root README](../README.md) | `apps/`, `packages/`, root `tests/` and [ANDOLAN roadmap](ROADMAP.md) |
| Manage cloud storage or recover setup | [Workspace and cleanup guide](WORKSPACE_AND_CLEANUP.md) | Native handbook setup section and cleanup receipt |

The full roadmap and machine-readable backlog own production status. The handbook owns execution instructions; the research brief owns source navigation. Historical reports describe their pinned builds. Avoid copying old numbers into a new acceptance claim.

## Select the correct product before running commands

Run from the repository root. Node dependencies share `package-lock.json`.

| Product | Start | Focused verification | Important boundary |
| --- | --- | --- | --- |
| Native YUGA | `godot --path games/yuga-native` | See handbook; `bash tools/cloud/setup-native.sh` is the complete prepared-environment check | Godot 4.6.3 standard; actual playable world is offline |
| Browser YUGA | `npm run yuga:dev` | `npm run yuga:typecheck` and `npm run yuga:test` | Client 5180/server 3005; protocol 2, 3v3, 480 seconds; hosted authority is separate |
| Browser mechanics labs | `npm run yuga:lab:dev` | `npm run yuga:lab:test` | Client 5181; original local experiments |
| ANDOLAN | `npm run dev` | `npm run typecheck` and `npm test` | Client 5173/server 3001; separate city/story game |

Use `npm ci` if dependencies are missing. Godot imports use `godot --headless --path games/yuga-native --editor --import --quit`. The handbook includes missing-tool recovery, render/runtime environment variables and package commands. Do not run every game's suite for a documentation-only change.

## Resume or delegate a task

1. Read `git status --short`, the current branch and HEAD. Preserve local changes. Use the existing isolated checkout; do not automatically switch, reset or create another worktree.
2. State one observable outcome and its backlog task ID when applicable. Choose the product above and read its relevant handbook/source section.
3. Give each worker exclusive files and a shared API/data contract. Parallelize independent work; serialize changes to shared manifests, source freezes, imports and heavy renderers.
4. Use three bounded rounds: contract and source review; implementation and counterexamples; independent integration/visual review. Add a fourth correction round only when a finding warrants it.
5. Handoff exact changed files, source commit/hashes, commands, pass/fail results, evidence paths, remaining limits and the next owner. Test reports must belong to the code being accepted.

Copyable assignment:

```text
Goal / task ID / product:
Read first: docs/START_HERE.md plus the relevant handbook section
Exclusive files and shared interfaces:
Acceptance checks and actual-render/input requirement:
Round/report checkpoint:
Return: changes, source hash, executed commands/results, evidence, limits, next step
```

The current integration bottlenecks are shared rules/elevation, two rendered native clients against authority, and accepted continuous hero motion/contact. Offline improvements provide supporting evidence; they do not close those online/production gates. Recheck the backlog's `next_packets` before assigning work.

The current visual limitations are sculpted hair, a stiff long sash, stylized drape and material richness. The underlying gameplay still needs human balance/feel review, listening review and real hardware profiling. Keep these separate from deterministic integration and recorded animation checks. The roadmap retains native authority/two-client milestones and the full production art gates.

## Known restoration limits

The committed native assets can be imported and played. The original `/workspace/tooling/yuga-art/output/rama-authored.blend` remains absent. A reproducible editable reconstruction now lives at `games/yuga-native/art/production/reconstruction-rama.blend`, with its pinned GLB input and [rebuild notes](../games/yuga-native/art/production/reconstruction-notes.md). It preserves imported merged topology/actions and packed textures, not original modeling history. General Blender edits/re-export require fresh rig/skin/animation equivalence review. The original raw Reddit collection directories were also lost during restoration: retained reports and retrieval metadata survive, but this does not recreate the missing comments. The research brief records the fresh 403 and successful official-doc checks.

Keep source, accepted evidence, attribution and user saves. Large copied release ZIPs/extractions and regenerable caches belong in scratch, with a known recovery route. See the workspace guide before deleting anything. No credentials belong in handoff documents, research archives or commits.
