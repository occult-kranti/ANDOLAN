# Retained findings

- `rama_hud_layout_cases`: 9/9 assertions, but engine missing the concurrent new gold finish cache; diagnostic only.
- `ui_hud_edge_cases`: 11/12; compact relay and controls overlap, plus missing finish cache.
- `ui_theme_map_consistency_cases`: 16/17; compact overlap, missing finish cache and cleanup warning.
- `graphics_g1_screen_cases-r2`: 17/18; clean engine, supported long Space binding plus actual RELOADING state exceeded HUD width.
- `graphics_g1_screen_cases-r3`: 17/18; same retained width failure with added card-boundary details.

The first three runs preceded root’s serialized material import and were not a frozen whole-project acceptance. Compact phase/population text now yields to the objective; the long reload/remap row fits the final 820 px HUD. Accepted reruns are separate immutable reports. No rendered acceptance is inferred from these tests.
