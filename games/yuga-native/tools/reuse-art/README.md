# Optional static-world preflight

This offline authoring tool uses glTF-Transform 4.3.0 and meshoptimizer 0.24.0 to
weld bitwise-identical vertices and reorder triangle/vertex data. It writes a
candidate and report into a **fresh external directory**. It never promotes an
asset into the game. This is an optional Round 9 optimization aid; it is not a
dependency of face, groom, soldier or environment art work.

From the repository root, with Node 20.9 or later:

```sh
npm ci --prefix games/yuga-native/tools/reuse-art --ignore-scripts
npm test --prefix games/yuga-native/tools/reuse-art
node games/yuga-native/tools/reuse-art/static-world-preflight.mjs \
  games/yuga-native/assets/environment/lanka_courtyard.glb \
  /workspace/scratch/my-fresh-static-preflight
```

The output parent must already exist; choose a destination that does not exist.
The direct packages and all resolved transitive packages are locked locally;
the root package/lock are untouched. The tool was executed with Node 24.19.0 on
Linux. `node_modules` is not committed or shipped with the game. The installed
Linux dependency tree occupies about 38 MiB, including unused image-processing
packages pulled by the upstream functions package. This is not a runtime cost.
The directory's `.gdignore` keeps these optional Node dependencies out of
Godot's resource import scan; native export presets also exclude authoring tools.

Accepted input is a self-contained GLB v2 up to 64 MiB, with static triangle
meshes and opaque/masked materials. The only registered extension is
`KHR_materials_emissive_strength`. Skins, animations, morph targets, skin
attributes, cameras, transparent BLEND materials, external payloads and other
extensions are refused. Asset metadata beyond generator/version, accessor or
buffer/view names/extras/extensions, and image extras/extensions are also
refused because their preservation has not been established. This restricted
adapter is not a general glTF schema validator.

The oracle compares each primitive's sorted multiset of oriented triangles,
where every corner hashes the exact bytes of **every present vertex attribute**.
Cyclic triangle rotations are equivalent; reversed winding is not. Attribute
semantic/type/normalization and primitive material assignment are retained.
After writing and reloading the candidate it also compares normalized scene,
node, material, sampler, mesh and primitive metadata, plus embedded image
payload hashes and the supported texture metadata. The comparison uses
NodeIO's normalized representation; it does not promise preservation of every
possible original glTF JSON field or binary layout. Input bytes are rechecked
before output. Existing destinations, destinations containing the source,
symlinked output parents, and destinations in this checkout are refused.

On the current courtyard, the measured result is 266,311 → 265,989 vertices,
135,654 unchanged triangles, 22 unchanged primitives and 12 byte-identical
embedded images. GLB size is 17,036,264 → 17,017,068 bytes (19,196 bytes,
0.113%). The separately installed Khronos validator 2.0.0-dev.3.10 reported
0 errors, 0 warnings and 16 informational findings on both input and candidate.
That small saving does **not** warrant replacing the current runtime asset.
There is no simplification, quantization, compression extension, normal/tangent
regeneration or image processing. GPU timing, Godot import behavior, rendered
appearance and arbitrary metadata preservation remain untested.

[The research record](../../docs/research/community-reuse/art.md) and
[source ledger](../../docs/research/community-reuse/art-sources.json) identify
the current input, independent review, upstream source and actual measurements.
[NOTICE.md](NOTICE.md) separates software licensing from input asset rights.
