# Generated Rama source viewer

This is an interactive inspection of the **actual generated GLB**, not a new game, rig or animation system. It reuses the repository's pinned **PlayCanvas 2.23.3** dependency and the original painted PBR environment helper at `games/yuga/client/environment-light.ts`. The glTF container loader, embedded-image decoding, material setup, mesh rendering and shadow system belong to that existing engine. The small new layer supplies framing, orbit/zoom controls and truthful loading/error feedback.

The root-owned model is `../web/media/rama-generated.glb`. It is loaded relative to the built viewer document as `../media/rama-generated.glb`. There is no configurable remote-model URL, CDN script or new dependency/lockfile change. The generated source has no skin or animation, which remains visible in the interface. Neutral studio key/fill/rim lights preserve imported material/texture bindings.

## Build

From the repository root, after the existing lockfile-based `npm ci`:

```sh
node_modules/.bin/vite build \
  --config games/yuga-native/tools/build-observatory/viewer-source/vite.config.ts
```

Check the new TypeScript source with the existing compiler:

```sh
node_modules/.bin/tsc --noEmit --strict --target ES2022 --module ESNext \
  --moduleResolution bundler --lib ES2022,DOM,DOM.Iterable --skipLibCheck \
  games/yuga-native/tools/build-observatory/viewer-source/main.ts
```

Only the owned `web/viewer/` build output is cleared. Vite uses `base: './'`; engine code is bundled locally. Its font warnings are intentional external-file preservation: the built CSS loads the dashboard's existing `web/media/NotoSans-Regular.ttf` and `NotoSerif-Regular.ttf` via `../../media/`, avoiding duplicate font copies. These runtime requests were checked by the actual browser run.

Run the observatory's [local server](../README.md), then open its `/viewer/` route. The static host uses the same `viewer/` subdirectory. Root's dashboard asset can use the exact `model_url: "viewer/"`; the backend and frontend allow that fixed route, with no general relative navigation allowance. The server supports `.glb` as `model/gltf-binary`, `.txt` notices and `.ttf` fonts.

## Controls and states

- Pointer/touch drag or focused-canvas arrow keys orbit.
- Scroll, +/− keys and buttons zoom within fitted limits; Home or **Reset view** restores framing.
- Bounds fit the whole source and refit when the viewport changes, preserving user zoom.
- Nothing rotates automatically, including under reduced-motion preferences.
- Failed loading retains a visible explanation and retry. Failed asset entries are removed before retry so an earlier missing-file response is not cached as a permanent failure.
- Hidden pages do not request renders. The engine renders when the model, view or viewport changes; no frame-rate claim is made.

`window.__YUGA_ASSET_VIEWER__` exposes read-only-purpose inspection diagnostics: loaded mesh/material/triangle/skin/animation counts, bounds, current camera and actual rendered-frame count. These are not performance or game-acceptance metrics.

## Actual verification on 23 October 2026

An installed Chromium browser opened the real GLB with requested ANGLE/SwiftShader software rendering. The loaded source reported **one mesh, one mesh instance, 96,660 triangles, one material, zero skinned primitives and zero animations**. Imported bounds were approximately 0.601 × 1.002 × 0.466 source units; units have not been accepted as real-world scale.

The [versioned evidence index](evidence/receipt.json), [original visual-run receipt](evidence/receipt-pre-type-correction.json), [exact test script](evidence/smoke.mjs) and original [desktop front](evidence/desktop-front.png), [orbited](evidence/desktop-orbit.png) and [mobile](evidence/mobile.png) captures bind the actual run. Twelve browser checks passed: actual model loading, keyboard orbit, zoom, reset, pointer orbit, no automatic rotation, source label, desktop overflow, mobile/reduced-motion loading, mobile overflow, useful missing-file error and actual retry recovery. There were no page errors or console warnings/errors on that full visual run. Independent strict TypeScript review then found nullable mesh/material references and inferred angle-array types; these were fixed narrowly. The strict typecheck and rebuild passed, followed by three no-screenshot actual-load/count/orbit checks on the corrected bundle. The [correction confirmation](evidence/type-correction-confirmation.json) binds that final source and bundle separately; the original screenshots remain labeled as pre-type-fix evidence. Three original screenshots were retained: desktop front, desktop orbited view and 390-pixel mobile layout. Earlier route/retry failures were retained separately and corrected; they are not represented as successful tests.

The actual images show bronze skin, ivory/cobalt garments and gold armor. Facial/hair/trim detail remains soft and the asset is unrigged. This proves interactive source display, not commercial game-art quality, animation readiness, native integration or physical-GPU FPS. Rigging, topology/LOD, materials at gameplay distance, collision and continuous animation review remain separate gates.

Engine MIT license and source attribution are copied into the built viewer's `NOTICE.txt` and `PLAYCANVAS-LICENSE.txt`. Font notices stay with the dashboard's existing media package. Model provenance remains with the generated-source reports.
