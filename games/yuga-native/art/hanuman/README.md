# Hanuman · The Returning Leap

The editable Blender source contains the anatomical mesh, 167-joint rig, individual
garment and jewelry surfaces, articulated tail, modeled gada, packed materials,
studio camera and lights, and 11 actions. The [game GLB](../../assets/heroes/hanuman/hanuman.glb)
is a consolidated export with four normalized skin influences, 17 surfaces, 14
embedded images, and three boneside landmarks: gada grip, gada head and tail tip.
It faces +Z in an upright +Y glTF coordinate frame.

- [hanuman.blend](hanuman.blend) opens in Blender 4.3 or newer.
- [Final portrait](hanuman-face-denoised.png) uses Open Image Denoise on the
  [original round-five 640 × 640 Cycles render](hanuman-face.png).
- [Round-four rear](hanuman-rear-r4.png) shows the corrected rear harness and
  calf cuffs. Round five changes only the face.
- [Round-three studio figure](hanuman-beauty-denoised.png) and its
  [original render](hanuman-beauty.png) retain the earlier look for comparison.
- [Asset manifest](manifest.json) pins the donor inputs, geometry counts,
  clip names and exact GLB.
- [Build receipt](receipt.json) pins the scene, renderer and output files.
- [Temple court keyframe reconstruction](match/README.md) includes the rebuilt portrait scene and comparison reviews.
- [ImageGen-guided look development](lookdev/README.md) includes the actual
  Cycles render, packed editable scene, concept and madder fabric swatch.
- [Source recipe](../../tools/hanuman-art/build.py) rebuilds geometry and
  animation from the existing YUGA Hanuman authoring pipeline.
- [Provenance](NOTICE.md) identifies the original and reused components.
- [Generated art and Blender material transfer](../../docs/research/hanuman-nov25/LOOKDEV.md) records the alternate dusk look, source images and verified color-map connection.
- [Studio motion](reels/hanuman-motion.mp4) and [native trial](reels/hanuman-gameplay.mp4) show the authored clips and game effects from two different cameras.

This is the Hanuman trial asset. Export tests demonstrate that the result can
be animated and imported. Studio stills do not establish run-cycle contact,
cloth collision at every pose, or the frame rate of a full match.

## Five art rounds

| Round | Result | Review decision |
|---|---|---|
| 1 | Existing CC0 body and mace motion reused. Added continuous facial sculpt, temple bronze armor, golden gada, red drapery and the four-joint tail. | Face still read too human. Disconnected chest pieces, difficult shoulder transition and teeth-shaped cloth intersections made the outfit hard to read. Native Blender omitted the integrated denoiser. Retained the render failure and ran unfiltered Cycles. |
| 2 | Darkened skin, deepened muzzle, corrected texture color encoding, replaced two breastplates with one cuirass, added unique planted `tail_sweep` and `mountain_pulse` clips. Export reduced from 141,764 to 96,988 triangles and included tangents. | Fitted drapes intersected and fragmented at the belt. In the studio, idle soles were approximately 30.6 mm above the plinth. |
| 3 | Replaced drape projection with separate smooth thigh wraps, simplified hems, widened belt, corrected per-face skin versus fabric tint, added a rear harness and grounded the studio using evaluated sandal geometry. | The exact studio original confirms continuous belt and hems in the reviewed pose and visibly supported feet. Runtime motion retains the same authored foot heights. |
| 4 | Shared dorsal projection and attachment across the plate and crossing sash. Added rolled calf cuffs and darker iris/pupil depth. Refined gilt surface patina. | The rear Cycles image shows a continuous sash over its shell. Across 589 source vertices on the crossing, the closest measured rest-space clearance is 16.16 mm and the crossing pieces share the same spine bone. The round-four portrait exposed a lip crease that still read too black. |
| 5 | Replaced the thick dark lip line with fitted lip volumes, tapered russet crease, and soft copper variation around the muzzle and cheeks. | The matched close-up shows the quieter lip and nostril profile. The rear-clearance test reproduced round four exactly. The final 105,848-triangle export keeps 167 joints, 11 clips and three moving landmarks. |

The old browser model is retained as a comparison. Neither its rig nor the
original Rama assets are overwritten by this build. See the hero design and
panel review for effects behavior and gameplay evidence. More detailed work
remains in facial rigging, material and groom detail, hand contact, tear-free
cloth through the full move set, LODs, and profiling a physical GPU under
match load.

## Rebuild and render

Run from the ANDOLAN repository root with Blender 4.3.2. Use a fresh directory.

```sh
blender -b --factory-startup -t 2 --python-exit-code 1 \
  --python games/yuga-native/tools/hanuman-art/build.py -- \
  --output /tmp/yuga-hanuman --render --views face
```

The builder writes the GLB, compressed editable scene, an asset manifest and
any requested images. The saved scene uses Cycles CPU, a maximum of 48 samples,
adaptive sampling and AgX. The Debian Blender build lacks integrated OIDN.
The separate filter preserves the rendered original and produces a clearly
named derivative. The reviewed tool is Linux x64 OIDN 2.5.1 from
[RenderKit's release](https://github.com/RenderKit/oidn/releases/tag/v2.5.1).
The official asset SHA-256 is
`743c3e2aff8c220d5d70fe6cb970fb3d36f2702d2693c61d1d148e404cf37cd6`.

Render additional views from the editable scene without reexporting geometry:

```sh
blender -b /tmp/yuga-hanuman/hanuman.blend -t 2 --python-exit-code 1 \
  --python games/yuga-native/tools/hanuman-art/render.py -- \
  --output /tmp/yuga-hanuman rear profile
python3 games/yuga-native/tools/hanuman-art/denoise.py \
  --oidn /path/to/oidnDenoise /tmp/yuga-hanuman/hanuman-face.png
```

The [dorsal clearance receipt](dorsal-clearance.json) captures the model-space
check used during the last two rounds. Reproduce it with Blender on the saved
source, using `--python games/yuga-native/tools/hanuman-art/check_dorsal.py`
and passing `-- --output /tmp/hanuman-dorsal.json`.
