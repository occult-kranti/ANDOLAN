# YUGA: six specialist agents on an 8 GB laptop GPU

Updated 23 October 2026. The user confirmed a **Lenovo Legion 7i, RTX 4070 Laptop GPU, 8 GB dedicated GPU memory and 16 GB shared GPU memory**. Shared memory uses system RAM; it is not another 16 GB of local VRAM. The previous USA/US$7,000 RTX 5090 laptop study remains an upgrade comparison, not the current machine's specification.

This is the execution guide for six project skills and a local setup kit. It does not claim that six agent processes, local model inference or the complete game have been demonstrated on that laptop. The user will download model weights. Current source research is linked below; actual installed model revisions, sizes, terms and client compatibility must be recorded on the laptop.

**Follow-on implementation:** [GAME_BUILD_FARM.md](GAME_BUILD_FARM.md) and [the new research index](research/ps4-swarm-oct23/README.md) add actual cloud CPU generation, an executable job/quarantine runner, the retrieved PS4 thread and fresh GPU-service checks. The earlier study below retains its own scope; it does not override the newer exact receipts.

## Recommended stack and what each layer does

| Layer | First choice | Purpose and boundary |
| --- | --- | --- |
| Local model service | Ollama, bound to loopback, cloud disabled | Download/manage a selected local model; serve it to compatible clients. Set one loaded model and one concurrent inference explicitly |
| Coding agents | Codex CLI first; Claude Code and Kimi Code as separately qualified clients | Different clients can share the same local model. Installing a client does not download OpenAI's or Anthropic's hosted model, or make Kimi K2 fit in 8 GB |
| Fine-grained GGUF serving | llama.cpp as an alternative | Explicit weights, context and GPU-layer control; do not run a second resident model service by default. Verify each client's actual protocol before routing it here |
| Optional GUI | Jan, or a separately reviewed interface | A chat interface is not the task scheduler. Open WebUI has its own current license conditions; LM Studio's open CLI/SDK does not establish that its desktop app is open source |
| AI app installer | Pinokio, only when a selected workflow needs it | Runs third-party app recipes; inspect their commands, dependencies and model terms. Directory/venv separation is not a security sandbox |
| Game production | Existing Godot + Blender + glTF pipeline | Generated assets enter the same geometry, material, rig, motion, collision and performance gates as authored assets |
| Coordination | Six canonical project skills plus the local-swarm helper | Exclusive file ownership, explicit routing and a cooperative GPU command lock. This is a setup/planning kit, not a deployed autonomous agent platform |

See the pinned [runtime study](research/local-swarm-oct23/runtimes/README.md) and [client interoperability study](research/local-swarm-oct23/interop/README.md) for exact source versions, supported flags and limitations. Treat “state of the art” as a benchmark question: measure accepted edits, tool-call reliability, review defects, context needs, latency and memory on this project before choosing a larger model or more complicated server.

## Fit the workload to 8 GB dedicated memory

Start with **one quantized model in the 3B–7B class**, chosen from the actual locally downloaded inventory. A nominal 7B model at four bits is about 3.5 GB of raw weights before quantization metadata, runtime buffers and KV cache. This arithmetic is not a measured memory budget. Begin with a bounded context, such as 4,096 tokens, and measure; larger agent system/tool prompts may require more context than that and must not be silently truncated. A smaller verified model or hosted reasoning profile can be more useful than an oversized local model that constantly offloads.

The newer candidate is **Qwen3.5-4B**, whose official repository records its release and family support in llama.cpp. Start text-only with a compatible Q4 artifact. **Qwen3-4B-Instruct-2507** is an intermediate fallback; **Qwen2.5-Coder 3B/7B Instruct** remain historical coding baselines. The [runtime study](research/local-swarm-oct23/runtimes/README.md) pins the evidence. These are candidates, not a performance ranking: exact weight metadata, license, chat template, quantization and tool-call compatibility still need checking. No model is selected automatically by the setup kit.

| Workload | Assessment for the confirmed laptop |
| --- | --- |
| Six specialist roles sharing one small coding model | Practical architecture to test; inference requests queue and all roles do not run independently at full GPU speed |
| Six separately resident 7B models | Not an 8 GB plan; share one service/model instead |
| TripoSR, published about 6 GB single-image requirement | Candidate for a separate GPU session with the coding model unloaded; actual driver, dependency, peak-memory and output checks remain unrun |
| TRELLIS, published minimum 16 GB | Exceeds dedicated VRAM; any community offload adaptation is a separate unverified implementation |
| TRELLIS.2, published minimum 24 GB | Exceeds dedicated VRAM; use a qualified larger-memory machine |
| Hunyuan3D 2.1, published 10/21/29 GB shape/texture/combined | Exceeds dedicated VRAM for the published configurations; code/weight/output terms also need review |
| Blender/Godot and a resident coding model together | Depends on the scene and measured headroom; pause/unload inference for large scenes, exports or GPU renders |

Keep at least 32 GB system RAM for a comfortable combined development workload; consider 64 GB if the exact laptop supports it and measurements justify the upgrade. These are recommendations, not an assertion about the installed RAM. CPU offload can use system RAM but may greatly reduce responsiveness. The Windows shared-memory figure is not a guaranteed CUDA allocation or performance level.

**Model routing and MoE are different.** This setup routes tasks to a chosen model/provider. A trained mixture-of-experts model routes tokens among its internal experts; the agent scheduler does not turn six ordinary models into such a model. For an MoE checkpoint, total weight storage, quantization and cache matter, not only its active-parameter count. A 30B four-bit checkpoint has roughly 15 GB raw weights before overhead; “3B active” does not make it a 3B-sized download or allocation. Kimi's large hosted/open-weight models must be assessed separately from its lightweight CLI.

## Local-only startup and client qualification

Use a supported Windows or Linux/WSL2 GPU setup and verify `nvidia-smi` reports the actual device. On WSL2, use the Windows NVIDIA driver/WSL support; follow current official setup guidance rather than installing conflicting kernel drivers blindly. Pin the model and runtime versions after a successful pilot. Preserve model files outside the repository.

Keep the model server and CLI clients in the same environment for the first pilot: all Windows-native or all inside WSL. A Windows-native server with a WSL client needs separately verified networking; `127.0.0.1` must actually reach the intended server. Do not solve a connection failure by exposing the service publicly. The helper's cooperative command lock requires Linux/WSL; its plan validator is portable.

For a **foreground Linux/WSL Ollama server**, after ensuring another service is not already occupying the port:

```sh
OLLAMA_HOST=127.0.0.1:11434 \
OLLAMA_NO_CLOUD=1 \
OLLAMA_MAX_LOADED_MODELS=1 \
OLLAMA_NUM_PARALLEL=1 \
OLLAMA_CONTEXT_LENGTH=4096 \
ollama serve
```

For a Windows-native foreground server, quit an existing Ollama instance first, then use PowerShell:

```powershell
$env:OLLAMA_HOST = "127.0.0.1:11434"
$env:OLLAMA_NO_CLOUD = "1"
$env:OLLAMA_MAX_LOADED_MODELS = "1"
$env:OLLAMA_NUM_PARALLEL = "1"
$env:OLLAMA_CONTEXT_LENGTH = "4096"
ollama serve
```

These are source-documented settings, not an executed laptop benchmark. Configure and restart the actual server process; variables set only in a client terminal do not reconfigure an already running daemon. The PowerShell example applies to that foreground process, not automatically to a future tray/service launch. Do not bind this tool-capable service to all interfaces or expose it publicly as part of setup.

1. Check the model inventory and select an **exact installed local ID**. Do not invoke a bare client command that may auto-pull a larger default. Keep cloud model tags disabled at the server; a localhost URL alone does not prove all work stays local.
2. Probe the service with the helper, then test a short generation, tool-call response and one read-only repository task. An inventory response does not prove generation or compatibility.
3. Validate the required API for each client. Current Codex OSS uses Responses API; a Chat Completions endpoint alone is insufficient. Claude Code's local route uses Anthropic-compatible endpoints and still runs the selected local model. Current Kimi Code configuration differs from the archived Kimi CLI; use the source-pinned examples, not mixed old flags.
4. Test a bounded edit in an assigned fixture, inspect the diff and run its counterexample. Interactive/manual tool permission modes and automated modes must be identified accurately; Kimi's prompt mode can override a manual default. Keep an automation worker confined to its assigned files and tools.
5. Only then use the agent on a production packet. Store secrets through each provider's supported local credential mechanism; never commit them or copy login files. Hosted Codex/Claude/Kimi routes are separately explicit, with their own credentials and usage costs. Do not silently fall back from local to hosted inference.

The [toolkit README](../tools/local-swarm/README.md) contains executable validation, inventory-probe and GPU-lock commands. The example deliberately leaves model identity unresolved. The GPU lock controls only commands that cooperate by using the same lock file. It neither unloads Ollama weights nor prevents a directly invoked program from allocating GPU memory. Before a 3D-generation/render session, finish requests, use `ollama ps`, then `ollama stop MODEL` for the exact resident model, confirm it is no longer listed, inspect free VRAM and run the existing [capacity preflight](../tools/ai-assets/README.md) with the real workload budget. Relaunch/requalify the coding profile afterwards.

## Six reusable skills and ownership

Canonical files are under the repository's `.agents/skills/`; they are project-local skills, not newly installed cloud plugins. [The skill index](../../../.agents/skills/README.md) provides direct links. Codex and the researched current Kimi Code support that location. For Claude Code, follow the interoperability document's supported discovery path or explicitly load the canonical file; keep a single authoritative copy rather than divergent skill variants.

| Worker | Skill | Scope |
| --- | --- | --- |
| W1 | `yuga-evidence-review` | Video/source provenance, reverse-engineering experiments, actual native evidence and independent QA |
| W2 | `yuga-ui-flow` | Launch/loading/settings/selection/HUD/results; input, accessibility and screen integration |
| W3 | `yuga-hero-art` | Rama form, hair, face, cloth, materials, retopology, rig/skin and hero LODs |
| W4 | `yuga-world-art` | Arena/city/swamp, lanes, modular buildings, armies/vehicles, collision and visual navigation |
| W5 | `yuga-motion-combat` | Continuous animation, action/effect/audio timing, traversal and authority integration |
| W6 | `yuga-models-build` | Model/server capacity, downloads/provenance, builds, packages and platform qualification |

The lead owns shared interfaces, final acceptance, common manifests, roadmap updates and release actions. Assign exclusive literal file paths before writes; an entire shared `scripts/` directory is not a safe worker assignment. W3 and W5 share a rig contract but do not overwrite the same exported assets independently. Serialize imports, exports and GPU captures. Use separate actual machines for real parallel rendering; creating more agent roles does not create more VRAM.

Each packet follows three bounded passes: **contract/source review → implementation with adverse cases → independent integration/visual review**. Rework responds to a named defect. Keep a backlog task ID, source/model pins, exact commands, outputs and rejected candidates. Research, tool installation, headless checks and images have distinct acceptance scopes; none alone closes a finished-hero or multiplayer milestone.

## Complete-game sequence using these same six owners

This maps to [the P1–P6 quality target](DEADLOCK_QUALITY_TARGET.md) and [FG00–FG15 production gates](FULL_GAME_PRODUCTION_ROADMAP.md); it does not invent a new guaranteed round count or mark the game complete. The complete native 3v3 match is an explicit intermediate gate before the 6v6 expansion.

| Existing gate | Six-owner integrated outcome | Evidence needed before advancing |
| --- | --- | --- |
| Tool qualification supporting P1 | W6 qualifies one local model/client; W1 verifies sources and output; W2–W5 supply bounded real tasks | Measured local task/tool reliability, source/weight provenance and no silent cloud routing; video claims only after access |
| P1: accepted Rama and arena | W3 hero; W4 arena; W5 motion/combat; W2 complete offline flow; W6 package/hardware; W1 independent review | Actual finished-looking geometry/materials, continuous combat/traversal, human feel/listening and physical-GPU results |
| P2: native authority | W5 simulation/prediction; W4 geometry/visibility; W3 replicated motion; W2 reconnect/state; W6 process/package; W1 adversarial tests | Two actually rendered clients agree with authority under delay, loss, duplicate inputs and reconnect |
| Intermediate FG06: complete native 3v3 slice | Rama/Hanuman/Sita, three lanes, private rooms/bots, complete start → result → rematch journey | Uncut rendered full match; authority outcome, rewards, tower/core, death/rejoin and rematch agree without developer intervention |
| P3: six distinct heroes and team core | W3/W5 complete kits and counters; W4 full lanes/units; W2 party/draft/results; W6 capacity; W1 human/automated review | Real 6v6 target behavior with bots/humans, readable compositions and stable match lifecycle |
| P4: fourteen-hero content | Same owners expand only through the accepted art/action pipeline | Fourteen distinct complete packages, full map, counters, animation coverage, accessibility and content-budget checks |
| P5: operated alpha | W5/W6 authority/services; W2 matchmaking/rejoin/reporting; W3/W4 content corrections; W1 independent player studies | Real hosted service operation, persistence, abuse handling, replay/support and recovery evidence |
| P6: beta/release | All owners repair observed defects; W1 independently qualifies exact packages | Sustained hardware/online tests, human balance/listening/accessibility, platform execution, delivery and live support |
| Deferred Android M1–M18 | Reuse accepted source assets and lessons through separate mobile owners/gates | Physical devices, mobile variants/touch UI, real 5v5, store/signing/services; desktop captures cannot substitute |

Current desktop campaign remains **17/78 accepted packets, 0/13 complete rounds**. Android remains **0/108 implementation packets across 18 planned rounds**. No completed packet is credited for this skill/setup work. Reforecast from accepted content-production and rework time after one complete hero/arena; six agents on an 8 GB GPU are a coordination strategy, not evidence of Deadlock-level quality.

## Videos, reverse engineering and current blockers

All three requested videos are recorded in the [video ledger](research/local-swarm-oct23/videos/video-ledger.json). Supported proxy requests returned CONNECT 403; titles, speakers, captions, timestamps and PewDiePie's actual setup remain unknown. No candidate tool is attributed to those videos. The user's later mention of **Ollama** resolves the earlier ambiguous “Plasma” wording without requiring a speculative product identification.

Independent primary sources explain useful differences: QuakeJS ports released engine code; noclip reconstructs scene rendering; REA connects analysis tools to an actual target. These workflows do not recover an absent Deadlock/Overwatch client, provide proprietary assets or produce authoritative multiplayer from footage. Use each method on a selected accessible input with a comparison oracle and recorded component/asset terms.

The cloud restored an older checkout during this task. The last pushed research checkpoint `eb0ecc79` is the recovery source; only newly verified/recreated outputs are claimed here. Its earlier ~425 MiB free-space measurement is historical. The restored cloud has about 29 GiB free at initial inspection, four CPU cores of quota, 32 GiB RAM and **no NVIDIA device**; this is still not a laptop/GPU inference test. YouTube network requirements remain saved but unapplied. Activation and a fresh request, or supplied accessible captions/video, are needed to finish the video inventory. Model/client installs, laptop inference and physical-game performance remain unrun.
