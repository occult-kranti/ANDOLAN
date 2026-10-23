# Existing RTX 4070 laptop: local model runtime evidence

Research date: 2026-10-23. Research only: no runtime installation, model download, GPU inference, or repository modification. Exact primary-source revisions and SHA-256 checksums are recorded in `sources.json`; all retrieved files are below 127 KB.

## Hardware and scope

The user confirmed **8 GB dedicated GPU memory and 16 GB shared GPU memory**. Plan against **8 GB VRAM**. Shared GPU memory uses system RAM; it is not another 16 GB of dedicated VRAM and does not create a 24 GB GPU. This confirmation is the evidence for this user's hardware. NVIDIA/Lenovo manufacturer pages were not fetched because their hosts are absent from the selected executor's allowed-domain snapshot.

Actual installed system RAM was not established. A 32 GB system-RAM target is a reasonable planning baseline for the editor, browser, build tools, agent processes, and occasional offload; 64 GB is an optional heavier-workload target. These are recommendations, not observations or guaranteed requirements. Neither increases dedicated VRAM. This report makes no purchase recommendation and does not spend the prior USA $7,000 budget. A 5090 **laptop** comparison must remain separate from the existing 4070; do not conflate laptop and desktop GPU memory specifications.

## Recommended first configuration

Use **one inference backend, one resident model, and one inference request at a time**. Six roles are six independent task descriptions, queues, and handoff records. They can share a single resident model. They are not six simultaneously resident models and need not all use different model weights.

| Candidate | Initial test | Intended use | Evidence limit |
| --- | --- | --- | --- |
| Qwen3.5-4B, a compatible Q4 GGUF selected by the user | 4,096-token context; one request; start with text-only tasks | Newer candidate for bounded coding, routing and tool-use evaluation | Official current README names the 2026-03-02 release and supports Qwen3.5-series text/vision with llama.cpp. Exact GGUF, tokenizer/template, tool-call compatibility, license and laptop fit remain unverified. |
| Qwen2.5-Coder-3B-Instruct GGUF, Q4_K_M | 4,096-token context; one request | Small edits, routing, extraction, summaries; evaluate whether its quality is adequate | Official preserved README lists the 3B Instruct GGUF. Exact selected artifact size/license/checksum and laptop fit still require inspection. |
| Qwen2.5-Coder-7B-Instruct GGUF, Q4_K_M | 4,096-token context; one request | Primary coding candidate if a representative task fits and passes review | Official preserved README lists the 7B Instruct GGUF. Fit and speed are hypotheses, not benchmark results. |
| The same accepted model at 8,192 tokens | Only after the 4,096-token test passes with adequate measured VRAM margin | Larger bounded handoffs | Re-measure peak VRAM, RAM, prompt processing time and output quality. Model maximum context is not a laptop recommendation. |

Use instruction-tuned weights for role conversations. Base/FIM variants are a separate completion workflow. Quantization reduces weight storage but does not remove KV cache, runtime buffers, temporary activations, GPU display usage or operating-system overhead. Exact model-file bytes are not the inference memory requirement.

The Qwen2.5-Coder candidates are conservative **historical baselines** for an 8 GB fit-and-quality experiment. This report does not rank any candidate as the newest, fastest or strongest current coding model, and includes no local comparative benchmark.

### Newer small-model candidate: Qwen3.5-4B

The current official Qwen3.5/Qwen3.6 repository resolves to a shared Qwen3.8-family source at commit `2ea10dc725823bf7c3e21ce8557cbe15245132ae`. Its README still explicitly names **Qwen3.5-4B** in the 2026-03-02 release entry (line 52), describes the Qwen3.5 family's coding and agent capabilities (lines 34–44), and documents llama.cpp text/vision support for the family (lines 132–136). The broad family capability descriptions do not establish the 4B checkpoint's tool-call reliability, coding quality or installed-runtime compatibility.

For the user's download selection, that release entry links the official [Qwen3.5 model collection](https://huggingface.co/collections/Qwen/qwen35). Select the entry named **Qwen3.5-4B** and inspect the exact model card, license and compatible GGUF conversion before downloading. The README does not provide a direct 4B GGUF artifact URL, so none is represented here as verified. The linked collection/model cards were not inspected in this restricted cloud session. The source's repository `LICENSE` is Apache 2.0, but its model-license section explicitly directs readers to the license distributed with each set of model weights; the repository license alone is not weight-license evidence.

For memory planning, **4B is the published checkpoint size label**, not an `A4B` suffix indicating only active experts. The exact total/active parameter counts and architecture of the selected artifact remain pending model-card/config inspection. If its total weight count is approximately four billion, ideal uniform four-bit weight storage is approximately **2.0 GB decimal / 1.86 GiB**. This is only an arithmetic lower bound: quantization metadata, higher-precision tensors, cache/state, runtime buffers, display usage and any vision components add memory. It makes Q4 a plausible 8 GB evaluation candidate; it does not establish fit or permit a 2 GB runtime-memory claim. Keep the initial task text-only and the context at 4,096; verify behavior with the exact downloaded artifact and runtime before using its tool calls.

If this newer checkpoint fails the loading, compatibility, memory or quality gate, retain the historical Qwen2.5-Coder 3B/7B profiles. An additional grounded intermediate fallback is **Qwen3-4B-Instruct-2507**: the official Qwen3 README at commit `7a2f61ffc7a20d47efcd2bf97f6f2bf52729042e` directly links its [exact model card](https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507) in the 2025-08-06 release entry (line 68), describes coding/tool capabilities for Qwen3-2507 (lines 30–42), and states Apache 2.0 for its open-weight models (lines 395–398). That card and a corresponding quantized artifact remain uninspected. This is a named alternative, not a recommendation to download every candidate or a performance ranking.

**Do not promote Qwen3-Coder-30B-A3B as a 3B-memory model.** Its A3B designation describes active computation; the total model is still approximately 30B parameters. Even an idealized uniform four-bit representation of 30 billion weights is about 15 GB decimal before scales, metadata, KV cache and other overhead. Full residency is outside the 8 GB profile. CPU/RAM offload is a separate latency tradeoff to benchmark, not evidence of 8 GB GPU fit. Similarly, 14B Q4 is not a safe initial 8 GB profile.

## Runtime configuration

Ollama is the simplest default for managed local model serving. `llama.cpp` is the direct-GGUF alternative when explicit command-line control is preferred. Jan is an optional desktop interface. Avoid running multiple model backends against the same GPU during initial measurements; each backend's own resident-model limit does not govern the other processes. vLLM is optional infrastructure and is unnecessary for this initial single-user 8 GB workflow.

For a user-installed Ollama on Windows, fully exit any existing Ollama server before starting a process that inherits these settings. This example does not install software or download weights:

```powershell
$env:OLLAMA_HOST = "127.0.0.1:11434"
$env:OLLAMA_NUM_PARALLEL = "1"
$env:OLLAMA_MAX_LOADED_MODELS = "1"
$env:OLLAMA_CONTEXT_LENGTH = "4096"
$env:OLLAMA_NO_CLOUD = "1"
ollama serve
```

The pinned source defines the parallel-request limit, loaded-model limit, context default and `OLLAMA_NO_CLOUD`. It describes the last flag as disabling Ollama remote inference and web search. It is not a machine-wide firewall or an offline guarantee for other applications. Context can be overridden by a client request, so the role orchestrator must also enforce the chosen budget.

Before an asset-generation or rendering job needs the GPU, pause the role queue and let the current inference finish. Run `ollama ps`, copy the exact running local model name, and run `ollama stop MODEL` with that name substituted. Run `ollama ps` again and wait until the model is absent; also check the GPU monitor for reclaimed dedicated memory before starting the next GPU job. The current CLI documents `stop MODEL` as “Stop a running model”; its handler requests unloading with a zero keep-alive duration. This stops the loaded model without deleting its stored weights. Resume the role queue after the asset/render job ends. This lifecycle is source-verified but unexecuted on the user's laptop; do not treat the stop command alone as proof that all GPU processes released memory.

If using a user-downloaded GGUF with a user-installed compatible `llama.cpp` build instead:

```powershell
llama-server.exe --model "C:\Models\Qwen2.5-Coder-7B-Instruct-Q4_K_M.gguf" --ctx-size 4096 --parallel 1 --gpu-layers auto --host 127.0.0.1 --port 8080
```

The file path is an example, not an asserted existing file. This is a recommended unexecuted command. Check the installed build's `--help` because these flags were verified against the pinned current source, not the user's installed version. `auto` can offload to CPU when necessary; inspect logs to learn actual GPU residency rather than inferring it from a successful response.

If selecting llama.cpp's optional multi-model router, use `--models-max 1 --parallel 1 --ctx-size 4096`. **The pinned router default is four simultaneously loaded models**, so leaving that default is inappropriate for this baseline. A single explicit `--model` command avoids needing router mode initially. Keep model downloads under user control; do not use `-hf`, `--fim-...-default`, or commands that automatically pull missing weights in the setup phase.

## Licensing distinctions

| Component | Verified statement |
| --- | --- |
| Ollama source | MIT, from its pinned `LICENSE`. Model licenses are separate. |
| llama.cpp source | MIT, from its pinned `LICENSE`. Model licenses are separate. |
| Jan | Apache License 2.0 in the current pinned `LICENSE`, corroborated by README. |
| LM Studio | The retrieved `lmstudio.js` SDK is MIT. That does **not** establish that the LM Studio desktop GUI is open-source; do not label the GUI MIT/open-source on that evidence. |
| Qwen3.5-4B selected weight artifact | Its current publisher README directs readers to each weight artifact's license. Repository Apache 2.0 code license does not resolve the uninspected model/GGUF license. |
| Exact Qwen2.5-Coder GGUF downloads | Official model identities and upstream download links verified. Artifact licenses, exact sizes and checksums were not retrieved. Verify the exact selected release's license and source before describing it as permissively licensed. Do not apply the current Qwen3 README's blanket Apache statement to old Qwen2.5 models. |

Both `QwenLM/Qwen2.5-Coder` and `QwenLM/Qwen3-Coder` currently resolve to the same Git repository HEAD. Its current README covers Qwen3-Coder. This report instead uses the official `qwen2.5-coder-bk` branch pinned to `d5ead97fea36bca3744e1a4c49e882f6fa2f406a` for the small Coder model identities. Advertised historical benchmark or context claims in that README are not new laptop measurements.

## 3D and application work

TripoSR's official README reports about **6 GB VRAM for one image with default settings**. That makes it a plausible separate, single-job experiment after unloading the LLM and closing competing GPU work. It is not a verified fit on this laptop, and its A100 timing must not be represented as 4070 timing. Verify dependency/platform support before promising installation.

TRELLIS documents an NVIDIA GPU with **at least 16 GB** and TRELLIS.2 **at least 24 GB**, with Linux-based tested setups. Neither belongs in the supported 8 GB baseline. Community low-memory variants would need separate source and execution evidence.

The practical initial pipeline is: bounded planning/coding task → reviewed files or structured handoff → unload the model if a heavy GPU task needs the memory → one 3D/image job → inspect outputs → reload only when needed. Standard web builds, CPU tests and artifact inspection can proceed independently where resources allow. A generated mesh is not evidence of animation, usable topology, complete game reconstruction or validated gameplay.

## Acceptance gate for the user's laptop

1. Record the exact GPU name, **dedicated total/free VRAM**, installed system RAM, runtime version, model filename, actual byte size, checksum, source and license.
2. Run a representative coding task with the chosen Q4 model, 4,096 context and one request. Record peak dedicated VRAM/RAM, time to first token, generation rate, context use and whether CPU offload occurred.
3. Validate the produced edit with the project's real checks and human review. A health endpoint or completed generation alone does not establish coding capability.
4. Run two role requests through the intended queue and verify that model inference stays serial. Keep bounded handoffs so each role does not inherit six full transcripts.
5. Increase to 8,192 context or try the 7B candidate only after the prior profile fits and meets quality/latency needs. Reduce context or use the 3B candidate after memory failures; do not reinterpret shared memory as spare VRAM.

All of these laptop execution checks are **unrun** in the cloud research session.

## Pinned primary-source locations

- [Ollama envconfig](https://github.com/ollama/ollama/blob/1472203c47d93d64020fdafa33f9b038bc1583e9/envconfig/config.go#L214): settings at lines 214–238, 276–281 and 328–338. SHA-256 `0b0ea669b31cfe2b54313427257326a2b7a909bbc7bf8a671035efc446fb1895`.
- [Ollama CLI lifecycle](https://github.com/ollama/ollama/blob/1472203c47d93d64020fdafa33f9b038bc1583e9/cmd/cmd.go#L2630): `stop MODEL` command at lines 2630–2635, zero-keep-alive stop handler at lines 707–718, and `ps` at lines 2710–2714. SHA-256 `2da8da75b4d571296e1666b39fd5697e918bd93619699abe1e27d86c5cdec5e1`.
- [llama.cpp server README](https://github.com/ggml-org/llama.cpp/blob/9ff0d7e90f0faaa7c16017e6dcf9cf91c50a100e/tools/server/README.md#L230): router limits at lines 230–233; context, GPU layers and slots at lines 50, 85 and 177. SHA-256 `ff08ea4e2f248692140efa3e1b589f4b966d9359e6064111ee393156ab8bf6ff`.
- [Preserved official Qwen2.5-Coder README](https://github.com/QwenLM/Qwen3-Coder/blob/d5ead97fea36bca3744e1a4c49e882f6fa2f406a/README.md#L55): model and quantized-format table. SHA-256 `600d946e07e4cb74cd329cba828f026b2eff08ac5b639d1f4b3898c7ec1700e6`.
- [Current Qwen3-Coder README](https://github.com/QwenLM/Qwen3-Coder/blob/33bc6aabd7791ad7b32f7e92104f11f2359ba890/README.md#L45): model families and 30B-A3B identity. SHA-256 `7553f06c6f17a7ce22a76995a210b07fb6724d32a0cdc7bd4961ed2866d80fd4`.
- [Current Qwen3.5/3.6 family README](https://github.com/QwenLM/Qwen3.6/blob/2ea10dc725823bf7c3e21ce8557cbe15245132ae/README.md#L52): Qwen3.5-4B release at line 52, family llama.cpp support at lines 132–136, artifact-specific license instruction at lines 195–197. SHA-256 `a71ec46607f81d6056336fb0a8431a26a1c7d8db6ac568a0c021c36f1ed3c92e`.
- [Current Qwen3 README](https://github.com/QwenLM/Qwen3/blob/7a2f61ffc7a20d47efcd2bf97f6f2bf52729042e/README.md#L68): exact Qwen3-4B-Instruct-2507 model-card link and release; its open-weight license statement appears at lines 395–398. SHA-256 `0b2c2bb11806f7a00c8465f2586e2e99f15de28622fd5c9b70b83ae1ab18c75d`.
- [Jan LICENSE](https://github.com/janhq/jan/blob/a4f0ddde041761c09acbdb60d631c4f0486eb5ba/LICENSE): Apache 2.0. SHA-256 `240e79d4976dbf1d4c76e0ac1da223df97935a75497eaf8dd045771c3e92de16`.
- [LM Studio JavaScript SDK LICENSE](https://github.com/lmstudio-ai/lmstudio.js/blob/8ba8348fb244a05dce8a9b493b4d235224c1a071/LICENSE): MIT SDK license. SHA-256 `85f3989bd8264b6e758ed5efb7c04415c1b63abfa758b920a1c2e6acf8a3fc93`.
- [TripoSR README](https://github.com/VAST-AI-Research/TripoSR/blob/107cefdc244c39106fa830359024f6a2f1c78871/README.md#L41): default single-image memory estimate. SHA-256 `ed40f078c5e451c58eae716187e0128f0ce8575e467aab2440b4ed9c75e490b9`.
- [TRELLIS README](https://github.com/microsoft/TRELLIS/blob/442aa1e1afb9014e80681d3bf604e8d728a86ee7/README.md#L41): 16 GB prerequisite. SHA-256 `675a1bab7837d22972a776dec8e2a2eb01f9211bd40b4c57112a8335ccb9ec3e`.
- [TRELLIS.2 README](https://github.com/microsoft/TRELLIS.2/blob/75fbf0183001ed9876c8dbb35de6b68552ee08bd/README.md#L60): 24 GB prerequisite. SHA-256 `adc985d5a71fda0a5cb7287f58b6baa7de8db1568c4483ac210f3447b786552b`.

`sources.json` includes all successful fetches and three 404s, so missing docs are explicit. Ollama's previously used `docs/faq.md` and `docs/context-length.md` paths returned 404 at current HEAD; its current source code supplies the setting evidence above. No denied endpoint, alternate mirror, credential extraction or TLS bypass was used.
