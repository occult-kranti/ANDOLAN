# Final source-frozen R3 verification

All three sequential runs passed on the same **506 runtime files**, with exact before/after identity. Godot 4.6.3 standard ran on CPU affinity `0,1`; the independent renderer retained `2,3`. No gameplay or rendering source was edited during this task.

| Executed catalog | Actual outcome |
| --- | --- |
| New visual contracts, all 12 suites | 727 assertions pass; 12 native exit codes 0 |
| Existing quality catalog, all 16 suites | 777 assertions and 15 reproducible PCM files pass; 16 native exit codes 0 |
| Current resource and effect census | 51 assertions pass; native exit code 0; five scene lifecycles and all five accepted ability fixtures |

`verify_receipts.py` independently parses reports with duplicate-key and nonfinite-number rejection, checks every assertion and native exit code, verifies stored report/log hashes, compares all runtime records between the three runs, and scans 44 logs for engine errors and warnings. It passes with zero such lines. Run it directly from any directory:

```sh
python3 games/yuga-native/docs/evidence/visual-campaign/final-verification/verify_receipts.py
```

The raw reports, captured stdout/stderr, runner output, and complete source manifests are preserved in `visual/`, `quality/` and `resources/`. Temporary user profiles and font caches were omitted. `summary.json` pins the exact district, ability, atmosphere, motion, material, player and boundary shader sources. This evidence describes working source based at `38d11148fe69b184e981164c8a71387c91dc64c5`; it is not a published release receipt.

## Commands actually executed

From `/workspace/ANDOLAN`, with `LP_NUM_THREADS=2` and `PYTHONDONTWRITEBYTECODE=1`:

```sh
taskset -c 0,1 /workspace/tooling/yuga-native-python/bin/python games/yuga-native/tools/run-visual-checks.py --python /workspace/tooling/yuga-native-python/bin/python --engine godot --output /workspace/scratch/visual-final-checks-r3 --max-cpus 2
taskset -c 0,1 /workspace/tooling/yuga-native-python/bin/python games/yuga-native/tools/run-quality-checks.py --python /workspace/tooling/yuga-native-python/bin/python --engine godot --output /workspace/scratch/quality-final-r3 --max-cpus 2
taskset -c 0,1 /workspace/tooling/yuga-native-python/bin/python /workspace/scratch/run-resource-final-r3.py
```

Each runner requires a fresh output directory. The exact resource wrapper is preserved as `run-resource-final-r3.py.txt`: it uses the existing strict authoring process/report helper and full runtime/source snapshots around the real `visual_resource_budget_cases.gd --effects` invocation. Its report includes the actual command. Change the fresh scratch destination when reproducing it.

## Why the resource check was repeated

The Guardian boundary shader changed after the earlier effect allocation census. The final run therefore repeated the full current 51-check fixture. Scene counts remain 345 nodes, 63 mesh instances, 955,540 resident triangles, 427,618 triangles visible by scene-tree flags, 11 lights, 19 collision objects and one 164-bone skeleton. The saturated effect fixture remains 21,360 triangles; reduced settings remain 12,192. The older baseline comparison in `../performance/` was preserved rather than rerun.

These are numerical and lifecycle results. They do not establish rendered-art acceptance, continuous motion/contact quality, listening quality, physical-GPU frame rate, native online play, Windows execution or release qualification. Scene-tree triangle visibility is not actual renderer frustum/occlusion visibility. Five steady object/resource exits do not prove that every possible leak is absent. Assertion totals from overlapping catalogs must not be presented as independent whole-game coverage.
