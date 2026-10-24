# Lanka lane gate — original CC0 source reuse

The native runtime asset `assets/world/lanka-lane-gate.scn` reuses selected original project-authored courtyard geometry and textures. The existing source declaration `assets/environment/lanka_courtyard.metadata.json` grants **CC0-1.0 to this generated courtyard geometry and textures**. Its authoring generator `art/build_courtyard.py` remains under the repository's code licence. No commercial game model, texture, animation or reverse-engineered art is included in this gate.

It is an invented Lanka-inspired coastal-court design, not a surveyed archaeological reconstruction. The source and native runtime scene use metres and +Y up. Source gate centre `(0,0,-24.8)` is gate-centred at bake and placed at `(-40,0,-54)` in Confluence. Original source UVs, normals, tangents, native material values and embedded image bytes remain unchanged.

| Item | SHA256 |
| --- | --- |
| Source `assets/environment/lanka_courtyard.glb` | `1454e03627e9a7708557f64122cf8f170d0f8365256e69fa7689e94cd3585c33` |
| Original selected-triangle receipt | `fe2a1374b91396ca88a67e7740a3e23753a2739ea3f5c720d024386e2561234c` |
| Qualified runtime `assets/world/lanka-lane-gate.scn` | `e895e0aaef172901e445aa1e782b7ecbfbdf6b021cf13f1c311db3c60cae7d25` |

The self-contained native scene is 3,793,793 bytes and contains 241 whole source pieces, 17,862 triangles, 11 mesh/material surfaces, 23,305 compacted vertices, six shared original materials and twelve 512×512 original image resources. It preserves 6,706 original structural collision triangles separately from renderer mesh compression. Ten source-component ground footprints serve only the offline army's conservative planar geometry through a private copy of the map manifest; the overhead arch is never a filled gate box. The original map and eight original authority/deck arrays are unchanged.

Preparation reuses the existing `tools/map-reuse-intake/map_loader.gd` native Godot GLTF loader. `tools/map-reuse-placement/prepare.py` selects complete connected source pieces without clipping source triangles; `bake.gd` writes standard native resources once. Gameplay uses `scripts/lanka_lane_gate.gd` and the scene above, with shared immutable mesh/material resources and separately owned collision bodies/shapes. It has no tool or scratch-path runtime dependency.

A fresh rebuild must preserve all source arrays, native material/image bytes and original collision/footprint metadata. Godot may assign different internal resource IDs, so whole-file byte reproducibility is not claimed; the exact qualified runtime scene hash is pinned separately. Source correspondence and physics checks do not establish hardware performance, a complete map, multiplayer or commercial visual parity.
