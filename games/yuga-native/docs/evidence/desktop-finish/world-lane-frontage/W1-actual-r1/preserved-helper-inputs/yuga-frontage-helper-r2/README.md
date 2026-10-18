# Frontage common capture helper r2 — SOURCE ONLY

Pinned product: YUGA native source96d5b9cd3114b9732f7dc80433b1ca0a1d4a9b12. This directory contains no captured images, native parse/preflight, runtime promotion or visual acceptance. W1 owns that next gate; W4 ran only the Python comparator's 32 synthetic controls on CPU3.

Stage identical `capture_frontage.gd` into BOTH private siblings as `res://tools/graphics-six/capture_scene_anchors.gd`. It extends the inherited exact `res://tools/graphics-six/capture_compact_screens.gd` (9a0fb75c6fab298f0babb19c1c7d6aa7e5234b94b9472971086e34a54391c51e). No other collector script needs staging. Source-only r1 remains preserved at /workspace/scratch/yuga-frontage-helper-r1; r2 repairs its final-modifier sampling seam and explicitly checks the ConcavePolygonShape3D subclass before subclass APIs. Both siblings also need identical original candidate.gd cc78e2b941c175ad535cb317619f4282a1a6a06d3ce040fbabcfb31af6f1b924 and candidate-mesh.json117123f32c232dc2c2693bbf0180578feb85396fcddaf1518b7c6d653698f141 under `res://art/world-finish/lane-frontage-r1/`. Include both art files and helper/base/selection in each immutable manifest, including import closure.

The ONLY differing input JSON is `res://tools/visual-rounds/frontage-review.json`: exactly `{"branch":"baseline"}` versus `{"branch":"candidate"}`. Derived snapshot markers differ accordingly. Common code invokes configure only for candidate after ordinary world ready, then identical settle. The stock snapshot inventory must use W1's explicit two-art-file adapter, not silently omit these dependencies. Use the same separately frozen runner whose scene-anchors expected count is3; no canonical runner edit.

Frames are 960×540, base1280×720 at factor1.0. Actual boot→title scales→real Enter→live world stays the inherited workflow. Three ordered shots:

1. `00-world-product`: actual current active player camera.
2. `01-frontage-contact`: explicitly supplemental camera at[16,1.65,-44], looking at[20,1.9,-36.35], FOV58,near.08,far380. Hero/physics/clocks continue. This is an authored close view, not a new product camera.
3. `02-overview-context`: real F1 overview, held army/kit clocks and hero position, then real F1 return to product camera and clock resume. Both branches retain the accepted roof and same overview composition.

No pose, time, lighting, authority, motion or production-camera rewrite. Full actual164 global bone poses cached INSIDE RamaMotion.modification_processed (never read back after restoration), hero transform/velocity, army root+joints/report, clocks, original player camera, sampled active camera/getters, actual Environment stored properties and SSAO getters, all scene Light3D stored properties, effective per-surface materials/overrides/overlays and shader uniforms, nav-manifest hash, every world body/shape/metadata, existing mesh transform/visibility/materials/AABB/vertex counts are captured. The callback also records rig/hero transforms, active modifier order and raw physics/process/drawn counters. RamaMotion must be last active modifier. A common frames override preserves the exact inherited schedule while observing completed frame_post_draw signals; actual snapshots require callback process/physics age0 and exactly one completed draw since the callback. Preflight requires no real draw (age0), explicitly establishing no rendered-frame correlation. Raw Engine draw_age remains recorded; no guessed Engine counter offset is asserted. Full matrices and age controls remain exact cross-branch. Typed-null resource handling is the exact narrow correction established by the AO diagnostic. Unsupported nonnull objects/RIDs/depth or nonfinite values remain failed controls.

The explicit exception is the original block2 mesh subtree hidden plus one2816triangle/3surface replacement using the SAME actual material objects, and its SAME authority-solid-2 body/sole CollisionShape3D Box→Concave detail. No new bodies, roof change, lights, textures or materials. Local mesh points must equal raw near geometry, body-local faces must equal transformed visible points exactly; world reconstruction additionally uses the existing native fixture's Vector3.is_equal_approx and records maximum error. These are float-coordinate checks, not mathematical exact arithmetic or full ability testing. The previously sealed39/39 native capsule/ray/restore controls remain the contact evidence; this capture does not replay or replace that fixture.

Cross-branch comparison has no camera, pose, clock, material or light tolerance. Per-branch native overview return checks exact camera path/origin/projection and Godot Basis.is_equal_approx only for the previously measured SpringArm roundoff; raw before/after matrices remain reported and must match across branches. Audio cleanup runs after scene disposal: eight main frames, two real mixer ticks within250ms, then eight cleanup frames. Failure or exit warnings must remain reported; do not weaken an assertion to conceal a fixture/lifecycle issue.

Run comparator (after both preflight or actual reports exist):

```sh
python /workspace/scratch/yuga-frontage-helper-r2/compare_frontage.py \
  --baseline /absolute/baseline/preflight.json \
  --candidate /absolute/candidate/preflight.json \
  --output /absolute/fresh/control-comparison.json
```

For raster replace report basenames with capture.json. W1 chooses and pins exact e69 executable/provenance, same112Godot+101Mesa seeds copied symmetrically, same external runner/adapter, fresh output and native warning audit. Preserve>=500MiB workspace reserve; no new /tmp copies/imports. Native parse/preflight is REQUIRED and UNRUN by W4. If it finds a fixture defect, preserve this frozen r1 and make an explicit identical successor in both branches.

Comparator controls:27/32 synthetic JSON checks; stale/missing/followed-by-later-modifier/draw-uncorrelated callback and corrupt bone/clock/camera/light/AO/material/roof/nav/body, oldbox/extra shape, local vertices/bounds/material identity/newtexture, moved/lost frontage, unsupported/NaN, native failure, overview return and mixer failure are rejected. This is not a native result.

Source derivation: accepted roof helper555a4abb…f67985 (164pose/unit/collision and mixer cleanup), overview helperd15683f5…751ae (native overview ownership), AO helper86e0037c…f1ede9e plus separately proven typed-null correction (full material/environment/light encoding), current compact base9a0fb75c…91c51e. See receipt.json for complete input hashes. No proprietary binaries/assets or new textures are introduced.

W5 bounded independent source review accepted the callback/cast delta; its one requested comparator correction binds each shot's preflight_no_draw to its parent report.preflight. Both actual reports falsely selecting the headless age0 path are now a retained synthetic negative. Callback freshness bounds are proposed native admission gates, not measured engine facts; W1 must preserve a headless phase mismatch if encountered and use an explicit successor rather than silently relaxing ages.
