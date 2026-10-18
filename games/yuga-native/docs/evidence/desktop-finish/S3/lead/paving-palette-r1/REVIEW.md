# S3 — quieter courtyard paving

The lead and W2 reviewed both actual daylight title/training pairs and accepted a bounded palette refinement. The training floor has less checker contrast, keeping attention on Rama and the targets; the title change is subtler. Stone joints, shadows and separation from the architecture remain visible. Broad plain paving, seam aliasing and the remaining character/environment quality gap are still open.

Only four stone tint vectors in `environment_surface_finish.gd` changed. Maps, UVs, masonry shader, geometry, exposure, light, cameras, pose and clocks were preserved. Each complete before/after shot record differs only in the image SHA. The original [title](native/00-title.png) and [training](native/01-training.png) are untouched 960×540 captures; compare with the [S2 originals](../../../S2/W1/scene-anchors-r1/REVIEW.md). No image repainting or postprocessing was used for the comparison.

The actual Forward+ run completed in 120.407 seconds, exit 0, with two originals. It used the installed Godot4.6.3 engine on llvmpipe, CPU3, with copied Godot/Mesa cache while the independent source-engine build occupied CPU0,1. Wall time is not hardware FPS. The preserved source/command/snapshot/logs and [comparison](comparison.json) identify every input. The copied Godot seed is recoverable from the retained S1 seed plus the two new payloads in this directory's delta archive.

The exact tested helper was integrated at SHA256 `eb4335695318daedc578cc9cd7e8424d329896b36149e786ae473346b642726a`. This accepts the daylight tint change only. Night, continuous motion, OS-input play, cold launch and physical-GPU/commercial-quality acceptance remain separate gates. This staged API capture also predates the later S3/S5 compact interface changes.
