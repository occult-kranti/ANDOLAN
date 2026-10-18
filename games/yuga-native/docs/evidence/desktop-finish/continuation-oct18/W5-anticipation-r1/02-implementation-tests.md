# Results: rejected and inactive

The fixed time-based trial reduces the measured rate-dependent airborne extension peak, but fails the strict low-speed contact endpoint and exposes a high-speed entry discontinuity. Root therefore rejected promotion. Canonical motion remains unchanged.

| Component case | First contact L/R, mm | Largest local joint step, degrees | Largest world ankle step, mm |
|---|---:|---:|---:|
| ordinary30Hz | 1.411 / 1.410 | 25.17 | 271.94 |
| ordinary60Hz | 1.411 / 1.411 | 25.17 | 268.64 |
| ordinary120Hz | 1.411 / 1.410 | 27.19 | 266.52 |
| elevated60Hz | 1.411 / 1.411 | 25.17 | 268.64 |
| low60Hz | 1.411 / 1.410 | 25.61 | 68.92 |
| slow-low60Hz | **11.483 / 7.921 — FAIL≤5mm** | 26.81 | 46.86 |
| slow-elevated60Hz | 1.411 / 1.411 | 25.17 | 46.86 |

The21 predicates comprise three per case: endpoint≤5mm, exact root/clock/nonleg/anchor controls, and no extra negative penetration with the existing−5mm floor. Result **20/21**, clean18.89s. The slow cases prescribe0.1m/s descent from30mm at zero acceleration. Their float32 world positions cross the prescribed cap on different evaluation samples; this is a useful timing counterexample, not a claim about native collision behavior. The failing endpoint is preserved, with no threshold relaxation.

Every component updates at its declared30/60/120 rate but evaluates poses at30Hz. `rate-comparison.json` retains maxima over all these evaluations. Airborne local-joint peaks change from997's45.86/33.67/27.59° to20.68/20.05/18.26° for ordinary30/60/120. The new overall maxima in the table occur after grounding. World ankle motion includes the identical ballistic root displacement. These are finite geometry measurements, not a human smoothness or rendered-knee assessment.

**16/16** support guards pass clean4.79s: valid preparation, moved/deleted owner, moved/disabled/removed/resized shape, collision-layer removal, moved root, animated footprint mismatch, action/aim activation after query, and invalid velocity/delta. Existing safe ownership does not remove the timing failures.

The independent W6 review identified the capped-ray seam: at20m/s, a first hit just inside1.2m occurs with a positive precomputed weight. The new actual imported-rig query witness at root1.19m measured **105.027mm left-ankle extension on first admission**. At1.21m the ray misses and extension is zero. This reproduces an abrupt boundary; the6/6 geometry checks are not a smoothness pass. They also confirm freshly moved support at+0.1m, rejection of a tilted normal, a low-speed ray miss, and rejection when the animated left foot exits its20mm-wide support after the hit. Detailed before/after poses and query planes are retained.

The first boundary fixture had a Variant inference parse error and never simulated. Its exact source/log/receipt remain `probe_limits-parse-failed.gd` and `probe-r1`. A bool annotation alone fixes it; `probe-r2` finishes6/6 clean2.18s. Candidate bytes do not change between runs.

All engine invocations used the pinned e69 executable, CPU3 affinity and LP/OMP/BLAS/MKL1; no Godot worker-pool cap is claimed. They loaded the private script explicitly against existing frozen near-rig resources, without import or canonical writes. Full small reports are losslessly gzipped with raw and compressed SHA/size records. No report exceeds20MiB. No new natural270 run, raster, image or video was generated.
