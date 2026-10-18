# I2-06 — independent final catalog and resource-census review

Product: YUGA native. Reviewer: `ui_06_acceptance`. Status: bounded acceptance complete for the exact final integration freeze. No runtime edits, imports, renders or duplicate scene-cycle test were performed by this role.

The **one new full screen catalog passes 23/23 suites and 459/459 checks**, exit 0, in 78.35 seconds. This includes the new eight-check effects-feedback suite and the final overview-motion player/world source. No previous U5 pass was substituted. Every suite report has a strict boolean `passed=true`; all exited zero, with no timeout or logged error diagnostics. The engine is Godot `4.6.3.stable.official.7d41c59c4`.

Executed project: `/tmp/yuga-i1-final-r1/ANDOLAN/games/yuga-native`. [Frozen manifest](source-freeze.json) SHA-256: `9919dccbd3fd18446abf2ff435be55696e913ad8d5cb7874e7e641f9fd13f088`. All **755 source files and 350 imported-cache files** matched before and after the run. The seven reviewed runtime scripts also match Git commit `4bd82ad5909ce949df536b2809d8b37a7f9d20f8`, independently checked against Git objects in [commit-runtime-pins.json](commit-runtime-pins.json). The complete executed identity remains the frozen manifest.

The exact [wrapper](run-catalog.py) verified pins, invoked this command once after UI03 released CPU2, and verified the pins again:

```sh
taskset -c 2 python3 \
  /tmp/yuga-i1-final-r1/ANDOLAN/games/yuga-native/tools/run-visual-checks.py \
  --catalog screens --max-cpus 1 --timeout 120 \
  --output /tmp/yuga-i2-independent-screen-catalog-r1
```

OMP/BLAS environment limits were one thread; the runner used isolated per-suite user directories and single-threaded scene processing. The frozen runner sets `LP_NUM_THREADS=2` internally; this run used headless engines and performed no rendering/import. CPU2 was released immediately afterward. [Receipt](receipt.json), [summary](catalog-r1/summary.json), all 23 reports, source lists and logs are retained. The original U5 rejected frame-budget fixture and its corrected reconciliation remain separate historical evidence.

## Independent review of the ten-cycle census

Root executed [I2-01](../role01/REVIEW.md)'s actual courtyard→world→courtyard route ten times. This role independently checked its command receipt, exit status, artifact hashes, all seven source pins against the final freeze, all 43 assertion booleans, the complete 20-sample sequence and actual warmed ranges. The reproducible read-only review is [review-census.py](review-census.py), with [results](census-review.json). These **43 root-executed checks are not added to this role's 459 independent catalog checks**.

| Warm scene samples, cycles 2–9 | Court | World |
| --- | ---: | ---: |
| Tree nodes | 420 | 2,715 |
| Window focus callbacks | 4 | 5 |
| Resources | 225 | 245 |
| Objects, diagnostic range | 3,759–3,760 | 6,667–6,669 |
| Orphan nodes, diagnostic | 1 | 0 |
| Persistent loader | 1, done | 1, done |

Old scene WeakRefs and old collision-group removal are tested on the actual routes. The warmed tree-node, focus-listener and resource counts remain stable across eight samples per scene. Cold courtyard resources start at 208 and then stabilize at 225; aggregate counts identify a one-time initialization/cache difference, not the identity of every retained resource. Small object-count variation is diagnostic.

The courtyard's orphan count is already one in its first sample and remains one; the world count is zero. The orphan identity was not captured. This supports **no accumulating orphan count over these cycles**, not zero orphans or proof of no leaks. Heap allocation ownership and GPU memory were not measured.

## Limits and handoff

These checks establish frozen native offline screen/input/lifecycle contracts and the bounded census findings. They do not establish OS input or new rendered pixels, physical-GPU FPS, current hero-art quality, online matches, other platforms or packaged-release qualification. Prior U5 r1/r2 images retain their own source identity; the separate I3 packaged font/theme/image review remains next. Compact 11–12 logical-pixel world text remains a readability limit. Other I2 owners' external sequence, preference and seeded-stress fixtures are separate evidence, not members of this 23-suite catalog.
