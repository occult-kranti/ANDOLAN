# YUGA reuse and provenance ledger

Recorded 16 October 2026 UTC. This ledger covers the research contribution. Runtime dependencies and authored mythology/character provenance also require their owners' inventories before release.

| Material | Exact provenance / license | Use in YUGA | Imported material |
| --- | --- | --- | --- |
| Tank Battle room/schema/network slice | `endel/tank-battle-multiplayer`, `6339493130b4b1d4d28f0f52d17b2fba738c7d47`; MIT, Endel Dreyer / Maksims Mihejevs. Exact files and hashes in [rea-summary.json](../tools/research/rea-summary.json). | Source analysis and actual REA static analysis informed authority, score, lifecycle and input-validation review gates. | No game code, art, model, audio or dependency imported. Research summaries are original. |
| Valve GameNetworkingSockets documentation | `ValveSoftware/GameNetworkingSockets`, `d534c19aa760df3fb75fd20db13ba1932b8a5463`; BSD-3-Clause, Valve Corporation. | Read README, README_P2P and license to separate transport from gameplay/services. | No native library, code or binary imported; no compilation. |
| Sketchbook | `swift502/Sketchbook`, `62f4b7986fd1ce1e4f91daba89ef032c20a6ce55`; MIT. | Prior bounded camera/transition analysis, explicitly referenced as prior work. | No YUGA source/assets imported. |
| Geckos snapshot interpolation | `geckosio/snapshot-interpolation`, `a171cefb626085bfff5241cbd60c8099bdd742bf`; BSD-3-Clause. | Prior source/probe evidence on timestamp buffering and edge cases. | Not adopted as a game dependency; no YUGA source copied. |
| REA | Official `rea-agents` 6.5.0 npm runtime, previously registry-integrity/signature checked; MIT root project. | Optional external research tool. New three-file analysis and one ambiguous semantic trace. | No runtime product dependency or persistent agent/MCP integration. Full raw evidence stays outside checkout. |
| Schreiber teaching text | Public mirror `eugenioclrc/gamedesignconcepts`, `5c98165cb261143bda0147463acbaee922ca46c9`; canonical-course attribution retained. Mirror describes Creative Commons publication; exact live canonical license version not independently verified. | Selected sections read and paraphrased as design lessons. | No course text copied into the product. No license inference from mere public availability. |
| Overwatch, Deadlock, Dota 2 | Commercial games; official public web requests blocked in this environment. | Broad genre comparison, explicitly not current patch verification or implementation recovery. | No source, binary, assets, story, dialogue, map layout, character design or branding imported. |
| YUGA simulation, hero kits, map, UI, meshes and audio | Authored in this branch by project owners; review actual source and content research separately. | Original implementation of the accepted shared contract. | Research does not certify that every authored asset is finished or production quality. |
| YUGA initial runtime world art | Renderer owner reports original `client/world.ts`, `client/render-kit.ts`, `client/scenery.ts`: shared primitive meshes, authored canvas textures, lane architecture and combat effects. | The initial character placeholders are superseded by the separately documented skinned asset pipeline below. Environment geometry/effects remain authored. | This is an author provenance report, not an independent forensic audit. Local pose is immediate; remote target damping uses a time-based exponential with snaps, not timestamp buffering or extrapolation. |
| MakeHuman anatomical asset data | Official `makehumancommunity/makehuman`, `a8bc2d54ff0ac92e78ff71431b1023eda42bf482`; CC0-1.0 under root LICENSE section C / LICENSE.ASSETS plus mesh/rig file metadata. Exact files and SHA-256 in [source manifest](../art/sources/makehuman/manifest.json). | Continuous body topology/UVs, two adult morph data sets, native163joint skeleton and normalized native skin weights are actually imported into the hero GLBs. | Data is bundled in `art/sources/makehuman`. No AGPL application source copied or imported. This is external anatomy reuse, not an all-original mesh claim. |
| Authored hero mesh additions and animation | Original `art/pipeline/{anatomy,geometry,build_heroes,animations}.py`; generated concept/brocade/gold images are separately recorded by the project. | Layered garment meshes, ornaments, weapons, face additions, hair, per-hero proportions, original9clip motion and bowstring helper; actual GLB inventory in [hero-assets.json](../art/hero-assets.json). | These are original additions around licensed anatomy. No commercial game models or motion capture imported. Actual Blender previews are distinct from generated concept art; key-art parity and commercial animation polish are not claimed. |
| Lobby concept illustration | The authored build notices identify OpenAI image generation. | Presentation illustration, separate from runtime procedural character/world art. | Does not establish a completed cinematic or production character asset pipeline. |

## Boundaries

A permissive repository license does not automatically license every external asset linked from its README. Tank Battle's linked third-party tank models were not fetched or reused. The REA tool's ability to inspect binaries does not grant permission to copy game content, and this investigation performed no binary extraction.

The research produced documents and compact evidence metadata. No new game dependency was added. If future implementation copies a substantial permissive source fragment, append its exact file/commit, local destination, retained notice, modifications and validation; do not silently relabel copied code as original. A future asset import needs its own creator, license, source file/hash, allowed uses and attribution entry.

## Verification scope

- Selected Tank Battle file hashes were compared against the earlier immutable-URL manifest and matched.
- The new Valve documentation was fetched over normal HTTPS from its official pinned GitHub repository; bytes/hashes are in [source-access.json](../tools/research/source-access.json).
- REA analysis and trace both exited 0; the trace remains `ambiguous` and coverage `partial`.
- No reference game was launched, no whole repository audit was performed, and no commercial-game fidelity or balance claim follows from this ledger.

The detailed research and proposed gameplay gates are in [MECHANICS_RESEARCH.md](MECHANICS_RESEARCH.md); the staged production obligations are in [PRODUCTION_ROADMAP.md](PRODUCTION_ROADMAP.md).
