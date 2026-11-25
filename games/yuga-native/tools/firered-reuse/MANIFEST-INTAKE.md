# Bring generated Rust assets into Blender

The FireRed Rust renderer opens four manifests. This Blender tool reads those same file layouts to turn populated local directories into editable collections, texture materials and terrain data. The linked fork and upstream have the same pinned tree. The clean checkout yields an inventory with four absent manifests. Supply a populated directory containing the assets you intend to use. [Pinned Rust loading code](https://github.com/JoshuaCoatesworth/FireRed-remake-and-remaster/blob/6a40d31175f5ce5ba15cdd74a141b1df9e1d0853/rust-prototype/src/models.rs) · [Battle stage consumer](https://github.com/JoshuaCoatesworth/FireRed-remake-and-remaster/blob/6a40d31175f5ce5ba15cdd74a141b1df9e1d0853/rust-prototype/src/battle_stage.rs) · [Validation with YUGA artwork](../../art/reuse-library/manifest-intake-check.json)

Run these commands from the ANDOLAN repository root. Choose a fresh output directory outside the inputs.

```sh
tool=games/yuga-native/tools/firered-reuse/import_manifests.py
blender -b --factory-startup --python-exit-code 1 -P "$tool" -- \
  --assets /path/to/assets --output /path/to/new-library
```

Use `--checkout /path/to/FireRed-remake-and-remaster` in place of `--assets` to inspect the checkout's `rust-prototype/assets` directory. The tool writes `intake.json` with its source paths, identities, aliases and missing or invalid entries. An `elements.blend` is created when the inventory has usable assets.

| File relative to assets root | What it supplies |
| --- | --- |
| `letsgo/kit/kit.json` | Each named entry contains a `path` for a GLB or a tile image. |
| `letsgo/scenery.json` | Each map's `scenes` array contains scene paths. Optional `overlay` and `heights` fields identify its layout and height-grid data. |
| `models/slice-models.json` | Each item has a `key` and GLB `file`. Properties such as `clip_speed` follow the model into Blender. |
| `letsgo/battle/battle.json` | Named stage entries contain GLB paths and optional map assignments. |

In Blender, use **File → Append → elements.blend → Collection** or register the output directory as an Asset Library. Drop the required collection from the Asset Browser. The material assets expose standalone kit textures. Height grids open in the Text Editor. Each role has its own stable ID. Aliases share the same source geometry when the GLB bytes and the external resource bytes match. A change to a referenced texture creates a separate editable resource. Armatures, parent-child relationships and imported animation tracks travel with the collection.

The bundled terrain generator fills missing ground from neighboring samples, then uses zero when a row has none. The Rust reader also accepts null samples as zero. The intake retains explicit nulls in the original grid text and reports their count. Grid dimensions, finite numeric samples and tree coordinate pairs are checked before bundling. [Terrain generator](https://github.com/JoshuaCoatesworth/FireRed-remake-and-remaster/blob/6a40d31175f5ce5ba15cdd74a141b1df9e1d0853/rust-prototype/tools/letsgo/terrain.py#L17-L67)

To repeat the fixture and independent reopen on Linux, run the following command. The optional checkout argument also checks the actual code-only source at the pinned revision.

```sh
python3 games/yuga-native/tools/firered-reuse/verify_manifest_intake.py \
  --upstream-checkout /path/to/pinned/FireRed-remake-and-remaster \
  --report /tmp/yuga-manifest-intake-check.json
```

The fixture uses YUGA’s Rama rig, nature kit and textures in the upstream manifest layouts. After removing its source directory, it appends the hero into an empty Blender file and checks the skinned mesh, nine actions, two packed images and 164 bones. The same run checks shared geometry, external texture variants, missing entries and malformed terrain. [Importer](import_manifests.py) · [Fixture](verify_manifest_intake.py)
