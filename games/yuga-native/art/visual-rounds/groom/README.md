# Round 3 principal groom candidate

R3-08 replaces the principal hair geometry in one isolated hero candidate. The
actual Round 2 courtyard front, profile and left three-quarter originals show a
large uncovered temple wedge and many uniform narrow nape locks. The original
`hero-rama-quality/build_quality.py` generates those narrow locks while retaining
the older foundation's high 1.78 m cutoff. This stage replaces that foundation
with a shell ray-fitted to the actual skull and authors five broad crown clumps,
two short temple clumps and nine asymmetric nape clumps. Original eyebrow and
topknot components remain exact, including their existing shortcomings.

The current candidate is `/workspace/scratch/visual-round3/role-08/groom-r7`.
It derives from the accepted corrected Round 2 form geometry. The previous r6
source and its fixed package proposal remain archived unchanged.
No canonical runtime asset, source rig, material, image or face data is changed.

## Reconstruct

Run from `games/yuga-native` with the existing Python NumPy/SciPy environment:

```sh
python3 art/visual-rounds/groom/build_groom.py \
  --near /workspace/scratch/visual-round2/role-14/form-lods-r4/overlay/assets/heroes/rama-hero.glb \
  --mid /workspace/scratch/visual-round2/role-14/form-lods-r4/overlay/assets/heroes/rama-hero-mid.glb \
  --far /workspace/scratch/visual-round2/role-14/form-lods-r4/overlay/assets/heroes/rama-hero-far.glb \
  --output /workspace/scratch/visual-round3/role-08/groom-next
python3 art/visual-rounds/groom/validate_groom.py \
  --manifest /workspace/scratch/visual-round3/role-08/groom-next/groom-manifest.json \
  --output /workspace/scratch/visual-round3/role-08/groom-next/validation.json
python3 art/visual-rounds/groom/measure_coverage.py \
  --manifest /workspace/scratch/visual-round3/role-08/groom-next/groom-manifest.json \
  --output /workspace/scratch/visual-round3/role-08/groom-next/coverage.json
python3 art/visual-rounds/groom/replay_motion.py \
  --manifest /workspace/scratch/visual-round3/role-08/groom-next/groom-manifest.json \
  --runtime /workspace/scratch/visual-round2/role-05/baseline-runtime-r3.json \
  --output /workspace/scratch/visual-round3/role-08/groom-next/pose-and-frame-replay.json
```

The generator refuses existing output directories and requires the three exact
source hashes in its `PINS`. It appends geometry to the existing binary payload
and changes only mesh 2, primitive 0 references plus appended accessor/view data
and buffer length. All original binary bytes remain exact. Original data stays
recoverable; the extra unreferenced original hair data makes the candidate GLB
larger even though its rendered hair triangle count is lower. A second build in
`groom-r7-reproduce` produced byte-identical near/mid/far GLBs.

| Level | Hair vertices | Hair triangles | GLB bytes |
| --- | ---: | ---: | ---: |
| Near | 16,343 | 29,448 | 36,049,948 |
| Mid | 7,556 | 13,450 | 25,847,144 |
| Far | 3,755 | 6,444 | 20,901,820 |

All levels share the same control guides and skull source. Mid/far preserve
their original corresponding eyebrow/topknot records. The measured upper bounds
from lower-LOD vertices to the near triangle surface are 5.208 mm and 1.761 mm.
These source-space bounds do not replace actual LOD transition review.

## Binding and material contract

New vertices bind rigidly to existing skin joint 104 (`head`). Existing retained
records remain exact; the 164-joint skeleton, nine embedded clips, four face
morphs and separate runtime animation library are untouched. No runtime writer
is added. The existing `Swept black hair` material keeps its exact name, textures,
normal strength, roughness/specular settings and double-sided opaque culling.

`COLOR_0` RGB stays white. New scalp, crown and temple alpha is zero; only nape
vertices below 1.70 m have a smooth alpha ramp, capped at 0.78. Alpha is the
existing secondary motion weight, never transparency. Its maximum authored
displacement is 10.951 mm under the existing 18 mm offset limit. `COLOR_1` stays
white. New UVs, normals and tangents are finite; normals/tangents are normalized,
orthogonal and retain explicit tangent handedness. New closed clump ends have
nondegenerate geometry and UVs. All cap triangle winding points outward.

## Verification and known limits

- 56 source geometry/preservation checks pass across three LODs. All nonhair
  primitives, all original binary bytes and original material/skeleton JSON are
  exact. No new degenerate triangles exist.
- 208 predetermined bilateral temple rays covered within 25 mm of the actual
  skull increase from 2/208 in the source to 208/208 in the candidate. This is a
  bounded coverage measurement, not a visible-hair-quality score.
- Conservative full-triangle rest clearance lower bounds in near are: ears
  6.095 mm, eyes 46.834 mm, eyebrows 42.611 mm and diadem 5.554 mm. AABB distances
  below 6 mm are refined with separating-axis projection bounds.
- Replaying 37 previously captured actual Godot pose matrices on the source
  candidate passes finite head attachment. Maximum ear motion relative to the
  head is 0.602 mm. This does not claim that the candidate was imported or that
  new runtime action/locomotion samples ran.
- New geometry under six ±axis 18 mm secondary offsets has p95 geometric normal
  change 2.309°, maximum 5.161°, and zero samples above 90°. The unchanged shader
  does not update those frames. The exact retained topknot has a known 178.838°
  stress maximum and 264 samples above 90°, plus 220 original degenerate
  triangles. Those inherited defects remain explicit.
- Khronos reports zero errors for all three corrected r6 GLBs, with three
  inherited `NODE_SKINNED_MESH_NON_ROOT` warnings per GLB. The prior r5 mid/far
  had 17 errors each inherited from R2's stale face/body/lip NORMAL/TANGENT
  bounds. Role14 corrected those upstream optional bounds and issued the r4
  source pins. Rebuilding changes only nine JSON fields per lower LOD; all
  binary geometry is exact between groom r5/r6, and near is byte-identical.
  Original failing reports remain archived; r5 source files are preserved in
  `/workspace/scratch/visual-round3/role-08/groom-r5/source/`. Current reports
  and reconciliation are under `docs/evidence/visual-rounds/round3/role08/corrected-r6/`.

Actual imported front/profile/rear and gameplay views, action/turn/dash/reset
review, background separation, texture direction, headband contact, physical
GPU timing and final artistic acceptance remain open. Render/import owner 06
owns the serialized heavy lane. The optional R1 wisps are not part of this groom.

## Native editable companion

`import_editable.py` was run by role06 for r7 in Blender 4.3.2. The saved/reopened
editable is SHA256 `940c8208d8f5ee8c2e8dd9e4bea2d9893450026189f1a4eb24cd0b1874378f25`;
its inspection is `9af85ce316cc3a270ef62bef98ad4b203218c6f29a5a27c81dc6d4af8d28e031`.
The earlier r6 editable and inspection remain frozen. The importer inspects
the original native groom, imports the candidate, saves hidden authoring control
polygons and exact guide JSON, then saves/reopens a native editable. It never
exports a runtime GLB. Command:

```sh
blender -b -t 1 --python art/visual-rounds/groom/import_editable.py -- \
  --manifest /workspace/scratch/visual-round3/role-08/groom-r7/groom-manifest.json \
  --native-source art/hero-rama-face/rama-hero-face.blend \
  --output /workspace/scratch/visual-round3/role-08/groom-r7/reconstruction.blend
```

Role06 completed the r7 command above, including save/reopen, with 16 hidden guide
curves, one 164-bone rig, nine actions, 17 packed images and four face morphs plus
Basis. The retained R2 inspection of
native source `c541b2…` was read; it lists the original foundation and individual
articulated locks. The procedural generator plus its guide manifest is the
current reconstruction source. Imported Blender geometry is editable, while a
historical modeling stack or automatic Blender-guide roundtrip is not claimed.


## Bounded r7 nape correction

Independent role10 found exposed r6 lower-clump intersections with collar and
neck triangles; its barycentric witnesses are not scalp/root attachment. The
same nine broad nape guides now have a smooth posterior/upward displacement
only below source y=1.70 m. Original guide points, widths, depths, UVs, topology,
head binding, scalp/crown/temple and retained brow/topknot data remain exact.
Normals/tangents are rebuilt, and the existing alpha-height rule is reapplied.

The largest local tip movement is 79.057 mm. Whole hair width and top height
remain unchanged; rear extent grows 5.719 mm and the lowest tip rises 14.911 mm.
A 31-check boundary audit passes. This is one bounded posterior bend of the
lower nape, not an expansion to encompass every posed arm or cloth surface.

Independent full-triangle replay on exported r7 confirms zero rest crossings:
silk gap 3.472 mm, neck gap 5.456 mm, gold/brocade at least 12 mm. Twenty of the
21 unique captured nonstress geometries clear the declared neck/collar region.
`measured_step_recoil` still has crossing pairs (52 gold, 106 silk, 106 brocade,
272 neck); 19 of 24 opposing bounded secondary stress fixtures also intersect.
These unresolved contacts prohibit full action/secondary clearance acceptance.
Counts depend on topology and are not quality scores. Root and independent R3-15
reviewed the six actual rear/profile/recoil diagnostic originals and authorized
full comparison. Role06 completed the 150-frame pair; the independent reviewer
reported 604/604 source-bound controls and direct inspection of 19 paired
originals without a new groom/cloth blocker. The recoil contact remains an
explicit disposition item; no default asset promotion occurred.

Current source pins: `source-manifest-r7.json`. The older `source-manifest.json`
remains the exact frozen r6 history, including the status recorded when it was
written. Current reports and reconstruction instructions are in
`docs/evidence/visual-rounds/round3/role08/nape-r7/HANDOFF.md`. The r6 schema4
package deliberately does not accept r7 bytes; a new accepted stage would need
new explicit pins and a matching saved/reopened editable.

The strict R7 source package, completed editable receipt, font qualification and
current promotion boundary are recorded in `docs/evidence/visual-rounds/round3/role14/r7/HANDOFF.md`.
The new proposal uses the rendered GLBs exactly, without retagging or re-export.
