# Coverage-first continuous hair — C4 authoring

Rejected inactive coarse editable hair construction for native YUGA. The canonical hero is
unchanged. Both C4 actual gates are complete; root and the source owner reject the final
major forms. See [the final actual review](ACTUAL_REVIEW.md). No accepted art,
rig transfer or runtime quality follows. The rejected C3 scene, sources, actual originals and receipt are untouched.

C4 loads the exact rejected C3 scene, SHA-256
`1d4a2f77b09a721655145c120ec58c72f2752ec72d464c0fd27c1fc1913646b3`,
then replaces only its coarse hair result and hidden editable hair sources.
A thin continuous scalp volume seats to the protected head via radial ray hits.
Its outer/inner offsets are +3.5/−1 mm, with an explicit forehead hairline,
openings above both ears and a lower nape boundary. Six shallow surface-following
sweeps rise from tapered buried roots. An authored filled gather passes through the
fixed tie, and two unequal overlapping S falls narrow in width and depth over
their terminal length. These are major authoring forms; no fine strands were added.

Ten closed source meshes remain editable under `EDITABLE_C4_CoverageAndSweeps`.
The scalp source has a direct high-resolution cage. The nine lofts retain
unapplied Subdivision 2. The visible `EDITABLE_WholeHair_CoarseClay` is a 1.5 mm
voxel union with one two-iteration light surface fairing. Source cages are hidden
from rendering. Edit sources and rebuild the union rather than treating the
union as finished production topology. Coordinates in JSON are glTF metres,
+Y up and +Z front; Blender uses (x, −z, y).

The first C4 actual was rejected; see [its owner review](ACTUAL_REVIEW_R1.md).
The one bounded correction roots a filled gather in the rear scalp and brings
the upper falls together. The original executed builder remains
`build_volume_r1.py`; the current `build_volume.py` creates the r2 correction.
The scalp and all six sweep cages are byte-identical across r1/r2.

Current build command from `/workspace/ANDOLAN`:

```sh
taskset -c 3 env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 blender --background games/yuga-native/art/hero-finish/hair-sculpt-design/clay-volume-r3/authoring-payload/build-r1/whole-hair-volume-r3.blend --threads 1 --python-exit-code 1 --python games/yuga-native/art/hero-finish/hair-sculpt-design/clay-volume-r4/build_volume.py -- --output /workspace/scratch/yuga-hair-volume-r4/build-r2
```

The exact editable scene, source cages, derived mesh, semantic snapshots,
projection/check reports and source logs are retained in
[authoring-payload](authoring-payload/), with a hardlink recovery map.
No payload bytes were physically duplicated.

The build exited 0 and saved `whole-hair-volume-r4.blend`, SHA-256
`da97ad89b5660eadc688eb58e4c73cad42b7b3f767daefb99c17028758439a88`.
The visible result has 134,814 vertices and 134,812 faces. The builder's semantic
comparison permits only hair source/result changes and resulting material user
counts. A fresh Blender reload with `check_saved.py` also exited 0: protected
objects/mesh arrays, cameras, material values, lights, world and scene settings
match the parent; all 11 source/result meshes have zero boundary/nonmanifold
edges; all four unchanged camera projection gates pass. Process-only
`session_uid` and derived `users` counts are excluded from this comparison.
These are source-owner checks, not independent art acceptance. Blender emitted
its known unsupported denoiser enum warning during property census; it did not
prevent save or verification.

`capture_volume.py` is byte-identical to the preserved C3 capture helper. It
requires a pinned exact scene SHA and fresh output directory, preserves four
1024×1024 cameras and 32 CPU Cycles samples, and disables unsupported denoising
only in memory. It never saves the source. W1 owns the sole CPU0/1 actual raster
lane; the exact executed handoff is in `CAPTURE_HANDOFF.md`. The first actual take
exited 0 in 90.940 seconds, and the single corrected take exited 0 in 94.301
seconds. All eight originals were directly opened. The saved scenes and capture
helper remained unchanged during capture. The correction budget is exhausted.

Hidden scalp seating intersections are intentional. Visible skin breakthrough,
rail and tie readability, fold shape and fall taper were judged in the actual
originals; the peg, inflated falls and helmet-like side panels reject the result. There is no blanket zero-contact requirement. No GLB, import,
rig, animation, runtime, fine-detail or promotion work is included.
