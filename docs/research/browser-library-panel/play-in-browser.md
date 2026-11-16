# PlayInTheBrowser panel: source and reuse study

15 November 2026. Product: YUGA native and its separate browser tooling.
Baseline `work/yuga-studio@7162b5d0`; existing uncommitted work preserved.
This owner changed only this report and [its source catalog](play-in-browser-sources.json).

## Decision

The strongest direct reuse is the **MIT browser-client layer** from
[JonCodeOfficial/gta-vice-city-wasm](https://github.com/JonCodeOfficial/gta-vice-city-wasm/tree/5c6cccc56c1df5c3717c0b39953d5fe833f97b73):
OPFS file storage, save-transfer patterns and range-aware local serving for our
own files. Its engine/data directories are outside this adoption. The first
proposed experiment is an isolated own-asset serving probe, with explicit
adverse tests, rather than a replacement game engine or registered production
service worker.

For native map production, **FuncGodot** is a useful related MIT authoring
candidate. It is discovered through Quake map tooling, not directly listed by
the blog. A texture-free original `.map` to Godot mesh/collider spike remains
unrun; current user steering prioritized the supplied ultimate-ability video.

## What was actually accessible

The blog's public HTML was fetched (58,962 bytes), and its inline `GAMES` array
was extracted as strict data without running site JavaScript. There are 75
records: 66 point to INXANITY game pages and only three directly to GitHub.
Seventy-one are tagged “Open Source,” and all 75 set `requires:false`.
These are catalog claims, not a reuse grant or reliable data requirement.

The direct Vice City source README requires the user's own PC installation;
Xash instructions require a legitimate `valve` directory. Their source facts
contradict the catalog's universal no-files flag. The blog also references two
unrelated third-party script hosts; no such scripts or hosted games were executed.

Public HTML from q1/q2.pieter.com explicitly credits FTE QuakeWorld. Selected
primary GitHub files were then read at full commit pins. The linked
`CJ-Joseph/shar-wasm` repository returned HTTP 404; its unavailable code/license
was not inferred. No game assets, ROMs, commercial maps, account credentials or
private services were accessed.

## Concrete resource and code dispositions

| Project / exact pin | Useful subsystem | License / data boundary | Disposition and next implementation |
| --- | --- | --- | --- |
| [Vice City browser client](https://github.com/JonCodeOfficial/gta-vice-city-wasm/tree/5c6cccc56c1df5c3717c0b39953d5fe833f97b73) | `public/sw.js`, `src/convert/opfs.js`, selected save-transfer patterns | [MIT grant](https://github.com/JonCodeOfficial/gta-vice-city-wasm/blob/5c6cccc56c1df5c3717c0b39953d5fe833f97b73/LICENSE) covers original client/SW/OPFS/build code; retain 2026 joncodeofficial notice. It excludes commercial game rights. | Adopt selected tooling after tests. Serve only owned YUGA files; exclude `public/engine`, `public/revc`, game data and GTA-specific saves. |
| [FTE QuakeWorld](https://github.com/fte-team/fteqw/tree/f09ac7cccd2d713ddf881d3f1324703082c2cfe4) | `PM_ClipVelocity`, `PM_SlideMove`, `PM_StepSlideMove`, friction/acceleration and client prediction architecture | Engine GPLv2; inspected `pmove.c` header allows GPLv2-or-later. Any code adaptation must retain applicable copyleft/source obligations. Game data and website frontend are separate. | Study a movement/contact behavior specification; do not transplant engine code or legacy map data into YUGA by giving credits alone. |
| [Xash3D FWGS](https://github.com/FWGS/xash3d-fwgs/tree/707596f4905689ec224e993fcaa4d4ad66aa67d6) | Collision hull/trace separation, platform and network layers | Selected `engine/common/pm_trace.c` header is GPLv3-or-later. Full tree/SDK dependencies require separate review; Half-Life files are not supplied by that grant. | Architecture reference. Replacing Godot physics/authority is not justified by a source port's existence. |
| Simpsons Hit & Run WASM | None verified | Linked repository currently 404; source/license unknown | Defer code/asset use. A running browser page would not resolve the missing source grant. |
| [FuncGodot](https://github.com/func-godot/func_godot_plugin/tree/352f3d3083f1fb9142cfaf1db07ca60a95aed9aa) — related tool | Pure-GDScript `.map`/`.vmf` parser, scene builder, entity definitions and convex/concave collision | MIT, copyright 2023 func-godot; preserve authors/license. No commercial WAD/texture/map rights implied. | Stage separately under ignored tooling; test one original brush module in Godot 4.6.3 before runtime adoption. |
| [TrenchBroom](https://github.com/TrenchBroom/TrenchBroom/tree/ebb2746523f6339f52609655a18d3db66085bcb1) — related editor | Original brush-map and entity authoring | GPLv3 editor; bundled components have separate notices. Editor code and authored map output are different artifacts. | Offline authoring candidate; keep original map/texture provenance, versioned import and collision acceptance. |

## Selected source inspection and counterexamples

At the pinned Vice City client, `public/sw.js` lines 38–44 dispatch OPFS requests
by pathname and GET/HEAD. Its same-origin check is only in the separate app
revalidation branch at lines 51–56. An adaptation must scope its own namespace
and origin explicitly rather than copying those GTA paths.

`parseRange` at lines 90–107 returns null for missing, malformed and unsatisfiable
ranges. `serveFromOPFS` at lines 109–139 then sends a full 200 response when null
is returned. Valid ranges produce 206 and a file slice; HEAD produces headers
without a body; storage lookup errors produce 404. A new server/probe must
separate absent range from malformed/unsatisfiable range, reject unsupported
multi-ranges deliberately, bound integer parsing and test empty files, suffix
ranges, EOF, HEAD, encoded paths and foreign origins. These are source-derived
observations, not tests run by this researcher.

The tiny OPFS helper retries a transient `NoModificationAllowedError` every
100 ms through attempt 30. All other errors propagate. Its deletion helper
swallows every failure, which should not become a false successful deletion in
our UI. Save-transfer code also demonstrates size checks and write/readback;
its proprietary save format is not adopted.

FTE's step-slide path compares direct sliding with an attempted raised route,
checks support normals/solid starts and preserves a bounded ground decision.
This provides concrete behavior questions for an original Godot contact test.
It is not proof of a current YUGA bug or license-free permission to copy C code.

## Evidence, checks and handoff

I used Exa for **50 search-result slots across five distinct searches**, then
read primary sources through the GitHub connector and direct public HTTP.
Slots include off-topic/duplicate results; only linked primary files support
the dispositions. No third-party marketing benchmark is accepted as measured.

The JSON retains the complete factual 75-entry catalog, full pins, file scope,
scratch locations and SHA-256 values. Key license hashes: browser-client MIT
`459ff921a82861efe0ee0737d37371fd491ea3cce62ce32b982994ad02d9a2d7`;
FuncGodot MIT `8172da66df06d8e5f16880ea89acd7dc71b0b16ba8343fda7732ace6641c2df5`.

Executed checks: strict JSON extraction of all 75 records, metadata/pin/tree
retrieval, actual selected-file/license reads, source line inspection, and
catalog count/hash validation. Unrun: target games, multiplayer sessions,
commercial data loading, engine compilation, browser-client execution and the
isolated FuncGodot spike. This research does not change production acceptance
counts, art quality or authority status.

Next owners: root/build engineer implements the credited own-asset probe and
held-out error cases; a later authoring worker qualifies FuncGodot on original
map input. The researcher now prioritizes the supplied ultimate-ability video
on the user's latest steering. No whole-game reverse engineering is claimed.
