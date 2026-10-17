# R2-14 bounded integration handoff

Source baseline: `0437ea91edf6989ff78c1eeadb3661f4825b60f2`. Product: YUGA native.
No runtime default, native NOTICE, roadmap, commit, push or release was changed.

The corrected role08 r5 form is coherently transferred to both existing body LODs.
Every eligible LOD row matches a complete original near attribute row. Both LODs
retain all 1,812 face, 1,560 body and 564 lip displacement records, including
corresponding normal/tangent frames. Rig nodes, weights, UVs, topology, morphs,
images, animations and unrelated geometry remain byte-exact in the binary.
All 18 POSITION extrema are exact per output; JSON changes only eligible lip
POSITION min/max. Maximum displacement is 1.562 mm. This is numerical evidence,
not acceptance of anatomy, continuous morph contact or rendered appearance.

The original r1 transfer is retained and rejected because the inherited lip
POSITION bounds were stale. Corrected overlay:
`/workspace/scratch/visual-round2/role-14/form-lods-r2/overlay`.

| Asset | SHA-256 |
| --- | --- |
| near | `2dbd60ae1ca090340a1b927f71f815da313e976d8645991ea3ecc73282f7dd88` |
| mid | `dcfdc6413e7d23744b12189b6f63dab5116ad84f8feef8e2b963266df2ac4b38` |
| far | `02f54e29bcd7351d6c4b2c25290faf133e4435962b2b7b78a9c2c5885210c30d` |

`package-native.py` now retains schema1/schema2 behavior and accepts exactly one
schema3 append: `principal-facial-form-v1`. Its parent is the preserved faceGLB;
`inputEditableSha256=null` and `editableOrigin=imported-stage-asset` identify the
new Blender file honestly. The import receipt binds candidate/editable/importer,
and the form/LOD manifests bind every source/output. Original schema2 notice is
pinned by its immutable original hash; original three authoring stage objects
must remain identical. Complete mid/far outputs and their original inputs are
required, so a near-only replacement cannot pass the form provenance gate.

Executed on CPUs 0,1: packaging counterexamples 174/174; form/LOD admission and
mapping counterexamples 23/23; corrected actual near/mid/far seam 4/4 each; full
real schema3 proposal validates all 42 provenance sources. Reports are retained
in `affected-checks/`. No importer, renderer, Blender or export was run by role14.

Concrete review proposal:
`/workspace/scratch/visual-round2/role-14/provenance-review-r1`.
Its `promotion-manifest.json` (copied here as `promotion-proposal.json`) enumerates
16 exact proposed promotion files with byte hashes. Root can copy only those
paths after art/source approval, with NOTICE last. The unchanged historical
source files in the review tree are validation dependencies, not replacements.
Already reviewed generator/helper/package source changes also remain necessary.
The new source-stage NOTICE is a draft in the proposal; root reviews it before
copying. This tree has no PCK or release artifact.

Renderer owns `/workspace/scratch/visual-round2/capture-forms-project-r1`; it has
all three candidate assets and eight copied existing test scripts under tests/.
Role06 must finish its serialized import before actual candidate lifecycle,
face, LOD, material, cancellation and integration checks run. CPU0,1 checks can
then be owned by role13/root. Planned suites: rama_facial_cases (with exact asset
argument), hero_lod_binding_cases, hero_lod_cases, rama_material_cases,
rama_surface_finish_cases, rama_finish_adversarial_cases, rama_ability_cases,
rama_hero_integration_cases. Inspect both JSON checks and logs for engine errors;
zero exit alone is insufficient. Material mip/SSS/light overlays remain separate
role01/03 diagnostics and are not silently combined into this form candidate.

No actual frames were reviewed by role14. Root/art review, imported resource and
continuous expression/action checks remain the promotion gates. Next owner:
root plus renderer06 and resource engineer13.
