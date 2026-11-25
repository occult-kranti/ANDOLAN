# Independent Hanuman ability verification

The native courtyard passed **111 checks at each of two fixed frame cadences** in Godot 4.6.3. The two reports were byte-identical, including the source hashes, all ten per-ability timelines, release animation samples and recipient outcomes. The report pins the revised five-action animation library, Hanuman GLB, ability and presentation definitions, input bindings, courtyard scene and affected runtime scripts. [Integration receipt](QA-integration.json) · [Integration test](../../../tests/hanuman_ability_integration_cases.gd)

## Five abilities in the real trial

Each input traveled through Godot’s action dispatcher and the trial’s input handlers. The test opened the actual courtyard and used the Begin Practice button’s existing signal. It moved Hanuman using the movement action for Gada and used the actor’s normal camera method to aim on the headless backend. Tests used the existing opponents and ally. The combat clock advanced in 50 ms steps with regular actor physics frames between them. It received a single 50 ms delta in the full-effects pass and three deltas totaling 50 ms in the reduced-effects pass.

| Ability | Release | Authority impact | Recovery and end | Verified result |
| --- | --- | --- | --- | --- |
| Vajra Gada | 0.25 s | 0.25 s | 0.55 s and 0.55 s | The first enemy took 34 damage after moving into range. |
| Vajra Kavacha | 0.35 s | 0.35 s | 0.60 s and 0.60 s | The caster and the gold allied target each received 48 shield. |
| Maruti Udayana | 0.20 s | 0.20 s | 0.85 s and 0.85 s | Launch emitted the movement receipt. The collision-aware actor completed the clear 8.5 m path. Measured landing error was under 0.001 m. |
| Lanka Dahan | 0.45 s | 0.45 s | 0.85 s and 2.45 s | The first rear target took 28 initial damage and 16 through 40 exposure ticks. |
| Mountain Pulse | 0.70 s | 1.15 s | 1.65 s and 1.65 s | The target took 65 damage and the wounded caster restored 25 health. The animation reached the distinct landing marker on the impact event. |

All five reached their release marker on the corresponding event, refused immediate retrigger during windup, refused retrigger one clock step before their cooldown ended, and accepted it at the exact edge. Pause froze Mountain Pulse in flight. Cancel retired the pending landing, and reset rejected an old-generation landing event. Reset also stopped an airborne vault and restored the grounded actor. A recovered tail effect and landed mountain shared the field atlas, survived a reduced-effects toggle, and retired on their original boundaries. The 32-primary-cycle stress pass received 64 busy inputs and kept a bounded 64-entry combat history.

## Cross-checks and limits

| Suite | Passed | Failed |
| --- | ---: | ---: |
| Combat | 39 | 0 |
| Presentation | 20 | 0 |
| Ground field | 23 | 0 |
| Contact shadow | 12 | 0 |
| Launch and return | 30 | 0 |

The integration fixture mutes audio because it advances empty combat time much faster than audio wall time. The separate presentation suite reported the same 20 successful assertions with and without `--fixed-fps 60`. The accelerated run emitted a WAV resource teardown diagnostic. Repeating at the ordinary clock completed without it. The scoped suite receipts preserve the ordinary-clock presentation result and the fixed-clock diagnostic. Headless measurements establish action routing, animation markers, geometry and lifecycle. Visual polish, physical input, sound quality and hardware performance require their own capture and review. [Supporting suite receipts](QA-supporting.json) · [Accelerated audio diagnostic](QA-fixed-audio.log)

## Reproduce the two integration runs

Run from the repository root after importing the native project. Each run uses separate user data. The same Godot engine physics cadence is used even though the two commands supply different fixed frame settings.

```bash
qa_dir=$(mktemp -d)
for fps in 60 120; do
  XDG_DATA_HOME="$qa_dir/user-$fps" godot --headless --path games/yuga-native \
    --audio-driver Dummy --fixed-fps "$fps" --script res://tests/hanuman_ability_integration_cases.gd \
    -- --report="$qa_dir/run-$fps.json"
done
cmp "$qa_dir/run-60.json" "$qa_dir/run-120.json"
```
