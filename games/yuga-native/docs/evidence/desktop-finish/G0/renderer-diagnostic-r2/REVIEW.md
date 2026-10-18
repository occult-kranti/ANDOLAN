# G0 renderer diagnosis — checkpoint 2

A concrete shader-expression comparison now renders the full G2 material bindings. Removing only the remaining `fwidth(fine_phase)` filtering expression from the no-carving shader produced **two original 1280×960 framebuffers, engine exit 0 and 6/6 observer checks in 108.841 seconds**. The initial draw completed at 66.591 seconds. The matched no-carving shader retaining that expression timed out after 129.978 seconds with zero images. Both use the corrected camera helper and otherwise identical source, engine, imported caches, seed and render controls.

| Exact derivative | Outcome | Scope |
| --- | --- | --- |
| Minimal texture-preserving body `80d4591e…` | 105.933s, exit 0, two images, five historical checks | Full bindings/maps; mineral/carving code removed. Training image has the camera-metadata defect below. |
| Mineral wash + packed maps, carving removed `17a7044c…` | 129.978s, watchdog exit −15, zero images | Removing carving alone is insufficient. |
| Same wash/maps, `detail=1.0` replaces the fine derivative filter `cb7af1e0…` | 108.841s, exit 0, two images, six checks | Full broad/fine mineral math and maps; carving still omitted and fine pattern unfiltered. |

This isolates a usable expression-level discriminant in the full G2 combination. It does not prove the exact native compiler/worker lock cycle or that derivatives are generally unsupported: earlier G1 rendering used the fine derivative filter with different binding inputs. The last logged shader-cache key is not proven to identify the masonry material. No engine replacement, product setting change or canonical product shader change was performed.

All four new originals were directly opened. The successful no-derivative pair shows actual hero/courtyard geometry and warm/cool paving with authored texture detail. Broad lit surfaces and stippled fine seams remain visible. Static frames do not establish motion shimmer, fine-pattern antialiasing, commercial quality or hardware FPS. The environment remains diagnostic; a feature-preserving, filtered production shader and current S1 integration originals are still required.

The camera helper had a separate defect: `start_training()` selected the gameplay camera while the old second capture retained review-camera metadata. The original no-binding and minimal-body training images remain genuine framebuffers, but their declared camera and matched-camera framing cannot be accepted. Their earlier first-draw successes and title images remain valid. [The correction receipt](camera-identity-correction.json) preserves exact old/new helper hashes. Future captures reselect the review camera after training begins and assert actual viewport camera identity. No prior sealed receipt or image was rewritten.

The corrected no-derivative pair records physics/render frames 27/13 and 51/25 with the same actual review camera. Imported, same-callback sole minima are title L+0.572000/R+0.571720 mm and training L+0.855399/R+0.855557 mm relative to actual collision rays. These are settled support anchors, not a measurement of first-acquisition continuity. The title-light change is an existing training transition, not a gold-material comparison.

Every 997-entry snapshot and the parent immutable inventory verified unchanged after execution. All runs use CPU0,1, LP_NUM_THREADS=2 and one OMP/BLAS/MKL thread; no validated Godot worker limit is claimed. The 30 Hz fixed capture rate is sampling, not performance. No engine ERROR lines occurred in the completed no-derivative run; RGB8-to-RGBA8 fallback warnings remain in raw logs.

[Receipt](receipt.json) pins commands, raw logs, full observer JSON, source deltas, snapshots, exact helper and all four original PNGs. [Checkpoint 1](../renderer-diagnostic-r1/REVIEW.md) remains unchanged. Production renderer/art acceptance remains open pending the shader owner's filtered candidate and coordinator integration review.
