# Four-round licensed character import study

The official Godot TPS demo character is a usable, explicitly licensed **reference asset**. It has been downloaded unchanged, inspected, imported in a separate Godot 4.6.3 project and sampled structurally. It has not replaced a YUGA hero, been retargeted to Rama, or received visual acceptance. It is an original open demo asset—not a character recovered from Deadlock or Overwatch.

Source pin: [`godotengine/tps-demo@a82f15448e9b015440d3bbdf5e10801b260c4e9f`](https://github.com/godotengine/tps-demo/tree/a82f15448e9b015440d3bbdf5e10801b260c4e9f). Reusable source context: [REUSABLE_GAME_SYSTEMS.md](REUSABLE_GAME_SYSTEMS.md) and [reusable-game-sources.json](reusable-game-sources.json).

## Round 1 — choose a model with explicit reuse terms

Selected [`player/model/player.glb`](https://github.com/godotengine/tps-demo/blob/a82f15448e9b015440d3bbdf5e10801b260c4e9f/player/model/player.glb). The [pinned license](https://github.com/godotengine/tps-demo/blob/a82f15448e9b015440d3bbdf5e10801b260c4e9f/LICENSE.md) explicitly assigns all assets to CC BY 3.0, with Juan Linietsky and Fernando Miguel Calabró credited. Code has separate MIT terms. The upstream GameTextures.com derivative-material notice is preserved; the project-level asset statement is not converted into a claim that separately obtained GameTextures source materials are available under the same terms.

The file is 23,844,032 bytes, within the requested per-model 25 MB limit. Its four maps, two material resources and original import settings bring the model/material bundle to **30,499,084 bytes**. Adding selected license/context/code-study files yields **30,547,446 bytes**. No whole-repository clone, music or unrelated level assets were downloaded.

Result: selected model reuse is supported with attribution and retained notices. This does not establish ownership or reuse permission for commercial game assets.

## Round 2 — pin and inspect the source

Model SHA-256: `16b783ec2e19245d034326d401796b9bd2635de75f4e38917854316abeee4f9c`.

The downloaded bytes also match the pinned Git blob `d4cfd9ac472f1a9798f6daa1ad0e78b6c75a5575`. Every selected texture, material, import file and study source has its own size, SHA-256 and source path in [source-manifest.json](../../art/reference-models/godot-tps-player/source-manifest.json).

The GLB contains one skin with 145 joints, five meshes, two material definitions and 56 authored animation entries. It has no embedded images; four separately fetched source maps supply albedo, normal, ORM and emission. This distinction prevents the untextured GLB alone from being presented as the complete material setup.

A separate research agent independently matched the model size, SHA-256, Git blob and source inventory. The [raw inspection](../../art/reference-models/godot-tps-player/source-glb-inspection.json) preserves the animation names rather than converting the inventory into a count of polished abilities.

## Round 3 — import and challenge the result

Only the model/material/texture data entered `/workspace/tooling/reference-character/godot`. The upstream gameplay scripts and full player scene were not run. YUGA’s native project, renderer and protocol-2 server were not changed.

Two concrete integration issues were retained and addressed:

1. The first material load resolved four textures by their text paths but warned that original texture UIDs were missing. Fetching the four pinned `.png.import` files restored that metadata.
2. A fresh reproducibility check exposed a duplicate-name error: both `Cannon_Charge` and `Cannon_Charge-cycle` normalized to `Cannon_Charge`. The isolated import setting `nodes/use_name_suffixes=false` retains their distinct authored names. The GLB remains byte-identical; eighteen loop flags remain present. Any future reuse of the upstream AnimationTree must explicitly reconcile its clip aliases.

The [final import log](../../art/reference-models/godot-tps-player/godot-import.log) and [inspection log](../../art/reference-models/godot-tps-player/godot-structural-inspection.log) contain no warnings or errors. Earlier logs are retained alongside them. A second project with no prior Godot import cache reproduced the same counts with zero warnings/errors; its separate import and inspection logs are retained.

| Structural check | Result |
|---|---:|
| Imported skeletons / bones | 1 / 145 |
| Imported mesh instances | 5 |
| Source material definitions / resolved texture maps | 2 / 4 |
| Imported animation resources, including helpers | 56 |
| Names explicitly containing `-noexp` | 27 |
| Sampled bone transforms | 24,360 |
| Non-finite or singular sampled transforms | 0 |
| Rendered frames / applied retargets | 0 / 0 |

Samples were taken at 0%, 50% and 99% of each imported animation. This proves finite transforms at those sample points, not full interpolation, contact, attachment quality or polished animation. The [inspection JSON](../../art/reference-models/godot-tps-player/godot-structural-inspection.json) records all clip durations, track counts, loop modes, skeleton parents and resolved materials.

The [candidate retarget map](../../art/reference-models/godot-tps-player/yuga-retarget-candidates.json) identifies 21 explicitly **unapplied** semantic candidates between this 145-bone robot and YUGA’s 164-bone Rama rig. Only three names match exactly: `root`, `foot.L`, `foot.R`. Root semantics, spine/neck segmentation, twist bones, mechanical controls, four-digit robot hands, five-digit human hands and weapon attachments differ. Name matching is insufficient; no rotations or animation curves were transferred.

## Round 4 — decide what to reuse

The useful near-term transfer is the animation and attachment architecture, with the licensed model available for isolated comparison. Its science-fiction robot silhouette does not satisfy the requested Rama art direction by itself.

| Pinned source pattern | Concrete YUGA adaptation | Acceptance still needed |
|---|---|---|
| [`player.tscn` additive aim filter](https://github.com/godotengine/tps-demo/blob/a82f15448e9b015440d3bbdf5e10801b260c4e9f/player/player.tscn#L70) separates aim from lower-body motion. | Build a dedicated upper-body bow-aim layer over locomotion. | Bow grip requires two-hand constraints; the demo’s neck/right-arm filter is not a suitable direct copy. |
| [`player.tscn` strafe and walk blend spaces](https://github.com/godotengine/tps-demo/blob/a82f15448e9b015440d3bbdf5e10801b260c4e9f/player/player.tscn#L150) distinguish four directions plus idle, and speed versus weapon posture. | Author direction-specific movement while keeping aim orientation stable. | Rama needs compatible strafe/aim clips, diagonal blend inspection and foot-contact checks. |
| [`player.gd` root-motion extraction](https://github.com/godotengine/tps-demo/blob/a82f15448e9b015440d3bbdf5e10801b260c4e9f/player/player.gd#L128) converts animation displacement to velocity, then clears accumulated translation. | Study motion-matched stride presentation and explicit root-displacement ownership. | Keep existing authoritative movement limits; do not let copied animation displacement replace protocol-2 authority. |
| [`player.tscn` weapon attachment and marker](https://github.com/godotengine/tps-demo/blob/a82f15448e9b015440d3bbdf5e10801b260c4e9f/player/player.tscn#L543) ties projectile origin to a bone-mounted marker. | Use an authored bow emission socket and hand/string contact targets. | Verify actual projectile origin and camera-ray convergence across all aim poses. |
| [`player_input.gd` pitch bounds and short-press aim toggle](https://github.com/godotengine/tps-demo/blob/a82f15448e9b015440d3bbdf5e10801b260c4e9f/player/player_input.gd#L5) expose bounded camera and hold/toggle behavior. | Offer explicit hold/toggle aiming and bounded camera pitch. | Accessibility and focus/pause input tests; do not silently change existing bindings. |
| [`player.gd` local presentation versus server input application](https://github.com/godotengine/tps-demo/blob/a82f15448e9b015440d3bbdf5e10801b260c4e9f/player/player.gd#L47) separates visual state from combat spawning. | Preserve that boundary when integrating richer presentation. | The demo RPC/input protocol is not ported. Client aim claims, cooldowns and authority validation remain YUGA’s responsibility. |

The initial study selection contains 18 named idle/run/walk/aim/strafe/jump candidates. It intentionally excludes `-noexp` helper entries. Selection is a research queue, not visual approval.

The next gate is a controlled two-clip experiment: establish rest-axis and scale compensation for one locomotion clip and one aim pose, define explicit aliases, retain loop boundaries, then render foot contact, bow grip and shoulder behavior on YUGA’s rig. Until that gate passes, the imported robot remains a reference and Rama’s original animation curves remain unchanged.

## Reproduce

From the ANDOLAN root, with Godot 4.6.3 available:

```sh
python3 games/yuga-native/art/reference-models/godot-tps-player/reproduce_reference.py \
  --destination /workspace/tooling/reference-character
```

The command checks pinned downloads, creates the isolated project, applies the documented import-only adjustment, runs a two-worker headless import and executes the original structural inspector. Use another absolute destination for an independent fresh workspace. `--download-only` skips execution. Runtime assets are not copied into YUGA; the research folder is excluded by `.gdignore` and export filters.

The [four-round summary](../../art/reference-models/godot-tps-player/review-summary.json) ties these results to source and evidence hashes. There is no rendered-quality, retargeting, full-game reconstruction or multiplayer-security claim in this study.
