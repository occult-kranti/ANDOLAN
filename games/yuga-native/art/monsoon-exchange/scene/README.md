# Monsoon Exchange in Blender

Open the packed Blender file to edit the district. Camera 1 frames the entire exchange from the southwest. Timeline markers 2, 3 and 4 take you to Sun Court, the Indigo Cistern and Weavers’ Gate. Marker 5 looks straight down with north at the top. Each street photograph places the camera 1.60 m above its local approach floor. [Editable Blender scene](monsoon-exchange.blend) · [Self-contained glTF 2.0 model](monsoon-exchange.glb) · [Camera coordinates and source receipts](scene-register.json)

| Place | What to inspect in the model |
| --- | --- |
| Sun Court | A raised, sun-inlaid floor opens onto a copper-roofed sabha. Its ribbed cupola, instrument wheel, hanging lamps and money-changers’ upper galleries mark the eastern court. The arcade on the approach has its own roof rhythm. |
| Indigo Cistern | Look over the western parapet into five indigo terraces, a recessed turquoise pool, upper water gauges and a shaded column gallery. The separate Sluice Walk carries 0.12 m of water across a registered floor. Its two dry margins stay open. |
| Weavers’ Gate | Carved sandstone oriels, open diamond lattice, a cusp arch and opposing dyed textiles identify the central choice at eye height. The arch springs above the passage. |
| Dyers’ Passage | A split loom shade and three sprung ribs admit strips of daylight. The eastern springer above the Sluice doorway has an open span under it, keeping the side connection clear. |
| Caravan Yard and Archive Court | Each has five brass-and-lime pad markings. Deep southern porticoes hold an ember pot and trade jars. A pale stone registry and its two north cupolas shelter the water ewer. |

The district uses metre-scale east, north and up axes in Blender. The exported GLB uses east on X, up on Y and north on negative Z. Architecture beyond the surveyed perimeter gives the streets depth. The ornamental western reservoir, upper money-changers’ galleries and roof gardens are outside the playable floor. Two 3 m ritual rings and twenty authored cover volumes anchor the five-player start on each side. [Authoritative floor and cover data](../plan/survey.json) · [Door cuts and grades](../plan/geometry.json) · [Measured elevations and paths](../plan/README.md)

## Change the scene

- Edit room footprints, doors, cover and levels in the survey first. Rebuild the floor geometry before the Blender scene. Floor objects carry their `patch_id`, walls their `wall_id`, and furnishings their `cover_id`. Architecture is grouped by building in local frames. Bricks, trim, shutters and textile faces share a building object and remain individually editable in Edit Mode. [Geometry compiler](../plan/geometry.py) · [Native scene builder](build.py) · [Landmark architecture](district.py)
- Reuse the original kit by placement ID. Ten original Mandala GLBs furnish twenty pieces of cover and four trade or ritual displays. Cover placement combines a fitted source object with a masonry plinth and a hidden full-size design volume. The register records source hashes, transforms, dimensions and the download paths for every reused object. [Placement register](scene-register.json) · [Original kit](../../mandala-map-studio/models/index.json) · [Reuse decisions](../design/transfer-register.md)
- The separate gameplay collection contains edit-only cover proxies, 10 spawn origins, two ritual volumes and a 1.80 m scale figure. The GLB retains floor, wall and cover IDs plus named cameras. Each cover furnishing carries `collider_center_xyz_m` and `collider_size_m` in authored Blender axes. The district viewer reads this scene and the survey. [Browser atlas](../viewer/README.md) · [Mesh checker](../qa/check_meshes.py)
- Original painted stone, plaster, water, copper, clay and woven surfaces repeat in physical metres. The generated indigo block print appears on Weavers’ Gate, Dyers’ Passage and the Caravan Yard portico at a 1.75 m repeat. The appearance register records the real UV bounds and face count of each use. Both deliverables contain the textures. [Surface recipes](surfaces.py) · [Architecture motifs](architecture.py) · [Generated fabric and art direction](../concepts/direction.md)

## Rebuild and photograph

Run these commands from this directory using Blender 4.3 or compatible, with Pillow and NumPy importable in Blender’s Python. The project’s existing glTF import/export add-on reads the original kit and writes a single GLB. The packer builds the original material tiles temporarily and embeds their pixels in both output files. The optional `--output` argument to `build.py` sends the packed scene, GLB and receipt to another directory.

```sh
blender -b -t 3 --python-exit-code 1 --python build.py
blender -b -t 3 --python-exit-code 1 --python render.py -- --samples 24
```

Rendering uses CPU Cycles and the scene’s AgX transform. Blender builds with Intel Open Image Denoise use the built-in denoiser. Where available as a separate program, `--denoiser /path/to/oidnDenoise` applies the project’s linear HDR denoising path before the display transform. `--preview` produces half-size camera checks. `--shots indigo-cistern` renders one selected view. `--blend` and `--output` let you photograph a different build without replacing the release. [Render source](render.py) · [Reused HDR color pipeline](../../mandala-map-studio/src/light_study.py) · [Released photographs](../renders/render-register.json)

The Khronos validator reports 333,148 triangles, 547,112 exported vertices, 1,453 mesh primitives and 91 materials. Its informational notices concern unused glTF properties and non-power-of-two texture dimensions. The release has zero format errors and zero warnings. Run `node check-format.cjs` with the `gltf-validator` package installed, or point `GLTF_VALIDATOR` at an existing copy. [Validation receipt](format-verification.json) · [Validation program](check-format.cjs) · [Khronos validator](https://github.com/KhronosGroup/glTF-Validator)

A second build in an empty output directory reproduced the 22,534,556-byte GLB exactly. Its survey, geometry, camera, placement and material records also matched. Blender can vary the compressed bytes of a native save. Each set of photographs therefore records the hash of the particular packed scene it rendered. [Release manifest](scene-register.json) · [Render receipt](../renders/render-register.json)

The exported model is an art and level-authoring deliverable. Browser orbit inspection exercises one viewing session. Production frame budgets need measurements with ten heroes, effects and gameplay active. The floor, sightline and standing-cover checks have their own independent geometry receipts. [Viewer tests](../viewer/check_viewer.py) · [Native and glTF results](../qa/geometry-verification.json) · [Re-run the geometry checks](../qa/check_meshes.py)
