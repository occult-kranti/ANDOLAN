# Hanuman temple court reconstruction

The generated Hanuman keyframe guides the pose, costume, character silhouette and lighting. The reconstructed Blender scene starts with the existing R5 rig and includes modeled geometry, weighted grooms, drapery, gada, carved stone, bells, and individual lamps. It carries the rig's 167 joints and 11 action datablocks. The render uses an editable camera and actual reflected light. The reference image is kept beside the render for review. [Generated target](../lookdev/hanuman-imagegen-reference.png) · [Previous Blender still](../lookdev/hanuman-lookdev.png) · [R5 playable asset and provenance](../README.md)

Open the packed scene in Blender 4.3 or later. The 1448 × 1086 still comes from the scene's keyframe camera. The facial study shows the underlying sculpt from the front, three-quarter and side. [Editable Blender scene](hanuman-keyframe.blend) · [Rendered keyframe](hanuman-keyframe-denoised.png) · [Unfiltered render](hanuman-keyframe.png) · [Face](hanuman-face-detail.png) · [Grip](hanuman-grip-detail.png) · [Feet](hanuman-feet-detail.png) · [Alternate camera](hanuman-alternate.png) · [Facial form study](hanuman-facial-form-study.png) · [Build report](build-report.json) · [Reopen and contact checks](verification.json)

## Rebuild in Blender

Run from the repository root using Blender 4.3.2. Use a fresh output directory for each render.

```sh
blender -b --factory-startup -t 2 games/yuga-native/art/hanuman/hanuman.blend \
  --python-exit-code 1 --python games/yuga-native/tools/hanuman-match/build_match.py -- \
  --output /tmp/yuga-hanuman-keyframe --width 1448 --samples 40
```

The builder writes a packed Blender file, an unfiltered Cycles still and a JSON record of source hashes, rig and camera landmarks. Use `--width 480 --samples 12` for a quick geometry and lighting check, or `--build-only` to save the scene without rendering. The artist can edit the staging, lighting and pose in the Blender file or tune the shared profile and rerun the build. The profile holds framing, stance, gaze and gada contact placement. The sculpt, exposed anatomy, hands and feet, wardrobe and court stages own their individual surfaces. [Reference profile](../../../tools/hanuman-match/reference-profile.json) · [Builder](../../../tools/hanuman-match/build_match.py)

The tested cloud Blender does not bundle Open Image Denoise. To produce a separately labeled presentation PNG, run the existing `tools/hanuman-art/denoise.py` script with the pinned CPU tool against the original render. All meshes, light sources and materials remain editable in the scene. [Denoiser command and provenance](../README.md#rebuild-and-render)

## Inspect individual parts

The review renderer reads the same scene. It renders the selected region at a larger virtual frame size so near-camera anatomy retains more detail. Available views are `face`, `grip`, `torso`, `feet`, `tail` and `alternate`.

```sh
blender -b --factory-startup -t 2 /tmp/yuga-hanuman-keyframe/hanuman-keyframe.blend \
  --python-exit-code 1 --python games/yuga-native/tools/hanuman-match/render_detail.py -- \
  --view face --samples 48 --output /tmp/yuga-hanuman-keyframe/face.png

blender -b --factory-startup -t 1 /tmp/yuga-hanuman-keyframe/hanuman-keyframe.blend \
  --python-exit-code 1 --python games/yuga-native/tools/hanuman-match/check_match.py -- \
  --report /tmp/yuga-hanuman-keyframe/audit.json
```

The checker verifies the reopened scene against the R5 rig and action data, inspects packed images and external dependencies, and reports projected bounds and bare sole-to-stone measurements. [Per-region review skill](../../../../../.agents/skills/yuga-anatomy-review/SKILL.md)

## Panel decisions

| Pass | What the actual render exposed | Correction |
| --- | --- | --- |
| 1 · Whole figure | Gada and stance read. Both knees broke through opaque cloth, the chest shell left large openings, and pale stone made the court look enclosed. | Use donor weights around the knees, rebuild the upper shell, dim and open the court, and move the gada head behind the shoulder. |
| 2 · Contact and light | Knees and armor were closed. Feet touched the frame, the exposed bronze read black, and eye sockets were too dark to read. | Reframe from projected bounds, bring the soles to real paving, relight the face and add physical patina and depth to the temple. |
| 3 · Body parts | Close render showed too much sclera, lip contours floating over the muzzle and an upright hair crest. Forearms and calves needed clearer planes. | Refine lids, iris, lip seam and directional groom. Reshape exposed muscles, fit fingertip and toenail surfaces to the existing skin weights, and review tail and cloth separately. |
| 4 · Integrated review | The brow read more clearly and both feet fit in frame. A dark gap remained along the hairline. Rays through the dark fold at the left hip hit cloth throughout. | Keep the garment and fit the scalp border from the actual head mesh. |
| 5 · Hairline and final render | Reopened measurement found 112 sampled hairline edge points seated about 2 mm inside the scalp. The hero projections stay inside the frame. | Render the packed scene at the reference dimensions. Use the facial study and the close region views for the next sculpt reviews. |

## Verification and remaining likeness

The packed scene passed nine Blender reopen checks, including exact rest-transform and action data comparison. It retains 167 bones, 11 actions and packed materials. Across 16 near-sole samples per foot, the lowest surface was within 0.45 mm of the paving. A wider band includes the feet’s natural arches. The body detail stayed within 13 mm of the donor pose across 77 sampled poses. The final wardrobe’s tail was sampled at 99 poses. In the integrated grip and foot study, all 20 fitted nail centers stayed above the skin in the held pose and nine sampled action frames. A separate forced flex embedded two left index nail rim vertices roughly 0.47 mm into the skin. Those are sampled contacts. The runtime combat and presentation suites passed 39 and 20 checks respectively, and the launch integration suite passed. [Exact Blender reopen and sole checks](verification.json) · [Runtime verification commands](../../../docs/HANUMAN_HANDOFF.md)

The rendered Hanuman is still more stylized than the generated target. The muzzle and jaw are flatter, the eyes face more forward, the strands and layered fur are more uniform, and the dhoti volumes are fuller. The hip fist and tail plume still need silhouette work. Keep the same camera for likeness comparisons and use alternate views for the areas the concept does not show. [Target keyframe](../lookdev/hanuman-imagegen-reference.png) · [Region review skill](../../../../../.agents/skills/yuga-anatomy-review/SKILL.md)

## Reuse for the next scene

Start with the same camera checks, body weighting and render pipeline. The revised anatomy, combed locks, wrapped cloth, gada, and four-bone tail match Hanuman’s design. Make the next hero distinct with their own anatomy, costume, hair direction, silhouette and weapon contact. Keep the authored keyframe as a look-development master. Before changing the playable asset, qualify retopology and baking, grip and cloth clearance in motion, near and far silhouette, and game-engine timing and cost. [Panel roadmap](../../../docs/HANUMAN_SWARM_ROADMAP.md)

The court reuses the existing Lanka temple kit for selected architectural elements and Poly Haven’s CC0 rock maps for stone albedo, roughness and relief. The renderer is Blender Cycles, with AgX, a warm key, sky fill and reflected diya pools. The artist extension uses a separate Blender profile. [Pinned stone inputs](../match-court-assets/source-manifest.json) · [Source and Blender extension audit](../../../docs/research/hanuman-match-sources.md)
