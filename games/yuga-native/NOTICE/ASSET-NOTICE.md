# Native asset provenance

The courtyard geometry and generated PBR textures are original YUGA assets,
dedicated to CC0 1.0 by their authoring record in `art/README.md`. Its scene
metadata records the actual file hash and build parameters. It contains no
Deadlock or Overwatch meshes, maps, textures or audio.

The preserved baseline Rama is the existing YUGA model, reused unchanged from
`games/yuga/client/assets/heroes/rama.glb`. Its anatomical mesh, rig and weights
derive from MakeHuman CC0 data. Costume, hair, weapon and motion were authored
for YUGA. `HERO-PROVENANCE.json` identifies the source revision and exact model
hash; `MAKEHUMAN-ASSET-LICENSE.md` preserves the source data license.

The active `rama-production.glb` revision retains that anatomy, rig and nine
animation curves, with newly authored costume, hair, bow-grip detail and original
generated PBR textures. `RAMA-PRODUCTION-PROVENANCE.json` identifies its exact
generator, texture and model hashes. This is an incremental art revision; it is
not a finished sculpt or a claim of commercial-game visual parity. The generator
and structural validator are in `art/production/` in the source repository.

The runtime generates its own brief interface and combat sounds. No sampled
commercial game audio is included.

Godot 4.6.3 is distributed under the MIT license, with its dependency notices
preserved in `GODOT-LICENSE.txt` and `GODOT-COPYRIGHT.txt`.
