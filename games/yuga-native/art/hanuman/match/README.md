# Hanuman temple court reconstruction

The generated Hanuman keyframe guides the pose, costume, character silhouette and lighting. The reconstructed Blender scene starts with the existing R5 rig and includes modeled geometry, weighted grooms, drapery, gada, carved stone, bells, and individual lamps. It carries the rig's 167 joints and 11 action datablocks. The render uses an editable camera and actual reflected light. The reference image is kept beside the render for review. [Generated target](../lookdev/hanuman-imagegen-reference.png) · [Previous Blender still](../lookdev/hanuman-lookdev.png) · [R5 playable asset and provenance](../README.md)

Open the packed scene in Blender 4.3 or later. The 1448 × 1086 still comes from the scene's keyframe camera. The facial study compares the earlier and revised sculpt from matched front, three-quarter and side views. [Editable Blender scene](hanuman-keyframe.blend) · [Rendered keyframe](hanuman-keyframe-denoised.png) · [Unfiltered render](hanuman-keyframe.png) · [Reference and render comparison](hanuman-comparison.jpg) · [Face](hanuman-face-detail.png) · [Belt-side fist](hanuman-belt-hand.png) · [Embroidery and armor](hanuman-torso.png) · [Tail](hanuman-tail.png) · [Grip](hanuman-grip-detail.png) · [Feet](hanuman-feet-detail.png) · [Alternate camera](hanuman-alternate.png) · [Facial form study](hanuman-facial-form-study.png) · [Build report](build-report.json) · [Reopen and sole checks](verification.json) · [Belt-hand contacts](hip-hand-verification.json) · [Measurements by part](part-measurements.json)

## Rebuild in Blender

Run from the repository root using Blender 4.3.2. Use a fresh output directory for each render.

```sh
blender -b --factory-startup -t 2 games/yuga-native/art/hanuman/hanuman.blend \
  --python-exit-code 1 --python games/yuga-native/tools/hanuman-match/build_match.py -- \
  --output /tmp/yuga-hanuman-keyframe --width 1448 --samples 48
```

The builder writes a packed Blender file, an unfiltered Cycles still and a JSON record of source hashes, rig and camera landmarks. Use `--width 480 --samples 12` for a quick geometry and lighting check, or `--build-only` to save the scene without rendering. The artist can edit the staging, lighting and pose in the Blender file or tune the shared profile and rerun the build. The profile holds framing, stance, gaze and gada contact placement. The sculpt, exposed anatomy, extremities, wardrobe and court stages own their individual surfaces. The textile stage packs the woven ornament masks. The pose stage fits the belt-side hand on the original finger rig. [Reference profile](../../../tools/hanuman-match/reference-profile.json) · [Builder](../../../tools/hanuman-match/build_match.py)

The tested cloud Blender does not bundle Open Image Denoise. To produce a separately labeled presentation PNG, run the existing `tools/hanuman-art/denoise.py` script with the pinned CPU tool against the original render. All meshes, light sources and materials remain editable in the scene. [Denoiser command and provenance](../README.md#rebuild-and-render)

The complete review set renders all seven views from one packed scene, filters the PNGs and compares the full frame with both the original concept and the named prior revision. It requires Python with Pillow and NumPy, Git history for the earlier revision, and the OIDN binary from the preceding link. The output also includes the unfiltered detail views and a SHA-256 manifest. [Review script](../../../tools/hanuman-match/review_set.py) · [Published image identities](review-manifest.json)

```sh
python3 games/yuga-native/tools/hanuman-match/review_set.py \
  /tmp/yuga-hanuman-keyframe /tmp/yuga-hanuman-review \
  --oidn /path/to/oidnDenoise --threads 4 \
  --previous-ref 6b505f0414827732f58456778162b515797afbeb
```

## Inspect individual parts

The review renderer reads the same scene. It renders the selected region at a larger virtual frame size so near-camera anatomy retains more detail. The published detail views use 28 Cycles samples each. Available views are `face`, `grip`, `belt_hand`, `torso`, `feet`, `tail` and `alternate`.

```sh
blender -b --factory-startup -t 2 /tmp/yuga-hanuman-keyframe/hanuman-keyframe.blend \
  --python-exit-code 1 --python games/yuga-native/tools/hanuman-match/render_detail.py -- \
  --view face --samples 28 --output /tmp/yuga-hanuman-keyframe/face.png

blender -b --factory-startup -t 1 /tmp/yuga-hanuman-keyframe/hanuman-keyframe.blend \
  --python-exit-code 1 --python games/yuga-native/tools/hanuman-match/check_match.py -- \
  --report /tmp/yuga-hanuman-keyframe/audit.json

blender -b --factory-startup -t 1 /tmp/yuga-hanuman-keyframe/hanuman-keyframe.blend \
  --python-exit-code 1 --python games/yuga-native/tools/hanuman-match/check_hip_hand.py -- \
  --report /tmp/yuga-hanuman-keyframe/belt-hand.json

blender -b --factory-startup -t 1 /tmp/yuga-hanuman-keyframe/hanuman-keyframe.blend \
  --python-exit-code 1 --python games/yuga-native/tools/hanuman-match/check_plate_motion.py -- \
  --report /tmp/yuga-hanuman-keyframe/plate-motion.json

blender -b --factory-startup -t 1 /tmp/yuga-hanuman-keyframe/hanuman-keyframe.blend \
  --python-exit-code 1 --python games/yuga-native/tools/hanuman-match/check_plume_motion.py -- \
  --report /tmp/yuga-hanuman-keyframe/plume-motion.json
```

The checker measures the left and right rest-mesh landmarks across the rig’s sagittal plane, compares the reopened scene to the R5 rig and action data, inspects packed images and external dependencies, and reports projected bounds and bare sole-to-stone measurements. [Per-region review skill](../../../../../.agents/skills/yuga-anatomy-review/SKILL.md)

## Panel decisions

| Pass | What the actual render exposed | Correction |
| --- | --- | --- |
| 1 · Whole figure | Gada and stance read. Both knees broke through opaque cloth, the chest shell left large openings, and pale stone made the court look enclosed. | Use donor weights around the knees, rebuild the upper shell, dim and open the court, and move the gada head behind the shoulder. |
| 2 · Contact and light | Knees and armor were closed. Feet touched the frame, the exposed bronze read black, and eye sockets were too dark to read. | Reframe from projected bounds, bring the soles to real paving, relight the face and add physical patina and depth to the temple. |
| 3 · Body parts | Close render showed too much sclera, lip contours floating over the muzzle and an upright hair crest. Forearms and calves needed clearer planes. | Refine lids, iris, lip seam and directional groom. Reshape exposed muscles, fit fingertip and toenail surfaces to the existing skin weights, and review tail and cloth separately. |
| 4 · Integrated review | The brow read more clearly and both feet fit in frame. A dark gap remained along the hairline. Rays through the dark fold at the left hip hit cloth throughout. | Keep the garment and fit the scalp border from the actual head mesh. |
| 5 · Hairline and final render | Reopened measurement found 112 sampled hairline edge points seated about 2 mm inside the scalp. The hero projections stay inside the frame. | Render the packed scene at the reference dimensions. Use the facial study and the close region views for the next sculpt reviews. |
| 6 · Sculpt and surface review | The earlier muzzle and chin read broad in clay, the hip hand folded into a hook and the gada’s raised beads flattened its silhouette. | Mirror the cheek and nostril changes in rest space, fit the fist against the waist, cut nine flutes around the gada and reshape the rooted tail plume. |
| 7 · Costume and light | The first integrated cloth rendered pale pink. Arm motion also pulled the rigid shell away from the inlaid detail. | Tint the cloth sheen, adjust thread relief, and bind the inlays and shell to the same spine interpolation. Check the result under the actual court lights and reopen the saved scene for contact measurements. |
| 8 · Face, plume and court | The portrait had a flat lid line. Individual tail rings flipped at the bend, pinching the surface. The alternate shot exposed an empty edge beyond the pillar. | Lift the nasal tip, sculpt the inner eyelid and tilt the brows. Carry the ring orientation around the bend, group the plume into nine locks, and project original architectural relief onto the three towers and return gallery. |

## Verification and remaining likeness

The final scene passed eleven structural and symmetry checks. The rest-position mirror comparison covers 5,304 directed samples with zero measured discrepancy to six decimal places in millimeters. The check deliberately excludes the held pose. A separate verifier found zero interpenetrating face pairs between disjoint fingers or between the sampled belt hand and its clothing. It covered 1,287 hand faces, all ten digit pairs and 33 garment objects. The smallest measured skin-to-fold clearance was 0.895 mm. [Belt-hand verification script](../../../tools/hanuman-match/check_hip_hand.py) · [Hand receipt](hip-hand-verification.json)

Across 77 sampled poses, the largest measured displacement from adding the localized body sculpt was 18.4 mm or less. The tail segments and plume roots were sampled through 99 poses across 11 clips. The breastplate and its inlays now share a smooth weighting across four spine links. Restoring the upper arms to neutral produced zero measured plate displacement in those samples. The former plate had moved by up to 45.6 mm in the shoulder test. The final packed scene also passed an independent test that rotated each arm 20° and measured all 15,810 evaluated shell vertices. The wrist moved at least 8.87 mm, and the spine control moved the shell 141.93 mm. [Plate motion receipt](plate-motion-verification.json) · [Rig, body symmetry and sole measurements](verification.json) · [Runtime checks](../../../docs/HANUMAN_HANDOFF.md)

The current portrait builds on the narrowed jaw at `6b505f04`. It defines the nasal bridge, medial lids, lower muzzle and closed mouth. A small portrait light is linked to the eye surfaces. At the tail crest, the prior file showed 177.76° of residual twist between adjacent cross-sections. The current crest measures 0.00° across 43 edges to the reported precision. Nine guide groups spread 328 weighted plume fibers into a fan. Across 99 sampled poses, the largest measured tail-to-plume join gap was under 0.001 mm. The tail tip moved 577 mm relative to its base during Tail Sweep. [Plume motion receipt](plume-motion-verification.json) [Face](hanuman-face-detail.png) · [Tail](hanuman-tail.png) · [Reference and successive renders](hanuman-comparison.jpg) · [Prior published art](https://github.com/occult-kranti/ANDOLAN/tree/6b505f0414827732f58456778162b515797afbeb/games/yuga-native/art/hanuman/match)

The court wraps four original carvings around shallow tower walls and a gallery return using face-local texture coordinates. The 512 × 512 relief atlas is packed in the Blender scene. The current court has 302 relief panels and 86,654 triangles across its meshes. The prior court had 110,690 triangles. These counts apply to the court collection alone. The raking-light and alternate-camera views show where the detail is visible. [Temple study](temple-relief-study.png) · [Build report](build-report.json) · [Developer sources and technique review](../../../docs/research/HANUMAN_INDIE_RENDER_TECHNIQUES.md)

The concept still has finer broken-up hair, a more pronounced cheek-to-muzzle transition and more distinct knuckle planes. Check these features at the intended gameplay distance when baking the studio master. [Facial form study](hanuman-facial-form-study.png) · [Belt-side hand](hanuman-belt-hand.png)

## Reuse for the next scene

Start with the same camera checks, body weighting and render pipeline. The revised anatomy, combed locks, wrapped cloth, gada, and four-bone tail match Hanuman’s design. Make the next hero distinct with their own anatomy, costume, hair direction, silhouette and weapon contact. Keep the authored keyframe as a look-development master. Before changing the playable asset, qualify retopology and baking, grip and cloth clearance in motion, near and far silhouette, and game-engine timing and cost. [Panel roadmap](../../../docs/HANUMAN_SWARM_ROADMAP.md)

The court reuses the existing Lanka temple kit for selected architectural elements and Poly Haven’s CC0 rock maps for stone albedo, roughness and relief. The renderer is Blender Cycles, with AgX, a warm key, sky fill and reflected diya pools. The artist extension uses a separate Blender profile. [Pinned stone inputs](../match-court-assets/source-manifest.json) · [Source and Blender extension audit](../../../docs/research/hanuman-match-sources.md)
