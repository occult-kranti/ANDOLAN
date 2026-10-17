# R2-14 bounded integration handoff

Source baseline: `0437ea91edf6989ff78c1eeadb3661f4825b60f2`. Product: YUGA native.
No runtime default, native NOTICE, roadmap, commit, push or release was changed.

The corrected role08 r6 form is coherently transferred to both existing body LODs.
Every eligible LOD row matches a complete original near attribute row. Both LODs
retain all 1,808 face, 1,560 body and 564 lip displacement records, including
corresponding normal/tangent frames. Rig nodes, weights, UVs, topology, morphs,
images, animations and unrelated geometry remain byte-exact in the binary.
All 18 POSITION extrema are exact per output; JSON changes only eligible lip
POSITION min/max. Maximum displacement is 1.562 mm. This is numerical evidence,
not acceptance of anatomy, continuous morph contact or rendered appearance.

The original r1 transfer is retained and rejected because the inherited lip
POSITION bounds were stale. R5/r2 transfer is also rejected because four
source-ring records moved <=9.876 micrometres. The required pinned held-ring
receipt now supplies all 288 original native quad-ring positions. Final r6
preserves all 434 exported face/body matches in position/normal/tangent data
at all three LODs. Old r5 now fails the transfer admission gate explicitly.
The original source receipt is committed at art/visual-rounds/face/held-ring.json
and is required by form, transfer and package provenance. Corrected overlay:
`/workspace/scratch/visual-round2/role-14/form-lods-r3/overlay`.

| Asset | SHA-256 |
| --- | --- |
| near | `140f8ff3695bb3d28bd894cb74bca8cd5f1756bbffcf59dad6c4630f377c351a` |
| mid | `44bf3961fa52aef0b1a212dff05dcc6bda5c3cae7c9eaf00303aba9f39d45416` |
| far | `62e65520da49d4f81d8cf0755f77df214f7ce0929d4818c13f62555b300a8f43` |

`package-native.py` now retains schema1/schema2 behavior and accepts exactly one
schema3 append: `principal-facial-form-v1`. Its parent is the preserved faceGLB;
`inputEditableSha256=null` and `editableOrigin=imported-stage-asset` identify the
new Blender file honestly. The import receipt binds candidate/editable/importer,
and the form/LOD manifests bind every source/output. Original schema2 notice is
pinned by its immutable original hash; original three authoring stage objects
must remain identical. Complete mid/far outputs and their original inputs are
required, so a near-only replacement cannot pass the form provenance gate.

Executed on CPUs 0,1: packaging counterexamples 180/180; form/LOD admission and
mapping counterexamples 29/29; corrected actual near/mid/far seam 4/4 each; full
real schema3 proposal validates all 43 provenance sources. Reports are retained
in `affected-checks/`. No importer, renderer, Blender or export was run by role14.

Concrete review proposal:
`/workspace/scratch/visual-round2/role-14/provenance-review-r2`.
Its `promotion-manifest.json` (copied here as `promotion-proposal.json`) enumerates
17 exact proposed promotion files with byte hashes. Root can copy only those
paths after art/source approval, with NOTICE last. The unchanged historical
source files in the review tree are validation dependencies, not replacements.
Already reviewed generator/helper/package source changes also remain necessary.
The new source-stage NOTICE is a draft in the proposal; root reviews it before
copying. This tree has no PCK or release artifact.

Renderer06 owns the final r6 capture/import snapshot. Eight existing test
scripts were copied into the earlier capture-forms-project-r1/tests; they can
be reused for the new frozen snapshot, but its older results do not accept r6.
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
