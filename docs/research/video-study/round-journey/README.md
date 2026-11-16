# Normal-wave core outcome reachability

Task `NATIVE-ROUND-JOURNEY-01`, 16 November 2026. Product: native offline YUGA. Baseline `work/yuga-studio@7162b5d0b666e4422b0bc73100e1fba947d3323f`, preserving other workers' uncommitted changes. This worker owns the new [test](../../../../games/yuga-native/tests/native_round_journey_cases.gd) and this receipt directory; no authority/runtime source was edited.

**Accepted scoped result:** the normal three-lane army and configured Rama ability kit can reach a real Sun core outcome under scripted hero intervention. The first run finished at **151.8 simulation seconds**, after **3,036 × 0.05-second steps**. Moon core reached 0, Sun core remained 100, and twelve normal middle-lane arrivals supplied the core damage. The test never assigns core/unit health, winner, route progress, damage tuning, cooldowns or rewards.

| Actual observation | Result |
| --- | --- |
| Checks | 9/9 passed, exit 0 |
| Total process wall time | 7.485 seconds |
| Child CPU time | 7.328 user + 0.074 system = 7.402 seconds |
| Bounds | Maximum 1,800 simulation seconds and 20 seconds of internal wall time; launcher CPU hard limit 30 seconds |
| Ability requests | 35 accepted, 35 released; Piercing Dawn, Dawn Volley and Guardian Circle |
| Actual damage | 38 accepted troop-damage receipts, 2,205 damage applied |
| Actual support | 399 guardian receipt entries across real field updates |
| Earned currency | 22 confirmed hero last hits exactly explain 614 gold; no reward injection |
| Final core outcome | One Sun outcome event, cores Sun 100 / Moon 0, arrivals `[0,12,0]` |
| Normal army behavior | Six normal wave events; peak 69 live and 69 total unit nodes; finite state, zero invalid damage/steps/pulses and zero blocked route moves |
| Terminal adverse check | New kit cast rejected; twenty further army steps changed no elapsed time, core health or gold, and emitted no duplicate outcome |
| Source integrity | Seven selected runtime/rule/manifest files plus the test remained unchanged |

The reviewed existing `lane_army_cases.gd` already contains a 20-minute symmetric boundedness soak and a separate arrival fixture that directly stages troops near endpoints. Neither requires a naturally completed round. This new test leaves all normal troops' positions/progress, paired waves, arrivals and combat rules alone. Every actual core-health reduction is checked against increased arrival count in the same simulation tick. It challenges normal completion with real configured kit effects instead of substituting the old endpoint fixture.

Hero intervention is an explicit automation fixture: whenever a configured power is eligible, it selects a real middle-lane Moon front or Sun ally and supplies a planar origin behind that unit to `kit.request_ability`. The complete origin/target/request trace is retained in [round.json](round.json), together with 30-second army checkpoints, event counts and confirmed last-hit identities. Existing action locks, cooldowns, cover/ground validation, projectile sweeps, receipts and guardian effects remain active. Primary Kodanda and Measured Step are omitted; this avoids implying that a direct kit request enforces magazine/reload or mounted traversal eligibility.

This is **not** a human or mounted full-world journey. There is no actual OS input, physics navigation between origins, incoming hero damage, audio listening, rendered image review, online authority or hardware-FPS claim. Instant scripted relocation is stronger than ordinary movement. The 151.8-second result is a reachability example, not a normal match-duration or balance target. Only one deterministic Sun outcome was exercised; Moon victory/draw and the new result-page interaction flow remain separate acceptance work.

Exact executed command, with four-core process affinity and a fresh data directory, is recorded in [execution.json](execution.json):

```sh
XDG_DATA_HOME=/workspaces/scratch/yuga-native-round-journey-20261116-r1/user \
  godot --headless --path games/yuga-native \
  --script res://tests/native_round_journey_cases.gd -- \
  --report=/workspaces/scratch/yuga-native-round-journey-20261116-r1/round.json
```

The [manifest](manifest.json) pins test/receipt bytes and baseline; [round.json](round.json) binds all selected tested source hashes; [round.log](round.log) retains the actual engine/check output. No failed run occurred in this bounded test. Root is the next owner for integrating its interpretation, actual world input/capture evidence and result-flow work. Do not label this authority-level trace as a complete human-played match.

## Prepared native capture fixture, not executed

Root requested a separate [capture fixture](../../../../tools/capture-round-result.gd) for the shared Forward+ render lane. It mounts the actual Confluence world and existing metrics recorder, freezes automatic world/player/army physics, directly logs/stages the actual player root, and requests the same three powers through the configured kit. It deliberately avoids `teleport_to`/`player.reset`, which would refresh combat state. Original muzzle, siege damage, death/respawn, core outcome and metrics callbacks remain connected. Default gate/garden footprints are retained; any existing additional district is reported only if available. Relay capture/supply is not advanced or injected by this fixture.

The prepared command is:

```sh
<reviewed-render-engine> --path games/yuga-native \
  --script /workspaces/ANDOLAN/tools/capture-round-result.gd -- \
  --output=/fresh/absolute/result-capture-directory --restart
```

Root must provide its owned display/render environment. The output directory must not already exist. A natural army outcome and completed matching metrics are required before the result PNG is captured; a 1,800-second simulation / 30-second internal wall budget preserves an explicit failure receipt if the mounted world cannot finish. `--restart` invokes the actual restart action afterward and captures cleared metrics/result visibility. No outcome is fabricated to obtain a screenshot.

Only Godot `--headless --check-only` was executed for this fixture. The first parse found an inferred-type error; that original and output are retained. The corrected [R3 parse](capture-fixture-parse/r3-parse.json) exited 0 with source hash `3eb18c0def4f4f19eb2946f14bb3067669e30a215da2e834fa7b3c4641de8a53`. **No rendered capture or mounted-world fixture outcome has been established.** Absolute-script loading with `--main-pack` is designed to use runtime resources without a test dependency, but package execution is also unrun. Root owns execution, image inspection and any subsequent bounded correction.
