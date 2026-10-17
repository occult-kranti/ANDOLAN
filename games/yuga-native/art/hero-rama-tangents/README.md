# MikkTSpace authoring diagnostics

This is executable, licensed source reuse: the official, unmodified Morten S.
Mikkelsen C implementation is compiled and called through `bridge.c`. It is an
offline authoring tool, with no Godot runtime dependency. It does not copy or
analyze a commercial game's assets.

Upstream: [mmikk/MikkTSpace](https://github.com/mmikk/MikkTSpace), commit
`3e895b49d05ea07e4c2133156cfa94369e19e409`. The exact C, header and upstream README
hashes are in [vendor/upstream.json](vendor/upstream.json). Their complete
zlib-style permissive notices remain in the source files. The original YUGA
bridge is declared CC0-1.0; it is not the upstream algorithm.

## Commands

Run from the repository root with Python 3, NumPy 2.3.5 and a C99 compiler:

```sh
python3 games/yuga-native/tests/hero_tangent_cases.py \
  --report=/absolute/fresh/tangent-tests.json
python3 games/yuga-native/art/hero-rama-tangents/build_bridge.py \
  --output=/absolute/fresh/mikk-build
python3 games/yuga-native/art/hero-rama-tangents/regenerate.py \
  --source=/absolute/source.glb \
  --library=/absolute/fresh/mikk-build/libyuga_mikktspace.so \
  --report=/absolute/fresh/diagnostic.json \
  --corners=/absolute/fresh/corners.npz \
  --candidate=/absolute/fresh/tangent-candidate.glb
```

All report/candidate paths must be fresh. The test suite builds offline in a
temporary directory by default; `--build-dir=/absolute/fresh/cache` retains its
build. `--candidate` and `--corners` are optional. A completed diagnosis exits 0;
a requested but refused candidate exits 2 with its reasons in the report.
Malformed input or unsafe output aliases raise an error. Inputs are read only.

## Corner and preservation contract

Upstream's header warns that outputs are unindexed, and that averaging or
overwriting tangent spaces through an existing index list produces incorrect
results. The bridge therefore writes one `(tangent.xyz, handedness)` record for
each face/corner. Conversion to existing source vertices is allowed only when
every valid corner at that vertex has exactly the same float32 direction and
sign. No averaging or tolerance-based welding is performed. Mirrored seams
remain distinct. The report includes direction differences so small numerical
conflicts are distinguishable from large seam discontinuities.

Finite float32 geometry/UV coordinates are bounded to magnitude 1,000,000;
capacity is two million vertices and six million corners per domain. Boolean,
fractional, negative and out-of-range indices are rejected before callbacks.
Normals must already be unit within 0.002; this tool does not silently change
source normals. Float64 values overflowing or collapsing during float32
conversion are checked in the representation actually supplied to C.

The conservative authoring policy marks geometry double-area or absolute UV
determinant at or below `1e-12` unresolved. Diagnostics run MikkTSpace on the
clean faces and retain unresolved corners as NaN **only in the diagnostic
archive**. Upstream can inherit tangents onto degenerate primitives; that is not
treated here as a verified UV-derived recovery. A strict candidate requires no
unresolved, unused or conflicting vertices. This is a tool acceptance policy,
not a claim that upstream MikkTSpace cannot process degenerates.

Compatible candidates change dense base `TANGENT` records only, in the original
byte layout. JSON, indices, positions, normals, UVs, weights, joints, morphs,
COLOR masks, images, clips and face/rig ownership remain unchanged. Independent
reparse checks reject aliasing between tangent storage and protected accessors
or images before a candidate is published. Existing tangent morph deltas or
changed accessor min/max metadata require a separate authoring step and block
this tool. No native import, Blender export, render or runtime promotion occurs.

## Actual Rama result

The source is the repaired R4f GLB, SHA-256
`de61dc4c470920eab6f3265bc5467da7f9fb33d6fae2129a9353e7ca6d24d3f5`:
234,846 vertices, 408,316 triangles and 18 material domains. The strict rebake
was refused and no candidate GLB was written. The source hash is unchanged.
There are 5,400 geometry-degenerate and 18,360 UV-degenerate faces, 22,912 in
their union. Three additional clean-face corners in Ivory silk fail the output
frame validation, giving 68,739 unresolved corners in total. Six source vertices
have differing valid corner directions under
the exact-agreement policy. There are no shared-index handedness conflicts.
Three skin/lip domains satisfy the strict mapping; fifteen domains are blocked.
These counts describe this tool's stated epsilon and float32 domain.

7,693 of the existing 7,797 nonorthogonal source tangent records touch unresolved
corners. Replacing them with averaged or arbitrary frames would hide the
authoring problem. The next controlled experiment is a source-native UV/pole
and seam correction in a bounded cloth or gold region, preserving rig, weights,
contacts, mask semantics and face partition. Re-run this tool, then compare the
same lighting/camera/material/pose in the native renderer, including normal-map
handedness and animation deformation. A rebake alone cannot accept final art,
runtime performance or commercial game quality.

Evidence and exact source/build/diagnostic identities live under
`docs/evidence/reuse-study/mikktspace/`. Static REA/Ghidra analysis of this actual
compiled bridge is independent supplemental evidence; it does not establish
full shader parity, asset quality or whole-game reverse engineering.
