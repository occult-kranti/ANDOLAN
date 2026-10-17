# Practice AI component verification

Status: **PASS for the isolated grounded decision component; integration OPEN.** No second native hero, rendered practice opponent or online bot match is implemented by this work. This is supporting production code for the future admitted actor, rather than a separate game or substitute avatar.

Source base: branch `game/yuga-native-production`, HEAD `1ab1f5e330d256a6ffb6a5706a07f2ff8c3bbb0e`. The new component/test were uncommitted at execution. The final report pins their exact SHA-256 values and six actual dependency sources, so the base commit alone is not the tested source identity.

## Three bounded rounds

1. **Contract and actual-source audit.** Reviewed current player/runtime, actual kit/army/geometry, practice receiver, rules and native replication audit. Root approved component-only ownership. Agreed that the future admitted actor supplies perception and applies requests through actual movement/reload/kit APIs; the brain grants no movement, ammunition, cooldown, health or damage itself.
2. **Implementation and counterexamples.** The earlier focused suite passed 45/45. Its exact executed source is retained under `before-review/`; the source snapshot was reconstructed from the subsequent narrowly changed source and verified against the earlier report's SHA-256 before archiving. A read-only peer review then found one tactical issue: two enemies behind one another on one first-hit Volley lane were counted twice. The earlier 45-case pass did not detect this.
3. **Correction and final checks.** The final component counts unique nearest receivers across the three Volley lanes. Its exact collinear-target negative case now chooses Piercing Dawn; the spread-lane positive case still chooses Volley. Added stricter generation, same-clock tick, unknown payload, movement-cover and unapplied-turn checks. The final suite passes **52/52**, clean exit 0 on Godot 4.6.3. Independent closure is archived alongside the original finding.

## Executed verification

```sh
godot --headless --path games/yuga-native --single-threaded-scene \
  --script res://tests/rama_practice_brain_cases.gd \
  -- --report=/tmp/rama-practice-brain-r4/report.json
```

The coordinated lightweight run completed in about 0.24 seconds. It loaded no GLB, editor import, actual renderer or commercial resource. `final/report.json` and `final/run.log` are copied from that execution; `final/*.gd.txt` preserve the executed component/test text. The report checks:

- Delayed first movement, aim and fire; turn-rate and request-cadence limits.
- Actual slab geometry blocking sight through a 1 mm wall; immediate release of hidden targets; a separate actor-width movement corridor check.
- Friendly/dead/unobserved/rear/elevated/out-of-range exclusion, deterministic tie/retention and replay.
- Neutral pause/end/death/airborne state; bounded finite input/callbacks; stale/duplicate/invalid identity and generation; strict reset generation advance; callback reset/reentry and detached input/report data.
- Actual cooldown/action hints, reload intent, Guardian/Step selection and distinct first-hit Volley selection.
- An explicit caller submitting one proposed primary action through the **real Rama kit and practice army**, resulting in exactly one 28-damage hit. Brain decisions alone leave target health and kit cast counts unchanged.

## Remaining acceptance gates

The future actor owner must supply player-equivalent authority, current map/cover/navigation adapters, actual movement/collision/reload and Rama event presentation. Transformed-map integration, complete route finding, multi-actor death/reset, target/damage rules, full encounters, perceived fairness and human balance are unverified. Native online additionally needs the authenticated native authority and action replication described in the replication audit. No physical GPU, Windows execution, OS input, animation rendering, listening, Deadlock AI equivalence or completed game-quality claim follows from these tests.

The module is deliberately unwired. The root integration owner decides when its prerequisites are satisfied. No existing gameplay, browser protocol, old test, authority source or package was changed by this task.
