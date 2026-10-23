# 3D generation and game-model shortlist

Reviewed 21 October 2026. These are independently researched candidates. **The supplied YouTube video has not been accessed or transcribed; none of these tools is attributed to that video.** Official README claims are identified below and have not been reproduced on YUGA hardware.

The practical first experiments are **TripoSR for a low-memory baseline** and **TRELLIS.2 for a higher-detail PBR asset candidate on suitable GPU hardware**. The model outputs must still pass artist, topology, rig, motion, material and engine checks. A generated mesh does not establish a finished animated hero or a multiplayer game.

## Primary-source comparison

| Candidate | Published memory requirement | What it produces / useful experiment | License and adoption boundary |
| --- | --- | --- | --- |
| [TripoSR](https://github.com/VAST-AI-Research/TripoSR/tree/107cefdc244c39106fa830359024f6a2f1c78871) | Approximately **6 GB VRAM**, default single image | Fast single-image mesh reconstruction; compare one original diya, carved pier ornament and Rama costume accessory against existing art | README explicitly says **MIT code, pretrained models and demo**. Retain notices; source images and generated likenesses still need their own provenance. |
| [TRELLIS.2](https://github.com/microsoft/TRELLIS.2/tree/75fbf0183001ed9876c8dbb35de6b68552ee08bd) | **At least 24 GB NVIDIA VRAM**; Linux tested; publisher verified A100/H100 | 4B image-to-3D model with base color, roughness, metallic and opacity; higher-detail prop and hero-base experiments | README states **MIT model and code**. `nvdiffrast` and `nvdiffrec` have separate terms. Check the actual dependency set and downloaded checkpoint revision before production use. |
| [TRELLIS](https://github.com/microsoft/TRELLIS/tree/442aa1e1afb9014e80681d3bf604e8d728a86ee7) | **At least 16 GB NVIDIA VRAM**; publisher verified A100/A6000 | Images/text to meshes, radiance fields or Gaussians; image-conditioned path is the publisher's recommended quality route | Models and most code **MIT**; octree renderer and modified FlexiCubes have separate licenses. A radiance-field preview is not a riggable engine mesh. |
| [Stable Fast 3D](https://github.com/Stability-AI/stable-fast-3d/tree/ff21fc491b4dc5314bf6734c7c0dabd86b5f5bb2) | Approximately **6 GB VRAM**, default single image; documented CPU fallback | UV-unwrapped GLB, material prediction and optional triangle/quad remeshing; a useful low-memory comparison | **Stability AI Community License**, not MIT. Hugging Face model is gated. Inspected terms require registration for commercial use and have an aggregate annual-revenue threshold of US$1 million; output ownership and use restrictions are separate clauses. |
| [Hunyuan3D 2.1](https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1/tree/82920d643c0dc2f7bfd7255f45f62d386edfe60c) | **10 GB shape / 21 GB texture / 29 GB combined** | Shape generation followed by PBR texture generation; compare only after license and hardware review | **Tencent Community License** applies to models/software. Territory excludes EU, UK and South Korea; §5(c) explicitly also covers outputs/results. §4 has an additional-license condition for the stated >1 million MAU release-date threshold. Do not choose it as the default global asset pipeline without project-specific review. |

[Hunyuan3D 2](https://github.com/Tencent-Hunyuan/Hunyuan3D-2/tree/f8db63096c8282cb27354314d896feba5ba6ff8a) is a lower-memory comparator: its README reports 6 GB shape / 16 GB combined. Its own pinned 2.0 license retains territorial/output restrictions; do not assume the lower memory figure changes those terms. For Hunyuan 2/2.1, Tencent's statement that it claims no rights in outputs (§6(d)) does not remove the explicit output-use condition in §5(c). This is a source reading for tool selection, not a blanket legal determination for the project.

The TRELLIS.2 timings of approximately 3/17/60 seconds at 512³/1024³/1536³ are **publisher H100 results**. They are not RTX 5090 laptop, desktop or current-cloud performance. Published minimum VRAM also excludes any unmeasured concurrent game/editor/model workload. A model whose listed minimum equals a GPU's total memory has no assured room for another GPU-heavy process.

## Game world models are a different category

| Project | Verified capability | What it does not establish |
| --- | --- | --- |
| [Open Oasis 500M](https://github.com/etched-ai/open-oasis/tree/f59deef2c019c212bd0c5a3a5b986a51f3701847) | Action-conditioned autoregressive gameplay frames; released inference code and a link to a downscaled 500M checkpoint. Code is MIT. The README links a stronger [hosted demo](https://oasis.us.decart.ai/). | No mesh/rig/level export or authoritative multiplayer simulation is demonstrated by that README. The hosted demo is not evidence that the same model is locally downloadable. Checkpoint-card terms and practical VRAM requirements remain unverified. |
| [DreamerV3](https://github.com/danijar/dreamerv3/tree/e01491fad6434b2245a3b8ca201dd7faedcc458c) | MIT reinforcement-learning implementation that learns a latent world model and trains actor/critic policies using imagined trajectories; JAX-based task training. | This is not a text LLM, 3D art generator or pretrained YUGA bot. It needs a game observation/action/reward interface, training budget and evaluation against a deterministic baseline. |

Most tools above are reconstruction/diffusion/flow/world models, **not language models**. Do not use “gaming LLM” as a substitute for a capability test. Coding agents can author engine code; asset models generate candidate content; world models generate predicted frames; game authority must still maintain consistent rules and state.

## A local coding LLM is a separate workload

The current [official Qwen3-Coder README](https://github.com/QwenLM/Qwen3-Coder/blob/33bc6aabd7791ad7b32f7e92104f11f2359ba890/README.md) names 30B-A3B, 480B-A35B and Qwen3-Coder-Next (built on an 80B-A3B base). The old `QwenLM/Qwen2.5-Coder` repository URL now returns that current family README; do not silently treat it as a source for older models. A MoE model's active parameter count is not its total weight-storage requirement.

For a smaller, concrete local coding experiment, the official [archived Qwen2.5-Coder README](https://github.com/QwenLM/Qwen3-Coder/blob/d5ead97fea36bca3744e1a4c49e882f6fa2f406a/README.md) lists **7B and 14B Instruct** checkpoints in GGUF, AWQ and GPTQ-Int4 forms. Start by evaluating `Qwen/Qwen2.5-Coder-7B-Instruct-GGUF`; compare `Qwen/Qwen2.5-Coder-14B-Instruct-GGUF` only after the smaller model is measured. This is an accessible baseline, not a claim that the older family is today's best coding model. Model cards/licenses, exact quantization filenames and immutable weight revisions remain unretrieved.

At nominal four-bit storage, 7 billion weights × 4/8 is **3.5 GB**, and 14 billion is **7 GB**, before quantization scales, higher-precision tensors, KV cache, activations and inference-runtime memory. These are arithmetic lower bounds, **not measured model sizes or VRAM requirements**. One such quantized coding service is a plausible candidate on a 24 GB GPU at bounded context; running it alongside a near-capacity 3D generator is not established. Long context and concurrent sequences increase memory. Agent roles can share one inference server, but that does not create six independent GPUs or guarantee six concurrent generations.

Use coding-model output for reviewed source changes and tests. It does not produce a sculpted/rigged hero simply because it can write Blender or engine scripts. Record a small set of repository tasks with pass/fail checks, runtime, token rate, context size and peak GPU memory before adopting the local model as a production worker.

## Download and execution status

Only official documentation, licenses and the unexecuted TripoSR `run.py` source were downloaded. [source-manifest.json](source-manifest.json) records every successful byte count/SHA-256 and the failed SF3D `LICENSE` lookup followed by successful `LICENSE.md`. All source links are pinned to full Git revisions obtained by `git ls-remote`. The machine-readable shortlist is [model-catalog.json](model-catalog.json).

**No weights, inference environment, model output or model benchmark were downloaded/created by this research task.** The parent environment check reports no NVIDIA GPU, a four-CPU quota, 32 GiB RAM and roughly 426 MiB free disk; Hugging Face access is blocked pending configuration activation. SF3D documents CPU fallback, but its weights/access, dependencies, disk needs and runtime remain unqualified here. Installing large CUDA wheels or multi-GB weights cannot be justified as a successful setup on this machine.

Checkpoint IDs to resolve and pin after access/storage are ready:

- `stabilityai/TripoSR` — first baseline.
- `microsoft/TRELLIS.2-4B` — primary high-detail GPU experiment.
- `microsoft/TRELLIS-image-large` — intermediate-memory fallback.
- `stabilityai/stable-fast-3d` — gated optional comparison.
- `tencent/Hunyuan3D-2.1` — license-reviewed research comparator.
- `Etched/oasis-500m` — separate world-model experiment, not an asset production dependency.
- `Qwen/Qwen2.5-Coder-7B-Instruct-GGUF` and optionally `Qwen/Qwen2.5-Coder-14B-Instruct-GGUF` — choose one exact quantized file, not every variant in the repository.

The checkpoint IDs are advertised by inspected official documentation or source. TripoSR `run.py` explicitly defaults to `stabilityai/TripoSR` and loads `config.yaml` plus `model.ckpt`. Their **Hugging Face revisions, complete download sizes, hashes and access terms have not been retrieved**. The Git code pin is not the model-weight pin. Record both before inference; preserve TLS verification and use the environment's supported network and credential paths.

## Proposed acceptance experiment for both roadmaps

1. Fix original input art and camera views for three small static assets. Pin image rights, source code, checkpoint revision, dependency lock, seed and inference settings. Do not start with the entire hero or map.
2. Run TripoSR and, on suitable hardware, TRELLIS.2 separately. Record elapsed time, peak allocated/reserved VRAM, process/GPU memory, disk footprint and failed runs. Check GPU architecture support in PyTorch/CUDA and custom extensions; upstream A100/H100 validation is not Blackwell qualification.
3. Review unseen back/underside geometry, thin structures, material seams, normal/tangent consistency, scale and silhouette. Artist acceptance is separate from inference success.
4. Clean/remesh, UV/bake, create collisions and LODs, then import into native Godot. For hero experiments, additionally create a deformation-appropriate retopology, rig/skin and facial/garment solution; test all animation transitions and counters. Generic quad remeshing alone is not adequate rig validation.
5. Derive Android variants from accepted source assets: reduced geometry/material count, texture compression/atlases, LODs and collision budgets. Measure frame time, heat and memory on physical devices; desktop inference speed does not prove mobile runtime cost.
6. Compare **accepted artist hours saved**, rework, originality, visual quality and runtime budgets against authored assets. Adopt a model only if that result improves the production workflow. Keep inference offline in the asset pipeline; the shipped game need not include model weights.

These are proposed research/production checks, not completed desktop/mobile packets and not a claim of fewer rounds to commercial quality.

## Source archive notice

Files under `sources/` are verbatim, unexecuted copies of the named upstream README/license documents and the TripoSR `run.py` source retained for provenance. Copyright and license terms remain with their original authors; they are not YUGA-authored code. No linked script was executed. The manifest owns exact origins and byte hashes. Transient source-fetch errors remain in the manifest rather than being rewritten as success.
