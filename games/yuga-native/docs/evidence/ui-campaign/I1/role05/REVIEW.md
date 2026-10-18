# I1-05 — persisted preferences across actual scene routes

Status: **16/16 passed**, exit 0, no engine errors, warnings or leaked-object diagnostics. This is a new I1 execution against the current promoted R7 combined source, separate from U4 preference edge tests and U5 screenshots.

The [test report](preferences-routes-r1.json), [exact execution](execution-r1.json), [source copies](source-r1/), [source pins](source-pins-r1.json) and [existing imported-resource pins](imported-resource-pins.json) bind the result. Godot 4.6.3, CPU2 and one LP/BLAS/OMP thread; isolated `/tmp/yuga-i1-preferences-routes-r1` save; 9.34 seconds. No import or render was run.

Actual settings callbacks save sensitivity 1.65, inverted aim, volume .25, fullscreen, disabled shadows and moonlit courtyard. Native GUI event dispatch remaps Piercing Dawn to J and toggles both ability-only effect reductions. Paused training mute stops action audio and Done restores pause. The real asynchronous courtyard→world→courtyard→scripted duel→courtyard routes replace and free the old owners.

World loads saved aim/key/effect preferences and propagates mute to traversal, siege, Rama action and invocation audio. Its actual volume slider changes the shared saved value to .55. Returned courtyard loads it while retaining display/aim preferences; controls display J. Duel and return leave the settings file bytes unchanged. Every source hash remains unchanged during the run.

Headless dispatch is not OS keyboard capture. Sound evidence is receiver volume/playing state, not listening quality. Fullscreen/shadows/night evidence is persistence and loaded values; no OS fullscreen application or visual lighting-quality claim. Four real scene transitions do not establish endurance/leak freedom; I2 owns longer sequence stress.
