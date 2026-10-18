# S4-W3 isolated diadem import

The three inactive rail-refit GLBs import correctly in Godot 4.6.3. One isolated editor import exited 0 in 16.475 seconds; two subsequent cached-resource probes exited 0 in 2.226 and 2.110 seconds. All three logs are clean. No retry, rendering, canonical asset replacement or shared-store write occurred.

The baseline and candidate probes differ in exactly 15 fields: the three raw GLB hashes, three imported scene hashes, and three gold POSITION/NORMAL/TANGENT array hashes per LOD. Within those gold arrays, all imported nonrail rows remain byte-exact. Materials, actual texture pixels/formats/mips, UV/color/joint/weight/index arrays, all other surfaces, node transforms, full-mesh bounds, skin binds, all 164 bone names/parents/rests/poses, morphs and animation payloads match. The selected imported rail counts are 729 / 491 / 249; their stored positions match the copied source GLBs exactly.

The private import retained the canonical render/import settings and original three import descriptors, removing only `run/main_scene="res://scenes/boot.tscn"`. All 51 generated PNGs and CTEX files, plus all 54 import descriptors, match the baseline. Only three SCNs and their MD5 receipts changed. Fifty-four source-to-import bindings validate. The canonical 474 relevant files, the shared base's 1,009 files and every referenced immutable store blob remain unchanged.

The baseline near GLB, descriptor and SCN exactly match the retained 348-sample draw tape. W5 independently closed its numeric bone-index mapping through the earlier actual imported skeleton receipt: all 164 names match, including index 104 = head. That proves resource identity; the old direct-API pose replay remains distinct from new native controller execution.

The earlier source-only [receipt](receipt.json), [source report](../W3.md), generator and all its pinned files remain unchanged. This follow-up supersedes only their then-pending import/mapping status. W5's [source review](../W5/REVIEW.md) remains independently scoped.

`import-comparison-r1.json` contains the exact semantic differences, preservation checks and archive hashes. `semantic-payloads-r1.tar.gz` retains both actual probe outputs and gold arrays. `candidate-import-cache-r1.tar.gz` retains the three new SCNs/MD5s and unchanged GLB descriptors for reconstruction without another import. Commands and engine identity are retained in `import-preparation.json`, `import-run-r1.json` and `semantics-runs-r1.json`.

Still open: matched front/profile/rear rest and live cast originals, actual candidate controller/render acceptance, mid/far posed and whole-body contact, and general continuous motion. The dark hair cap/lobes remain a separate art defect. The copied candidate is review-only and has no default activation.
