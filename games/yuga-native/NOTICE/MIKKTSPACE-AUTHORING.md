# MikkTSpace authoring dependency

The offline tangent tool under `art/hero-rama-tangents/` uses Morten S.
Mikkelsen's MikkTSpace implementation at upstream revision
`3e895b49d05ea07e4c2133156cfa94369e19e409`:
<https://github.com/mmikk/MikkTSpace/tree/3e895b49d05ea07e4c2133156cfa94369e19e409>.

Copyright (C) 2011 by Morten S. Mikkelsen. The unmodified C source and header
retain their complete zlib-style permissive notices. Exact source hashes and
the upstream README are in `art/hero-rama-tangents/vendor/`. The original YUGA
C adapter is marked separately; it is not represented as upstream code.

This is an authoring-tool dependency, not a newly embedded game runtime,
commercial model, animation or texture. A generated tangent candidate requires
its own source/mesh/morph checks, provenance update and actual normal-map render
review before promotion. Tool adoption does not change the currently selected
Rama GLB or its canonical provenance notice.

The separate OpenMW object-pool experiment under
`docs/evidence/reuse-study/games/module-check/` retains its own GPLv3 source,
license and harness notices. That standalone research executable is not linked
into the native game. Source studies of TF2, ioquake3, OpenMW, OpenRA and Godot
demos have the adoption boundaries recorded in `docs/research/OPEN_GAME_CODE_REUSE.md`.
