# One Vayu landing-court pilot

This opt-in module replaces only `sun-lift-west`, an 8 × 8 × 8 m traversal podium at `(-20, 0, -88)`. Its landing plane remains y=8. The other seven decks, ten grapple anchors, routes, army and economy are outside this change. Canonical enablement belongs to the full-world integration owner after the same candidate passes physics and actual visual review.

The one-court geometry passed that review in [R4](../../art/ten-rounds-oct23/world/r4/INDEX.json): 16 actual 960 × 540 images and 65 positive checks, with frozen source copies. The product scene now enables this one pilot through `wind_court_pilot_enabled`; the builder's default remains opt-in. The current capture helper sets that scene property false **before** adding it to the tree, reproducing the legacy baseline before its isolated swap. Its later integrated-source headless preflight has 34 checks. The exact earlier R4 helper and world sources remain in the evidence packet; later tool changes do not rewrite the original capture contract.

The shape follows the existing [next visible map task](../../docs/evidence/desktop-finish/continuation-oct18b/W4-world-r1/NEXT_VISIBLE_MAP_TASK.md): broad stepped plinth, solid closed blind bays between engaged piers, and a continuous stepped crown wrapped around all four sides. There is no doorway or additional skyline building. These are original fictional Vayu-court forms informed by the existing [source library](../../art/production/SOURCE_LIBRARY.md); they are not a historical temple reconstruction.

The implementation adapts the existing `world_render_resources.gd` immutable BoxMesh cache and the existing stone shader, warm trim and shade materials. SurfaceTool merges the authored primitive assemblies into three opaque material surfaces per detail level. Near geometry has 588 triangles; mid geometry has 444. The twelve small pier collars are omitted beyond 38 m. Original medallion, six ember meshes and gold tether ring remain separate, unchanged signals. No shader, texture, light or external model is added.

## Collision integration contract

`Landmarks.new().build(parent, traversal, {"wind_court_pilot": true})` enables the candidate for the exact known landmark ID and 8 m dimensions. The default two-argument builder remains unchanged. The result identifies `replaces_manifest_collision: "sun-lift-west-deck"`.

The caller **must omit or remove that exact manifest collision box** when the pilot is enabled. The candidate creates one `WindCourtDetailedCollision` StaticBody3D containing 36 authored BoxShape3D shapes. Retaining the old full box creates an invisible wall across the recessed bays. A safe integration first constructs the existing bodies, then replaces only the old body in its array slot after a positive enabled report and actual detailed-body check, before world readiness. Unsupported or changed dimensions therefore retain legacy physics. Root integration must also register the new body in the native-platform group and retain the seven unrelated boxes. `pilot_collision: false` is for a visual-only fixture whose caller explicitly owns equivalent detailed collision; it must not silently enter gameplay.

All solid architecture is inside the original 8 m envelope. The core backs every bay. A radius .65 m, height 1.8 m capsule matches the actual Confluence hero dimensions. The fixture checks a small flight-height clearance in a bay, the real closed surface, roof contact and an outside-footprint counterexample. This is a local 3D collision change, not an assertion that the old flat box and new geometry have identical physics.

## Reproduce the checks

From the repository root, with Godot 4.6.3:

```sh
godot --headless --path games/yuga-native --script tools/wind-court-pilot/test_pilot.gd -- --report=/tmp/wind-court-physics.json
```

The actual native fixture has 41 checks. It deliberately omits the manifest flat collider. In addition to contact queries, it compares all seven unrelated deck meshes, all ten anchors and original roof signals, and checks geometry and material budgets. Independent adversarial review also compares the actual solid mesh triangles with real physics hits and injects the old full box as a negative control. That review is separate from the author fixture.

For actual staged full-world views, prepare the project's ignored `.godot` imports first using the same engine. Preserve tracked import-sidecar bytes before any editor import; retain generated changes for diagnosis and restore those exact bytes if necessary. The capture runner does not download dependencies or perform imports:

```sh
python games/yuga-native/tools/wind-court-pilot/run_capture.py --godot /workspace/scratch/ten-rounds-oct23/runtime-release/restored/godot --runtime /workspace/scratch/ten-rounds-oct23/runtime/runtime --output /tmp/wind-court-capture-fresh --display 121 --timeout 300
```

Prove the full-world staging and both actual collision rays without images first:

```sh
godot --headless --path games/yuga-native --script tools/wind-court-pilot/capture_pilot.gd -- --preflight --output=/tmp/wind-court-preflight-fresh
```

The runtime must contain verified Xvfb and Mesa Vulkan libraries and have its adjacent `setup-report.json`. The runner reserves a fresh display in 90–199, retains command/PID/log/hash receipts, checks actual PNG dimensions and rendering counters, and stops only its own processes. An existing output directory is rejected.

Eight matched states compare the ordinary historical camera, close court, roof/context, rear face and short three-frame lateral move. Day and night are compared at ordinary and close cameras. The full canonical world is loaded, then every actual process/physics callback is held individually. Animation mixers and skeletal modifiers are deactivated, and two frames settle before the state is pinned. Hero bone poses, all army transforms and simulation clocks must remain identical; failures retain field-level differences. Physics bodies stay active. Existing water animation speed is set to zero in both variants, and existing lighting changes only to the named day/night phase. Exact old material resources and roof signals are reused by the live isolated swap. Other decks and anchors retain their original instances.

Do not substitute `world.process_mode = DISABLED` for this hold. CollisionObject3D's default disable behavior removes it from the physics space, while children with their own explicit process mode can continue advancing. The retained failed R3 comparison exposed both errors; its real images were diagnostics, not accepted matched evidence.

This fixture is an art comparison with explicit staging. It does not demonstrate ordinary input, network play, hardware FPS, final commercial visual parity or full-game completion. The short lateral sequence tests the selected near-view edges; it does not cover every LOD threshold or every route.

## Separate optional material study

`capture_material_study.gd` compares the accepted geometry with its original material against the **same mesh and collider instances** using a native PBR surface override. It reads the already audited [Poly Haven Sandstone Blocks 05 kit](../../art/source-kits/production-reuse-oct23/sandstone-blocks-05/manifest.json), credited to Rob Tuytel under CC0-1.0. Its 1K diffuse, OpenGL normal and red-channel roughness source PNGs total 6,220,633 bytes. They are not downloaded again or copied.

The adapter preserves the source `.tres` scalar settings in a small private native resource clone, binds verified source images as ImageTextures, and follows the existing `hero_district_detail.gd` StandardMaterial3D world-triplanar pattern. A tile spans the source manifest's 3 m. The normal depth is .55; albedo stays white, metal stays zero and roughness uses the red channel. Roughness is R8 in memory; original PNGs stay unchanged. Three maps with 10 mip levels occupy 9,786,707 decoded bytes; the 16 MiB GPU allowance is a conservative estimate, not a hardware measurement. Three texture samplers and approximately nine triplanar texture fetches replace only surface 0 at both detail levels. The three architectural surfaces, gold/shade materials, roof signals, geometry and detailed colliders remain unchanged.

```sh
godot --headless --path games/yuga-native --script tools/wind-court-pilot/capture_material_study.gd -- --preflight --output=/tmp/wind-court-pbr-preflight-fresh
python games/yuga-native/tools/wind-court-pilot/run_capture.py --material-study --godot /workspace/scratch/ten-rounds-oct23/runtime-release/restored/godot --runtime /workspace/scratch/ten-rounds-oct23/runtime/runtime --output /tmp/wind-court-pbr-capture-fresh --display 121 --timeout 300
```

This is a distinct, optional art study with three camera pairs: close day, close night and rear day. Its headless preflight has 19 checks; actual images and independent review are required separately. It does not alter the canonical court material or waive the original geometry gate's no-new-texture contract. There is no added shader file, light, texture copy or geometry.

The [frozen PBR study](../../art/ten-rounds-oct23/world/pbr-r1/INDEX.json) contains six actual images, 31 positive capture checks, the 19-check headless result, exact helper/material source copies, native scalar settings, and verified original texture hashes. All poses, clocks, camera pairs, mesh and collider identities passed. Root reviewed the three candidate views; independent review viewed all six originals and accepted the material direction. It remains a labeled optional candidate; the game's canonical material remains the original R4 material. Further ordinary-distance, motion and art-coherence review belongs to a later gate.
