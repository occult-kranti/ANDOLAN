# Vanara Sena · Blender motion study

This is an editable, original **offline animation study** for Hanuman's Vanara Sena. It uses the project's existing 167-joint Hanuman, the `cast2` and `fire` actions, an additional left-arm IK path, a thin gold strand, five tinted spectral stand-ins, a marked ground zone and drifting petals. The five stand-ins reuse Hanuman's skinned mesh: they are not separately sculpted Vanara warriors or autonomous NPCs. Their animation is for this studio scene; the playable game uses its own Rust authority and browser presentation.

[Open the editable Blender scene](vanara-sena-study.blend) · [Watch the rendered preview](preview/vanara-sena-preview.mp4) · [Raw contact sheet](preview/contact-sheet.png) · [Timeline](timeline.json) · [Reopened-scene verification](scene-verification.json) · [Rebuild script](build.py)

## Animation and authority timings

The study runs at 30 frames per second against the planned 20 Hz ability clock. Its timeline maps the **start** to frame 1, **release and initial impact** to frame 19 (0.6 s) and **field end** to frame 79 (2.6 s). A close-up studies the hand, strand and breath before a camera cut to the marked three-metre-radius zone. The five spirits appear after release, briefly animate with the existing gada strike, and disperse by the field end. The extra twelve frames allow a quiet return. [Measured timeline and source hashes](timeline.json)

The artist controls are in `Sena · animator controls`; spirit rigs, target rings, strand and petals are in `Sena · spirit study effects`. The left-arm IK is a **visual gesture study**, not a physically verified finger-to-hair or hand-to-mouth contact solve. The ghosts use shared spectral material overrides and weighted copies of the original hero. They are intentionally illustrative; do not promote the five high-detail duplicate rigs as a real-time optimization.

## Rebuild and verify

From the repository root with Blender 4.3.2, NumPy and Pillow:

```sh
OPENBLAS_NUM_THREADS=1 blender -b -t 2 --python-exit-code 1 \
  -P games/yuga-native/art/vanara-sena-motion-2026/build.py
OPENBLAS_NUM_THREADS=1 blender -b -t 1 --python-exit-code 1 \
  -P games/yuga-native/art/vanara-sena-motion-2026/verify.py
```

The source scene and source model are checked against pinned SHA-256 values before building. The script saves a separate, packed scene and does not alter them. Blender project bytes may change on resave. The verifier reopens the exact scene, checks the 167-joint caster, all five rigs, frame timings, material slots, packed images and sampled finite wrist/target/ghost transforms. This is not a continuous deformation, contact, runtime performance or visual-quality test.

The preview is a **3.1-second, 480 × 270, 10 fps** CPU render of 31 samples from the 30 fps timeline. Each frame used three Cycles samples. Original noisy PNG frames are preserved; the H.264 film has temporal noise reduction and has no sound. A separate [OIDN-filtered contact sheet](preview/contact-sheet-denoised.png) improves presentation but smooths details. [Render settings and frame hashes](preview/render-receipt.json) · [Full video decode check](preview/media-verification.json) · [Denoiser receipt](preview/denoised/receipt.json). To regenerate the preview (requires FFmpeg), then verify it:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=2 blender -b -t 2 --python-exit-code 1 \
  -P games/yuga-native/art/vanara-sena-motion-2026/render.py
python3 games/yuga-native/art/vanara-sena-motion-2026/verify_media.py
```

The audio-free low-sample film is a timing and composition aid, not a polished animation release. Denoising or temporal filtering can suppress or invent fine details; inspect the raw frames when judging contact or silhouette.

To regenerate the optional display sheet using the official Open Image Denoise CLI, pass its executable path:

```sh
OPENBLAS_NUM_THREADS=1 python3 games/yuga-native/art/vanara-sena-motion-2026/denoise_sheet.py \
  --oidn /path/to/oidnDenoise
```

## Visual and gameplay boundaries

The illustrated pluck and breath is a proposed performance direction. Confirm actual hair/finger contact, elbow clearance, garment and mace intersections, and attack/recovery transitions in artist review before exporting a production character action. The gold strand and five figures are visual storytelling; all damage, eligibility, timing, cover and interruption in the playable ability must come from the game authority, never from this movie. Reference art is separate from geometry and this scene does not claim to reproduce another game's footage or assets.
