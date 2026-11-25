# Hanuman · reversible skin surface study

This is a **rejected runtime candidate** and an editable experiment, not a replacement for the shipped hero. It adapts the project's already skinned Hanuman and its existing textures: no external photographs, game assets or generated textures were imported. The artistic target is a slightly richer cheek and arm surface, guided by the separately generated turnaround, while preserving the current silhouette, 167-joint rig and eleven actions. Painted relief is not strand geometry or a photographic skin scan.

The first analytic pass produced conspicuously regular stripes in the texture map; it is retained as a rejected experiment in [the first config](surface.json) and [its report](surface-report.json). The preferred **aperiodic** candidate uses seeded, anisotropic 3D value noise, with a broad region mask fitted to rest-space cheek and arm positions. It begins from the [facial v1 candidate](../hanuman-facial-refinement-2026/hanuman-face-candidate.glb), whose SHA-256 is `257ff4daf8694d682acc4dbfd171729ed2d5575225cfa9259533c1e9eb113abf`.

- [Aperiodic candidate GLB](hanuman-surface-noise-candidate.glb), SHA-256 `334cfbedc552a4628ebe1ebe98b4a9d6e581344c018d16821b2a1230dd926fc1`.
- [Parameters](surface-noise.json) · [generator](surface.py) · [normal, base-color and metallic-roughness PNG maps](maps-noise/) · [generation receipt](surface-noise-report.json).
- [Material byte comparison](material-validation.json) · [rig and animation structure comparison](structural-validation.json) · [Khronos glTF Validator comparison](gltf-validation.json).

## What changed

The generator barycentrically rasterizes the existing body mesh's `POSITION` into `TEXCOORD_0`, builds smooth spatial masks, pads island edges for filtering and rejects overlapping UV samples that disagree by more than 20 mm after mirrored-X comparison. On this 1024 × 1024 raster it covered 506,703 texels; its overlap test detected zero conflicts. This grid-based test cannot prove the absence of all UV seams, mirrored orientation artifacts or filtering problems.

Only `Vanara · painted copper anatomy` receives three new textures. The normal and metallic-roughness maps are linear glTF data; the new white-to-light-gray base-color texture is sRGB and multiplies the existing vertex pigment. The original 0.255 normal scale and metallic/roughness factors remain unchanged. Other materials and all original binary data remain intact. The generator does not create face wrinkles, hair strands or silhouette details.

The candidate has the same 143,432 triangles, 18 material slots, skin joints, vertex weights, inverse binds and animation tracks as the facial v1 source. The independent glTF Validator reports **0 errors and 1 warning** for both files; the warning is the inherited skinned-mesh non-root warning. The structural comparison is not an art or motion acceptance. Both the original analytic version and the aperiodic version reproduced byte-for-byte on a second local run.

The [matched face crops](../hanuman-visual-qa-2026/face-crops-surface.webp) and [arm comparison](../hanuman-visual-qa-2026/matched-surface-arm.webp) show a very subtle change that does not convincingly move the model toward the requested reference. At the source figure resolution the filtered mean absolute RGB difference is **0.31/255 for the face and 1.17/255 for the arm**; after downsampling to an approximately 175-pixel-tall hero it is **0.25/255 and 1.19/255** respectively. These are fixed-still pixel measurements, not a perceptual threshold or live-game test. [Measurements and simulated scale](../hanuman-visual-qa-2026/surface-measure-filtered/surface-differences.json)

The surface pass is therefore rejected for runtime promotion in its current form. Three additional 1024² textures would require roughly **12 MiB uncompressed RGBA**, or about **16 MiB including a complete mip chain**, before considering renderer format, original texture reuse or loading of unused source maps. Those are arithmetic estimates, not measured GPU allocation. Hardware profiling, UV seams, mip behavior and screen-distance readability remain open.

## Reproduce

With Python 3, NumPy, Pillow and SciPy installed, run from the repository root:

```sh
art=games/yuga-native/art/hanuman-surface-study-2026
OPENBLAS_NUM_THREADS=1 python3 "$art/surface.py" --config "$art/surface-noise.json" \
  --output /tmp/hanuman-surface.glb --maps /tmp/hanuman-surface-maps \
  --report /tmp/hanuman-surface-report.json
python3 "$art/verify_material.py" --candidate /tmp/hanuman-surface.glb \
  --report /tmp/hanuman-material-validation.json
```

The optional `--source` also supports the separately pinned contact-fit candidate for experiments, but the face-contact fit failed visual review and is not the recommended starting point. The generator checks its allowed input digests and refuses to overwrite the source. Run the project's matched Cycles and browser-game checks on any candidate before deciding whether to ship it.
