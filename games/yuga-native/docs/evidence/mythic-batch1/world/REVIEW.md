# Bounded world presentation review — FG05-T01

The corrected packet passes its bounded geometry, lighting and collision checks, and the ten captured views have been inspected. It adds original sparse ornaments and presentation adjustments to the current prototype. It does **not** establish a finished production map, commercial visual parity, native multiplayer or hardware performance.

## Build and method

- Capture: actual Godot 4.6.3 Forward+, X11/llvmpipe, 1280 × 720, MSAA2, Dummy audio; ten staged screenshots. No full-motion water/camera or audio listening acceptance.
- Exact final hero GLB: `3424d72e74bb425c7e6bb2ff2fddc05c792657c437a888c56671fbd7d3ec3bcc`.
- Capture report: [world-presentation-review.json](world-presentation-review.json), SHA256 `c739eff960b63144de5d89e9eb7aab2741f6a7d2342b8e65471d32437c27cc1d`; 243 source/file pins unchanged during capture; four imported GLBs pass source/destination checksum freshness checks.
- Command, from the repository root: `python3 /workspace/scratch/yuga-next/world/run-world-next.py --project /workspace/ANDOLAN/games/yuga-native --output /workspace/scratch/yuga-next/world/render-r2 --display 122`.
- The exact [runner](run-world-next.py) is the existing world helper adapted to call `tools/capture-world-next.gd` and consume this report. Its Xvfb, engine and isolated user settings were owned by the process; the Mesa cache was seeded from the earlier capture. The run exited cleanly; its archived log contains no script errors, engine errors or warnings.
- Source pins include the capture helper, all scripts, scenes, assets, shaders, project configuration and canonical world-map input. Root owns the final integration commit and top-level archive manifest.

## Changes actually present

Original batched geometry adds ten hanging lotus lamps and a seven-ray gate crest to the Lanka courtyard; the Confluence outskirts gain a seven-rib naga-inspired river loom, lamp boats and roof kite accents. These are invented motifs, not historical reconstructions. The river loom is offshore at (-88,0,-18), outside actor bounds and clear of the existing watchtower. The close detail camera is also outside playable bounds; this capture does not establish an accessible new route.

The courtyard adds three mesh/material batches and 1,692 triangles; Confluence adds six and 5,902. Both stay within the explicit six-mesh/18,000-triangle budgets. The new geometry has no physics bodies, collision shapes, added lights or shadow casting. Twelve thousand phase changes per district reuse geometry and material identities. Phase affects wick emission only.

Confluence dusk gains a warm horizon and directional tint. The directional normal bias is 0.55 instead of 0.8, with the same 72 m shadow distance; the existing twelve practical/two directional light budget remains. Paving has broad mineral variation. Courtyard water reduces high-frequency normal detail at subpixel scales, slows its cosmetic motion and raises roughness; no vertex displacement or water physics is added.

## Actual visual inspection

The implementation owner viewed all ten final PNGs. Root independently viewed 01, 04, 05, 08 and 10.

| Views | Observation |
| --- | --- |
| 01 courtyard dusk / 02 courtyard night | All five target silhouettes remain visible; the dawn crest stays above the aim corridor. Night preserves blue fill and warm practical accents. Final hero indigo is visibly less electric than the earlier material pass. |
| 03 gallery day / 04 gallery night | Corrected brass normals show the new lotus facets and directional highlights. Suspended lamps remain above training targets and walking space. Deep gallery recesses remain darker than the open court. |
| 05 courtyard coastal water | Water and original low-poly lotus/rock assets are visible after moving the camera off the gallery wall. **The original finite sea-plane cutoff is clearly visible from this outboard inspection camera and remains future visual work.** This is not a seamless coast acceptance. |
| 06 reed court day / 07 dusk / 08 night | The relocated river loom is clear of the watchtower. Dusk shifts toward muted warm rose; night retains route visibility. Wet-ground patches and vegetation remain sparse and visibly procedural. |
| 09 city dusk | Routes remain open and large world topology is visible. Repeated block architecture, empty expanses and unfinished distant edges remain obvious. |
| 10 river-loom detail | Seven separate curved patina ribs, brass tips and small suspended lamps render with corrected face normals. This is a staged scenery view, not an interaction or traversal demonstration. |

Remaining visual work includes grazing-angle courtyard floor aliasing, distant building simplification, the finite coastal plane, sparse wet-ground detail and broader encounter composition. The static capture cannot establish that temporal water shimmer has been eliminated. Actionable target/route visibility is bounded evidence, not human readability/balance testing.

## Executed checks

The final imported hero and corrected world source were present for these runs:

- [Presentation cases](world-presentation-cases.json): **32/32**, including geometry budgets, finite vertices, clockwise outward normals, watchtower separation, repeated phase/configuration safety and fourteen actual courtyard target/floor ray comparisons with decorations attached, detached and restored. All five actual targets remain hittable.
- [Lighting cases](world-lighting-cases.json): **30/30**, including practical count/range/shadow budget, ambient floor, phase limits, water settings and resource reuse.
- [World scene cases](world-scene-cases.json): **27/27**, including all lane/rotation capsule sweeps, actual floor and blocker rays, negative collision controls, landing decks, actor bounds and scene controls. Headless tests do not establish rendered art, online authority or hardware performance.

The headless commands are `godot --headless --path games/yuga-native --script res://tests/<suite>.gd -- --report=<new absolute report path>`. The exact final suites are `world_presentation_cases`, `world_lighting_cases` and `world_scene_cases`; source hashes and detailed assertions are inside each JSON. Logs are adjacent.

## Rejected evidence retained

[rejected-r1](rejected-r1/) preserves the first actual pass's report, two diagnostic images, exact hash-verified failed module/capture source, logs and the failing winding regression. Its new ornaments initially used mathematical counter-clockwise normals against Godot's clockwise front faces, and its river loom overlapped the watchtower. Both were repaired before this final capture. Earlier test-only parser and floor-only target-mask failures are retained separately; no assertion was weakened to hide a runtime defect. The other seven rejected raw PNGs remain in scratch, not in this selected archive.
