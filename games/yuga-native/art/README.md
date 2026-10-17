# Original coastal courtyard

`build_courtyard.py` creates the actual three-dimensional environment in
`assets/environment/lanka_courtyard.glb`. It does not download or extract any
commercial game content. The setting is an original fantasy training court:
scalloped arches, fluted columns, lotus reliefs, stepped palace silhouettes,
brass lamps, stone paving and a coastal marsh edge. These are broad visual
references to Indian architecture and mythology, not a reconstruction of a
specific historical temple or a claim about the historical geography of Lanka.

Run from the repository root with Blender 4.3 or newer:

```sh
blender --background --threads 2 --python games/yuga-native/art/build_courtyard.py
python games/yuga-native/art/validate_courtyard.py
```

The deterministic seed controls all stone grain, veins and marsh placement.
Four original material sets have embedded 512 × 512 albedo, tangent-space normal
and roughness maps. Other surfaces use compact, authored PBR constants. All
meshes have normals and UVs; explicit triangulation gives every exported
primitive tangent data. Paving shares limestone normal and roughness maps.
Geometry is grouped
by material and collision category to limit imported mesh instances. No lights,
cameras, animations, fonts or third-party images are embedded in this asset.

The generated geometry and textures are dedicated to the public domain under
[CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/). The generator follows
the repository's source-code license. This dedication applies only to this
courtyard asset, not to unrelated hero assets, tools or dependencies.

`lanka_courtyard.metadata.json` records the Blender version, seed, triangle and
object counts, file size, SHA-256, light anchor coordinates and build duration.
Build guards reject output above 25 MiB or 300,000 triangles.
The standalone validator also checks binary indices, finite coordinates,
unit-length normals/tangents, embedded images and agreement with the metadata.

The GLB uses metres and Y-up, with XZ as ground. The playable boundary is
44 × 50 m, and the central 24 × 28 m plaza has no blocking scenery. Spawn feet
are `(0, 0.05, 12)`; five target anchors are at `z = -8`. The runtime supplies the
continuous `y = 0` floor and perimeter. Nodes beginning `COL_` contain structural
geometry for static trimesh collision. `FLOOR_` paving, `DECOR_`, `WATER_` and
`SKYLINE_` are visual only. Floor inlays rise by a few centimetres and do not
change the walking plane. Runtime lights illuminate selected emissive lanterns;
the export deliberately contains no punctual lights.

This is a bounded native training environment foundation. It does not establish
commercial-game visual parity, animation quality or complete gameplay. Assess
its appearance using a frame rendered by the game; the build metadata is only
structural evidence.

## Courtyard refinement, revision 2

The first actual native frame, `build/visual-initial/frame-3.png` from the
`3f1b782` foundation, showed a dominant foreground lotus, dark paving lines and
uniform gilding. The original asset remains identifiable by SHA-256
`d1f7346aad37cecf3a8202022daea0d37cc773ba980a1a582b100540babe13da`.
This revision follows the software-agent art review of that rendered frame.

| Element | Original | Revision 2 |
| --- | --- | --- |
| Paving joints | 35 mm, dark bed 20 mm below the surface | 10 mm, pale mortar 2 mm below the surface |
| Paving chamfer | 18 mm | 4 mm |
| Spawn lotus | 2.1 m radius, raised metallic brass | 0.62 m radius, shallow matte stone |
| Central lotus | 2.1 m radius | 1.0 m radius, quieter fine rings |
| Main gate depth | 3.9 m arch | 7.5 m arch with deeper stone piers and recessed soffit |
| Ornament | Frequent brass trim and roof crests | Selective burnished brass, stone gallery reveals and fewer crests |

The front gate plane, 44 × 50 m movement boundary, spawn and target anchors are
preserved. Additional gate depth extends behind the facade; no new wall or door
crosses the central aim corridor. The material, topology and provenance checks
are reproducible through the builder and validator. Visual acceptance requires
the subsequent native game render; geometry changes alone do not prove that
the intended hierarchy is achieved.
