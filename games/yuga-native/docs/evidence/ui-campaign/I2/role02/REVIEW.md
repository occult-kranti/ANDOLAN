# I2-02: shared UI resource ownership and repeated creation

The actual native 2D probe passes **184/184 assertions** in `native-r2/runtime.json`. It constructs and frees native Controls with the current shared theme, font resources, generated icons, local style overrides and CanvasItemMaterial objects. Twelve measured pairs alternate the themed fixture and an otherwise identical native-control fixture with empty Themes, after three warmup pairs. Each themed fixture exercises eight role resets.

The executed surface is `hero_ui_theme.gd` SHA `b1d630e9087f939ba6a68a5bbfac6f126064d417393786380c324317ac5d39a6`, three font sources, three import descriptors and their three existing FontFile payloads. All **10 files** match final I1 freeze manifest `9919dccbd3fd18446abf2ff435be55696e913ad8d5cb7874e7e641f9fd13f088`; exact reconciliation is in `SUMMARY.json`. This is execution of that shared resource surface, not of the whole final world scene.

## Findings

- The primary fonts and their shared authored fallback keep the same resource IDs across every build/free cycle. Actual `FontFile.data` SHA-256 values match all three pinned raw TTF files; system fallback stays disabled.
- Mutating a button's owned style leaves its peer and base Theme unchanged. Mutating one Theme leaves the second independent Theme unchanged. Each role reset releases all six replaced local styles.
- The themed live fixture owns 150 StyleBoxes, 38 Texture2Ds, two Themes and two CanvasItemMaterials. Weak-reference checks cover every owned resource and native child, including internal popup/scroll controls. All watched owners release after teardown. Theme operations preserve each button's distinct CanvasItemMaterial identity and blend mode.
- After every measured teardown, native node/orphan counts return to **1/0**. The ResourceCache monitor remains **5**; it does not count the unfiled local resources, which the probe enumerates separately.
- Creation takes **2.222 ms median** for the empty fixture and **4.732 ms median** for the themed fixture in this run. Ranges are 1.708–3.996 ms and 4.564–7.538 ms. These are local CPU observations for two theme instances plus the fixture's controls; they are not a frame-rate result or a budget.

Global ObjectDB observations vary from 1490 to 1495 across the sequence, including intervening empty controls. The explicit owned objects release, but the small global residual is not attributed to a specific engine cache here. Allocator measurements also include the growing report arrays/dictionaries. This evidence therefore does **not** assert whole-process leak freedom or a product memory budget.

## Execution and retained correction

Godot 4.6.3 official Linux SHA `f64d4ed19fc9df9440321653fcc80df8c6e365ba7b6de0a29e2cfa9fa71bfeb3`, headless native 2D, CPU 3, BLAS/OMP one thread, isolated XDG directories. A 2.93 MB fixture copies exact source/font/cache bytes; it performs no import, export, GLB load or full-project copy. Logs are clean, the process exits 0, and source plus copied resource hashes remain unchanged.

`native-r1` retains the earlier successful ownership run. Its census instrumentation left a final WeakRef loop variable in scope and omitted internal child enumeration. R2 moves weak-reference summaries into their own scope and includes internal children. The remaining small global ObjectDB variation is still reported. Both executed probe sources and logs are retained; current results are R2.

The runner stages a fresh fixture and requires the exact manifest hash:

```sh
python docs/evidence/ui-campaign/I2/role02/run_probe.py \
  --freeze /tmp/yuga-i1-final-r1/ANDOLAN/games/yuga-native \
  --freeze-manifest-sha256 9919dccbd3fd18446abf2ff435be55696e913ad8d5cb7874e7e641f9fd13f088 \
  --workspace /workspace/scratch/ui-campaign/I2/role02/NEW --run
```

The recorded actual run used the U5 r2 freeze, then reconciled all executed resource files to final I1 without transferring unrelated scene execution. Repeats need the scheduler's free CPU lane. There were no visual reviews or runtime edits in this role. Full-scene/listener cycles, loader stress and action/preferences sequences remain with their separate I2 owners.
