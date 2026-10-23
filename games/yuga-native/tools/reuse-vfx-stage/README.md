# Reused-source diya and bow effects stage

This standalone Godot 4.6.3 preview imports the **exact existing original diya**
and runs the **unchanged existing Rama ability presentation**. It does not make
another engine or alter the accepted game. It is an integration candidate for
review, outside native runtime promotion.

The generated diya contains an opaque white mesh flame in the same surface as
the bowl. `source_mask.gdshader` preserves the original GLB and its two textures,
but discards fragments in a small source-coordinate box around that flame.
This is a reversible draw-time mask, **not deleted or repaired topology**. The
replacement uses two crossed alpha quads (four triangles), a single local light,
an explicit bounded clock and a small original teardrop shader. No global shader
`TIME`, screen reads, downloaded effect textures or commercial-game assets are
used. The source mesh is still 96,190 triangles; this does not solve prop LODs.

`flame_lamp.gd` owns one configured source. Failed inputs roll back, duplicate
configuration cannot add another model, invalid deltas cannot advance the clock,
suspension freezes it, reduced motion stops swaying and pulsing, reduced effects
lower intensity, and a viewer distance over 18 source units hides the flame and
sets its light energy to zero. The preview's distance method is an explicit
adapter hook, not automatically connected to the game camera. Source scale still
needs real-world calibration. Culling the flame does not cull the source prop.

`rama_ability_effects.gd` and its three shaders are copied unchanged from the
current project. The preview sends schema-valid **staged presentation events**.
They demonstrate release, travel, contact, natural contact expiry, pooled contact
reuse and end/reset. They do not authorize damage or demonstrate animated hero
body poses. The six-second video is an actual frame sequence at 12 simulated FPS,
not a recording of real-time gameplay or proof of hardware performance.

The data-only lifecycle fixture can run directly from the repository root without
generated imports. It uses Godot's existing GLTFDocument loader for the exact GLB:

```sh
godot --headless --path games/yuga-native \
  --script res://tools/reuse-vfx-stage/test_stage.gd \
  -- --report=/absolute/writable/lifecycle.json
```

The optional report's parent directory must exist. A failed check exits1; an
unwritable report exits2. Rendering is deliberately separate. Run these commands
from the repository root, selecting fresh scratch directories:

```sh
python3 games/yuga-native/tools/reuse-vfx-stage/prepare_preview.py \
  --output /workspace/scratch/vfx-reproduce/project
godot --headless --path /workspace/scratch/vfx-reproduce/project --editor --import --quit
godot --headless --path /workspace/scratch/vfx-reproduce/project \
  --script res://test_stage.gd -- --report=/workspace/scratch/vfx-reproduce/lifecycle.json
python3 games/yuga-native/tools/setup-render-runtime.py \
  --root /workspace/scratch/ten-rounds-oct23/runtime
python3 games/yuga-native/tools/reuse-vfx-stage/run_capture.py \
  --project /workspace/scratch/vfx-reproduce/project \
  --runtime /workspace/scratch/ten-rounds-oct23/runtime/runtime \
  --output /workspace/scratch/vfx-reproduce/capture --display 153
```

The renderer must be serialized with other heavy software captures. The runner
refuses occupied displays and existing
output directories, isolates XDG settings/cache, and cleans up only its own child
processes. It reuses the repository's checksum-verified Debian runtime setup.
The capture explicitly uses Forward+ with Mesa lavapipe software Vulkan.

The 72 advancing frames cover night/full cues, day/full cues and night/reduced
cues, with real directional shadows. Three additional matched controls hold the
camera, clock, exposure and local-light energy constant: mask off, mask on without
replacement, mask on with replacement. Directional shadows are disabled identically
only in those controls. The capture's frame data records exact phases, local-light
energy, event state, effect budgets, pool counts, draw calls and object counts.

The current actual study's conservative AABB gate remains failed, even though the
held review and exact indexed-geometry projection put the visible cast inside the
content margins. Do not weaken that test or relabel the capture as fully passed.
The wrapper exits nonzero for this result and does not write a success runner
report; preserve images, log and `capture.json`. [The evidence packet](../../art/ten-rounds-oct23/vfx/README.md)
records the failed outcome and observed-failure hash receipt. It also preserves
the earlier windup/caption/shadow-control findings and the one actual correction.

The separate geometry diagnosis runs without rendering:

```sh
godot --headless --path games/yuga-native \
  --script res://tools/reuse-vfx-stage/analyze_floor_occlusion.gd \
  -- --capture=/absolute/capture/capture.json --report=/absolute/writable/diagnosis.json
```

It iterates actual indexed triangles, clips against the existing opaque floor,
and preserves the original conservative-AABB failure. It does not replace an
actual visual review. `verify_capture.py` verifies advancing-frame pixels and
source hashes separately; use `--receipt` when reviewing the explicitly recorded
failure receipt instead of a missing success `runner-report.json`.

Before integrating, review all three controls and moving flames at normal game
distance; set physical scale; author a lower-cost source prop; review the original
model/output rights intake; connect the existing game clock, camera and settings;
then test over the actual courtyard. No final-art or complete-game gate is closed
by this isolated stage. See [source notices](NOTICE.md).
