# Friendly-unit camera readability

The actual W2 gate approach revealed a Sun spearman completely covering Rama.
The new helper makes a nearby friendly unit partially transparent only while its
existing articulated geometry intersects the camera-to-Rama torso segment.
Rama becomes readable while the ally retains a faint visible silhouette.

This reuses Godot's per-instance `GeometryInstance3D.transparency`, the existing
unit meshes/materials and their articulated local bounds. The helper does not
hide or remove units, edit materials, change poses/colliders, select targets,
alter damage or modify enemy presentation. Friendly collision bodies deliberately
use layer 0, so a physics raycast would not find this visual obstruction.

The current rule is for **offline Sun allies in the Forward+ desktop renderer**.
It is not a team-agnostic online or mobile-camera implementation.

## Implemented behavior

- Existing mesh instances are cached with weak references, bounded by the
  army's 96-node cap and 128 instances per unit. The actual nearby part AABBs
  are tested in their own local space along the camera-to-torso segment.
- Fade enters at six units/second, stops at 0.82 transparency, and restores at
  four units/second. Small entry/exit margins reduce boundary flicker; one update
  is capped at 0.1 seconds. Existing per-instance transparency is preserved.
- Reset restores the exact initial values and releases the cache immediately
  on pause, overview, travel, army reset, accepted return and scene exit.
- The public read-only `friendly_camera_visibility_report(detailed=false)`
  reports counts; optional details identify affected units and mesh opacity
  ranges. The gameplay update does not generate detailed diagnostics each frame.

## Evidence and acceptance

The root reviewed all three original Forward+ software-rendered views:

| View | Actual result |
| --- | --- |
| [Baseline](paired-r1/01-baseline.png) | The existing spearman obscures Rama. |
| [Friendly fade](paired-r1/02-friendly-fade.png) | Rama's full body is readable; the ally's faint body, shield and spear remain visible. |
| [Restored](paired-r1/03-restored.png) | Restoring original transparency restores the original obstruction. |

These are an explicitly **staged matched comparison**, using the recorded R1
camera and one repositioned existing spearman. They do not recreate the old
unrecorded unit placement or establish ordinary input. All 30 units are retained.
The camera, 164 hero bone poses, all unit poses and army/hero authority reports
match across the three views. One Sun unit's 22 mesh instances change opacity.
The frozen HUD still reflects its staging origin; it is not map-route evidence.

[The original report](paired-r1/report.json) and [wrapper](paired-r1/wrapper.json)
retain the exact sources and 46.03-second capture duration. That is software
capture wall time, not a hardware frame-rate claim. Exact pre-promotion source
files are retained under `source/`; the accepted helper bytes were moved to the
canonical scripts directory rather than kept as a second active implementation.

The R1 wrapper's optional hero-file entry used a nonexistent nested path and
therefore did not pin that GLB. The future runner now uses the correct path.
The current Rama GLB was checked afterwards against HEAD and remains
`db4b2ec7…`; [execution.json](execution.json) records this as a postrun check,
not an original capture-time pin or a new hero-art qualification.

- [17 actual-unit headless checks](cases-canonical-r1.json): friendly/enemy
  separation, shared-mesh independence, unchanged authority, depth/range,
  smooth enter/restore, existing alpha, disable/removal, invalid delta, bounded
  hitch and 30/60/120 Hz endpoints.
- [12 actual-world lifecycle checks](integration-r1.json): normal world process
  entry and immediate pause, overview, army reset, teleport, restart and exit
  cleanup. These use arranged camera/ally positions and are not input evidence.
- W1 independently reviews all five infantry/vehicle roles and canonical wiring.
  Its separate packet owns that evidence; W2 owns the subsequent ordinary-input
  retry on the complete integrated source.

Run the bounded headless checks from the repository root:

```sh
godot --headless --path games/yuga-native \
  --script res://tools/reuse-camera-readability/cases.gd -- \
  --report=/absolute/scratch/unit-checks.json
godot --headless --path games/yuga-native \
  --script res://tools/reuse-camera-readability/integration_cases.gd -- \
  --report=/absolute/scratch/integration-checks.json
```

Continuous rendered motion, human readability/feel and physical-GPU performance
remain distinct from these geometry/property checks and three reviewed stills.
