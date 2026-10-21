# Game reconstruction and browser-port source review

Checked 21 October 2026 against YUGA source `ec4d7bb2b8d5a14fce7cab68fef6efc9dc50bf72`.
This is a bounded primary-source study, not a transcript or identification of
anything in `https://youtu.be/tDWtcyeNNew`. The video's contents were unavailable
to this worker. No live game, model inference, binary decompilation or engine
build was executed in this pass. All five projects below were selected
independently because they answer the user's game-reuse question.

## What the available projects actually do

| Project and freshly resolved revision | Evidence read | Classification and useful lesson | Reuse boundary |
| --- | --- | --- | --- |
| [REA](https://github.com/morluto/rea/tree/01788bac863ac786bfbb648cad69b11e23b40a89), `01788bac…` | README capability/requirements table, package version, MIT license; model-artifact documentation; native-investigation document retained for the next scoped study | Current source package is **6.7.0**, versus the earlier local study's 6.5.0. Connects agents to Ghidra/Hopper/IDA, static JS/.NET/APK and browser inspection. Model-file support reads GGUF/safetensors metadata; it **does not load weights or run inference**. Godot PCK inspection is a relevant future check of our own exported packages. | MIT for REA-authored code; external tools retain their terms. No REA upgrade was installed. Tool capability does not reconstruct an absent game client or its server. Requires a selected accessible input and comparison oracle. |
| [ioquake3](https://github.com/ioquake/ioq3/tree/87a99d18206e878a20289f05ac3c16005dcae5c3), `87a99d18…` | README native/web build and game-data sections, GPLv2 text, `code/cgame/cg_predict.c` prediction description and selected command-loop code | A continuation of released Quake III source, not a new LLM reconstruction. Current README explicitly includes **Emscripten web builds**. Client prediction starts with a server player-state snapshot, replays unacknowledged commands and decays correction error. | GPLv2 engine/game code; original Quake III data is excluded from that grant. A standalone original game is possible under the stated code terms. Study prediction semantics; do not copy its code into a differently licensed runtime without resolving compatibility. |
| [QuakeJS](https://github.com/inolen/quakejs/tree/977b188e05b239b6c48d7ecda9d04e9ca03f1578), `977b188e…` | README, selected asset-graph/packing sections of `bin/repak.js` | Concrete browser-port example: **ioquake3 compiled through Emscripten**, WebSockets for transport, separate content hosting and map-related asset packs. README advertises [quakejs.com](http://www.quakejs.com); availability/playability of that live site was **not tested here**. This pinned project describes JavaScript output; do not relabel it a newly verified WASM build. | README labels its own code MIT; `LICENSE` returned 404. That label does not replace the ioquake3 submodule's GPL or game-data EULA. Do not adopt the old installer/packing script blindly; selected source constructs shell commands from paths and requires a separate review before use on new inputs. |
| [OpenRA](https://github.com/OpenRA/OpenRA/tree/1f594e32065615ed1847962c80ecfe6e868a11c3), `1f594e32…` | README/modding/license sections, GPLv3 text; `OpenRA.Game/World.cs` tick, render-tick and sync-hash sections | Playable native RTS engine with reimagined Westwood games and mod support. Actor/trait ticks, deferred frame-end actions and separate render ticks illustrate explicit simulation/presentation ownership. Sync hashing includes actor/synced-effect state and shared RNG state. | GPLv3-or-later code. This is not permission to redistribute every Westwood asset, nor evidence that its RTS networking should replace a real-time shooter authority design. No OpenRA assets or client downloaded. |
| [noclip.website](https://github.com/magcius/noclip.website/tree/e47a8cc8a9fe16e83adc0bf19153ff04c666ceca), `e47a8cc8…` | README development/controls and license notice | Browser map/model renderer built from format reverse engineering. Controls expose camera travel, scene selection, freeze/time stepping and saved camera states. [noclip.website](https://noclip.website) is a reference for **scene inspection**, not proof of a reconstructed playable campaign, combat AI or server. The live site was not visited in this pass. | MIT notice explicitly says some implementations were reverse engineered without a clean-room process; do not call the entire project clean-room. Separately credited icons and source-game assets retain their own terms. |

## How this differs from a video-to-game claim

There are several distinct routes:

1. **Released-source port:** compile an existing engine for a new target and
   supply compatible game data. ioquake3/QuakeJS demonstrate this route; input,
   graphics, audio, networking and asset delivery still need platform adapters.
2. **Reimplementation:** implement compatible rules/formats/runtime behavior in
   another engine. OpenRA provides a playable reimagining, not a claim that a
   model generated all original source code automatically.
3. **Format reconstruction:** parse model/map formats and reproduce their
   rendering sufficiently for inspection. noclip's camera controls are useful
   evidence of this narrower goal; a viewer does not provide complete gameplay.
4. **Agent-assisted analysis:** use REA with an actual target and a decompiler,
   browser or static parser, then test an implementation against observations.
   It is an analysis toolchain, not itself an LLM or 3D generator.
5. **Generated imitation or world-model video:** output that resembles gameplay
   still needs explicit tests for persistent state, collision, controllability,
   repeatability, network authority and exportable meshes/rigs. No candidate in
   this worker's five-source set establishes those properties through an LLM.

None of these findings supplies Deadlock/Overwatch source, character meshes,
animation graphs, maps or authoritative servers. Existing YUGA evidence remains
the original Mikk component analysis and the separately attributed Source 2
Viewer animation-key audit; those historical results are not newly completed
work in this study.

## Concrete desktop roadmap recommendations

- Retain Godot/Blender/glTF for the active hero-and-arena gate. A renderer/engine
  replacement does not resolve the current hair, drape, rig/contact or artistic
  acceptance defects. Generated assets enter that same acceptance gate.
- Add an **optional REA 6.7 evaluation**, separate from automatic installation:
  inspect one owned PCK and one model header, compare with independent parsers,
  and record the installed package hash/provider versions. A header digest is
  not a weight-file digest. Do not increase campaign completion counts for this
  source review or merely installing the tool.
- In the existing native two-client authority milestone, use the ioquake3 study
  to define original tests: replay unacknowledged inputs after a snapshot;
  reject stale/out-of-window inputs; isolate simulation correction from camera
  smoothing; handle teleports separately. Test with two actually rendered
  clients under delay/loss/reconnect. These are proposed tests, not executed
  YUGA behavior in this pass.
- For minions/waves, keep simulation ticks, render-only effects, shared random
  choices and spawn/despawn queues under explicit ownership. The selected
  OpenRA source explains this separation; no network architecture change is
  justified by this reading alone.
- Add deterministic scene/camera bookmarks, pause/time stepping and material
  inspection to the existing art-review harness when useful. Take the workflow
  lesson from noclip; keep YUGA's original assets and renderer.

## Concrete Android roadmap recommendations

- **M1/M3:** establish renderer/device limits and one finished hero before
  expanding content. A browser port is not an Android performance measurement;
  desktop hero assets still need measured mobile LOD/material/texture variants.
- **M5/M6:** preserve server authority and test actual ten-client behavior.
  QuakeJS's README explicitly reports a native/web transport compatibility
  limitation; platform builds require a common tested protocol rather than
  assuming code compilation creates cross-play.
- **M9/M10/M15:** apply the asset-graph lesson to original content delivery:
  shared core resources plus bounded map/hero bundles, content hashes, declared
  dependencies and missing/offline/update tests. Preserve the current packaging
  contract before proposing a new downloader. The old QuakeJS packer is not an
  Android-ready dependency.
- Keep asset-generation models in an **offline authoring pipeline** by default.
  This research gives no reason to ship large generative models in the APK or
  make competitive match simulation depend on nondeterministic inference.
- Keep all **18 implementation rounds / 108 tasks uncompleted** until their
  own evidence exists. This study does not shorten that schedule or demonstrate
  that another game's art can be reused automatically.

## Retrieval and verification

[sources.json](sources.json) records immutable URLs, resolved commits, response
codes, UTC retrieval times, exact byte counts and SHA-256 hashes. Five ordinary
`git ls-remote https://github.com/<owner>/<repo>.git HEAD` calls succeeded through
the inherited proxy. Fifteen small source files returned HTTP 200; one guessed
QuakeJS `LICENSE` path returned 404. Successful downloads totaled **252,209
bytes**. No repository clone, dependency installation, game-data download,
model-weight download, decompiler invocation or live-site execution occurred.

The saved files are upstream reference material, not runtime imports. Preserve
their original notices and the accompanying licenses. OpenRA/ioquake3 sources
retain GPL terms, REA/noclip their respective MIT notices, and QuakeJS's README
MIT declaration remains incomplete adoption evidence until the required exact
component notices are resolved. No blanket repository license overrides these
upstream terms.

Next owner: root integrates the bounded recommendations into both roadmaps;
video inspection remains a separate source-identification task. Actual gameplay,
GPU inference and Android hardware acceptance remain unrun.
