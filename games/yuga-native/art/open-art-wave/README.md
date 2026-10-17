# Open-art cloth candidate

This staged native resource adapts three **Microsoft SheenCloth (2020), CC0-1.0**
texture maps from the pinned Khronos sample repository. It is an actual PBR
texture/material candidate, not a concept image or a recovered commercial game
asset. It has not been promoted into the playable runtime.

Use `res://art/open-art-wave/materials/indigo-woven-cloth.tres` as the input to
the role07 material fixture. Only the existing semantic surface
**`Cobalt handwoven silk`** is eligible. Preserve `Cobalt lotus brocade`,
`Worked warm gold`, hair, skin and all other surfaces. Preserve the existing
secondary-motion ShaderMaterial and vertex masks: copy its supported PBR inputs
through the fixture rather than replacing the offset writer or imported mesh.

The original sample is a technical fabric, not a historical Indian silk scan.
Our original calibration retints its luminance in linear light to restrained
indigo, compresses the large diamond contrast, extracts linear roughness from
ORM green, and reduces the tangent-normal XY amplitude to 28%. Four integer
repetitions per axis are baked into each 1024² map, preserving source texels and
the motion shader's identity UV contract. This does not invent higher resolution
detail. Source acquisition is 384,181 image bytes; derived PNGs total 613,976 bytes.

The StandardMaterial3D uses opaque Burley/GGX, no metal, default 0.5 specular,
roughness map red, +Y tangent normals, repeated linear mipmaps, and disabled
culling matching the existing thin cloth shader. It adds no lights, emission,
rim, AO, extra material pass or fake sheen. Godot's ordinary PBR implementation
does not establish the source sample's `KHR_materials_sheen` rendering behavior.

Rebuild from the repository root:

```sh
python3 games/yuga-native/tools/build-open-art-materials.py
python3 games/yuga-native/tools/build-open-art-materials.py --check
python3 games/yuga-native/docs/evidence/open-art-wave/materials/verify_materials.py --report /tmp/yuga-open-art-check.json
```

Python dependencies observed: NumPy 2.3.5 and Pillow 12.3.0. No network access,
engine import, mesh, rig, gameplay or scene changes are needed for this build.
`source-manifest.json` pins upstream URLs, exact files, sizes and SHA-256;
`build-manifest.json` pins the authored recipe, derived maps, scalar ranges and
candidate resource. Source identity mismatches refuse the build.

Review gates remain: actual Godot import/mipmap and compression settings;
same-camera day/night full-body and close-cloth comparison; no unwanted fabric
scale, seam, shimmer or gold/blue loss; secondary offset preservation and exact
unbind. Root owns serialized imports and native rendering. The known 182.3 px
material-frame glint remains a separate controlled geometry/material comparison.
This texture does not fix mesh tangents. Three 1024² RGBA8 maps with full mips
would conservatively consume 16 MiB before compression; actual imported memory
and hardware frame cost are unmeasured. Source licensing and valid texels do not
close the production art or commercial-game-quality gate.

See [the notice](../../NOTICE/OPEN-ART-WAVE.md) for separate asset and metadata
terms. No upstream sample geometry, sheen map or software was incorporated.
