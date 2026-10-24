# Source and reuse notice

The new candidate contains existing original YUGA courtyard geometry and textures
from `assets/environment/lanka_courtyard.glb`, SHA-256
`1454e03627e9a7708557f64122cf8f170d0f8365256e69fa7689e94cd3585c33`.
The adjacent `lanka_courtyard.metadata.json` explicitly grants **CC0-1.0** for the
generated courtyard geometry and textures. Its generator/code uses repository
licensing. The source is an original fictional Lanka-inspired training courtyard,
not an archaeological reconstruction or commercial-game extraction.

`prepare.py` and `bake.gd` adapt the existing
`tools/map-reuse-placement/prepare.py`, `placement.gd` and `bake.gd` source-selection
and array-preservation process. `mount.gd` adapts the existing cached native scene
and private army-manifest contract in `scripts/lanka_lane_gate.gd`.
`capture.gd` extends the existing gate/wind-court matched-state capture helpers;
`capture.py` adapts the existing gate runner. Those scripts retain repository
licensing. No REA/commercial source, reverse-engineered client, leaked code or
commercial texture/model is copied by this packet.

The unchanged contextual nature source is `assets/world/nature.glb`, SHA-256
`856fc1ed86daf624611a5afaeaa4d27b6c370cc2d9ba2b6a4dcec3c282d4be7f`.
Its `art/world/nature-manifest.json` records original YUGA-authored geometry under
repository licensing; it is not relabelled CC0. The existing world water shader
and ground remain repository code. No new copy of the nature source is made.
