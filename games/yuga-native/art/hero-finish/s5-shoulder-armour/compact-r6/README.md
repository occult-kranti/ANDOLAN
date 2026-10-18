# Original compact shoulder — inactive review candidate

`replacement-r7/` is the final source candidate for this packet. It replaces the
original anatomical-left cap with a curved gold cap, a smaller cobalt overlap,
rolled gold edges and one five-petal lotus. It is original repository authoring,
guided by the left Rama in `games/yuga/art/references/rama-hanuman-sita.png`.
No commercial mesh or new external texture is included. The original cap exists;
this proposal changes its silhouette rather than filling an absent asset.

The shape is deliberately compact after the retained larger, articulated and
skinned trials failed actual-pose contact or metal-strain checks. The gold wall is
3.5 mm, cobalt wall 3 mm, with a 6 mm radial layer step and roughly 10% overlap.
All new vertices use the existing `shoulder01.L` joint 49 at weight 1 and secondary
alpha 0. The original 164-joint rig and motion controller remain unchanged.
Worked gold, recessed gold and cobalt silk use their existing material resources;
there is no new runtime helper, shader, material, draw primitive or bone writer.

| LOD | Final SHA256 | Active triangles before → after | Removed / added | Added BIN bytes |
| --- | --- | --- | --- | --- |
| Near | `8755b65b1b103b3d3210993240c9e18c196510757e1b031bb684eb45e47b629b` | 367864 → 359084 | 15228 / 6448 | 10300764 |
| Mid | `8ae53f22a9536d7dcf3d9506906ac83e15222d0b9eadacd51cff82c7d7b43371` | 202034 → 199590 | 5812 / 3368 | 4349208 |
| Far | `5b382f97b64658784d15fbb6ef816af22c62d8148717b70c797dea8e2172be37` | 136228 → 135866 | 1990 / 1628 | 1922388 |

The parent is the accepted sash-UV trio db4b/b594/aef8, including the smooth crown.
`accepted-uv-composition-r7.json` proves that every byte of each parent BIN remains
as the prefix. Compared with the cleared shoulder-r6, only the two copies of the
declared sash UV rows change: the original retained array and its appended active
copy. All other BIN bytes and the entire GLB JSON are identical. The unaccepted
hair proposal is excluded. No canonical asset or notice was replaced.

`replacement-proof-r7.json` verifies the exact old-cap triangle removal map,
four bounded body primitives, 14 unchanged primitives, all original vertex
records, every image/rig/animation/morph/material, finite new frames/UVs and
rigid49 masks. All three actual Khronos results have zero errors and the same three
inherited non-root skinned-node warnings. Material primitive count stays 18.

`candidate-r5/` is the standalone authored sculpture. `build_candidate.py`
reconstructs those three GLBs byte-for-byte in the executed `reconstruction-r5/` run.
`replace_left_cap.py` builds the historical smooth-parent replacement;
`compose_accepted_uv.py` builds the accepted-UV successor and verifies the exact
two-copy UV composition. Both fail if expected source pins differ. The assembly
manifest records all source paths/hashes, exact removed triangle/vertex IDs and
the borrowed original authoring source. The full-hero reconstruction command is
provided by `reconstruct_review.py`; a second full-hero rebuild was not run merely
to duplicate the 99 MB candidate. Python/NumPy and the original sealed generator
are required; contact tools additionally use the existing SciPy geometry helpers.

## Executed contact scope

- 348 retained direct-API draw/cancel samples at each LOD, plus 37 additional
  named-bone idle/five-ability samples at each LOD, pass full triangle checks
  against all 18 source primitive groups. Only the exactly superseded rigid50
  cap triangles in gold, recessed gold and sapphire are omitted.
- Minimum checked nominal gaps are 1.970 mm near, 4.908 mm mid and at least 6 mm far.
  All 37 additional poses guarantee at least 6 mm. Stored float32 rounding under
  all 385 bone49 skin operators reduces the guaranteed minima by less than
  0.000062 mm; `stored-pose-margin-r6.json` transfers to r7 because geometry is exact.
- 120 separate secondary fixtures pass: five retained poses, eight opposing
  offset directions, three LODs. Only runtime-admitted cloth/gold/brocade receives
  75 mm offsets and hair 18 mm, weighted by normalized alpha². Skin/neck stays skinned
  and static; new armour alpha is zero. This is a bounded stress set.
- The 348-sample arrow check uses the actual captured `arrow_global` transform and
  a conservative local segment y 0…0.785 m with 12 mm radius. The radius expands by
  the transform's largest singular value; separated AABBs provide a conservative
  lower bound, about 174 mm. Hidden arrows are checked too. The additional 37-pose
  tape lacks arrow transforms and has no arrow-clearance claim.

The face is neutral in these source collision evaluations. Source bow/string
geometry follows the retained bone poses; optional fletching is absent. No actor
physics-capsule fit, world/other-character contact, new-plate self-intersection,
arbitrary facial morph, arbitrary continuous transition or unaccepted-hair contact
is certified. Decorative rolled-edge/plate overlaps are authored joins, not a
self-collision simulation. These tests are mathematical source replay, not new
GPU skin execution or rendered motion.

## Import and image handoff

W1 owns the later isolated import and matched images. `shoulder_import_semantics.gd`
exports actual cached resource semantics and arrays for the four changed body
materials. `compare_shoulder_import.py` compares complete noncap vertex bytes and
oriented triangle multisets, so cyclic index reorder is allowed while reversed,
missing or extra triangles fail. It checks exact source POSITION/UV/topology for
new geometry, with explicit small decoded-frame quantization bounds. All remaining
materials, textures, transforms, 164 bones/binds, animations and morphs must match.
Its eight executed synthetic negative controls pass; the actual shoulder import
comparison is **not run**.

`shoulder_capture.gd` is a common, source-pinned four-view helper: rest-front,
rest-profile, rest-rear, then an actual public Piercing Dawn windup. Copy it into
both private children as `tools/graphics-six/shoulder_capture.gd`; use
`YUGA_SHOULDER_REVIEW=baseline` or `candidate` and
`--mode=groom-stills --output=<fresh-absolute-directory> [--preflight]`.
It requires motion8c377 and finish6eb, accepted-UV baseline and the exact final
candidate pins. Optional hair/fletching/old shoulder helpers must be absent.
It uses the existing actual modifier callback and inverse binds, checking exact
selected material/bone counts with 24px projection margins. The source predicate
matches exactly the removed or new rows in `capture-selection-proof.json`.
The helper is authored but **not parsed or executed yet**. Both branches must use
one identical frozen runtime, engine, controls and seeded-cache policy.

Compare all 164 final poses, camera/light, action age, morphs, secondary state,
LOD and clocks exactly. Only declared source/branch fields, shoulder projection
bounds/counts, framebuffer hashes and wall/cleanup measurements may differ.
Reject changed event outcomes or relaxed framing. W1 must retain its actual import,
preflight and pair receipts before any art disposition.

The main visual questions are whether the compact outer-deltoid silhouette is
readable, whether removal exposes an awkward inner-shoulder opening or floating
attachment, and whether the layered metal stays convincing through the cast.
No shoulder picture exists yet; there is no claim of improved game graphics or
Deadlock parity. Mid/far images, transition shimmer and title-scale visibility
remain beyond the first near-LOD four-view pair.

Before eventual combined shipping, remove proven unreachable buffer/accessor
storage in a separate reviewed compaction task. Preserve these proof inputs and
exact active arrays, rig/materials/clips; require fresh import and pixel controls
after hashes change. Parent explicitly deferred implementation. The current
release excludes this shoulder and the unaccepted hair.
