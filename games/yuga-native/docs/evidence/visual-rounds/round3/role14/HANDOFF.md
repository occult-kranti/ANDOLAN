# R3-14 — finite groom and cloth provenance proposal

The external review tree is `/workspace/scratch/visual-round3/role-14/review-r3`.
Its source identity validates, but promotion remains blocked on independent
nape/collar/neck clearance findings and actual art review. No canonical asset,
NOTICE, import, render, PCK or release was changed by this assignment.

The current source commit is `6046171a5ae53e1b1a9777c0ee0011e2ebf1dc95`.
The accepted R2 NOTICE remains schema3, SHA256
`754f81cef0da3d3fb03a21e083e0e3ab7a8b6feed7e0b95fcd47b88a99c33f58`.
Its 43 source records still validate. The proposed schema4 NOTICE is
`87a78611a1a47265c266152039275588a36029bffa914e47398da48e0f4e2ebf`;
the promotion manifest is
`914e40e74b051b8f070336cc9bdfd2d6873d858bd82b6633a7cb9211990399d3`.

## Changes and boundary

`tools/package-native.py` admits exactly one additional `principal-groom-v1`
stage after the frozen R7/Q3/face/R2-form stages. The complete schema3 parent
notice is retained unchanged. The groom input, all three output GLBs, original
generator, guide/source manifests, saved editable and reopened inspection are
fixed SHA256 pins. The gate independently compares the entire original BIN
prefix and all original JSON after restoring only the hair primitive reference,
appended accessor/view suffixes and buffer length. Original nonhair arrays,
images, material definitions, skins, joints, clips and morphs remain exact.

The groom retains original eyebrow/topknot records and replaces mesh 2 primitive
0. Its newly authored scalp/crown/temple vertices have zero secondary alpha;
lower nape alpha is bounded at 0.78. Existing single-head binding and one runtime
secondary owner remain. This package stage preserves the existing shader bytes;
it does not admit the optional normal/tangent correction shader.

Cloth has a separate `clothStage` receipt. Only the existing runtime woven
roughness PNG and its `mipmaps/generate=true` import setting change. It pins the
original procedural authoring, RED linear scalar profile and original input
texture/import. The cloth source manifest honestly records the earlier face
GLBs inspected during R3-01; the new receipt links runtime application to the
final accepted R2 parent. It does not invent cloth GLB authoring ancestry.

`prepare_groom_review.py` creates a fresh external proposal, validates all 65
required sources, and enumerates 24 exact promotion files. Existing finish and
shader scripts are recorded as preserved dependencies and excluded from that
copy list. Package support is listed separately with its exact hashes. The
helper never promotes its output. A source identity pass provides no art approval.

## Actual evidence

- `package-cases.json`: 237/237 pass: all 181 inherited schema1/2/3 checks and
  56 additional real-source schema4 checks. These challenge altered dependencies,
  ancestry, self-rehashed substitutions, paths/symlinks, stale LODs, edited
  runtime shaders, cloth import changes and direct nonhair BIN/JSON mutations.
- `editable-inspection.json`: role06 ran Blender 4.3.2 import/save/reopen. The
  native editable is `ad3d599935bb817c43a763171412c5c638b5eab58d2aa4801c1dad3e5d40b508`.
  One 164-bone rig, nine actions, all 17 packed images, four face morphs plus
  Basis, and 16 hidden guide curves survive reopening. It is an editable import
  with guide controls, not a recovered historical modeling stack or a validated
  Blender roundtrip export.
- `cloth-import.json`: role06's actual import passes all 11 recorded checks,
  including ten mip levels, 1024×1024 dimensions, exact linear scalar samples
  and a real ShaderMaterial input. Integrated resource sharing is a separate gate.
- The three GLBs, cloth texture/import, and unchanged finish/shader scripts in
  role06's `capture-candidate-project-r1` are byte-identical to this proposal.
- Groom role08's zero-error Khronos results for all three LODs, 56 source checks
  and byte-identical repeated reconstruction remain under
  `../role08/corrected-r6/`. Three inherited skinned-nonroot-node warnings per
  GLB remain. Original failed r5 bounds evidence was preserved, not overwritten.
- `git diff --check` passes. Role14 did not run imports, renders or exports and
  reviewed no new candidate pixels; those belong to role06 and artist reviewers.

## Active geometry and stored cost

These are whole-GLB indexed triangle totals, not measured GPU timings or memory.
The original hair views remain stored and become unreferenced by live meshes.
Retaining the exact source prefix makes byte preservation auditable while
increasing total GLB file size by 2,919,604 bytes across the three levels.

| Level | Active triangles, before → after | Hair triangles, before → after | New GLB bytes | Dead original hair view bytes |
| --- | ---: | ---: | ---: | ---: |
| Near | 408,316 → 367,864 | 69,900 → 29,448 | 36,049,948 | 3,854,580 |
| Mid | 216,544 → 202,034 | 27,960 → 13,450 | 25,847,144 | 1,769,652 |
| Far | 140,966 → 136,228 | 11,182 → 6,444 | 20,901,820 | 753,348 |

The retained full BIN prefixes are 33,251,736 / 23,989,296 / 19,447,304 bytes;
new appended BIN payloads are 1,726,188 / 796,104 / 392,748 bytes. File sizes also
include JSON. The cloth PNG falls from 142,267 to 5,823 bytes; this says nothing
about imported texture memory, shader cost or compressed PCK size.

## Independent review and remaining blocker

Independent reviewer `/root/r4_05_motion`, acting as R3-09/10/13, completed eight additional package checks with no observed hole. It independently
confirmed all 65 sources/24 promotion files, fixed ancestry/preservation scope,
unchanged shader/finish exclusion, and rejection of matching-byte symlinks
through ancestor directories, traversal and absolute paths. The source/material
audit also passes 24 checks. See `independent-package-review.json`.

The same reviewer has found exact **new-groom** triangle crossings in the
captured rest pose: 24 gold, 14 silk, 14 brocade and 187 neck/chest crossings in
the declared lower-groom/neck region. See role10's `geometry-probe.json` and
`intersection-witnesses.json`. A nape/gold witness lies near
(-0.101, 1.385, -0.035) m. This is source geometry skinned with actual captured
poses, not a pixel assessment. Baseline has 128 gold, 239 silk, 179 brocade and 670 neck crossing pairs in
the same pose. Topology differs, so counts cannot establish improvement or
regression. The candidate witness lies in exposed nape-7 tip vertices
15824–15839 (alpha 0.646–0.696), not a scalp/root anchor; a neck witness belongs
to nape-0. The previous ear/eye/brow/headband checks do not cover or refute these
witnesses. Root reopened role08 for one bounded collider-based correction.

Root must resolve or explicitly dispose these source clearance findings and
review actual front/profile/rear/action/locomotion pixels, cloth appearance and
integrated resource/culling evidence before considering promotion. Exact
retained topknot degeneracies and the existing secondary-frame limitation are
also inherited and remain explicit. This task provides a reviewable identity
package, not authorization to promote it.

## Reproduce and next owner

Run from `games/yuga-native` with a fresh external output directory:

```sh
python tools/visual-rounds/integration/prepare_groom_review.py \
  --candidate /workspace/scratch/visual-round3/role-08/groom-r6 \
  --output /workspace/scratch/visual-round3/role-14/review-next
python tests/rama_package_cases.py \
  --groom-review /workspace/scratch/visual-round3/role-14/review-next \
  --report /workspace/scratch/visual-round3/role-14/package-cases-next.json
```

The GLB generator command and editable reconstruction command remain in
`art/visual-rounds/groom/README.md`; role06 has now executed the latter, as the
new inspection receipt establishes. Rebuilding GLBs in a fresh folder preserves
the exact GLB hashes, while manifest absolute output paths differ; the stage
retains the original r6 manifest bytes. Editable Blender saving is not claimed
byte-deterministic; the actual saved/reopened artifact is fixed separately.

Root owns disposition and eventual exact-file promotion. Role06 owns further
imports and captures. Role08 owns any groom correction; changed groom bytes
require new explicit source pins and a reviewed stage contract. The failed
first assembly (`review-r1`) remains in scratch: it exposed sparse morph
accessors without a direct bufferView, now correctly handled by preservation
accounting. `review-r2` is the earlier successful proposal; `review-r3` excludes
the unchanged runtime shader/finish files from the finite promotion copy list.

The exact validated r6 package support code is preserved at
`/workspace/scratch/visual-round3/role-14/support-r3/` before any reopened groom
iteration. The reviewed proposal and its 237-check receipt remain immutable
historical evidence; a future groom revision requires new explicit pins.

After this seal, root reopened role08 and the current checkout's groom generator
now authors r7. The command above describes the sealed r6 source snapshot; the
current helper intentionally rejects the changed live generator/importer against
its fixed r6 pins. Review or validate the existing complete `review-r3` tree for
r6. Its original authoring sources and the separate `support-r3` snapshot retain
the exact implementation that produced this receipt. Do not loosen the pins or
substitute r7 implicitly. Current r7 reconstruction and limited-clearance evidence
are in `../role08/nape-r7/HANDOFF.md`.
