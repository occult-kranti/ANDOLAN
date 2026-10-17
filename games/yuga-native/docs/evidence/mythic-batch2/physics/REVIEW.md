# MYTH-07 bounded physics experiment

Source baseline `eedfd1f94181cddfad293e3e95f126b96c72baed` plus the exact accepted-source hashes in HANDOFF.json. This is a headless offline query comparison, not a live network match or production collision acceptance.

Final evidence: 48 TypeScript tests, strict typecheck, 24 actual Godot checks and 1,586 comparison checks pass. Both implementations execute 1,474 queries in the declared normal fixture. Rays preserve bridge/road and stacked-deck support; high-speed sweeps and a bridge-edge floating-point sample have measured divergences. The decision recommends a single headless Godot authority for the next native prototype. `cross_engine_equivalence` remains false.

R1 retains invalid ceiling-clearance and typed-JSON assertion failures with hash-matched source. R2 retains the genuine bridge-edge support mismatch before the comparator explicitly reported that bounded ambiguity. No tolerance was enlarged to hide it. Independent review caught an unsafe interpretation of clear sweeps from initially overlapping actors; both streams now query overlap first and refuse movement. Original and closure probes are retained.

The separate bridge-axis review runs 102 actual-node checks over actor/minion/neutral aiming and projectile long-axis orientation, plus nonfinite rejection and collision-free presentation. It confirms the corrected projectile pitch on the hash pinned in that report. These checks do not rasterize art or exercise transport.

Source snapshots here are historical evidence. Runtime files remain in their normal project paths. Reproduce with `python3 games/yuga-native/tools/physics/run.py --output /tmp/yuga-physics-fresh`. Root owns the batch manifest and parent roadmap status.

## Node22 CI runner compatibility

After the r6 evidence was archived, the runner added explicit `--experimental-strip-types` for pinned Node22.14.0. Runtime fixture, TypeScript query implementation, Godot harness and comparison code did not change. Original r6 runner and handoff remain as historical-run-r6.py and historical-handoff-r6.json. Current accepted-source runner matches node22-compatible-r7/receipt.json, which repeats the48/24/1,586 checks successfully; a separate actual Node22.14.0 execution passes48 reference tests. Its version and output logs are retained. The r7 receipt was produced under the workspace Node24 engine with the compatible flag; it is not mislabeled as the separate Node22 execution.
