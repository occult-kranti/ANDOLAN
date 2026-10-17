# Independent Rama finish review

Role 09 reviewed the new finish component, five runtime roughness maps and four
actual near-camera frames. Final technical counterexamples pass **7/7**, map and
provenance checks pass **13/13**. Overall hero art remains **LIMITED**.

The independent test is `tests/rama_finish_adversarial_cases.gd`. It uses small
synthetic meshes for ownership, plus the actual imported skin roughness image.
It does not replay the owner's 53-check suite or qualify a whole playable build.

## Three confirmed defects, now closed

1. Moving a standard-material mesh to another visual made `configure` detect
   loss of ownership, but `release` still replaced that transferred mesh's
   appearance. Release now checks original-visual ancestry.
2. A finish component outside the scene tree could configure a live visual;
   freeing it never called `_exit_tree`, leaving its cloned material behind.
   Configuration now requires both the owner and visual to be in the tree.
3. If two meshes shared a secondary shader and one moved to another visual,
   release restored five uniforms through the remaining sibling. That changed
   the transferred mesh too. Shader rollback now requires all recorded slots
   to remain owned; otherwise it leaves the shared resource unchanged.

The material owner implemented the fixes. This reviewer independently executed
each failure and repeated the same probes after correction. [R1](r1/report-harness-corrected.json)
retains the first two failures, [R3](r3/report.json) the third, and
[R4](r4/report.json) is the final **7/7 PASS**, real Godot exit **0**, without
warnings or errors. Source snapshots preserve both failed component versions.

The initial R1 sharing-control assertion incorrectly compared a float32 engine
property to the literal `.51`. Its corrected version compares the original
stored value. Both test versions and reports are retained; this harness error
is separate from the three product defects.

Final component SHA-256:
`7936f28f29c4b96cb49742bb3309c96df962f95e3cec99d5a7b514ea03c369e1`.
Independent test SHA-256:
`73f40ffbba850c4293d83da31d12acb4b47ce14c368a9709b7173c9fa71beb63`.

## Actual appearance reviewed

[The image receipt](visual-review.json) pins the four original PNGs individually:
baseline and candidate near-day/near-night. Candidate R1 also changes lighting
and scene decoration, so these frames cannot isolate the material contribution.
The capture's finish source is `8b006235…2264d`; the
[source delta](candidate-to-fixed.diff) to the final component changes lifecycle
admission and cleanup only. Profiles, roughness images and successful appearance
writes are identical. This is not an exact-final-source capture receipt.

The candidate preserves indigo brocade and gold motifs. Skin highlights are
broader and less sharp, and the drape reads more consistently as cloth. Ivory
folds remain readable without a new obvious color or UV discontinuity in these
two views. This supports the material direction as a bounded improvement.

Night facial contrast remains weak; tiny skin or weave detail cannot be judged
at this distance. Hair remains coarse separated strips, and the face, fingers
and sculpted drape still fall well short of the requested production target.
The candidate's pavilion bases and pots appear to float above the floor. The
root assigned that scene defect to its district owner; this review does not
claim it corrected.

No continuous animation/contact, LOD transition, far-distance appearance,
physical-GPU timing or Deadlock-equivalent quality is qualified here.

## Map provenance

[Map checks](maps.json) decoded each PNG, checked scalar mode and bounds,
dimensions, actual source/output hashes and byte lengths against the manifest.
All five maps are monochrome 8-bit data. Woven roughness is an exact copy of the
previous CC0 derivative, and its file-specific upstream license remains
present. Four remaining maps derive from the existing original YUGA material
maps. The runtime map is loaded as an actual 512 × 512 texture with the intended
red roughness channel in the independent Godot test.

The [summary](summary.json) records commands, native exit codes and source pins.
The wider campaign owns full integration, final scene correction and publication.
