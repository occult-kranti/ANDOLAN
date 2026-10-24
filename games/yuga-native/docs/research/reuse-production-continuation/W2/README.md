# Ordinary-input Lanka gate qualification

The integrated `02031d2c` source completed the ordinary route, camera, menu and return sequence with **14 requested originals and 10 automatic originals**. Native Quit exited **0** after one explicitly recorded supplementary Return key release. The final driver had omitted that release edge; this is an assisted completion, not an unassisted automation pass. [Receipt](receipt.json), [exact actual output](actual-r2/archive.json), [32-check evidence review](tests/actual-r2-review.json).

The retained trace has 1,856 physics observations. All 645 nearby gate samples are grounded with clear static sightlines; both full approach/exit spans were crossed with a maximum adjacent physics displacement of 0.1000004 m. One ordinary Kodanda shot released; no enemy damage is claimed. The live camera fix faded real friendly units in 456 physics samples, with a maximum fade of 0.82. The [natural obstruction original](actual-r2/auto-friendly-occlusion.png) records `sun_bow_guard_3`, its position and all 24 live mesh transparency values in the accompanying JSON. Map and pause reset the fade.

This continuation reuses the existing XTest native-window driver and UI observer. The added observer records the real `CharacterBody3D` position, velocity, floor contact, slide collisions, spring camera, static-world sightline and ability events; it never assigns gameplay state. The controller sends actual keyboard/mouse events to its one owned X11 window. Starting from the normal title and Confluence spawn is required.

The requested route is spawn `(0,0,-112)` → Ghat entry `(-40,0,-112)` → gate approach `(-40,0,-64)` → north exit `(-40,0,-45)` → south exit `(-40,0,-64)`. One ordinary bow release, map/pause navigation, return to courtyard, settings/keyboard controls and native Quit follow. All coordinates use the existing map's metre/Y-up contract. Closed-loop input is automated; this is not a human playtest.

## Acceptance and retained failures

The route oracle requires actual contiguous travel through both approach/exit planes `z=-60` and `z=-48`, within two metres of lane center, at ground height, in each direction. Adjacent physics displacement over 0.5 m is rejected, over 98% of nearby samples must have native floor contact, and over 90% of moving nearby samples must carry ordinary movement intent. It is a bounded route check, not a substitute for source review of the observer and the native input chronology.

An independent W1 challenge found that the initial center-plane criterion wrongly accepted tiny center jitter, grounded traces above the gate, and movement with no ordinary input. These were meaningful oracle failures, fixed before rendering. The original failure and unchanged four-case independent probe are owned by W1. The tightened oracle passes those four cases and eight owner controls (empty, one-way, teleported, missing-physics, airborne, off-lane and paused traces are rejected).

Actual execution is recorded in the accompanying receipt; synthetic controls and headless parsing alone never establish traversal or graphical quality. The warm software Vulkan renderer and Dummy audio do not measure physical-GPU performance or listening quality.

The first actual take completed both spans and one ordinary Kodanda release, then failed the full navigation plan. Its driver held Tab through two slow software frames, allowing X11 autorepeat to move focus from the observed Return control to Quit before activation. The process exited normally through Quit, but the planned journey was incomplete. The correction uses the existing qualified helper's short press/release and waits for frames only after release. Exact original driver/observer bytes and all actual first-take output are retained under `failures/`; the original receipt remains failed.

The first actual approach also exposed an existing camera readability issue: an allied soldier passes between the shoulder camera and Rama and obscures him. It is visible in the original frame, and the army is not hidden to improve the capture. Static camera/capsule passage and polished moving-actor occlusion are separate gates. A future presentation-only ally-occlusion treatment needs its own visibility, enemy readability and transition review.

W6 subsequently integrated its reviewed, bounded friendly-camera helper. The second ordinary-input take observes that exact helper, alongside the new water-garden integration. All runtime source and imported resources remained unchanged during the take. Fourteen requested originals plus the natural obstruction frame were visually inspected. Existing empty streets, repeated materials and coarse hero/soldier detail remain visible; this check does not close the commercial graphics target.

At the end of R2, process frames kept advancing on the title with Quit focused and Return held: shutdown had not started. The ownership-checked [correction helper](../../../../tools/reuse-gate-input/release_pending_quit.py) sent only the missing ordinary XTest key-up; [its receipt](actual-r2/quit-keyup-correction.json) retains the exact before state, process/display identity, event time and source hash. Native Quit then returned 0. The exact executed driver and observer are archived under `source/`. The future driver now uses the existing complete short tap for Quit; that tool correction is separate from the executed R2 source. Its 421.959 seconds includes waiting at this held key and is not a performance result.

## Run

Only the assigned heavy-render owner should launch this command, after freezing native runtime source files. Use a fresh output and unused display. The runner preserves the inherited qualified caches and does not override CPU affinity or XDG paths.

```sh
LD_LIBRARY_PATH=/workspace/scratch/ten-rounds-oct23/runtime/runtime/usr/lib/x86_64-linux-gnu \
python3 games/yuga-native/tools/reuse-gate-input/run.py \
  --output /workspace/scratch/reuse-production-continuation/W2/fresh-take \
  --engine /workspace/scratch/ten-rounds-oct23/runtime-release/restored/godot \
  --runtime /workspace/scratch/ten-rounds-oct23/runtime/runtime \
  --display 177 --timeout 300
```

The runner stops only its owned engine/display, retains failures, hashes runtime and observer inputs before/after, and writes original framebuffers plus read-only per-physics trace. Source hashes, command, input events, exact output hashes and native Quit status belong to `run.json` for the actual take. No screenshots are staged by moving the hero or stopping the authority clock.

This route uses the default WASD, F1 and Escape bindings. The actual take records the inherited preferences and viewport; it does not erase a user's settings. A machine with different remaps needs its corresponding input plan. The current ordinary viewport is 960×540 physical with the existing 1280×720 logical canvas at 100%. Earlier 200% fixtures are separate evidence, not an ordinary settings control exercised here.

For the composed source, the observer also reads the existing world's `friendly_camera_visibility_report` API. It records inexpensive basic counts during physics and detailed actor IDs, team, position and live per-instance transparency at captures. One automatic capture observes a naturally occurring obstruction after fade reaches 0.7; it does not move the soldier, pause the world or set transparency. This provides an actual input witness alongside the camera owner's separately staged comparison.
