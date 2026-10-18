# Exact 0964564 native CI failure

[Run 39127712773](https://github.com/occult-kranti/ANDOLAN/actions/runs/39127712773) failed at step 24, Confluence native traversal and rendering resource checks, on exact source `0964564d1ba283a5ac0aee8eab0a6cccd8f443f3`.

The retrieved remote log contains `world_scene_cases.gd` **25/27**. The two failures are `actual authority box surfaces` and `restored scene collision passes after mutations`; four authority-solid-2 rays hit the accepted frontage surfaces before the older enclosing box. The step stopped there, so its later new frontage, lighting and flow commands did not execute. Subsequent workflow steps were skipped except the always-run artifact archive and cleanup.

W4 already preserved the same failure and repaired the fixture in [the source-bound regression packet](../../world-lane-frontage/W4-world-scene-regression-r1/receipt.json). Successor source `1b2e6f5202490036a6195581f2901a2075750b56` has its own run and must not relabel this failure. No new diagnosis, runtime fix, local engine, render or export was performed by W6.

The compressed failed-step log, complete emitted world-scene result, exact job/step metadata and source pins are retained. The public `96d5b9cd` executable keeps its separate qualification.
