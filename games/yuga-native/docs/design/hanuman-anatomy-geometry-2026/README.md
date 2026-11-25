# Hanuman · practical geometry and anatomy notes

This is an artist handoff for improving the existing Hanuman mesh. The [construction sketch](construction-specimen.svg) is an original editable diagram, with a [PNG preview](construction-specimen.png). The [Blender specimen](mirror-surface-specimen.blend) is an intentionally simple teaching surface, **not** Hanuman, a complete face, or a game-ready model. Its [generator](make_blender_specimen.py) and [preview](mirror-surface-preview.png) make the mirror and shape-key exercise reproducible.

The reference for decisions is the [existing playable character](../../../art/hanuman-hero-finish/models/hanuman-enhanced.glb) and the separately [generated portrait target](../../../art/hanuman-hero-finish/design/hanuman-portrait-target.webp). The image suggests lighting, anatomy and costume; its hidden side and topology are unknown. The task is to improve the actual mesh and its motion, not to declare the portrait a finished 3D model.

## Coordinate and scale notes

The measured baseline GLB has SHA-256 `6612e710578c2527fc1edb84cd8c2c64936cd7ec2a0b201d4a714eead870273a`. Its POSITION values are **mesh-local before node transforms and skinning**, with glTF Y up. The existing sculpt script explicitly maps glTF `(x,y,z)` to Blender `(x,-z,y)` when it creates its editable groom; verify actual object and armature transforms before applying this mapping to other models. One unit is treated as one metre in this project's geometry.

These are observed extents, not ideal proportions: the baseline `Eyes · warm sclera` primitive spans x = -0.0688 to +0.0688, y = 1.8627 to 1.9087, z = 0.1489 to 0.1969 in mesh-local metres. These are bounding extrema for both eyes, not eye centres or interpupillary distance. The skin material spans local y = 0 to about 2.020 m; the added groom reaches local y ≈ 2.111 m. These material bounds should not be confused with the total posed silhouette or weapon height. The 167-joint skin and eleven gameplay animations belong to the existing model; the separate [facial expression study](../../../art/hanuman-hero-finish/expressions/README.md) is not part of those shipped clips.

## Region-by-region cheat sheet

| Region | Form and sketch pass | Pose, contact and engine checks |
| --- | --- | --- |
| Eyes and brow | Block paired orbit volumes before grooves; compare inner/outer corners, iris direction, lid thickness and brow shadow front and three-quarter. Preserve the tilak and readable eye opening. | Check blink open/closed and gaze in the independent expression study; inspect lid/cornea contact from an oblique view, not just a front render. |
| Nose and muzzle | Sketch bridge, nostril wing, cheek transition and the front muzzle as interlocking masses. Check nostril depth under grazing light and both profiles. | Keep separate recess/skin surfaces together under the same deformation; inspect clipping and lip silhouette while the jaw moves. |
| Lips and chin | Find the closed mouth seam and corners first; taper the seam and retain a cheek-to-chin plane change. Avoid an unnaturally uniform groove. | In neutral and recovery, lips meet without opening into a hole; test the result in an actual facial rig pose if the topology changes. |
| Skull, ears, hair and neck | Establish the cranium and jaw silhouette before individual locks; check ear attachment, hairline, neck and clavicle in front, profile and rear. | Check the head turn and neck bend; intentional hair parting and nape silhouette need not mirror. The portrait's fine hair requires its own strand/card and runtime budget work. |
| Chest, shoulders and armor | Draw rib-cage and pelvis masses as simple tilted blocks with a connecting spine; layer armor over them and keep negative space around the armpit. | Sweep shoulder and spine motion; examine plate/body intersections, strap clearance and the silhouette at shoulder-camera distance. |
| Arms, hands and gada | Sketch upper-arm/forearm axes and the gada as a cylinder. Look for elbow plane, tapered wrist, thumb opposition and knuckle cascade on both sides. | Check gripping hand and weapon contact during idle, anticipation, strike and recovery; never move gameplay collision to hide a visual grip defect. |
| Hips, knees, feet and cloth | Identify load-bearing foot, knee direction, hem and ankle contours. Inspect textile grain/UVs separately from geometry. | Check both soles, knee bends, vault landing and stretched border textures across actions; inspect both sides at normal and slow playback. |
| Tail and attachments | Sketch a single clear arc from pelvis through bend to tuft before drawing individual strands. Use taper and overlap to show depth. | Inspect root, tail segment motion, body/weapon clearance and silhouette through idle, turn, vault and Mountain Pulse. Asymmetric movement is intentional. |

The source anatomy text discusses human facial muscles, including the ring-like muscles around eyes and lips and the masseter and temporalis around the jaw. It is a **functional observation for a fictional vanara character**, not a claim that this stylized model must match a human anatomical specimen. Observe Indian art references and the project's portrait alongside the sculpture; no universal head-count or golden-ratio rule is imposed.

## Symmetry and safe shape edits

1. Freeze the file, model hash, action, phase, camera and lights. In the model's own unposed mesh coordinates, an X-plane reflection is `R(x,y,z)=(-x,y,z)`. Verify the plane and transforms first; X = 0 is not automatically the anatomical midline of every object.
2. For an intentionally paired feature, compare a vertex `p` against an appropriate opposite-side point `q` with `d = ||R(p) - q||`. Make measurements in the same coordinate space. Distinguish mesh-local rest points from evaluated, posed points, where a weapon hand or turn should usually be asymmetric.
3. Blender's Mirror modifier uses local object axes, or a separate mirror object's axes. Its merge and clipping options solve different problems. **Symmetrize is destructive**: the documented direction copies one side across the origin and deletes the other. Try on a duplicate and review UV seams, material partitions, weights and intentional asymmetry before adoption.
4. A smooth, bounded one-sided shape correction can use `F(p) = p + g(p) d`, where `d` is an artist-selected displacement and `g(p) = (1-r²)²` for `r < 1`, otherwise `0`, with `r²` an ellipsoid-relative squared distance. This example has zero displacement and first derivative at the boundary; it is a technique, not a recommended face shape or automatic sculpt.
5. For a differentiable local deformation with Jacobian `J = dF/dp`, a normal transforms with `normalize(J⁻ᵀ n)` when `J` is invertible. Transform a tangent by `J`, orthogonalize it against the transformed normal, normalize it and check the tangent handedness, UVs and face winding. A negative determinant reverses orientation; a positive sampled determinant alone does **not** rule out global self-intersection. Rebuild or verify tangents using the actual export/render pipeline.

The [baseline receipt](baseline-rest-symmetry.json) and [measurement script](measure_rest_symmetry.py) scan a fixed face window per material. The skin region's left-to-right nearest-reflected distance has median 0.0000 mm and p95 0.0003 mm, but the sclera and ears show larger p95 values of 3.5170 mm and 6.1296 mm. Different sampling, seams, clipping by the spatial window and intentionally different topology may cause these numbers: they are **not** evidence of a bad eye or ear, true vertex pairing, or a reason to overwrite one side.

The same diagnostic was run on the [V1 facial study](../../../art/hanuman-facial-refinement-2026/README.md) and its [receipt](candidate-v1-rest-symmetry.json). Skin p95 remains 0.0003 mm, but the number of sampled skin vertices changed from 2,093 to 2,062 as the fixed window was reapplied. That makes the percentile comparison a limited diagnostic, not matched-vertex deformation evidence or a visual acceptance of V1.

```sh
python3 games/yuga-native/docs/design/hanuman-anatomy-geometry-2026/measure_rest_symmetry.py \
  --input games/yuga-native/art/hanuman-hero-finish/models/hanuman-enhanced.glb \
  --output /tmp/hanuman-rest-symmetry.json
```

The probe needs NumPy and the repository's existing GLB reader. It matches each left-side sample to the nearest right-side sample **within the same material**, with no vertex ID, one-to-one assignment, skin-weight, UV or connectivity guarantee. It ignores pose, action and the centre strip. The region filter is recomputed on each input, so compare sample counts and investigate boundary changes before comparing percentiles. A result is a prompt for a visual/topology review, not a quality gate.

## Use the Blender teaching specimen

Open [mirror-surface-specimen.blend](mirror-surface-specimen.blend) in Blender 4.3.2. Select `STUDY ONLY · editable half-surface`; in the Modifiers tab inspect the active local-X Mirror, Merge and Clipping settings. In Object Data Properties, adjust shape key `Cheek relief · up to 8 mm` from 0 to 1, then orbit to see the paired surface change. Edit one side on a disposable copy to study the center seam. The file has 725 original vertices, 672 quads, a 0.1 mm merge threshold and no skeleton, real eyes, texture or game export.

To rebuild it from the repository root, run:

```sh
blender -b --factory-startup -t 1 --python-exit-code 1 \
  -P games/yuga-native/docs/design/hanuman-anatomy-geometry-2026/make_blender_specimen.py -- \
  /tmp/hanuman-mirror-study.blend
```

The saved specimen was reopened in Blender 4.3.2, and its mesh, X mirror and shape key were checked. A low-sample CPU preview was rendered and inspected. The first preview failed because this Blender build lacks OpenImageDenoise; the generator was corrected to enable it only when available, and the second preview succeeded. The specimen tests a teaching workflow only; it proves nothing about the hero's final topology or performance. [Verification and artifact hashes](verification.json)

## Review protocol for the actual model

- Compare before/after under the [existing matched studio recipe](../../../art/hanuman-hero-finish/render/README.md): same action/phase, orthographic camera, light, samples and view transform. Keep a full figure, face crop and alternate angle; keep raw images and parameters.
- Check center seam and protected boundaries, no NaNs/infinities, normals and tangents, UV/material continuity, skin weights and joint associations. Test extreme shape-key or rig poses, not only neutral. For imported GLB compare skin joint order, inverse bind matrices, animation channels and timestamps as separate checks.
- Observe idle, run, attack, vault/land, defeat and return on the actual rig. Check hands and feet against their contact points, tail and garment against body, and facial features at a real shoulder camera. A mathematically mirrored rest mesh is not a passing animated character.
- Separate Blender study, exported GLB and playable build by hash. Promote only after the actual engine import, animation and performance tests pass; document any failures and keep the previous playable asset recoverable.

## Sources consulted, 25 November 2026

1. Blender Foundation, [Mirror modifier source](https://projects.blender.org/blender/blender-manual/raw/branch/main/manual/modeling/modifiers/generate/mirror.rst) and [Symmetrize source](https://projects.blender.org/blender/blender-manual/raw/branch/main/manual/modeling/meshes/editing/mesh/symmetrize.rst). The raw manual text was fetched and read; the repo's `main` resolved to `9129f3c8877b99927ffcccb1dc89408a76ab44b0` at the time. Rendered docs returned HTTP 403 in this environment. Installed Blender 4.3.2 API descriptions were also checked for the modifier, clip/merge and six symmetrize directions.
2. Khronos Group, [glTF 2.0 specification source at `da88a3bb`](https://github.com/KhronosGroup/glTF/blob/da88a3bbbe168cc728eddf71fa5e1915cc2c0629/specification/2.0/Specification.adoc), sections on mesh attributes, tangent handedness, morph targets and skin influences. The raw specification was fetched and searched; it documents `TANGENT.w`, normalized vectors, joint/weight sets and morph deltas before skinning.
3. Scratchapixel, [Transforming Normals](https://www.scratchapixel.com/lessons/mathematics-physics-for-computer-graphics/geometry/transforming-normals.html). Read for the inverse-transpose treatment under nonuniform transforms. The general Jacobian application and checks above are this project's engineering interpretation.
4. OpenStax College, *Anatomy and Physiology* (2014), [Axial Muscles of the Head, Neck, and Back](https://github.com/philschatz/anatomy-book/blob/eadaa6b2992f4e4010f45d58ad4db065e398093e/contents/m46484.md), CC BY 3.0 per the [repository licence](https://github.com/philschatz/anatomy-book/blob/eadaa6b2992f4e4010f45d58ad4db065e398093e/LICENSE.txt). Consulted the facial and jaw sections for functional references; no text or figures were copied into the specimen.
