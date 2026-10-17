# Final source-frozen R4 verification

The reviewed shadow-depth correction now has a complete fresh verification run. All three sequential runners used identical **506 runtime files**, with unchanged before/after identities. Godot 4.6.3 standard ran on CPU affinity `0,1`; the film renderer retained `2,3`. No gameplay or rendering source was edited during this verification task. The prior R3 archive remains intact at `../final-verification/`.

| Executed catalog | Actual outcome |
| --- | --- |
| New visual contracts, all 12 suites | 727 assertions pass |
| Existing quality catalog, all 16 suites | 777 assertions and 15 reproducible PCM files pass |
| Affected world presentation fixture | 32 assertions pass |
| Affected world lighting fixture | 30 assertions pass |
| Current resource and effect census | 51 assertions pass, including five scene lifecycles and all five accepted ability fixtures |

All **31 child processes exited 0**. Independent strict JSON, report/log hash, nonempty assertion and source-identity validation passed. All **48 logs contain zero engine errors or warnings**. Assertion totals across overlapping catalogs must not be presented as independent whole-game coverage.

## Reviewed lighting profile

This run pins `production_lighting.gd` at `b1da45eeb090eabb802f199c84759532b4fd202371fa6c543de6316c2740ca52` and `world_lighting.gd` at `2b0e9c992b7e13456ef135fc9457172d3731103a27715d54f393c62d391c1ceb`. Both retain the promoted depth bias **0.2** and normal bias **0.35**. The quality fixture at `90a6b41720915aeda6264862b05acb76519c82d5b5d1066dde7fc2ad8ed23a24` now preserves that reviewed numerical profile. Numerical checks alone do not establish shadow appearance; separate actual day/night courtyard and world image review supplies that evidence.

## Reproduce the receipt audit

```sh
python3 games/yuga-native/docs/evidence/visual-campaign/final-verification-r4/verify_receipts.py
```

The verifier rejects duplicate JSON keys and nonfinite JSON values, checks every positive assertion and child exit, verifies captured report/log hashes, compares runtime identities across all three runners and scans their raw logs. Reports, stdout/stderr, runner output and complete source snapshots live in `visual/`, `quality/` and `world-resources/`. Temporary user profiles and font caches were omitted. `summary.json` records exact runtime and fixture source identities. This archive is working-source evidence based at `38d11148fe69b184e981164c8a71387c91dc64c5`, not a published release receipt.

## Commands actually executed

From `/workspace/ANDOLAN`, with `LP_NUM_THREADS=2` and `PYTHONDONTWRITEBYTECODE=1`:

```sh
taskset -c 0,1 /workspace/tooling/yuga-native-python/bin/python games/yuga-native/tools/run-visual-checks.py --python /workspace/tooling/yuga-native-python/bin/python --engine godot --output /workspace/scratch/visual-final-checks-r4 --max-cpus 2
taskset -c 0,1 /workspace/tooling/yuga-native-python/bin/python games/yuga-native/tools/run-quality-checks.py --python /workspace/tooling/yuga-native-python/bin/python --engine godot --output /workspace/scratch/quality-final-r4 --max-cpus 2
taskset -c 0,1 /workspace/tooling/yuga-native-python/bin/python /workspace/scratch/run-world-resource-final-r4.py
```

Each destination must be fresh. The exact supplementary wrapper is preserved as `run-world-resource-final-r4.py.txt`; it runs `world_presentation_cases.gd`, `world_lighting_cases.gd` and `visual_resource_budget_cases.gd --effects` sequentially through the existing strict authoring process/report helper, with complete source snapshots. Change the scratch destination when reproducing it. Each receipt retains its actual child command.

## Resource scope

The final source census remains 345 scene nodes, 63 mesh instances, 955,540 resident triangles, 427,618 triangles visible by scene-tree flags, 11 lights, 19 collision objects and one 164-bone skeleton. Saturated effects remain 21,360 triangles; reduced settings remain 12,192. This run repeats all current resource/effect checks after the lighting promotion; the earlier baseline comparison in `../performance/` was preserved.

These results do not certify rendered-art quality, continuous motion/contact, listening, physical-GPU frame rate, native online play, Windows execution or release qualification. Scene-tree visibility is not actual frustum/occlusion visibility, and five stable object/resource exits do not prove the absence of every possible leak.
