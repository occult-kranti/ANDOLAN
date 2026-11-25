# World-art panel: Ghat Coast and Mountain Pulse

This study tests reuse of a real, openly licensed rock asset in the existing YUGA world. The two shoreline layouts are **rejected visual prototypes**, not changes to the live map. The compact rock was subsequently integrated as a temporary Mountain Pulse projectile; it does not affect collisions, damage or the authoritative simulation.

## Five review passes

| Pass | Work and evidence | Decision |
| --- | --- | --- |
| 1. Observe | Examined the existing three-lane world, the shoreline and both teams' gameplay cameras. The [baseline images](evidence/first-pass/) use real released-WASM states in a staged offline browser room. | Preserve the existing lane, collision and authority data. |
| 2. Place | Built a six-rock [Ghat Coast placement plan](candidate-plan.json) outside the actor envelope. [Layout](evidence/refined/layout-review.json) and [geometry](evidence/refined/geometry-review.json) checks found unchanged original map data and preserved source attributes. | Technical clearance alone is insufficient for visible level composition. |
| 3. Review composition | Compared [Sun](evidence/refined/candidate-sun.png) and [Moon](evidence/refined/candidate-moon.png) camera views against the [baseline](evidence/first-pass/). The refined view shows a disconnected fragment behind architecture and the other view barely reveals the new formations. | Reject the six-rock scenery layout. |
| 4. Reduce and replace | Generated a compact version of the source rock, then substituted it into the existing `rock_island` prefab in a separate candidate. [Structural checks](evidence/replacement/replacement-review.json) passed, but the [Sun view](evidence/replacement/candidate-sun.png) reads as a thin, disconnected textured slab at the water's edge. | Reject this shoreline replacement too. The current map keeps its original scenery. |
| 5. Apply and evaluate | The compact asset was integrated into Mountain Pulse for an in-flight cue. Its [in-game capture](evidence/lod/mountain-pulse-v3.png) shows it is visible without covering Hanuman. | Retain as an interim effect. At gameplay distance it reads as a dark flat rock, not the authored mountain concept, and its photoreal texture clashes with the stylized world. |

The first shoreline test also exposed an independent camera issue. In the prior build the normal movement path could place the fixed camera inside `authority-solid-4`, hiding the character even though the actor retained clearance. The [reproduction data](evidence/camera-occlusion.json) and [image](evidence/baseline-camera-inside-wall.png) record that earlier baseline; see the camera tests for the new fix before drawing conclusions about current behavior.

## Asset and rights

- Source: [Rock Face 01](https://polyhaven.com/a/rock_face_01), by Dario Barresi, [Poly Haven CC0](https://polyhaven.com/license). Its source glTF and texture files are preserved in [the existing world-landmark collection](../../../art/world-landmark-study/sources/rock_face_01/).
- The [compact GLB](art/rock-projectile.glb) has 2,823 triangles, down from 20,174. glTF-Transform 4.5.1 and meshoptimizer 1.3.0 simplified the source and MikkTSpace generated tangents. The original 1K base-color, normal and roughness textures remain embedded. The [build receipt](evidence/lod/lod-build.json) records hashes and parameters.
- The Khronos glTF validator reported [zero errors and warnings](evidence/lod/validator.json). Matched front/side Blender Cycles renders and a sampled nearest-surface comparison are in the [LOD evidence](evidence/lod/lod-visual-review.json). The measured values are sampled distances in normalized space, not an exhaustive geometric bound or a frame-rate measurement.
- The runtime copy and attribution are [here](../../../../yuga-rust/web/art/mountain-rock-NOTICE.txt). The source and compact output are identified by SHA-256 `96c332c01d173a2431115f3bac29be101fba341e5500e2a08e384f4edd17299e` and `1849d2e42477d72b2f3d41f2422f768575c0f4f86f3c65e86e3816ce376703da` respectively. The visual study's build receipt predates game integration, which is why it says candidate-only.

No GPU timings, accessibility results, network-load test, or proof of production-quality world art follows from this study. The recorded screenshots use a fixed 1280×800 view and staged room transport, not live multiplayer.

## Additional boulder candidate: research only

[Rock 07](https://polyhaven.com/a/rock_07), by Jenelle van Heerden, is a Poly Haven [CC0](https://polyhaven.com/license) scanned boulder. Its [source files](art/rock07-source/) and [compact GLB](art/rock07-compact.glb) are preserved here for a future visual review. **It is not integrated or visually tested in the game.** The 1K source glTF has SHA-256 `efcc2dcaa133ff8ad5c865dc2135772e8f5dbc83fa38db2ee2cf25382436b6e6`; the compact GLB has SHA-256 `41ebe3de5c774a2dd78fc5361639d79733be210cc34c66188814913caa5e57b9`. The [build receipt](evidence/lod/rock07-build.json) pins the hashes of the binary and all three texture files as well.

This candidate reduces 14,844 indexed triangles to 2,968 and uniformly scales its longest axis to one unit, preserving source proportions. Khronos glTF validation reports zero errors and warnings. A separate [Blender geometry check](evidence/lod/rock07-geometry.json) found 10 boundary edges and 15 non-manifold edges after coordinate welding, so it is not established as watertight. Do not use the scan for collision. The count of Blender-imported faces after welding is not an engine performance measurement. No in-game silhouette, camera, lighting or style-match approval has been performed.

Rebuild and inspect it from the repository root after installing the world-panel dependencies:

```sh
node games/yuga-native/docs/research/world-panel-2026/build-rock07-study.mjs games/yuga-native/docs/research/world-panel-2026/art/rock07-source /tmp/yuga-rock07-study
blender -b --python games/yuga-native/docs/research/world-panel-2026/inspect-rock07.py -- --input /tmp/yuga-rock07-study/rock07-compact.glb --output /tmp/yuga-rock07-study/geometry.json
```

## Reproduce the compact rock

From the repository root, with Node 22 and the source files present:

```sh
npm ci --prefix games/yuga-native/docs/research/world-panel-2026
node games/yuga-native/docs/research/world-panel-2026/build-rock-lod.mjs /tmp/yuga-rock-check
node games/yuga-native/docs/research/world-panel-2026/verify-rock-lod.mjs /tmp/yuga-rock-check/rock-projectile.glb /tmp/yuga-rock-check/validation.json
sha256sum /tmp/yuga-rock-check/rock-projectile.glb
```

The expected compact digest is listed above. These commands validate and rebuild the visual source only. They do not install it into the game.

## Reproduce the discarded world candidates

The scripts intentionally pin the earlier game package and will reject a different one. Recover the original tracked ZIP from commit `d1cad241` and set its path before running. The following writes temporary files only:

```sh
git show d1cad241:games/yuga-rust/downloads/yuga-rust-confluence.zip > /tmp/yuga-world-baseline.zip
export YUGA_BASE_GAME_ZIP=/tmp/yuga-world-baseline.zip
node games/yuga-native/docs/research/world-panel-2026/build-candidate.mjs /tmp/yuga-ghat-candidate
python3 games/yuga-native/docs/research/world-panel-2026/verify-layout.py /tmp/yuga-ghat-candidate/map-candidate.json
node games/yuga-native/docs/research/world-panel-2026/verify-geometry.mjs /tmp/yuga-ghat-candidate
python3 games/yuga-native/docs/research/world-panel-2026/package-candidate.py /tmp/yuga-ghat-candidate
node games/yuga-native/docs/research/world-panel-2026/build-replacement.mjs /tmp/yuga-ghat-replacement
node games/yuga-native/docs/research/world-panel-2026/verify-replacement.mjs /tmp/yuga-ghat-replacement
```

Browser recapture also requires the repository's Playwright dependencies and Chromium. After creating and packaging a candidate, run `node games/yuga-native/docs/research/world-panel-2026/capture-candidate.mjs /tmp/yuga-ghat-candidate`; that script records its staged-transport method in the output JSON. Review actual views and gameplay readability before ever promoting a scenery change.
