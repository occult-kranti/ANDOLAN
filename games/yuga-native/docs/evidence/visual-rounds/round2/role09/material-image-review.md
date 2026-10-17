# R2-09 independent material review

Source `0437ea91edf6989ff78c1eeadb3661f4825b60f2`. **Source preservation accepted for isolated follow-up; neither material probe is accepted as a demonstrated stippling fix.** No runtime promotion.

Reviewed all ten original courtyard baseline PNGs individually, then the original left-three-quarter day PNG for roughness mips and for SSS off. The twelve exact paths and hashes are in `reviewed-images.json`. Baseline copies in role06 match the original scratch files viewed. No form candidate render or moving candidate frames were reviewed.

The concrete defect is strongest behind the ear and down the hair/neck boundary in the left-three-quarter day/night originals: a dense dark dotted band remains. Front views show finer forehead stipple. Right-three-quarter and profile views are quieter on skin, but the hair crown and courtyard floor also contain dots. Ordinary gameplay preserves recognizable indigo cloth and gold identity; its rear view cannot establish facial quality. These observations do not assign a unique cause.

The roughness-mips original retains the ear/neck band and forehead dots. Actual recorded finish textures have nine mip levels, so this is a real imported-mip probe. It does not visibly reduce the demonstrated defect enough to pass. The SSS-off original also retains the same defect; its recorded skin materials have SSS disabled and zero roughness mips. No gross new seam, bleaching or halo is evident in either single diagnostic image. That limited observation does not accept all views, temporal stability or material finish quality.

Both comparison reports verify identical recorded camera, viewport, player transform, rig pose pin, motion/face state, LOD and all baseline light fields. The new recorder adds angular-distance and actual skin-state metadata, plus import hashes. Its probe mode omits the earlier front shot; absolute frame counters therefore differ, while each shot retains four warmup frames and the frozen pose. The recorder source diff was inspected. No shade improvement is credited to changing the camera or light. Baseline import hashes were absent from its capture manifest; the independent actual-resource check confirms the baseline's zero mip levels.

The correction is to preserve authored maps and continue the lighting owner's one-variable sampling/lighting diagnosis against this defect view, then validate any actual correction across the required contexts. Reject both current probes as demonstrated fixes. Retain them as useful negative diagnostics; disabling SSS remains a diagnostic, not an accepted final skin treatment.

## Source and lifecycle evidence

- `source-review.json`: 13 independent checks pass. Source pins and decoded image ranges agree; control/mips/SSS overlays contain exactly zero/one/one declared edit. Authored metallic-roughness is RGB with green 134–136 and red 255; active finish is grayscale 128–168 bound through red.
- `imported-material-review.json`: 14 new checks against actual imported near-hero resources pass. Actual authored channel is GREEN; finished face/body use RED, multiplier 1, specular approximately .34, SSS .08 and normal scale approximately .24. Original palette, normal texture, UVs, a second hero, exact material identity restoration, repeated configuration, competitor rejection, transferred-face preservation, owner teardown and visual teardown pass.
- `existing-finish-review.json`: the existing 54-check ownership/resource suite passes with `--resources`. This supplies its existing shared-secondary-slot transfer, external-edit and rollback counterexamples; it is not counted as newly invented coverage.
- Role08 form r4 `491c2cb608227c48be57937db3351daa51cc22871b00c1587f1f205053766144`: independently verified 75,048 changed bytes restricted to the three declared primitives' base POSITION/NORMAL/TANGENT XYZ. JSON, materials, texture payloads, UVs, skin weights, sparse morph payloads, unrelated geometry and animation bytes are exact. Tangent W is exact. Moved vertices are 1,812 face, 1,560 body skin, 564 lips; maximum displacement is 1.562 mm. Moved normal/tangent dot maxima are below 9e-8. This is frame preservation evidence, not proof of posed closure or improved art.

Role08 changes near body forms while current mid/far body geometry remains the baseline. Keep the candidate explicitly near-only for diagnostics or refresh compatible LOD body geometry before promotion. Preserved morph bytes alone do not establish closure after a base-form edit. Those image/deformation gates remain with roles05/06 and the independent art reviewers.

## Executed commands

From `/workspace/ANDOLAN`:

```bash
taskset -c 0,1 python3 games/yuga-native/docs/evidence/visual-rounds/round2/role09/review_source.py --report /workspace/scratch/visual-round2/role-09/source-review-r1.json
taskset -c 0,1 godot --headless --path games/yuga-native --script /workspace/ANDOLAN/games/yuga-native/docs/evidence/visual-rounds/round2/role09/imported_material_review.gd -- --report=/workspace/scratch/visual-round2/role-09/imported-material-r2.json
taskset -c 0,1 godot --headless --path games/yuga-native --script res://tests/rama_surface_finish_cases.gd -- --resources --report=/workspace/scratch/visual-round2/role-09/existing-finish-r1.json
python3 games/yuga-native/docs/evidence/visual-rounds/round2/role09/compare_captures.py /workspace/scratch/visual-round2/capture-baseline-court-r1 /workspace/ANDOLAN/games/yuga-native/docs/evidence/visual-rounds/round2/role06/diagnostics/roughness-mips --report /workspace/scratch/visual-round2/role-09/mips-pair-r2.json
python3 games/yuga-native/docs/evidence/visual-rounds/round2/role09/compare_captures.py /workspace/ANDOLAN/games/yuga-native/docs/evidence/visual-rounds/round2/role06/baseline/courtyard /workspace/ANDOLAN/games/yuga-native/docs/evidence/visual-rounds/round2/role06/diagnostics/sss-off --report /workspace/scratch/visual-round2/role-09/sss-pair-r1.json
```

All final commands exited zero. The first new GDScript run hit two reviewer-script type-inference parse errors; the log is retained in scratch, and explicit bool annotations corrected them before the successful run. The first pair check rejected a new metadata field as an entire light mismatch; the revised checker compares every original light field and records new fields separately. Both failed attempts remain in scratch and are not passing evidence.

No imports, runtime writes, Blender runs, heavy renders or shared-roadmap edits were made by this role. Pending: form original-image review; further lighting probes; candidate front/profile/night/Confluence and moving evidence. Root may rotate this slot and reactivate it when the corrected form images exist.
