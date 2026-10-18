# Native content8 — stale-pin export/CI correction

Source85d5831dd8586a264caa93a7ba4625d1ec0b7f21 retained native content7 pins for the old army/minion code. The source preflight correctly failed2 of54 checks before export. This packet preserves the exact original log and reproduced52/54 report. No engine export or workflow was dispatched here.

The root-approved correction is a new native content revision8, not relaxation of the content7 guard. Exact raw content7 catalog bytes from85d and its descriptor derived by the prior actual Godot validator are retained under tests/fixtures/contracts. The previous validator source/hash and derivation command/output are preserved. Catalog7 SHAcfb956462042a867f6ac1a51d7be77fc98310acfae8d15d112456fc2a19eb191; descriptor SHA7ea8e560742081487df9d8b15b25e122b2f2a363fa6bead4f569559dd63354ef.

Only four catalog fields change: the two admitted source pins, aggregate and native content revision7→8 (`manifest-delta.json`). Browser/proposal profiles, all envelope/wire versions, coordinates, limits, map and non-content native rules remain exact. The runtime change is solely its expected native content revision. Native contracts are not in their own15-file content-source set, so no self-hash cycle is introduced. The visual helper dependency is not claimed as wire-pinned art.

| Source | Previous content7 SHA | Current content8 SHA |
|---|---|---|
| lane_army.gd | f6a56f3e7b4144a26caaed31eb3e64cfd1594de2847627de43af09961a37fb0c | 10dc1372ac2580b5ca20573a6a28f5a01e7973c731965c87a2473d7859eb032e |
| lane_minion.gd | 90fe2d84f5c408b4b99779b00c11e59e850c1bb4f88dafb42a8a5aba74cc119c | 39e9dd57dc229bb6d99dcf84a42b5e6ef5919d203dfc2092d5f8dae7aa6dc387 |

Aggregate f189a381ff896dad9e6bd09963ced1c523a3c6b1912f8e7d1f780ec991ab2ef2 →570353754be882faa6243f7cc2d504b9d841d6f5015088d51708db53c25c0589, computed with the existing compact sorted-key JSON rule.

## Focused verification

- Source checker **58/58** (the original54 plus four new preservation/current-revision guards). Revision6→7 minion-only history remains checked against retained7. Revision7→8 allows exactly army/minion pins and excludes all other native rules changes.
- Actual Godot native cases **279/279**, clean exit0,0.744s: retained revision7 descriptor derivation, catalog/open/resume/migration/replay transactional rejection, version-only forgery and previous-digest forgery reject; valid current8 admission still works after rejection. Earlier revision/lifetime/bounds/replay tests remain.
- Actual source-proof/package fixtures **21/21**, clean exit0,1.059s. All four revision6/7 retained fixture files reject both missing and mutated bytes. Finite package input closure extends3/4/5→3/4/5/6/7; no production export/package ordering or engine policy changed.

The first package-fixture run failed4 of21 cases because that old fixture assumed contracts preceded the later UID/engine identity prerequisites. Its failure is retained. The fixture now supplies valid unrelated prerequisites through scoped mocks; the contract subprocess, source hashing, proof-binding and rejections always run for real. The old83f player-mismatch fixture reconstructs every non-player content input from that exact historical Git commit and asserts its expected SHA, preventing current army/minion changes from confounding the intended stale-player negative. Current-player mismatch remains. Historical sources/proofs are restored and current proof equals the initial proof.

Documentation now states current native Rama health and the exact15-file ledger; historical Batch2 results are labeled. No gameplay/map/renderer/UI changes, imports, new textures, bulk copies, export or commit occurred. Root owns the fresh source successor/CI/export; passing local validators is not package or live-network acceptance.
