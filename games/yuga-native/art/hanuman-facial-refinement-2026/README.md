# Hanuman · measured face refinement study

This is a reversible study of the existing skinned Hanuman, not a replacement
for an artist-authored sculpt or a claim of Deadlock-level character quality.
It targets a subtle cheek-to-muzzle transition and makes the limits measurable.
The existing [portrait](../hanuman-hero-finish/design/hanuman-portrait-target.webp)
and the generated turnaround are design references, not 3D scans. The source
and its historical rig, textures and license notices are preserved in the
[hero studio](../hanuman-hero-finish/README.md).

## Candidate and counterexample

| Artifact | Decision | What it does |
| --- | --- | --- |
| [V1 GLB](hanuman-face-candidate.glb), [editable staged scene](hanuman-face-candidate.blend) | **Limited experimental candidate** | Applies a symmetric rest-space form adjustment to skin, the fitted lip/lower-eyelid material and the existing mouth lines. It changes a maximum of 3.47 mm on the actual vertices. The gameplay-scale effect is subtle, and the muzzle still reads as a projecting wedge in profile; this is not final art. Its separate browser preview passed 39 practice checks and a 5v5 browser/peer screen. [Preview evidence](../hanuman-build-qa-2026/README.md) |
| [V2 GLB](hanuman-face-contact-candidate.glb), [staged scene](hanuman-face-contact-candidate.blend) | **Rejected for visual use** | Fits the dark mouth/nostril surface closer to the skin, but the matched profile looks more conspicuously bright and open. Keep it to reproduce the failed experiment; do not ship it merely because its projected clearance improves. |
| [V3 GLB](hanuman-face-profile-candidate.glb) | **Unpromoted experiment** | Starts from V1 and smoothly retracts skin, lip and line together around the closed-mouth silhouette. Matched images show a slight retraction without an obvious new discontinuity, but the bright protruding seam remains, so this is not an accepted mouth fix. [Controls](profile-refinement.json) · [Measurements](profile-report.json) · [Field samples](profile-field-check.json) · [Matched crops](../hanuman-visual-qa-2026/face-crops-profile-v3.webp) |

Both scenes are **reconstructions imported from their GLBs** and staged with
the repository's existing courtyard and camera. They are not original sculpt
history. Each can be reopened in Blender with the rig and actions. The V1
reopened scene contains one 167-bone rig, 18 hero materials, 32 packed images,
11 hero actions and no linked libraries. It has not been approved as final art.
The published baseline gameplay model remains unchanged. The experimental V1
browser package is separate. [Reopened-scene receipt](scene-inspection.json)

## Geometry and controls

Edit [refinement.json](refinement.json), which describes the field in glTF
rest coordinates: X left/right, Y up and +Z toward the face. Each paired form
uses a symmetric Gaussian across X, a vertical Gaussian, and smoothstep gates
that fade toward the back and away from the lower face. The small outward term
uses `tanh(x / 0.012)` to avoid a discontinuity at the midline. The same warp is
applied to the existing skin, eyelid/lip and line materials so fitted parts
travel together. See [the builder](refine.py) for the exact formula.

For transformation `p' = f(p)`, finite differences estimate the 3×3 Jacobian
`J`. Normals use `normalize(J⁻ᵀ n)`, tangents use `J t` followed by
orthogonalization, and the original handedness is retained. The builder rejects
excessive displacements and locally folded vertex samples. The
[independent sampled-field check](field-check.json) reports perfect mirrored
agreement across 21,609 sampled locations and a minimum sampled determinant of
0.919. This is a numerical check over samples, not proof that the result is
anatomically correct or watertight.

The 1,027 skin, 248 eyelid/lip and 346 line vertices above a 0.01 mm movement
threshold include some **lower eyelid margin**; the separate eyeballs, irises
and brows remain unchanged. Skin weights, UVs, indices, material assignments,
skeleton and animation channels are preserved. See the full
[geometry receipt](refinement-report.json) and the independent
[rig/motion audit](../hanuman-rig-qa-2026/README.md).

The exploratory [V2 fitting recipe](contact_fit.py) evaluates frontmost skin
triangles below each separate mouth or nostril vertex in rest space, then
compresses the depth and recalculates normals and tangents using the triangle's
local plane. Its [receipt](contact-report.json) records 0.25–1.61 mm mouth and
0.25–2.06 mm nostril projected vertex offsets. A 20-pose
[directional screen](../hanuman-rig-qa-2026/animated-face-clearance.json)
found no negative projected offsets in the sampled idle, run and attacks. These
are directional vertex samples, not a watertight penetration test. Crucially,
the [matched face views](../hanuman-visual-qa-2026/face-crops-v2.webp) show the
V2 wedge and fail the intended visual gate despite those measurements.

V3 is a separate test of a continuous, bilateral profile taper rather than a
line-to-skin snap. It has a maximum 6.06 mm displacement from V1 on the sampled
vertices and zero field change above Y=1.835 m, leaving the eyes and nostrils
outside its edit. Its mathematical field check samples 21,609 positions with a
minimum determinant of 0.865 and zero mirror error. Matched three-quarter and
profile views show a modest retraction without an obvious new discontinuity,
but the bright projecting seam remains. The rig and 20 sampled body-action
poses match the baseline bone/socket landmarks. V3 does not meet the visual
gate for a completed closed-mouth fix and remains an unpromoted study; a bounded
field or a rig pass alone cannot establish an art improvement.

## Rebuild the studies

From the repository root, using Python 3, NumPy and Blender 4.3.2:

```sh
python3 games/yuga-native/art/hanuman-facial-refinement-2026/refine.py
python3 games/yuga-native/art/hanuman-facial-refinement-2026/check_field.py
python3 games/yuga-native/art/hanuman-facial-refinement-2026/contact_fit.py
python3 games/yuga-native/art/hanuman-facial-refinement-2026/refine.py \
  --config games/yuga-native/art/hanuman-facial-refinement-2026/profile-refinement.json \
  --output games/yuga-native/art/hanuman-facial-refinement-2026/hanuman-face-profile-candidate.glb \
  --report games/yuga-native/art/hanuman-facial-refinement-2026/profile-report.json
blender -b -t 2 --python-exit-code 1 \
  -P games/yuga-native/art/four-hero-motion/tools/render/blender_scene.py -- \
  --hero hanuman \
  --model games/yuga-native/art/hanuman-facial-refinement-2026/hanuman-face-candidate.glb \
  --save /tmp/hanuman-face-candidate.blend --threads 2
```

The input GLB SHA-256 is
`6612e710578c2527fc1edb84cd8c2c64936cd7ec2a0b201d4a714eead870273a`.
The V1, V2 and V3 GLBs reproduced byte-for-byte in separate clean output paths;
their hashes are in the receipts. Blender files have separate digests and can
vary on resave. The fixed comparison cameras, original captures and settings are
owned by the [visual QA study](../hanuman-visual-qa-2026/README.md).

## Next correction

Avoid another blind projection. An artist should rebuild or retopologize the
lip-to-muzzle transition as a continuous surface, or fit the actual seam, upper
lip and lower lip together with controlled material response. Evaluate front,
three-quarter and silhouette views under grazing and soft lights, including an
open mouth and motion; verify eyeball clearance and oral deformation in a
separate facial-rig study. Test the ordinary game camera and the target GPU
before promoting an exported candidate. These actions remain future work.
