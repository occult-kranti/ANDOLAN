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
