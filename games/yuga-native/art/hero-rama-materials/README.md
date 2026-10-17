# Rama native-PBR calibration candidate

This optional quality-slice component retains Godot's `StandardMaterial3D`. It does not add a skin shader, screen-space scattering, a corneal shell, refraction or lights. The currently released GLB already has correctly exported roughness textures, normal strengths and metallic values. A shader replacement would add compatibility and maintenance cost without correcting the main face/hair/texture-art limitations.

**Promotion status: UNRUN for matched actual appearance.** The component is not wired into the playable hero. Root owns promotion after the frozen candidate is rendered before/after under identical conditions. Passing resource checks does not establish improved appearance or commercial quality.

## Narrow calibration

| Exact source material | Candidate change | Reason and limit |
| --- | --- | --- |
| Rama warm skin | Specular 0.50 → 0.42 | Forward+ maps this to normal-incidence dielectric reflectance 4.00% → 2.8224%. The Filament material table lists skin around 2.8%; this is a calibration lead, not a measured value for the authored complexion. Skin albedo, roughness texture and normal strength are preserved. |
| Natural lips | Specular 0.50 → 0.42; roughness 0.56 → 0.50 | Keep the same dielectric family while testing a slightly smoother lip surface. The roughness choice is authored and requires visual review. |
| Warm sclera | Specular 0.50 → 0.395; roughness 0.23 → 0.20 | Approximately 2.4964% reflectance, guided by the table's 2.5% eye entry. The lower roughness is an art candidate, not a sourced measurement. No claim of a physically layered cornea. |
| Deep brown iris | Specular 0.50 → 0.395; roughness 0.27 → 0.22 | Preserve original iris color and geometry. The current single-surface eye limits the result. |
| Polished sapphire | Metallic 0.26 → 0.00; specular 0.50 → 0.68 | Test a dielectric colored stone rather than a partial conductor. Reflectance is 7.3984%, consistent with an approximate IOR of 1.75. The medallion is still opaque: this does not simulate gemstone transmission or dispersion. |
| Recessed antique gold | Metallic 0.80 → 0.90 | Small authored shift toward conductor response. Roughness, albedo and all existing detail remain. Its mixed/aged surface is not a measurement of pure gold. |

The ordinary cloth, brocade, worked-gold trim and hair materials are **untouched**, because the secondary-motion owner converts those four materials using their semantic vertex-alpha mask. White vertex RGB and alpha motion weights remain unchanged. The main worked-gold surface is therefore not included in this calibration's claim.

Godot Forward+ uses `F0 = 0.16 * specular * specular` for a dielectric. The frequently quoted linear expression would give the wrong values here. The exact pinned engine source and Filament table are recorded under M04/M05 in [the shared source ledger](../../docs/research/rama-quality-sources.json); [selected excerpts](../../docs/evidence/rama-quality/planning/source-excerpts.json) retain the read ranges. Godot generally recommends retaining the default specular value; these narrow departures are candidates to compare, not a blanket change to every object.

## Integration contract

`res://scripts/rama_surface_materials.gd` exposes:

- `configure(visual: Node3D) -> bool`: discover exact named surfaces, shallow-duplicate their native materials per instance, then apply all changes atomically. Repeated calls for the same configured visual return true without allocating again. A configured component refuses another visual until restored.
- `restore_materials()`: restore the exact previous per-surface overrides only where this component still owns the active override. A later external override wins. Freed meshes are safe.
- `diagnostics()`: profile version, configured status and bounded owned-material counts. This contains no performance or art-quality assertion.

Attach one component as a child of the hero visual. The root integration owner may call it before or after secondary-motion configuration because their material domains are disjoint. A global mesh material override deliberately wins and is skipped. Unknown or shader materials are retained. A nonfinite matching source rejects the complete transaction before any mesh is changed. Exiting the tree restores owned overrides.

Imported meshes/materials, textures, animation, skeleton, skin weights, UVs, vertex colors, light budget and mesh LODs are never edited. Material duplication is shallow: image textures retain their original identity. Skin roughness is intentionally unchanged: its imported multiplier is already 1 over an authored texture, so increasing that multiplier cannot represent a useful calibrated correction within its 0–1 range.

## Verification and visual gate

Run from repository root:

```sh
taskset -c 0,1 godot --headless --single-threaded-scene \
  --path games/yuga-native --script res://tests/rama_material_cases.gd \
  -- --report=/absolute/fresh/material-cases.json
```

The current suite passes **38/38** checks for profile setup, map/channel/UV/normal/render preservation, secondary-mask byte preservation, per-hero isolation, 100 idempotent calls, 100 configure/restore cycles, invalid-source rejection, external overrides and freed-mesh cleanup. The first rejected run caught a real cleanup API typo; that report/log are preserved. Its synthetic color-mask assertion also incorrectly assumed 0.5 survives ArrayMesh color packing exactly; the corrected check compares before/after packed bytes.

For acceptance, freeze one exact imported art candidate and lighting configuration. Toggle only this material component. Capture the same close-up and gameplay pose at day, dusk and night, plus an active ability with identical camera/FOV/exposure/output size. Review actual full-size images for skin highlight clipping, eye readability, metal/plastic appearance, texture/normal seams, black crush and ability contrast. Title, training and world must each be checked. Pin source hashes and import freshness. A historical differently lit studio render is a baseline finding, not a controlled before/after pair.

The hero remains below the target while geometry, hair, facial performance, textile art, secondary motion, full-match readability and physical-GPU performance are incomplete.
