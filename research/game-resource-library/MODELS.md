# Khronos glTF model inventory

All **153** models in the official Khronos index at revision `e124e8d8d7330a5372bc2b4d00d39a4a9d7997ea` have a model-specific license, credits, a canonical glTF 2.0 scene descriptor and a preview path in the Git tree. The importer read all 153 descriptors, 153 metadata files, 153 terms files and the index. **28 models have animation, 8 have a skin, and 85 declare at least one extension.** There are 40 animation clips, of which 25 have names. [Official index](https://github.com/KhronosGroup/glTF-Sample-Assets/blob/e124e8d8d7330a5372bc2b4d00d39a4a9d7997ea/Models/model-index.json) · [Coverage and license breakdown](evidence/model-coverage.json)

| Model to examine | What the descriptor contains | Terms to investigate |
| --- | --- | --- |
| Fox | One mesh, one skin, 24 distinct joint nodes and three clips named Survey, Walk and Run. Useful for a locomotion-transition test. | The original model credit lists CC0. Rigging, animation and conversion credits list CC BY 4.0. [Descriptor](https://github.com/KhronosGroup/glTF-Sample-Assets/blob/e124e8d8d7330a5372bc2b4d00d39a4a9d7997ea/Models/Fox/glTF/Fox.gltf) · [Credits](https://github.com/KhronosGroup/glTF-Sample-Assets/blob/e124e8d8d7330a5372bc2b4d00d39a4a9d7997ea/Models/Fox/metadata.json) |
| Cesium Man | One mesh, one skin, 19 distinct joint nodes and one unnamed clip. A useful check for an importer that assumes every animation has a name. | The credit splits identify attribution and the separate Cesium mark. [Descriptor](https://github.com/KhronosGroup/glTF-Sample-Assets/blob/e124e8d8d7330a5372bc2b4d00d39a4a9d7997ea/Models/CesiumMan/glTF/CesiumMan.gltf) · [Credits](https://github.com/KhronosGroup/glTF-Sample-Assets/blob/e124e8d8d7330a5372bc2b4d00d39a4a9d7997ea/Models/CesiumMan/metadata.json) |
| Flight Helmet | Six mesh definitions and six nodes, with zero skins and zero clips. Supports material and lighting comparisons. | The model credits list CC0. [Descriptor](https://github.com/KhronosGroup/glTF-Sample-Assets/blob/e124e8d8d7330a5372bc2b4d00d39a4a9d7997ea/Models/FlightHelmet/glTF/FlightHelmet.gltf) · [Credits](https://github.com/KhronosGroup/glTF-Sample-Assets/blob/e124e8d8d7330a5372bc2b4d00d39a4a9d7997ea/Models/FlightHelmet/metadata.json) |

## Interpreting an asset record

The `counts` object distinguishes defined meshes and nodes that instantiate them. Joint counts use distinct node indices across the model’s skins. Joint bindings count every joint incidence across skins. Primitives, material definitions, channels, declared buffers, nodes, skins, cameras, textures and scene roots can be checked against the pinned .gltf file. Clip names preserve source order and case. A JSON `null` identifies an unnamed animation. Tags, description, thumbnails and 218 scoped credit records come from each model’s own metadata. Required extensions and declared extensions are separate lists. [Searchable JSON inventory](data/models.json.gz) · [Importer](tools/models.py)

Bulk inspection covered **30,759,786 bytes of descriptor JSON**. Binary vertex buffers, textures, alternate GLBs and screenshot contents were outside this pass. Every preview URL points to a blob present in the pinned source tree. Geometry counts and clip names can guide selection. An animation’s motion quality, rig retargeting compatibility and performance in the game require a later import and playback test. [Input Git blob IDs and declared sizes](evidence/model-inputs.json.gz)

Asset records preserve component-specific credits, rights holders, attribution terms and custom notices. Some have noncommercial constraints or separate trademark conditions. The Damaged Helmet lists both CC BY 4.0 and CC BY-NC 4.0. Selecting one license from that pair would lose the component distinction. The `license_url` opens the pinned model-specific notice, and `credits[].terms_url` opens each credited component’s terms. Project metadata and summaries are credited to KhronosGroup/glTF-Sample-Assets contributors and the authors in the individual records. [Damaged Helmet credits](https://github.com/KhronosGroup/glTF-Sample-Assets/blob/e124e8d8d7330a5372bc2b4d00d39a4a9d7997ea/Models/DamagedHelmet/metadata.json) · [Model metadocumentation terms](https://github.com/KhronosGroup/glTF-Sample-Assets/blob/e124e8d8d7330a5372bc2b4d00d39a4a9d7997ea/Models/DamagedHelmet/LICENSE.md)

## Reproduce the inventory

```sh
python research/game-resource-library/tools/models.py --verify
python research/game-resource-library/tools/models.py --offline --verify
```

The first command fetches missing JSON and legal text from the exact commit. Its default cache is `~/.cache/yuga-library/khronos/<revision>`. The second checks the same inputs without network access. Pass `--cache /path/to/cache` to use another directory. To independently reconstruct the Git-tree receipt, run `python research/game-resource-library/tools/models.py --refresh-inputs --verify`. A failed download or mismatched Git blob reports an error. Index-only rows preserve unknown counts if a future pinned index lists a model without a canonical .gltf file. The stored gzip JSON digest is `8ada29066316c31760b9f2bdcbdcff27897781465a6e081a6c4cb3637a0688e9`.

```sql
SELECT a.name, a.license, json_extract(a.metadata, '$.counts.joints') AS joints,
       json_extract(a.metadata, '$.clips') AS clips, a.source_url
FROM assets AS a
WHERE a.kind = '3D model' AND json_extract(a.metadata, '$.counts.skins') > 0
ORDER BY joints DESC, a.name;
```
