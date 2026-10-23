# Read-only anatomy-gated rig review

The R2 generated-hero skin transfer remains **failed**. Its filtered weight
families remove the R1 arm-to-leg failure class, but the latest owner metrics
still report idle p99 edge stretch of 4.04×, idle maximum 35.86× and run-frame-10
maximum 93.19×. Zero unweighted vertices, four influences and normalized finite
rows do not establish anatomical correspondence or continuous deformation.

[The review receipt](rig-r2-code-review.json) binds the inspected script,
anatomy module, report and installed Blender export-source hashes. This review
read code and owner-reported data. It did not independently evaluate a Blender
scene, render, export or reimport the candidate, and changed no rig-owner file.

Concrete findings sent to the rig owner:

- `family()` classifies `clavicle.L/R`, `shoulder01.L/R`, `pelvis.L/R` and other
  sided bones as `core`. Existing zero opposite-arm/leg metrics therefore do
  not exclude opposite-side shoulder or pelvis weights. Audit named sided
  groups separately before claiming no cross-limb correspondence.
- Mirrored hardcoded source landmarks miss the left wrist/fingertip surface
  by about 0.120/0.119 m, versus 0.006/0.007 m on the right. Fully arm-labeled
  counts are 171 left and 956 right. These are provisional capsule labels,
  not authored anatomy; the asymmetry needs investigation before another
  global skin pass.
- Repose moves 4,915 vertices by up to 0.391 m. Pose ratios use that already
  reposed REST as baseline and can hide damage introduced by repose itself.
  Compare original-fit→reposed edge lengths and neighboring label transitions,
  then localize worst actual pose edge deltas. Core-boundary nearest-face
  distance reaches p95 0.322 m / max 0.453 m, another correspondence warning.
- Capsule radius changes when the nearest segment changes; hard z cutoffs
  and the z=1.02 core/leg split also need boundary-local checks. A smooth
  weight formula within one branch does not establish continuity across all
  branches.
- Donor surface-local coordinates and rig-local landmarks assume one common
  frame. The inspected donor mesh and armature transforms are identity, so
  this holds for these inputs; assert it or transform both explicitly for
  future donors.

The installed Blender 4.3 exporter defaults
`export_rest_position_armature=True`. Its joint tree uses `bone.matrix_local`
for REST and its inverse binds invert `armature.matrix_world @ bone.matrix_local`
(with axis conversion). Future export code should set that option explicitly
and compare the exported/reimported REST and action poses. R2 currently has
`export: null`; export correctness is untested, rather than a demonstrated bug.

The rig owner agreed to retain R2 as failed, avoid new render/export work,
and add a read-only original-fit/repose/boundary audit. The next decision is
which anatomy and boundary correspondence to author; passing row counts is
not a promotion gate.
