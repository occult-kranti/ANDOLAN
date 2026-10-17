# Independent skin shading diagnosis

The reviewed R2 raw frame shows broad triangular cheek and neck patches, plus
fine scalp stippling. These are visible defects. Their cause is not yet isolated.
The source asset remains unchanged; this review performs no import or rendering.

Raw frame actually viewed:
`/workspace/scratch/visual-campaign-candidate-r2/character-temple-three-quarter-baseline.png`.
This is the current runtime hero under the existing portrait light; “baseline”
in that capture refers to the optional temple-wisp comparison, not the original
release or absence of the current surface finish.

## Measured evidence

- The extracted skin normal PNG is byte-identical to its embedded GLB image.
  It is 512 × 512 RGB: R 123–132, G 122–133, B 255. Its GLB normal scale is 0.24.
  An XY-scaled unit-normal estimate gives 0.275° median, 0.381° p95 and 0.652°
  maximum perturbation. These are texture calculations, not GPU measurements.
- Both affected skin domains pass the existing source-matched Mikk diagnosis:
  Face mesh 1 / primitive 0 has 10,756 triangles; body mesh 2 / primitive 11 has
  85,152. Both have **zero** geometry/UV degeneracies, unresolved Mikk corners or
  corner-direction conflicts. The broader whole-hero tangent refusal therefore
  does **not** diagnose the skin patches.
- The skin texture import has no Y inversion and uses lossless mode 0. The GLB
  importer ensures tangents and permits mesh compression. Imported GPU arrays
  have not been independently inspected in this task.
- Current `rama_surface_finish.gd` changes roughness, specular and subtle SSS;
  it retains skin normals, albedo, UVs and geometry. The existing portrait light
  is unshadowed. The primary sun uses shadow bias 0.025, normal bias 0.35,
  four directional splits over 70 m, and a low day angle of −26°.

The nearly flat micro-normal map makes a large normal-texture defect a weaker
explanation. Self-shadowing / a shadow terminator is a credible leading
hypothesis given the triangular patches and scalp stippling. SSAO, imported
array compression and source surface geometry remain competing explanations.
The separate reuse worker also measured smooth source normals; that worker's
report owns those calculations. No causal explanation is marked confirmed here.

## Reversible A/B probe for the render owner

Use an **isolated copied project**, the same frozen pose, camera, resolution and
light values as the raw R2 close-up. Capture these variants one at a time and
restore the exact previous property before the next variant:

1. **A:** current baseline.
2. **B:** only `normal_enabled = false` on the unique `Rama warm skin`
   `StandardMaterial3D` instances. Keep every other material/property unchanged.
3. **C:** restore skin normals; only `SettingSun.shadow_enabled = false`.
4. **D:** restore sun shadows; only `Environment.ssao_enabled = false`.
5. Repeat A and verify byte-identical pose/camera/material property snapshots.

If C removes the triangles while B does not, prioritize a bounded shadow-bias /
shadow-terminator correction and verify ground contact at both gameplay and
portrait distances. If B removes them, inspect actual imported tangent frames
before changing source normals. If neither changes the pattern, test a separate
scratch import with mesh compression disabled, and compare the source mesh's
surface geometry. That additional import is outside this read-only diagnosis
and has not run.

Do not permanently disable hero shadows or normal maps as a presumed fix.
Do not modify the accepted mesh, bake arbitrary tangents, or introduce a new
skin shader before the one-factor captures identify the responsible path.

`inspect_skin_normal.py` reproduces `inspection.json` with NumPy and Pillow;
the report pins every source read. The exact execution command and viewed frame
hash are in `receipt.json`. No canonical runtime edits were made by this review.
