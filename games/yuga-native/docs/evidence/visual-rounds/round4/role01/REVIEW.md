# R4-01 — source skin continuity and archived motion limits

Product: YUGA native. Current source commit: `495fae3aad59bfcce22506cc27f9d042741cd4ab`.

The retained R7 skin needs no seam resculpt for the measured boundaries. Exact
source comparison found146 coincident face/body and231 lip/body vertices with
zero position, normal and joint-weight difference. All four face blink targets
have zero boundary displacement. With the same joint matrices and bind data,
these pairs remain coincident under skinning. This proves positional seam
continuity for these source pairs; it does not prove smooth motion over time.

Face and body share material4, `Rama warm skin`, including normal texture6 at
scale0.24, base-color texture7 and metallic/roughness texture8. Lips use the
separate `Natural lips` material12. The existing surface-finish system binds
those names to separate skin/lip finish values. The seam audit preserves that
material distinction. No materials, vertices, normals, weights, morphs, runtime
controllers or imports were changed.

`source-continuity.json` includes the exact R2/R7 nonhair preservation proof,
actual vertex witnesses and independent archival-source reconciliation. R7 is
`8b6cf0f4…84d5c`; R2 is `140f8ff3…351a`. Identity alone does not complete motion
review. Two additional findings matter for its next comparator:

1. The R4-05 contact-subset classifier marks a vertex as foot/toe only when one
   individual foot/toe influence exceeds0.5. On the actual44821-vertex body,
   9114 vertices have combined foot/toe weight above0.5, but878 of those have
   no individual influence above0.5. All878 lie below rest y=0.04m. Example
   vertex4894 combines toe1-1.R0.495, toe1-2.R0.416, toe2-1.R0.087 and foot.R0.002:
   entirely foot/toe weighted but untagged by that classifier. The source-order
   every96th subset includes eight such misses among94 foot-dominated points.
   Imported vertex ordering has not been equated to source ordering, so that
   last count is a source diagnostic. Aggregate weights by foot side in future
   contact subsets. This limitation affects contact coverage and planted-skin
   metrics; it does **not** invalidate all-skin minimum-height or step failures.
   The motion reviewer acknowledged this counterexample and will carry it into
   the next comparator.
2. The raw `continuity-r3a.json` and `continuity-r4.json` reports bind historical
   source `de61dc4c…d3f5`; the later role05 source-pins ledger lists R2
   `140f8ff3…351a`. The archived report hashes were verified without alteration.
   Comparing the actual historical GLB against R2 shows1560 changed body
   positions, but all9756 body vertices below y=0.3m retain **every vertex
   attribute exactly**. All body joint indices/weights, node/skin JSON and
   inverse binds also match. R7 then preserves all R2 nonhair bytes. This
   reconciles the retained lower-body source; it does not relabel the old run
   as a new R7 runtime execution.

The script records the ordinary accelerated-reversal and rejected start/stop
witnesses at120Hz from both r3a and r4. The ordinary baseline joint witness is
lowerleg01.L at frame97; r3a's is lowerleg01.R at110. The start/stop baseline
witness is toe5-2.R at64, while r3a's lowerleg01.R witness occurs at191. The
archived all-skin measurements still show the rejected ordinary floor and
start/stop step regressions described by role05.

The report compactor removes per-frame joint positions, and no full bone bases
or worst-skinned-vertex identities survive in these archived reports. Exact
independent skin replay at those transition frames is therefore unavailable
from this packet. A future authorized runtime comparator should retain the
before/after joint matrices, root transform, actual surface/vertex identity,
weights and posed positions for each maximum/floor witness. Keep reset
teleports separate from ordinary transitions. No new Godot or Blender run was
used here, and no rendered-silhouette or physical-GPU claim is made.

Reproduce from `games/yuga-native`:

```sh
taskset -c 2,3 env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
 python docs/evidence/visual-rounds/round4/role01/source_continuity.py --project . \
 --r7 /workspace/scratch/visual-round3/role-08/groom-r7/rama-hero.glb \
 --output /workspace/scratch/visual-round4/role-01/source-continuity-fresh.json
```

Next owner: root and the independent R4 motion comparator. R4-14 integration
still requires their actual motion/art disposition. R3 package provenance was
kept separate and completed first; this task adds evidence only.
