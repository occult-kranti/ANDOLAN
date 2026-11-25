# Blender world elements

Download and extract the YUGA library. In Blender, open **Edit → Preferences → File Paths → Asset Libraries**, add the extracted folder, then select it in the **Asset Browser**. Drag a collection into a scene. Use **Link** when several maps should share future edits to a master. Use **Append** for an independent copy to remodel. The included gallery displays linked instances of the editable masters. Blender's **File → Append → Collection** also works without registering the library. [Download the library ZIP](https://raw.githubusercontent.com/occult-kranti/ANDOLAN/game/yuga-hanuman-trial/games/yuga-native/art/reuse-library/yuga-world-elements.zip) · [Preview every element](preview.jpg) · [Open the Blender file](yuga-world-elements.blend)

| Catalog | Count | Contents and source |
| --- | ---: | --- |
| Architecture | 8 | Existing YUGA modules including the Lanka shikhara, watchtower, temple crown and transit garden. The meshes retain their normalized source dimensions. The gallery uses footprint proportions from the native map where available. [Architecture donor](../../assets/world/architecture.glb) |
| Nature | 7 | Reed, mangrove, lotus, diya, lantern, shrine and rock modules from the existing YUGA nature kit. [Nature donor](../../assets/world/nature.glb) |
| Foundations | 4 | A unit block, two-triangle UV tile, low display plinth and adjustable roof band. These editable Blender stock shapes use the dimensions and geometric conventions of the Rust renderer. [Builder and pinned upstream call sites](../../tools/firered-reuse/foundations.py) |
| Symbols | 24 | All nonempty mapped outlines from the DejaVu Bold symbol subset shipped inside the linked repository. The floor-centered meshes include arrows, circled numbers and markers. The original font and its notice are included. [Glyph inventory and source](symbols/manifest.json) · [Font notice](symbols/DejaVu-LICENSE.txt) |

Blender 4.3.2 reopened a relocated copy, appended all 43 collections into a fresh scene, and evaluated all 43 again as linked instances. The 15 world donors retained their per-material geometry and UVs, and the library packs six source textures. The gallery is scaled for browsing. Set each world-module instance to its intended footprint when placing it on a lane. [Asset catalog](catalog.json) · [Geometry and portability checks](verification.json)

## What came from the Rust remake

The supplied GitHub address redirects to `lime41225/FireRed-remake-and-remaster`. Joshua Coatesworth's fork points to the same inspected revision, `6a40d31175f5ce5ba15cdd74a141b1df9e1d0853`. Both contain the Rust builders, glTF pipeline and data provenance. The revision has 1,155 tracked files and zero tracked Blender, glTF, FBX or OBJ models. Its importers expect separate game data for the authored environments, characters and animations. The Rust project pins Bevy 0.17.2, with bevy_mesh 0.17.3 in Cargo.lock. [Upstream](https://github.com/lime41225/FireRed-remake-and-remaster/tree/6a40d31175f5ce5ba15cdd74a141b1df9e1d0853) · [Joshua's fork](https://github.com/JoshuaCoatesworth/FireRed-remake-and-remaster/tree/6a40d31175f5ce5ba15cdd74a141b1df9e1d0853) · [Upstream distribution notes](https://github.com/lime41225/FireRed-remake-and-remaster/blob/6a40d31175f5ce5ba15cdd74a141b1df9e1d0853/README.md#legal)

We compiled seven pinned geometry functions and their position helper using a small Rust recording adapter. Their draw calls produced a separate **36-collection working study** containing furniture, player and NPC placeholders, a tree, two window orientations, house and lab variants, fence and sign, and field and interior tiles. The study also includes a preview plinth reconstructed from renderer parameters. Its 339 part instances share ten mesh data blocks. Each fixture records its source function and dimensions. The input maps were small synthetic examples. The texture carriers have neutral surfaces, and the actor placeholders are static. [Coverage, compiler and fixture details](../../tools/firered-reuse/RUST-FALLBACK.md) · [Rust recorder](../../tools/firered-reuse/record_geometry.py) · [Blender importer and verifier](../../tools/firered-reuse/import_study.py) · [Actual 36-piece Blender inventory and checks](rust-study-check.json)

The Rust prototype has no license declaration in its package or directory. The upstream noncommercial recompiler has a separate notice. The local working study and its mixed demonstration scene can be regenerated from the pinned checkout. The public 43-piece library uses the identified font terms, existing YUGA art and stock forms. [Rust package metadata](https://github.com/lime41225/FireRed-remake-and-remaster/blob/6a40d31175f5ce5ba15cdd74a141b1df9e1d0853/rust-prototype/Cargo.toml) · [Recompiler license](https://github.com/lime41225/FireRed-remake-and-remaster/blob/6a40d31175f5ce5ba15cdd74a141b1df9e1d0853/FireRedLeafGreenRecomp/LICENSE)

### Rebuild the Rust study from a checkout

From the ANDOLAN root, use Git, Python 3.11+, rustc and Blender with Pillow available to its Python. The recorded run used Blender 4.3.2 and rustc 1.88.0. The recorder verifies the pinned Rust inputs before compiling the geometry routines. An empty local working directory keeps builds separate.

```sh
work=$(mktemp -d)
tools=games/yuga-native/tools/firered-reuse
git clone https://github.com/lime41225/FireRed-remake-and-remaster.git "$work/upstream"
git -C "$work/upstream" checkout --detach 6a40d31175f5ce5ba15cdd74a141b1df9e1d0853
python3 "$tools/record_geometry.py" "$work/upstream" "$work/shape-manifest.json"
blender -b --factory-startup --python-exit-code 1 -P "$tools/import_study.py" -- \
  --manifest "$work/shape-manifest.json" --output-dir "$work/Rust"
```

Open `$work/Rust/rust-fallback-study.blend`. Choose a piece in the Asset Browser, append its collection and edit any part. Multiple parts can share mesh data. Use **Object → Relations → Make Single User → Object & Data** to change the mesh of only one copy. The build also renders an overview and compares the saved geometry to the captured vertex coordinates, faces, materials and visibility.

### Assemble an example from both libraries

Place the public library at `$work/YUGA/yuga-world-elements.blend` and the compiled study at `$work/Rust/rust-fallback-study.blend`. The waystation example links the fallback house, fence, sign, field tiles and table with YUGA's watchtower, wayfinding arrow, lantern and wetland plants. Its relative paths let the whole folder travel together. The sample uses 40 placements of 15 source collections. Blender resolved all 123 mesh instances after relocating the scene, with both libraries linked by relative path. Changing a library master updates its placements. [Waystation recipe](../../tools/firered-reuse/build_waystation.py) · [Relocation test](waystation-check.json)

```sh
blender -b --factory-startup --python-exit-code 1 -P "$tools/build_waystation.py" -- --folder "$work"
blender -b --factory-startup --python-exit-code 1 -P "$tools/build_waystation.py" -- --folder "$work" --verify
```

### Add assets from a populated Rust checkout

The manifest importer reads the upstream format for kit entries, map scenery and height grids, character models and battle stages. It keeps references to the same geometry shared, packs textures and records missing inputs. Point it at a populated `rust-prototype/assets` folder. A code-only checkout has no populated catalog. The intake was exercised with existing YUGA scenes and a rigged GLB, including append after relocation. [Manifest guide](../../tools/firered-reuse/MANIFEST-INTAKE.md) · [Importer](../../tools/firered-reuse/import_manifests.py) · [Fixture verification](manifest-intake-check.json)

```sh
blender -b --factory-startup --python-exit-code 1 -P "$tools/import_manifests.py" -- \
  --assets /absolute/path/to/populated/assets --output "$work/registered-elements"
```

### Rebuild the public library

```sh
blender -b --factory-startup --python-exit-code 1 -P "$tools/build_library.py" -- \
  --output-dir "$work/YUGA" --thumbnails "$work/thumbs"
python3 "$tools/contact_sheet.py" "$work/YUGA/catalog.json" "$work/thumbs" "$work/YUGA/preview.jpg"
blender -b --factory-startup --python-exit-code 1 -P "$tools/verify_library.py" -- \
  --library "$work/YUGA/yuga-world-elements.blend" --catalog "$work/YUGA/catalog.json" --report "$work/YUGA/verification.json"
```

The original art, combat assets and downloadable Hanuman game are separate versioned artifacts. This library is an authoring input for future scenes. [Hanuman handoff](../../docs/HANUMAN_HANDOFF.md)
