# Start here: project and agent handoff

**Active desktop work:** [resume handoff](../games/yuga-native/docs/ACTIVE_DESKTOP_HANDOFF.md) → [ten screen rounds + three integration rounds](../games/yuga-native/docs/DESKTOP_FINISH_CAMPAIGN.md) → [78-packet execution ledger](../games/yuga-native/docs/DESKTOP_FINISH_CAMPAIGN.json). The user has deferred mobile until desktop quality work is complete. The active 78-packet campaign tracks actual screen, hero, world and motion acceptance. Source checkpoints and the public UI preview have separate qualification records; the commercial graphics target remains open.

For native UI work, read [YUGA PRODUCT](../games/yuga-native/PRODUCT.md), [DESIGN](../games/yuga-native/DESIGN.md) and the [pinned Impeccable application contract](../games/yuga-native/docs/research/impeccable/README.md). The root product/design files belong to the separate browser game.

Updated 18 October 2026. Start here, then open only the subsystem assigned to your task. This repository contains separate native, browser and protest games.

**Deferred mobile planning track:** [YUGA 5v5 mobile roadmap](../games/yuga-native/docs/MOBILE_PRODUCTION_ROADMAP.md) → [code/stack decisions](../games/yuga-native/docs/mobile/CODE_AND_STACK_DECISIONS.md) → [108 planned implementation packets](../games/yuga-native/docs/MOBILE_PRODUCTION_BACKLOG.json). Six completed research assignments cover original mobile controls/art/maps/services and device qualification. This is planning evidence, not a playable Android/iOS release or completion of the separate native G1–G6 graphics campaign. When mobile work resumes, start at M1; do not assume the existing native 6v6 proposal or browser protocol 2 implements 5v5.

## The current build in one minute

The active product is **YUGA native**, an original mythology-inspired third-person game under `games/yuga-native/`, on `game/yuga-native-production`. It has one Rama hero with a bow and four abilities shared by courtyard training and offline Confluence practice.

**The active campaign has 14/78 accepted scoped packets and 0/13 complete rounds.** The [active handoff](../games/yuga-native/docs/ACTIVE_DESKTOP_HANDOFF.md) owns the current source, six-worker queue and exact next gates. The earlier [48-assignment screen campaign](../games/yuga-native/docs/SCREEN_CAMPAIGN.json) and [three fifteen-role visual rounds](../games/yuga-native/docs/VISUAL_ROUNDS_2_4_EXECUTION.json) retain their separate outcomes.

**Published preview:** [desktop finish preview](https://github.com/occult-kranti/ANDOLAN/releases/tag/yuga-desktop-finish-2026-10-18), source `96d5b9cd3114b9732f7dc80433b1ca0a1d4a9b12`, public 18 October 2026 at 11:17:53 UTC. The exact extracted Linux archive passed warm and independent fresh-user cold native input. Independent review opened all 59 original screens and passed 152 journey/raw checks. All five public assets were downloaded and byte-verified. [Publication](../games/yuga-native/docs/evidence/desktop-finish/published/release-r4/REVIEW.md), [package execution](../games/yuga-native/docs/evidence/desktop-finish/package-native-review/W1-patched-r1/REVIEW.md), [export identity](../games/yuga-native/docs/evidence/desktop-finish/package-export-r4/W6/receipt.json) and [independent download audit](../games/yuga-native/docs/evidence/desktop-finish/published/W5-public-download-r4/REVIEW.md) own their exact scopes. Windows remains unexecuted; software-rendered captures do not establish hardware FPS, listening or human game feel.

The [earlier UI preview](https://github.com/occult-kranti/ANDOLAN/releases/tag/yuga-native-ui-2026-10-18) remains source `9e81a7c` with its own [historical publication receipt](../games/yuga-native/docs/evidence/ui-campaign/I3/published/REVIEW.md). Later evidence-only commits never relabel a released package's source.

**Play:** choose **Confluence** or **Bow training**, then the primary action. LMB draws/shoots; Q pierces, E steps, C places a protective field and X fires three paced arrows. R reloads; F/G fly and grapple. F3 opens Rama’s guide, F2 opens Help/remapping, Escape pauses, and F5 resets practice. Enemy siege blasts damage Rama; defeat respawns him after three simulation seconds. Saved bindings replace these defaults.

Confluence is an offline 140 × 260 m world with three lanes, local armies, capture/supply relays, core outcomes and day/night lighting. The older fourteen-invocation catalogue is a separate study through the existing avatar; the 24-second duel film has its own authored actors. Neither establishes fourteen finished native heroes.

The intended production game remains **6v6, fourteen heroes, three lanes and an 18-minute match**. Native online matches, shared elevation authority, the full roster, human playtesting, physical-GPU profiling and Deadlock-level art/motion quality remain open. Small HUD text, foot support, garment contact and abrupt cast-entry motion retain explicit limits. Use the [visual handoff](../games/yuga-native/docs/VISUAL_CAMPAIGN_HANDOFF.md) for current art evidence and the [reuse consultation](../games/yuga-native/docs/research/community-reuse/README.md) for source research and next production goals.

Earlier [Mythic](../games/yuga-native/docs/evidence/mythic-published/REVIEW.md), [Triad/siege](../games/yuga-native/docs/evidence/triad-published/REVIEW.md) and [Rama milestone](../games/yuga-native/docs/RAMA_HERO_MILESTONE.md) reports retain their original sources and acceptance scope. Do not substitute historical reports for a new source or package check.

## Read by purpose

| Need | Start with | Then open only if relevant |
| --- | --- | --- |
| Build, change or test native YUGA | [Build handbook](../games/yuga-native/docs/BUILD_HANDBOOK.md) | Its task-to-file and test matrices |
| Verify current screens or package | [Active desktop handoff](../games/yuga-native/docs/ACTIVE_DESKTOP_HANDOFF.md) | Current exact export, execution, original-image and public-byte receipts |
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

The current visual limitations include solid-looking hair, a glossy sash, stylized drape, restrained facial expression and material richness. The material-frame finding and source-bound reviews are linked from the quality-pass handoff. The underlying gameplay still needs human balance/feel review, listening review and real hardware profiling. Keep these separate from deterministic integration and recorded animation checks. The roadmap retains native authority/two-client milestones and the full production art gates.

## Known restoration limits

The committed native assets can be imported and played. The original `/workspace/tooling/yuga-art/output/rama-authored.blend` remains absent. A reproducible editable reconstruction now lives at `games/yuga-native/art/production/reconstruction-rama.blend`, with its pinned GLB input and [rebuild notes](../games/yuga-native/art/production/reconstruction-notes.md). It preserves imported merged topology/actions and packed textures, not original modeling history. General Blender edits/re-export require fresh rig/skin/animation equivalence review. The original raw Reddit collection directories were also lost during restoration: retained reports and retrieval metadata survive, but this does not recreate the missing comments. The research brief records the fresh 403 and successful official-doc checks.

Keep source, accepted evidence, attribution and user saves. Large copied release ZIPs/extractions and regenerable caches belong in scratch, with a known recovery route. See the workspace guide before deleting anything. No credentials belong in handoff documents, research archives or commits.
