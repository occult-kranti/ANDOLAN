# I1 content revision 6 — overview player identity

The native-offline profile now advances from **content revision5 to6** for the explicit overview presentation hold in `player.gd`. It pins the actual player SHA `54beb1c88df226983edf8bf4609b989731c0915103e590b97d303f77f845cc86` and aggregate `18c5f4913bfdb3241191e653de3cb58f5ecfa1720cd434c5070d04d08b30e4ed`. The runtime validator expects6; it does not silently refresh revision5. Browser and proposed profiles remain byte-equivalent as parsed data, all wire/envelope versions remain1, and native map, rules, features and remaining source pins are unchanged.

The original CI failure is archived in `ci-original-failure.log`. The reproduced [baseline source check](baseline-pin-check.json) fails exactly one of47 checks: the stale native player pin. It does not indicate a new gameplay or rendering failure.

Before any migration edit, the exact revision5 catalog was copied to `tests/fixtures/contracts/native-content5-catalog.json` and verified byte-for-byte against commit `83f88f840c59934155aec19d95b41d920d15c6c1`. Its SHA is `509ef9860dfc32ed0c9dd064bdd011feef01d9b6c90db755aa9c5e37bf29aae2`. The unchanged Godot4.6.3 validator generated the historical descriptor, SHA `f220b47c699754590d6415f500c6b5ff9793343a2e506d1a55af080497dd33a0`, before the expected revision changed. [Derivation receipt](revision5-derivation.json), exact helper and clean log are retained. Older revision3/4 fixtures remain unchanged.

Validation completed:

- **51/51 source-pin checks**: exact prior5 fixtures; actual source hashes/aggregate; unchanged other profiles, top-level wire/coordinate/limit contract and native non-content rules; only the player content-source pin changes from5.
- **259/259 Godot admission/lifecycle checks**, clean exit0. Ten new assertions independently derive the retained5 descriptor, reject its catalog and prevent failed catalog loading from replacing current identity, reject5 for fresh open/resume/migration/replay without mutating state, reject a forged revision number or stale digest, and admit valid6 after the rejection. Existing revisions1–4 and stream/replay bounds remain covered.
- The actual `run-visual-checks.py` catalog entries **native-content-pins** and **native-contract-admission** both pass with51+259 checks, zero warnings/errors and stable source. These are repeated targeted executions of the same two suites, not310 additional unique cases. Full catalog receipts/logs are under [catalog-run](catalog-run/summary.json).

Commands from `games/yuga-native`:

```sh
python tools/check-native-contracts.py --report=/tmp/content6-pins.json
env LP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 XDG_DATA_HOME=/tmp/content6-admission taskset -c 2 godot --headless --max-threads 1 --path . --script res://tests/native_contract_cases.gd -- --report=/tmp/content6-admission.json
env LP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 XDG_DATA_HOME=/tmp/content6-catalog taskset -c 2 python tools/run-visual-checks.py --engine /usr/local/bin/godot --output /tmp/content6-catalog --suite native-content-pins --suite native-contract-admission --max-cpus 1
```

Only the catalog, validator revision constant, source checker, admission tests and new historical5 fixtures changed. Exact before/after source copies are retained. No movement, action timing, UI layout or network implementation changed. This is validator/specification compatibility, not a live server migration. The earlier I3 package-r2 remains historical; it must be rebuilt with revision6 before new packaged capture acceptance. Root and the independent contract reviewer receive this source-pinned handoff; the package owner separately adds mandatory preflight. Unrelated screen/render suites do not need rerunning for this identity-only overlay.
