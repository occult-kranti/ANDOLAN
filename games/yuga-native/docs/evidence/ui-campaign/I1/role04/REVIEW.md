# I1-04 — combined action, clock and HUD synchronization

Status: corrected source **30/30** with the unchanged independent witness. Initial **29/30** runtime counterexample remains preserved. [Report](action-hud-r1.json), [execution](execution-r1.json), [source copies](source-r1/), [source pins](source-pins-r1.json) and [R7 imported-resource identity](imported-resource-pins.json) record the exact rejected candidate. Godot 4.6.3, CPU2/one thread, isolated save; 3.63 seconds, no error/warning diagnostics, no import/render.

All five actual ability requests enter the combined world runtime and its single rig action. Real SceneTree pause freezes combat/motion/army clocks and displays unavailable HUD. Resume produces one authoritative release and one motion release, with current ammo/cooldown text. Repeated HUD-only refresh cannot advance authority. Actual reset and terminal-rule tick synchronize action clearing, effects, outcome and disabled slots.

The overview witness accepts Kodanda, enters actual F1 overview, enables the native player/army callbacks and waits eight physics frames. Kit state, army elapsed, release count and unavailable HUD stay frozen. **The unreleased motion action clock incorrectly advances from 0 to .133333 seconds** because inactive player processing still advances the presentation. This is not a rendering or fixture-only failure. Root assigned the narrow player/overview repair to the motion owner, preserving title idle behavior and authoritative clocks. No player/motion runtime edit was made by this reviewer.

The independent 30-check witness remained unchanged for the corrected-source rerun. A separate actual overview pause/resume visual witness remains outside this headless report. This new I1 contract does not relabel previous U4 results or claim physical-GPU/OS-input/FPS quality.

## Corrected-source independent rerun

[Final report](action-hud-r2.json) and [exact execution](execution-action-hud-r2.json): **30/30**, exit 0, clean log, CPU2/one thread, 6.30 seconds. [Executed source copies](source-action-hud-r2/) retain the unchanged test plus exact runtime bytes. Player SHA-256 `54beb1c88df226983edf8bf4609b989731c0915103e590b97d303f77f845cc86`; world SHA-256 `1fc6869f6a6b96f5142de4cf41402f78cead76008dcfbba836e539f3ed3ecf99`.

The motion owner added explicit presentation suspension at the player update boundary, set by the existing overview entry/exit. The original independent test now holds the unreleased presentation clock while preserving all prior pause, release, HUD, reset and terminal behavior. Title-idle negative control and longer overview/resume checks belong to the separate [motion-owner witness](../role01/overview-sync/), not this 30-check count. Neither this rerun nor the source snapshot is rendered acceptance.
