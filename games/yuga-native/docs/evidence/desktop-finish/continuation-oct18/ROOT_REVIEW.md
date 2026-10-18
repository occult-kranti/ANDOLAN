# Desktop continuation — 18 October 2026

This pass uses six roles across the existing ten screen rounds and three integration rounds. It does not count rejected art, diagnostics or repeated checks as new completed rounds. Desktop remains the priority; mobile is deferred.

## Accepted source changes

- **Controls and hero guide:** changing from 100% to 200% while capturing or selecting a late entry now reveals that same focused control after layout. Shared deferred reveal retains ownership and rejects hidden, disabled, freed or changed focus. The identical regression improves from 21/23 to 23/23. W1 and W2 reviewed all six native originals; lead reviewed all six too. This actual evidence uses production modals in a small native fixture, separately from full packaged play.
- **Landmarks:** per-builder, material-free primitive meshes reduce 238 geometry allocations to 13. Full mesh arrays, transforms, materials and collision behavior are retained. The native suite passes 23/23; a matched actual full-world pair is pixel-identical. Four known process-local shader owner IDs are normalized strictly; the original raw comparison failure is retained.
- **Armies:** fixed bar and held-arrow geometry is shared per army, reducing 102 initial geometry allocations to four. Each unit retains its materials and capsule. The same regression improves from 16/21 to 21/21. Both actual posed-unit originals are pixel-identical and were opened by W1, W4 and lead. The initial fixture cache-metadata error is preserved. This is allocation reuse, not a measured FPS or draw-call gain.
- **Idle traversal HUD:** the fully charged, grounded, ready state now uses one energy value and the current flight/tether keys and range. Its actual panel height falls from 171 to 88 logical pixels, keeping the same width and text sizes. Flight, cooldown, failed-aim, drill and outcome details retain their contextual presentation. The same fixture improves from 13/18 to 18/18, including native 100→200→100 scaling and persisted remaps. W1, W2 and lead opened the matched ordinary-scale full-world pair and accepted it. Exact scene/pose/physics controls match; UI-shadow differences and two distant pixels with a one-channel-value delta mean no whole-frame pixel-identity claim is made.
- **Packaging:** both new runtime helper scripts are required in the resource pack, including compiled-remap admission and orphan/substitution rejection. The same security fixture improves from 127/132 to 132/132.

The final common catalog passed 39/39 checks; its two screen suites passed 41/41 and its two resource suites passed 44/44 with unchanged runtime source inventories. The idle traversal HUD passed its focused behavior, independent source and ordinary-scale actual review. Exact-source CI and successor package qualification remain separate integration gates.

## Art and motion remain open

The connected editable C5 hair sculpt and its single major-shape correction both failed four-view actual review. The correction reduces the neck gap but still produces a smooth helmet, narrow capped gather and plate-like rear folds. Head, crown, tie and cameras remained fixed; no production GLB was changed. Preserve the finite source and two takes. Do not restart the same sculpt with more surface detail.

Private landing candidates improve some contact measurements but introduce other defects. The velocity-aware candidate meets the natural 60 Hz contact target but produces a sharp knee change at 30 Hz. The fixed 150 ms preparation successor improves ordinary angular changes, yet misses the 5 mm slow-drop contact target (11.483/7.921 mm) and produces a 105.027 mm extension at first high-speed support entry. All remain inactive. Canonical motion stays unchanged, and the continuous actual recording still owns the visible settling defect.

## Recovery and continuation

The remotely verified d199f607 recovery-map commit allowed removal of 182 exact inactive asset copies across seven old capture projects. The execution receipt records 1,034,743,808 allocated bytes reclaimed. No unique source, original capture, cache, user state or meaningful failed run was removed. These historical projects now require their exact recovery map before reuse.

Next work must resolve whole-hair form with a materially different method, qualify continuous motion across slow/ordinary/high-speed boundaries, and improve the map and unit art beyond their current structural finish. The original offline slice is still below the commercial graphics target. Native multiplayer, full roster, physical-GPU profiling, Windows execution and human listening/full-speed feel remain separate production gates.

## Evidence index

- [Modal owner](W2-screens-r1/receipt.json) and [actual UI](W1-actual-r1/ui-focus-r1/receipt.json)
- [Landmark owner](W4-world-r1/receipt.json) and [actual world pair](W1-actual-r1/world-landmarks-r1/receipt.json)
- [Army owner](W4-army-resources-r1/receipt.json) and [actual unit pair](W1-actual-r1/army-resources-r1/receipt.json)
- [Idle HUD source/behavior](W2-idle-hud-r1/source-receipt.json) and [independent source review](W6-integration-r1/idle-hud-source-review.json)
- [Final focused catalog integration](ROOT-integration-r1/receipt.json) and [fourth catalog source review](W5-catalog-idle-review-r1/receipt.json)
- [Package helper regression](W6-integration-r1/package-helper-checks.json)
- [Rejected motion candidates](W5-motion-r1/receipt.json) and [fixed-time successor](W5-anticipation-r1/receipt.json)
- [C5 source and two-take rejection](../../../../art/hero-finish/hair-sculpt-design/clay-volume-r5/source-receipt.json)
- [Exact storage execution](W6-integration-r1/storage-execution.json)
