# Optional cloth review binding

`cloth_candidate.gd` is a fixture-only Node. No game scene or controller loads it
by default. It adapts the separately attributed open-art candidate onto the
existing `rama_secondary_cloth.gdshader` instances owned by
`scripts/rama_secondary_motion.gd`. It never replaces their shader or material.

```gdscript
const ClothReview = preload("res://art/open-art-wave/integration/cloth_candidate.gd")
var review = ClothReview.new()
fixture.add_child(review)
# Call after secondary motion and all three review LODs are configured.
var material = load("res://art/open-art-wave/materials/indigo-woven-cloth.tres")
assert(review.bind(player.visual, material))
var receipt: Dictionary = review.report()
# Capture the controlled comparison, then roll back explicitly.
var rollback: Dictionary = review.unbind()
```

`bind(visual: Node3D, candidate: StandardMaterial3D = null) -> bool` validates a
live tree node, the complete stored candidate settings and every target before
its first write. A null candidate loads the agreed resource at bind time. Only
the exact name `Cobalt handwoven silk · bounded secondary` with the exact
preloaded cloth shader is eligible. A source StandardMaterial with the original
name is refused because secondary motion has not taken ownership. An unknown
shader carrying a target name refuses the whole operation. Brocade, gold, hair,
skin and face surfaces are excluded.

The binder collects unique material instance IDs, so a ShaderMaterial shared
between three LOD surfaces is updated once. Distinct owned LOD materials are
handled once each. Fifteen surface uniforms carry albedo/color, roughness and
metallic maps/scalars/channels, normals and specular. The semantic alpha mask,
mesh arrays, skins, bones, morphs, animations, LOD state and `secondary_offset`
are never written. The secondary motion component can keep updating its offset
throughout review.

`report() -> Dictionary` includes `bound`, `unique_materials`, `surface_slots`,
`material_ids`, `touched_fields`, `candidate_path`, `candidate_sha256`, filter
conversion, the last reason and the last rollback. The source digest covers the
loaded material file; the separate artist build manifest owns texture hashes.
The fixed shader uses repeating linear mipmap samplers. A candidate anisotropic
sampler is accepted as an explicitly reported conversion; other unsupported
settings or effects are refused rather than silently discarded.

Repeated binding with equivalent mapped fields to the same live visual is a
no-op. A different visual/candidate, foreign uniform change, withdrawn owner slot
or replaced shader refuses re-entry. `unbind() -> Dictionary` restores an owned
uniform only if its value still matches what this binder wrote. It leaves a
foreign write intact and reports its material ID/uniform under `conflicts`.
Withdrawn slots and replaced shaders are listed under `invalidated_materials`
without stale-material writes. Each still-owned field rolls back independently;
an externally edited field can therefore remain beside restored fields. A
second unbind is a no-op. Visual tree exit and component exit both disconnect
the visual callback and attempt the same guarded rollback.

Run synthetic material/lifecycle counterexamples without importing the new art:

```sh
godot --headless --path games/yuga-native \
  --script res://tests/open_cloth_material_cases.gd -- \
  --report=/tmp/open-cloth-material-cases.json
```

After the artist source is frozen and the serialized editor import has finished,
add `--candidate-resource` to execute the actual resource/digest case. Synthetic
tests use real ShaderMaterials and secondary-motion code but do not establish
the actual hero's appearance. They do not repair the hero's degenerate UVs,
prove historical silk authenticity, qualify real-time rendering or promote the
candidate into the game. Matched rendered evidence owns the visual decision.
