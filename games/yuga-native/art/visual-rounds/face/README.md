# Round 2 principal facial-form candidate

`build_form_candidate.py` adds a reproducible, reversible authoring stage to the
reviewed original near hero. It shapes the upper lid shelf and superior fold,
malar/lower cheek transitions, lip support, labiomental groove and chin with
eight compact smooth fields. It writes a fresh external candidate and an exact
per-vertex edit ledger. No runtime GLB is replaced by this tool.

Source base: `0437ea91edf6989ff78c1eeadb3661f4825b60f2`. The tool requires the
original `de61dc…` hero. It preserves the GLB JSON values except the changed
POSITION bounds, and every binary byte outside the selected
POSITION/NORMAL/TANGENT records. The 146 face/body seam vertices
have a 4 mm hold collar and smooth influence recovery out to 16 mm. The exact
288 source quad-ring positions in `held-ring.json` are independently excluded
from every position/normal/tangent edit; the distance collar alone is insufficient.
The required original-ring SHA256 is
`71cc40e8f5eb732382255cbb9ca2eca88f6306429c2c649f8223dbe5b4db0ccd`.
Normals use the deformation Jacobian's inverse transpose; tangents use its
push-forward followed by orthogonalization, retaining original handedness.
UVs, mesh topology, materials, images, weights, skeleton and four morph payloads
are exact. The existing runtime remains the sole facial writer.

Run from the repository root, using a new output directory:

```sh
python3 games/yuga-native/art/visual-rounds/face/build_form_candidate.py \
  --input games/yuga-native/assets/heroes/rama-hero.glb \
  --held-ring games/yuga-native/art/visual-rounds/face/held-ring.json \
  --output /workspace/scratch/visual-round2/role-08/face-form-next
python3 games/yuga-native/art/visual-rounds/face/validate_form_candidate.py \
  --input games/yuga-native/assets/heroes/rama-hero.glb \
  --candidate /workspace/scratch/visual-round2/role-08/face-form-next/candidate.glb \
  --report /workspace/scratch/visual-round2/role-08/face-form-next/form-check.json
```

Also run the existing `hero-rama-face/validate_native_seam.py`,
`validate_face.py` and `validate_aperture.py` against source and candidate.
Actual rest/half/full blink, aim/draw and day/night visual comparisons remain
required. The existing 19-check face validator has two retained open-cornea
failures in both original and candidate; do not report it as a complete pass.

The renderer owns the shared heavy-work slot. In that slot, the following saves
and reopens an editable imported companion while inspecting the existing older
reconstruction and native face source. It does not re-export a runtime GLB:

```sh
blender -b -t 1 --python games/yuga-native/art/visual-rounds/face/import_editable.py -- \
  --candidate /workspace/scratch/visual-round2/role-08/face-form-next/candidate.glb \
  --output /workspace/scratch/visual-round2/role-08/face-form-next/reconstruction.blend \
  --native-source games/yuga-native/art/hero-rama-face/rama-hero-face.blend \
  --reconstruction-source games/yuga-native/art/production/reconstruction-rama.blend
```

The current numerical candidate is scratch `face-form-candidate-r6`, GLB
`140f8ff3695bb3d28bd894cb74bca8cd5f1756bbffcf59dad6c4630f377c351a`.
It changes 3,932 vertex records, at most 1.562 mm, with 74,966 changed binary bytes.
Its 34,322,216-byte size, 234,846 vertices, 408,316 triangles, 18 primitives,
164 bones and nine embedded clips remain fixed. The separate 23-state runtime
animation library is untouched. The saved/reopened Blender companion is
`1a917821f2cb50854a16ff40ed4e80847e011f4e023d116540c569620808c6d9`.
The exact importer hash and 17 packed images are recorded in the editable
inspection receipt. Its companion held-ring file records 288 original source
quad-ring positions for independent verification.

Early scratch attempts are preserved: r1 failed on NumPy 2 batched solve shape;
r2/r3 failed the triangle rotation bound before producing a candidate GLB. The
observed narrow boundary recovery rotated some cheek triangles by 19.51°.
Widening the smooth transition from 10 to 16 mm reduced that maximum to 14.93°,
while holding the same exact attachment. No acceptance threshold was relaxed.
The r4 geometry passed those checks but self-review caught stale lip accessor
bounds: its forward Z maximum was still the original value. The r5 correction
updates only POSITION accessor 157 min/max JSON, retaining the same candidate
binary geometry. The expanded independent validator passes 206 checks,
including all 18 exact POSITION bounds. Independent source-ring review then
rejected r5: four nominally held records moved by at most 9.876 micrometres.
R6 restores their positions, normals and tangents exactly using the required
original-ring input; all 288 held positions now pass. R4/r5 and their evidence
remain in scratch. The final form generator SHA256 is
`7bdf0ed92958dca350d8b12c32fcc2a05c0e03110702dc90ebf4ee0cb2dd2134`.

Root and independent reviewers own visual selection and runtime promotion.
Role 14 owns exact source-row transfer into the existing mid/far bodies and an
honest new provenance stage; a new near asset alone would leave mismatched LOD
body forms. This is a bounded facial-form iteration, with dialogue performance,
groom, costume, bow and full production art still outside its result.
