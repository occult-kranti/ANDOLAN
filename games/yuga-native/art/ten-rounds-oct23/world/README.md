# One wind court: geometry and material evidence

The geometry pilot replaces only `sun-lift-west`. The playable source enables
its base, engaged piers and stepped crown, with 36 explicit collision boxes
replacing the old full-box collider. Other seven courts, original roof signals,
anchors, routes and the map manifest are preserved.

- [R4 geometry evidence](r4/INDEX.json): 16 actual matched day/night views and
  65 passing capture checks. The exact original capture/world/helper sources
  are retained; later source integration does not relabel those staged views.
- [Optional PBR evidence](pbr-r1/INDEX.json): six actual matched images, 31
  capture checks and 19 headless checks. Existing CC0 sandstone maps provide
  the material direction. The game's canonical material remains unchanged.
- [Reproduction and integration](../../../tools/wind-court-pilot/README.md):
  geometry budgets, collider ownership, callback holds and qualified renderer.
- [Independent review](../../../docs/research/ten-rounds-oct23/review/README.md):
  original-image inspection, counterexamples and source identities.

These are software-rendered component views. Sparse lateral samples do not
qualify continuous input, LOD transitions, temporal aliasing, hardware frame
times or the full map's commercial-quality target. No game completion packet
is awarded by this art study.
