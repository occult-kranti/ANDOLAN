# Panel round 1 — rendering and production tools

Date: 15 November 2026. Researcher: tools/platform specialist. Read-only examination of current `main` plus native/backup branch documentation. No tool was installed or application code changed in this round.

## Recommendation

Keep the game in its existing engine. The active YUGA desktop game is Godot, while this `main` checkout is the separate PlayCanvas ANDOLAN browser game. Add tools around a concrete asset/capture task; adopting several render engines together would require separate scene, input and physics integrations and does not itself improve the accepted game.

Use **Blender + existing engine + browser/native screenshot evidence** for production assets and UI verification. **HyperFrames** is a suitable optional trailer/contact-sheet companion. **Raea** and **ThreeRT** warrant isolated examples after a functioning scene and suitable GPU adapter are demonstrated. **REA**, **Raea**, and **rea-video** are three different projects.

## Verified inventory

| Tool and primary source | Verified purpose / license | Fit and installation decision |
| --- | --- | --- |
| [Raea](https://github.com/shinyobjectz/raea) / [license](https://github.com/shinyobjectz/raea/blob/main/LICENSE) | React/TypeScript compositions rendered by Rust/Bevy/wgpu; frame/video rendering and live game commands. Current license **FSL-1.1-ALv2**, with a competing-use restriction and Apache-2.0 grant after two years. Source available, not presently an unrestricted open-source license. | Optional isolated renderer, not a replacement for existing YUGA/Godot. Official Linux x86_64 release exists; source build needs Rust, Bun, CMake, NASM and native libraries. Prefer reviewed release + checksum to a long new engine build. |
| [ThreeRT](https://github.com/meshy-dev/ThreeRT) / [comparison method](https://github.com/meshy-dev/ThreeRT/blob/main/docs/COMPARE.md) | MIT Rust/wgpu renderer plus TypeScript scene/gameplay/voxel packages. Native engine uses hardware ray queries where available and a software BVH otherwise. The same scene can use ordinary three.js browser rendering. | Isolated lighting experiment only. Node 24, Bun and Rust required for source engine. Native packaged clients documented for Apple Silicon macOS 14+ and iOS 17+ are closed source. Browser fallback is not proof that native path tracing runs in every browser/device. |
| [HyperFrames](https://github.com/heygen-com/hyperframes) / [CLI](https://github.com/heygen-com/hyperframes/blob/main/packages/cli/README.md) | Apache-2.0 HTML/CSS/media-to-MP4 pipeline; seekable browser frame capture with Chromium/Puppeteer and FFmpeg. | Best near-term optional web-capture/trailer tool. Node >=22 and FFmpeg. Install pinned in a separate tooling directory; do not add it to the game runtime. |
| [rea-video](https://github.com/JuneYaooo/rea-video) | Apache-2.0 shot/video breakdown and reconstruction reports in VIDEO.md. Python >=3.10 and FFmpeg; optional video-model endpoint improves analysis. | Useful if the user supplies actual video references. It analyzes footage, not executable game mechanics. No reference clip has been supplied in this task. |
| [OpenMontage](https://github.com/OpenMontageInc/OpenMontage) | AGPL-3.0 agentic video production toolkit. Python, Node, FFmpeg; providers vary from local models to paid external APIs. | Optional production-study checkout. Not needed to compile either game. Do not conflate installation with having configured generation providers or a complete production. |
| [OpenJutsu](https://github.com/D3voz/openjutsu) | MIT app code for video character/object swaps on ComfyUI with H3/SAM/Qwen. Node >=22.6, Python, ComfyUI >=0.41.2; documented tested GPU is RTX 4060 Ti 16 GB plus 64 GB RAM. Models and custom nodes have separate terms. | Defer model/runtime install here: no NVIDIA device was observed. Not a game engine, rigging tool, or way to obtain interactive hero motion from a still. The distinct [Comfy-hosted variant](https://github.com/Comfy-Org/comfy-openjutsu) requires an account, API key and deployment credits. |
| [Rapier](https://github.com/dimforge/rapier) / [license](https://github.com/dimforge/rapier/blob/master/LICENSE) / [official web support](https://rapier.rs/) | Apache-2.0 2D/3D physics with Rust, JS/Wasm and Bevy bindings. | Good physics reference or isolated browser experiment. Existing authoritative simulation and Godot physics already have behavior/contracts; introduce a new backend only for a specified missing feature and parity tests. |
| [three-gpu-pathtracer](https://github.com/gkjohnson/three-gpu-pathtracer) | MIT three.js path-tracing project. Current main documents WebGPU compute rendering, supports selected PBR material classes, and calls its WebGPU API unstable. | Useful external comparison project. Pin `three-mesh-bvh` and renderer versions. Does not plug directly into PlayCanvas or Godot. |
| [Blender license](https://www.blender.org/about/license/) / [requirements](https://www.blender.org/download/requirements/) | Cross-platform asset creation/rendering. Blender binaries GPL-3.0-or-later; upstream source default GPL-2.0-or-later, individual modules differ (Cycles Apache-2.0). | Strongest useful install: headless procedural modeling, glTF export, camera renders. Generated artwork does not thereby become GPL; redistributed Blender/add-on code retains its own applicable terms. Actual GPU rendering still needs a compatible adapter; CPU rendering can support bounded asset previews. |

## Corrections to supplied claims

- Raea local rendering and Linux/macOS/Windows support are supported by its README. The supplied timing numbers and a generic 3–5x CPU slowdown were **not independently reproduced**; they must remain source claims, not project performance promises. Software Vulkan requires an installed working adapter/driver, not merely a CPU.
- ThreeRT advertises 60 fps on selected scenes. Its comparison describes measurements on one Mac and dynamic render scaling to maintain that rate. This is not a universal 60 fps guarantee. Its repository metadata reports creation on 10 November 2026; that does not establish a public launch date of 13 November. Windows, Android and Steam Deck native support were not established by the current installation documentation.
- Rendering tools create frames and footage. Neither a concept image nor a renderer's own demo establishes polished real game screens, a complete hero roster, networking or sustained hardware performance.

## Repository evidence and environment

`origin/game/yuga-native-production` at `7162b5d0` contains an `AGENTS.md` directing work to `docs/START_HERE.md` and subsystem ownership before parallel changes. That guide identifies Godot 4.6.3 YUGA native, one Rama hero, offline Confluence and training, and still-open full roster, native online, art/motion and hardware qualification. It explicitly treats root ANDOLAN as a separate game and the backup branch as historical recovery, not accepted game source.

The native guide lists 17/78 scoped accepted desktop packets and 0/13 complete rounds; those are historical branch claims, not independently rerun outcomes in this round. Read the active handoff before choosing the next native packet. No backup assets were copied into main.

The current host probe found Linux x86_64, Node v24.22.2, approximately 62 GiB system RAM, and 104 GiB free filesystem space. `/dev/dri/card0` exists, but no `/dev/nvidia*` was observed. The first PATH probe found no `ffmpeg`, `blender`, `cargo`, `rustc`, `bun`, `vulkaninfo` or system Chromium. GPU vendor/features and software Vulkan were not established. This supports installation feasibility, not rendering performance.

Existing `docs/research/REA_RUNBOOK.md` documents `rea-agents@6.5.0` as optional static source-analysis tooling and Sketchbook as a pinned reference. Its `/workspace/...` paths are historical and must be rechecked here. Raea is a distinct engine; rea-video is a distinct footage analyzer.

## Reproducibility anchors

Read-only `git ls-remote <canonical-url> HEAD` succeeded for all eight source repositories. Observed heads:

| Repository | HEAD |
| --- | --- |
| shinyobjectz/raea | `6665a2e5a8b735172d5515e5f498e5968f16bdb7` |
| meshy-dev/ThreeRT | `1a25d1fc240ca5ba6675e197ca8961cf559b05f8` |
| heygen-com/hyperframes | `e2430edecf5492a02a363eaa5c30ad2708af5aee` |
| JuneYaooo/rea-video | `ebe853e330d63719a1f91754f789647c515eac19` |
| OpenMontageInc/OpenMontage | `fecb9a1e3cc23ef84de30b272059457a427f16f8` |
| D3voz/openjutsu | `7fe118bb5a61fcfac0148e1bfea3dd29884dbf26` |
| dimforge/rapier | `475caa3ff4646fd9a796b67d14116256f4962bc7` |
| gkjohnson/three-gpu-pathtracer | `e91ee806eed5069eaed531a7f1f4f2b69debf278` |

Sources reviewed: **35 Exa search result slots across 7 queries**, followed by 10 direct primary-page fetches. The 35 slots include duplicates and irrelevant results; only the linked primary pages above support the recommendations. No third-party performance comparison was adopted as a measured fact.

## Round 2 questions

1. Select the product and one end-to-end screen/asset workflow before installing multiple new engines.
2. Prove Blender/FFmpeg or a selected renderer with a tiny original scene and retain command, output and checksum.
3. Compare generated targets to actual runtime screenshots; accept screens by visual/interaction evidence, not a mockup alone.
