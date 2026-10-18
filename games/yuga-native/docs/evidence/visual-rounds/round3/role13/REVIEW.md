# R3-13 independent geometry, retained-byte and LOD costs

**Bounded accounting passes; this is not a hardware performance approval.**
The independent source reader reports 367,864 / 202,034 / 136,228 active triangles
for near / mid / far groom-r6, including body, bow and face. Hair contributes
29,448 / 13,450 / 6,444. The R2 baseline totals were 408,316 / 216,544 / 140,966.
Nine source checks pass, independently confirming active indices and old BIN
preservation rather than trusting the author's reported totals.

| LOD | GLB bytes | Added bytes over R2 | Retained unreferenced old-hair bytes |
| --- | ---: | ---: | ---: |
| Near | 36,049,948 | 1,727,732 | 3,854,580 |
| Mid | 25,847,144 | 797,612 | 1,769,652 |
| Far | 20,901,820 | 394,260 | 753,348 |

The append-only preservation contract reduces active geometry while increasing
package bytes. The old hair views are no longer referenced by active primitives,
rigs, clips, images or morph data, but remain in the GLB. Source accounting
includes sparse morph view references; an initial missing-bufferView assumption
was corrected before any complete result.

The actual imported candidate passes 12 independent ownership/count checks:
seven live meshes, exactly one 164-bone skeleton, one retained near face, and
three visible meshes at each of the five forced 0→1→2→1→0 level transitions.
The visible triangle counts exactly match source totals. Reset restores near
visibility. Two other candidate faces and skeletons are not live. All seven
meshes remain loaded; hiding a level does not release its geometry.

The imported probe exposes 22 distinct texture resource identities and 40
material identities after surface/secondary/finish binding. CPU image payload
is 49,370,436 bytes, including the shared woven map; this counts referenced
image resources, including uniforms potentially inactive in a shader. It is
not GPU allocation. Base mesh-array payload sums exclude blendshape data,
resource overhead, renderer copies and import caches; raw per-mesh values are
in `imported-costs.json`. No FPS, VRAM, streaming or draw-call claim is made.

Executed with Godot 4.6.3 headless, CPUs 0,1, against role06's read-only frozen
`capture-candidate-project-r1`; no editor import or render. Exact sources are
pinned in the reports. The initial GDScript static resource-path parse failure
is retained separately and was corrected to explicit source paths.

Reproduce from repository root:

```sh
taskset -c 0,1 python3 games/yuga-native/docs/evidence/visual-rounds/round3/role13/source_costs.py
taskset -c 0,1 timeout 60s godot --headless \
  --path /workspace/scratch/visual-round3/capture-candidate-project-r1 \
  --script /workspace/ANDOLAN/games/yuga-native/docs/evidence/visual-rounds/round3/role13/imported_costs.gd -- \
  --report=/tmp/r3-imported-costs-fresh.json
```

No runtime edit in this role. Groom-r7 keeps topology but needs its own source
pins; this packet remains explicitly r6. Next owners: root/role14 for package
cost disposition and role06 for actual visual/hardware measurements.
