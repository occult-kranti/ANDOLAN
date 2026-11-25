# Record the FireRed procedural fallback for local Blender study

The upstream Rust renderer can construct scenery out of simple geometry before it loads art supplied by the player. This recorder compiles seven unchanged function bodies from the pinned checkout and passes synthetic map and prop inputs to them. The local geometry sink records the resulting positions, sizes, materials, visibility and roof extrusions. It also reads the dimensions, offset and color of the model preview's cylinder. The recording contains 36 specimens and 339 individual part instances. [Pinned Rust presentation](https://github.com/JoshuaCoatesworth/FireRed-remake-and-remaster/blob/6a40d31175f5ce5ba15cdd74a141b1df9e1d0853/rust-prototype/src/presentation.rs) · [Model preview](https://github.com/JoshuaCoatesworth/FireRed-remake-and-remaster/blob/6a40d31175f5ce5ba15cdd74a141b1df9e1d0853/rust-prototype/src/models.rs) · [Checks and file identities](recording-verification.json)

## Reproduce

Install Python 3 and a Rust compiler. The recorded Linux run used Rust 1.88.0 with its standard library and ordinary system C linker. It compiles a small standalone recorder in a temporary folder. Cargo and the Bevy engine build are unnecessary for this operation.

```sh
git clone https://github.com/JoshuaCoatesworth/FireRed-remake-and-remaster.git /tmp/firered-source
git -C /tmp/firered-source checkout --detach 6a40d31175f5ce5ba15cdd74a141b1df9e1d0853
python3 games/yuga-native/tools/firered-reuse/record_geometry.py \
  /tmp/firered-source /tmp/firered-study/shape-manifest.json
```

Use a fresh output path. The optional `--rustc /path/to/rustc` selects a local compiler. The recorder checks the SHA-256 of each input Rust file and the dependency lock before compiling. The compiler version and adapter identities are part of the output manifest. A compiler-version change can therefore change the manifest digest even when the emitted geometry agrees.

| Fixture family | What the recorder exercises |
| --- | --- |
| Architecture | Both window orientations, house and lab solids, the conditional doormat and both buildings' projected panel variants. |
| Furniture and street | Table, sofa, bed, houseplant, fence and sign. Width and depth are explicit test inputs. |
| Vegetation and field | Tree, two lawn parity cases, path, water with and without the stripe, both rock colors, a ledge, tall grass, flowers and the tree metatile. Four kit-material tiles and a generic ground projection retain their surface geometry. |
| Interior | Plain floor, full back wall and the low cutaway on the second row. These tiny fixtures include their generated floor and support pieces. |
| Actors and display | Unrigged player and NPC, including the NPC's two hidden emotion-mark pieces, plus the model preview platform. |

The Blender artist can inspect or replace each captured mesh. Coordinates are in tile units and follow Bevy's Y-up convention. The 23 projected quads store the original vertex UV values. The 285 cubes, 30 triangular prisms and preview cylinder use editable polygon surfaces. The locked Bevy cylinder defaults to 32 circumferential subdivisions. [Cylinder mesh builder](https://github.com/bevyengine/bevy/blob/v0.17.3/crates/bevy_mesh/src/primitives/dim3/cylinder.rs)

## Scope and reuse

The house and lab use a synthetic 4 × 3 tile footprint. The recording uses the initializer's palette before ROM-based overrides. Neutral carrier materials identify the missing textures. The source's battle stage, animated trainer/creature models and large scenic map instances require game-supplied GLBs. World layouts, live animation, character skinning, camera systems and gameplay simulation are outside this local geometry study. No original map or commercial-game textures were supplied.

The root project README identifies licences for selected subprojects. The public tree declares no general license for the Rust prototype. Keep the source-derived study as a local design reference pending explicit reuse terms. The separate YUGA library contains assets with their own documented origin. [Upstream terms](https://github.com/JoshuaCoatesworth/FireRed-remake-and-remaster/blob/6a40d31175f5ce5ba15cdd74a141b1df9e1d0853/README.md#legal)
