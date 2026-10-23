# Rama source generation through the official public GPU service

On 23 October 2026, one original RGBA Rama concept was successfully processed by the [official public Microsoft TRELLIS.2 demo](https://huggingface.co/spaces/microsoft/TRELLIS.2). One anonymous generation and one same-session GLB export completed. These are actual provider-controlled GPU function results, not a newly acquired general-purpose GPU machine.

The canonical [Rama GLB](../../../../art/production-stage-oct23/hero-source/rama-generated.glb) is **4,480,716 bytes**, SHA-256 `0c9fe46baa0a2f6e5f9cdb9386aad1405f9f22470a729c2538142576981f5c0b`. It is stored once under art; this evidence bundle does not duplicate it. The [original input](../../../../art/production-stage-oct23/images/hero-concept.png) is 2,407,184 bytes, SHA-256 `674077b910106cc718748530a1fa3fd4400ef959c2461b06060e41ff759c6872`. Root retains its managed image-generation provenance separately.

## Actual work and admission

| Stage | Observed outcome |
| --- | --- |
| Current capabilities | No local NVIDIA/ROCm inventory tool, GPU-provider CLI, configured GPU capability, secret or outbound identity; outbound manifest version 1 has no connections |
| Official Space metadata/config/API | HTTP 200; source `ebf60b20fc5a4607f90a1c11c0aab0ceeda5429d`, application `RUNNING`, Gradio 6.1.0; named endpoint schema exactly matches the earlier successful pilot |
| Input processing | Original genuine RGBA mask; CPU session/upload/preprocessing completed without a separate background-removal model |
| Generation | One request, seed 71, 512 profile, eight sampling steps per stage; provider event `c681a30ef20a4ac9bd5e76c5e07f55bc` completed in **16.6727 s wall time** |
| Export | One separate quota-enforced request, 100,000-face target, 1024 texture; event `fe9e327720124d65b66ea6ad92ff2174` completed in **12.2215 s wall time** |
| Download | HTTPS same-host bounded download; valid glTF 2 container and byte-length header; SHA-256 bound above |
| Resource boundary | Exactly two GPU function submissions, zero GPU retries, no login/token/cached account, paid API or rental; local HTTP client exited 0 |

The [pinned app source](https://huggingface.co/spaces/microsoft/TRELLIS.2/blob/ebf60b20fc5a4607f90a1c11c0aab0ceeda5429d/app.py) declares the separate GPU functions. The [model card](https://huggingface.co/microsoft/TRELLIS.2-4B/blob/af44b45f2e35a493886929c6d786e563ec68364d/README.md) metadata still declares MIT at `af44b45f2e35a493886929c6d786e563ec68364d`. The app's exact resident weight revision and physical GPU model/VRAM were not independently observed. Its legacy `zero-a10g` metadata label is not a hardware inventory. Service wall times are not GPU kernel timing or a measure of remaining quota. Provider admission was used normally; no account, quota or network access was bypassed. Metadata licensing is not a complete clearance of every dependency or output term for release.

The official TripoSR application was also checked without an inference submission. It remains `RUNTIME_ERROR` at source `f84354eb350eb07a108faf33a6bc564d455f9764`, with its existing `torchmcubes`/scikit-build-core installation failure. A ready domain entry does not make that application runnable. No alternate inference was submitted because the primary pipeline succeeded.

## What the result establishes

[Structural inspection](run1/structural-inspection.json) found one mesh, **96,660 indexed triangles**, 93,214 position-accessor vertices, one material and two embedded WebP images. There are **zero skins and zero animations**. All buffers and images are embedded. The preview contains 48 rendered model views and six UI mode icons; all remain inside the [original provider preview](run1/preview.html). Three separately retained views were actually inspected: [rear](run1/preview-24.jpg), [side](run1/preview-27.jpg) and [front](run1/preview-28.jpg).

The cobalt/ivory/gold costume, long silhouette and relief detail are recognizable. Face, hair and fine ornament are softened; texture contrast and anatomical/contact quality require artist work. This source has no demonstrated deformation, locomotion, ability motion, collision, authored LOD or gameplay-distance acceptance. The native-art worker owns subsequent real Blender import/render checks. This report closes no finished-hero or full-game graphics gate.

## Reuse, reproducibility and evidence

This reuses the [earlier verified transport and pinned HTTPX environment](../../ps4-swarm-oct23/access/README.md), the existing official model service and the source-confirmed API contracts. It does not rebuild a 3D foundation model or reconstruct commercial game clients. The [executed script](trellis2_pipeline_once.py) adds explicit input/output arguments, a combined two-submission ceiling, atomic receipts and full queue errors. It validates the exact input hash before any HTTP request and never retries an admitted or ambiguous GPU event.

The [actual receipt](run1/receipt.json) binds input, script, event identities, observed stages, timings and output. A final-source [negative preflight check](preflight-verification-final.json) rejected a wrong hash with exit 1, zero HTTP calls and zero GPU submissions; its [failure receipt](preflight/receipt.json) is a local test, not a failed remote generation. The current source is not a continuously running GPU service or an unrestricted scheduler. The retained local PID identifies only the completed CPU transport process.

To deliberately submit another original input through the same supported demo, first inspect its live source/schema, account mode, quota and terms, then use fresh output paths and a bounded resource decision. The copied script is an explicit one-shot submission, not a startup step or an automatic retry mechanism. No inference should be submitted merely to make a dashboard indicator look active.

[The manifest](manifest.json), [capability evidence](capabilities.json), [primary metadata ledger](metadata-ledger.json), [supplemental source ledger](supplemental-ledger.json), and `SHA256SUMS` retain the exact evidence boundary. The bundle excludes virtual environments, cached weights, bytecode, source/build caches and the duplicated GLB. No personal device, paid provider account or general-purpose GPU host was attached by this worker.
