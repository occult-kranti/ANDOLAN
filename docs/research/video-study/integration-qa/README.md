# VIDEO-INTEGRATION-QA-01

The selected native offline integration checks have **387 passing assertions** across eight focused suites. This packet records headless simulation, native Control data and viewport key dispatch. It does not establish rendered readability, OS-window input, listening, GPU performance or a packaged release.

Baseline commit: `7162b5d0b666e4422b0bc73100e1fba947d3323f`, preserving the shared dirty checkout. [The machine-readable review](qa-review.json) binds reports, exact commands, source hashes, retained failures and the final source comparison. [The first run](existing-suites-index.json) and [final affected-boundary reruns](final-boundaries-index.json) retain their separate source identities.

| Focused suite | Assertions | Selected passing report |
| --- | ---: | --- |
| Actual ability kit, damage and vitals lifecycle | 85 | [Rama abilities](rama_ability_cases/report.json) |
| Actual mounted hero integration and pause/reset matrix | 138 | [Hero integration](rama_hero_integration_cases/report.json) |
| Actual siege simulation and cancellation/receiver rules | 31 | [Siege army](siege_army_cases/report.json) |
| Saved bindings, remapping and malformed settings | 44 | [Input bindings](input_binding_cases/report.json) |
| Disabled/hidden/disposed focus recovery | 26 | [Focus recovery](ui_focus_recovery_cases/report.json) |
| Full title/practice/modal/pause/result navigation | 19 | [Pause navigation r4](ui_pause_navigation_cases-r4/report.json) |
| Siege menu, bound shop entry, focus traversal and lifecycle | 25 | [Siege UI r3](siege_ui_cases-r3/report.json) |
| Independent mounted shop/damage/result counterexamples | 19 | [Shop/result r2](shop-result-counterexamples-r2/report.json) |

Each suite ran with a separate `XDG_DATA_HOME`. At most two headless processes ran concurrently. No import, renderer or export was launched. Both multi-suite source comparisons passed unchanged during their respective runs. The only initial-to-final changes in the monitored closure are root's `confluence_world.gd` pause correction and the two explicitly assigned test expectation changes. The final tested world hash is `cf58bec7c5379bbfaac52efd3c7a4a049fd8cda70e8cd907c54200f3a9e0674e`.

The mounted counterexamples use actual F4 viewport key dispatch to open the real shop, actual army siege signals and the mounted hero damage receiver. They verify damage while shopping; replayed-ID, cancellation, friendly/nonimpact, invalid radius and distance rejection; an actual buy/heal without erasing recorded damage or fabricating earned gold; genuine pause/overview suspension; and Sun/Moon/draw terminal ticks. Each terminal result's elapsed time, cores, earned gold, confirmed lane last hits and chart samples equal the recorder/army reports, and result presentation does not change that frozen state. Core endpoints are explicitly staged test fixtures; no runtime source/authority was changed by this QA probe.

The initial failure receipts remain intact:

- [Original siege UI](siege_ui_cases/report.json) failed two checks expecting thirteen pause actions. The original shop adds a fourteenth. Root granted the test update; it now requires fourteen actions **and** the exact Field shop entry using its current binding. The existing traversal, wrap and scroll checks remain.
- [Original pause navigation](ui_pause_navigation_cases/report.json) expected a fixed zero scroll after the result grew. Root approved replacing that implementation-specific expectation with visible result heading, correctly focused Restart and visible Restart.
- [The stronger r2](ui_pause_navigation_cases-r2/report.json) still failed. [Diagnostic r3](ui_pause_navigation_cases-r3/report.json) found a real carried-scroll problem after prior modal/volume navigation: result heading y−22..9 was above viewport y34..506 while focused Restart remained visible. [The isolated fresh-world probe](terminal-focus-probe.json) was a counterexample to assuming all terminal entry failed: it kept both visible at scroll50.
- Root corrected fresh pause entry to reset prior scroll while modal returns preserve opener context. The independent final r4 passes the complete prior-modal sequence, and all 63 affected pause/siege/shop/result boundaries were rerun against that corrected source. This agent made no runtime, packager or contract edits in this QA task.

One warning remains recorded: pause-navigation r4 logs `ObjectDB instances leaked at exit`; diagnostic r3 before root's fresh-pause correction logs the same warning. No attribution to the correction is established. The other selected logs contain no `ERROR:`, `SCRIPT ERROR:` or `WARNING:` diagnostics. The passing assertions are not a warning-free lifecycle qualification.

After these source-bound checks, root reported a concurrent Sangam/content10 migration outside this task's ownership. This packet does not validate that migration or relabel the earlier content9 source checks as content10 evidence. The integration owner must bind any subsequent package/export to its actual stabilized sources.

Changed product tests: `games/yuga-native/tests/siege_ui_cases.gd` and `games/yuga-native/tests/ui_pause_navigation_cases.gd`, with exclusive root authorization. `git diff --check` for both passed. New probe/runner/reports live only in this directory. Actual visual/input review remains root's rendered/package lane. Next owner: root.
