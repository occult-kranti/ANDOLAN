# Rama facial component: bounded acceptance

Final reviewed face: `1fdb01ccb894004a618a594cb41b2e955810c7bdc76855c42f7ce19b0516d92b`.
Final tangent-repaired output: `de61dc4c470920eab6f3265bc5467da7f9fb33d6fae2129a9353e7ca6d24d3f5`.

The independent [44-image review](independent-r4f-review.json) opened all nine actual static candidate views, three matched baseline views, two failed R4e views and every one of the 30 consecutive blink frames. Full closure, neutral eye alignment and blink continuity passed their bounded checks. No white-globe aperture, doubled overlay band or broken frame was observed in the final closed views. Root and project QA separately reviewed the functional result.

**Overall face art remains LIMITED.** The upper fold is puffy, corner contours are stylized, and neutral eye openings are wider after removing the old rim tubes. Skin, hair, gaze, expressive brows/jaw/lips and a production sculpt remain unfinished. This is not commercial character-quality acceptance.

## What changed

The accepted candidate splits actual native orbital quads into one small `RamaFace` mesh. There are no added skin shells and no extra skeleton. Original eye surfaces and 164-bone rest data remain unchanged. Pinned CC0 native upper/lower lid poses are baked into four full/half morphs. A spatial gain adjustment closes the medial corners without raising the entire lid back to the rejected full-strength pose.

The [source pins](final-source-pins.json), [geometry report](geometry.json), [seam report](seam.json) and [whole-aperture report](aperture.json) distinguish topology and numeric coverage from actual appearance. The 146 face/body attachment vertices have zero exported position/normal/UV discrepancy and zero morph position/normal deltas. Original skin-weight discrepancy is at most `5.96e-8`.

## Executed verification

| Evidence | Executed result | Scope |
| --- | --- | --- |
| `component-imported.json` | 41/41 PASS | Small authored-morph fixtures plus final repaired GLB import/binding/close-reset. Includes 30/60/120 Hz comparison, malformed input, pause, death from neutral/partial/full blink, respawn, ownership and 100 resets. |
| `geometry.json` | 19/19 PASS | Actual small morph payload, attributes, target bounds, intended eye and central coverage; neutral visibility compared with original baseline. |
| `seam.json` | 4/4 PASS | Exported native partition attachment and held morph boundary. |
| `aperture.json` | 8/8 PASS | All 855 currently visible sampled globe points covered at four view directions per eye; complete head/nose participate in visibility. Minimum sampled margin approximately 0.977 mm. |
| `candidate/capture.json` | 39 actual frames, clean exit | Nine neutral/half/closed views plus 30 consecutive 60 Hz simulation samples, Godot 4.6.3 Forward+, software Vulkan. |
| `baseline/capture.json` | Three actual views, clean exit | Same capture source, camera, lights and original Q3 hero. |
| `candidate/rama-blink.mp4` | Encoded and fully decoded | Video integrity, not hardware FPS or observation by itself. |
| `independent-r4f-review.json` | Full closure PASS; art LIMITED | All 44 listed images opened individually. |

Recorded fixed-rate samples are not achieved real-time performance. Actual-world input/integration, Windows and physical-GPU performance are not established by this component archive.

## Counterexamples retained

`rejected-r2/` shows the failed overlay's exposed eye and black outer patch outlines. `rejected-r3/` retains the overlay candidate rejected for a raised horizontal strip and corner joins. `rejected-r4d/` retains the overclosed full-strength native pose. `rejected-r4e/` retains medial white wedges despite passing the earlier central ray grid. The stronger whole-aperture checker rejects R4e in seven of eight directions; the final native corner correction passes all eight. Raw earlier outputs remain in their recorded scratch directories and were not removed.

## Tangent-only transfer of face evidence

The [repair receipt](tangent-repair/receipt.json) compares the exact visually reviewed GLB with the final output. Only 37 actual bytes differ, all inside the three allowed 16-byte Ivory silk tangent records at vertices 8160, 8188 and 8875. Existing UV triangles and normals yield signed frames `+1, -1, +1`. Every face, skeleton, morph, position, UV, skin, material, image and animation byte is identical. The original input can be reconstructed from the final bytes and the three recorded preimages.

The [repair CLI](../../../../art/hero-rama-face/README.md) was run against the fixed reviewed input and reproduced the final hash. The editable `.blend` remains unchanged. The source-only LOD owner's strict self-validation passed after the repair. This does not resolve the separate inherited tangent-frame orthogonality Q02 finding or add a fresh rendered cloth/hardware claim.

## Death-transition correction

Inspection after the art freeze found a separate runtime edge: death during a partial/full blink restarted the closure easing from zero and briefly opened the lids. The [old-source regression](death-transition/before.json) fails exactly the two new transition cases (39/41); the [fixed-source regression](death-transition/after.json) passes 41/41 with actual final GLB import. The controller now captures both current eye closures on the alive-to-dead transition and blends each monotonically to full closure over 0.28 seconds.

This changes only the death transition and reset bookkeeping. The frozen GLB, editable source, generator and candidate metadata are unchanged. The recorded 30 live-blink frames never enter the changed death branch; their exact original controller snapshot remains beside the capture. No new rendered death or actual-world result is claimed here.
