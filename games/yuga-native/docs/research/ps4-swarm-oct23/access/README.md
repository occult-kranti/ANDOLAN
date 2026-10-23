# GPU access and video recheck — 23 October 2026

A real **anonymous TRELLIS.2 shared-GPU generation and GLB export succeeded** during this study. The original diya concept became a 3,805,612-byte GLB, with 48 source-rendered views retained. The cloud still has no discoverable general-purpose GPU allocation tool, configured provider account or local GPU. Managed image generation supplied the original concept, and the public model demo supplied bounded 3D processing; neither exposes a general CUDA host for arbitrary jobs.

## What was checked

The runtime reports `observations_current: true`, running/connected, with empty capabilities, outbound identities, secrets and runtime variables. No NVIDIA/ROCm device nodes or inventory tools were found. Runpod, Vast, Modal and cloud-provider CLIs are absent. SSH, FFmpeg and Chromium are installed. Some Azure platform identity variable **names** exist, but no selectable outbound identity or `OIC_MANIFEST_PATH` is configured; those names do not authorize a GPU account. No credential values or credential files were read.

The HTTP policy is restricted and its runtime enforcement state is `unknown`; TCP grants are empty and VPN is unconfigured. The static allowlist alone is not evidence that a destination currently fails. Initially the Space runtime host returned CONNECT 403. After a parent-reported environment restart and newly successful model access, a fresh supported request returned HTTP 200 for the Space config and API schema. The four YouTube URLs remained CONNECT 403. Both observations are retained; no proxy bypass was used.

See [capability observations](capabilities.json), [tool inventory](tools-inventory.json), [source retrievals](source-ledger.json), [initial Space checks](space-ledger.json) and [post-restart recheck](recheck1-ledger.json). No provider GPU was provisioned, paid API invoked, model weights installed locally or SSH host connected by this study. A hash-locked Gradio client environment was installed (about 46 MiB allocated); the successful calls ultimately used explicit anonymous HTTP requests with its pinned HTTPX dependency.

## Four requested videos

| Video | Fresh supported HTTPS outcome | Content evidence |
| --- | --- | --- |
| `9W7QgI3pmT8` | curl 56, CONNECT 403, zero body bytes | Unknown title/creator/transcript/frames |
| `Pl7ThC4PiVA` | curl 56, CONNECT 403, zero body bytes | Unknown title/creator/transcript/frames |
| `s9HMWYxwnOw` | curl 56, CONNECT 403, zero body bytes | Unknown title/creator/transcript/frames |
| `tDWtcyeNNew` | curl 56, CONNECT 403, zero body bytes | Unknown title/creator/transcript/frames |

[The initial video ledger](video-ledger.json) and [post-restart recheck](recheck1-ledger.json) record exact URLs, dates and response artifacts. All four remained inaccessible after the meaningful environment change. No source was attributed to PewDiePie or to those videos. Activating their saved network requirements and retesting, or supplying accessible captions/video, is still needed. Chromium is not a remedy for a destination-policy denial. No alternate proxy or mirror was used.

## Authorized shared GPUs: Hugging Face ZeroGPU

The pinned [official ZeroGPU document](https://github.com/huggingface/hub-docs/blob/faaeaa0629b03dbaeb9168e8740e7923fc651e9b/docs/hub/spaces-zerogpu.md) describes a legitimate shared-GPU service for public Gradio/PyTorch demos. It is not an unused machine that this cloud can take over. Its current documented rules are:

- Public existing Spaces: 2 minutes/day unauthenticated, 5 minutes/day for a free account; queues and remaining quota affect priority. The quotas reset 24 hours after first use. These are source-documented allowances, not measured quota on the user's account.
- `large` uses half an RTX Pro 6000 Blackwell, 48 GB VRAM; `xlarge` uses a full card, 96 GB, and consumes 2× quota. Hardware labels may change; pin the document date rather than extrapolating from older A10G/H200 names.
- GPU functions use `@spaces.GPU`; default maximum runtime is 60 seconds. A custom function duration may differ. Supported app/runtime/library versions matter; this is not an arbitrary SSH/CUDA/Blender execution host.
- A qualifying free personal account can host up to two ZeroGPU Spaces; PRO can host up to ten. No qualifying Hugging Face account or hosting entitlement is connected here.
- Paid tiers can consume prepaid credits after included quota. Anonymous evaluation must not silently adopt a cached account/token or imply that ChatGPT/Claude/Kimi subscriptions include HF quota.

Three official model demos were inspected through read-only Hugging Face metadata:

| Space | Exact inspected source SHA | Observed application state | Consequence |
| --- | --- | --- | --- |
| `stabilityai/TripoSR` | `f84354eb350eb07a108faf33a6bc564d455f9764` | `RUNTIME_ERROR`; requested ZeroGPU, current hardware null | `torchmcubes` installation fails on a scikit-build-core version mismatch; not a working inference route |
| `microsoft/TRELLIS` | `e9f217fddcd570861645dcc67214d165dc73dd2c` | `CONFIG_ERROR`; current hardware null | Not a working inference route |
| `microsoft/TRELLIS.2` | `ebf60b20fc5a4607f90a1c11c0aab0ceeda5429d` | `RUNNING`; requested/current `zero-a10g` | A concrete public-demo candidate; this metadata does not allocate a GPU to us or establish a successful job |

The domain status `READY` is not sufficient: the two broken applications also report ready domain records. Application state, actual config access and successful work must each be checked.

The Space API still uses the pool identifier `zero-a10g`; this is not an `nvidia-smi` inventory or a measured VRAM allocation. The newer infrastructure document describes Blackwell-backed sizes. No physical accelerator model was independently observed for these requests.

## TRELLIS.2 experiment: generation and export completed

Initial runtime access returned CONNECT 403. After the environment restart, [config](spaces/recheck1/trellis2-config.json) and [API info](spaces/recheck1/trellis2-info.json) returned HTTP 200 and exposed the Gradio 6.1.0 contracts. The inspected Space source is `ebf60b20fc5a4607f90a1c11c0aab0ceeda5429d`; the app loads `microsoft/TRELLIS.2-4B` without an immutable weight revision. The freshly inspected model card at `af44b45f2e35a493886929c6d786e563ec68364d` declares MIT, but that metadata does not prove the running service's resident weight revision. The model's standalone LICENSE-file request returned 404; its retained error body is not license text.

The source establishes two separate GPU functions, both declaring `@spaces.GPU(duration=120)`: `image_to_3d` and `extract_glb`. The latent state is server-side `gr.State`. A successful generation is not itself the exported GLB. These are quota-controlled public demo functions, not unrestricted GPU access.

| Artifact/check | Actual outcome |
| --- | --- |
| Original input | Task-generated brass/cobalt diya, SHA `0e26e3719a4f90064c48582d8eac59749ecf35dc18cc2a5a1b10a23ee04b023b`, 1,812,060 bytes, 1024×1536 RGBA; root owns original-image provenance |
| First client attempt | Gradio client 2.0.1 constructed anonymously, but CPU-only `start_session` produced no final result within 30 s; cancellation requested, **zero GPU submissions**. Failed receipt preserved |
| Transport qualification | Explicit official `/gradio_api/call/start_session` with a stable `session_hash` completed in 2.008 s; source-pinned request/state handling inspected |
| Input preprocessing | Original RGBA supplied a real alpha mask, so source processing skipped its separate BRIA background-removal service; upload and preprocessing succeeded |
| Generation | One anonymous call, seed 23, `512` voxel profile, 8 sampling steps per stage, remaining guidance values at source defaults; **11.7707 s wall time**, successful response |
| Generated views | 48 original 1024×1024 JPEG snapshots from six render modes and eight viewing angles; three directly inspected. Six mode-selector icons were also extracted, for 54 JPEG files total. These are discrete views, not a continuous-animation performance test |
| Export | One further anonymous quota-enforced call in the same session, 100,000-face target and 1024 texture size; **10.8377 s wall time**, successful GLB response and download |
| Download | `original-diya.glb`, **3,805,612 bytes**, SHA `03a9928c489b4b3f2f52ea52c7cbea823eeeaeb082e51d092efb4eef952c966d`; glTF v2 header and declared byte length verified |
| Resource/cost boundary | Two GPU function submissions total, no retry, no HF account/token/cached login or prepaid credits used; no provider allocation. Actual GPU-device name, charged GPU seconds and remaining daily quota were not exposed |

The initial generation receipt deliberately held export pending a quota observation. The lead then authorized exactly one further anonymous request and relied on the public provider's admission/quota enforcement to accept or reject it. The later export receipt owns that successful outcome; the earlier held receipt remains unchanged. No success, GPU-time limit or remaining quota was inferred from the generation's wall time.

Executed source and evidence:

- [Failed client attempt](job/run1/receipt.json), [executed client script](job/trellis2_once.py), [hash-locked dependencies](job/requirements.lock).
- [Finite CPU protocol probe](job/direct-cpu-probe.json) and [source](job/direct_cpu_probe.py).
- [Successful generation receipt](job/run2-direct/receipt.json), [executed generation script](job/trellis2_direct_once.py), [original preview HTML](job/run2-direct/preview.html), [one original shaded view](job/run2-direct/preview-27.jpg).
- [Successful export receipt](job/run2-export/receipt.json), [executed export script](job/trellis2_export_once.py), [downloaded GLB](job/run2-export/original-diya.glb) and [structural inspection](job/run2-export/structural-inspection.json).

The Gradio client at the server's 6.1.0 tag is version 2.0.1. Its constructor uses **`token=`**, not an older `hf_token=` spelling, and defaults can consume cached login. The attempt explicitly used `token=False`, verified no auth headers and disabled analytics both through the flag and environment. One job also needs a separate SSE reader thread, so `max_workers=1` is not a sound transport setting for this version. The first client's completion issue was not assigned a proven cause; explicit sequential official HTTP calls succeeded. Their plain HTTPX transport never loads HF credentials.

The successful direct calls used the source-verified `SimplePredictBody.session_hash` contract and live function names. The export's full input array includes the hidden state placeholder `[None, 100000, 1024]`; the server restores the existing latent state. The export result was streamed once with an 80 MiB file cap and same-host HTTPS checks. The actual file is much smaller. No signed-query URLs or credential values were logged.

These scripts preserve an exact **one-shot experiment**, including original absolute capture paths and new-output guards. Reuse requires a fresh owned input, live-schema/version check, explicit free or billable resource budget and fresh receipt paths. Do not rerun a previously submitted GPU job merely because a client timed out. The local client virtual environment is excluded from source handoff; retain the lock file and installation receipts.

Three generated snapshots show a recognizable diya silhouette and brass/cobalt palette. Faceting and incomplete/translucent-looking flame geometry remain artist-review findings. Structural inspection records 96,190 indexed triangles, one material, two embedded images and `EXT_texture_webp`. The GLB has no rig, skin, animation, collision or authored LOD acceptance. Blender import, deformation where relevant, geometry/material correction, game-scale/collision/LOD work and actual Godot review are still required. This is an original prop-source generation pilot, not a finished hero or a closed game-quality gate. Root owns any later Blender/Godot evidence.

## Explicit external GPU worker options

These are verified open-source client candidates, not connected capacity:

| Client | Pinned source | Software license inspected | Relevant documented capability |
| --- | --- | --- | --- |
| Runpod CLI | `runpod/runpodctl@afbda964a842fb6bfa5ad394dc900949e08bc414` | GPLv3 text | List/get/start/stop/delete pods, serverless health and job status; an API account and resource are required |
| Vast CLI/SDK | `vast-ai/vast-python@42c3a47b44603775a5e31f54de0fce3994bd3f11` | MIT | Search offers, inspect and operate account instances; README now points to the `vast-cli` project |
| Modal SDK | `modal-labs/modal-client@32ee578ad2b6063a8b85f1bff4f96ee6263cb7f8` | Apache 2.0 | Deploy serverless functions and interact with platform resources; official skill installation is documented |

Open client source does not mean free backend compute. No current prices, available inventory, account credit or region capacity were measured. Installation alone would not connect the user's subscriptions to these providers. An already-owned GPU can instead be attached through the user's existing SSH configuration without buying a new service.

Before a billable worker is created, record the provider/account/region, named machine or endpoint, hourly maximum, maximum job duration, storage/egress budget and stop/destroy policy. A timeout is not evidence that the provider stopped charging: Runpod explicitly documents that timed-out jobs/resources can remain live, and status inspection must precede a retry. Verify the exact resource stopped and whether retained disks still incur charges. These are necessary budget fields, not an assertion that any resource exists here.

For an existing authorized Linux GPU worker, use the laptop as the control machine, an existing SSH key and verified host identity. Bind any model server to that worker's loopback and forward a loopback port over SSH. Check the named GPU's **free** memory, driver/runtime/kernel compatibility and actual inference; then submit one versioned asset job with input/model/code hashes. Download and verify outputs before cleanup. This cloud presently has no TCP grant or worker endpoint, so no SSH session can be claimed ready.

## Gaming-focused division of work

| Machine | Intended work after qualification | Evidence still required |
| --- | --- | --- |
| RTX 4070 laptop, 8 GB dedicated | One small local coding model, source control, Godot interaction, moderate Blender work; alternate heavy GPU sessions | Actual model tool-call behavior, context/memory and game/render performance |
| Original PS4 Linux | Small CPU-model experiment, auxiliary lightweight jobs or test worker over SSH | Console firmware/distro/available RAM/ISA, exact build and measured speed; no GPU acceleration assumed |
| Current 4-core/32 GiB CPU cloud | CPU-model qualification, source/test/build jobs and orchestration documents | Parent CPU worker owns the actual build/inference receipt; this access study did not perform inference |
| Qualified shared demo or explicitly attached GPU | The public demo already generated/exported one original prop; a separately attached worker can run broader offline jobs | This bounded success does not establish hero quality, arbitrary Blender/CUDA execution, repeat capacity or actual-engine acceptance |

Keep generation out of authoritative match runtime. Retain the existing Godot/Blender/glTF pipeline and the current complete native 3v3 gate before 6v6. More machines and agent roles do not close hero, animation, networking or physical-hardware acceptance gates by themselves.
