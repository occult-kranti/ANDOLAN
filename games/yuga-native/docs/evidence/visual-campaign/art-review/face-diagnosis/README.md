# Side-face shading: bounded source inspection

The R2 raw `character-temple-three-quarter-baseline.png` visibly contains broad
triangular shading patches across temple, cheek and neck. This diagnostic does
**not** establish their cause. It rules out a few easy but unsupported claims
before an artist changes geometry.

`source-check.json` pins the unchanged near GLB
`de61dc4c470920eab6f3265bc5467da7f9fb33d6fae2129a9353e7ca6d24d3f5`.
The two PNGs here are exact embedded payload extractions, with no conversion or
retouching. Both were individually viewed, together with the current runtime
`assets/materials/rama-finish/skin-roughness.png`.

- Both skin primitives have near-unit authored normals. Among 34,860 triangles
  whose three rest-space vertices all have `y > 1.48 m`, none has three equal
  corner normals within `1e-5` Euclidean vector distance. This is not a blanket
  flat-shaded mesh.
- Within each primitive, exact duplicate-position groups above that rest-space
  height have identical normals. This check does not measure posed shading or
  replace the separate facial boundary validator.
- `COLOR_0` RGB is white for both skin primitives. The orbital face partition
  has alpha zero and the remaining skin has alpha one; no claim is made that
  vertex RGB triangle tinting caused the visible patches.
- The exact embedded albedo and normal maps show fine generic repeating grain,
  not authored cheek, temple, eyelid or lip planes. The new runtime roughness
  map likewise adds fine grain. This is a visible authoring limitation, not
  proof that any one texture produces the observed broad facets.
- The finish owner changes roughness, specular response and subsurface settings
  while preserving the underlying albedo, normal map and geometry. This source
  fact does not by itself rule out a lighting/material interaction.

Computation: the existing `art/hero-rama-face/validate_face.py` sparse-capable
accessor reader decoded `POSITION`, `NORMAL`, `TANGENT`, `COLOR_0` and triangle
indices. For each skin primitive, select triangles with all three vertex
heights above 1.48 m; compare each corner normal with the first; group vertices
by the exact position tuple; measure normal spreads inside those groups. Raw
minimum/maximum values and channel facts are retained in `source-check.json`.
No engine, Blender, mesh repair, re-export or runtime edit was performed.

A controlled actual-engine view with only sun shadows disabled, only skin
normals disabled, and only SSAO disabled is requested by the moderator. Until
those pixels are inspected, root cause and a repair remain **OPEN**. Do not
replace these observations with a speculative smoothing or triangle-count fix.

Follow-up: the completed [controlled ablation review](../FACE_ABLATION_REVIEW.md)
now isolates the visible patches to the sun-shadow path in that fixed view.
The earlier source-only observations above remain scoped as recorded; a
shadow-on correction still needs separate acceptance.
