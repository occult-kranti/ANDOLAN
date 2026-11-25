# Hanuman matched visual review

This review renders the real weighted Hanuman mesh in Blender, with the same idle action phase and studio camera, lighting, Cycles seed and AgX transform for each model. It is an art review aid; these images do not establish game-engine appearance, continuous animation quality, hardware performance or likeness to the generated target.

## Results

| Model | SHA-256 | Status in this still review |
| --- | --- | --- |
| Existing playable model | `6612e710578c2527fc1edb84cd8c2c64936cd7ec2a0b201d4a714eead870273a` | Baseline. The face remains smoothly shaded, the profile has a projecting mouth seam, and the cheek locks obscure the eye in profile. |
| [Facial candidate v1](../hanuman-facial-refinement-2026/hanuman-face-candidate.glb) | `257ff4daf8694d682acc4dbfd171729ed2d5575225cfa9259533c1e9eb113abf` | The muzzle and lower-lip contour change is visible in the close crops but subtle at full figure. It does not resolve the projecting mouth seam or the larger gap to the portrait target. |
| [Contact-fit candidate v2](../hanuman-facial-refinement-2026/hanuman-face-contact-candidate.glb) | `ce238b5d020ff8e4233cf70eca58502130afef87ebf199c929027f32bfc16b75` | **Rejected for the closed-mouth profile gate** in this fixed studio view: the bright, wedge-like seam is more conspicuous than in the baseline and v1. Smaller measured surface distances alone do not show an acceptable silhouette. |
| [Profile candidate v3](../hanuman-facial-refinement-2026/hanuman-face-profile-candidate.glb) | `ae143cd63e4ac47a4f0f95e4d8f735f9bd7ee5d88ff11d958fa4cb06b27a55a8` | The lip tip is retracted slightly from v1, but the bright projecting seam remains. This is a limited study, not an accepted closed-mouth fix; continuous facial motion is unverified. |
| [Aperiodic surface study](../hanuman-surface-study-2026/hanuman-surface-noise-candidate.glb) | `334cfbedc552a4628ebe1ebe98b4a9d6e581344c018d16821b2a1230dd926fc1` | A material-only variant of facial v1, not geometric fur. The arm change is slight in the fixed views; added fine surface detail is not reliably distinguishable in the downsampled figure by this reviewer. |

[Baseline vs v1, five views](matched-comparison.webp) · [Baseline vs v2, five views](matched-contact-v2.webp) · [Three-way enlarged face crops](face-crops-v2.webp) · [Source reference illustration](../hanuman-hero-finish/design/hanuman-portrait-target.webp)

The subsequent [v1 vs v3 close-ups](face-crops-profile-v3.webp) use a hash-checked subset of the earlier v1 captures. The associated [full-frame comparison](matched-profile-v3.webp) and [`profile-v3`](profile-v3/) raw captures cover the three-quarter and profile views only.

The surface review has a matched [face study](face-crops-surface.webp), [arm study](matched-surface-arm.webp) and [full five-view board](matched-surface.webp). At the original figure resolution, the denoised mean absolute difference from facial v1 is 0.31/255 RGB levels in the selected face rectangle and 1.17/255 in the selected arm rectangle. After downsampling to a roughly 175-pixel-tall figure, the corresponding values are 0.25 and 1.19 levels. [Filtered measurements](surface-measure-filtered/surface-differences.json) · [Raw measurements](surface-measure-raw/surface-differences.json) · [Simulated scale](surface-measure-filtered/gameplay-scale-simulation.png). These are display-referred pixel differences in one still, not a formal perception test or a gameplay capture.

The contact sheet displays Open Image Denoise filtered copies. Original 480 × 622, 12-sample Cycles renders are retained in [`baseline`](baseline/), [`candidate`](candidate/), [`contact-candidate`](contact-candidate/) and [`surface-candidate`](surface-candidate/), alongside source hashes and camera matrices; the arm-only views are in [`candidate-arm`](candidate-arm/) and [`surface-arm`](surface-arm/). Denoising can soften or invent fine detail, and the crops are enlarged from these same images; consult the raw images before making a geometry decision. The profile issue was also reviewed on the noisy raw captures. The [`qa.json`](qa.json) record covers comparison integrity only.

## Reproduce a set of views

From the repository root, using Blender 4.3.2 and the existing project dependencies:

```sh
blender -b -t 2 --python-exit-code 1 \
  -P games/yuga-native/art/hanuman-visual-qa-2026/render_views.py -- \
  --model games/yuga-native/art/hanuman-hero-finish/models/hanuman-enhanced.glb \
  --output /tmp/hanuman-review-baseline --samples 12
```

Repeat with `--model` pointing to a candidate and a different output directory. The script uses the existing [`studio.py`](../hanuman-hero-finish/render/studio.py) and its rig import, fixed camera and light functions. The archived results above contain five views. The script now defaults to six, including an additional `arm-front` view for surface checks. Any view subset can be requested, for example with `--views face-front face-three-quarter face-profile` or `--views arm-front`.

To build a raw comparison board, run the following from a Python environment with Pillow:

```sh
python3 games/yuga-native/art/hanuman-visual-qa-2026/compare_views.py \
  /tmp/hanuman-review-baseline /tmp/hanuman-review-candidate \
  --output /tmp/hanuman-review.webp
```

The board generator rejects differing camera matrices, pose phases, lighting, sampling and image hashes. `face_crops.py` produces enlarged face details, and `select_views.py` copies a named, hash-checked subset of an existing render set when a revision needs only specific angles. `filter_views.py` can make separate LDR sRGB display copies using an independently supplied [Open Image Denoise CLI](https://www.openimagedenoise.org/); it preserves source hashes and records the binary digest. Apply the same filter to every set before comparing. The packaged examples use OIDN 2.5.1 with one CPU thread and no auxiliary passes. Do not use the filtered result as the sole evidence of fine geometry or texture detail.

The next check is a revised mouth/nostril fit compared at front, three-quarter and profile, followed by continuous-expression and in-game verification. The five-view sheet does not replace that work.
