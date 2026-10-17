# Published Triad relay and siege preview

17 October 2026. [Public prerelease](https://github.com/occult-kranti/ANDOLAN/releases/tag/yuga-traversal-armies-2026-10-17-triad-siege), source **`ae33db4520bd14fe7b38aed173b764de7a7424d5`**. This archive records verification after publication; later documentation commits do not change the tagged game.

## Public bytes and CI

Both [foundation](https://github.com/occult-kranti/ANDOLAN/actions/runs/39016682299) and [prerelease](https://github.com/occult-kranti/ANDOLAN/actions/runs/39016682252) workflows succeeded on that exact source. An independent worker downloaded all **77 assets**, checked the remote tag/inventory and every digest/length, verified **233 tagged runtime source files**, and checked both ZIPs and all **232 PCK entries** per platform. `public-verification.json`, `verification-summary.json`, the downloaded manifests/checksums and `workflow-verification.json` retain the results. The verifier and local/public comparison script are retained for inspection; their original scratch paths describe this run. The retained `public-release-SHA256SUMS.txt` describes the 77 public release assets, not this smaller evidence folder. Its released `archive-manifest.json` is retained here as `public-release-archive-manifest.json`; this folder's own `archive-manifest.json` separately covers the local review evidence. Run release verification against the complete downloaded release directory, not this evidence subset.

The published relay reports pass **42 rules**, **30 art/geometry**, **38 actual-world integration** and **106 Triad publication-fixture** cases. These reports are source-pinned; the complete workflows include their other required gates. The three six-second relay, siege and traversal movies were freshly decoded and their source identities checked against the exact tag. This verifies recorded media and provenance, not full-video aesthetic acceptance or a new CI render.

Linux ZIP SHA-256: `434d633455e8f28e81984058d51a81eb9a39d24cbc6c0c63be3a04bf61dee5d2`.

Windows ZIP SHA-256: `60fc793031b96575f5d8e71be0516d95e7805b32f44a6d290532de853f0ab5c9`.

Public PCK SHA-256: `ae13333325687dab76ded075ad521eb162390237c6d76ad1326b29edff03b6cf` (26,113,004 bytes).

## Exact downloaded Linux window

Root ran the safely extracted public engine/PCK in an actual **960 × 600 X11 window**, Godot 4.6.3 Forward+ on llvmpipe, with isolated settings and Dummy audio. OS XTest keyboard/mouse events drove the game without injecting simulation state. `public-linux-input-review.json` records the executable/PCK identities, event order/times and all 14 screenshot hashes; its PCK matches the independent public verification. Root inspected every retained image.

| Frames | Observed result |
| --- | --- |
| 01–02 | Startup evidence only: **01 is the Godot splash**, despite its `01-title` filename; **02 is the title**, despite its `02-pause-lotus-focus` filename. These early captures preceded completion of rendered transitions and do not prove focused menu state. |
| 03 | The recorded Explore, Escape/three Tabs/Return sequence reaches the Lotus approach: 7 m from centre, 12/12 arrows, correct forward-facing zone. No separate focused Lotus-menu screenshot is claimed. |
| 04–05 | W enters the capture zone. Actual firing reduces arrows to 10/12; capture progresses from 6% to 70%. |
| 06–07 | Lotus becomes Sun-owned; the station changes to the Sun symbol. Frame 07, named `supply`, still shows 10 arrows and is not the supply confirmation. |
| 08–09 | The fitting pause menu and subsequent resumed view show **12/12 arrows** while Lotus remains Sun-owned. No reload event occurred: supply restored the two missing arrows to the cap. |
| 10 | F5 restores ordinary Wave 1 at Surya arrival court, all three relays Open, 12 arrows and both cores at 100. |
| 11–12 | Escape → Tab visibly focuses Siege practice; Return opens the drill, showing two cannons, two chariots and two enemy siege units. Relays explicitly become inactive. |
| 13–14 | Pause → mouse Return to courtyard restores the title. |

The log contains no engine/script errors or warnings. The helper then stopped its own processes; cleanup exit −15 is expected. This is a bounded public-package repeat. The broader local help/overview/pause review remains in [triad-window-r2](../triad-window-r2/REVIEW.md). Wall-clock event spacing in software rendering is not a measurement of simulation cadence or consumer frame rate.

## Source equivalence and remaining work

Compared with the local `f87de495` package, the public `ae33db45` export has the same **233 runtime source records** and **232 resource paths**. **223 payloads are identical; nine generated scenes differ** (three exported scenes and six imported GLB scenes). All 27 compiled scripts, 27 script remaps, 47 imported textures, 23 audio resources and 76 import descriptors are identical. The public PCK is 16 bytes smaller. `local-public-package-comparison.json` retains exact differences; it does not decode changed scene internals or establish binary/visual equivalence.

Godot's compiled/remapped script bytes match the CI export and package inventories, and the original source inventory matches the tag. This is not an independent source-to-bytecode rebuild. The independent download report correctly says execution was false **at that verification stage**; the subsequent input record above supplies the separate Linux execution evidence.

The build remains offline practice with prototype hero/world art. Native online matches, hero health/death, full roster and production balance remain open. Neutral inlay contrast, distinct station silhouettes, Moon/contested close views, crowded warning readability, hand grip/contact and continuous animation quality remain art tasks. Dummy audio/silent clips do not establish listening quality; Windows is archive/resource-validated but unexecuted, and llvmpipe does not establish physical-GPU performance. No commercial game reconstruction, imported TF2 assets or Deadlock/Overwatch visual parity is claimed.
