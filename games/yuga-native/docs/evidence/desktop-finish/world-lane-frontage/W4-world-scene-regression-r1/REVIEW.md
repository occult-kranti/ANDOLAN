# CI world-scene frontage fixture correction

The unchanged fixture3693c4ff reproduced25/27. Four authority-solid-2 side contacts differed from the old flatBox expectation under one check; the restored-scene aggregate also failed. All25 other check results passed. The original CI failed-step log is preserved byte-for-byte.

Only tests/world_scene_cases.gd changes. Same40ray origins/finishes and0.02m tolerance; seven other boxes/35rays and targettop stay exact. AtY1 reviewed block2 planes are localX±8.76, frontZ−8.35, rearZ+8.76 within the unchanged±9 broadbounds. Expected coordinates are explicit review oracles, not sampled from the implementation under test.

The fixture additionally requires exact reviewed data67950a68, installedConcave4824tri/backfaces/broadbounds, sole enabled holder/owner, published-shape identity and visible replacement. Restoring the formerBox must trigger all four target surface errors AND the installed contract, then exact Concave resource is restored. Every original missing-blocker/floor/prop mutation check remains; restored aggregate includes the new contract. Scope distinguishes planar broadbounds from detailed3D parity.

Corrected fixture29/29 passes clean2.729s under officialf64/exactCIargs onCPU4. Both runs preserve all runtime bytes; only the fixture differs between runs. All27 original names retained;25previous passes remain passed;2 original failures improve and2new controls pass. No runtime/source art/engine/package changes, imports, raster or unrelated suites. Root reviewed the exact patch and will commit/push ordinary CI separately.
