# Continue the Hanuman build

The playable deliverable is the Rust/Wasm Confluence ZIP. The single-file game carries the finished hero, meshes, textures, animation and room client. For the actual mesh, start with its matched Cycles photographs. The separately generated portrait guides the title screen and the next sculpt pass. [Game entry and download](README.md) · [Matched photographs](media/images/matched-studies.webp) · [Target artwork](design/hanuman-portrait-target.webp)

| Change | Edit first | Inspect the result |
| --- | --- | --- |
| Eyeline, muzzle, head silhouette and groom | [Artist controls](design/groom.json) and [sculpt](tools/sculpt.py) | [Groom source and region inventory](design/SCULPT.md), matched front, rear and recovery views |
| Facial poses | [Three-action Blender library and fitted corrections](expressions/README.md) | Inspect both eyelids in the calibrated close-up and apply the actions in a separate artist scene. Gameplay has eleven shipped clips. |
| Metal, textile, skin or hair response | [Surface authoring](tools/surfaces.py) | [Swatches](data/surface-compare.webp) and the dressed model under fixed lights |
| Secondary tail motion | [Four local rotation curves](tools/motion.py) | [Sampled recoil](evidence/combined-tail-recoil.json) and [pose overlay](media/images/tail-recoil.webp) |
| Ability ranges and interactions | [Native design profile](../../assets/design/hanuman-ability-kit.json) and [Rust combat](../../../yuga-rust/src/combat.rs) | [Actual input and timing guide](GAMEPLAY.md), then an extracted release in practice and a private room |
| Practice hints, targeting and remote detail | [Practice progress](../../../yuga-rust/web/practice-coach.ts), [HUD](../../../yuga-rust/web/main.ts), [screen height helper](../../../yuga-rust/web/groom-detail.ts) | Exercise failed and successful actions, reset, and both directions across the distant-groom thresholds |
| Camera, lights, matched images and motion reel | [Cycles studio](render/studio.py) | [Render settings and controls](render/README.md), [performance film](media/video/hanuman-showcase.mp4?raw=true) |

## Rebuild from the repository checkout

Use Blender 4.3.2 with NumPy and Pillow. The assembler checks the donor SHA before shaping the face and groom, applying the new material maps and modifying the recovery motion. Run the assembly twice into separate output directories if you change the geometry or material generator. Compare the GLB bytes. Blender project saves carry their own file digests. [Donor rig](../four-hero-motion/models/hanuman.glb) · [Build receipt](evidence/build.json) · [Credits](../hanuman/NOTICE.md)

```sh
finish=games/yuga-native/art/hanuman-hero-finish
studio=games/yuga-native/art/four-hero-motion
python3 "$finish/tools/finish.py"
blender -b -t 2 --python-exit-code 1 -P "$studio/tools/render/blender_scene.py" -- \
  --hero hanuman --model "$finish/models/hanuman-enhanced.glb" --save "$finish/blender/hanuman.blend"
blender -b -t 1 --python-exit-code 1 -P "$finish/tools/verify_studio.py"
python3 games/yuga-rust/tools/build_web.py
node games/yuga-rust/tools/test_hanuman_release.mjs --zip games/yuga-rust/dist/yuga-rust-confluence.zip
```

The final model SHA-256 is `6612e710578c2527fc1edb84cd8c2c64936cd7ec2a0b201d4a714eead870273a`. Check that digest against the embedded asset in the actual distributable before updating a release. The saved editable studio has 32 packed texture files, six action strips and zero external Blender libraries. The separate groom scene exposes the five editable surfaces combined into one draw in the game. [Packaged game proof](evidence/packaged-game.json) · [Editable studio proof](evidence/editable-scene.json) · [Official glTF validation](evidence/gltf-validation.json)

## Where this version ends

The near mesh has 143,432 triangles including 37,584 for the added groom. On distant remote heroes, the renderer removes the extra groom below 55 CSS pixels of projected height and restores it above 70. The original hair, tail, armor and weapon remain in the silhouette. The rule uses the camera and viewport, so players can move or resize the window while watching a teammate. The renderer always keeps the local hero's full groom. Measuring the real GPU cost is an open roadmap item. [Runtime implementation](../../../yuga-rust/web/scene.ts) · [Distance tests](../../../yuga-rust/tools/test_groom_detail.mjs) · [Visible and hidden states in the packaged WebGL renderer](evidence/groom-visibility.json)

The central face still reads as a smooth sculpt under close lighting. Some nape and cheek tips blend into the skin by a few millimetres, and the trousers stretch the textile border around the knee. Compare these areas with the generated portrait and the dressed model before accepting a subsequent sculpt. Preserve the readable amber eyes and the right-wrist gada grip during revisions. [Portrait target](design/PORTRAIT.md) · [Next work and acceptance measures](ROADMAP.md)

## Distribution

The release groups the playable game, both artist studios, the animator book and the direct media downloads under one tag. The distribution branch holds the two verified archives in chunks. Its GitHub Actions job reconstructs the archives and extracts the individual files, then checks every asset digest before attaching it to the release. A future production round should create a new release and pin its own digests. [Studio release](https://github.com/occult-kranti/ANDOLAN/releases/tag/yuga-four-hero-motion-studio-2026-11-25) · [Distribution source](https://github.com/occult-kranti/ANDOLAN/tree/distribution/hanuman-four-hero-studio-2026-11-25)
