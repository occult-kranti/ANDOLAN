# Start here: project and agent handoff

Updated 17 October 2026. This is the short entry point for a new chat, contributor or subagent. Start here and open only the subsystem assigned to your task; the repository contains several games and historical experiments.

## The current build in one minute

The active production track is **YUGA native**, an original mythology-inspired third-person team game under `games/yuga-native/`, on `game/yuga-native-production`. Its current [downloadable Triad and siege preview](https://github.com/occult-kranti/ANDOLAN/releases/tag/yuga-traversal-armies-2026-10-17-triad-siege) is source **`ae33db4520bd14fe7b38aed173b764de7a7424d5`**. Later documentation commits do not replace that release source.

The native preview has Rama training, a separate 24-second animated duel film, and offline three-lane Confluence practice: a 140 × 260 m world, flight/grappling, five army roles including siege vehicles, three capture/contest/supply relays, local gold/core outcomes, original sound, day/night lighting and saved/remappable controls. Press **Escape → Visit Lotus relay** for the centre approach, or **Siege practice** for the six-unit drill; F5 restores ordinary waves and resets relays. Supply restores capped troop health and hero arrows; native hero health/death is not implemented.

Both CI workflows passed. All **77 public assets**, **233 tagged runtime sources** and three decoded, source-matched six-second captures were independently verified. The exact downloaded Linux build passes forward Lotus entry, capture, capped arrow supply, pause, ordinary reset, siege entry and title return. Windows remains unexecuted. [Public evidence and limitations](../games/yuga-native/docs/evidence/triad-published/REVIEW.md). The earlier [62-asset siege review](../games/yuga-native/docs/evidence/siege-published/REVIEW.md) remains historical evidence for its own release.

The intended game is **6v6, fourteen heroes, three lanes and an 18-minute match**. Native online matches, the complete native hero roster, production character art/animation, Windows execution and physical-GPU performance remain open. The browser prototype has different rules. Concept paintings are art direction, not captured gameplay. No Deadlock/Overwatch/Dota 2 client binaries or commercial models were recovered here.

See the [Triad milestone](../games/yuga-native/docs/TRIAD_MILESTONE.md) for current test/capture/release status and the next five production packets. The verified [TF2 source study](../games/yuga-native/docs/research/TF2_REUSE_STUDY.md) is behavior research; no TF2 code or assets were imported.

## Read by purpose

| Need | Start with | Then open only if relevant |
| --- | --- | --- |
| Build, change or test native YUGA | [Build handbook](../games/yuga-native/docs/BUILD_HANDBOOK.md) | Its task-to-file and test matrices |
| Choose the next milestone | [Production roadmap](../games/yuga-native/docs/FULL_GAME_PRODUCTION_ROADMAP.md) | [Dependency/status ledger](../games/yuga-native/docs/ROADMAP_BACKLOG.json), [design master](../games/yuga-native/docs/GAME_DESIGN_MASTER.md) |
| Use criticism, mythology, books or open-source references | [Research brief](../games/yuga-native/docs/research/RESEARCH_BRIEF.md) | The exact source/report linked in the relevant row |
| Verify the current feature milestone | [Triad milestone](../games/yuga-native/docs/TRIAD_MILESTONE.md) | [Practice UX](../games/yuga-native/docs/SIEGE_PRACTICE_UX.md), source-pinned tests, actual render and published-package review |
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

Small follow-ups remain: close continuous vehicle/art review, crowded warning readability, neutral-pad contrast and a smoother initial world-loading transition. Triad corrects the Help footer's round-reset wording and the Lotus visit's approach direction. Keep these separate from the full-game production gates.

## Known restoration limits

The committed native assets can be imported and played. Rebuilding Rama from editable art additionally expects `/workspace/tooling/yuga-art/output/rama-authored.blend`, which is absent in this restored worker; recovering that source is separate from running the committed GLB. The original raw Reddit collection directories were also lost during restoration: retained reports and retrieval metadata survive, but this does not recreate the missing comments. The research brief records the fresh 403 and successful official-doc checks.

Keep source, accepted evidence, attribution and user saves. Large copied release ZIPs/extractions and regenerable caches belong in scratch, with a known recovery route. See the workspace guide before deleting anything. No credentials belong in handoff documents, research archives or commits.
