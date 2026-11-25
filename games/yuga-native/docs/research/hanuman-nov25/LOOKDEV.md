# From generated Hanuman art to Blender

The ImageGen direction called for a full-body realistic CG Hanuman with age-patinated bronze, madder cloth, an arched tail and a fluted gada. The camera brief called for a grounded three-quarter stance, a broad warm grazing key, a cool separating rim, damp slate and the softly lit architecture of an original dusk court. The generation used the supplied PDF’s Hanuman reference plus two images of our own rig for identity. [Generated keyframe](../../../art/hanuman/lookdev/hanuman-imagegen-reference.png)

The second generation used that keyframe as the palette reference for a flat red fabric albedo. The prompt requested a straight-on scan with no folds or cast shadows, a fine axis-aligned weave and matching tile edges. The result has a mostly uniform grain, with measurable seam variation. [Generated cloth color map](../../../art/hanuman/lookdev/madder-cloth-imagegen-albedo.png)

The [Blender transfer script](../../../tools/hanuman-art/apply_lookdev.py) opens the exact editable R5 scene. It adds a presentation scene with its own camera, lamps, material overrides and an image reference that stays in the viewport. Both scenes share mesh, skeleton and action data in the saved file. The generated cloth is packed and connected to the madder material’s UV color input in the new scene, while its tangent normal stays on the existing source. The peer reopened the packed file away from the inputs, checked both reference hashes, and took the next edit to give the weave a finer scale on the rig.

The downloadable look development scene and its Cycles still show the real model under the translated material and lighting choices. The generated keyframe remains the target for added anatomy, embroidered shapes and the full environment. None of that background is composited into the Cycles proof. The packed look scene is an editable comparison and carries the original motion. The playable GLB and native trial retain their separately verified materials.

The second look repeats only the generated color texture three times per source UV span. The neighboring normal map keeps its original UVs. The art reviewer opened the two matched images and the packed blend. In the sampled thigh crop, residual grayscale contrast dropped from 7.423 to 4.634 counts after removing the local average, matching the visible change from large dots to fine cloth. [Final Cycles still](../../../art/hanuman/lookdev/hanuman-lookdev.png) · [Transfer receipt](../../../art/hanuman/lookdev/hanuman-lookdev.json) · [Independent reopen checks](../../../art/hanuman/lookdev/review-r2.json)

To reproduce the look from the repository root, use Blender 4.3.2 and a fresh output directory:

```sh
blender -b games/yuga-native/art/hanuman/hanuman.blend -t 2 --python-exit-code 1 \
  --python games/yuga-native/tools/hanuman-art/apply_lookdev.py -- \
  --source-sha256 b27582783f7a68f35225cd0545e7e31e3c09762c736da1e6a689cabaa400e589 \
  --reference games/yuga-native/art/hanuman/lookdev/hanuman-imagegen-reference.png \
  --reference-kind imagegen \
  --cloth-texture games/yuga-native/art/hanuman/lookdev/madder-cloth-imagegen-albedo.png \
  --profile games/yuga-native/tools/hanuman-art/teal-dusk-look.json \
  --output /tmp/hanuman-look/hanuman-lookdev.blend \
  --render /tmp/hanuman-look/hanuman-lookdev.png
```
