# Native acceptance scenarios

Run with Godot 4.6.3 after a project import. The headless renderer checks simulation and imported animation transforms; it does not assess graphics quality or frame rate.

```sh
godot --headless --path games/yuga-native --editor --import --quit
godot --headless --path games/yuga-native --fixed-fps 60 --script res://tests/native_acceptance.gd -- --report=/tmp/yuga-native-acceptance.json
godot --headless --path games/yuga-native --script res://tests/projectile_cases.gd -- --report=/tmp/yuga-projectile-cases.json
python3 games/yuga-native/art/validate_courtyard.py
python3 games/yuga-native/art/production/validate_rama.py
```

In the managed cloud environment, use the writable XDG directories documented in the native setup instructions. An alternative report location can be supplied after `--`, for example `-- --report=/tmp/yuga-native-acceptance.json`.

The runner uses real Godot character collision, physics ray casts, timers and imported Skeleton3D animation evaluation. It deliberately injects Godot action state and builds labelled isolated collision fixtures. This is reproducible scripted QA, **not evidence of physical keyboard/mouse input**, a full match, commercial-game parity, visual polish, or multiplayer synchronization.

The scenarios cover input registration; entering training; pause and held-input neutrality; restart and menu safety; the production Rama model's 164 bones and nine animation clips at five sample times; forward/diagonal movement; wall collision and dash; jumping and landing; fire cooldown, magazine and reload; high-speed projectile damage, defeat and timed target restoration; and world occlusion. They also verify selection of the production model, preservation of the original Rama source bytes, and the presence and stability of 12 runtime/source files, including the production lighting, water shader and hero asset.

A nonzero exit code or a report containing `passed: false` fails acceptance. Preserve failed reports when fixing a defect. A separate rendered-window check is required to judge art, readability, animation appearance and actual OS input.

## Four recorded QA milestones

### R1 — Baseline and failing cases

The original courtyard baseline is preserved in [native-acceptance.json](evidence/native-acceptance.json): **16/16 checks passed**. Earlier evidence remains available in [native-acceptance-before-final-art.json](evidence/native-acceptance-before-final-art.json).

The first pause test, [native-acceptance-before-pause-fix.json](evidence/native-acceptance-before-pause-fix.json), passed 14 of 15 checks but exposed 0.425 m of unintended coasting after resuming held movement. Separately, [projectile-lifetime-before.json](evidence/projectile-lifetime-before.json) preserves three failures among seven checks: the projectile lost its final fractional travel, missed a valid final-segment hit and shortened total range when lifetime was partitioned into substeps.

### R2 — Implementation repairs and regression checks

The pause repair clears horizontal velocity and active dash; the original drift assertion then passes with 0 m of coasting. The collision scenario also verifies that living targets block movement while defeated targets permit passage.

The projectile repair sweeps the remaining lifetime before expiring and clamps travel to that remaining range. [projectile-lifetime-after.json](evidence/projectile-lifetime-after.json) records **7/7 checks passing**, including final-segment hits, range bounds, thin-wall occlusion and shooter exclusion. The repaired projectile source is pinned to `39b651bf014b91352e3cd62d15ec22966e5de4707a6dd1b9bcfb2dddd438695a`. These are explicit isolated physics fixtures; their failures and assertions are retained.

### R3 — Final production asset and source checks

[native-acceptance-production-v2.json](evidence/native-acceptance-production-v2.json) preserves **18/18 passing checks** on production hero `86e4acc36c7da2d4abef8823e9bd1b4549ede34091d5518c89f9edbf6a7ea808`. A subsequent actual-render review found a mesh-selection defect that finite-transform tests could not detect, so the corrected asset received a fresh run.

The v3 report is [native-acceptance-production-v3.json](evidence/native-acceptance-production-v3.json): **18/18 checks passed** on hero `459fab62bcf29066490c0156cdf1a3ba7378ff3dba2fa6e4882b9eff96a801a0`. It records 164 bones, nine clips and 7,380 finite/non-singular sampled bone transforms, with all 12 source hashes unchanged throughout the run. Original Rama remains byte-identical at `a366dc927cb34208742e5617decefb2580e1cdab97f946ed4eb14687dc7abfbc`.

The final [native-acceptance-production-v4.json](evidence/native-acceptance-production-v4.json) also passes **18/18** on hero `6657f4bf2fdb41b1f8b1bbd64777b35b5b4acfe00b3e3e22e4bc793fd4df3e8e`, after actual frames exposed and the generator repaired ten omitted lower-leg garment faces. All 12 source hashes remain stable.

[courtyard-refinement-v2-validation.json](evidence/courtyard-refinement-v2-validation.json) verifies the current courtyard's embedded images, geometry indices, finite attributes, unit normals/tangents, size budget and metadata hash. CI runs the acceptance suite, projectile regression cases and both production asset validators. CI status must be read from the relevant commit's actual workflow run.

### R4 — Remaining visual and platform gates

Use separately recorded native frames and visible-window input checks to assess silhouette, grip, garment intersections, camera feel and control readability. Sampling five times per clip does not cover every blend, every frame or every hero. The v2 visual defect is a concrete example of that limit.

The headless run's short wall time is not a graphics or hardware performance measurement. A packaged Windows build still requires execution on Windows, and Linux rendering evidence applies only to its recorded configuration. These tests do not establish a complete match, multiplayer synchronization or commercial-game fidelity. Keep final visual review and platform execution results alongside the corresponding asset/package hashes.
