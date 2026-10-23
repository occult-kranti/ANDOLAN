# Reuse the accepted Rama production base

This is a source-authoring intake and one **Arjuna authoring template**. It reuses current accepted Rama resources; it does not create a finished Arjuna, change the canonical roster, recolor fourteen copies, or promote the rejected generated source and skin-transfer experiments.

The shared Godot scene references the original `assets/heroes/rama-hero.glb`. It delegates setup to the existing motion, LOD, material, secondary-motion, finish and facial components in the same order as `scripts/player.gd`. The template keeps Rama's appearance deliberately. New face, silhouette, clothing, weapon and action work must pass separate review.

The accepted GLB has **164 bones and nine embedded legacy actions**. The **23 current runtime clips** are separately referenced from `assets/animations/rama_hero_motion.tres`. Blender does not import those 23 Godot clips from the GLB.

## Commands

Run from the repository root. Audit reads the current source files; creation requires a fresh directory.

```bash
python3 games/yuga-native/tools/hero-family-reuse/intake.py audit --output games/yuga-native/docs/research/hero-family-reuse-oct23/rama-family-manifest.json

python3 games/yuga-native/tools/hero-family-reuse/intake.py validate --manifest games/yuga-native/docs/research/hero-family-reuse-oct23/rama-family-manifest.json --hero arjuna --source games/yuga-native/assets/heroes/rama-hero.glb --weapon bow --motion draw

# Another isolated authoring setup, not a finished hero or raw model copy.
python3 games/yuga-native/tools/hero-family-reuse/intake.py create --manifest games/yuga-native/docs/research/hero-family-reuse-oct23/rama-family-manifest.json --hero arjuna --output /workspace/scratch/arjuna-authoring-template-new

python3 -m unittest discover -s games/yuga-native/tools/hero-family-reuse -p test_intake.py -v

timeout 45s godot --headless --path games/yuga-native --script tools/hero-family-reuse/probe_template.gd -- --output=/workspace/scratch/arjuna-template-probe-new.json
```

An alternate authored GLB must supply `--source-sha256`; its skeleton, rest, skin binding, material roles, mask, face and mesh contracts are still checked. A supplied hash identifies bytes; it does not approve their art, licensing, animation or gameplay. Unsupported weapon/anatomy/motion requests and unknown sockets fail explicitly. A finished-hero claim is always rejected by this intake.

## Editable pilot

The [pilot scene](../../docs/research/hero-family-reuse-oct23/pilot/arjuna-template.tscn) uses a real shared external GLB resource. `family_template.gd` performs no gameplay and never writes source assets. A failed setup is nonretryable: discard/reopen the authoring instance, preventing duplicate modifiers or material writers after a partial failure.

The [Blender pilot](../../docs/research/hero-family-reuse-oct23/pilot/arjuna-rig-authoring-template.blend) is a small **rig-only scaffold** with the accepted skeleton and nine unchanged embedded actions. It records the geometry source path/hash for verified **reimport**; it is not a live Blender mesh-library link. It contains no geometry or image copies. The 23 runtime clips, material roles, sockets and LOD constraints are recorded as external contracts. Use the shared Godot scene to inspect the unchanged complete donor. Reimport the pinned canonical GLB into a separate artist scene when editing source geometry; do not assume older `.blend` files match the current accepted GLB.

```bash
blender -b -t 1 --python-exit-code 1 --python games/yuga-native/tools/hero-family-reuse/build_armature_template.py -- --manifest games/yuga-native/docs/research/hero-family-reuse-oct23/rama-family-manifest.json --output /workspace/scratch/arjuna-rig-template-new.blend --report /workspace/scratch/arjuna-rig-template-new.json
```

See the [production handoff and next ten rounds](../../docs/research/hero-family-reuse-oct23/README.md). Existing asset provenance continues to apply. No commercial game character or proprietary asset is added by these tools.
