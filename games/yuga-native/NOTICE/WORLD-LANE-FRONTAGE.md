# Confluence lane frontage

`scripts/world_lane_frontage.gd` and `assets/world/block2-frontage.json`
contain original YUGA code and geometry for the single building
`CityArt/block-2`. The authoring source is
[`art/world-finish/lane-frontage-r2`](../art/world-finish/lane-frontage-r2/).
No external game model, texture, animation or sound is included in this addition.
Existing architecture materials and their provenance remain unchanged.

The design uses broad floor bands, pilasters, recessed window bays and a closed
two-leaf entrance. It is an original stylized building, not a reconstruction of
a particular historical site. The runtime selects the 4,824-triangle near mesh;
the separate mid mesh does not establish automatic runtime LOD selection.

Exact mesh data SHA-256:
`67950a68d7b6384b8b114987a27efff1f113d44f8fb1b7df8632f3e9217406a2`.

The [source receipt](../art/world-finish/lane-frontage-r2/receipt.json),
[matched actual views](../docs/evidence/desktop-finish/world-lane-frontage/W1-actual-r2/receipt.json),
[production integration](../docs/evidence/desktop-finish/world-lane-frontage/W4-production-r1/receipt.json)
and [package checks](../docs/evidence/desktop-finish/world-lane-frontage/W6-package-r1/receipt.json)
record their own exact sources and scope. Acceptance covers this building's
form and closed collision. Repetitive city layout, material finish, lighting,
temporal rendering and whole-map visual quality remain separate work.
