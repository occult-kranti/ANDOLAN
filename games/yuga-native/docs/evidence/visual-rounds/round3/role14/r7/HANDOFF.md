# R3-14 R7 provenance and bundled-font qualification

The reviewable R7 + cloth proposal is sealed at
`/workspace/scratch/visual-round3/role-14/r7-review-r2`. Its promotion manifest is
`394ffea43f8c7f79ce911e7d0c3c8b9428c4ffa571c0aeca6bdf1e4e32478ff5`;
the proposed schema4 NOTICE is
`5026675c7af8b83412eb375b9883ffe52efd883e20c7fd9594bdf3fdd9c8f5d8`.
It validates 66 exact sources and lists 24 promotion files. No canonical assets,
NOTICE or release package were promoted. The accepted R2 schema3 NOTICE and
43-source contract still validate. Historical R6 proposal/support/evidence stay
unchanged at `review-r3`, `support-r3` and the parent evidence directory.

## Exact boundary

The finite schema4 gate pins the corrected R2 parents, exact R7 near/mid/far
outputs, original groom generator/guide metadata, current source manifest and
actual saved/reopened editable. It independently compares the entire original
BIN prefix and original JSON after restoring only the permitted hair primitive
reference and appended view/accessor data. Original nonhair arrays, images,
materials, rig, animation, face morphs, eyebrow and topknot stay exact.

R7 outputs are `8b6cf0f4…84d5c`, `d95a061e…5beed`, `ee2e3527…6317c`.
The full pins are in the proposal. Role06's Blender4.3.2 editable is
`940c8208d8f5ee8c2e8dd9e4bea2d9893450026189f1a4eb24cd0b1874378f25`;
inspection is `9af85ce316cc3a270ef62bef98ad4b203218c6f29a5a27c81dc6d4af8d28e031`.
Actual save/reopen retains 16 guide curves, one164-bone rig, nine actions,
17 packed images and four face morphs plus Basis. It is an editable import,
not a recovered historical modeling stack or a validated Blender roundtrip.

There is **no GLB retag, re-export or other metadata change from the rendered
candidate**. The runtime proposal contains three exact R7 GLBs, the authored
woven scalar PNG and its sole import change, `mipmaps/generate=false -> true`.
The new NOTICE, source companions and package checks record their ancestry.
The already committed secondary lifecycle correction is a separate explicit
`runtimeSources` pin. The existing surface-finish script and shader remain
unchanged. The optional frame-correction shader is excluded.

Role06's `../../role06/proposal-reconciliation.json` confirms all five runtime
files and three preserved dependencies match the rendered candidate exactly,
and all four actual imported resources/descriptors remain bound to the earlier
serialized import receipt. No new import is needed. Role06 reports all334
originals/167 pairs complete; art and motion disposition belongs to root and
independent reviewers. This role reviewed source identity, not new pixels.

## Actual checks

- `package-cases-parser-r3.json`: **288/288**, covering the prior181 schema1/2/3 cases,
  58 fixed R7/cloth adversaries and49 font cases. Changed ancestry, stale LODs,
  dependencies, external symlinks, direct nonhair BIN/JSON mutations, undeclared
  shader and altered cloth imports reject.
- `pck-security-parser-r3.json`: **75/75** existing directory/integrity/security cases.
- The actual isolated font-load proof decodes all three `FontFile.data` values
  to their pinned raw TTF hashes. Repeated proofs match. Substituting the real
  NotoSerif compiled resource at NotoSans's path rejects even though every raw
  TTF and license remains correct; the observed failure is retained.
- `font-cold-export-parser-r3.json`: a fresh tiny project imported only the three raw
  fonts and exported a real font-only PCK. The bindings stayed stable across
  that export. Its six genuine font/remap payloads pass the production PCK
  inspector in the existing structural native fixture; swapping the actual
  exported remap rejects. This is not a full YUGA export or runtime test.
- `git diff --check` passes for owned support changes. Existing R7 geometry,
  collision, repeated reconstruction and zero-error Khronos reports remain
  under `../../role08/nape-r7/`; they are not replaced by package identity tests.

Font qualification pins three original TTF files and all five accompanying
license/source-notice files. It verifies the actual imported font's embedded
TTF bytes, then requires the same export's payload hash/length and correct
runtime remap in each PCK. Packed descriptors are checked after Godot trims
them. License bytes must survive copying into the package's NOTICE directory.
Cache resource hashes are measured per export, never permanent source pins.
Cold CI therefore may produce different cache bytes while preserving the same
raw-font and same-export identity contract. Full native exports must run from
an imported, frozen tree, as the existing exporter already requires.

The first isolated font-only export attempt is retained under
`/workspace/scratch/visual-round3/role-14/font-export-r1`: its minimal empty
preset-options section logged errors despite creating a pack. The successful
r2 probe supplies the required architecture option and requires clean logs.

## Stored cost and remaining limits

| LOD | Active whole-asset triangles, R2 → R7 | Active hair triangles | R7 GLB bytes | Retained dead hair view bytes |
| --- | ---: | ---: | ---: | ---: |
| Near | 408,316 → 367,864 | 29,448 | 36,049,948 | 3,854,580 |
| Mid | 216,544 → 202,034 | 13,450 | 25,847,144 | 1,769,652 |
| Far | 140,966 → 136,228 | 6,444 | 20,901,820 | 753,348 |

The exact retained prefixes add auditability but the three GLBs grow by
2,919,604 bytes overall. Fewer active triangles do not establish lower file
size, memory use or GPU time. R7 costs are unchanged from R6. The cloth PNG is
5,823 bytes; imported texture memory and whole-release compressed size are
separate measurements.

The bounded R7 nape correction clears the measured rest collar region. The
independent exact triangle replay still finds `measured_step_recoil` collar/
neck contacts and intersections in19/24 opposing secondary stress fixtures.
Root and R3-15 viewed the diagnostic originals and authorized full comparison;
that does not erase the retained contact finding or authorize promotion. The
retained topknot degeneracies and shader frame limitation also remain explicit.

## Reconstruction and next owner

```sh
taskset -c 2,3 env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  python tools/visual-rounds/integration/prepare_groom_review.py \
  --candidate /workspace/scratch/visual-round3/role-08/groom-r7 \
  --output /workspace/scratch/visual-round3/role-14/r7-review-fresh
python tests/rama_package_cases.py --groom-review /workspace/scratch/visual-round3/role-14/r7-review-fresh \
  --font-engine /opt/godot/4.6.3/Godot_v4.6.3-stable_linux.x86_64 \
  --font-evidence /workspace/scratch/visual-round3/role-14/font-tests-fresh \
  --report /workspace/scratch/visual-round3/role-14/package-fresh.json
python docs/evidence/visual-rounds/round3/role14/r7/font_export_probe.py --project . \
  --output /workspace/scratch/visual-round3/role-14/font-export-fresh
```

The exact support files are retained in
`/workspace/scratch/visual-round3/role-14/r7-support-r3`. The accepted asset
proposal remains immutable at r7-review-r2; `support-overlay.json` records only
the independently requested parser correction and exact support hashes. The
previous r2 support and282-check evidence remain historical. Groom reconstruction
commands are in `art/visual-rounds/groom/README.md`. The actual saved Blender
artifact is fixed by hash; a new Blender save is not claimed byte-deterministic.
Root owns art/motion disposition, eventual exact-file promotion and R4-14
integration. Role06 owns imports/renders. No shared ledger or commit was made.

Independent review found that the first font descriptor parser could read its
target from the wrong ConfigFile section. The correction requires explicit
case-sensitive `[remap]` keys and rejects duplicate sections/keys and defaults.
Six new adversaries plus the repeated actual cold export pass. No raw font,
license, R7 asset, cloth or proposed NOTICE bytes changed.

The assembly command is a pre-promotion operation and intentionally requires
the exact R2 parent NOTICE. After root promotion, validate the preserved review
tree instead; do not relabel a new stage or loosen its parent hash to rerun it.

After this source seal, root reported bounded art acceptance from R3-11 and
R3-15 and took ownership of exact24-file promotion. The support-overlay review
remains separate; this assignment did not promote canonical assets or NOTICE.
The R4-01 skin/seam/contact-subset report is separately recorded under
`../../../round4/role01/`; source equivalence does not transfer imported execution.

Final independent support review passed31/31 and retained the original
misplaced-section failure. `independent-support-review.json` is the unchanged
reviewer receipt (SHA256 `d530ae58debcc1f1fa11c8a89bbf392a27a8bbb4931d6769b3f2fe62397cd26b`).
`support-acceptance.json` accepts the frozen support overlay without rewriting
it or the asset proposal. Root may now integrate the listed support hashes.
All288 package,75 PCK-security and31 independent checks pass; the real cold
font-only export also passes. No full native release export is claimed.
