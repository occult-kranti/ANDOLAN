# Game-development agent skills: Hanuman adoption

## Source and scope

The user-suggested [awesome-gamedev-agent-skills repository](https://github.com/gamedev-skills/awesome-gamedev-agent-skills) exists. We inspected a shallow checkout at revision [`c6ca6c41c839b68319ffc08430b99ab768debc32`](https://github.com/gamedev-skills/awesome-gamedev-agent-skills/tree/c6ca6c41c839b68319ffc08430b99ab768debc32), accessed 25 November 2026. The checkout contains **79 `skills/**/SKILL.md` files plus one router**, and its README lists 12 engines. These counts are for this revision; they may change. The repository is [Apache-2.0](https://github.com/gamedev-skills/awesome-gamedev-agent-skills/blob/c6ca6c41c839b68319ffc08430b99ab768debc32/LICENSE); its [NOTICE](https://github.com/gamedev-skills/awesome-gamedev-agent-skills/blob/c6ca6c41c839b68319ffc08430b99ab768debc32/NOTICE) credits Abhishek Barali and contributors. The supplied post's attribution to Dr. Alvaro Cintas was not established by the inspected repository sources.

The local `yuga-hero-art` skill links to this intake; the pack was inspected and a specific checker was run, but its entire collection was **not** installed as project skills or executed automatically. No upstream source files were copied into this repository. If files are later redistributed or modified, preserve the upstream license, NOTICE and applicable change/attribution notices.

## Useful routing for this project

| Target | What to use | Boundary |
| --- | --- | --- |
| Hanuman's Blender model, visual target and material family | [`create-game-assets`](https://github.com/gamedev-skills/awesome-gamedev-agent-skills/blob/c6ca6c41c839b68319ffc08430b99ab768debc32/skills/disciplines/create-game-assets/SKILL.md) and its [3D pipeline](https://github.com/gamedev-skills/awesome-gamedev-agent-skills/blob/c6ca6c41c839b68319ffc08430b99ab768debc32/skills/disciplines/create-game-assets/references/three-d-pipeline.md) | Pin the source, target image and camera; inspect topology, normals, UVs, rig, weights, animations, scale, materials and actual engine import. An image alone does not prove a usable mesh. |
| Current Rust/Wasm game and PlayCanvas renderer | The router's [custom-engine fallback](https://github.com/gamedev-skills/awesome-gamedev-agent-skills/blob/c6ca6c41c839b68319ffc08430b99ab768debc32/router/references/custom-engines.md), plus actual project code and tests | The pack has Bevy and three.js skills but no dedicated PlayCanvas skill. Neither Bevy nor Godot APIs can be assumed to apply to this game. |
| Separate native Godot project | [`godot-animation`](https://github.com/gamedev-skills/awesome-gamedev-agent-skills/blob/c6ca6c41c839b68319ffc08430b99ab768debc32/skills/godot/godot-animation/SKILL.md) and [`godot-3d-essentials`](https://github.com/gamedev-skills/awesome-gamedev-agent-skills/blob/c6ca6c41c839b68319ffc08430b99ab768debc32/skills/godot/godot-3d-essentials/SKILL.md) where relevant | `games/yuga-native/project.godot` declares 4.6; those upstream examples target 4.7. Verify any API against the installed project version rather than upgrading implicitly. |

The router itself treats downloaded files as data, detects the target project before selecting engine guidance, and recommends loading a small relevant set. Its published evaluation results are the maintainers' claims; we did not independently reproduce their engine or routing evaluation.

## Applied check: existing Hanuman reference

We reviewed and executed the upstream [`asset_report.py`](https://github.com/gamedev-skills/awesome-gamedev-agent-skills/blob/c6ca6c41c839b68319ffc08430b99ab768debc32/skills/disciplines/create-game-assets/scripts/asset_report.py), SHA-256 `99f4b38f9c4fe036f97ab1d4effd7f6931b62d24a90330a5a2f5ae71e7d1a77c`, using Python 3.12.14 and Pillow 12.3.0. It reported that the existing studio beauty image is an RGB WebP of the specified **1280 × 800** pixels; alpha was not required for this opaque studio render. The image SHA-256 is `bf7fc440953a189e27fef87c2bfdbcf219bb86a1c2dc05f92a196ba0d192345a`. [Positive report](evidence/hanuman-beauty-report.json) · [Deliberately wrong 1 × 1 negative control](evidence/hanuman-negative-control.json) (exit 1).

Reproduce from the ANDOLAN root after checking out that exact upstream revision elsewhere:

```sh
python3 /path/to/awesome-gamedev-agent-skills/skills/disciplines/create-game-assets/scripts/asset_report.py \
  games/yuga-native/art/hanuman-hero-finish/media/images/hanuman-beauty.webp \
  --expect-size 1280x800 --json
```

This validates the reference image's dimensions, not the mesh, rig, artistic quality, new candidate or game performance. Continue with the [Hanuman handoff](../../../art/hanuman-hero-finish/HANDOFF.md), the [part-by-part anatomy skill](../../../../../.agents/skills/yuga-anatomy-review/SKILL.md) and the exact candidate's own checks.
