# Offline persistent triangle repair

`repair_mesh.py` creates a fresh candidate **outside the native project**. It
never overwrites, imports, exports, promotes or changes a runtime asset. This is
an original YUGA authoring tool using NumPy and the existing sparse-aware
`../hero-rama-lod/glb_lod.py` reader. It does not contain commercial game code.

The default `strict` policy removes a triangle only when an index is repeated,
or a pair of its vertices has byte-identical records in **every** vertex
attribute and **every** morph channel. Bind-pose zero area, small area and UV
degeneracy are insufficient. Different skin weights, position morphs or
procedural motion masks can make a flat bind-pose triangle visible later.

The optional `yuga-secondary-v1` experiment is restricted to these exact inputs:

| Input | SHA-256 |
| --- | --- |
| `assets/heroes/rama-hero.glb` | `de61dc4c470920eab6f3265bc5467da7f9fb33d6fae2129a9353e7ca6d24d3f5` |
| `shaders/rama_secondary_cloth.gdshader` | `c1712f075af34b0e57dd7f70e5494c2060703e7f1ee68ff87c8a645cff95c6d7` |

The inspected shader's complete `vertex()` function adds
`secondary_offset * clamp(COLOR.a, 0, 1)^2` to the skinned position. This policy
therefore requires equal POSITION, **all** JOINTS/WEIGHTS sets, **all** position
morph deltas and **all** COLOR records. UV, NORMAL, TANGENT and normal/tangent
morph deltas may differ: they do not change position under this specific
deformation contract. Full COLOR equality is deliberately more conservative
than comparing only the shader's effective alpha mask. A source or shader hash
change refuses the opt-in operation. This is not a general license to delete
seam duplicates on other meshes or custom shaders.

Both policies assume core glTF skin/morph semantics and no external
vertex-ID-dependent deformation. Unsupported extensions, compressed storage,
external buffers/images, non-indexed meshes and non-triangle primitives are
refused. Only the current material-only specular/sheen extensions are accepted.
Input size, expanded accessor storage, counts and layouts are bounded; this
deliberately narrow reader check is not a full glTF validation service.

From the repository root, with Python 3 and NumPy already installed:

```sh
taskset -c 0,1 env LP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=1 python3 \
  games/yuga-native/tests/hero_mesh_repair_cases.py

# Use fresh output names; an existing file is always refused.
taskset -c 0,1 env LP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=1 python3 \
  games/yuga-native/art/hero-rama-repair/repair_mesh.py \
  games/yuga-native/assets/heroes/rama-hero.glb \
  --candidate /workspace/scratch/my-mesh-check/rama-secondary.glb \
  --report /workspace/scratch/my-mesh-check/report.json \
  --deformation-policy yuga-secondary-v1
```

The importable API is `repair(source, candidate, report, policy="strict")`.
`inspect(glb, policy)` returns per-primitive diagnostics and selected index
arrays. The latter is a low-level diagnostic helper; it does not perform the
public experiment's source/shader pin gate. Call `repair()` for candidate
generation. CLI exit 0 means the candidate and report were written; exit 2
means refusal. A primitive that would become empty blocks the entire candidate
and writes a diagnostic report. Other invalid input is rejected before output.

Every changed primitive receives a new index accessor and bufferView. Shared
old index accessors are never mutated. The original embedded BIN chunk remains
an exact prefix, including its old padding; old accessors, views, geometry,
skin, morph, animation, image data and their JSON records remain exact. Only
primitive index references, appended index accessors/views and the buffer's
logical byte length change. New index accessors retain the unsigned component
type and get correct count/min/max; retained triangle order and material
partitions stay unchanged. Old unused index storage is intentionally retained,
so candidate files can grow. A no-op candidate is an exact source-file copy.

Geometry/UV diagnostics use float64 double area divided implicitly by the
maximum local squared edge length, with a `64 * float64 epsilon` threshold.
Reports distinguish exact computed zero and positive near-zero area. This
scale-relative threshold is **diagnostic only**. No tiny positive geometry or
UV-degenerate triangle is removed without an exact pair proof. A float64 zero
calculation itself is also not removal proof.

The source-bound experiment is archived under
`docs/evidence/open-art-wave/mesh/repair-r1/`. On the pinned hero, strict mode
removes zero faces; the opt-in policy removes 5,256 of 408,316 faces and retains
403,060. It leaves 36 computed-zero and 108 near-flat-but-positive faces for
authored topology review. All 5,256 pair proofs also pass full COLOR equality.
The candidate preserves remaining UV degeneracy and unresolved tangent domains;
it does not rewrite UVs or average tangent frames. This is supporting geometry
evidence, **not art acceptance, performance measurement or runtime approval**.

The fixture checks preservation, shared accessors/material boundaries, all
unsigned index widths, min/max, normalized weights, sparse morphs, interleaved
storage, tiny real triangles, scale variation, lifecycle of fresh outputs and
corrupt/unsupported inputs. Independent calculations show bind-pose duplicate
vertices becoming visible through different joint transforms, morph positions
and secondary alpha masks; all must be retained. Next owners must review posed
geometry and shading, diagnose remaining UV domains, regenerate official
per-corner tangents without averaging, and rerun independent acceptance before
considering promotion. No Godot/Blender import, renderer or human pose review
was performed by this tool.
