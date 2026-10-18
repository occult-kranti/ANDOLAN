# W4 world render resource reuse — D07 / I01

Source baseline: `a7c9f46bbbfeef59a042919231978436892be934`. One original procedural traversal builder changes; Confluence, frontage, floor, nav, collision and player sources are untouched.

The manifest builds 238 MeshInstance3D nodes across eight raised decks and ten tether relics. Previously each node owned a new primitive. The same node graph now references 13 per-build primitive resources (225 fewer unique Mesh resources). Complete typed keys retain dimensions, subdivisions, segment/ring counts, cap/hemisphere state and flipped orientation. Position/rotation/scale remain on the nodes. Shared meshes have no embedded material; existing material overrides remain local to each build. A reused builder starts a fresh pool, so old worlds do not retain its material/cache state.

This proves a bounded allocation improvement, not fewer draw calls, measured frame-time improvement, GPU memory savings, finished map art or commercial visual quality. No batching, MultiMesh, culling, geometry simplification, authority, collision, light or texture changes occur.

## Actual native evidence

The retained unmodified original builder is executed from text in baseline mode; it is independently verified byte-exact to the a7 Git blob. The final fixture hard-pins SHA `ee070b0a4b1c0bb07ac645681e6ef3dcf0311adb88afe07ece3ecc75b4ab971b` before compiling it. The baseline is not a weakened/reimplemented geometry oracle or a canonical source revert.

- Valid original baseline: **20/23**, failing resource-sharing, reused-builder reset and release of resources still retained by the old reused builder.
- Initial candidate: **23/23**, clean exit 0. Full generated arrays (vertices/normals/tangents/UVs/indices), AABBs, ordered topology, node transforms/metadata and authored material/shader values equal the original. Independent builders and same-builder fresh builds remain independent. Geometry/transform/material corruption is detected and restored; teardown releases resources.
- Existing actual world scene: **29/29**, clean exit 0, about 6.90 seconds. It exercises live Confluence startup, real floor/deck/authority surfaces, capsule route sweeps and restored mutation negatives.
- Final deterministic fixture replay: **23/23**, clean exit 0 in 0.260 seconds, no engine diagnostics. It adds the requested fixed original-source assertion and removes random UID data from ordinary reports.

The first fixture attempt incorrectly called ArrayMesh-only `surface_get_primitive_type` on PrimitiveMesh. It is invalid evidence, preserved in `fixture-api-failure-r1` with exact source, report and lossless compressed engine log. The fixture successor compares actual full arrays and concrete primitive classes. Runtime resources were unchanged by this fixture correction. Its wrapper's engine exit was not captured separately; the outer shell's final Python read returned 0 and is not reported as native success.

`executed-fixture-before-root-pin.gd.txt` reproduces the exact recorded SHA of valid baseline/initial-candidate executions. It was recovered from the final fixture by reversing the two documented root-requested source-only edits, and hash-checked against both original reports. Final fixture is a new explicit successor.

Stable helper/test UIDs were generated through native ResourceUID.create_id/id_to_text calls in these retained executions, separately recorded in `uid-generation.json`; no editor/import ran. The random generation field is intentionally absent from the final reusable fixture.

## Actual view gate

W1 owns one fresh matched full-world capture, not W4. Proposed common camera `(37,22,-51)` looking at `(37,5.5,-88)`, FOV50, near0.1/far400 exposes both east sun decks, their relief/trim/medallions/embers and tether rings/brackets. W1 must check actual projected bounds before capture and hold the same full world, camera, final-modifier pose, army/scene clocks, lights/material values and physics in both branches. Only the original-vs-pooled traversal builder is the behavior delta; helper may exist unused in baseline. Geometry/resource identity gate passes; native pixel equivalence remains open until W1's exact source-bound originals.

Independent W6 source review found no blocker; no extra engine rerun by that reviewer. Shared catalog/packaging registration and integration acceptance belong to root/W6.
