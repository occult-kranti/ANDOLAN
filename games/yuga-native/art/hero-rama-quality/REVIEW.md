# Rama quality candidate Q3

This is an incremental original art candidate against the left-hand Rama in `games/yuga/art/references/rama-hanuman-sita.png`. It preserves the accepted R7 hero under `art/hero-rama/`; runtime promotion belongs to integration. It does not meet the Deadlock or generated-reference quality target.

The pass replaces the broad remeshed hair sculpture with 68 sealed, individually tapered, grooved locks: swept crown, temple strands, varied back curls and a compact tied knot. The costume gains original lotus/vine gold brocade, controlled surface roughness, and asymmetric compression folds in the ivory front drape and fitted chest sash. These folds move outward by at most 9.58 mm and 3.07 mm respectively; sewn boundaries stay fixed. The face has a smooth, bounded bridge/jaw/cheek sculpt of at most 2.80 mm. Original eye sockets, separate lid rims, seated globes, hands, feet, bow and string geometry are retained.

The asset retains all 164 bone names, rest transforms and parent relationships, plus the exact nine original baseline animation curves. The current game's 23-clip motion library is separate; same-rig compatibility is an input to integration, not a claim that 23 new clips are embedded in this GLB.

## Three bounded rounds

1. Actual reference, R6 face/front and the packaged native title were inspected. The measured gaps were broad wax-like hair masses, a neutral face, weak eye/lip definition, regular drapery and sparse ornament.
2. Q1 replaced the hair and authored semantic movement masks. Actual front/face renders exposed flat root caps and incorrect side-face winding; Q1 was rejected. Its exact generator, metadata and two images remain in `history/q1-rejected/`, and the full source remains in scratch. Q2 corrected winding, tucked/tapered roots and strengthened fabric contrast.
3. Same-camera R7 baseline and Q2 views were inspected. Q3 reduces broad hair reflection, varies curl lengths and adds bounded cloth compression folds. Four final actual source-matched studio views and independent runtime review are required before any bounded promotion. The overall production-art gate remains open.

## Secondary motion contract

Every exported primitive has `COLOR_0`: RGB is exactly white, alpha is a semantic weight, and all materials remain opaque. This avoids tinting ordinary PBR surfaces. Hair clumps are zero at the root and smoothly approach one toward tips; scalp and eyebrows stay zero. Back-trailing mantle cloth and corresponding borders/trim share one continuous spatial field. Fitted chest/waist panels, skin, eyes, gemstones and the bow remain anchored.

Four material names can carry dynamic weights: `Swept black hair`, `Cobalt handwoven silk`, `Cobalt lotus brocade` and `Worked warm gold`. The brocade border must use exactly the same displacement as the mantle; moving only the blue fabric would separate the sewn edge. The secondary motion owner implements the runtime response. This art candidate alone does not animate these masks.

## Build and evidence

From the repository root:

```sh
blender -b -t 2 --python games/yuga-native/art/hero-rama-quality/build_quality.py -- --output /new/absolute/output --render --views face,front,side,back
python3 games/yuga-native/art/hero-rama/validate_hero.py /new/absolute/output/rama-hero-quality.glb
python3 games/yuga-native/art/hero-rama-quality/validate_quality.py /new/absolute/output/rama-hero-quality.glb
blender -b -t 2 --python games/yuga-native/art/hero-rama/verify_editable.py -- /new/absolute/output/rama-hero-quality.blend /new/absolute/output/editable-validation.json
blender -b -t 2 --python games/yuga-native/art/hero-rama-quality/verify_quality_editable.py -- /new/absolute/output/rama-hero-quality.blend /new/absolute/output/quality-editable-validation.json
```

The retained comparison uses CPU Cycles, 24 samples, no denoiser, 640 × 800, the same three area lights and AgX transform. `front` is the same slight three-quarter view used in the earlier R6 review, rather than a perfectly frontal orthographic angle. `face`, `side` and `back` use pinned cameras in the generator. These are actual meshes and PBR materials, not an edited concept image. Blender reports an unavailable optional Draco library; compression is not requested.

The input anatomy is the project's CC0 MakeHuman-derived anatomy. Hair, costume, ornament, texture algorithms and inherited animation sources are original project work. No commercial-game mesh, texture or binary was imported. The existing notices under `art/hero-rama/` and runtime notices remain authoritative for inherited inputs.

## Executed final checks

Q3 GLB SHA-256: `4a713daad6d94401e0d7fead0283769c05814f622f08f4cb19320c1d29820cc9`. Editable source: `a5c74af28b134e3d3e6bad3c9bc415b05a1a7e18c6c1f441df2d581d78e973a2`. Exact generator: `96ace6c9036bc237c9f38d78c20c9a119036470eaeecd22b3a89e6c5f07c850d`.

- The inherited seven-part GLB validator passed: finite geometry, skin normalization, required joints/nodes, retained baseline clips, tangent frames and embedded image payloads.
- Five independent quality/contact checks passed, including exact unique bow position/normal/UV/skin records within 1e-6 and the authored opaque semantic-mask contract.
- Reopened source verification preserved every bone rest matrix/parent and baseline animation F-curve, and all 27 sampled posed bounds were finite and bounded.
- Six additional source checks passed: original non-hair topology/UV/skin/material assignments are exact; unchanged parts retain exact coordinates; only the documented face and two cloth surfaces move. 32,483 of 32,640 nondegenerate hair side faces have outward winding (99.52%).

The candidate has 410,940 triangles and 236,284 exported vertices, compared with accepted R7's 450,084 triangles and 257,139 vertices. Those counts describe source cost, not a frame-rate result. All eight baseline/candidate images were actually opened; the four candidate views belong to the final Q3 source. Independent QA and the subsequent facial/runtime passes are separate acceptance steps.

## Remaining visible defects

The face still lacks authored expression and blink behavior. Hair remains stylized solid clumps, with a broad crown response and simpler scalp transitions than the reference. Fabrics still lack the reference's layered tension, tailored construction and physical folds. Ornament silhouettes and skin response need further art direction. No card/strand hair, authored physical cloth simulation, production facial rig, LOD acceptance, twelve-player scene cost or physical-GPU result is established here. The independent face, secondary-motion and LOD candidates require their own reviews.
