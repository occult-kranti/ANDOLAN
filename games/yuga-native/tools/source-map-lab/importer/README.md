# Dust II geometry for Blender

This importer turns the complete legacy CS:GO Dust II map and its mounted assets into a self-contained GLB. It keeps the Source world, brush models, decal projections, original studio meshes, instance transforms, skins and base textures. Blender can select one prop instance, examine individual faces by Source ID, and preserve the shared mesh of a repeated prop. The sibling Rust finishing tool recolors the playable ground for comparison.

## Reproduce the reference scene

Start in the ANDOLAN repository root. These commands use Python 3.12, Go, a Rust toolchain, `unzip`, and a local installation of SteamRE DepotDownloader. The acquisition script looks up only the map and its referenced assets. Its documentation identifies the Valve depot, manifest, and file checksums. [Valve acquisition script](../../../docs/research/dust2-map-lab/acquire_valve.py) · [SteamRE DepotDownloader](https://github.com/SteamRE/DepotDownloader)

```sh
lab="$PWD/games/yuga-native/tools/source-map-lab"
work="${TMPDIR:-/tmp}/yuga-local-dust2"
mkdir -p "$work/tools" "$work/scene"
python3.12 -m venv "$work/venv"
"$work/venv/bin/pip" install -r "$lab/importer/requirements.txt"
curl -fL https://github.com/REDxEYE/SourceIO/releases/download/5.4.8/SourceIO.zip -o "$work/tools/SourceIO.zip"
(cd "$work/tools" && echo '52cb92856771fc2785b7c4746e15968135973d11fe80bb78dac8001166bcdfac  SourceIO.zip' | sha256sum -c - && unzip -q -o SourceIO.zip)
python3 games/yuga-native/docs/research/dust2-map-lab/acquire_valve.py "$work" --downloader /path/to/DepotDownloader
mapdir="$work/valve-depot/csgo/maps"
(cd "$lab/nav" && go run . "$mapdir/de_dust2.nav" "$mapdir/de_dust2.bsp") > "$work/scene/official-nav.csv"
"$work/venv/bin/python" "$lab/importer/build_scene.py" "$mapdir/de_dust2.bsp" "$work/scene/official-nav.csv" "$work/scene" --sourceio-parent "$work/tools" --assets "$work/assets"
cargo run --locked --release --manifest-path "$lab/rust/Cargo.toml" -- glb "$work/scene/dust2-baseline.glb" "$work/scene/dust2-jade.glb"
"$work/venv/bin/python" -m unittest discover -s "$lab/importer" -v
```

Import either GLB through Blender’s **File → Import → glTF 2.0**. Source X points east, Y north and Z up. GLB coordinates in metres are `(x, z, -y) × 0.0254`. Blender’s glTF importer maps back to Z-up. Frame a bombsite or a spawn to see the gameplay district. A separate 1:16 sky-camera cluster and the original remote scenery extend the map bounds. [Blender cameras and comparison](../blender/README.md)

## What is in the files

| Output | Contents |
| --- | --- |
| `dust2-baseline.glb` | 43 brush-model nodes, their 8,840 visible faces, the 8,324 displacement meshes within those faces, 90 projected markings, every static prop placement and the soccer-ball entity’s model. |
| `dust2-jade.glb` | Rust changes the base-color factor on the 23 ground variants shared by the 260 selected faces. Decal art and props stay in the original material slots. |
| `floor-faces.json` | Sorted source face indices, consumed by both the native BSP pass and structural GLB audit. |
| `floor-support.json` | Official navigation area centres tested against interpolated heights on the original triangles, broken out by named place. |
| `objectives.json`, `source-entities.json` | Original-unit bounds of both bombsites, and the 375 source entity property dictionaries including worldspawn. The full BSP preserves repeated properties and game I/O exactly. |
| `entities.json` | Brush and point entity centres, target names and model references. Its indices count entities after worldspawn, matching the GLB’s external model metadata. |
| `import-report.json` | Digests, material and model resolution failures, brush and instance counts, the one authored out-of-range skin, and texture settings. |

Pass `--selection-only` to produce the two ground files without loading studio models or textures. Pass `--world-only` to inspect brushes, displacements, and projected markings without studio props. Additional `--assets` roots are searched in command-line order after the map’s own Pakfile. Increase `--texture-size` for the source artwork’s larger mip levels. The measured reference uses 512 pixels on the longest dimension.

## How the reconstruction works

- The importer reads original face planes, signed surfedges, texture axes, original texture dimensions, and Source primitive indices. For displacements it rotates the base quad to the authored start vertex, interpolates its grid, applies each recorded direction and distance, and reconstructs the alternating diagonals. Curbed streets, slopes and uneven plaster retain their deformations. [Valve BSP structs](https://github.com/ValveSoftware/source-sdk-2013/blob/3e957b70b167929f120360115d359d1ecb4c1699/src/public/bspfile.h)
- Each prop combines its MDL, VTX and VVD files after their checksums agree. SourceIO handles the studio formats and LOD fixups. Shared accessors keep the 3,158 placements compact. A real broken hanging-light prop requests skin 1 from a one-skin model. The importer uses family 0 and records the case in the report. [SourceIO 5.4.8, MIT](https://github.com/REDxEYE/SourceIO/tree/34be43e4d4b4da7a819de50075cb95ab7f28899d)
- Each projected road stripe, bombsite mark, stain or direction sign references a list of native faces. The importer decodes the oriented projection basis, clips the marking against those actual triangles and preserves unsigned and flipped texture axes. This follows rough surfaces and keeps holes and doorways clear. [Valve overlay serialization](https://github.com/ValveSoftware/source-sdk-2013/blob/3e957b70b167929f120360115d359d1ecb4c1699/src/utils/vbsp/overlay.cpp)
- BSP, entities, VMT patches and VTF image data are read with srctools. GLB embeds primary albedo with its original UVs, alpha mode, and repeat sampling. Original multi-layer Source terrain shading, lightmaps, cubemaps, ambient effects, runtime ropes, per-instance lighting and collision remain available in the native BSP and mounted game assets. The GLB provides an editable geometry and base-color comparison. [srctools 2.7.0, MIT](https://pypi.org/project/srctools/2.7.0/) · [Khronos glTF 2.0](https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html)

## Ground membership and measured coverage

A face must belong to worldspawn, have a signed original BSP plane with a vertical normal component of at least 0.55, and intersect the vicinity of a real navigation area at its interpolated height. The classifier samples authored displacement points, the face centre and inset edge points. Individual displaced triangles may slope more steeply than their parent face. Ground-like materials get 72 Hammer units of horizontal and 32 units of vertical tolerance to include street edges. Other upward surfaces require 12 units in each direction. Roofs, ceilings, architectural trim, antennas and door tops are excluded by material semantics. Selecting by face lets a ground and a wall share an original material without tinting both.

The complete render includes 302,156 structural triangles, 8,753 overlay triangles and 3,909,614 exported LOD0 prop triangles (3,908,880 after case-insensitive model deduplication). The selected 260 faces cover 7,736.74 m². Of 1,118 official navigation area centres, 991 have a nearby structural triangle within 18 Hammer units, and all 991 are on selected ground. Independent ray tests attribute another 109 centres to static props. The remaining 18 have no upward render triangle within tolerance. Of the 109 prop-supported centres, 56 land on modeled stairs and 16 on curbs. The six materials used by those 13 studio assets all cover both upward and side triangles. On the upper tunnel stairs alone, one VMT shades 1,023 upward triangles and 1,118 side triangles. Isolating tread color in a future edition requires a studio-mesh material split to preserve risers and curb walls. The GLB includes all 90 projected overlays and all 3,158 static placements. Its 262 embedded images resolve the primary textures for 319 material variants. [Independent mesh and native comparison](../qa)

Source map SHA-256 is `b91be410539fbbfc16300423f1e19c024f12addf1429c8cb2f72b53fe0fd6bcc`. The 512-pixel reference GLB is 205,312,168 bytes, with SHA-256 `03bf9abd57e1a5ed2d77b847378a63765e6951c7fefd424708bb9624ddace48c`. The exporter and tests use public library APIs. Valve map geometry and artwork are separate inputs acquired into the local build directory.
