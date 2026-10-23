# Original diya concept: image-to-3D pipeline input

`input.png` is a new image generated in this task with the available image-generation tool. It depicts an original brass/cobalt diya with a lotus bowl and peacock-feather finial. The input is a 1024 × 1536 RGBA image with a real alpha channel, suitable for testing a service's documented alpha-aware preprocessing without a separate background-removal service.

This directory contains concept/reference material outside the runtime asset pipeline. `input.png` is the original 2D concept; `candidate.glb` is the subsequently generated textured mesh. Neither is a rig, an animation or evidence of finished hero/game graphics. The [manifest](manifest.json) binds the exact image; [the pipeline report](../../../docs/research/ps4-swarm-oct23/README.md) owns any subsequent GPU request and output status. The generated original in `/workspace/generated_images/` was preserved.

The prompt requested a single isolated standing brass diya, a compact lotus bowl, curved peacock-inspired finial, hammered/patinated metal, cobalt enamel, a restrained flame, readable sculpted forms and a transparent background. It supplied no third-party image, game model or private user material. Any later generated mesh requires its own model/code/output terms, geometry/PBR/LOD/collision checks and actual-engine review before promotion.

The candidate mesh imported into Blender and an isolated Godot project. Four actual static views under `inspection/` were reviewed. The generated flame remains solid geometry; scale, topology/LODs, collision, effect authoring and gameplay-distance polish remain open. See [the detailed intake](../../../docs/research/ps4-swarm-oct23/asset-pilot/README.md).
