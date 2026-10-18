# S5 original left shoulder armour — inactive candidate

`candidate-r4/` contains three real, closed 3D meshes: a domed shoulder cap,
two overlapping curved plates, rolled borders and one five-petal lotus relief.
This is an original source candidate, not accepted game art. Its action contact
gate fails; no runtime caller or canonical hero asset is changed.

The inspected identity reference is the left Rama figure in
`games/yuga/art/references/rama-hanuman-sita.png`. His anatomical left shoulder
(viewer-right) has a substantial gold/cobalt layered pauldron. The actual
`G0/template-priority-cold-600-r1/00-title-100.png` and
`graphics-six/G1/hero-render/light-front.png` show a shallow cap, partly obscured
by the broad sash. The existing original `art/hero-rama/build_hero.py` does have
a cap, small leaves and lotus detail; the object called “Shoulder blue lining”
uses gold. The defect is missing volume and layering at the visible scale,
not literally absent geometry. Exact reference and title pins are in the source
manifest. No new concept image substitutes for a native comparison.

The editable authoring source is `build_armour.py`. Curved solid patches have
3–3.5 mm thickness, the lotus has 1.7 mm backing, and the rolled gold borders
have 2.3–2.7 mm radius. A broad support envelope samples the actual body,
retained cap and drape; it does not generate texture-like surface noise.
The original cap remains present, underneath and partly occluded. The nearest
rest gap to its gold is about 1.76 mm. This gap and increased silhouette need
render review; no claim is made that the overlap is invisible.

| LOD | Vertices | Triangles | GLB bytes | Material draws |
| --- | ---: | ---: | ---: | ---: |
| Near | 5,646 | 8,928 | 472,788 | 3 |
| Mid | 3,175 | 4,684 | 263,704 | 3 |
| Far | 1,670 | 2,204 | 137,612 | 3 |

These are additional costs, not reductions in the existing hero. No skeleton,
animation, texture or image is duplicated in the new GLBs. All three use the
same authored guide forms. Each geometric component is closed after welding
coincident seam vertices. Stored normals/tangents and UVs are finite; tangent
handedness is explicit; RGB is white and secondary alpha is zero.

The three self-contained preview materials are ordinary lit PBR materials.
They intentionally do not reproduce the accepted textured finish. A native
review must use `shoulder_review.gd`, borrowing the existing hero's **Worked
warm gold**, **Cobalt handwoven silk** and **Recessed antique gold** material
objects after calibration, secondary and finish owners configure. The helper
adds no material mutation or independent animation/physics loop. It owns one
BoneAttachment3D and three mesh instances; the existing LOD owner supplies
the visible index explicitly. Release the helper before releasing those
material owners. The helper also releases itself when its visual leaves the
tree. Borrowed meshes/materials remain owned by their callers.

The source is in exact `upperarm01.L` local metres (joint slot 50), with no
new bone or bone writer. A rigid attachment passes source-rest contact tests
at all three LODs, but fails skin contact in **6 of 13** retained representative
draw samples. Splitting existing shoulder/upper-arm attachments fails **8 of
13**; using the clavicle instead has identical deformation in those samples.
Those split trials are proposed bindings only, not a change to the shipped
review mesh or helper. Neither fewer triangle pairs nor rest clearance is a
motion-quality improvement claim. Do not inflate the shell or hide these
contacts merely to obtain a numerical pass.

`representative-r4.json`, `split-representative-r4.json` and
`clavicle-representative-r4.json` retain complete full-triangle witnesses.
The source skin is deformed with all original weights and the retained actual
164-bone tape in `S3/W3/native-r5.json.gz`; imported index/name identity is
independently closed by `S4/W5/rail-mapping-review.json`. These are offline
direct-API pose evaluations, not a new candidate import, continuous modifier
execution or rendered acceptance. Thirteen selected samples suffice to
reject this binding; the other 335, mid/far poses and opposing secondary stress
remain unqualified. The strongest retained skin counterexample is Volley,
pitch 0, step 35. The helper requires the literal acknowledgement
`S5_SOURCE_CONTACTS_UNRESOLVED` for a deliberate diagnostic review.

Reconstruct in a coordinated CPU-only slot from the native project:

```sh
env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  taskset -c 4 /workspace/tooling/yuga-native-python/bin/python \
  art/hero-finish/s5-shoulder-armour/build_armour.py \
  --output "$PWD/art/hero-finish/s5-shoulder-armour/rebuilt-r4"
```

The output path must be new and inside the native project, because recorded
asset paths are project-relative. The hero input hash is fixed and verified again
after generation. `candidate-r4/generator.py` preserves the exact producing
source; the live builder is identical and is the runnable entry point. The
archived copy is not directly runnable from its deeper directory. The source manifest records transforms,
bone order, envelope, geometry components and output hashes. Each pose report
pins its producing checker; corresponding `check-source-single50.py`,
`check-source-split49.py` and `check-source-split48.py` snapshots are retained.
Run a historical snapshot from a temporary sibling of `build_armour.py` or
adjust only Python's import path to that directory; do not overwrite a sealed
report. Full commands and evidence are collected in `W3.md` and `receipt.json`.

Khronos validation reports zero errors and zero warnings on all three GLBs.
It also retains six informational unused-tangent/UV messages and eighteen
buffer-view-target hints per file; no perfect-validation claim is intended.
Earlier r1 construction failure, intersecting r2 and oversized r3 remain
preserved. No source GLB, rig, skin weights, material owner or motion code was
rewritten.

Next gate: correct articulated clearance while retaining the intended form,
then an isolated import and exact title/front, cast and rear off/on comparisons.
If a diagnostic render is requested before that correction, label the known
contacts and keep the candidate inactive. Reject excessive width, a detached
cap, a hidden arm silhouette, visible plate intersections or detail that
vanishes at gameplay scale. This does not resolve the hair mass, crown bends,
flat sash, general motion quality or Deadlock-level art target.
