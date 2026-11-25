# Render the four hero films

The MP4s use the original animated GLBs, the Lanka courtyard, and YUGA’s PlayCanvas PBR lighting and geometry helpers. Each video frame evaluates a named skeletal action. The camera, timing, and presentation effects are authored for the study. The clips in the asset keep their original timing. The four samples in each shot’s JSON receipt capture world-space bone positions, quaternions, and the camera transform.

## Render an MP4

From the repository root, install the dependencies in the root lockfile and Playwright Chromium. Make FFmpeg with H.264 encoding available on PATH. Set `PLAYWRIGHT_CHROMIUM_EXECUTABLE` to a local Chromium binary if necessary.

```sh
node games/yuga-native/art/four-hero-motion/tools/render/film.mjs
```

By default the renderer rebuilds the enhanced Hanuman mesh and the near-detail Rama model from their tracked native inputs. Hanuman uses the Rust `hero_export` binary in `games/yuga-rust/target/release` or builds it with Cargo. Rama’s near-detail pack uses Python 3 and the recorded controller poses. Shiva and Krishna use the GLBs in the collection’s `models` folder. All data is served over an ephemeral loopback port during export.

To work on a single hero, choose its name. The following command renders one image per camera shot and omits video encoding.

```sh
node games/yuga-native/art/four-hero-motion/tools/render/film.mjs rama --pilot --stills /tmp/rama-camera-check
```

Use `--input` with a single hero to supply an existing compatible motion GLB. Use `--output` to write the H.264 MP4 and JSON receipt to a different directory. `--stills` also works on a full render. Edit `shots.json` to adjust action sampling, camera angle, distance, focal target, or presentation timing. Captions and effects are separate from the bone animation. Use `--gpu software` to request Chromium SwiftShader explicitly. To rerender individual shots, use `--pick fire,mountain_pulse --output /tmp/hanuman-retakes`. A filtered render retains the source timings and generates its own pose trace.

For the Shiva and Krishna fixed-camera shots, the renderer photographs the original static courtyard once, then composites the fully animated PBR character with its contact shadow over that plate. Moving cameras render the courtyard geometry and animated mesh together on every frame.

## Edit the shots in Blender

The companion script assembles the same clip sequence, camera timing, and original courtyard in a packed Blender file. Each shot is an editable NLA strip. Timeline markers identify the actions. The supplied [Blender projects](../../blender/) open directly with textures packed. Their physical area lights, camera tracks, ability effect objects and animation strips are editable. The MP4 captions and PlayCanvas effect treatment are implemented in `scene.ts`. [Project checks](../../blender/manifest.json)

```sh
blender -b -t 3 -P games/yuga-native/art/four-hero-motion/tools/render/blender_scene.py -- \
  --hero hanuman --model games/yuga-native/art/four-hero-motion/models/hanuman.glb \
  --save /tmp/hanuman-motion.blend
```

Add `--render /tmp/hanuman-frames/frame-` to export a PNG sequence directly from Blender. The workstation used for these studies ran Blender 4.3.2. Open the saved project in Blender's Animation workspace to inspect or revise individual strips. To recheck all four packaged scenes, run `blender -b -t 1 --python-exit-code 1 -P games/yuga-native/art/four-hero-motion/tools/render/verify_blend.py` from the repository root.
