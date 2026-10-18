# U4-01 native resize and reachable settings footer

Accepted for independent UI review: focused actual-engine checks improve from 6/17 to 17/17. Existing launch (35), pause navigation (17), and integrated flow (25) checks also pass. No rendering or OS-window-manager acceptance is claimed.

The actual Window retains the production 1280×720 content base. The test changes physical size to 960×540 and content scale to 1, 1.25 and 2, then returns to the original size. Physical size alone does not reduce logical canvas size under the configured stretch. The 2× case actually exercises a 640×360 logical canvas. The title now establishes a 960×540 native minimum; the engine clamps a requested 64×64 window to that usable minimum. This is an explicit supported-window boundary, not a claim that 64×64 can present the full interface.

Previously, a lower focused launch or pause action became clipped after a live scale change. Deferred reveal now retains the same focus owner and scrolls it into view after layout. It does not grab a different action. The courtyard and world pause paths preserve their existing clocks and return routes.

Settings now has a fixed 48-pixel Done footer outside the scrolling body. All options remain in the body, and its existing Card/Scroll/Content path and persistence callbacks remain intact. Done stays visible at both ends of the body for all three scale factors. Native keyboard dispatch changes sensitivity, verifies the real ConfigFile and player value, reaches Done through Tab, and returns to the exact Settings title opener without starting practice. Tests use isolated user data.

Changed runtime scope: launch_shell.gd window minimum and focus reveal; courtyard.gd settings-only layout plus pause/modal resize reveal; confluence_world.gd pause layout reveal. The shared theme was changed concurrently by its owner; candidate and regression reports pin the exact revisions they observed. This worker did not edit theme, HUD, reset/return routes, loader, animation or combat state.

The baseline's eleven failures, window-metric probes, focused logs, and regression logs are retained in logs-and-probes.zip. candidate.json contains the seventeen concrete checks and source hashes. Existing integrated flow intentionally injects missing-resource failures; its successful final status is separate from those expected diagnostics. No source was staged or committed by this worker. U2 and the frozen U3 source snapshot remain preserved.

Next gate: U4-06 independent counterexamples and centrally owned actual UI capture, including the fixed footer at the minimum supported window and 2× scale.

## Independent U4-06 teardown counterexample and correction

UI06 reproduced deferred callbacks that began after detachment, or resumed after detachment, causing null-tree errors despite passing focus assertions. The launch, courtyard settings/modal and world pause reveal helpers now reject detached/queued owners at entry and after each await. Launch's sibling focus-when-unclaimed helper also rejects hidden/detached/queued owners. The original17/17 report remains preserved: it did not test this lifecycle boundary. The corrected focused resize suite passes17/17 again; UI06 owns the independent lifecycle rerun and clean-engine-log gate. No focus, layout or gameplay thresholds were relaxed.
