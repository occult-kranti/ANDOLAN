# Secondary-frame probe

Run from repository root, with Python 3 standard library only:

```sh
python -m unittest discover -s games/yuga-native/tools/visual-rounds/reuse -p 'test_*.py' -v
python games/yuga-native/tools/visual-rounds/reuse/secondary_frame_probe.py \
  games/yuga-native/assets/heroes/rama-hero.glb --output /absolute/fresh/report.json
```

This offline diagnostic measures how the current shader's per-vertex
`offset * alpha * alpha` displacement changes **triangle geometry normals**.
It admits the four existing secondary-material names and samples six mesh-local
axis directions at the current 75 mm cloth and 18 mm hair limits. It records
varying-mask triangles, exactly zero masks, baseline nearly degenerate triangles
(cross-product length <= 1e-12), deformed degeneracies, and normal-angle quantiles.
Quantiles include only varying-mask, nondegenerate triangles across six offsets.
An empty sample set means no varying-mask triangles, not measured angle accuracy.

Input is read only; output must be a new file. No installation, engine import,
runtime dependency, mesh rewrite, image bake or renderer is involved. Supported
inputs are embedded GLB2 triangle primitives using ordinary scalar/vector
accessors, including strided/normalized unsigned colors. Sparse accessors,
compressed selected primitives and external buffers are refused. This is not a
complete glTF validator or adversarial-file security boundary.

The selected face-normal construction is a small adaptation of Godot 4.6.3
`Plane`/`SurfaceTool` (MIT); see [NOTICE](NOTICE.md). We use its counterclockwise
branch for glTF. Original UV differential math and tests retain mirrored
handedness; **that UV frame helper is tested on synthetic triangles, not audited
across every imported GLB UV/tangent in this command**.

Interpretation matters: this is a rest-space local stress test. It does not skin
vertices, apply hierarchy transforms, sample actual spring trajectories, compare
smooth imported vertex normals, or prove triangle inversion/collision/shading
in gameplay. A >90° turn relative to rest is not on its own a topological
inversion. The six directions do not bound every direction on the sphere.
Actual `_publish()` offsets also depend on visual/mesh basis conversion.
No threshold here grants art acceptance or FPS claims.

An anchored vertex can stay exactly fixed while an incident triangle rotates.
Squaring masks does not eliminate that discrete triangle effect. Any runtime
frame correction must match the actual displaced/skinned surface, preserve
normal-map tangent handedness and handle mirrored/degenerate UVs. Replacing
smooth normals with flat face normals can change the intended authored surface.
Use this tool to identify questions for actual matched moving-light/pose reviews.

The source ledger and executed baseline are in
`docs/evidence/visual-rounds/round3/role07/`. Candidate owners may retain their own
reports beside their independently frozen source manifests.
