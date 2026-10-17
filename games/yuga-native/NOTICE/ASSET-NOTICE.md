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

The Confluence duel adds a separately authored Ravana Sentinel costume on that
same CC0 anatomy and rig, two film-specific skeletal animation libraries, original
timeline effects, camera direction and captions. Its 24-second soundtrack and ten
cue files are deterministic mathematical synthesis. No commercial game models,
motion capture or recordings are used in this film. Exact resource hashes and
source records are in `CONFLUENCE-DUEL-PROVENANCE.json`; the generation sources
are under `art/cinematics/` and `tools/cinematics/` in the repository. Film animation
does not replace the existing playable Rama clips.

The separate experimental `tps_rama_motion_library.tres` adapts licensed Godot
TPS Demo motion. It has not replaced the active hero's nine original clips.
Its CC-BY 3.0 attribution, exact source revision and changes are recorded in
`TPS-MOTION-NOTICE.txt`; the complete upstream notice is preserved in
`GODOT-TPS-UPSTREAM-LICENSE.md`. Distributing this library requires retaining
those notices even while the runtime does not select its clips.

Godot 4.6.3 is distributed under the MIT license, with its dependency notices
preserved in `GODOT-LICENSE.txt` and `GODOT-COPYRIGHT.txt`.
