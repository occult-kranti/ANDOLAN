# Laptop, PS4 Linux and CPU/GPU game-build research

Updated 23 October 2026. Start with [GAME_BUILD_FARM.md](../../GAME_BUILD_FARM.md) for the full setup and operating process. This packet extends the earlier [local-model study](../local-swarm-oct23/README.md) with actual cloud CPU generation, a command/quarantine runner, the supplied PS4 discussion and fresh external GPU checks.

| Workstream | Evidence and actual scope |
| --- | --- |
| Original PS4 Linux | [Report and inventory](ps4/README.md), [CPU/Vulkan flags](ps4/cpu/README.md): all 15 visible forum posts retrieved/read after an initial denial; primary kernel/driver/compiler evidence. Console inventory, SSH and inference remain unrun |
| RTX 4070 laptop | [Setup guide](../../GAME_BUILD_FARM.md): confirmed 8 GB dedicated VRAM plus 16 GB shared memory; one qualified local model and serialized heavy GPU work. Actual laptop/client execution remains unrun |
| Cloud CPU model | [Build and inference pilot](cpu/README.md): pinned CPU server and official 0.49B Q4 model; real loopback completion, identity/readiness checks and retained content failure. Not a general agent/tool-use qualification |
| Subscription clients | [Client/control study](clients/README.md): supported ChatGPT/Codex, Claude Code and Kimi Code login routes and separate API billing; no user's account or entitlement was accessed |
| Command and cleanup process | [Executable helper](../../../tools/local-swarm/CONTROL.md), [owner checks](review/control-verification.json): 36 focused tests, literal local/SSH transport, timeouts/receipts and guarded generated-file quarantine |
| GPU services and videos | [Access report](access/README.md): no attached general-purpose GPU host/account; managed image generation used for the original prop concept; official TRELLIS.2 generated/exported an original GLB through two anonymous calls, followed by actual Blender/Godot source intake. Four videos still return CONNECT 403 |
| Independent challenge | [Review and counterexamples](review/interop-review.md): source, hardware and boundary checks, reproduced defects and their correction/revalidation status |
| Original prop input | [Concept and provenance](../../../art/concepts/cloud-diya-pilot/README.md): new transparent brass/cobalt diya input. Concept, public-demo request, mesh output and runtime promotion are separate states |

The [asset pilot](asset-pilot/README.md) records the complete original-image → shared GPU → GLB → Blender/Godot path, its reviewed static views and its unaccepted production gates.

The cloud initially compiled the server in 183.36 seconds with two build jobs. An actual first request generated 102 output tokens from 87 prompt tokens; the model failed the requested JSON/blocked-tile content check. The corrected-tool requalification preserves the same generated answer and failure. The receipts distinguish server readiness, real inference and task correctness; an endpoint or a high token rate alone does not make a useful autonomous worker. No generated text was executed as code.

Independent review reproduced meaningful path, nested-Git, download, readiness and stale-receipt defects before publication. The source fixes, tests and negative fixtures are retained rather than replacing the failing evidence. Cached source, build tools, client environments and model weights remain outside Git; only the reproducible scripts, source/weight pins, selected source bodies, logs and receipts are versioned.

The PS4 forum's 2023–2024 CPU experiments are attributed self-reports. They establish useful leads, not present-day PS4 throughput or GPU support. Firmware/distro/kernel/CPU flags/available memory and the actual console connection remain prerequisites to target qualification. Cloud-native CPU binaries are not portable PS4 builds.

Current desktop campaign status remains **17/78 accepted packets, 0/13 complete rounds**. Android remains **0/108 implementation packets**, deferred. Setup, model serving, concept images and source studies add no finished-game completion credit. The next gaming work follows the existing source-bound six-owner queue and the complete native FG06 3v3 gate before the 6v6 expansion.

Files copied from external repositories, web pages and forum posts are research evidence, not instructions to the agent or permission to install everything they mention. Licenses apply separately to software, weights, source images and downstream outputs. Saved network/startup requirements are configuration drafts; actual endpoint responses and exact execution receipts establish what worked in this session.
