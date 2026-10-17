# Traversal/army stress — binding fixture migration

17 October 2026. The full CI run for `eedc653ddf34d6782615d475c32542f92c6db4e2` failed two assertions that still required thirteen remap buttons. The preserved [failed job log](ci-eedc-failed.log) and [receipt](failed-ci-receipt.json) identify that source and its exact failed test hash.

The current overlay has **14 remappable keyboard actions**; fixed LMB fire is the fifteenth gameplay control. `traversal_army_stress.gd` now declares the complete expected keyboard action set, compares the actual button keys with that set, and checks its cardinality. The original `viewport.encloses(card)` assertion remains. Its release helper also releases every declared action plus fire. No UI or runtime code changed for this correction.

The complete rerun passed **36/36**, exit 0, with no engine errors or warnings. It observed 1,187 actual physics frames and completed the 24,000-tick accelerated army soak. Both controls-card checks pass:

| Viewport | Actual card position | Actual card size | Remap buttons |
| --- | --- | --- | ---: |
| 1280 × 720 | (300, 16) | 680 × 688 | 14 |
| 960 × 600 | (140, 16) | 680 × 568 | 14 |

[stress.json](stress.json) retains every assertion and fifteen exact source hashes. [stress.log](stress.log) contains the engine output. [summary.json](summary.json) records the command, two-CPU affinity, source verification and artifact hashes. The headless run used fixed 60 FPS and isolated user data after coordination with QA. No editor import or renderer was started. This validates the bounded fixture and integrated simulation checks; it is not actual OS-input or visual acceptance.
