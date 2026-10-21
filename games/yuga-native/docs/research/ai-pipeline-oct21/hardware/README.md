# Hardware decision for local YUGA AI production

Checked 21 October 2026 against the sources in [source-receipt.json](source-receipt.json). This is a source-based capacity assessment, not a benchmark on purchased hardware. The supplied YouTube video's transcript and exact model list were unavailable to this worker; the models below are independently researched candidates, not asserted video contents.

## Purchase recommendation

**User constraints: a laptop is required, purchase country USA, total budget up to US$7,000.** Target an RTX 5090 laptop with 64 GB RAM and 4 TB SSD capacity, then queue large GPU jobs. Prefer an 18-inch performance chassis if its size and weight are acceptable. Neither that laptop nor a desktop 5090 is a credible promise to run every local LLM, 3D generator, video generator and game renderer simultaneously.

The published product capacities normally relevant to this comparison are **24 GB GDDR7 for the RTX 5090 Laptop GPU** and **32 GB GDDR7 for the desktop RTX 5090**. They are different products. The official NVIDIA specification pages listed below returned proxy CONNECT 403 here, so these product figures have **not been freshly verified from those pages in this session**. Confirm the exact purchased SKU, GPU memory and manufacturer power configuration before ordering. No current price, availability or best-performing laptop SKU was verified.

| Configuration | Proposed specification | Practical role and limitation |
| --- | --- | --- |
| Portable workstation | 5090 Laptop GPU; 64 GB RAM minimum target, 96/128 GB only if the exact laptop supports it; 2–4 TB NVMe | Godot/Blender, code assistance and a fitting model at a time. Prefer a chassis with demonstrated sustained cooling and GPU power delivery. A thin laptop with the same GPU name may sustain a different workload. |
| Desktop comparison only; does not satisfy the user's portability requirement | 5090 desktop GPU; 128 GB RAM target; 4 TB NVMe plus backup; modern 12–16-core CPU; case/cooling/PSU matched to the exact GPU and vendor guidance | More GPU memory and better sustained thermal headroom for asset generation and renders. Still only one GPU memory pool, with a 29 GB published model pipeline leaving little headroom in 32 GB. |
| Heavy-model supplement | On-demand GPU with a verified 48–80 GB or larger memory configuration, selected after model measurement | Large pipelines, experimentation and batches. This is a capacity recommendation, not a confirmed cloud allocation or a claim that every model fits. |

RAM, SSD, CPU and cloud-memory figures in this table are engineering planning recommendations, not model vendor minima. Fast NVMe reduces loading friction but does not become GPU VRAM. Host RAM/offloading can permit otherwise oversized models at a latency cost; it does not provide equivalent GPU performance. A large desktop GPU also does not qualify the Android release: physical target phones still need frame-time, thermal, memory and battery tests.

### US laptop shortlist and budget allocation

These are **models to obtain current exact-SKU quotations and test reports for**, not verified in-stock offers. The three official vendor pages all returned proxy CONNECT 403. Exact prices, current availability, GPU power limits, RAM limits, SSD slots and the available configurations were therefore not verified in this session.

| Candidate | Decision to investigate |
| --- | --- |
| [ASUS ROG Strix SCAR 18, G835LX family](https://rog.asus.com/us/laptops/rog-strix/rog-strix-scar-18-2025/) | First 18-inch quote to compare: RTX 5090, vendor-supported 64 GB RAM and 4 TB storage. Confirm the exact US SKU, sustained GPU power, memory/SSD accessibility and warranty. |
| [MSI Titan 18 HX AI, A2XW family](https://us.msi.com/Laptop/Titan-18-HX-AI-A2XWX) | Compare the premium against measured sustained cooling, supported memory expansion, storage and serviceability. More RAM capacity does not increase the 5090 Laptop GPU's VRAM. |
| [Razer Blade 16](https://www.razer.com/gaming-laptops/razer-blade-16) | Compare when smaller size and carrying weight matter more. Check the exact generation's soldered/replaceable RAM arrangement and sustained power before selecting; do not assume later RAM upgrades. |

**Buying target:** 24 GB RTX 5090 Laptop GPU; manufacturer-supported 64 GB RAM; 4 TB SSD total; preferably at least two accessible M.2 slots if the exact model supports them; adequate cooling and plugged-in sustained performance. Consider 96/128 GB only when both the processor and laptop vendor explicitly support the selected memory configuration. A high CPU tier and a premium screen are secondary to usable memory, stable GPU thermals and repairability for this workload. Compare independent sustained Blender/AI workloads, not only short gaming bursts or advertised boost clocks.

Treat $7,000 as a ceiling, not a requirement to spend everything on the laptop. A proposed allocation is **$5,500–6,000 for the machine, leaving $1,000–1,500 for larger-memory cloud GPU jobs, a representative Android test phone, storage/backup or warranty**, adjusted after real quotations and local sales tax. Those are planning allocations, not asserted market prices or a claim that every desired configuration fits. Avoid paying a large premium solely for another 5090 label when both configurations have the same 24 GB GPU-memory ceiling.

Before purchase, request a refundable-trial or return policy sufficient to run the exact selected model, CUDA extension compilation, Blender workload and Godot capture. The acceptance decision should bind the complete SKU and its plugged-in performance mode. No blanket recommendation to buy the most expensive laptop is supported by this research.

## Verified model requirements and concurrent-use arithmetic

| Source checked | Upstream statement | Implication |
| --- | --- | --- |
| [Hunyuan3D-2.1 README, revision 82920d64](https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1/blob/82920d643c0dc2f7bfd7255f45f62d386edfe60c/README.md) | 10 GB VRAM shape generation; 21 GB texture generation; 29 GB shape and texture together. A `--low_vram_mode` example also exists. | A 24 GB GPU does not meet the published 29 GB combined figure. A 32 GB GPU nominally exceeds it, but actual output settings, dependencies and other allocations must be measured. Low-VRAM mode is not a verified memory/performance claim here. |
| [TRELLIS README, revision 442aa1e1](https://github.com/microsoft/TRELLIS/blob/442aa1e1afb9014e80681d3bf604e8d728a86ee7/README.md) | NVIDIA GPU with at least 16 GB; tested on Linux with A100/A6000; CUDA 11.8/12.2 tested. | Both proposed capacities exceed that stated minimum. This does not verify RTX 5090 compatibility, exact runtime peak or simultaneous use with a game editor. |
| [PyTorch 2.7.0 release](https://github.com/pytorch/pytorch/releases/tag/v2.7.0) | Blackwell support added across native kernels, CUDA math libraries and `torch.compile`; CUDA 12.8 added to CI/CD. | Use a Blackwell-capable framework/driver stack and qualify each model's compiled extensions. The existence of support does not make every old pinned model environment compatible. |

Illustrative raw four-bit weight storage is `parameter_count × 4 / 8` bytes:

| Parameter count | Raw four-bit weights, decimal GB |
| --- | ---: |
| 7 billion | 3.5 |
| 14 billion | 7 |
| 32 billion | 16 |
| 70 billion | 35 |

These are lower bounds, not runnable memory budgets. Quantization scales/metadata, non-quantized layers, KV cache, context length, request concurrency, activations, CUDA allocation and the desktop/editor consume additional memory. A particular seven-billion-parameter model may not support the intended quantization or backend.

For example, **a 14B four-bit model's raw 7 GB plus Hunyuan3D-2.1's stated 29 GB combined requirement is already 36 GB before overhead**. That combination exceeds both proposed GPU capacities. The 21 GB texture stage plus 7 GB raw LLM weights is already 28 GB, exceeding a 24 GB laptop and leaving very limited theoretical room on a 32 GB desktop. This is capacity arithmetic, not a performance benchmark; upstream GB labels may also use conventions different from tool-reported GiB.

Six code/design workers need not mean six resident copies of a local LLM. Share one bounded inference server where appropriate; account for the additional KV cache from simultaneous requests. API-hosted worker models do not consume the laptop's model-weight VRAM. CPU analysis/build tasks can continue while a single reserved GPU lane runs model inference or rendering.

## Execution layout to qualify

1. Keep each model in an isolated, pinned environment. Start with one candidate and one original YUGA prop. Use the model's stated input/output and weight license, not just the code license.
2. On an RTX 5090, verify driver, framework CUDA build, reported architecture support and one real CUDA operation. Then compile/test that model's rasterization, attention and sparse-convolution dependencies. TRELLIS's default PyTorch 2.4/CUDA 11.8 setup predates the cited Blackwell support; copying it unchanged is not a qualification path. Prefer a supported recipe, and record any adapted version pins.
3. Prefer native Linux for the first Linux-tested model qualification. WSL2 may be practical for a Windows workstation, but WSL2/CUDA availability alone does not prove every extension or Blender interoperation path. Test the actual chosen operating system and exporter.
4. Reserve one heavy GPU lane. Unload the coding model before a near-capacity 3D job; generate geometry and texture in stages if supported. Serialize video generation, large 3D generation, GPU Blender rendering and hardware frame-time qualification. Continue CPU work in parallel.
5. Benchmark cold/warm generation, peak VRAM and host RAM, storage, wall time, failure recovery and output quality. Record exact model revision, quantization, resolution, seed, driver, OS and dependency pins. Repeat a sustained run under the purchased laptop's intended power mode and plugged-in conditions; short peak scores do not establish thermal stability.
6. Convert candidates to editable meshes, inspect silhouette/anatomy, retopologize, UV/bake, rig, animate and build LODs. Validate in Godot. For mobile, create a separate budgeted derivative and qualify it on real Android hardware. A good generated image/mesh does not close these production gates.

Suggested scheduling policy: interactive editor or gameplay has priority; run heavy generation when the editor can release GPU memory; stop background GPU jobs during performance measurements. Do not count a single GPU as six independent full-capacity worker GPUs. Even multiple GPUs do not automatically combine VRAM for every framework; distributed/model-parallel support must be demonstrated.

## Source access and validation limits

- Official laptop specs to recheck: <https://www.nvidia.com/en-us/geforce/laptops/50-series/> — proxy CONNECT 403 observed.
- Official desktop specs to recheck: <https://www.nvidia.com/en-us/geforce/graphics-cards/50-series/rtx-5090/> — proxy CONNECT 403 observed.
- US vendor shortlist hosts to allow for direct verification: `rog.asus.com`, `us.msi.com`, `www.razer.com` — all returned proxy CONNECT 403. No alternate proxy was used.
- NVIDIA CUDA platform/WSL details: <https://docs.nvidia.com/cuda/wsl-user-guide/index.html> — reference for later OS qualification, not read in this packet.
- Model requirements are from successfully downloaded, revision-pinned official repository READMEs retained beside this report. PyTorch evidence is retained as small excerpts plus the complete response hash. Two guessed raw documentation paths returned 404; they are recorded, not used as evidence.
- No GPU, model weight, inference, training, rendering, laptop thermal or Android test was run by this research worker. No full commercial-game reverse engineering or source recovery is established.

Next owner: lead chooses one GPU/OS/model experiment after resolving cloud or local hardware access; model/art owners then benchmark one original asset and compare total cleanup time with the existing Blender workflow. Update schedule forecasts only from accepted assets and measured iteration time.
