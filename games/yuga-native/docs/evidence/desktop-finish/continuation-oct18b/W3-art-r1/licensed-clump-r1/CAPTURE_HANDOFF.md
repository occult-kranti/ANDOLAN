# Exact frozen C7 capture handoff

Owner W1 desktop_actual_w1; four authoring clay views only after its serial actual slot. No source edits before review. Root has received source eligibility and known fit limits. Actual target must be fresh; source-save/reload do not substitute for actual renders.

Scene: `/workspace/scratch/yuga-next-W3-r1/licensed-build-r1/whole-hair-licensed-r1.blend` (same inode as `art/hero-finish/hair-sculpt-design/clay-licensed-r1/authoring-payload/whole-hair-licensed-r1.blend`). SHA256 `0acb259a6a5b1c538fa050cc5b42125e31399ed0a8ea41eaae33b24b7ac84b07`,2476133B.

Helper: `/workspace/ANDOLAN/games/yuga-native/art/hero-finish/hair-sculpt-design/clay-licensed-r1/capture_sculpt.py`, SHA256 `0d05dacf96490ae3a130e513c9e807bddad2931073fa2fe18942fe131f899dc7` (unchanged four-view helper).

```sh
env LP_NUM_THREADS=2 OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 taskset -c 0,1 timeout 900s /usr/bin/blender --factory-startup --disable-autoexec --background /workspace/scratch/yuga-next-W3-r1/licensed-build-r1/whole-hair-licensed-r1.blend --threads 2 --python /workspace/ANDOLAN/games/yuga-native/art/hero-finish/hair-sculpt-design/clay-licensed-r1/capture_sculpt.py -- --output /workspace/scratch/yuga-next-W3-r1/licensed-actual-r1 --expected-scene-sha256 0acb259a6a5b1c538fa050cc5b42125e31399ed0a8ea41eaae33b24b7ac84b07
```

W1 uses its private unchanged execution environment/watchdog/log location and retains originals. CPU0,1 exclusively,32samples/raw/no denoise,1024². No source-save/render overlap or source mutation. Confirm fresh ≥500MiB storage before start and every frame; source unchanged before/after. Fixed VIEW_front, VIEW_anatomical-left-profile, VIEW_rear and VIEW_cast-angle-authoring/lenses/lighting remain exact to C6. Fourth view is rest authoring scope, not an animated cast.

Review each original directly: front crown/hairline/eyes/ear exposure; profile low curled gather and flowing scalp-to-nape contour; rear unequal rounded grouped falls and staggered taper; oblique the same coherent flow without helmet or peg. Watch exposed skin through seating intersections, tie coverage, and lower-back hair/gold contact. No blanket zero buried-contact gate. Bun-band radius33.38mm vs32.08mm reference aperture means hardware fit is unaccepted until actual inspection. Source cap/connector geometry is absent. No GLB, rig, runtime material or canonical change; independent all-view shape decision precedes `INTEGRATION_PATH.md`.
