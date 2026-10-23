# Diya flame and reused Rama cast: isolated render evidence

This packet belongs to the reuse-first source/effects lab. It imports the existing
original diya and runs the existing original Rama cast effects. It is separate
from the accepted game and does not close a finished-game or final-art gate.

The [corrected six-second sequence](sequence.mp4) contains **72 actual advancing
960 × 640 frames at 12 simulated FPS**, rendered in Godot 4.6.3 Forward+ on
llvmpipe software Vulkan. It is a silent isolated effects study, not gameplay,
hero body animation, real-time GPU performance or Deadlock-quality acceptance.
The [video probe](video-probe.json) records the encoded frame count and duration.

The source diya's white flame is opaque geometry. The adapter keeps its GLB bytes
unchanged and uses a reversible, bounded material fragment mask. Two crossed
animated alpha quads and one local light provide the replacement cue. This is
draw-time replacement, not repaired topology, a new low-poly prop or an animated
hero model.

Headless checks and actual render evidence are recorded separately. The script
sources and precise reproduction commands live in
[the standalone tool](../../../tools/reuse-vfx-stage/README.md).

The [27 lifecycle checks](lifecycle.json) pass. Actual pixel checks show 36 distinct
normal-motion flame crops and one unchanged crop over all 12 reduced-motion
frames. The contact presentation expires naturally and reuses one allocation
across three casts; reset clears it. The exact original GLB remains 96,190
triangles, with 4 replacement-flame triangles and one local light added.

**The corrected capture's strict conservative framing gate remains failed.**
[Its original report](capture.json) retains `passed: false`; Godot exited 5 and
the wrapper exited 1, so no success `runner-report.json` exists. The separately
recorded [observed-failure receipt](observed-failure-receipt.json) binds all 75 raw
image hashes, source/engine/log hashes and those outcomes. [97 of 98 actual
checks pass](verification.json). This failure is not relabeled as success.

The [separate indexed-geometry diagnosis](floor-occlusion-analysis.json) replays
the identical accepted event fixture, matches captured effect state counts and
projects actual triangle vertices. In eight contact frames the enclosing AABB
reaches 641 px, while actual indexed vertices stop at 546 px. The existing opaque
floor further reduces the visible envelope to 523 px. Thus empty enclosing-box
volume causes the strict false positive; floor occlusion is an additional effect.
The original 575 px content margin is unchanged. This supports only the bounded
visible presentation reviewed here; the unoccluded AABB gate stays open.

Matched [source](control-mask-off.png), [masked source](control-mask-on.png) and
[replacement](control-replacement.png) controls share camera, clock, exposure and
zero local-light energy. Directional shadows are disabled **only in these three
controls**, identically. The source mask changes 1,356 pixels inside its projected
box when the maximum RGB-channel difference exceeds 3/255; zero pixels outside
that box and subtitle band exceed this threshold. The tiny gray wick/base
is intentionally retained. Real shadows remain throughout the moving sequence.

The [independent visual review](../../../docs/research/ten-rounds-oct23/review/vfx-visual-r2.json)
inspected ordered actual originals, captions, movement and controls. Its threshold-0
pixel comparison finds 1,360 changed mask pixels and zero outside in the content
band; the four-pixel difference from the 3/255 count is expected. The
[independent exact-geometry review](../../../docs/research/ten-rounds-oct23/review/vfx-exact-geometry-review.json)
reran the helper, inspected the shaders and recalculated all 72 projection bounds.
It accepts this bounded visible presentation while preserving the strict failed
conservative gate and all runtime/whole-ability limits.

The [first sequence](sequence-original.mp4), [first failed pixel report](verification-original.json)
and original controls remain available. They showed clipped windup, low day-caption
contrast and 523 changed pixels from the removed opaque flame's shadow. The one
correction widened framing and backed captions; it did not overwrite the original
evidence. Project06 was prepared for control-only rendering but never rendered.
Exact original/final preview and runner sources are retained alongside their
[source manifests](source-manifest.json). [Status](status.json) keeps source tests,
render completion, failed gates and integration limits separate.

Review the moving sequence, mask-off/on/replacement control images, frame clocks,
source hashes and independent lifecycle checks together. Simulation playback
rate is not measured renderer FPS. The software Vulkan adapter does not establish
availability of a physical GPU. Public model/output rights intake remains in
[the existing source notice](../../../NOTICE/CLOUD-DIYA-PILOT.md).

The next integration gates are source LOD/physical scale, connecting the existing
game clock/settings/camera, real-level day/night review and light-count budgets.
The accepted runtime, source GLB and original effect/shader files were not changed.
