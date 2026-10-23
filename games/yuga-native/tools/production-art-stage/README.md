# Reuse-first production art stage

This isolated Blender workflow reuses the exact accepted Rama GLB, its 164-bone rig and embedded idle pose, the existing Lanka court/nature kits, and the generated diya source. It adopts one verified CC0 Poly Haven sandstone texture set for four court paving materials. It does not generate another hero from primitives, edit canonical sources, or replace the runtime scene.

```sh
blender -b -t 2 --python-exit-code 1 --python games/yuga-native/tools/production-art-stage/build_stage.py -- \
  --output /absolute/fresh/stage-output --samples 16 --render
blender -b -t 2 --python-exit-code 1 --python games/yuga-native/tools/production-art-stage/verify_scene.py -- \
  /absolute/fresh/stage-output/lanka-water-stage.blend \
  /absolute/fresh/stage-output/reopened-verification.json
```

The output directory must be new. The build retains a compressed, packed editable scene, four fixed-pose hero views, one contextual court view and a manifest with source/output hashes, cameras, shader adoption, image inventory and exact render settings. Cycles CPU uses two threads and no denoiser. Run only in the shared heavy-render lane, after capacity and ownership checks.

The four hero cameras reuse the existing Q3 review camera contracts; they show the **accepted current hero**, not that candidate's geometry. They share embedded idle frame 1 and new lighting. They are new presentation views, not matched before/after quality evidence or acceptance of a replacement hair master. The contextual scene uses local water-plane set dressing and relocated court geometry; it is not an exported gameplay map or a collision check.

[The retained art packet](../../art/production-stage-oct23/README.md) owns actual execution, reviewed images and remaining gates. Artist-controlled hair flow/joins, garment construction, continuous contact/animation, diya topology/LODs/flame effects and gameplay-distance acceptance remain open. Rendered presentation alone cannot establish Deadlock-level graphics or physical-GPU performance.

## Newly generated unrigged hero source

```sh
blender -b -t 2 --python-exit-code 1 --python games/yuga-native/tools/production-art-stage/inspect_generated_hero.py -- \
  --source games/yuga-native/art/production-stage-oct23/hero-source/rama-generated.glb \
  --output /absolute/fresh/generated-source-intake
```

This source-specific intake requires the bound GLB hash, validates finite positions and image dimensions, records rig/action/UV/material counts, renders front/rear three-quarter views and retains a packed editable scene. Its exact current input is unrigged and has no animations. Source coordinates are preserved; display framing does not qualify real-world scale. The current-avatar workflow and generated-source workflow have separate manifests and acceptance.
