# R5 compact knot attachment — inactive

R4 visibly detached the unchanged topknot from its reduced crown in the rear and cast originals. R5 adds one compact gathered attachment beneath that same knot. It preserves the accepted smooth crown and sash UVs, every R4 active vertex and triangle, knot/tie positions, reduced silhouette, nape and material. No runtime helper is enabled.

`build_candidate.py` pins the sealed R4 builder and the exact three `hair-silhouette-r1/candidate-r4-accepted-uv` parents. It appends a zero-alpha head104-bound attachment to the existing hair primitive. The complete old BIN remains an exact prefix, and all previous active arrays and indices are exact prefixes. Existing JSON outside new accessor/view/buffer references and the hair primitive is preserved.

From `games/yuga-native`, regenerate into a fresh directory using the existing Python environment with NumPy and SciPy:

```sh
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 taskset -c 3 /workspace/tooling/yuga-native-python/bin/python art/hero-finish/hair-knot-bridge-r5/build_candidate.py --output /tmp/yuga-hair-r5-rebuild
```

The recorded runs used a 4 GiB address-space limit and 55-second timeout per command. `candidate-r1/manifest.json` pins the actual generated trio. `check_candidate.py` checks complete-triangle head/gold clearance, both attachment ends, exact source preservation and the declared 37-pose replay. `check_draw_contacts.py` replays only new triangles against 348 captured draw samples, actual imported hands, source bow/string and conservative arrow capsules. `check_secondary.py` checks attachment to fully anchored head104 hair and 32 bounded collar stresses per LOD.

The reports, exact commands and source receipt live in `docs/evidence/desktop-finish/hair-knot-bridge-r5/W2`. These are offline source checks using pinned ancestor native tapes. They do not execute the R5 candidate or establish visible continuity. Private import followed by the same four actual baseline/candidate views remains required. Inspect the full rear and cast originals for a connected gathered root, preserved knot/tie clearance and no bulky return of the old crown mass. The lower nape is deliberately unchanged.

The source payload intentionally retains previous buffers for exact preservation proof. Shipping compaction is a separate future step after art acceptance; do not silently rewrite this candidate or compose the unaccepted shoulder proposal.
