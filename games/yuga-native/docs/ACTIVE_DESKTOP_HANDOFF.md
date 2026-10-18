# Active desktop work — resume here

Updated 18 October 2026. **Mobile is deferred by the user until the desktop quality work is done.** Its researched roadmap remains available; no mobile implementation is authorized by this active packet.

## Current request and state

Implement five new screen rounds, then ten new integration/graphics rounds, six workers in each; stress and edge test as work lands; improve the original hero, map, elements, buttons, loading and whole package; push checkpoints and remove only verified unnecessary storage. The plan and live queue are [DESKTOP_FINISH_CAMPAIGN.md](DESKTOP_FINISH_CAMPAIGN.md) and [DESKTOP_FINISH_CAMPAIGN.json](DESKTOP_FINISH_CAMPAIGN.json).

Branch: `game/yuga-native-production`. Prior HEAD `0fb96d108b1d886a4ebf84d3b5140abca3905465` published mobile documentation only. G1/G2 desktop source candidates and exact logs are checkpointed at remote-verified `613ff5ca84313edfbcc2a70987919fa03bed5226` (work checkpoint, not a qualified release). Five S1 source components are frozen with focused tests; W1 is reviewing gold comparisons while W4 prepares a derivative-free, feature-preserving shader candidate. S1 visual/integration acceptance remains pending. The public executable remains the reviewed `yuga-native-ui-2026-10-18` release from `9e81a7c`; do not relabel it as the current candidate.

G1 of the earlier six-round campaign has actual image review and open art findings. G2 has six component reports, numerical checks and an optional inactive hair helper; integrated render acceptance remains open. Pending G3–G6 work is carried into the new integration queue, never counted as already completed. The older U1–U5/I1–I3 and fifteen-role campaigns remain historical.

## Current implementation evidence

- Rama skin/rig/GLBs remain exact; original hair/gold roughness maps were integrated in G1. Optional G2 seven-layer upper-nape helper has 26 rig checks and historical triangle clearance but is **not active**; needs same-light off/on review.
- G1 bow-action entry handoff and G2 measured idle-foot support have focused evidence. G2 soles numerically moved from +50.571 mm to +0.572 mm without changing the player root. Continuous actual rendered contact/transition quality is still open.
- Shared HUD type/readability, glyphs, courtyard/world lighting/stone shading and shaped infantry are current candidates. S1 audits identify title hierarchy, strong gold glare, flat cloth/world planes, missing atlas deck footprints, stale full-body release pose and READY labels during action lock.
- Lead current checks: 74 VFX +269 contract +54 source assertions passed. Content revision7 is an intentional native-only migration retaining exact historical6 fixtures; browser wire2/3v3 and proposed6v6 remain separate.
- G0 packaging checks: 287 historical +109 schema5/PCK +108 security checks passed. Exact schema4 parent and old binding remain preserved; schema5 validates new source assets. The optional-hair notice addition has a deliberate pin update; old G1 notice bytes remain in evidence.

Detailed records are under `docs/evidence/graphics-six/G1`, `G2` and `docs/evidence/desktop-finish/G0`. Do not rerun all old suites or read the entire archive to begin a focused task.

## Rendering gate and environment

Godot4.6.3 standard, Blender4.3.2, Python tools and FFmpeg are installed. Cloud CPU quota4, RAM32GB; **no physical GPU**, Vulkan is llvmpipe. Use one heavy lane: CPU0,1 and LP/BLAS/OMP threads2/1/1; CPU2/3 only for coordinated short checks. An unsupported `--max-threads` flag was removed from the new focus runner; CPU affinity does not itself cap Godot's worker pool.

G2 focus rendering stalls before first draw. Original900s and instrumented130.505s failures produced zero images. The latter reached only `before_initial_draw6`, tree unpaused; geometry/observer/camera callbacks were not reached. Two headless preflights passed (two support observations and60 entry/cancel observations), which are not rendered evidence. Raw failures are retained in `G2/lead` and `G2/focus-diagnostic-r1`.

Renderer owner `ui_06_acceptance` is testing bounded immutable derivatives. Worker0 crashed; worker1, separate render-thread and the earlier successful groom harness stalled. Disabling only EnvironmentSurfaceFinish produced two actual Forward+ originals (5 checks, 88.437 seconds), reviewed by lead; full finish with only derivative relief removed still stalled. The new environment binding/shader is implicated, but the precise cause remains open. Minimal full-map body rendered; restoring the G1 mineral wash stalled again; replacing its final explicit `fwidth` with constant detail rendered two originals in108.841seconds, 6/6checks including corrected active-camera identity. Thus explicit shader derivative use is implicated on this software renderer. W4 is replacing derivative-dependent detail with original mipmapped texture data; diagnostic reductions remain unqualified for production. No diagnostic reduction is promoted as final graphics. Preserve exact diagnostic records and report failures. Do not silently lower product graphics, remove validation, change engine bytes or substitute unrelated footage.

Reusable source snapshot: `/tmp/yuga-graphics-six-project`; immutable import store `/tmp/yuga-graphics-six-store`. `tools/graphics-six/snapshot.py verify` before refresh; source imports happen only in canonical project. Existing G1 Mesa cache seed: `/tmp/yuga-g1-native-r1/user/cache/mesa`. Snapshot/source overlays and renderer changes must be explicit in receipts. Renderer owner coordinates all new runs.

## Ownership

| Worker | Owner | Exclusive area |
| --- | --- | --- |
| W1 | `ui_06_acceptance` | Renderer diagnosis, capture tooling, independent acceptance |
| W2 | `mobile_touch` (desktop assignment) | Launcher/shared UI styles, then screen navigation |
| W3 | `r3_08_groom` | Hero finish/authoring and matched candidate reviews |
| W4 | `mobile_render` (desktop assignment) | World/atlas/units, shared environment presentation |
| W5 | `r4_05_motion` | Hero motion and combat HUD states |
| W6 | `ui_03_loading` | Loading, transitions, packaging and payload checks |

Lead owns shared rule/content/asset notices, campaign ledger, scene composition/caller integration, Git/publication and cleanup. Freeze interfaces before parallel edits; serialize shared manifests/imports/exports. Names inherited from earlier work do not imply mobile tasks are active.

## Storage and continuity

The user explicitly authorized cleanup. Follow [workspace guidance](../../../docs/WORKSPACE_AND_CLEANUP.md). Never delete `.git`, source, editable art, unarchived originals, installed tools, saves or user `.design/`/root `scratch/`. Review only explicit historical package extractions or exact duplicates; retain recovery ZIPs and verify every file before deletion. Cleanup completed: 1,496,768,512 allocated workspace bytes freed from exact duplicate historical package extractions; two duplicate ZIPs freed additional space on separate `/tmp`. Current receipt: `docs/evidence/desktop-finish-storage-cleanup.json` at repository root.

Context compaction is managed by the platform. This file replaces repeated history reading, not the source of truth. At each round update the ledger with exact files/hashes, tests actually executed, actual image/input/motion review, rejected candidates and remaining gates. Before stopping or compaction, record the active engine/process/output owner and next command. Do not claim Deadlock-level art, GPU performance, native online play or full-roster completion from a round count.

## S1 current component checkpoint

W2 launcher:233 clean assertions; W3 gold:29 source +54 material +12 imported-map checks; W4atlas:32 clean assertions; W5motion/HUD:30 clean assertions; W6boot/package:334 clean assertions; lead titlecamera:18 clean projection/ownership checks. These scopes overlap and do not sum to a visual-quality certificate. W2 host tests predate the final W6 loader guard; lead final-host repeat passed27 assertions but logged an ObjectDB exit-leak warning. W2 is investigating the exact verbose instance instead of hiding it. Gold actual matched capture is active on CPU0,1; canonical imports complete and light tests use CPU2/3.

Final source hashes and meaningful rejected tests are in each S1/W*.md report. Hero schema5 has an intentional12-dependency closure for the new map; schema4history remains exact. No updated executable is published yet.
