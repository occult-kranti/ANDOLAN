# I2-03 — seeded transition lifecycle stress

Sealed: **70/70 checks**, two deterministic shuffles (741903 and 283017), each32 real lifecycle scenarios plus3 final gates. Runtime copied from final I1 freeze `/tmp/yuga-i1-final-r1/ANDOLAN/games/yuga-native`; loader SHA256 `8ecaa8ae6359b2a5a89f1acbdd1d544058570a3effe656698b97a9adab7ec5e0`. No runtime changes.

Each seed alternates actual allowlisted tiny PackedScenes, invalid IDs/path attempts, queued duplicate activation/cancel, actual threaded loading cancellation and immediate reuse, cancellation before synchronous construction, missing-resource retry/back, live caller detach, queued cancellation and cancelled-signal reentry. Checks include paused/unpaused caller process and focus restoration, terminal counts, single persistent loader/layer, released ownership, abandoned-request drain, and exact event deduplication. Reports retain the full seeded order, before/after scene census and actual phase events.

Both commands ran on CPU2 with Godot4.6.3, no editor/import/3D rendering. Exact copied source and existing font caches remained unchanged; both engine exits0 with no errors, warnings or leaks. This is a tiny-resource lifecycle test, not product scene construction timing or rendered acceptance. Packaged native execution is I3-03.

Reproduce from the product directory:

```sh
taskset -c 2 python3 tools/ui-campaign/check-transition-stress.py --engine /usr/local/bin/godot --source /tmp/yuga-i1-final-r1/ANDOLAN/games/yuga-native --seed 741903 --report /tmp/yuga-i2-new-seed741903.json
```

Changed files: `tests/ui_transition_stress_cases.gd`, `tools/ui-campaign/check-transition-stress.py`, this evidence directory. Source commit at seal `83f88f840c59934155aec19d95b41d920d15c6c1`; the runtime test authority remains the pinned I1 freeze. Root owns optional CI catalog registration.
