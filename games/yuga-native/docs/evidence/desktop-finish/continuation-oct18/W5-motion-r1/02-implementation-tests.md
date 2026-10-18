# Private landing continuation: implementation and tests

Canonical motion remains exact `5023b301`; no runtime, asset, catalog or gameplay source was promoted. Private `rama_motion.gd` is `997bfb18add769c43dcfaf482c8b1677b620c5c7a5a1143b1b3310332bdaad11`. This is **inactive: endpoint accuracy improved, smoothness unresolved**.

The preserved first candidate `candidate-3a0.gd` completes preparation when remaining descent reaches the bounded extension. The successor additionally reserves one existing physics update of downward travel, capped at 290 mm completion clearance, leaving at least 160 mm of easing distance. It rejects nonfinite velocity/delta and delta outside (0, 0.1]. Target height still follows the actor, extension stays at most 160 mm, fresh per-foot support validity remains required, and the 100 ms whole-body land transition and normal foot-lock admission remain unchanged. The full delta from canonical is `canonical-to-successor.patch`; `candidate-timestep.patch` isolates the successor from 3a0. The solved pose may become the next transition snapshot; there is no additional stored preparation state.

| Retained execution | Result | Interpretation |
|---|---:|---|
| 3a0 natural270 headless, exact inherited60Hz physics/30Hz capture | 10/10 coverage; 9/9 differential | First grounded soles 0.590/3.246 mm versus canonical111.422/75.347 mm. |
| 3a0 fresh-support interruptions | 12/12 | Actual imported rig; valid extension plus owner/shape/layer/root/footprint and action/aim invalidations. |
| First new component fixture | 7/15 | Preserved fixture failures: float32 capped root compared to double never admitted ground in ordinary cases; positive hover reduction was incorrectly treated as deeper penetration. |
| Corrected component fixture, same 3a0 | 14/15 | Real remaining30Hz failure: first contact30.532/26.243 mm. No threshold changed. |
| 997 same five component pairs | 15/15 | 30/60/120Hz update rates, elevated60Hz and low60Hz first contact all≤1.411 mm. Actual near-rig skin; prescribed root states, not native collision authority. |
| 997 fresh-support interruptions plus invalid inputs | 16/16 | Original12 plus nonfinite velocity, zero/nonfinite/oversize delta. |
| 997 natural270 headless | 10/10 coverage; 9/9 differential | First grounded0.589/0.589 mm; exact root/capsule/input/authority/clocks, nonleg matrices and lock schedule. |

Both natural takes use identical retained96d5 runtime/helper/input/import closure apart from motion and their declared snapshot marker. Canonical motion matches current a7 source, but the historical whole stage is not relabeled current a7. Natural minimum signed sole remains −3.796 mm; no deeper sampled penetration. Changed final poses are limited to leg bones in frames248–252. Headless first ground is250/physics589; the previous actual take first grounds at249/587. These are not interchangeable observations.

**Temporal concern remains substantive.** The component's maximum sampled local knee step at30Hz rises from24.22° with3a0 to45.86° with997 per33.3 ms; corresponding ankle displacement rises307.25→347.16 mm, including shared root descent. At60Hz updates the local knee peak rises29.34→33.67°, while at120Hz it falls32.78→27.59°. These maxima cover every retained30Hz pose evaluation, not unseen intermediate rendered poses. In the natural60Hz take, maximum adjacent global leg rotation during the last airborne interval improves19.28→15.53° and left ankle descent316.98→291.75 mm compared with3a0, yet grounded leg rotations remain about11°. Endpoint checks do not establish a smooth knee/cloth transition. `component-kinematics.json` and `adjacent-metrics-r3.json` retain axes, joints, rates and witnesses.

The first natural attempt used an unsupported FIFO destination; Godot failed `FileAccess.open` at serialization and the180s watchdog ended it. Its log, empty gzip and exact runner are retained in `failed-fifo-r1`; it provides no pose evidence. Corrected runs use the existing regular compact report, each15.71 MB (<20MiB), then deterministic streaming gzip, exact round-trip SHA verification and authorized removal of only that newly generated raw duplicate. Both corrected natural executions exit0 clean in112.45/111.26s. These wall times are headless execution observations, not game FPS.

All finite logs, original reports and failed cases remain losslessly archived. No runtime changes were made to hide a failure. Prior26/27 comparative limitation and canonical actual100ms settling remain open. No new images or human full-speed review occurred.
