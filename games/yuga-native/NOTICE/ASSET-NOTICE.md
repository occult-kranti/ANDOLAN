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

The retained `rama-production.glb` revision keeps that anatomy, rig and nine
animation curves, with newly authored costume, hair, bow-grip detail and original
generated PBR textures. `RAMA-PRODUCTION-PROVENANCE.json` identifies its exact
generator, texture and model hashes. This is an incremental art revision; it is
not a finished sculpt or a claim of commercial-game visual parity. The generator
and structural validator are in `art/production/` in the source repository.

The runtime generates its own brief interface and combat sounds. No sampled
commercial game audio is included.

The single Confluence lane-building replacement uses original YUGA geometry
and the existing architecture materials. Its editable source, exact data hash
and bounded review are recorded in [WORLD-LANE-FRONTAGE.md](WORLD-LANE-FRONTAGE.md).

The selected playable hero is `assets/heroes/rama-hero.glb`, whose exact runtime
identity and editable authoring chain are recorded in
`RAMA-HERO-PROVENANCE.json`. Source work under `art/hero-rama-quality/` adds
original hair clumps, cloth folds, brocade and semantic secondary-motion masks.
Candidate source is distinct from accepted runtime promotion.

The fifteen Rama action/counter WAVs in `assets/audio/rama-quality/` are original
deterministic oscillator and seeded-noise synthesis, with no external samples,
recordings or transcribed melodies. Their exact generator and file identities
are in the adjacent manifest and source `art/audio/rama-quality/`. The plucked,
modal and bell colors are abstractions, without historical-authenticity or
psychological-effect claims.

Facial authoring source under `art/hero-rama-face/` uses the two CC0 MakeHuman
standard face-pose data files at revision
`a8bc2d54ff0ac92e78ff71431b1023eda42bf482`. Attribution:
“(c) 2020 Data Collection AB, Joel Palmius, Jonas Hauquier. Standard face pose
units. Author: MakeHuman. License: CC0.” Its source ledger and NOTICE retain
upstream URLs and exact hashes. These are pose data; no MakeHuman application
code or commercial game character/animation is imported. Rejected facial
candidates are not an accepted runtime model.

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

The separate offline tangent authoring tool reuses unmodified MikkTSpace code;
see `MIKKTSPACE-AUTHORING.md` and the preserved upstream source notices. Adopting
this tool does not automatically replace or approve a runtime hero asset.

The separate `art/open-art-wave/` cloth candidate adapts three Microsoft CC0
technical-fabric maps from the pinned Khronos sample collection. Its source
metadata has separate CC-BY-4.0 terms; `OPEN-ART-WAVE.md` preserves attribution,
license distinctions and changes. This is a review material outside the selected
runtime hero, and does not establish historical silk authenticity.
