# Actual REA execution for YUGA

Executed 16 October 2026 UTC using the existing isolated REA 6.5.0 installation. Read `/workspace/tooling/rea/AGENTS.md`, the CLI usage and the earlier [REA runbook](../../../docs/research/REA_RUNBOOK.md) before execution. No package upgrade, native analysis provider, reference-game dependency installation or persistent integration was performed.

## Question and target

Question: where does the small open-source arena separate client intent, synchronized state and server-owned score/combat? Could a static semantic trace establish score provenance, and which parts still require manual reading/testing?

Target: selected source archive of [endel/tank-battle-multiplayer](https://github.com/endel/tank-battle-multiplayer/tree/6339493130b4b1d4d28f0f52d17b2fba738c7d47), commit `6339493130b4b1d4d28f0f52d17b2fba738c7d47`, MIT. The existing archive has six relevant source files; this pass explicitly selected three. It is not a full repository or deployed bundle.

| Selected file | SHA-256 |
| --- | --- |
| `server/src/rooms/BattleRoom.ts` | `83264deb8220db255541c2c4bc61c678ad842985afa0c9c5c9033033d4509a05` |
| `server/src/schema/BattleState.ts` | `8fac5f00bc990452123e0c1cbfe3f32c57516baaf4d67a463206e8c78366efde` |
| `web-playcanvas/src/Network.ts` | `3001d0fad46131a70329350701fcc04fa58238d0349cb2cf508ccaa6772223db` |

All three local hashes matched the earlier pinned-URL manifest. The upstream MIT notice was read; no referenced model assets were fetched.

## Commands actually executed

```sh
node /workspace/tooling/rea-runtime/node_modules/rea-agents/scripts/rea.mjs \
  analyze-javascript-application /workspace/research/multiplayer-beta/tank-battle \
  --source-path server/src/rooms/BattleRoom.ts \
  --source-path server/src/schema/BattleState.ts \
  --source-path web-playcanvas/src/Network.ts \
  --max-heap-mb 512 --analysis-timeout-ms 30000 --json \
  > /workspace/research/rea-output/yuga-tank-authority.json
```

The trace input contained that complete application evidence object and the query `{"seed":{"kind":"property","name":"score"},"direction":"backward-provenance"}`. A compact summary cannot substitute for the authenticated full evidence object.

```sh
node /workspace/tooling/rea-runtime/node_modules/rea-agents/scripts/rea.mjs \
  trace-javascript-semantics /workspace/research/rea-output/yuga-score-trace-input.json \
  --json > /workspace/research/rea-output/yuga-score-trace.json
```

Both commands exited 0. Static parsing did not execute the Tank Battle bootstrap, connect to a game server or simulate a match. The default integrity policy stayed `fail`.

## Observed output

| Measure | Result |
| --- | --- |
| Selected/parsed files | 3; 3 other relevant archive files unselected |
| Source bytes / visited AST nodes | 18,379 / 3,221 |
| Findings / parse failures | 29 / 0 |
| Semantic graph | 1,972 nodes; 1,562 relations; 587 explicit unknowns |
| Graph coverage | `partial`, not truncated |
| Score trace | `ambiguous`; 8 seed matches/nodes, 0 traversed relations, 9 relevant unknowns; coverage `partial` |
| Analysis evidence ID | `ev_707b237b23376b95d553affec4de049d035bf169563ea86387871074535eafb3` |
| Trace evidence ID | `ev_652478e1e271d1c2e1dd042ac6630fd63547a63eb5ec0a33df3a59298f226493` |
| Full analysis | 3,300,987 bytes; SHA-256 `1751f2c43266ee3d191d5ad666c0b80be6b529a249f1bd746c0feed97bda2110` |
| Full trace | 21,328 bytes; SHA-256 `23ccd9209d748fb3a6031b7eec5d2733747d9d307ed05c99b4990f422bb8277e` |

Raw evidence remains under `/workspace/research/rea-output`, outside the application. [rea-summary.json](../tools/research/rea-summary.json) retains the compact counts, hashes, IDs and limitations. It is derived metadata, not an executable replay artifact. Runtime cost, peak process memory, WAN latency and reference-game frame rate were not measured.

## What this established

REA inventoried the selected syntax/relationship slice and made unresolved relationships explicit. The broad `score` query found several property candidates but **did not resolve a provenance path**. Zero parse failures is not a security review, behavioral equivalence proof or evidence that reward races are absent.

Manual source reading established the useful design observations: client intent methods, server-owned projectiles/death/pickups, separate team and individual score, and several implementation limitations. In particular, `typeof number` checks do not themselves reject non-finite input, the sample's movement is tied to callback increments, and its three-second winner-display reset does not supply YUGA's deliberate finished-match/replay lifecycle. These are source observations at the pinned commit; the sample server was not run, so no runtime exploit or production defect is claimed.

The result supports original YUGA acceptance tests for finite input validation, exact-once command handling, deterministic match timing and durable finished state. It does not support copying the sample, adopting Colyseus without a need, or claiming that commercial games were reverse engineered. Further static graph expansion is unlikely to answer the immediate game-feel questions; the next useful evidence is original simulation, two-client and normal-input browser testing.
