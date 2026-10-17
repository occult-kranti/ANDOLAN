# Independent image review: R1 cloth candidate

**LIMITED for optional material exploration; REJECT default promotion.** The candidate reduces broad glossy sash highlights, but replaces authored dark indigo/gold ornament with brighter blue technical fabric. It does not establish an overall art improvement.

Role12 individually viewed all eight original 1280 × 960 full frames using `view_image` at original detail, plus the three 1024 × 1024 derived maps. No raw image was edited; no generated image, crop or contact sheet supports this finding. The raw images and frozen source snapshots are in [render/r1](../render/r1/). [review-r1.json](review-r1.json) records full findings and image paths; [input-verification.json](input-verification.json) records independent checks.

## Pixel findings

- **Courtyard day/night:** sash region x578–752, y231–444 loses broad white specular streaks, but reads brighter and flatter. At (658,331), day RGB changes 24/31/80 → 57/82/163 and night 16/25/75 → 49/74/158. These are raw display-color samples, not isolated roughness measurements.
- **Front blue drape:** x676–802, y471–724 loses most gold lotus-like motifs and shows low-contrast repeated blue cells. Gold edge trim and sparse separate accents remain. The recorded old target albedo is `rama-hero_q1-cobalt-ornamental-weave-basecolor.png`; the visual ornament loss therefore occurs on the eligible handwoven surface even though separate brocade/gold surfaces remain excluded.
- **Confluence day/night:** cloth region x601–752, y374–605 retains brighter blue and reduced highlights. Fine weave and normal relief are too small to judge at this camera. The near repeated-cell pattern does not establish tactile fabric richness at mid distance.
- **Seams/geometry:** no new gross silhouette split or conspicuous bright UV seam is visible from this frozen three-quarter angle. Angular hems, overlap/notch shapes and stiff drape remain. Unseen surfaces, moving seams, shimmer and deformation remain untested.

## Independent capture checks

`python3 games/yuga-native/docs/evidence/open-art-wave/visual-review/verify_review_inputs.py` exited 0. Direct checks verified all eight raw hashes/dimensions; four actual pairs; 495 runtime source files; 492 canonical/fixture source files; 260 text snapshots; 12 imported-resource records; equal pair cameras/lights; and exact full restoration. Full baseline/candidate JSON states independently match after removing only the 15 named uniforms on exact `Cobalt handwoven silk · bounded secondary` materials. Exactly three material instances change; bone poses, mesh/skin/morph identities, shader identities, controller states, secondary offset and nonowned materials remain equal. Recorded state hashes match; Godot's JSON hash serialization was not independently reproduced.

The renderer is Godot 4.6.3 Forward+ on X11, **llvmpipe (LLVM 19.1.7, 256 bits)**. The camera placement targets are 780 px near/350 px mid; projected rest AABB heights are 986.35/386.26 px and are not measured silhouette heights. Above an 8-level per-channel RGB threshold, pair-difference bounds stay around the hero: near [505,220,884,852), mid [582,359,752,643). Smaller night background differences remain consistent with temporal renderer history; pixel differences are not a semantic cloth mask. No uncontrolled background TIME shader was reported.

The renderer owner confirmed completion and exact archive copies. Terminal transport disconnected; the owner's runner receipt is written after subprocess return 0 and schema validation, and no process remained on reconnect. The reviewer did not personally observe terminal exit. Receipt hashes and source/raw pins are independently verified.

Source commit: `658804fd6e454c6d584ac3245601506b22075c0b` plus the pinned uncommitted R1 fixture. Candidate SHA-256: `856809ad52a04360f63d260ea5af1d217b6fb34323ab02fcfb70c754cd6af029`. Source: Microsoft SheenCloth selected CC0 maps from KhronosGroup/glTF-Sample-Assets revision `edc7c9e67c639d230715049ee31f9a96a6babbbe`; this is technical fabric, not a historical silk scan. Exact receipts: material capture `ebec00ae7bdf446e48a61284163fdc22e3073ca162d67be8905fa95860b89b12`, runner `643805e1bef26a42acaf05815432c8f9fe0d6670a70e5d54e00019b02449fb37`, source identity `d547e5df13a0084bc080d48920850b26b59ad669947cf0d19965a9e8c19ec2e8`.

| Viewed original frame | SHA-256 |
| --- | --- |
| courtyard-day-baseline.png | 02dfb2de4529faef56e2adf64974899298b4260da312af5a8fbeea4c25349e09 |
| courtyard-day-candidate.png | 2f1368322d6f6b044fcf4a59482b6f807fd194449775ba0201b5983252b4ab11 |
| courtyard-night-baseline.png | b04daf47cca244656f99a3a845e8e849af816d5179c5dc8d973fe250cafcfc17 |
| courtyard-night-candidate.png | b86336163c1f97ce0caef81c1a4b56e7b2b0de9f00c507d48ef54b4a875e331a |
| confluence-day-baseline.png | 63be8660337eabb7eb44326244492be3ae26cba0813d9e89836f4cc0cd911a19 |
| confluence-day-candidate.png | 2b1060e803cbcf24b47a91524f7a7f27be1d89233bf9286766782dd2d06cdf7a |
| confluence-night-baseline.png | 7b581729b418660b370f02572db73f52c3051307a64f6606232c3e85fbfc99e2 |
| confluence-night-candidate.png | 489e71877d96d12d0c6c94e8da714685b0821d64fe9ded00acce71d8e591ffcb |

Preserve the original authored albedo/ornament and test candidate roughness/normal in a separately pinned R2. Keep R1 evidence intact. The current skin, hair, face, anatomy and drape limitations remain; this review supplies no continuous-motion, human-feel, hardware-performance, finished-art, commercial-game-parity, default-adoption or release acceptance.
