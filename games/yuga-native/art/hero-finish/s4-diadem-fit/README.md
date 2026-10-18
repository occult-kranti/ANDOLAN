# Review-only diadem rail refit

The retained front/profile/rear originals show an open gold halo around the
hair. The authored lower rail sits 6.88–32.78 mm from the source hair/head;
its rear vertex median is about 25.3 mm. The broad dark hair lobes are a separate
defect and are not corrected by this component.

`build_candidate.py` refits the original lower rail using its original tube UV
parameter and the actual R7 hair/head envelope. The side/rear centerline moves
inward; the front centerline stays fixed. Original 3.5 mm tube offsets are
transported to that centerline. No new geometry, material, texture, node, bone
or callback is added. The near component is exactly vertices 24830–25558 of
mesh 2 / gold primitive 2. Matching mid/far components are independently selected
and their vertex IDs are recorded, because those LODs compact the source arrays.

The separate front lotus/leafwork components remain byte-exact. This does not
promise unchanged front rail frames: all rail normals/tangents are recomputed,
and neighboring-centerline transport changes sixteen near front rail positions
by at most 0.146 micrometres. The independent review follow-up records exact
front-sector differences in `docs/evidence/desktop-finish/S4/W3/`.

The three copied GLBs in `candidate-r1/` retain their file sizes, complete JSON
and every binary byte except the selected rail POSITION/NORMAL/TANGENT records.
Indices, UVs, all other vertex records, images, materials, morphs, skin bindings,
rig and animation are unchanged. The rail remains fully bound to head joint104
with weight1 and secondary alpha0. Canonical GLBs are untouched. This directory
is excluded from ordinary import/export by the existing authoring boundary.

From the native project, in a coordinated CPU-only slot:

```sh
taskset -c 2 env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  /workspace/tooling/yuga-native-python/bin/python \
  art/hero-finish/s4-diadem-fit/build_candidate.py --output /absolute/fresh/directory
```

The output path must not exist. Input SHA pins are strict. The generator uses
the existing GLB reader and retained independent full-triangle narrow phase;
it does not launch Blender, Godot, an importer or exporter. `source-manifest.json`
records input/output hashes, selected records, original/candidate centerlines,
byte-preservation checks and rest-clearance witnesses. The generator's initial
clearance uses its double-precision construction. `verify_candidate.py` then
reads the stored float32 GLBs, checks the allowed byte ranges and frame validity,
repeats full-triangle rest clearance and replays the retained 348 native draw
transforms against actual imported hand influences. Native candidate import
remains separate.

R1 has 1,130 / 764 / 380 rail triangles in near/mid/far, unchanged from source.
Maximum movement is 29.76 mm. Its complete rail triangles clear the source
head/hair by at least 2.12 / 2.02 / 2.29 mm in the retained rest model. These are
geometry results. Stored-float checks pass with the same rounded bounds, all
three Khronos reports have zero errors and three inherited warnings, and the
near rail stays at least 40 mm from the selected hand triangles in all 348
retained direct-API draw samples. No new candidate was imported or executed;
mid/far action replay, whole-body/motion continuity and pixels remain unqualified.

W1 owns candidate import and actual matched front/profile/rear rest plus cast
images. Keep the same camera, light, pose, time, shaders and upper-hair/fletching
helpers off. Reject pinching, visible tube kinks, crest separation, new arm/ear
contact or no useful silhouette improvement. No default promotion follows from
source checks. The crown rail, solid hair mass and cast/cloth contacts have
separate acceptance scopes.
