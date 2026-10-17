# R2-12 independent face/background/context review

**Disposition: BASELINE_CONTEXT_LIMITED.** Existing geometry and frozen day/night controls pass the checks below. Candidate face/material/lighting acceptance remains pending. This review is source-bound to native YUGA commit `0437ea91edf6989ff78c1eeadb3661f4825b60f2`; no runtime source or asset was edited, imported, rendered, promoted or committed by this reviewer.

I inspected seven original full-size PNGs using `view_image`: courtyard three-quarter-left day/night, courtyard ordinary rear gameplay day/night, Confluence stone three-quarter-left day/night, and the separate courtyard PCSS-off daylight diagnostic. Exact paths, SHA-256 hashes, camera/pose data, sample boxes and calculations are in [context-review.json](context-review.json). Images remain owned by R2-06.

## Findings from the actual originals

- **Baseline courtyard close:** eyes, nose and outer jaw remain readable against the pale architecture/sky. Black hair is strongly separated from those backgrounds. A broad dark patch suppresses cheek/nose form, and the lit temple, ear boundary and neck show stippled shadows. The night frame retains the facial outline but further reduces cheek/hair detail. No foreground pillar, plant or lamp visibly crosses the facial features in these inspected angles.
- **Stone close:** the fixture supplies existing sandstone architecture with dark recessed panels and brass vertical strips. It is correctly a mixed stone context; it is not a uniform pale backdrop. The face outline remains visible and the bright stone perimeter helps the hair silhouette, but the black hair reads as a heavy mass and facial shading is comparatively flat. The forehead and cheek are darker than in the courtyard; these are different world lighting systems and pose pins, so cross-context pixels are not a controlled lighting ablation.
- **Courtyard gameplay:** costume, limbs, bow and feet remain distinguishable against the floor in both phases. The feet appear attached to the floor, and the visible shadow extends rightward without an obvious detached start. These are paused rear views with the HUD enabled. They do not show frontal facial detail, establish live HUD behavior, or prove contact during motion.
- **PCSS-off diagnostic:** the actual daylight original visibly reduces ear/neck stippling, while structural/ground shadow edges become harder. Camera and pose pin match the baseline. Its directional angular distance is explicitly zero; the baseline source uses 0.7. This is a lighting-policy change, so its pixels cannot alone prove a face-geometry improvement. The diagnostic's inherited overlay status still says unrendered; the actual complete capture is the evidence that it has now rendered. Final policy status belongs to R2-03/R2-06/integration.

## Independently measured controls and context constraints

`python games/yuga-native/docs/evidence/visual-rounds/round2/role12/audit_context.py` completed successfully. It reads the current files, the role02 fixture and actual role06 capture metadata; it does not invoke Godot or another worker's geometry verifier.

- All **16** fixture scene/script/asset SHA-256 pins match current files and both frozen baseline capture source maps. This includes courtyard and Confluence scenes/scripts, architecture/nature/courtyard GLBs, world manifest, existing lighting and environment-detail sources. There is no source evidence of a new environment mesh, collider, material or light in this baseline. This does not certify an unseen candidate overlay.
- All **3** inspected day/night pairs preserve camera matrix/FOV/near/far, pose pin, player transform/yaw, LOD level, facial weights, viewport and paused/UI state. Shadows remain enabled, depth/normal biases remain `.2/.35`, exposure remains `1.0`, and portrait fill remains off. Expected day/night sun color, rotation and energy differ. Baseline courtyard metadata predates the explicit angular-distance field; its pinned source supplies that value.
- Independently recomputed all three fixture camera offsets from visual yaw and the supplied target. Both close and four-times-distance frontal review positions match the fixture exactly, with maximum error **0.0 m**. Actual stone captures use the permitted head-derived camera variant, and day/night actual matrices match exactly. Do not compare the literal fixture target with a head-derived frame as if their cameras were identical.
- Independently recomputed horizontal distance to all **16** Confluence authority/deck boxes, then subtracted the stated **0.65 m** hero radius. Minimum clearance is **4.35 m** at light stone and **7.894003745 m** at foliage. This verifies the two static footprint placements against those boxes. It does not repeat role02's triangle-ray analysis, validate a runtime capsule sweep, or prove every foliage pixel lies behind the face.

Fixed manually chosen pixel samples use inverse-sRGB transfer and linear Rec709 luminance. They describe inspected patches, not automated segmentation or pass thresholds:

| Patch | Courtyard day | Courtyard night | Stone day | Stone night |
| --- | ---: | ---: | ---: | ---: |
| Cheek median | 0.03607 | 0.02346 | 0.02101 | 0.01846 |
| Hair median | 0.00241 | 0.00065 | 0.00219 | 0.00215 |
| Right-background median | 0.05152 | 0.04172 | 0.14059 | 0.13494 |

The paired gameplay rear-costume sample is 0.03273 day / 0.01487 night, while its floor sample is 0.52300 / 0.29505. These measurements support the observed value separation while leaving local edge cases and expression readability to direct review.

## Exact inspected image identities

Paths below are relative to `role06/` under this round:

| Original | SHA-256 |
| --- | --- |
| `baseline/courtyard/courtyard-three-quarter-left-day.png` | `1cabca9ec2dea9762eac7f28384a48f0519a880414ffa1a683e4eb388a5e2438` |
| `baseline/courtyard/courtyard-three-quarter-left-night.png` | `ec5a1dc391573142a45ec5e1f8bd69a3cffdd828aa91930703613fc9ec9f2fb9` |
| `baseline/courtyard/courtyard-gameplay-day.png` | `c1265bff2297a9ae14e49941608ed2d083c67aadee97822ac73acb655200bd2b` |
| `baseline/courtyard/courtyard-gameplay-night.png` | `48b29864f4d0217b0493f85089407b9b59345d2241c352c311a30b6ef38b9176` |
| `baseline/stone/stone-three-quarter-left-day.png` | `5d1397cef69a97ad1ba830a3d37ef31e434daa4eb918a08f4c86f92f4cb3fc10` |
| `baseline/stone/stone-three-quarter-left-night.png` | `54d1b23cb11d7bcfaa8dd0c0f52b5eff60c092b802e5bd8fcdf731983eb505c3` |
| `diagnostics/directional-pcss-off/courtyard-three-quarter-left-day.png` | `a596d3fe71964e7b6f43dec9c0fcffb98f19d97bd81e53191253a7cc07459e53` |

## Remaining acceptance gates and next owners

R2-06 reported that final candidate forms were staged and candidate capture was queued; no final candidate original was available for this bounded review. R2-06/integration must attach source-bound candidate originals, compare exact camera/pose controls, and declare every lighting/AA difference. A lighting change requires courtyard and Confluence day/night gameplay/contact evidence plus moving camera/caster cascade review; one portrait cannot approve it.

Foliage day/night originals were still queued. Require foliage around the face silhouette, not merely a center-ray leaf hit, and reject foreground branches/near clipping. The optional indigo/gold fixture and frontal gameplay-scale context views remain uncaptured in the initial 14-view subset. Ordinary courtyard rear gameplay frames do not close those gates. Existing center-ray and clearance evidence may support these fixtures but cannot substitute for those pixels. No physical-GPU performance, continuous animation, full-game or commercial-art completion claim is made.

Changed files are restricted to `role12/audit_context.py`, `role12/context-review.json` and this report. Next owner: R2-06 for pending originals; R2-03 for explicit shadow-policy disposition; R2-14/integration for final acceptance against declared scope.
