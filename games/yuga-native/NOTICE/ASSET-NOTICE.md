# Native asset provenance

The courtyard geometry and generated PBR textures are original YUGA assets,
dedicated to CC0 1.0 by their authoring record in `art/README.md`. Its scene
metadata records the actual file hash and build parameters. It contains no
Deadlock or Overwatch meshes, maps, textures or audio.

Rama is the existing YUGA model, reused unchanged from
`games/yuga/client/assets/heroes/rama.glb`. Its anatomical mesh, rig and weights
derive from MakeHuman CC0 data. Costume, hair, weapon and motion were authored
for YUGA. `HERO-PROVENANCE.json` identifies the source revision and exact model
hash; `MAKEHUMAN-ASSET-LICENSE.md` preserves the source data license.

The runtime generates its own brief interface and combat sounds. No sampled
commercial game audio is included.

Godot 4.6.3 is distributed under the MIT license, with its dependency notices
preserved in `GODOT-LICENSE.txt` and `GODOT-COPYRIGHT.txt`.
