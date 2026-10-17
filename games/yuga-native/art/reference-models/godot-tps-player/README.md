# Licensed TPS character reference

This folder contains provenance, structural inspection evidence, a candidate bone map and a reproducible downloader for the official Godot TPS demo player. The original 23.84 MB GLB and its material bundle remain in the task-local inspection workspace; they are not installed as YUGA heroes. The parent `.gdignore` also excludes these research files from native resource import, and native export presets exclude `art/*`.

Source: [godotengine/tps-demo at a82f15448e9b015440d3bbdf5e10801b260c4e9f](https://github.com/godotengine/tps-demo/tree/a82f15448e9b015440d3bbdf5e10801b260c4e9f). Character: `player/model/player.glb`.

**Attribution:** Assets © 2018 Juan Linietsky and Fernando Miguel Calabró, [CC BY 3.0](https://creativecommons.org/licenses/by/3.0/). Code © 2018–2021 Juan Linietsky and Godot Engine contributors, MIT. Preserve the complete [upstream license](UPSTREAM-LICENSE.md), including its GameTextures.com derivative-material notice. No endorsement is implied. The original GLB and texture files are unchanged. Only the isolated Godot import setting described below is adjusted.

Reproduce from the ANDOLAN repository root with Godot 4.6.3 installed:

```sh
python3 games/yuga-native/art/reference-models/godot-tps-player/reproduce_reference.py \
  --destination /workspace/tooling/reference-character
```

Use a different absolute destination for an independent fresh run. `--download-only` performs hash-checked acquisition without import. The complete selected download is 30,547,446 bytes; the model alone is 23,844,032 bytes. The model/material/import bundle is 30,499,084 bytes, so the complete textured bundle is **larger than 25 MB**.

The tool downloads only pinned manifest files, checks SHA-256 and Git blob hashes, then prepares a separate project. Upstream gameplay scripts and the player scene are retained as study text and never executed. The only executed inspection script is the small original `inspect_reference.gd` included here.

A fresh Godot 4.6 import exposed a duplicate animation-name error: suffix normalization tried to map both `Cannon_Charge` and `Cannon_Charge-cycle` to one name. The isolated importer uses `nodes/use_name_suffixes=false` to retain distinct authored names. Eighteen source loop flags remain present. The source GLB is not modified. Four source texture `.import` files preserve their UIDs. The earlier error/warning logs remain available beside the clean final import and inspection logs.

Final structural result: one 145-bone skeleton, five meshes, two source materials, four resolved texture maps, 56 animation resources and 24,360 finite sampled bone transforms. **Twenty-seven animation names contain `-noexp`; these are inventory/helper entries, not 27 validated gameplay moves.** The review selects 18 named locomotion/aim/strafe/jump candidates for later evaluation.

`yuga-retarget-candidates.json` contains 21 **unapplied** semantic candidates for YUGA’s 164-bone rig. It performs no retargeting, skin changes, rest-axis compensation, IK or root-motion transfer. Only `root`, `foot.L` and `foot.R` have exact name overlap; matching names do not establish matching semantics.

The [full decision report](../../../docs/research/REFERENCE_CHARACTER_IMPORT.md) explains the four rounds, reusable design patterns and next acceptance gate. Headless import proves structural loading, not image quality, animation continuity or commercial-game parity.
