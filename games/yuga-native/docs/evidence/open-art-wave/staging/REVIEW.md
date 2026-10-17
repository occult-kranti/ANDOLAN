# Role 14: isolated open-cloth fixture

Source base: `658804fd6e454c6d584ac3245601506b22075c0b`, native YUGA,
17 October 2026. The change fixes the review workflow's confirmed import
boundary: the product's existing `art/.gdignore` intentionally prevents PNG
imports beneath `art/`. That file remains unchanged.

`tools/stage-open-cloth.py` builds a fresh project outside the checkout. It
copies eight explicit dependencies at their original `res://` paths: the
secondary-motion owner, shader, real material test, candidate binder, candidate
material and three PNG maps. It generates a ninth payload, a minimal
`project.godot`, and records the original configuration's separate digest.
The secondary-motion script is required by the material test's actual preload.
No `.gdignore`, scene, full-world asset, import sidecar or Godot cache is copied.

The CLI emits one JSON receipt and saves the same receipt at the fixture root
as `open-cloth-stage-manifest.json`. Every row identifies the project-relative
source, fixture-relative destination, source digest and staged digest. The
generated configuration is explicitly distinguished. All source bytes and file
identities are pinned before staging and checked again after copying. Existing
destinations, checkout overlap, source aliases, symlinks, missing/nonregular
inputs, malformed source envelopes, corrupt PNG envelopes and undeclared
resource dependencies fail with nonzero exit status.

Executed from `/workspace/ANDOLAN`:

```sh
python3 games/yuga-native/tools/stage-open-cloth.py --project-output /tmp/yuga-open-cloth-stage-role14-r1
python3 games/yuga-native/tools/run-authoring-checks.py --unittest-child games/yuga-native/tests/open_cloth_stage_cases.py --report /tmp/yuga-open-cloth-stage-role14-cases-r1.json
```

The real staging command passed with nine payloads plus its JSON manifest.
The test command passed **22 tests**, including relocated real-source CLI
counterexamples, byte/hash equivalence, no ignore/cache inheritance, source
preservation, concurrent source mutation detection, and execution with no
engine on `PATH`. The actual receipts are retained as
`stage-manifest-r1.json` and `stage-cases-r1.json`; helper/test hashes are in
`source-pins-r1.json`.

No Godot invocation, render or input review was performed by this assignment.
The fixture uses the compatibility renderer for resource and lifecycle checks.
It does not establish hero appearance, performance or gameplay readiness.
The CI owner must perform the bounded editor import, verify all three real
imported texture payloads, then execute the actual material test with
`--candidate-resource`. The main product ignore boundary must remain intact.
