# Actual floor-artifact isolation

The finite actual-scene probe in `probe-r1/` **confirms directional floor
self-shadow acne** in the new lower-bias candidate. This supersedes the
provisional hypothesis in `read-only-diagnosis.json`.

Both scenes use identical frozen skeletal pose, camera, materials, exposure and
scene time across four variants. Only the recorded shadow controls differ.
The run completed eight real 1280 × 720 Forward+ frames with 481 unchanged
source pins and nine fresh source/import pairs, on software Vulkan. Its runner
validated image hashes and matched view/pose/exposure state. No runtime source
or asset was edited by this probe.

The original eight-image probe log includes an **ObjectDB leaked-at-exit
warning**. It is not a warning-free render. Later verbose headless diagnosis
isolated a stopped music WAV/playback still awaiting Dummy mixer retirement.
The probe harness now includes explicit retirement time and passed a parse
check, but these eight rendered views were **not rerun**. Their capture-time
tool source is preserved under `probe-r1/tool-source/`; raw reports/images/logs
are unchanged. See `../harness-cleanup-r3/` for the separate clean 146-case
headless teardown verification, not a new visual acceptance.

| Variant | Actual observed result |
| --- | --- |
| New candidate bias 0.025 / normal 0.35 | Strong radial bands reproduced on both floors. |
| Only former bias restored | Strong title bands removed; world bands substantially reduced, with some faint distant pattern. Hero/building shadows remain. |
| Sun shadows disabled | Bands removed; the hero cast shadow also disappears. Diagnostic only. |
| Only ground casting disabled | Bands removed while hero/building shadows remain. Ground still receives them. |

Ground casting was changed only on five courtyard meshes (four `FLOOR_BEVEL_*`
groups and `COL_Limestone_mortar`) or two world meshes (`FlatCityPaving` and
`NoncollidingTerrainApron`). It did not hide meshes or change collision.

Actual GLB inspection also shows courtyard slabs at Y=0 over foundation
Y=−0.002000004. World code creates one paving plane Y=0 over an apron Y=−0.18.
Courtyard floor texture imports generate mipmaps; Confluence paving is a
procedural shader without texture sampling. Because the exact floor appearance
changes when only shadow casting/bias changes, neither missing mipmaps nor an
intentional concentric texture explains this introduced artifact.

The smallest numeric repair is to restore the previous `0.035` bias and normal
bias `0.7` (courtyard) / `0.55` (world), keeping the new colour/fill/fog. A more
targeted flat-floor repair is to disable casting only on those named ground
meshes during construction, preserving their receiving of other shadows. Do not
disable the sun's shadows globally or introduce recurring scene-tree scans.
Root owns the correction decision and subsequent final visual/tests freeze.

The editable probe is `art/lookdev/capture_floor_probe.gd` with
`art/lookdev/run_floor_probe.py`. Its exact executed command, source/import/image
hashes and per-variant settings are in the raw reports. `probe-r1/review.json`
records the observations and limits; neither route is accepted across all
cameras/day/night or on a physical GPU by this bounded probe.
