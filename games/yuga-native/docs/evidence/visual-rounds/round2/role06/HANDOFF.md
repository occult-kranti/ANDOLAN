# R2-06 capture handoff

The bounded R2 capture contract is complete: **55 baseline and 55 final candidate
originals**, plus three geometry-only previews, four one-variable diagnostics and
two metadata-reconciliation originals. The final source reconciliation passed.
Root owns promotion; this role changed capture tools and evidence only.

| Evidence | Baseline | Candidate | Originals per source |
| --- | --- | --- | ---: |
| Courtyard day/night | `baseline/courtyard/` | `candidate/courtyard/` | 10 |
| Confluence stone day/night | `baseline/stone/` | `candidate/stone/` | 2 |
| Confluence mixed coast/architecture | `baseline/foliage/` | `candidate/foliage/` | 2 |
| Adjacent blink/Kodanda/Piercing cancellation | `baseline/continuity/` | `candidate/continuity/` | 36 |
| Five actual late-windup face/neck poses | `baseline/actions-corrected/` | `candidate/actions-corrected/` | 5 |

Use the `actions-corrected` directories. The earlier `actions` directories retain
cropped originals and explicit framing rejections. The corrected camera follows
the paused posed-head origin at 42° FOV with the same metric offset for both
assets. A CPU projection gate checks 18,696 imported face/lip/head/neck vertices;
independent original-pixel review remains required and was completed by R2-15.
The hand/ribbon partially occludes the jaw in some ordinary action poses.

The 36-frame takes sample normal runtime updates at 30 Hz for 1.2 seconds.
Preparation advances the public facial updater 181 times while the world is
paused; this is explicitly staged clock preparation. Kodanda actually releases,
Piercing actually cancels, and that cancelled cast produces no release/impact.
Every adjacent render frame is retained. Silent MP4s are viewing conveniences;
the original PNGs and receipts are authoritative. R2-15 reviewed all 72 adjacent
originals and found the mouth and chin visible throughout. Lower neck/chest may
cross the frame border. No ordinary-speed playback or measured hardware FPS is
claimed.

## Source identity and intentional differences

Baseline is exact commit `0437ea91edf6989ff78c1eeadb3661f4825b60f2`.
Geometry-only previews in `candidate/form-only/` use corrected R6 forms with
baseline lights. Final candidate captures combine those forms with directional
sun angular distance **0** in both actual worlds, replacing .7 in the courtyard
and .6 in Confluence. Bias .2/.35, other lights/exposure, materials, viewport,
camera, pose and LOD remain matched. The title portrait fill is off.

The roughness-mipmap and SSS-off diagnostics did not remove the residual stipple.
They were not included in the final candidate. TAA was diagnostic only and was
not promoted. Zero-angular lighting improves the observed stipple with the
explicit cost of harder shadows. The material and lighting reviews retain the
remaining neck pattern and broad cheek/neck shadows as limits.

All original full-set captures retain the originally imported R6 pins. A later
Khronos check found stale NORMAL/TANGENT accessor bounds in mid/far. The final
metadata-only correction is reconciled in `reconciliation/reconciliation.json`:

| LOD | Final source SHA-256 |
| --- | --- |
| Near | `140f8ff3695bb3d28bd894cb74bca8cd5f1756bbffcf59dad6c4630f377c351a` |
| Mid | `27d998d924d2732b13bc8e18c3e3ec1ce9d58f0408bf3fda1ff0613cf32cba9f` |
| Far | `ea9818e1464c9b6bc077ae83f8354a6357fb19d2a18fc84b2deb65c58aff901a` |

The reconciled scratch project is
`/workspace/scratch/visual-round2/capture-final-project-r3`. All three GLB BIN
chunks match the captured versions. Fresh import succeeded without errors or
warnings. Actual loaded mesh/morph arrays, AABBs, skin binds, skeleton data,
animations and node transforms match exactly. Full serialized resource
properties also match after resolving generated texture aliases and removing
regenerated node unique IDs. Raw imported cache hashes remain recorded: mid/far
cache bytes differ because of those IDs. The full text resources are preserved
in `reconciliation/full-imported-properties.tar.gz` with verified member hashes.
The matched before/after framebuffer is byte-identical:
`93a2bad8c0e6f5e99c39ceface2870c272a955e47fda5980ff6ecc39b880bffc`.
No old source or capture report was rewritten.

## Checks and retained failures

- Eight affected stock suites: **424/424**.
- Actual imported facial runtime: **73/73**; independent CPU deformation:
  **15/15**, 50 samples, exact held ring and zero attachment gaps.
- Corrected imported lifecycle: **81/81**, repeated successfully after the final
  bounds correction.
- Every producer receipt, raw PNG hash, archived harness and frozen source pin
  is rechecked in `archive-audit.json`. `comparison.json` indexes all matched
  control comparisons; `run.json` records completion and scope.

The rejected paused-cast attempt, 36-frame back-facing attempt and ten cropped
action originals remain preserved. The failed lifecycle fixture expected the
wrong LOD at 8 m; role13 retains that failure and its corrected 4 m projection
test. The first resource-probe parser error is preserved in reconciliation.

The historical `foliage` station name does **not** establish dark-foliage
contrast: surrounding pixels show coast and architecture. The optional indigo
station, frontal gameplay-scale matrix, independent blink-side/aim extremes,
all-action continuous reels, moving camera/cascade tests and consumer-GPU
performance remain outside this bounded capture. R2-15 provides the art verdict.

All heavy jobs used CPUs 2,3 and two llvmpipe threads. Headless checks used CPUs
0,1. The frozen R2 projects exclude ongoing R3/R4 and UI working-tree changes.
No commit, push, runtime promotion or deletion was performed by this role.
