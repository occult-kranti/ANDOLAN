# W4 bounded route/collision/overview parity

The current native fixture passes19/19 with exit0 and a clean log. [Final report](r5/report.json), [exact command](r5/command.json) and [source/receipt manifest](receipt.json) bind the observed result. Runtime source files remain unchanged.

Run from the repository root:

```sh
taskset -c 4 godot --headless --path games/yuga-native --audio-driver Dummy \
  --script res://tests/desktop_world_route_parity_cases.gd -- --report=/absolute/fresh/report.json
```

The fixture caps its own presentation process at60fps so the ordinary live HUD refresh runs without an external fixed-fps flag or a manually invoked layout. This cap is a test clock choice, not a performance result. Native movement/army schedulers are frozen during isolated predictive queries; the world presentation process remains active for actual overview/camera/marker observations.

Coverage is deliberately finite:

- Actual paving material parameters contain the same seven primary segments used by the atlas lane data. This is an input-contract check, not a rasterized paving check.
- Three short capsule sweeps and floor rays sample the Temple mid lane and the two Sun-side promenade/garden approaches.
- An observed blocker wall boundary matches its atlas footprint and blocks the configured .65m hero capsule. Disabling only that disposable scene collider and shifting only a copied atlas wall by3m both make the validator reject parity; both are restored and rechecked.
- Two opposite native deck samples have actual8m/10m top hits and capsule landing sweeps. Street-level crossing is blocked, while crossing above the top is clear. Their atlas footprints are XZ truth and do not encode a traversable ramp or a floor at every height.
- A Temple sky-ring ray reaches the actual0m floor, rather than an invented15m platform. A visual apron sample outside the nominal floor has no walkable floor hit. Clear and occluded rays use the real traversal obstruction method; no claim is made about every grapple availability condition.
- At a spawn and a raised deck, live→overview→live uses the actual cameras and preserves the world position, map point and heading through the ordinary presentation refresh. The source manifest, restored collider/map data, source files and army report remain unchanged.

The current world paving also receives18secondary rotation/circuit segments. The atlas draw path shows the primary lanes, not those secondary links. This fixture records that scope explicitly. Whole-world screenshot review must decide whether a quiet live map and a more complete overview need different route detail; adding every line is not an established readability improvement.

Historical runs remain under r1–r4. r1 is a fixture type-inference parse failure. r2/r3 passed the assertions but emitted an exit warning; verbose r3 identified only AudioStreamWAV/AudioStreamPlaybackWAV references. The fixture now gives a bounded80ms real audio-mixer disposal grace after freeing the scene, matching existing native HUD fixtures; unthrottled fixed-fps process frames alone did not establish that grace. r4 is clean, and final r5 also passes the ordinary headless invocation. This is fixture cleanup evidence, not a runtime audio leak repair.

The existing39 layout/29 navigation receipts remain separate. Neither those results nor this19-check gate establish all-terrain clearance, rendered route legibility, a complete navigation graph, physical walking on every deck, shared army elevation, browser/online authority or final graphics quality. Those claims need their own bounded traversal and actual-image evidence.
