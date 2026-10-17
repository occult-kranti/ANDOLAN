# Independent R2 image review

**ACCEPT the bounded optional surface profile** `preserve-original-albedo_cc0-roughness-normal-v1` for this fixed-view experiment. Original dark indigo and gold motifs remain, while excessive broad highlights on the front blue drape are reduced. Overall hero art remains LIMITED; default promotion requires a separate broader packet. The [R1 review](../REVIEW.md) is unchanged.

All eight original R2 1280 × 960 full frames were individually viewed with `view_image` at original detail. Each baseline was compared with its matching R2 candidate. No cross-round pose assumptions, image generation, raw editing, diagnostic crop, contact sheet or Godot run was used by this reviewer. [Raw originals and frozen sources](../../render/r2/), [machine-readable review](review.json), [independent verification](input-verification.json).

## Observed improvement and limits

- Near courtyard day/night, the original dark blue/gold ornament remains on the sash and front drape. The broad white satin-like stripe at x715–790, y470–680 is substantially softer; folds and gold motifs remain readable. At front-drape pixel (729,570), day RGB changes 103/110/140 → 49/57/103 and night 92/99/131 → 41/49/96. This supports a restrained combined roughness/normal response with unchanged albedo; it does not isolate the cause between maps.
- At Confluence mid distance, the original color and motif identity remain. The material change is subtle, especially at night; fine technical-fabric normal relief cannot be judged reliably at the 350 px placement target. No new conspicuous seam, silhouette split or mismatched day/night material is visible from this three-quarter angle.
- Angular hems, panel overlaps/notches, stiff drape, solid-looking hair, glossy skin and restrained expression remain. Unseen UV regions, moving seams, continuous deformation/contact and temporal shimmer remain untested.

## Independent contract verification

`python3 games/yuga-native/docs/evidence/open-art-wave/visual-review/r2/verify_review_inputs.py` exited 0. Independent checks cover eight raw hashes/dimensions and exact archive copies, four matched R2 pair cameras/lights, 495 runtime sources, 492 canonical/fixture sources, 260 text snapshots and 12 imports. Full baseline/candidate state equality holds after removing only the 12 exact eligible non-albedo uniforms on the exact secondary-owned handwoven material. Exactly three material instances change per pair; seven field values actually differ. Mesh/skin/morph/bone/controller/shader identity, secondary offset and nonowned materials remain equal; full restoration is exact.

All three original fields `base_color`, `base_texture`, `use_base_texture` remain identical in baseline/candidate/restored across 12 pair/material observations. Original texture `rama-hero_q1-cobalt-ornamental-weave-basecolor.png` remains SHA-256 `f1369ca6a4b4ca838b54305ffddd2dddef7b104c5dadc9c6fd0be5ea9a6a459c`. Recorded state hashes match; Godot JSON hash serialization was not independently recomputed.

Godot 4.6.3 Forward+ on X11 uses **llvmpipe (LLVM 19.1.7, 256 bits)**. Near/mid camera placement targets are 780/350 px; projected rest AABB heights are 986.35/386.26 px, not visible-silhouette measurements. No uncontrolled background TIME shader was reported. Source bytes match before/after; the renderer owner directly observed exit 0 and archived a zero-exit receipt with no warnings. The reviewer independently verified the artifact pins.

Candidate material SHA-256 remains `856809ad52a04360f63d260ea5af1d217b6fb34323ab02fcfb70c754cd6af029`; binder `8a14fbeb0422f86d4ecc98934991e4592ce39ca674cfbe204697819942bb8eec`. Source commit is `658804fd6e454c6d584ac3245601506b22075c0b` plus pinned uncommitted R2 fixture sources. Microsoft SheenCloth CC0 technical-fabric roughness/normal maps derive from KhronosGroup/glTF-Sample-Assets revision `edc7c9e67c639d230715049ee31f9a96a6babbbe`; original hero albedo is retained. This does not establish historical silk authenticity or KHR sheen equivalence.

| Viewed original frame | SHA-256 |
| --- | --- |
| courtyard-day-baseline.png | 02dfb2de4529faef56e2adf64974899298b4260da312af5a8fbeea4c25349e09 |
| courtyard-day-candidate.png | 7d774b9a268f3ea34cfaca1f2a0cf330fcfccd7403fcfe37f4e25401f9f910be |
| courtyard-night-baseline.png | b04daf47cca244656f99a3a845e8e849af816d5179c5dc8d973fe250cafcfc17 |
| courtyard-night-candidate.png | a5e0294ffbcd1e7cd725832ff197d3c9e4348226555ea5f5ab1a6e8e98b2f8dd |
| confluence-day-baseline.png | 63be8660337eabb7eb44326244492be3ae26cba0813d9e89836f4cc0cd911a19 |
| confluence-day-candidate.png | 9c72864b5d746bb27cc11a941211875a24b74bfd58bc6e1e81272d5a8a8bf74a |
| confluence-night-baseline.png | 7b581729b418660b370f02572db73f52c3051307a64f6606232c3e85fbfc99e2 |
| confluence-night-candidate.png | 3a11d3bb36e98a578d95991bc6ec4601a8151151734a0e5bfbb015ddefcb1dee |

Acceptance is limited to this optional surface profile and fixed-view excessive-gloss correction. There is no default adoption, finished-art, commercial-game parity, human-feel, hardware-performance or release acceptance.
