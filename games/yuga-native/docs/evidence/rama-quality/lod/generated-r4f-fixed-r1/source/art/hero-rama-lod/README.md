# Rama LOD candidate pipeline

This pipeline prepares compact, constrained **automatic candidates** for review. It does not replace the current hero, turn automatic reduction into authored production art, or establish a hardware budget. The final input queue is **art → facial geometry, if any → LOD**. Source geometry must be frozen before generation and actual native comparison.

## Measured starting point

The accepted R7 source SHA-256 is `667f3a215a7b868e3bdbcde880a73d42b68b29af1303db4e1d99b93f73cf2b50`.

| Quantity | R7 measured value | Meaning |
| --- | ---: | --- |
| Triangles |450,084|5,401,008 for12 visible copies before view/shadow culling |
| Vertex records |257,139|17,485,452 bytes of explicit vertex channels |
| Index records |3,351,336 bytes|Source index buffers; import representation may change |
| Materials / primitive submissions |13 /17|At least17 submissions per view/pass, without batching; shadows add passes |
| Skin joints |164|One existing live skeleton must drive every rendered level |
| Unique texture payloads, RGBA8 + full mips |57,322,132 bytes (~54.67MiB)|Explicit uncompressed estimate from dimensions, deduplicated by payload hash |

PNG file size is not VRAM cost. The estimate does not claim an actual engine allocation, compression, GPU residency or timing. Shared identical hero textures may be shared between instances; a future roster cannot be assumed to share them. Changing triangle count does not reduce material submission count or source texture cost.

The subsequent R4f face/art input, after the source owner's three zero-tangent UV-frame correction, is pinned at `de61dc4c470920eab6f3265bc5467da7f9fb33d6fae2129a9353e7ca6d24d3f5`:408,316 triangles,234,846 vertices,20,112,696 vertex-channel bytes,3,100,728 index bytes,18 primitive submissions and61,516,436 bytes of estimated unique RGBA8+mips. Its small native facial partition remains exact across candidate files and is omitted from runtime variants so the existing face stays unique.

**Material-frame finding remains open:** the source contains7,797 unit-but-nonorthogonal tangent/normal records above absolute dot0.01, including2,734 above0.5. This pipeline preserves those supplied records; unit/nonzero tangent and handedness checks do not establish an orthogonal, production-accepted normal-map basis. [The source-pinned Q02 finding](../../docs/evidence/rama-quality/lod/source-tangent-finding/nonorthogonal-material-frame.json) records per-material counts and the next bounded UV/native-basis rebake and actual A/B review. Only the separately authorized three zero tangents were repaired by the face source owner.

## Reproduce

Use a fresh output path for each run. Coordinate compilation, generation, imports and rendering with the global heavy-work owner. Tool download and metadata inspection can run independently.

```sh
python3 games/yuga-native/art/hero-rama-lod/measure_source.py \
  --source games/yuga-native/assets/heroes/rama-hero.glb \
  --report /tmp/rama-lod-NEW-source.json

python3 games/yuga-native/art/hero-rama-lod/bootstrap_meshoptimizer.py \
  --output /workspace/tooling/meshoptimizer-v0.24-yuga-lod --fetch-only

# Hold the exclusive build/render slot before these commands.
python3 games/yuga-native/art/hero-rama-lod/bootstrap_meshoptimizer.py \
  --output /workspace/tooling/meshoptimizer-v0.24-yuga-lod
python3 games/yuga-native/art/hero-rama-lod/build_lods.py \
  --source /absolute/frozen-final-rama.glb \
  --source-provenance /absolute/final-provenance.json \
  --library /workspace/tooling/meshoptimizer-v0.24-yuga-lod/libmeshoptimizer.so \
  --output /workspace/scratch/rama-lod-NEW
```

The tool is pinned to meshoptimizer v0.24 commit `7b2d4f4c817aea55d74dcd65d9763ac2ca608026`, MIT. Every downloaded source/license byte is SHA-256 checked. The local shared-library/compiler command and hash are recorded; exact library bytes may depend on compiler. No meshoptimizer runtime dependency is added to the game.

The two profiles request40% and16% of body triangles, with a smaller reduction for the separate bow. Error and locked regions may prevent reaching those numbers; **the measured output is authoritative**. Face, eyes/lips, exposed hand/sole contact regions and nonzero morph-delta vertices are locked. Normals, UVs, COLOR_0 masks and skin records participate in the simplification metric. The metric is not a measured physical Hausdorff bound.

Selected vertex data is copied exactly, including all UV/tangent/skin sets, COLOR_0 and every morph delta. Unreferenced vertices and accessors are removed so vertex buffers actually shrink. The independent validator checks original selected-record identity, nodes/rest/contact names, joint order and inverse bind matrices, actions, material/image payloads, normal/tangent frames, normalized weights and bounded indices. Blender sparse morph accessors are explicitly expanded with bounded, strictly ordered indices and retained as exact dense evaluated arrays. Compressed source data fails explicitly instead of silently dropping channels.

## Runtime integration hook

`scripts/rama_visual_lod.gd` is an isolated selector, currently unused by the player. `choose_camera(camera, center_world, hero_height_m, delta)` chooses levels0/1/2 using actual camera projection and viewport pixel height. `choose_pixels()` provides the same bounded selection for testing. Level changes have15% hysteresis, a150ms minimum hold, and at most one change per update. Invalid/freed cameras, nonfinite input and reset choose near and clear history. `reset()` must run on any hero/death/reset ownership change.

The selector never loads scenes, creates skeletons or changes animation state. `scripts/rama_lod_binding.gd` provides the optional bounded binding helper. Root owns player/runtime promotion.

```gdscript
# After RamaMotion has bound the live rig, before Surface/Secondary/Face:
var lod = preload("res://scripts/rama_lod_binding.gd").new()
visual.add_child(lod)
var has_reviewed_lods = lod.configure(visual, rama_motion.rig, [
    "res://assets/heroes/rama-hero-mid.glb",
    "res://assets/heroes/rama-hero-far.glb",
])
# These paths are a proposed integration contract, not files promoted by tooling.
# A false result is explicitly near-only/rejected; inspect lod.report().
# Then configure Surface/Secondary/Face on visual so all levels receive them.
lod.update(active_camera, delta)
lod.reset("death or practice reset")
```

The helper transiently loads at most two imported scenes with cache-ignore, checks one matching164-bone rest hierarchy plus ordered inverse binds/material/mask/transform contracts, and retains only four optional body/bow MeshInstances. Each level uses **the one existing Skeleton3D and sole motion writer** with two shared named Skin resources. Candidate `RamaFace`, skeletons and animators never enter the live tree; the small native facial mesh stays unique at every distance. Whole imported LOD scenes must not be kept alive as extra rigs.

The mesh-to-skeleton relation is preserved through real nested transforms; named bind order remains unchanged because vertex JOINTS index the bind array. Compact ArrayMesh resources receive the near hero's material references, sharing original textures and leaving imported source resources unchanged. Running Surface/Secondary afterward calibrates every level; authored alpha masks and material partitions are validated before binding. Loader/import transient memory and physical VRAM residency still require profiling. Disable additional autogenerated LOD reduction for the reviewed candidate imports before claiming exact reviewed geometry in runtime.

`configure(visual, skeleton, paths)` returns true only when at least one candidate is actually bound. An empty/missing/invalid candidate transaction leaves the existing near hero visible, reports the reason and returns false. `update(camera, delta)` performs bounded visibility changes; omitted delta uses actual process delta. `reset(reason)` returns near without altering any pose/face state; `dispose()` restores original visibility and removes only owned meshes/skins. No per-frame resource loads or allocations are performed by update. Invalid/freed live ownership disposes safely.

## Required three review rounds

1. **Source/contract:** source hash, hierarchy/rest/inverse-bind/action/material and image identities; measured triangle, actual compact vertex/index and texture estimates. The current tooling and synthetic failure cases cover this part.
2. **Candidate/counterexamples:** regenerate from final art/facial input, independently validate each level; reject contact/morph/mask damage, undefined materials, invalid weights and nonfinite data. Compare source and candidate per-material counts, not only total triangles.
3. **Native visual/runtime review:** render source and each candidate with identical camera/FOV/lighting/frame/pose at near, mid and far sizes; inspect face, crown/hair, fingers/bow/string, soles, cloth edges and attack/locomotion/defeat poses. Review continuous camera transitions and hysteresis in motion. Test reset/death/pause and confirm only one live rig. A visible silhouette or deformation defect rejects that level even if structural tests pass.

Actual physical-GPU frame traces,12-player cost, memory residency and target-hardware frame budgets remain **UNRUN** in the cloud software renderer. Do not infer them from offline video capture rate or build wall time.

## Focused checks

```sh
python3 games/yuga-native/tests/hero_lod_cases.py --report /tmp/rama-lod-NEW-plumbing.json
LP_NUM_THREADS=2 godot --headless --path games/yuga-native \
  --script res://tests/hero_lod_cases.gd -- --report=/tmp/rama-lod-NEW-selector.json
LP_NUM_THREADS=2 godot --headless --max-threads 2 --path games/yuga-native \
  --script res://tests/hero_lod_binding_cases.gd -- --report=/tmp/rama-lod-NEW-binding.json
```

The structural suite intentionally damages masks, UVs, morph targets, rest/contact nodes, joint order, materials, weights, tangents, positions, indices, sparse records and GLB length. The selector suite covers oscillation, hold/reentry, rapid zoom, FOV/orthographic projection, nonfinite input and invalid/freed camera ownership. The small actual-engine binding suite uses real164-bone Skeleton/Skin/Mesh fixtures and nested rotation/scale, rejects malformed masks/rest/ordered binds/transforms/materials, proves one live rig/unique face and checks atomic rollback, bounded ownership and disposal. These checks do not accept actual rendered hero candidates.

## Technical references

The research desk read these pinned official sources; the local implementation uses their constraints:

- [Godot Mesh/ArrayMesh/ImporterMesh/GeometryInstance3D class definitions](https://github.com/godotengine/godot/tree/89cea143987d564363e15d207438530651d943ac/doc/classes): skin arrays contain4 or8 weights; index-only ArrayMesh LODs share vertex buffers; skin-aware importer generation needs transforms; visibility-range hysteresis and fading have distinct semantics.
- [Godot mesh LOD documentation](https://github.com/godotengine/godot-docs/blob/b10b7ed373c2d15555186914b82e167169b5b87b/tutorials/3d/mesh_lod.rst): screen-space selection and warnings about generated LODs on skinned meshes.
- [Godot image import documentation](https://github.com/godotengine/godot-docs/blob/b10b7ed373c2d15555186914b82e167169b5b87b/tutorials/assets_pipeline/importing_images.rst): encoded disk compression does not establish VRAM use.
- [glTF2 skin specification](https://github.com/KhronosGroup/glTF/blob/521a91d491f02bb7db7d445b35f591d09d2a64ce/specification/2.0/Specification.adoc): JOINTS values index the ordered skin joint list; inverse-bind order and paired normalized WEIGHTS sets must remain consistent.
- [meshoptimizer pinned source and MIT license](https://github.com/zeux/meshoptimizer/tree/7b2d4f4c817aea55d74dcd65d9763ac2ca608026): constrained attribute-aware simplification is an implementation aid, not art acceptance.
