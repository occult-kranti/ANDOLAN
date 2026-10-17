# Role 13 — native scene resource and lifecycle review

The R3 candidate passes **24 scene/lifecycle assertions** after the four diya
lights were added. The unchanged baseline passes 24; the preceding candidate
passes 51 scene and effect assertions. These runs overlap and should not be
summed into an independent assertion total. All three accepted runs have native
exit 0 and empty stderr. [The summary](summary.json) pins their receipts.

The [probe source](../../../../tests/visual_resource_budget_cases.gd) instantiates
the actual courtyard five times. Each instance performs six real
start/reset/menu transitions while alternating day and night, then frees the
scene. Autonomous simulation is disabled so the compared census is repeatable.
No editor import or heavy renderer was run. The baseline is the existing
isolated `38d11148fe69b184e981164c8a71387c91dc64c5` snapshot; all **489** recorded
source hashes still match its origin manifest ([identity](baseline-identity.json)).

| Actual scene allocation | Baseline | R3 candidate | Change |
| --- | ---: | ---: | ---: |
| Nodes | 331 | 345 | +14 |
| Mesh instances / unique meshes | 55 | 63 | +8 |
| Resident unique triangles | 912,532 | 955,540 | +43,008 |
| Triangles on scene-tree-visible meshes | 384,610 | 427,618 | +43,008 |
| Effective material resources | 77 | 85 | +8 |
| Referenced material textures | 29 | 34 | +5 |
| Texture texels, base dimensions | 14,680,064 | 17,563,648 | +2,883,584 |
| Referenced texture source-file bytes | 13,549,974 | 14,311,499 | +761,525 |
| Allocated lights | 7 | 11 | +4 |
| Skeletons / bones | 1 / 164 | 1 / 164 | unchanged |
| Collision objects / particles | 19 / 0 | 19 / 0 | unchanged |

These totals include all resident hero LOD meshes. Visibility is the scene-tree
flag, without frustum, occlusion, shadow-pass or GPU draw accounting. Texture
source bytes and texels are **not** GPU memory measurements. The four new
3.4-metre-range diya lights have shadows disabled and are hidden by day; their
night energy is 1.05. They are an intentional cost added after R2. R3 district
source is `09c6447f36a9eba2d0898f3db846fedb45693b9c9d56f3212bc2ec537de56431`.

Every R3 exit returns to one engine-root node, zero orphan nodes, 1,570 objects
and 43 resources. The baseline consistently returns to 1,566 objects and 39
resources; the candidate retains four additional resources after warmup,
without accumulation across the five exits. R3 exit RSS is 236,472 KiB in all
five samples. Engine static allocation rises by 283,724 bytes across the samples,
which also retain increasingly large JSON/check reports. This is bounded
node/resource lifecycle evidence; it does not establish that every allocation is
leak-free. Earlier R2 exit RSS settled at 243,208 KiB after warmup; that
allocator behavior is preserved rather than presented as a regression or gain.

The actual-kit effect probe samples five abilities at 25 ms steps for eight
simulation seconds each. Peak total allocated effect triangles were 282 for
Kodanda, 558 for Piercing Dawn, 450 for Measured Step, 1,312 for Guardian Circle
and 858 for Dawn Volley. These are sampled fixtures, not a universal maximum
over every possible accepted recipient/contact combination.

A separate capacity fixture expands a genuine accepted ward start event to
twelve presentation IDs and injects eighteen contacts. It allocates **21,360
triangles, 66 mesh nodes and 54 effective materials**, with zero effect lights,
particles or textures. The thirteenth cast is refused; reset frees every owned
child. Reduced-effects mode reduces the allocated geometry. The effect source
hash is identical in R2 and R3. The calligraphy shader is transparent,
double-sided and does not write depth; bounded geometry does **not** establish
bounded fragment cost when strokes overlap. Hardware multi-effect profiling
remains open.

Construction and transition microseconds in each receipt are host wall-clock
observations on two CPU-affinity cores. Other workers were active, and the
dummy renderer cannot establish frame rate, latency, GPU memory or achieved
Deadlock-level graphics. The separate candidate R1 capture uses Forward+ on
llvmpipe; its fixed capture clock also is not hardware FPS. R3 rendered
acceptance belongs to the visual review owner.

## Reproduce

From the repository root, with already imported assets:

```sh
taskset -c 0,1 timeout 150 godot --headless --path games/yuga-native \
  --script tests/visual_resource_budget_cases.gd -- --effects \
  --report=/absolute/fresh/current.json
```

Omit `--effects` for the affected-scene-only repeat. The original baseline uses
`--path /workspace/scratch/visual-campaign-baseline-project-r2` and the absolute
path to this same test script, without `--effects` because its older effect
report schema differs. Always require a complete JSON receipt, native exit 0,
every assertion passing and no engine error in either log.

The failed initial parse, rejected older-schema effect attempt and later typing
correction remain in their numbered folders. In particular,
`r2/baseline.json` is **invalid evidence despite its partial `passed: true`**:
its stderr contains a script error. The final probe requires an explicit
effect-completion marker, preventing that partial path from passing again.

Next owner: production profiling/visual acceptance. Run representative crowded
combat on a physical GPU, measure frame-time percentiles and transparent
overdraw, and inspect repeated match/load transitions before setting a hardware
performance gate. Keep all three resident LODs, material instances, practical
lights and render passes in the budget.
