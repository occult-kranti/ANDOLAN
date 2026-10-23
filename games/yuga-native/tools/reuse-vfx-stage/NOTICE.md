# Source and license mapping

This original project-local adapter does not assert a repository-wide license.
The copies in a scratch project retain their original source rights and are bound
by `source-manifest.json`, generated from the actual input bytes at assembly time.

| Reused source | Use | Rights/provenance |
| --- | --- | --- |
| `scripts/rama_ability_effects.gd` | Exact copied cast, ribbon and bounded contact-pool implementation | Existing original YUGA project code; no new license inferred |
| `shaders/rama_ribbon.gdshader` | Exact copied original effect shader; its explicit-clock/unshaded-alpha technique also informs the new small flame shader | Existing original YUGA project code |
| `shaders/rama_ability_calligraphy.gdshader` and `rama_ability_boundary.gdshader` | Exact copied shader dependencies | Existing original YUGA project code |
| `art/concepts/cloud-diya-pilot/candidate.glb` | Exact imported prop; draw-time material mask only | Original concept and official public TRELLIS.2 output; existing [pilot notice](../../NOTICE/CLOUD-DIYA-PILOT.md) and [source intake](../../docs/research/ps4-swarm-oct23/asset-pilot/README.md) remain authoritative; no new blanket clearance of model/dependency/output terms |
| `tools/run-traversal-capture.py` | Reuses the command/environment and owned-process cleanup pattern, not its gameplay capture | Existing original YUGA tool; inspected SHA-256 `abcf87a5919d919d38aade69b8996ebbd240acc340ff6091e2beceb0b38e3cb8` |
| `tools/setup-render-runtime.py` | Existing unmodified verified package installer | Existing original YUGA tool; inspected SHA-256 `5755aa20e2ada1e2379eb31b90881442a8dc9689191ff0cd3ad1b69d224cb5a4` |

The new flame profile, bounded material mask, staging adapter, checks and runner
are original project work. Godot 4.6.3 is separately installed MIT-licensed
software; Mesa/Xorg, FFmpeg and their dependencies retain their upstream/package
licenses. They are executed, not vendored into the game or relicensed here.
No Deadlock, Dota2, Overwatch or TF2 client mesh, texture, map, code or animation
is copied. This stage does not perform binary reverse engineering or model
inference, does not claim a physical GPU, and does not turn stills into purported
hero animation.
