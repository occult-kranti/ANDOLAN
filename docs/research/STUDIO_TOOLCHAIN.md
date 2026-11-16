# YUGA studio toolchain — executed 15 November 2026

The active hero game is restored on `work/yuga-studio` from `origin/game/yuga-native-production`. The separate ANDOLAN city game remains in `apps/`.

Run `bash tools/cloud/setup-studio.sh --help` for the reusable Ubuntu 24.04 setup. Its individual install/qualification commands were executed in this session; the helper itself passed shell syntax/help checks. Tool storage is outside the checkout at `/workspaces/tooling`.

| Tool | Installed and exercised |
| --- | --- |
| Godot | Official 4.6.3 Linux and Windows archives/payloads verified against repository pins; Linux `/usr/local/bin/godot` starts, imports and exports the native PCK. Windows is downloaded, not executed. |
| Blender | Official portable 4.3.2 matches the documented native art baseline; archive SHA-256 and background factory-startup pass. Run `blender4.3`. Ubuntu archive 4.0.2 is also installed. Existing game asset exports require their own validation. |
| Rendering/capture | Ubuntu Mesa 25.2.8 llvmpipe, Vulkan tools, Xvfb/XTest, FFmpeg 6.1.1 and Pillow 12.3.0. Actual native window capture completed. |
| Python | `/workspaces/tooling/yuga-native-python312/bin/python` has NumPy 2.3.5, SciPy 1.15.3 and Pillow 12.3.0 from wheels. Default Python 3.14 was unsuitable for the pinned SciPy wheel; the attempted source build was stopped. |
| Browser | Playwright Chromium 1248 / Chrome for Testing 156.0.8078.4 installed. Ubuntu's Chromium snap wrapper did not provide a working browser. |
| Search | ripgrep 14.1.0 installed. |

Baseline native checks passed: source pins **58**, native contracts **279**, Rama abilities **85**, and the complete headless screen catalog **47 suites / 971 checks**. The original main city baseline also passed typecheck/lint, **134 tests**, production build and standalone build before branch restoration. These are separate products and validation scopes.

The official Godot Forward+ runtime emitted both boot and native-ready markers but stayed on the preparing-scene overlay through the recorded 53-second attempt on software Vulkan. Its unchanged captures and terminated exit remain in the evidence; this observation does not prove it would never finish. Compatibility rendering opened the actual title, and clicking native Quit exited 0. Its expected VSync/subsurface-feature warnings remain in the log. The compatibility title is a reduced-effects presentation check and does not establish Forward+ art quality or physical-GPU performance.

Evidence: [toolchain summary](evidence/studio/toolchain/summary.json), [official engine provenance](evidence/studio/toolchain/engine-downloads.json), [compatibility title](evidence/studio/before-title-compatibility.png), [Forward+ loading stall](evidence/studio/before-title.png), and native input/log records in `evidence/studio/toolchain/`. Full regenerable reports remain under `/workspaces/scratch/studio-toolchain`.

No commercial game binaries/assets were installed; no REA MCP or agent configuration was changed by this setup. Research-only REA installation/qualification has its own source and dependency record. Game packages and generated design images require separate acceptance from these tool checks.

## Reused public runtime, qualified later in this session

The project's published Linux runtime was recovered from its exact recorded
archive (SHA-256 and byte count verified) without extracting or running the old
game PCK. Its source/patch/build/license closure was checked. The only local
patch against that pinned public Godot source changes native pipeline-task
priority; no engine source was rebuilt in this session.

That runtime loaded the current first-candidate PCK in Forward+: the actual
title appeared around 90 seconds and Confluence around 165 seconds, followed
by ordinary native Quit 0. These are software-render observations with a
different window from the official attempt, not a causal speed comparison.
The successor Linux package selects this reviewed runtime explicitly and bundles
its proofs; the official editor remains the exporter and Windows remains official.
See [recovery/provenance](evidence/studio/public-runtime-source.json),
[actual Forward+ title](evidence/studio/forward-probe/02-qualified-title.png),
[actual Forward+ world](evidence/studio/forward-probe/04-qualified-world.png)
and [final delivery](STUDIO_DELIVERY.md).

The separately recovered public-source Godot template runtime (`e69af4f6…`) was verified by the canonical package helper against the existing pipeline-priority build proof. Probing the first current candidate PCK produced actual Forward+ title and Confluence world frames, followed by native Quit 0. The quit request was recorded at 180.74 seconds from helper start; cleanup finished about seven seconds later. This does not establish that it is faster than the official runtime, whose recorded attempt ended earlier. See [probe evidence](evidence/studio/forward-probe/summary.json). The existing packager bundles its exact source/build/license proofs when selected for the successor Linux package.
