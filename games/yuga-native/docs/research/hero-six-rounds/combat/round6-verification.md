# Round 6 independent verification

Task **YUGA-HERO-6R**, native desktop/offline. Base commit
`7162b5d0b666e4422b0bc73100e1fba947d3323f`, branch `work/yuga-studio`.
This receipt records the combat reviewer's checks; root owns final snapshot,
import, package, render and ordinary-input capture.

## Final Sangam encounter checks

After root completed import 30135, the independent probe passed **60/60** on
the final R6d district with **no warnings or errors**. The probe uses the actual
default imported world, native physics, actual Rama kit and staged receivers.
It independently derives all 43 army boxes, including the nine existing relay
plinth shapes. Fifty capsule sweeps cover both directions of all lane and
rotation segments. The four cover monuments stop primary, Pierce and all three
Volley pulses before a protected receiver; planned Step targets and Guardian
visibility obey cover. Gallery undersides are at 8 metres, with clear ground
routes and no planar overhead blocker.

```sh
godot --headless --verbose --audio-driver Dummy --path games/yuga-native \
  --script res://docs/research/hero-six-rounds/combat/sangam_encounter_cases.gd \
  -- --report=/workspaces/ANDOLAN/games/yuga-native/docs/research/hero-six-rounds/combat/round6/sangam-encounter-r6d.json \
  > games/yuga-native/docs/research/hero-six-rounds/combat/round6/sangam-encounter-r6d.log 2>&1
```

[Report](round6/sangam-encounter-r6d.json) SHA-256:
`6598e2ecbb7de6d12b86b5f12492d2a27d61fe868aa1765efb15e505526eb8f8`.

| Input | SHA-256 |
| --- | --- |
| Sangam GLB | `c29f403d894d183355e785442695f35369b28da57c057be28256ff90c2498a3e` |
| Sangam metadata | `439e43b4a1b0fc78daf1caea589b8b02888b0b0db949521a2015c175ba6cf0fd` |
| Sangam adapter | `4bc793ca04f17ef4e9f3e3e2992551a55b7c90ff1e3b7fd67ba9bf835654df1e` |
| Independent encounter probe | `f70480a89773070a80ec1aad1c1ce547aee1e75b3f2ec5d69abe92e94332690d` |

The older R6 encounter run also passed 60/60 but retained an audio-resource
reference at shutdown. Its original result/log remains. Probe cleanup now
stops background streams, releases the scene and drains the mixer; expectations
and runtime were not weakened or changed. The final R6d run uses that cleanup.
The earlier 58/59 and 59-check evidence remains: the independent fixture had
omitted existing relay plinths, subsequently derived from their real shapes.

Camera checks here are bounded 0.18-metre sphere sweeps. They do not establish
full spring-arm behaviour, ordinary input, balance, final pixels or GPU speed.
The provisional district R2 images were inspected, but root rejected that
capture's source validation after a concurrent HUD edit. They cannot be used
as final R6d visual acceptance.

## Frozen-source packaging provenance

Authored [freeze-sangam-source.py](../../../../../../tools/studio/freeze-sangam-source.py)
to copy a finite, verified packaging closure into a new review destination.
It retains complete runtime, notices, tools, tests, import cache and the actual
hero/contract dependency closure, without bulk-copying research video/audio.
It includes `art/.gdignore` and `docs/.gdignore`. It rejects symlinks, creates
independent copies, hashes before/during/after copying and rediscovers inputs
to catch additions/removals. It preserves failed destinations and never
initializes Git, copies Git configuration, changes sources, imports or renders.
Root executes the actual freeze and package.

The helper's completed marker binds the original branch, HEAD and dirty status,
runtime source digest, packaging script and copy manifest. This prevents an
ignored copied checkout from being labelled as a clean original tree. Root
owns the corresponding `package-native.py` validation change.

Meaningful temporary-source counterexamples exercise the real copied packaging
module. The first run found two defects: a failure journal could coexist with
an accepted complete marker, and a dangling marker symlink could fall back to
unrelated clean Git metadata. Root fixed both guards. The unchanged test then
passed **22/22**, retaining the first failed run:

```sh
python games/yuga-native/tests/native_source_snapshot_cases.py \
  --report games/yuga-native/docs/research/hero-six-rounds/combat/round6/snapshot-counterexamples-r2.json
```

[Final counterexamples](round6/snapshot-counterexamples-r2.json) verify exact
original dirty metadata; wrong location; changed, added or removed runtime;
stale runtime/script/manifest identities; malformed Git fields; incomplete,
failed and malformed markers; and both identified guard defects. Marked
invalid snapshots never fall back to live Git. No real original source is
mutated. The final case verifies the original packaging script is unchanged.

| Source/result | SHA-256 |
| --- | --- |
| Freeze helper | `2ed640ce9c8b591712e0a13ee56b28d4f546dc65dd30fee2e47d582b924fa52e` |
| Snapshot counterexample test | `6c4c75e2adb0b4c2c484c11674742e7426fc16b43956a9b2725713b098503e6a` |
| Root packaging script tested | `c438d742474072722fae1d4f899d4d86030998766be345fea76f1cda9c7a7eed` |
| Passing counterexample receipt | `9fabf5296bc3d34c6482d8236076e219eaf826264a51b9377c5de8db27a57539` |

These cases establish provenance validation, not an exported package. Root's
subsequent freeze/import/export receipts establish the actual delivered build.
The combat reviewer made no additional runtime edits during final freeze.

## Legacy regression migration

Root's composed final regression found six failed predicates in
`world_scene_cases.gd`. Four still asserted the intentionally superseded
Block2 detail and legacy roof-top surfaces while the newly default Sangam
district was enabled. Two UI predicates required the old 12-button/13-action
pause menu; all measured rectangles, focus targets and overlap checks passed.
The new Field shop makes the intended menu 13 buttons and 14 keyboard actions.
The original failure remains in `../root/final-regression-r1/world_scene_cases/`.

The test now explicitly disables Sangam alongside the existing gate/garden
opt-outs and asserts that fixture selection. Every original legacy surface,
frontage and negative-geometry oracle is retained. Default Sangam remains
covered by its dedicated suite and the 60/60 integrated encounters above.
The menu oracle now requires the exact ordered labels, unique action list,
volume-slider position, Rama/legacy identities and three connected openers.
It additionally detects a missing field-shop keyboard action, duplicate or
reordered entries at unchanged count, a wrong label, and a disconnected shop
callback before restoring the exact menu contract. No runtime code changed.

```sh
godot --headless --verbose --audio-driver Dummy --path games/yuga-native \
  --script res://tests/world_scene_cases.gd \
  -- --report=/workspaces/ANDOLAN/games/yuga-native/docs/research/hero-six-rounds/combat/round6/world-scene-legacy-current-ui-r2.json \
  > games/yuga-native/docs/research/hero-six-rounds/combat/round6/world-scene-legacy-current-ui-r2.log 2>&1
```

Result: **36/36**, no warnings or errors.
[Receipt](round6/world-scene-legacy-current-ui-r2.json) SHA-256
`c1580ba05e26bfd0b5303006c3490066fcf9b93048ddd6dc4b7437c79c99f7c5`;
test SHA-256
`654f930a98078ec9e7b11d5c16fe10178b14aa63e155e1262106e6c4b8c20a59`.
The local r1 log retains an initial new-test typed-variable parse error;
the succeeding run uses an explicitly typed `Array[Node]`.

After the passing run, every live runtime file was independently compared to
the completed `sangam-release-r1` snapshot: **zero differences**, runtime digest
`b4a253fea063f4fdcb013b56bb83d95fb44fff9d9b8b1080f6084d99d8ada6b9`.
The test was run against the live copy of those identical runtime bytes. The
frozen snapshot and its original test bytes were not edited.

## Next owner

Root owns build delivery and composed acceptance. The subsequent actual
packaged LMB/Q/X originals now have an independent
[31-image continuous-interval review](round6/ordinary-primary-power-review.json),
covering all distinct screens among 162 consecutive samples. Actual post-primary
Piercing and raised-arm primary-to-Volley transitions are visible; strict
fully-raised warm Q and close finger contact remain unaccepted. Existing hero
frame review remains linked from the [combat handoff](README.md). Human motion
feel, audio listening, final art approval, physical-GPU performance and online
play remain separate from these deterministic offline checks.
