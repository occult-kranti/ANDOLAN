# I2-01 — repeated complete scene transitions

Ten actual courtyard → wired Explore → world → injected Escape → wired Return cycles pass **43/43**, exit0, without error/warning diagnostics. [Receipt](receipt.json), [report](report.json), [unaltered log](run.log) and exact [test](world_flow_cases.gd) bind this run to final I1 freeze `9919dccbd3fd18446abf2ff435be55696e913ad8d5cb7874e7e641f9fd13f088`.

Every transition verifies old scene WeakRefs and world collision groups are removed. After two warm cycles, courtyard retains exactly420 tree nodes and4 window-focus callbacks; world retains2715 and5. Each has one loader in done state. The first direct courtyard entry precedes loader creation and is explicitly excluded from warm comparisons.

Resource counts stay225/245. Observed global object counts vary3759–3760/6667–6669; courtyard orphan count1 and world0 remain diagnostic. These are native lifecycle observations, not whole-process heap, GPU memory, performance, rendered-layout or online qualification. Independent I2-06 reviews the actual census separately.
