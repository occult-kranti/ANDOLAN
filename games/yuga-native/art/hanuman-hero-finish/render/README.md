# Photograph the enhanced Hanuman

The studio compares the [original animated Hanuman](../../four-hero-motion/models/hanuman.glb) and the [enhanced model](../models/hanuman-enhanced.glb) with their embedded textures and native animation tracks. Blender evaluates the skinned meshes for every photograph and film frame. The matched studies use an absolute lens, light rig, pose, camera transform and Cycles sampler seed shared by the original and enhanced model.

## Reproduce the media

Run from the repository root in Blender 4.3.2 with Python packages NumPy and Pillow and FFmpeg's H.264 encoder on PATH. This edition used the official Intel Open Image Denoise 2.5.1 CPU tool for the presentation pass. Point `OIDN_EXECUTABLE` at `oidnDenoise` or put it on PATH. [Open Image Denoise releases](https://github.com/RenderKit/oidn/releases/tag/v2.5.1)

```sh
blender -b -t 2 --python-exit-code 1 \
  -P games/yuga-native/art/hanuman-hero-finish/render/studio.py -- \
  --take all --threads 2 --samples 32 --movie-samples 5 --work /tmp/yuga-hanuman-studio
```

Choose `baseline` and `enhanced` to render the two sets of images independently, then `contact` to assemble the matched sheet. The output includes each original PNG’s digest and the world matrices of the two cameras. Choose `beauty` to render the editorial portrait, or `movie` to render and encode only the performance. Use `--output` to export to a separate media directory.

## Read the views

The first matched column exposes the muzzle, eye and temple from three quarters. The second preserves the entire idle silhouette. The third shows the crown and nape from directly behind. The fourth uses a rear-quarter view at 87.5% of Mountain Pulse to look across the tail’s return. Both tail images have the same recorded inset crop. The separate editorial portrait uses a dark teal studio sweep, a warm key, a cool edge and a small eye catch. The portrait receipt records the measured studio light powers and exposure used to retain the copper highlights.

The 24 fps film opens on the idle portrait, widens to retain both feet and the gada throughout Mountain Pulse, then views the impact and recovery from the opposite quarter. Per-shot JSON records the actual source clip phase, camera matrix, rig joint centers, framing and media hashes. World-space coordinates are Blender metres with Z up. Each movie frame evaluates its source phase independently. The [wide-shot framing receipt](../media/video/hanuman-framing.json) measures every deformed vertex against the actual camera throughout all 42 frames. Regenerate it with `--take framing`.

Run `python games/yuga-native/art/hanuman-hero-finish/render/verify.py` to decode the entire showcase and check the shared camera transforms, major-joint registration, source hashes, frame counts and measured motion.
