# Restored compact-screen render — no-progress failure

The actual installed-engine attempt produced **zero PNGs** and stopped at the unchanged120-second no-progress watchdog after native readiness. The wrapper exited1 with `TimeoutError: No new engine log bytes or PNG count after native-ready (120.0s)`. The intended eight actual title/world/overview/guide images were not produced. Headless12/12 preparation remains a distinct result.

The immutable child was `a02bc44bcb09cd9b80c0afd4d5a18d42a72664e23aa4961875cb572bfb39e2b5`, with unchanged original full shaders. This attempt used recovered103-file Godot shader cache and **no Mesa cache**, onCPU2,3/llvmpipe. It does not establish cold startup: Godot cache was explicitly seeded. No live native stack was obtained before timeout, so this particular failure is not independently diagnosed as the earlier proven Version-mutex/worker-cycle defect.

Exact runner, command, process observations, cache manifests and original engine/Xvfb logs are retained. Do not repeat this unchanged attempt or loosen the timeout as a graphics fix. W1 owns a pinned public-source template baseline and an independently attributable scheduler experiment if the source baseline reproduces the problem. No production engine or shader was replaced.
