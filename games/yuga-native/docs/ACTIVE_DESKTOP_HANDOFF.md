# Active desktop work — resume here

Updated18 October2026. **Mobile is deferred.** The latest user request is ten screen rounds followed by three integration rounds, six workers each. Use this file, [active plan](DESKTOP_FINISH_CAMPAIGN.md) and [78-packet ledger](DESKTOP_FINISH_CAMPAIGN.json), then only the assigned subsystem references. Prior five-screen/ten-integration planning is preserved under `campaign-history/desktop-finish-v1/`; original evidence IDs are unchanged. Existing source improvements are carried forward, not recounted as completed new rounds.

## Source and public build

Repository `/workspace/ANDOLAN`, branch `game/yuga-native-production`. Last remote-verified checkpoint before recovery is `bf50ff8ef839ed5f4c9263bbedadb53bd99eab51`; it includes S1/S2 source, warm graphics, native lock evidence, and the semantic action-buffer CI test repair. Current S3/S4/S5 fixes and their evidence survived the reconnect and are awaiting the next reviewed checkpoint.

The public executable remains [yuga-native-ui-2026-10-18](https://github.com/occult-kranti/ANDOLAN/releases/tag/yuga-native-ui-2026-10-18), source `9e81a7c849837dea477ddb5a8c93f43665774573`. A pushed candidate is not a newly qualified executable. The intended full roster/native online authority, physical-GPU performance, Windows execution and human listening/feel remain distinct open production gates. Current native play is offline.

## Current fixes and acceptance

| Area | Exact source/evidence | Disposition |
| --- | --- | --- |
| Launcher/gold | S1 launcher233 checks; camera18. [Gold review](evidence/desktop-finish/S1/W1/gold-component-r2/REVIEW.md) | Actual matched front/profile material refinement accepted; full hero remains below target |
| Full S2 graphics | [Original title/training](evidence/desktop-finish/S2/W1/scene-anchors-r1/REVIEW.md), original full masonry6e532916… | Two actual product-camera originals,63.660s, copied shader/Mesa cache; staged API capture, not cold/input qualification |
| Courtyard paving | helper `eb4335695318daedc578cc9cd7e8424d329896b36149e786ae473346b642726a`; [review](evidence/desktop-finish/S3/lead/paving-palette-r1/REVIEW.md) | Four original tint vectors reduce checker contrast; actual matched daylight pairs accepted, all shot state except image SHA exact. Night/seam quality open |
| Compact HUD/world | HUD `68e3cc06b4176cd8720a6a132ae06582a0c605ff8113a421b048d60550238ea9`, world `8d597dea33a60dbbbfecbbb98cc31d78345667053d79f69d55c8d4316973d0e9`; [W4](evidence/desktop-finish/S3/W4.md), [W2](evidence/desktop-finish/S5/W2.md) | Real live100→150→200→100 resize39/39; navigation29/29; compact31+24. Single row glyph/key/state and102px world strip preserve torso. Earlier3919px overflow, blocked scrolling and172px HUD obstruction retained. Actual final composite images pending |
| Hero guide | `a76b3d2316305efbdb001426282275795f0273db006a29bffb8d05209fc6c58b`; [S4 W2](evidence/desktop-finish/S4/W2.md) | Focus guard rejects disabled/queued/hidden/nonfocusable openers;31+9 checks. Actual scaled guide review pending |
| Loader cancellation | `a5d236a40d1513111bd1a7d92281308019cd7de13d66350ac3935b331061b483`; [S3 W6](evidence/desktop-finish/S3/W6.md) | Synchronous post-callback eligible focus retry fixes reenabled child ordering;23/23 plus unchanged end-to-end25/25. Reentry/new focus/owner replacement protected |
| Material ownership | finish `6eb51ce8f34a3d5a33deb142ca92aaa20505516b0ee8fff3ca445bcab603078a`; [S2 W3](evidence/desktop-finish/S2/W3.md) | Actual46 slots/12 profiles, report accumulation fixed;25 lifecycle checks and201 import pins |
| Grounded motion | `8c3771a343a0538d749147393d0c407b1fb377d774a91b4cf99734e4852520f8`; [S3 W5](evidence/desktop-finish/S3/W5.md) | Provisional contact guard:11 contact/57 boundary checks pass; strict comparison **25/27**.120Hz landing step+2.435mm and60Hz swing+0.228/+0.219mm remain; no complete smoothness claim |
| Optional fletching | [S3 W3](evidence/desktop-finish/S3/W3.md) | Inactive original60-triangle candidate;18+6 checks/348 clearance samples, min3.19884mm; matched actual image benefit unreviewed |

The full35-screen recovery run is preserved at34/35 suites,719/720 assertions: only an old literal `F1 overview` assertion failed against the intentional active binding plus `Map & key` label. The precise test-only correction passes22/22 on the same548 runtime files; catalog selftests21/21. Do not relabel the failed full run as an all-pass rerun. Earlier16/16 quality778 assertions plus15 audio files,75 screen and68 motion checks belong to their recorded prior source freezes. Latest known GitHub run39098704519 atbf50 failed the pre-fix end-to-end120s timeout; CI is not yet green.

## Environment recovery and native renderer

Godot4.6.3, Blender4.3.2, FFmpeg, Python and installed renderer/debugger tools survived. Four-CPU quota,32GB cgroup limit, **no physical GPU**; Vulkan uses llvmpipe. LP_NUM_THREADS=2 and BLAS/OMP/MKL=1 for raster. Godot `--max-threads` is unsupported; CPU affinity does not cap its worker pool. Old receipts retain ignored flags; new commands omit them.

Reconnection preserved the repository and its356 compiled import files, but `/tmp` initially had only380KB. The unfinished source-build PID225016, source/object tree, previous render snapshots and Mesa cache were absent. Fresh cgroup counters are not evidence of the prior outage cause. A previously pending screen-run invocation later returned completed output; preserve that specific observation without claiming global temporary-file survival. [Recovery archive](evidence/desktop-finish/G0/workspace-recovery-r1/REVIEW.md) pins retained and reconstructed inputs.

GDB proves a cold first-draw cycle in the installed binary: main holds a shader-version mutex while awaiting a worker group; all five workers wait on that mutex. [Native lock](evidence/desktop-finish/S1/W1/native-lock-r1/REVIEW.md), [independent review](evidence/desktop-finish/S1/W4-native-cross-review.md), [scheduler study](evidence/desktop-finish/S1/W4-engine-scheduling.md). Installed commit7d41c59… differs from public4.6.3 source35e80b3…; no fabricated exact-source symbols. Full production shaders remain intact; no engine patch has been promoted.

W1 reconstructed immutable `/tmp/yuga-desktop-recovery-r1/current-project`, marker `6349218e2507bbf2ed7fd7d82543d464deb7c261defed2930f87995742513a19`:1009 files,176 validated raw/import pairs,66,482,843 compiled bytes. Its headless scene-anchor preflight passes5/5. Current canonical overrides are explicit; this is a successor to S2, not identical historical S2. Original101 shader-cache payloads plus the retained two-file delta recover103 files/11,938,824bytes. **Mesa cache was lost**; new captures must say absent. No editor import was used for recovery.

W2's eight-shot child is `/tmp/yuga-desktop-recovery-r1/compact-project-r1`, marker `a02bc44bcb09cd9b80c0afd4d5a18d42a72664e23aa4961875cb572bfb39e2b5`. It exercises actual boot/title100/150/200, primary Enter to world100/150/200, F1overview200 and pause/F3guide200. Headless12/12. The first actual installed-engine attempt produced0PNGs and stopped at the120s no-progress watchdog; [failed run](evidence/desktop-finish/G0/compact-render-no-progress-r1/REVIEW.md). No live stack was captured for this attempt, so its precise cause is not independently diagnosed. Sources/cameras/clocks are recorded; no manual layout or pose repair. [Preparation](evidence/desktop-finish/S5/W2-capture-preparation/README.md).

W5 stages matching current-source pairs differing only motion119db↔8c377:120-frame full sequence at30Hz capture/60Hz physics plus40-frame landing at120Hz capture/physics. Four preflights pass, including exact callback cadence and reproduced120Hz tradeoff; actual rendering remains pending. Never replace full-body comparison with only a close crop or infer visibility of a subpixel numerical difference.

The lost unmodified public-source editor build had no verified completion. W1 is preparing a smaller **template_debug** baseline with all runtime features and explicit path overrides, followed by identical unmodified-versus-patched comparison only if failure reproduces. This omits editor tools, not renderer/runtime functions, and is not an exact installed-editor rebuild. One temporary4–6GiB tree,3GiB free-space stop floor,2h cap, two compiler jobsCPU0,1; retain verified66MB source archive and≤300MB completed binary outside/tmp. No compilation restarted merely because a prior PID vanished. A pipeline-priority change is still a conditional proposal; never unlock shader Version blindly.

## Ownership and immediate order

1. Lead pushes the recovered, reviewed source/evidence checkpoint and keeps the revised13-round ledger exact. No unrelated `.design/`, root `scratch/` or generated UID files are included.
2. W1 owns immutable source/cache reconstruction, actual capture runner and source-engine comparison. Heavy raster usesCPU2,3 while a coordinated two-job engine build may useCPU0,1; short checks must yield those lanes.
3. W2 owns screens/HUD/guide/shared style and the eight-shot capture helper. Review actual originals before more screen edits.
4. W3 owns inactive original fletching and a new review-only diadem-rail refit. Candidate GLBs may alter only the declared original rail position/normal/tangent; no canonical replacement or automatic activation. Hair cap quality remains separate.
5. W4 owns atlas/world presentation and bounded real route/collision parity evidence. No authority/collision runtime edit without an actual finding.
6. W5 owns motion and exact paired capture; strict25/27 remains open until disposition based on actual sequence and retained samples.
7. W6 owns loading/catalog/package. Current loader source is frozen; seal source-dependent tests and current CI status before release claims.

Native content revision7/schema5 retain exact historical revision6/schema4 fixtures. Finish binding6eb51ce8 matches notice/package identity. Cold launch, continuous motion, first-visible support, human review and final target quality remain open.

## Storage and continuation

Context compaction is platform-managed; this handoff and source-bound evidence preserve continuity. Keep concise active receipts rather than rereading all prior campaigns.

Verified cleanup reclaimed **1,603,674,112 allocated workspace bytes**: [package duplicate receipt](../../../docs/evidence/desktop-finish-storage-cleanup.json) and [lossless trace duplicate receipt](../../../docs/evidence/desktop-finish-s2-raw-cleanup.json). Source/art/unique accepted and failed evidence remain. Follow [cleanup rules](../../../docs/WORKSPACE_AND_CLEANUP.md), push and remote-verify recovery bytes before deleting reviewed duplicates. Do not remove active caches/build trees, installed tools, user files, `.git` or source to reduce context.

Cloud setup/recovery instructions were saved as a draft; draft saving neither publishes a snapshot nor backs up filesystem bytes. Reusable configuration needs publishing through environment settings for future activation. Preserve existing authenticated Git access; do not read uploaded token files. Before another pause/compaction, update current executable/source, active process identity, actual completed tests/images and exact next command here.
