# Sangam district authoring source

Original full-district geometry for native YUGA Confluence. See [design, collision and evidence handoff](../../docs/research/hero-six-rounds/world/README.md) and [manifest](manifest.json).

Rebuild in the serialized authoring lane from repository root:

```sh
blender4.3 --background --threads 8 --python-exit-code 1 --python tools/studio/build_sangam_district.py
```

The command writes the runtime GLB/JSON and editable `.blend`, packs the existing credited YUGA material maps and records hashes/counts. Add `-- --render` only in an authorized serialized render lane; normal build does not render a still. No foreign add-ons or game data are used.

The final308,422 triangles include eight authored building modules, real overhead canopies/rooftop solids, two avenue galleries, four2.7m civic cover monuments and distant perimeter architecture. Ground solids/closed shutters retain original collision envelopes. True underpasses and lateral routes are usable; interiors are not opened. The native adapter owns overhead triangles and four shared planar cover footprints. See its lifecycle checks before changing transforms.

New geometry/code: original ANDOLAN/YUGA project work. Texture inputs: existing original YUGA CC0 courtyard maps with exact per-file source hashes in the manifest, governed by `NOTICE/ASSET-NOTICE.md` and `art/README.md`. Engine/tool licenses do not grant game-asset rights. No Deadlock/Overwatch assets, recordings, copied map layouts or external photographs are included.

`rejected-r1/` and `rejected-r2/` preserve over-budget authoring runs and their original sources; the successful source keeps near detail and reduces distant tessellation/internal faces. [Source freeze](source-freeze.json) pins final exported bytes. Native visual and physicalGPU acceptance must be recorded separately.

R6 corrects coplanar relief and buried distant facade placement found in actual native images. `accepted-r3/` preserves the prior successful model/source. The new native masonry shader is original project code; it changes material sampling, not texture pixels. Its exact hash is carried transitively by the asset JSON. Three stone materials share that shader and retain existing texture bindings; a private brass override reduces metallic glare. Blender retains original albedo, so native successor images are required to assess the finish.

Final R6d also corrects cover-top contact, mirrored panel winding and trim/banner contacts found by the full audit. `coplanar-audit.json` records zero exposed different-material rectangular overlaps and 28 hidden contacts with locations/reasons. Failed audit sources/logs remain in `audit-r6b-failed/` and `audit-r6c-failed/`. The shader adds filtered metre-scale ashlar joints, shallow bevel and restrained grain without changing texture pixels.
