# Hanuman at teal dusk

The look development scene uses the [generated concept](hanuman-imagegen-reference.png)
to direct warm grazing light, a cool rim, darker bell metal and wet slate.
The [generated madder swatch](madder-cloth-imagegen-albedo.png) supplies the
color of the red drape, trousers, and back strap. Both images are packed into
the editable Blender file.

- [Open the Blender look](hanuman-lookdev.blend) in Blender 4.3 or newer.
  The scene menu switches between `Hanuman - Look Development` and the
  original studio `Scene`. The ImageGen board is visible in the
  development viewport. Camera, lights, world and material nodes are
  editable per scene. Meshes, armature data and actions are shared between them.
- [View the actual Blender render](hanuman-lookdev.png) at 800 × 600.
  Cycles CPU drew the posed, textured model using a maximum of 48 samples.
  The key art board is excluded from rendering and the compositor is disabled.
- [Compare the initial render](hanuman-lookdev-r1.png). The second pass keeps
  the same camera, light and pose and repeats the cloth color three times
  more densely. This reduces the coarse dots in the trousers. The imported
  swatch has small differences across opposite edges. Its original pixel
  values are retained.
- [Review hashes and checks](review-r2.json). The archived Blender file
  reopened alone with 18 packed images. Both generated PNGs matched their
  input bytes. The same normal map and normal coordinates serve the fabric
  in both scenes. [Render receipt](hanuman-lookdev.json) · [Initial receipt](receipt-r1.json)

This scene polishes the appearance of the round-five rig in a studio. The
playable hero remains the separate [game export](../../../assets/heroes/hanuman/hanuman.glb).
Groom breakup, finer facial sculpt and richer clothing volumes remain work
for a character production pass.

## Reproduce the look

Run from the ANDOLAN repository root and use new output paths.

```sh
art=games/yuga-native/art/hanuman
blender -b "$art/hanuman.blend" -t 2 --python-exit-code 1 \
  --python games/yuga-native/tools/hanuman-art/apply_lookdev.py -- \
  --source-sha256 b27582783f7a68f35225cd0545e7e31e3c09762c736da1e6a689cabaa400e589 \
  --reference "$art/lookdev/hanuman-imagegen-reference.png" --reference-kind imagegen \
  --cloth-texture "$art/lookdev/madder-cloth-imagegen-albedo.png" \
  --profile games/yuga-native/tools/hanuman-art/teal-dusk-look.json \
  --output /tmp/yuga-hanuman-look.blend --render /tmp/yuga-hanuman-look.png
```

The [look profile](../../../tools/hanuman-art/teal-dusk-look.json) holds
camera, lighting, tint and weave settings independently of the build script.
