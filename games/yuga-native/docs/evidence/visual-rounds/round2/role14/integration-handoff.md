# R2-14 bounded integration handoff

Source baseline: `0437ea91edf6989ff78c1eeadb3661f4825b60f2`. Product: YUGA native.
No runtime default, native NOTICE, roadmap, commit, push or release was changed.

The corrected role08 r6 form is coherently transferred to both existing body LODs.
Every eligible LOD row matches a complete original near attribute row. Both LODs
retain all 1,808 face, 1,560 body and 564 lip displacement records, including
corresponding normal/tangent frames. Rig nodes, weights, UVs, topology, morphs,
images, animations and unrelated geometry remain byte-exact in the binary.
All declared bounds on edited POSITION/NORMAL/TANGENT attributes are exact.
JSON changes only those already-declared extrema. Maximum displacement is 1.562 mm. This is numerical evidence,
not acceptance of anatomy, continuous morph contact or rendered appearance.

The original r1 transfer is retained and rejected because the inherited lip
POSITION bounds were stale. R5/r2 transfer is also rejected because four
source-ring records moved <=9.876 micrometres. The required pinned held-ring
receipt now supplies all 288 original native quad-ring positions. Final r6
preserves all 434 exported face/body matches in position/normal/tangent data
at all three LODs. Old r5 now fails the transfer admission gate explicitly.
The original source receipt is retained at art/visual-rounds/face/held-ring.json
and is required by form, transfer and package provenance. Corrected overlay:
`/workspace/scratch/visual-round2/role-14/form-lods-r4/overlay`.

| Asset | SHA-256 |
| --- | --- |
| near | `140f8ff3695bb3d28bd894cb74bca8cd5f1756bbffcf59dad6c4630f377c351a` |
| mid | `27d998d924d2732b13bc8e18c3e3ec1ce9d58f0408bf3fda1ff0613cf32cba9f` |
| far | `ea9818e1464c9b6bc077ae83f8354a6357fb19d2a18fc84b2deb65c58aff901a` |

`package-native.py` now retains schema1/schema2 behavior and accepts exactly one
schema3 append: `principal-facial-form-v1`. Its parent is the preserved faceGLB;
`inputEditableSha256=null` and `editableOrigin=imported-stage-asset` identify the
new Blender file honestly. The import receipt binds candidate/editable/importer,
and the form/LOD manifests bind every source/output. Original schema2 notice is
pinned by its immutable original hash; original three authoring stage objects
must remain identical. Complete mid/far outputs and their original inputs are
required, so a near-only replacement cannot pass the form provenance gate.
The LOD receipt now requires `json_exact_except_frame_bounds=true`; an old
position-only receipt cannot pass this final gate.

Executed on CPUs 0,1: packaging counterexamples 181/181; form/LOD admission and
mapping counterexamples 45/45; corrected actual near/mid/far seam 4/4 each; full
real schema3 proposal validates all 43 provenance sources. Reports are retained
in `affected-checks/`. Pinned Khronos validator 2.0.0-dev.3.10 now reports
zero errors for all three corrected GLBs, with three retained
NODE_SKINNED_MESH_NON_ROOT warnings per asset. No importer, renderer, Blender or export was run by role14.

Concrete review proposal:
`/workspace/scratch/visual-round2/role-14/provenance-review-r3`.
Its `promotion-manifest.json` (copied here as `promotion-proposal.json`) enumerates
17 exact proposed promotion files with byte hashes. Root can copy only those
paths after art/source approval, with NOTICE last. The unchanged historical
source files in the review tree are validation dependencies, not replacements.
Already reviewed generator/helper/package source changes also remain necessary.
The new source-stage NOTICE is a draft in the proposal; root reviews it before
copying. This tree has no PCK or release artifact.

Round3 independent validation caught 17 optional NORMAL/TANGENT bound errors
in each previously captured R2 mid/far asset. Final transfer r4 repairs only
nine declared min/max fields across accessors 4474, 4476, 4589, 4598 and 4600.
The near GLB is byte-identical. Mid/far each gain 16 JSON bytes; every BIN byte
and all decoded attributes, rig, animations, morphs and images remain exact.
`affected-checks/frame-bound-reconciliation-r4.json` records exact old/new
identities, BIN SHA256, and every allowed metadata difference. Previous
receipts and captures keep their original pins under superseded-r6-bounds/
and their owning role evidence; none was relabeled as a new-source capture.

Renderer06 owns a fresh isolated import comparison of actual loaded mesh/rig/
resources for all three corrected LODs and a matched three-quarter framebuffer.
That actual reconciliation remains pending; binary equality alone does not
close the import/render gate. Root and role13 retain ownership of final
lifecycle/deformation/action acceptance. Round3 groom owner08 received the
corrected input hashes and must regenerate its candidate on those sources.

No actual frames were reviewed by role14. Root/art review, imported resource and
continuous expression/action checks remain the promotion gates. Next owner:
root plus renderer06 and resource engineer13.
