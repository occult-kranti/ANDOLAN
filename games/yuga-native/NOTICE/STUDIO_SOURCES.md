# Studio credits and reuse scope — 15 November 2026

Keep this with [ASSET-NOTICE.md](ASSET-NOTICE.md), existing dependency notices
and font licenses. This addition records the new studio workflow; it does not
replace earlier attribution or grant new rights to commercial game data.

| Source / creator | License / role in this delivery |
| --- | --- |
| [Godot Engine contributors](https://github.com/godotengine/godot) | MIT engine; official 4.6.3 editor/exporter and Windows runtime. The selected Linux public-source runtime has the reviewed one-line pipeline-priority patch; its exact source, patch, build and third-party notices are bundled. |
| [Blender contributors](https://www.blender.org/about/license/) | GPL Blender application; official 4.3.2 used for original map authoring. Application licensing is separate from the original exported geometry. |
| [PlayCanvas contributors](https://github.com/playcanvas/engine) | Existing MIT browser engine; unchanged browser YUGA and ANDOLAN retain their existing notices. |
| [FFmpeg contributors](https://ffmpeg.org/legal.html) | Ubuntu binary/build configuration and its applicable LGPL/GPL terms retained by package provenance; external capture tool, not newly embedded in game binaries. |
| [Microsoft Playwright contributors](https://github.com/microsoft/playwright) | Apache-2.0 browser test/capture tool; Chromium carries its own third-party notices. |
| [morluto/REA contributors](https://github.com/morluto/rea) | MIT analysis toolkit; pinned source research and REA 6.5.0 static analysis of owned project TypeScript. No MCP registration. |
| [GDQuest contributors](https://github.com/gdquest-demos/godot-4-3d-third-person-controller) | MIT source-code study. Pinned repository art is CC-BY-NC-SA-4.0 and is excluded from intake/product. No source code or art was copied into the new map/briefing. |
| [Dimforge/Rapier contributors](https://github.com/dimforge/rapier) | Apache-2.0 source reference; not added as a new Godot runtime physics backend. |
| [HeyGen/HyperFrames contributors](https://github.com/heygen-com/hyperframes) | Apache-2.0 source reference for future capture/composition work; source prepared, CLI/render runtime not claimed installed. |
| ANDOLAN/YUGA project studio work | New launch briefing and schematic, exact-texture sharing adapter and Relay Foundry Blender map geometry are original project work. Per-artifact source/build/validation records accompany them. |

Prometheus, OWLib/OWM, OpenGOAL, OpenLara, OpenMW, OpenRA, OpenJK, Xash3D,
Raea, ThreeRT and the other video projects are acknowledged in the research
reports/catalog as studied candidates. They are not newly redistributed game
components or proprietary asset sources. Their project-specific license and
game-data requirements must be checked before any later reuse.

Exact revisions and reviewed license-file hashes for the fifteen catalogued
projects are in `tools/research/opensource-catalog.json`. Preparation receipts
distinguish fetched source from installed/executed tools. The new concept boards
were generated with the built-in OpenAI image tool; their prompts and rejected
generated text/mechanics are recorded under `docs/concepts/studio-2026-11-15/`.
They are not shipped 3D assets or proof of production-game quality.
