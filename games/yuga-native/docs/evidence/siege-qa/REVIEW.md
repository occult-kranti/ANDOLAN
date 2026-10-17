# SIEGE-05 independent combat and articulation verification

These are headless tests of the original offline native army. They do not establish rendered art quality, network authority, player damage, Windows execution or hardware performance.

The independent review used three rounds: challenge the committed-ground-target, cancellation, symmetry and cap contracts; run adversarial actual-simulation fixtures; rerun against the final source and pin the evidence. A separate read-only reviewer inspected attack lifetime and simultaneous damage paths. No runtime defect was confirmed in these paths.

## Final gates

- `army-final.json`: **31 passing checks**, including fixed-point dodges for both roles, new victims entering a blast after the original target is freed, source-death cancellation, 4 cm walls before and after commitment, victim-side splash occlusion, exact-once player rewards, 40 reset/drill transitions, outcome cleanup, simultaneous lethal trade, a 72-unit lethal burst during corpse retirement, 33 eligible cannons against the 32-shot cap without charging the rejected shooter, mirrored wave cadence and positive 72-unit capacity.
- `pose-final.json`: **27 passing checks** on actual `lane_minion` vehicle instances for both roles and teams. Each actor receives 601 pose samples. Checks cover finite transforms, stable node identities, collider geometry, wheel-axis/contact-center placement, actual recoil, death/reset dispatch and rejected invalid sample times. Emitted shot origins are compared to the actual cannon muzzle mesh or bolt apex at three headings under a translated and rotated parent.
- `lane-army-regression-final.json`: **21 passing existing regression checks** with the updated capacity fixture, preserving the original damage, reward, reset, lane, core, 20-minute soak and human-art checks. The final log contains no engine warnings or errors.

The 24,000-step soak advances **1,200 simulated seconds**, rather than counting frozen ticks after an outcome. It observes all five roles, 556 windups and 537 successful impacts, with all three lanes fighting and zero blocked static-route moves. Lifetime counters peak at 72 living units, 76 total units, 9 corpses and 20 queued attacks. Periodically sampled siege queue peaks at 5; the separate adversarial fixture reaches the enforced 32-shot limit. This elapsed simulation is not a hardware benchmark.

The burst fixture deliberately places units close together to force simultaneous damage and freed-corpse references. It tests bookkeeping under pressure, not normal spawn placement. The cadence fixtures explicitly clear existing units or reposition them along valid routes to expose capacity policy without waiting for natural battle deaths. Wheel contact checks cover transformed wheel centers and axes on a planar lane; they do not claim physical terrain suspension or rendered contact-shadow quality.

## Source and reproducibility

Final army source: `da777328b8fe299c24d59c9175cd4d845588c9090dd43935b4253741e2a1b58a`.
Minion: `ba2339640a133307a495619dc60621333afa655d7db878ca3312909994acf983`.
Vehicle art: `c2962a3aab0bc6b6c819ef6fbdb77cad36e85a4066f2205f32d3b9748641aa2b`.
Reports also pin the staged map and all other relevant sources, and fail if those files change during execution.

Run from the repository root with Godot 4.6.3 standard:

```sh
godot --headless --path games/yuga-native --script res://tests/siege_army_cases.gd -- --report=res://docs/evidence/siege-qa/army-final.json
godot --headless --path games/yuga-native --script res://tests/siege_pose_cases.gd -- --report=res://docs/evidence/siege-qa/pose-final.json
godot --headless --path games/yuga-native --script res://tests/lane_army_cases.gd -- --report=res://docs/evidence/siege-qa/lane-army-regression-final.json
```

The existing lane-army capacity test now checks the real third-wave outcome of 72 units and per-lane role/team parity. The old 70-unit intermediate expectation became obsolete when the mirrored cannon pair filled the remaining two slots.

## Retained attempt history

- `army-attempt1.log` records a test-author GDScript type-inference error before any test ran. The local test variable received an explicit Boolean type; no runtime change was involved.
- `army-attempt2.json` passed its initial 30 checks on the earlier `ac1b41ab…` army source. The final suite adds direct queue pressure and uses lifetime high-water counters.
- `pose-attempt1.json` passed 23 checks before the emitted-origin checks were added.
- `lane-army-regression-attempt1.json` passed 20 behavior checks and failed only `tested_source_unchanged` when the approved muzzle-origin runtime edit arrived during the run. Its failed report is preserved. The final regression uses the final frozen source.

UI, effects/audio, actual render and packaged executable reviews belong to their separate evidence sets. They are not inferred from these headless tests.
