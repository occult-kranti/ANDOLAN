# Review-only smooth diadem revision

Separate follow-up to the sealed `s4-diadem-fit` candidate. Its actual matched images improve the floating rear rail but show angular temple turns and a wavy side band. The new generator replaces sampled radial conformity with one authored planar elliptical side/rear arc: 100 mm X radius, 130 mm Z radius, centre Z = 44 mm at Y = 1792 mm. A broad quintic transition retains the same original protected front sector. The fixed curve is checked against hair/head full triangles; it never changes shape to follow individual support samples. The original 3.5 mm tube cross-sections are transported using the preserved source UV parameter.

Only original rail POSITION/NORMAL/TANGENT records in three copied GLBs may differ. Separate front crest/leaf/stone components, complete JSON, morphs, indices, UV, rig, weights, vertex colours, materials, images and all non-rail binary records must remain byte-exact. Normals/tangents use the inherited UV-derived frame calculation. The near rail remains head joint104 with weight1 and secondary alpha0. Preserved front centre points do not imply byte-identical adjacent tube frames.

Generator and stored-float verifier derive from the sealed first packet without modifying it. Strict canonical source SHA pins remain, and the new builder refuses a changed first-builder dependency. Canonical hero assets are never output targets. This authoring directory is outside ordinary runtime import/export.

## Sealed source candidate

`candidate-r2/` contains the three complete inactive GLBs. The first 96 × 125 mm attempt is retained under `candidate-r1/` as REJECTED: its near scalp/hair full-triangle clearance failed before other LOD construction. The separate envelope probe explains its tight 5.22 mm radial centre gap. R2 widens the one global ellipse to 100 × 130 mm, rather than adding local bends.

Stored float32 full-triangle scalp/hair clearance is at least 2.810409 / 2.200967 / 2.485165 mm in near/mid/far, no crossing pairs. Rail triangle counts remain 1,130 / 764 / 380, and maximum vertex displacement is 22.204 mm. Near surface-gap vertex median is 11.855 mm (first fitted candidate 9.645 mm, original 15.964 mm); maximum 25.434 mm (first fit 21.795 mm, original 32.778 mm). These are source-rest distances, not visible-gap judgements. The intended tradeoff is roughly 2 mm more median stand-off than the first fit, with a continuous deliberate arc instead of local hair-following bends.

`verify_candidate.py` independently reads stored floats, proves complete JSON/file size and every byte outside selected POSITION/NORMAL/TANGENT records unchanged, rejects an injected outside-byte mutation, checks finite unit UV-derived TBN frames and repeats complete triangle clearance. The retained 348 direct-API near hand-transform replay passes a 40 mm lower bound. This is offline replay of the pinned historic tape, not 348 new runtime executions. Mid/far posed hand contact and arbitrary animated scalp/hair clearance are unqualified.

All three Khronos validations have zero errors and three inherited warnings, with entire issue payloads equal to the first fit. Canonical and first-candidate GLBs/builder still match the preserved input hashes. Full commands, logs, tools, dependency pins and rejected attempt are under `docs/evidence/desktop-finish/S4/W2-smooth-r1/`.

From this native project, reproduce into a **fresh** output directory:

```sh
taskset -c 4 env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  /workspace/tooling/yuga-native-python/bin/python \
  art/hero-finish/s4-diadem-smooth/build_candidate.py --output /absolute/fresh/output
```

No importer, Godot or Blender was run for this packet. Fresh private native import remains required: the first candidate's compiled SCNs are not valid for these new raw bytes. `capture_review.gd` preserves the exact original four-view camera/pose/light/cast procedure; only its admission hashes and comment differ. Stage it at the original helper runtime path in new sealed children. See [capture handoff](CAPTURE_HANDOFF.md).

Actual matched rest-front/profile/rear/cast-three-quarter images remain mandatory. Reject temple kinks, side humps, clipping, crest loss or a reopened floating rear gap. Neither construction nor clearance proves a smoother appearance. No default promotion is authorized by this source receipt, and this is not full-hero quality acceptance.
