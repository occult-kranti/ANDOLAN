# Next motion tape — source-only preparation

Status: **not staged, not Godot-parsed, not preflighted and not rendered**. The Python runner's syntax was compiled without executing it. Root approved this separate270-frame/9-second plan after the bounded `5023b301` landing acceptance. It is outside the current release/checkpoint hold; W1's hair, package and shoulder queue takes priority. No engine or raster slot is reserved.

The prior full take contains only two walk samples and resets before the declared input release. This new sequence measures sustained walking, a natural run-to-stop, two lateral input directions and an ordinary airborne-to-ground transition. It leaves canonical motion, authority, capsules, roots, sockets and fixed plant anchors untouched.

| Frames (inclusive) | Declared operation | Purpose |
| --- | --- | --- |
| 000–014 | Settled idle | Opening reference after fixed public-start preroll |
| 015–074 | Forward analog input targeting2.4 m/s | Two seconds below the existing3 m/s walk/run boundary |
| 075–089 | Release forward | Natural walk deceleration |
| 090–119 | Forward strength1 | One second at the normal6 m/s run target |
| 120–149 | Release forward | One second of natural deceleration and settled stop |
| 150–179 | Left strength1 | Sustained controller-relative lateral movement |
| 180–209 | Release left; press right strength1 | Direction reversal and sustained opposite lateral input |
| 210–224 | Release right | Natural lateral stop |
| 225–269 | Jump press225/release226; settle | One actual native jump, landing and recovery without reset |

All intervals are measured consecutively at30 captured frames/s and60 actual physics ticks/s. The public `start_training()` call and its reset/teleport side effects occur **before** the measured interval, followed by a fixed30-draw settle. Failure to settle rejects the premise; the helper does not wait adaptively, reset again or reposition the actor. No teleport, velocity, pose, animation phase, action clock or anchor assignment occurs during the tape.

Walk strength is derived from the live mean `InputMap` movement deadzone: `deadzone + (1-deadzone) * 0.4`. Existing speed6 m/s predicts2.4 m/s. The helper records all four deadzones, applied raw strength and actual input vector, then requires at least48 actual walk samples near that speed. This is an execution-premise check, not an assertion that the gait looks good. If the premise fails, preserve the failed preflight and inspect input semantics; do not force velocity or relax the gait gate.

Left/right are intentionally named **input directions**. Current player code rotates the visual toward velocity when not firing, so these inputs may produce a turn followed by forward-oriented leg motion rather than sustained anatomical strafing. Both controller-local and visual-local velocity, controller yaw and visual yaw are recorded in every final-modifier observation. Facing is never pinned to manufacture strafe coverage. A separate aim/cast movement take would require an explicit later scope.

## Reused observation and new checks

`capture_locomotion.gd` inherits the exact sealed S3 transition observer, which inherits corrected `capture_focus.gd` and the existing final `modification_processed` observer. All164 global bone transforms, root/rig/capsule transforms, actual skin sole selection/distances/rays, projected soles, current camera, original image hashes, LOD, materials, secondary offsets, action/authority state and physics/draw counters remain in the compact raw JSON. Compact formatting removes whitespace only; it does not discard poses or floats.

Ten proposed coverage checks require the complete270 observations, adjacent native draws and two actual physics steps per sample, same-callback body/sole counters, full-body framing, sustained actual walk/run/lateral speeds, settled natural stop, one real jump/landing, unchanged reset generation and bounded root steps. No contact-quality or ankle-step threshold is introduced. Report all sole penetrations, anchor errors, release discontinuities, local-direction changes and outliers even when execution coverage passes. Existing strict26/27 limitations remain independent.

Use the prior full-body camera unchanged:1280×960, offset(−4.5,2.8,−5.9)m, target(0,1.5,0)m,48° FOV. It follows horizontal root position using the existing observer. This is a declared review camera, not a user-input camera or proof of toe-edge visibility at subpixel scale. Headless framing and actual first images must validate the longer route; an obstacle or cropped frame must be retained as a failed premise, not hidden by teleporting.

## Future staging and invocation

After W1 grants a short preflight slot and a stable accepted source freeze, create one private snapshot with canonical motion SHA `5023b301ff4c4585e3b6a22827f55f4696045bb0206374ee1656a5b4bad6e4a5` and source-verified imported caches. The exact later hero/world/UI source is not yet selected; this packet makes no claim that a stage exists. Copy these declared helpers into the private stage and include them in its marker:

| Stage path | Source |
| --- | --- |
| `tools/graphics-six/capture_transition.gd` | Sealed `docs/evidence/desktop-finish/S3/W5-capture-preparation/capture_transition.gd` |
| `tools/graphics-six/capture_locomotion.gd` | This packet's `capture_locomotion.gd` |
| `tools/graphics-six/locomotion-sequence.json` | This packet's `locomotion-sequence.json` |

Preserve the remaining corrected observer dependencies and record all marker/import/source identities. Supply a fresh stage descriptor with `stages.current.project`, `seal_sha256`, `motion_sha256` and the existing3 GiB free-space floor. Bind that descriptor in a fresh `render-inputs.json`, using the exact unmodified dce0422d engine and separately copied, verified Godot/Mesa seeds. The historical runner field is still named `--pair`, but this derivative admits only `--role current`: it is one current-source take, not a new baseline comparison.

Prepared command shapes (the bracketed identities/paths are deliberately unresolved until the private stage is frozen):

```sh
taskset -c 3 python3 run_capture.py --pair <frozen-stage.json> --render-inputs <frozen-render-inputs.json> --role current --case locomotion --preflight --cpu 3 --output <fresh-preflight> --timeout 180 --progress-timeout 180
taskset -c 0,1 python3 run_capture.py --pair <frozen-stage.json> --render-inputs <frozen-render-inputs.json> --role current --case locomotion --render --cpu 0,1 --display 188 --output <fresh-originals> --timeout 900 --progress-timeout 900
```

CPU selection must follow the then-current W1 queue; these are not launch authorization. The runner is a small derivative of the sealed bounded runner: new case, current-only role, new helper entry and fixed30 capture cadence. Its source derivation is pinned in `derivation.json`. It preserves source/engine/cache identity checks, private caches, cleanup and the original900-second maximum. No unsupported worker-count flag or hidden quality/FPS reduction is added.

The earlier120-frame full take averaged0.767 MB per PNG (largest0.795 MB), with20.5 MB of seed files. At that observed scale,270 PNGs are about207 MB (215 MB at the prior maximum); allow40 MB raw capture plus cache growth/logs. A fresh source/cache child plus outputs and a second archival copy should be budgeted **under1 GiB additional**, subject to actual source freeze and free-space checks. The runner retains3 GiB free floor plus512 MiB start allowance. Prior rendering cost predicts roughly490–550 seconds, not a measured promise;900 seconds is the unchanged bound. Preserve failure on timeout rather than silently cutting frames.

After actual completion, archive every PNG and the complete JSON losslessly with hashes; derive a30 fps viewing video without interpolation. Independent review should inspect start/walk cycles, final run samples and all deceleration frames, both direction changes, and airborne/landing neighbors at normal speed and in original adjacent images. Do not promote coverage gates into visual acceptance. This packet remains excluded from the present checkpoint until separately requested.
