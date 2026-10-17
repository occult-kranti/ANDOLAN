# Rama hero: actual model review and handoff

17 October 2026. The R7 candidate carries a bounded central-drape skin correction and is awaiting actual continuous animation review. R6 was accepted for initial native integration; its first runtime strafe revealed the weight defect described below. Root independently opened the final front and face PNGs and accepted the corrected garment ordering and filled scalp. This is a materially improved actual model with editable source, skinning and embedded PBR maps; it is not acceptance of generated-reference likeness or commercial-game quality.

Current R7 GLB SHA256: `667f3a215a7b868e3bdbcde880a73d42b68b29af1303db4e1d99b93f73cf2b50`. The R6 rest-geometry source was `e0d25a39ec750f05d8ef6f5251530620f7b1357c523499e86f38abc71fc8cb8d`. It contains 450,084 triangles, 257,139 exported vertices, thirteen materials, eighteen embedded image maps, two mesh nodes and the same 164-joint conventions. The GLB retains nine original baseline clips. The separate motion library and controller own the new gameplay motion; this art report does not claim their tests.

## What the actual images show

`reviews/r6-front.png` and `reviews/r6-face.png` are Cycles renders of the actual exported scene in neutral rest presentation. They show continuous smooth chest, arm and facial anatomy; seated eyes within the native lids; complete surface-seated eyebrows; palette-matched native lips; fuller swept hair masses; layered cobalt and ivory cloth with thickness; shaped gold greaves, solid cuffs, leaf/lotus relief and sapphire settings; a separate recurved bow and feathered shoulder quiver. The gold shoulder rosettes, garment edges, jewelry and bow scrolls are geometry. Fine textile/skin/hair surface variation is carried by deterministic PBR maps.

The final front has no visible ivory peaks piercing the blue side wrap or blue slits piercing the ivory front sheet. The final face has no exposed orange scalp gap or isolated dark remesh fragments above the diadem. These specific defects were directly visible in rejected renders and corrected geometrically; they were not hidden by an image edit.

The remaining stylization is visible: broad sculpted hair masses, a fairly stiff cross-body sash, regularly spaced textile folds, simpler goldwork and a neutral face. The generated reference has more nuanced anatomy, expression, strand grouping, fabric tension and ornament density. Rest-pose open fingers are not a gameplay grip test. The bow's ornament and recurve read more clearly in the rear studio view than the frontal rest view; the motion owner must judge its playable carry/draw silhouette.

## Rejected evidence and correction history

- `reviews/rejected-r1-face.png`: raised symmetric crown rolls, embedded eyebrows and misplaced lip overlay. Corrected through surface raycasts, native lip polygon treatment and revised hair masses.
- R2/R3 source and full previews remain in `/workspace/scratch/rama-hero-art/`. They identified the flat secondary ivory chest strip and rigid nape grouping. The strip became a draped gold chain, and the hair acquired varied waves and tapered ends. Shoulder plates gained actual top rosettes and chased scrolls.
- `reviews/rejected-r4-cloth.png`: stronger trouser folds visibly pierced the blue side wrap. Upper-thigh folds were reduced and outer blue clearance increased.
- `reviews/rejected-r5-cloth.png`: the first clearance correction reversed the intersection, putting blue slits through the ivory front. The final sheet has a gradual depth offset below its anchored waist.
- `reviews/rejected-r5-scalp.png`: voxel union swallowed a thin scalp sheet. The final source keeps the fitted anatomical scalp outside the hair-volume union.
- `reviews/r5-rear-before-final-clearance.png` is explicitly the prior rear view, retained for the same backside design. It is not relabelled as a final-runtime rear capture; final continuous/rear review belongs to native integration.

The original failed scalar cast, absent world and unavailable CPU denoiser attempts remain in scratch logs. The final render uses CPU Cycles with 24 samples and no denoiser. Blender reports that its optional Draco compression library is unavailable; compression was not requested, the uncompressed GLB was written successfully and independently parsed. There is no claim that these Blender logs are engine-runtime validation logs.

## Executed checks

The exact final build command is recorded in `rama-hero.provenance.json`. `build.log.txt` records the completed export and actual final front/face renders.

`python3 games/yuga-native/art/hero-rama/validate_hero.py /workspace/scratch/rama-hero-art/r6/rama-hero.glb` passed seven focused checks: 164-joint skins; separate named hero/bow and required contact bones; expected nine clip names; finite geometry/index bounds/unit normals; normalized four-influence weights; tangents for normal-mapped surfaces; and embedded image payloads. Maximum weight-sum error is approximately `1.79e-7`; maximum normal-length error is approximately `1.19e-7`.

`blender -b -t 1 --python games/yuga-native/art/hero-rama/verify_editable.py -- /workspace/scratch/rama-hero-art/r6/rama-hero.blend /workspace/scratch/rama-hero-art/r6/editable-validation.json` passed after reopening the saved source. All 164 bone rest matrices and parents, and every retained baseline animation curve, match the pinned reconstruction exactly. All 27 sampled posed mesh bounds are finite and bounded. The editable source retains 424 separate modeled mesh objects, including the consolidated hair surface, and packed textures.

`validation.json`, `editable-validation.json`, `editable-validation.log.txt` and the provenance pin those results. Finite bounds do not establish intersection-free motion. Structural checks and studio stills do not accept native grip, continuous cloth/leg contact, gameplay legibility, twelve-player rendering cost or physical-GPU performance.

## Next owner

Integration owns `assets/heroes/rama-hero.glb`, runtime notices, import settings, the player model path and gameplay acceptance. Motion owns the continuous carry/draw/release test and new joint contacts. Combat owns actual ability captures with the imported model. Art will respond to concrete deformation findings against this frozen source; no further geometry change is implied by this handoff.

## R7: actual strafe exposed a skinning seam

The imported R6 model's actual continuous capture at frames97 and105 showed the front ivory sheet spreading into a triangular fan with striped self-overlap. This was a source binding defect. The central sheet had inherited nearest-anatomical-vertex weights: neighbouring vertices only6–9mm apart could jump from100% right thigh to100% left thigh. `dhoti-weights-diagnosis.json` measures270 edges with weight-vector L1 jumps above0.9; the maximum was2.0. The middle sheet was almost entirely thigh-bound, and the lower sheet also inherited knee/lowerleg/foot groups.

R7 changes only the central `Layered ivory dhoti` and its two `Ivory embroidered edge` meshes. Spine05 carries100% at the waist, smoothly decreasing to84%; at most16% total upper-thigh influence crossfades over90mm across the centre. Lower-leg influence is zero. All three pieces use the same continuous position-based function. Maximum adjacent weight-vector L1 change is now0.01758. The trousers and other garments retain their prior bindings.

The authoritative bounded patch changes5659 exported vertices' joint/weight records. `weight-correction.json` proves that every other GLB byte is identical toR6: geometry, normals, tangents, UVs, materials, embedded images, rig, skins' inverse binds and all animation payloads remain unchanged. The reopened editable scene also retains identical modeled geometry, UVs and materials. Its exact 164-bone rest/parent and baseline-action proof, and27 finite posed-bound samples, pass again.

`rebind_dhoti.py` owns the shared weight function; the main generator now calls it for future builds. Full Blender export is not asserted byte-identical to the bounded patch. The historical R6 generator and proof records are retained under `history/`; source input artifacts remain under the recorded scratch revision.

The R6 front/face images remain exact rest-geometry evidence. They cannot accept the changed posed drape. Actual R7 side-step, forward-run, draw/release and rear/cloth-clearance review is still required from the motion/integration owners. No acceptance is inferred from the smaller weight discontinuity alone.
