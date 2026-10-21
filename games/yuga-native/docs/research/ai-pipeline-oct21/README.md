# AI models, game reconstruction and laptop decision

Reviewed **21 October 2026**, against source `ec4d7bb2`. User constraints: **laptop required, USA, US$7,000 budget**. Desktop production remains first; Android implementation remains deferred. This research updates tool choices and acceptance steps, not game-completion counts.

## Video status and evidence boundary

Requested video: <https://youtu.be/tDWtcyeNNew>. Direct requests to that URL and its `www.youtube.com/watch` URL failed with proxy **CONNECT 403**. Its title, author, captions, audio, screenshots, named products and timestamps remain **unverified**. No transcript was produced, and none of the candidates below is attributed to the video. Installed Chromium cannot overcome the same destination policy; no alternate proxy or mirror was used.

Hugging Face, NVIDIA and the three laptop manufacturers also returned CONNECT 403. Required hosts were saved to the existing cloud configuration draft, preserving previous entries. A saved draft does not change the running network: **Environment Settings → Save → Publish**, followed by a fresh access check, is still required. [access-status.json](access-status.json) records the attempts and configuration boundary.

After access works, retrieve the video's metadata and available captions; otherwise obtain audio and use a transcription model only after storage/runtime checks. Retain language, manual/automatic-caption status and timestamps. Inspect frames for names/URLs that speech misses. Make an inventory of every named tool/site and verify its exact upstream repository, model card, weight availability, terms and demonstrated capability. Link claims to timestamp ranges and keep transcription uncertainty visible. Update this study from that evidence; do not relabel this independent shortlist as a video summary.

## What can help YUGA

| Tool/category | Verified source finding | Decision |
| --- | --- | --- |
| TripoSR | Single-image mesh reconstruction; approximately 6 GB VRAM; MIT code/models; upstream loader names `stabilityai/TripoSR` | First small-asset baseline once a GPU and storage are available |
| TRELLIS / TRELLIS.2 | At least 16 / 24 GB NVIDIA VRAM respectively; mesh/material generation; code/model MIT with separately licensed components | Higher-detail candidates, benchmark serially; 24 GB minimum is not a 24 GB laptop performance guarantee |
| Hunyuan3D 2.1 | Published 10 GB shape / 21 GB texture / 29 GB combined; territorial and output-use conditions in its own license | Research comparator pending project-specific licensing and hardware review; not the default global asset pipeline |
| Stable Fast 3D | Approximately 6 GB GPU; documented CPU fallback; gated weights and community-license conditions | Optional comparison; CPU support does not resolve current disk/access limits |
| Qwen coding models | Official Qwen sources list quantized coding models; nominal 7B/14B four-bit weights alone are about 3.5/7 GB before overhead | Start with one shared 7B coding service; validate code and concurrency rather than running a separate loaded model for each agent |
| Oasis / DreamerV3 | Predicted gameplay video / learned control policies, respectively | Separate experiments; neither supplies a rigged hero, consistent multiplayer authority or a finished game |
| REA 6.7 | Native/browser/APK/PCK analysis and model-header inspection; header tool does not run inference | Evaluate on our own known inputs, independent of asset-generation models |
| ioquake3 / QuakeJS / OpenRA / noclip | Released-source web port / JavaScript port / native RTS reimplementation / scene viewer | Study specific prediction, resource-delivery and inspection patterns; preserve component and original-asset terms |

Exact revisions, source files, licenses and limits: [model study](models/README.md), [reuse study](reuse/README.md), [hardware brief](hardware/README.md). These are upstream claims and code readings, not local inference or live-game benchmarks. Model-weight commits are separate from code commits and have not yet been resolved.

## Cloud and download outcome

The actual [capacity probe](preflight/cloud-capacity-r2.json) records a four-core CPU quota, 32 GiB cgroup RAM, no available `nvidia-smi` and roughly **425 MiB free disk**. The check correctly exits with a capacity failure. The absence of CUDA hardware also agrees with the existing software-rendering environment record. No model weights, PyTorch/CUDA stack, transcription model or generated 3D asset was downloaded or run. Small pinned upstream source documents were downloaded and hash-checked.

The [new preflight tool](../../../tools/ai-assets/README.md) checks declared single-GPU free memory and new disk footprint plus reserve, and does not sum separate GPUs' memory. Its nine focused tests cover failure and capacity boundaries. A passing capacity check would still not establish compatible CUDA kernels, model quality or legal suitability. Its saved 8 GiB/20 GiB requirements are illustrative test inputs, not a selected model's measured requirements.

On a qualified laptop or GPU cloud machine:

1. Resolve a selected model's exact weight revision and required files. Start with TripoSR's `config.yaml` and `model.ckpt`, including its actual auxiliary dependencies; do not download every candidate.
2. Record model/dependency terms, sizes and upstream hashes where published. Budget weights, Python environment, extension builds, download cache and output scratch. Keep artifacts outside Git and preserve source/weight provenance.
3. Run the capacity probe using that declared budget and VRAM headroom. Install into an isolated environment with a Blackwell-compatible PyTorch/CUDA build; compile and smoke-test custom extensions for the actual GPU. Do not blindly run older CUDA install scripts.
4. Download through the supported route, verify files, and generate one original static asset. Record peak memory, duration, failure log, seed/settings and output hash. Only then compare a higher-detail model and a hero candidate.
5. Measure quality and artist cleanup time. Preserve the authored source, retopology, UVs, rig, clips, collision, LODs, engine captures and provenance for accepted assets. Export ordinary game assets; inference weights do not belong in the Android APK or match server by default.

Download and inference remain blocked here by actual storage, GPU and access conditions. An SF3D CPU run may be technically possible on a different prepared CPU environment, but it is not tested or ready here.

## Laptop recommendation for the stated budget

Prefer a well-cooled **18-inch RTX 5090 Laptop GPU configuration, 64 GB RAM and 4 TB SSD**. Compare US **ASUS ROG Strix SCAR 18** and **MSI Titan 18 HX AI** configurations first; consider **Razer Blade 16** if carrying weight matters more. These are a shortlist, not a verified price/stock ranking: official manufacturer and NVIDIA pages were inaccessible. Confirm the exact SKU's GPU, sustained power limit, cooling, supported RAM expansion, SSD slots and warranty before purchase. Do not infer laptop specs from a same-named desktop card.

The published product capacities are **24 GB VRAM for the 5090 Laptop GPU versus 32 GB for the desktop 5090**; these specifications were not freshly reverified from NVIDIA in this session. Budget roughly US$5,500–6,000 for a suitable laptop if a verified configuration fits, reserving US$1,000–1,500 for a physical Android test phone, storage/warranty and occasional larger-memory GPU rental. These are allocation targets, not current quotations. There is no need to spend all US$7,000 on a laptop simply because it is available.

**All models cannot run simultaneously in laptop VRAM.** For example, the published 29 GB Hunyuan pipeline exceeds 24 GB before another application runs. TRELLIS.2's 24 GB minimum uses the entire nominal capacity. A 14B four-bit model adds roughly 7 GB raw weights before KV cache, activations and runtime. System RAM/offload may permit some workloads but reduces throughput and is model-dependent; it is not additional fast VRAM.

Use parallel CPU/API research, coding, tests and builds, with **one heavy GPU job at a time**. Share a coding-model server across agents and budget context/cache for concurrent requests. Pause/unload it for large generation or Blender renders when needed. Run low-load editor work alongside only after measuring actual headroom. Use a separate 48–80 GB GPU cloud worker for jobs that do not fit; this is a capacity recommendation, not a speed or cost guarantee. Keep a separate physical Android device for device qualification.

## Roadmap amendment and six-owner pilot

Both roadmaps retain their counts: **desktop 17/78 accepted packets, 0/13 rounds complete; mobile 0/108 implementation packets, 18 planned rounds**. Research and a preflight utility do not reduce the remaining game-production work. The following assignments refine existing gates; they are not six newly completed production tasks.

| Owner | Desktop pilot / existing gate | Android follow-through, when resumed | Required acceptance |
| --- | --- | --- | --- |
| W1 evidence and visual review | Finish video inventory; freeze original references and matched views for P1/I01 | M1/M3 reference-device and match-camera review | Timestamped video claims; source-pinned actual engine views; accepted/rejected decisions |
| W2 interaction and clarity | Check selection screen, HUD and ability silhouette with candidate assets | M2/M3/M9 touch readability and complete screen flow | Actual input/scale tests; art cannot obscure enemy telegraphs |
| W3 hero artist | Compare generated bases/accessories with authored Rama; fix topology, hair, cloth, skin and rig | M3 hero variants, M11–M13 roster only after pipeline acceptance | Full front/back/profile and continuous animation/contact review; no concept image counted as runtime art |
| W4 world artist | One original carved prop/lantern or pier detail in the existing arena | M10 shared modular map, collision, material/LOD variants | Traversal/collision truth, day/night readability, measured scene cost |
| W5 motion and simulation | Preserve action timing; study snapshot replay/correction for P2 separately | M5/M6 authority and reconciliation; M15 motion cohesion | Cast/cancel/hit/death transitions; two rendered clients then actual 5v5; no simulation generated from video |
| W6 models, package and independent QA | Pin downloads; qualify GPU/extensions; measure cleanup and runtime; evaluate REA on an owned fixture | M1 capacity, M9/M10 content dependencies, M16/M18 device/release gates | Reproducible model/output manifest, actual peak memory, licensed asset delivery, bad-input tests and physical-device results |

Order: access/capacity and source identification → small static-asset comparison → one complete hero/arena acceptance → production adoption and native online integration. Android derives mobile variants later and still requires its M3/M6/M10/M13/M18 gates. Reforecast rounds from **accepted production time and rework**, not repository count, generated images or inference speed. Keep Godot/Blender/glTF; no engine migration is justified by this source study.

Next external action: activate the saved network draft and supply a suitable GPU/storage environment before model execution. Next project action: resolve the video inventory and exact model download manifest, then run the bounded asset comparison. No laptop purchase, paid GPU rental, new public server or release was performed.
