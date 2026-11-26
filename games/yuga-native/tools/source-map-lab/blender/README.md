# Blender ground-material study

Open `dust2-ground-study.blend` and select **01 • Reference** or **02 • Ground recolour** in the scene dropdown. The Layout viewport opens in material preview. In camera view, move the timeline to frame **1** for the north-up overview, **2** for Site A and **3** for Site B. The two scenes share their mesh datablocks, camera objects, world and sun. A material override on the marked object slots supplies the edited ground colour.

The script reads both actual GLBs and verifies that their embedded binary payload is identical. It also compares scene structure and material fields. The before and after can differ only in the declared ground materials’ base-colour factors. It imports the two exact glTF material graphs through Blender’s built-in importer, including their UV mapping and packed images. The working swatches used to carry those alternatives across the import are removed before saving.

## Rebuild the scene and comparison

Run from this directory with Blender 4.3.2 or a compatible Blender 4.x version. The WebP comparison sheet also needs Python and Pillow. `MAP_DIR` is the importer output, `DEPOT` contains the matching map overview and `RENDER_DIR` is the destination. Place the matched navigation CSV in `MAP_DIR` for this example.

```sh
blender -b --factory-startup -t 2 --python-exit-code 1 --python scene.py -- \
  --baseline "$MAP_DIR/dust2-baseline.glb" --variant "$MAP_DIR/dust2-jade.glb" \
  --overview "$DEPOT/csgo/resource/overviews/de_dust2.txt" \
  --objectives "$MAP_DIR/objectives.json" --nav "$MAP_DIR/official-nav.csv" \
  --entities "$MAP_DIR/source-entities.json" --output "$RENDER_DIR" --resolution 1024 --samples 32
blender -b "$RENDER_DIR/dust2-ground-study.blend" --python-exit-code 1 \
  --python check_scene.py -- --output "$RENDER_DIR/reopened.json"
python3 compare.py "$RENDER_DIR"
```

## What each view measures

The overview is calibrated to the radar origin and scale in the level’s overview file. That extent frames the playable district. Off-map geometry and any detached 3D skybox retain their original transform in the editable scene. The eye-height views use the centres and dimensions of the two actual objective trigger brushes. Candidates stand on ray-cast geometry at 1.60 m eye height. When a NAV file is supplied, the camera floor must also agree with a registered navigation area within 0.38 m. The script tests overhead and side clearance and a visible line to the site from the candidate.

The input scale is 0.0254 metres per Source unit. glTF uses Y up. Blender imports the mesh back into Z-up coordinates, with local X/Y/Z corresponding to Source X/Y/Z times that scale. To use a registered camera in a glTF viewer, convert both its eye and target from Blender metres to `[x, z, -y]`. The north-up orthographic camera uses glTF `[0, 0, -1]` for its up vector. The two perspective cameras use `[0, 1, 0]`, a 24 mm lens on a 36 mm sensor and a 16:9 frame. The large overview is square. For a manual rerender inside the saved file, use 1024 × 1024 for the overview and 1024 × 576 for either site. The batch command applies those formats automatically.

Paired views use the same CPU sampling seed and direct lighting. With `--entities`, the sun uses the map’s `light_environment` yaw and pitch, and the sun and ambient sky use its sRGB colours and relative intensities. A half-degree minimum solar disk gives shadow edges a finite width. The ordinary Source baked lightmaps, 3D skybox compositing and engine visibility remain native runtime inputs. The reconstructed Blender materials show the imported texture and geometry under this separately reproducible daylight.

The nine `overview-*`, `site-a-*` and `site-b-*` PNGs give the reference, jade render and ground material-ID mask for each camera. The mask follows the visible, occlusion-tested material in the reference scene. `cameras-and-render.json` records the three transforms, their floor support, input hashes, scene hash and renderer. `reopened.json` is produced in a fresh Blender process and checks common mesh identity, placement, cameras, packed images and edited slots. `dust2-ground-comparison.webp` places matched frames side by side.
