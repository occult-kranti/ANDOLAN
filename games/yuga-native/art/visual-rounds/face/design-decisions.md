# R2-08 decisions and limits

Actual original images inspected with the image viewer:

- `docs/evidence/visual-campaign/capture-shadow-confirm-world-day-r3/shadow-bias-depth2-face-day.png`
- `/workspace/scratch/rama-native-face-render-r4d/three-quarter-open.png`
- `/workspace/scratch/visual-round2/capture-baseline-court-r1/courtyard-front-day.png`
- `/workspace/scratch/visual-round2/capture-baseline-court-r1/courtyard-three-quarter-right-day.png`

These show puffy upper orbital folds, a broad cheek plane, weak lip/chin
transition, restrained facial expression and conspicuous groom gaps. The last
two are fresh Round 2 baseline captures. This stage addresses only principal
face forms. Groom gaps, jewelry and clothing belong to later owners.

The authored shelf and upper-fold relief improve the geometric separation of
eyelid and superior fold. A small forward/lateral malar displacement and lower
cheek relief articulate that plane. Lip support, a shallow labiomental groove
and a fuller chin provide a continuous mouth-to-chin transition. These are
testable design intentions; matched candidate renders must establish whether
they improve the actual character.

The mouth/cheek changes use the same spatial field across skin and lip material
primitives so existing exact shared positions stay equal. The orbital attachment
is held exactly and blended over a broad collar. The first 10 mm recovery field
failed the original triangle-rotation bound; the final 16 mm recovery passes
without relaxing that bound. Maximum stored displacement is 1.562 mm; the eye
partition maximum is 0.834 mm. No topology, UV, skin weight, bone, animation,
texture, material or morph payload changes are part of this stage.

Blender 4.3.2 opened both editable inputs. The older reconstructed source has
one anatomical mesh and nine imported actions. The native facial source has
488 mesh objects and a 5,452-vertex, 5,378-quad `RamaFace`; it is the relevant
source for the original held-ring topology. The candidate companion imports
the reviewed GLB into three runtime meshes, one 164-bone rig, nine actions,
four ordered facial morphs and **17 packed images**. It is editable imported
data, not restored original modeling history.

Executed numerical evidence: 206/206 candidate preservation/differential-morph
checks; 4/4 original seam checks; 8/8 whole-visible-globe closure checks; and
byte-identical clean regeneration. The original 19-check face validator gives
17/19 for both baseline and candidate, retaining the same one open-cornea
obstruction point per eye. Full-closure central margins remain identical.
This inherited defect must not be converted into an overall pass.
The expanded preservation check includes exact POSITION accessor bounds.
Self-review caught stale lip bounds in the first complete candidate; r5 corrects
only that JSON metadata and preserves the same candidate geometry.

Exact 288 held-ring verification is assigned to the independent deformation
reviewer using positions extracted from the native quad source. The 146 shared
attachment checks alone do not prove that larger ring. Actual continuous
blink/action review and matched front/three-quarter/profile/day/night candidate
review remain independent gates. Role 14 owns exact-row LOD transfers and
provenance integration; root owns any runtime promotion.

Reference-only consultation: `research/community-reuse/art.md`, `animation.md`
and mythology MY-01. Existing anatomy/rig and original project palette remain
the source. No literary text is treated as an anatomical model and no new
cultural image/model was imported.
