# Lotus Gate — Surya arrival-court art packet

Original staged art for the **existing Rama/Confluence slice**, not a second map
or a claim that the world already has production art. Source baseline:
`1ab1f5e330d256a6ffb6a5706a07f2ff8c3bbb0e`.

The target is a coherent arrival view: a broad, load-bearing pale stone arch,
carved lotus capitals, recessed teal panels, deliberately sparse cast-bronze
edges, and two human-scale oil lamps. Large forms carry the view; there are no
painted masonry grids or dense glittering trim. The open centre preserves the
hero/reticle background, with subtle flush lead-in lines. No gameplay changes,
new collision or runtime lights are hidden in the asset.

The generator authors real closed relief, fluted shafts, rounded mouldings,
curved load-bearing arch/soffit, curved roof profiles and hollow lamp basins.
Stone and bronze use six original seeded analytic PBR maps; all other surfaces
are constant dielectric/metal values. Meshes are grouped by module and material.

## Proposed integration contract

Place the kit at Godot `[0,0,-90]`, yaw 0, near the existing spawn `[0,0,-112]`.
This is a proposal for root to compare with the actual three lane envelopes,
army, sight lines and collisions before promotion. Units are metres, +Y up.
`LotusGate`, `Threshold`, `DiyaLeft`, `DiyaRight` are independent modules.
The gate has a clear 18.1m opening, 4.8m spring height and 10.25m arch apex.
Pier centres are x±10.7, depth 3m. The arch is intentionally clear at hero height.

The provisional collision boxes in `manifest.json` cover only structural piers.
The overhead arch needs an agreed collider before accessible integration; the
lamps may require moving to the arrival-court edges. Root owns collision/map
integration. Threshold lines sit at y≈.009 and must not become physical steps.
The asset exports zero lights: warm flame geometry is only emissive. Any pooled
practical lighting must fit the existing lighting owner's separate budget.

## Budget and production gate

- ≤110,000 assembled triangles, five opaque PBR materials.
- Six 1024² source textures, embedded exported PNGs; no external runtime images.
- Zero skins, animation players, physics nodes, camera or embedded lights.
- No downloaded/commercial model, copied sculpture or photogrammetry.

Actual totals and exact hashes belong in `manifest.json` and `validation.json`,
not a guessed performance claim. This is one staged district feature pack; it
does not fix the entire map. Physical-GPU 12-player performance remains unrun.

Acquire the shared Blender/import/render slot before:

```sh
blender --background --python games/yuga-native/art/quality-arrival-court/build_arrival_court.py
python3 games/yuga-native/art/quality-arrival-court/validate_arrival_court.py
```

The editable `.blend` and exported `.glb` are created in this directory. Actual
native acceptance must compare the old and new spawn view at identical camera,
FOV, exposure, phase and resolution. Include side view, normal gameplay camera,
day/night, hero/minion/Guardian effects together, and route/collision checks.
An independent reviewer must inspect the actual images before promotion.
Until then this packet is **staged / actual visual gate UNRUN**.

## Provenance and reading boundary

Used the retained [native source library](../production/SOURCE_LIBRARY.md), its
exact immutable [source index](../production/source-index.json), and the
[Lanka/coastal study](../../../yuga/docs/LANKA_COAST_RESEARCH.md). That research
read selected Griffith *Ramayana* Book V gate/court passages and Fergusson's
broad entrance/portico mass descriptions. This pass read those retained notes,
not the whole books or unavailable Reddit artwork. The original Sangam City
concept board and actual released Confluence entry screenshot were viewed.
The resulting geometry is invented fantasy architecture; it does not reconstruct
historical Lanka or copy an existing temple facade.

New generated geometry/textures: **CC0-1.0**. The generator follows repository
code terms. No external mesh, texture, photograph, audio or executable is used.
