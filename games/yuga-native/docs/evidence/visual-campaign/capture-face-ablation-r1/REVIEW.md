# Facial ablation diagnostic

Four original Forward+ framebuffers isolate a single runtime rendering property at a time on the frozen R3 hero. The same camera and all 164 bone poses remain fixed. Each property is restored before the next case; product source files and assets are unchanged.

Direct review of all four originals found the large cheek/neck triangular patches and stippled scalp shadowing markedly reduced when only the sun shadow toggle was disabled. Disabling the four active skin materials' normal maps, or disabling SSAO, retained these patches. This supports a directional self-shadowing diagnosis; it does not justify disabling world shadows or establish final facial art quality.

The next requested test retains shadows and compares depth/normal bias values with both portrait and gameplay framing. The rejected optional temple wisps are absent.

The capture uses a fixed 15 Hz process/capture clock and 60 Hz physics on software Vulkan; these paused images do not measure hardware FPS or continuous motion. `capture.json` pins source bytes, raw PNGs, four diagnostic property sets, camera and skeletal pose. Exact runtime text is archived in `source/`; binary source identities are recorded rather than copied.
