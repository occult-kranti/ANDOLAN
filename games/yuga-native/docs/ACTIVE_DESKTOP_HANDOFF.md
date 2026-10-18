# Active desktop work — resume here

Updated 18 October 2026. **Mobile is deferred until the desktop quality work is done.** Read this file, the needed subsystem documentation and the exact evidence linked below; there is no need to reread the whole history.

## Goal and source

The user requested five new screen rounds followed by ten new integration/graphics rounds, six workers per round, toward an original Rama/Confluence game at the documented [quality target](DEADLOCK_QUALITY_TARGET.md). Improve the hero, map, animation, complete screen journey and package; test real edge cases, push checkpoints and remove verified duplicates. [The campaign](DESKTOP_FINISH_CAMPAIGN.md) and [90-packet ledger](DESKTOP_FINISH_CAMPAIGN.json) distinguish implementation from visual/integration acceptance. No round is completed merely by assigning six workers or passing assertions.

Branch `game/yuga-native-production`. Pushed source checkpoint `98e10cc5184ba1b51b42113496a529d8cc8f62b0` contains S1 candidates; the next checkpoint includes S2 fixes and renderer diagnosis. The public executable remains [yuga-native-ui-2026-10-18](https://github.com/occult-kranti/ANDOLAN/releases/tag/yuga-native-ui-2026-10-18), source `9e81a7c849837dea477ddb5a8c93f43665774573`. New source is not a new qualified executable. Earlier G1/G2 and UI campaigns retain their exact historical scope; pending G3–G6 work is incorporated into X1–X10.

## Current implementation and actual evidence

- **S1 launcher/camera:** clearer practice hierarchy, private shared-style roles, stronger title portrait framing. Focused launcher233 and camera18 checks pass; current-source native title/gameplay frames are being captured before composition acceptance.
- **S1 hero gold:** original linear roughness map softens the bow stripe and shoulder highlight while retaining engraving. Lead, W1 and W3 actually reviewed both matched front/profile pairs. [Gold r2](evidence/desktop-finish/S1/W1/gold-component-r2/REVIEW.md) is a bounded accepted material refinement on a diagnostic environment derivative and explicitly seeded cache, not full hero, motion, production environment or cold-launch acceptance. The earlier failed candidate remains in gold r1.
- **S1 atlas/motion/HUD:** missing raised-deck footprints restored; stale full-body release snapshot repaired; action slots show DRAWING/RECOVERING, BUSY and QUEUED from real authority. Actual new continuous-motion/atlas review remains open.
- **S2 loading:** stable lightweight presentation with real resource-progress scope, cancellation-safe ownership and no obsolete loader restoring old global state over a replacement scene. [W2](evidence/desktop-finish/S2/W2.md), [W6](evidence/desktop-finish/S2/W6.md). Loader completion means mounted scene, not GPU or first-draw readiness.
- **S2 material lifecycle:** 46 actual finished slots across12 profiles; repeated-label report accumulation fixed. Actual scene lifecycle25/25,201 source/import pins stable. [W3](evidence/desktop-finish/S2/W3.md).
- **S2 initial support:** bounded120ms acquisition blend reduces initial joint step without moving the actor/capsule or ability clocks. Actor-bound admission prevents a demonstrated bare-preview reset regression. Final30/60/120Hz matrices,39 cross-trace checks and6 release cases pass. Moving sole penetration remains unresolved (training about−26mm, moving reset about−49mm); a settled still cannot qualify continuous contact. [W5](evidence/desktop-finish/S2/W5.md).
- **S2 integrated checks:** final selected screens182, imported-rig release6, legacy boot/transitions/signals77, runner selftests12 and package/PCK244 pass (521 checks with overlapping scopes, not an art score). Exact source pins stable. Failed controls and the incorrect inherited scratch-baseline case are preserved. New suites are registered in existing CI/setup catalogs.

S1 intermittent final-host ObjectDB exit warning did not reproduce in two exact bounded verbose runs; retain [the witness](evidence/desktop-finish/S1/W2/final-host-leak/witness.json), do not invent a fix. Current GitHub run39096580645 at98e10cc failed one old action-buffer integration assertion; W6 has reproduced its raw-notice equality conflict with intentional RECOVERING/QUEUED text and is repairing the semantic assertion without changing gameplay authority.

## Native render blocker and controlled recovery

Godot4.6.3 standard, Blender4.3.2, FFmpeg and Python tools are installed. Four-CPU quota,32GB RAM, **no physical GPU**; Vulkan uses llvmpipe. Serialize heavy import/export/render on CPU0,1 with LP_NUM_THREADS=2 and BLAS/OMP/MKL=1. Coordinate short checks on CPU2/3. Godot `--max-threads` is unsupported; affinity does not limit its worker pool.

Actual GDB evidence identifies a first-draw lock/starvation cycle: main holds the shader-version mutex while waiting for a compilation group; all five worker threads wait on that mutex. W4 independently verified native function ranges/literals and the live mutex owner. [Native evidence](evidence/desktop-finish/S1/W1/native-lock-r1/REVIEW.md) and [cross-review](evidence/desktop-finish/S1/W4-native-cross-review.md) preserve exact binary/public-source identity limits. It is not evidence that shader derivatives are generally unsupported. No production shader reduction or engine patch has been promoted.

The first cache-seeded gold run completed in81.235s with two actual originals and exact matching pose/camera/light/clock controls. Cache-hit bypass can unblock component art review; **fresh cold launch remains blocked**, and uncached shader revisions may still deadlock. W1's next authorized run uses the full original G2 environment shader, exact final S1/S2 runtime, copied Godot/Mesa cache and actual title/gameplay cameras. The preserved overlay is `/tmp/yuga-final-s2-overlay-freeze-r1/receipt.json`, SHA256 `13c04ed273bdb553332c0501634d7e463ecc0150fb945b5dfc2b24abd4766f5b`; runtime motion119db2e6, loaderbcb0ff82 and finish6eb51ce8. This is staged scene API capture, not OS-input acceptance.

Reusable immutable base `/tmp/yuga-graphics-six-project`, store `/tmp/yuga-graphics-six-store`; run `tools/graphics-six/snapshot.py verify` before refresh. Do not import into that read-only shared cache. Verified local debugger `/workspace/tooling/native-debug/gdb-local` (GDB16.3); its signed-package/install receipt is retained in native-lock evidence. No global apt/tool configuration was replaced.

## Ownership and next subgoals

| Worker | Agent | Exclusive work |
| --- | --- | --- |
| W1 | ui_06_acceptance | Native diagnosis/capture, frozen-source actual graphics review |
| W2 | mobile_touch, desktop assignment | Screens/shared styles; S3 HUD readability, no authority changes |
| W3 | r3_08_groom | Hero finish/authoring; S3 optional original nocked-arrow fletching candidate |
| W4 | mobile_render, desktop assignment | Engine scheduling analysis; S3 atlas and delegated Confluence atlas-layout sections |
| W5 | r4_05_motion | Motion only during S3; investigate evidenced moving-foot contact defects |
| W6 | ui_03_loading | Loader/package/catalog; CI assertion repair and S3 mounted-scene readiness witness |

Lead owns common notices, campaign/handoff, CI setup integration, Git/publication and cleanup. No overlapping edits; serialize asset imports/exports and engine comparisons. Root has delegated only atlas construction/layout/overview sections of confluence_world.gd to W4. S3 independent components can advance while S1/S2 rendered integration is open; this is not a completed sequence of rounds.

Native content revision7/schema5 intentionally retains historical revision6/schema4 fixtures. Current binding hash is6eb51ce8; gold assets/source are unchanged by S2's report-only count fix. Browser authority, offline native play and proposed production multiplayer remain distinct. The complete roster, online authority, physical GPU performance, human feel/listening and Windows execution are separate open production gates.

## Storage, cloud setup and continuity

Context compaction is platform-managed. This handoff and source-bound evidence are the durable continuation mechanism. Do not clear workspace/source to reduce conversational context.

User-authorized cleanup freed **1,496,768,512 allocated workspace bytes** from exact historical package duplicates, plus two duplicate ZIPs on separate/tmp. Recovery archives and remote source were verified first. [Cleanup receipt](../../../docs/evidence/desktop-finish-storage-cleanup.json). New large S2 raw pose evidence is stored as deterministic gzip with exact original/encoded hashes; all samples and failed controls are preserved. Scratch originals remain until their remote recovery is verified.

Follow [cleanup guidance](../../../docs/WORKSPACE_AND_CLEANUP.md). Never delete source, editable art, `.git`, unique evidence, active tools/caches/saves or user `.design/`/root `scratch/`. Workspace has roughly3GB free; `/tmp` roughly12GB. A native engine build would need a separate bounded storage/resource plan.

Cloud environment draft was saved successfully with this handoff, desktop-only scope, native renderer limits and ownership rules. It still requires publishing in the environment UI for future activation; the running workspace was not replaced. Before the next pause/compaction, record active engine/output owner, latest checkpoint, exact unresolved gate and next action here.
