# Active desktop work — resume here

Updated 18 October 2026. **Desktop first; mobile deferred.** Work in `/workspace/ANDOLAN`, branch `game/yuga-native-production`. Read this handoff → [13-round plan](DESKTOP_FINISH_CAMPAIGN.md) → [78-packet ledger](DESKTOP_FINISH_CAMPAIGN.json), then only the assigned subsystem. Earlier 48-assignment screen and 45-assignment visual campaigns retain their own evidence; do not recount them as new rounds.

## Current source and package

| Identity | State |
| --- | --- |
| Runtime/package source | `96d5b9cd3114b9732f7dc80433b1ca0a1d4a9b12`, pushed and remotely verified. Adds guide/controls focus recovery and explicit patched-runtime packaging to the accepted f8 slice. [CI passed all 37 steps](https://github.com/occult-kranti/ANDOLAN/actions/runs/39119998695); [receipt](evidence/desktop-finish/checkpoint-96d5b9cd-ci/W3-native/receipt.json). Console totals were not independently retrieved because the log redirect was blocked. |
| Exact new archives | `/workspace/scratch/yuga-desktop-integrated-package-r4/build`. Linux SHA `27c36e5523643c647b245614721c0160b3d1548bf6da851d922886cffc180d0e`; Windows `34d8c19d30f7cafe6ad56247c2524d09c15f307cc0cde20572a56eb3d29b1fc6`. [Export/source/archive evidence](evidence/desktop-finish/package-export-r4/W6/receipt.json). |
| New archive execution | Warm route passed in 263.645 seconds with 40 originals; separate fresh-user cold passed in 305.551 seconds with 19. Both native Quit 0. [Owner](evidence/desktop-finish/package-native-review/W1-patched-r1/receipt.json) and [independent review](evidence/desktop-finish/package-native-review/W6-r4-independent-r1/receipt.json): all 59 originals opened and 152 journey/raw checks passed. |
| Public executable | [Desktop finish preview](https://github.com/occult-kranti/ANDOLAN/releases/tag/yuga-desktop-finish-2026-10-18), source `96d5b9cd`, public 18 October at 11:17:53 UTC. [All five public files independently verified](evidence/desktop-finish/published/W5-public-download-r4/receipt.json). |

The product is an **offline Rama slice**. Native multiplayer, the full roster, commercial graphics quality, physical-GPU profiling, Windows execution and human listening/full-speed feel remain open. No supplied proprietary Deadlock/Overwatch clients were analyzed or recovered. Concepts are design targets; actual native originals own visual evidence.

## Accepted changes and limits

The integrated slice includes readable title/compact layouts, keyboard overview and actual hero heading, concise loading recovery, delayed-volley feedback, title fill light, distant paving filtering, crown/sash UV repairs and a bounded landing-contact improvement. [The campaign ledger](DESKTOP_FINISH_CAMPAIGN.json) links their original evidence. Whole-hero/world quality remains open: the current hair is solid-looking, buildings repetitive, paving seams dotted, and sustained locomotion unreviewed.

The new focus repair handles missing, hidden, disabled and freed entries and removes a void-expression engine error. [77 integrated checks](evidence/desktop-finish/next-focus/W5-integrated-r1/REVIEW.md) plus 35 catalog checks and [independent review](evidence/desktop-finish/next-focus/W6-integrated-review-r1/receipt.json) passed. The new exact package route supplies separate OS-input evidence.

[Explicit patched-engine packaging](evidence/desktop-finish/package-runtime-priority/W6-r1/receipt.json) passed 50 focused checks, five compatibility checks and [23 independent checks](evidence/desktop-finish/package-native-review/W3-patched-runtime-r1/receipt.json). The packager preserves default unmodified behavior and declares the selected variant, patch, source, build and license evidence. Source/archive checks are separate from execution.

The canonical hero remains accepted crown+sash UV: near `db4b2ec7`, mid `b5949c9d`, far `aef8ae58`; raw GLBs and compiled imports are synchronized. R4/R5/R6 hair and compact shoulder are inactive. R6 passed source/import/control checks but failed all-view aesthetic review: the rear shelf, separate nape mass and pointed locks remained. [Actual R6 rejection](evidence/desktop-finish/hair-collected-r6/W1-native-r1/receipt.json) → [whole-hair artist brief](../art/hero-finish/hair-sculpt-design/ARTIST_BRIEF.md). Use a new gathered-flow design and four-view coarse clay review before another production GLB.

The actual floor-SSAO diagnostic was negative: four floor ROIs and three contact ROIs were pixel-identical with AO on/off; dotted seams remained. [Originals, initial helper failure and corrected controlled run](evidence/desktop-finish/G0/W1-title-floor-ssao-r1/receipt.json) are retained. Do not remove AO or infer that AO has no effect everywhere.

## Active six-worker queue

| Owner | Current gate |
| --- | --- |
| W1 `ui_06_acceptance` | Sole heavy lane: r4 warm/cold is sealed; run the actual frontage comparison, then four-view whole-hair clay/shoulder/motion in agreed order. |
| W2 `mobile_touch` | Original four-view continuous-hair concept; whole-hair coarse clay shape on the actual head/crown envelope. No tube-connector parameter loop or canonical promotion. |
| W3 `r3_08_groom` | CI96 archived; explicit unique-art/evidence backup inventory and complete workspace repository discovery. Lead owns staging/commit. |
| W4 `mobile_render` | One lane-frontage module: recessed closed door/windows, stronger storey/plinth shapes and matching collision. [Native 39/39](../art/world-finish/lane-frontage-r1/native-receipt.json) passed; [three-view recipe](../art/world-finish/lane-frontage-r1/RENDER_RECIPE.md) is unexecuted. |
| W5 `r4_05_motion` | Transport and public-download audit passed. Sustained walk/run-to-stop/jump recording remains prepared but unexecuted. |
| W6 `ui_03_loading` | Exact r4 export/execution/transport closure passed. Prepare exact recoverable expanded-package cleanup; no removal before remote backup and owner release. |

Lead owns shared integration, visual acceptance, roadmap, checkpoints and cleanup. The campaign remains **14/78 accepted scoped packets and 0/13 complete rounds**. A test suite, prepared source, rejected candidate or task count does not complete an art gate.

Frontage source is isolated under `art/world-finish/lane-frontage-r1`. It replaces only `CityArt/block-2`, retains the body ID/layer/mask/navigation/broad bounds, and deliberately changes local collision to the exact closed rendered triangles. The old flat box would leave a ghost standoff at recesses. Native tests cover the actual 0.65 m player capsule, closed depth, material sharing, remove/reset and external-deletion cleanup; both reproduced ownership failures remain. The quiet other three facades must pass overview review before adoption. No new textures/lights, canonical map edit or actual raster acceptance is implied.

## Runtime and rendering

Use the [build handbook](BUILD_HANDBOOK.md). Godot 4.6.3, Blender 4.3.2, FFmpeg and Python are installed. This cloud has a four-CPU quota, 32 GB memory and **no physical GPU**; Vulkan uses llvmpipe. Heavy raster/import work is serialized on CPU0,1 with `LP_NUM_THREADS=2`; short native checks use CPU4 and bounded source work CPU3. `--max-threads` is unsupported.

| Engine | Role / SHA-256 |
| --- | --- |
| `/opt/godot/4.6.3/Godot_v4.6.3-stable_linux.x86_64` | Official exporter/editor; `f64d4ed19fc9df9440321653fcc80df8c6e365ba7b6de0a29e2cfa9fa71bfeb3` |
| `/workspace/tooling/godot-public-4.6.3/binaries/godot-4.6.3-public-template-debug-unmodified` | Public unmodified template; `dce0422d5a2ef2e00494a9b7689613d14bd1fcc4c07eac21c7e91721adcf730f` |
| `/workspace/tooling/godot-public-4.6.3/binaries/godot-4.6.3-public-template-debug-pipeline-low-priority` | Explicit r4 Linux runtime; `e69af4f6f07876a83e49a02a86928db00993f88594c05ae589e4021d6916d54e` |

Both public builds use source `35e80b3a8822a9df9be390814b62f44c0a9c69e8`, not the installed editor's exact commit. The patch changes one pipeline-task priority; it does not reduce renderer features or shader quality. [Source diagnosis](evidence/desktop-finish/G0/W3-cold-scheduling-r1/REVIEW.md) distinguishes observed worker waits from a proven same-instance mutex cycle.

The preceding f8/dce package passed warm review but failed its original 600-second cold bound. Two separate f8/e69 cold diagnostics passed in 312.066 and 306.083 seconds; those external-binary diagnostic runs do not qualify r4. [Failed archive](evidence/desktop-finish/package-native-review/W1-public-r1/REVIEW.md), [first diagnostic](evidence/desktop-finish/package-native-review/W1-e69-diagnostic-r1/receipt.json), [second diagnostic](evidence/desktop-finish/package-native-review/W1-e69-diagnostic-r2/receipt.json) remain sealed. An earlier unmodified control also succeeded; no universal repair/performance claim follows.

Warm captures declare cache seeds; cold captures use fresh preferences and empty caches. The current r4 executes its actual extracted sibling binary/PCK, not an external override. Before launch, an independent counterexample exposed an omitted-member gap in a mutable extraction report. The successor pins that report's exact SHA before parsing; the original failure and missed review remain historical.

## Release and next sequence

[The r4 preview](evidence/desktop-finish/published/release-r4/REVIEW.md) is public and all five fresh downloads match the qualified bytes. Both ZIPs pass 79 member CRC/payload checks; both PCKs pass 543 internal entry checks each, and all 11 Linux engine-proof files match. [Actions 39122371874](https://github.com/occult-kranti/ANDOLAN/actions/runs/39122371874) transported the exact files to the fixed draft; root published separately. It performed no rebuild. Later evidence-only commits do not change the executable's `96d5b9cd` identity.

1. Review one frontage in ordinary play, eye-height contact and overview. Its source/native checks pass; actual product images are the next gate.
2. Review the continuous-hair coarse clay from four angles, separately from compact shoulder. Keep rejected R6 and unreviewed candidates inactive. The [new generated concept](../art/hero-finish/hair-sculpt-design/concept-r1/continuous-swept-hair-concept-r1.png) is a direction, not a runtime screenshot.
3. Execute sustained walking, natural run-to-stop and jumping without resets inside measured intervals. [Prepared route](evidence/desktop-finish/next-motion/W5-locomotion-preparation-r1/) is not an actual recording.
4. Reuse the accepted combined slice for remaining scale, cancellation, motion and stress gates; build and requalify a new exact package after runtime/art changes.

Publication closes two bounded I03 packets for this offline preview. The other I03 roles and I01/I02 dependencies remain open; no full round or commercial quality gate is closed by this release.

## Storage and continuity

Recorded desktop cleanup reclaimed **10,198,446,080 allocated file bytes** at the times of the operations; this is not net free space. Exact old r2/r3 expanded packages and duplicate Windows PCKs were removed only after remote backup and owner/hash checks. The formerly partial package checkout was subsequently fully restored: `/tmp/yuga-desktop-integrated-package-r1/ANDOLAN` is clean detached `96d5b9cd` with 18,038 tracked files and 552 runtime inputs. It was used for r4 export. Do not repeat restoration from stale partial-state notes.

`/tmp` has little reserve. Put all new archives, extraction, captures, XDG/cache state and downloads in `/workspace/scratch`. Preserve unique sources, accepted/rejected originals, tools, saves and meaningful failures. Follow [workspace guidance](../../../docs/WORKSPACE_AND_CLEANUP.md); no broad clean/cache wipe/prune. The pushed d1 [inactive-art backup](evidence/desktop-finish/inactive-art-backup-r1/README.md) preserves R4/R5/shoulder and exact duplicate mappings. New R6, AO, frontage and r4 evidence need a separately verified backup checkpoint.

The saved [cloud configuration draft](../../../docs/evidence/desktop-finish-current-cloud-r2/README.md) still pins d1 pending the next checkpoint. Preserve installation/network settings; update start instructions after complete repository discovery. Saving a draft is not a filesystem backup or published snapshot; Environment Settings → Save → Publish activates it. Context compaction is platform-managed; this handoff, ledger and exact commits carry continuity.
