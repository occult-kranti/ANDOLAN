# Closed-volume hair construction — C3 authoring

This is a rejected inactive coarse-clay construction for the Rama hero. The
current canonical hero is unchanged. All four actual views were reviewed and
rejected; no runtime gate is passed. The concept is a design target, not a
rendered game asset. See [the direct owner review](ACTUAL_REVIEW.md).

The rejected C1 and C2 sources/originals remain intact. C2's open C-section rear
surface plus Solidify produced a sheet, and its inherited radial scalp and
horizontal gather rings retained the helmet and capped-knob silhouette. Local
thickness and small dome displacements did not solve the construction.

`build_volume.py` instead creates six closed editable source lofts: three broad
directional scalp/temple sweeps, a sideways folded return through the fixed tie,
and two unequal volumetric S falls. Complete rounded-rectangle cross-sections
are oriented normal to each path. Width and depth are independent authored
controls. The inner scalp surface seats to the existing anatomy without
replacing its broad outer forms. There are no hair cards or Solidify modifiers.

The master retains all six source cages with unapplied Subdivision 1 under
`EDITABLE_ClosedLoft_Sources`. These source objects are hidden in the rendered
view; they can be unhidden and edited individually. The visible
`EDITABLE_WholeHair_CoarseClay` is their derived 1.5 mm voxel union, followed by
one light two-iteration surface fairing. Rebuilding updates the derived mesh;
it does not destroy the original source cages. This is coarse authoring
topology, not production topology or a skinning mesh.

The fixed gold tie occupies glTF Y 1.865–1.871 m, centered approximately at
(0, 1.868, -0.040). Its center is only 9.71 mm above C2's maximum scalp height;
the upright knob was not forced solely by this offset. C3 threads the same
anchor and turns laterally. The tie, crown, head, brows, other reference surfaces,
four cameras, lights and material values are protected. The loaded parent is
`../clay-framing-r3/whole-hair-clay-framing-r3.blend`, SHA-256
`71763ab25ed84719a8479bcce771732d50db980780b47c7c4b68114bf2bb9c2f`.
The authoring references are rest-space geometry, not an animated rig transfer.

The exact source save is retained at [authoring-payload/build-r1](authoring-payload/build-r1/).
The original `/workspace/scratch/yuga-hair-volume-r3/build-r1/` paths remain intact as
hardlink aliases. [The recovery map](authoring-payload/recovery-map.json) pins every
manifest member and the separate inner-wall classification; no payload bytes were
changed or physically duplicated. [The source receipt](source-receipt.json) seals
this rejected editable construction and its dependencies.
Its `manifest.json` pins the editable scene, source cages, actual derived mesh,
before/after semantic snapshots and four-camera projection report. Compressed
JSON geometry is world-rest glTF metres, +Y up, +Z front; Blender mapping is
(x, -z, y). The scene has six editable source objects plus one visible result.
Do not substitute the hidden source meshes for the visible union in fit tests.

Source save command, from the repository root:

```sh
taskset -c 3 env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 blender --background games/yuga-native/art/hero-finish/hair-sculpt-design/clay-framing-r3/whole-hair-clay-framing-r3.blend --threads 1 --python-exit-code 1 --python games/yuga-native/art/hero-finish/hair-sculpt-design/clay-volume-r3/build_volume.py -- --output /workspace/scratch/yuga-hair-volume-r3/build-r1
```

The first startup attempt failed with an unmatched closing parenthesis before
executing the builder, producing no model/output directory. That syntax error
was corrected; the subsequent source save exited 0. Blender emitted its known
unsupported-denoiser enum warnings while serializing scene properties. No
render, import, export, download or installation ran during source creation.
The four existing camera projection gates pass. Independent topology checks
pass for all six closed sources and the visible union, and the protected
semantic census passes 12/12. The independent check compares pinned exported
censuses, not a fresh Blender reload. Buried scalp intersections are retained;
hardware intersections remain unresolved. See the independent
[validation and contact classification](../../../../docs/evidence/desktop-finish/hair-volume-r3/W2-validation/REVIEW.md).

`capture_volume.py` supports a read-only `--preflight`, or the same four raw
1024×1024 Cycles 32-sample images as C1/C2. It requires the exact expected scene
hash and a fresh output directory. Actual capture must wait for the shared
CPU0/1 raster lane. The helper disables unsupported denoising only in memory;
it never saves the scene. Both helpers guard at least 500 MiB free on /workspace.

The actual four-view diagnostic completed with exit 0 in 89.554 seconds; exact
originals and capture metadata are under
`/workspace/scratch/yuga-hair-volume-r3/actual-r1`. W1 owns the executed capture
seal. The model, builder and capture helper remain unchanged from that run.
Full outlines must read before fine strands. A technically closed mesh or
successful fit check cannot accept the sculpt. Detail, UVs, weights, LODs,
GLBs, animated contacts and runtime activation remain deferred.
