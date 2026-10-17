# Rama quality: bounded technical study and engineering handoff

17 October 2026. Role 15 research desk. Baseline inspected:
`1ab1f5e330d256a6ffb6a5706a07f2ff8c3bbb0e`. The goal is one accepted
production-quality Rama/arena slice, followed by the complete original
competitive game. [The quality target](../DEADLOCK_QUALITY_TARGET.md) defines
acceptance; [the squad plan](../PRODUCTION_SQUADS.md) assigns fifteen roles.

This pass answers current lighting, LOD/skinning and material questions. It is
not a claim to have read all game-design books, watched the reference games,
recovered a commercial client or produced Deadlock-level art. The
[source ledger](rama-quality-sources.json) records exact successful responses,
hashes, sections read, retrieval failures and the distinction between source
semantics, design inference and executed evidence. Selected exact passages are
retained under [planning evidence](../evidence/rama-quality/planning/).

## Stack decision

Retain **Godot 4.6.3 Forward+ / Blender 4.3.2 / glTF 2.0** and the existing
versioned gameplay/authority work. Current defects are content, material,
secondary-motion, perception and integration problems, not evidence of an
engine's inability to render the target. Change a component only after a matched
experiment identifies a specific limit, reproduces the advantage and accounts
for migration, licenses, tooling and platform support.

Godot already uses meshoptimizer for imported mesh LOD generation. Downloading a
second optimizer does not automatically improve the pipeline. Blender and the
existing validator/importer are sufficient for the current bounded candidate
experiments. An artist-controlled decimation tool can be useful when it
preserves the mesh/skin contract and its result passes actual deformation and
switching review. More triangles or a tool described as “SOTA” is not a quality
metric.

REA/Ghidra is an analysis toolchain, not an art generator or commercial asset
license. Its previously executed original-C fixture remains its bounded native
analysis evidence. This pass has no supplied Deadlock/Overwatch/Dota 2 binary,
model or replay to analyse. Existing source studies of open engines and permitted
demo assets may inform architecture/contact; they do not supply a finished
mythology hero. See [reuse decisions](RESEARCH_BRIEF.md#rea-reconstructed-games-and-reuse-decisions).

## Lighting: role 06 answer

Sources L01–L03 are official Godot documentation at immutable commit
`89cea143987d564363e15d207438530651d943ac`. The documentation pin is not asserted
to be the installed engine binary's exact build commit; actual API use must run
on the installed engine.

- `Environment.ambient_light_color` and `.ambient_light_energy` only contribute
  when `ambient_light_sky_contribution < 1`. At zero, explicit ambient supplies
  illumination; at one, the sky supplies it. Ambient diffuse and
  `reflected_light_source` specular are separate controls. Keep scene-reflection
  context when evaluating whether gold/eyes look convincing.
- `tonemap_exposure` changes input brightness. Filmic also multiplies incoming
  values by 2.0 in its documented normalization. `tonemap_white` controls the white
  reference: the official photorealistic recommendation is at least 6.0; higher
  values preserve highlights but can reduce contrast. That is guidance, not a
  requirement for YUGA's authored visual style. Compare actual images instead of
  changing white/exposure until a close-up conceals defects.
- `DirectionalLight3D.SKY_MODE_LIGHT_ONLY` means visible in scene lighting
  including GI, but invisible to sky shaders. It does not mean “no lighting” or
  “no reflections.” Confirm the actual sky/reflection setup separately.
- Increasing `directional_shadow_max_distance` extends coverage at the cost of
  overall shadow detail and rendering work. `Light3D.shadow_normal_bias` offsets
  lookup along surface normals; tune it with `shadow_bias`. Too little bias
  creates acne; too much separates caster and shadow. Compare shoes, face, cloth
  folds and jewelry at the actual camera before accepting the change.

Implementation experiment: capture identical neutral/day/night front and normal
gameplay views with source hashes and fixed camera/exposure. Review skin, gold,
cloth, face, contact shadows and effects together. The old project's art/UX
acceptance is the available readability gate; no fresh Riot clarity article,
wiki or game video was read here.

## Skin and LOD: role 11 answer

Sources S01–S06 are official Godot/glTF documentation.

1. **Bind semantics are part of the asset contract.** glTF `JOINTS_n` values index
   the corresponding `skin.joints` array, not arbitrary node IDs. Joint order
   must match inverse-bind-matrix order. The matrices must be finite; the
   hierarchy needs a common root. Preserve names, hierarchy, rest transforms,
   inverse binds, sockets and clip references when a candidate promises a
   geometry-only reduction.
2. **Four versus eight influences must be explicit.** glTF has paired VEC4
   `JOINTS_n`/`WEIGHTS_n` sets; extra sets permit more than four influences, but
   implementations may support only one set. Godot Mesh arrays require four or
   eight values per vertex according to `ARRAY_FLAG_USE_8_BONE_WEIGHTS`. Reject
   silent influence truncation, duplicate non-zero joint entries, negative or
   non-finite weights, out-of-range indices and materially wrong weight sums.
3. **Index LOD is not a new compact vertex/rig buffer.**
   `ArrayMesh.add_surface_from_arrays` LOD entries are alternate index arrays for
   a surface. Count actual vertex storage, skin attributes and bone evaluation
   separately from reduced drawn triangles. A separately compacted mesh can
   reduce storage but needs stronger topology/skin/material equivalence review.
4. **Generation does not imply correctness.** Godot's official mesh-LOD page
   explicitly warns that automatic generation can break skinned meshes.
   `ImporterMesh.generate_lods` accepts bone transforms to account for mesh/skin
   scale discrepancies. Validate results in difficult existing poses, not only
   the rest pose or a structural JSON check.
5. **Automatic selection is screen-space.** FOV and viewport resolution affect
   imported LOD choice. `lod_bias = 0` forces the lowest level, one is default and
   larger values retain higher detail farther away. Test all supported FOVs and
   displays, including close face, hand/string, cloth edge and shadow silhouette.
6. **Manual switching needs hysteresis or a reviewed fade.**
   `GeometryInstance3D.visibility_range_*_margin` is a hysteresis distance only
   when fade mode is disabled; with self/dependency fade it is a transition
   distance. Avoid claiming an index-LOD threshold is a manual distance switch.
   Oscillate the camera about each threshold and review both directions for
   flicker, gaps, double rendering, skin/clip resets and material changes.
7. **Shared instancing is not free independent culling.** The Godot guide notes
   that MultiMesh/particles choose LOD from the nearest point of their shared
   AABB; spatially distant groups may need separate nodes. Automatic instancing
   depends on shared meshes/materials and opaque or alpha-tested materials.
   Alpha blend can change rendering order/cost and must be measured.

Candidate counterexamples should deliberately reorder a bind, drop a weight
set, damage a tangent/normal/channel and force a bad threshold. The validator
must reject the promised-contract failure. Valid format still cannot certify
face quality, hand/string contact or an invisible mesh switch.

## Texture and PBR preservation: roles 02/03 answer

Sources M01–M04 include the glTF specification, Godot material/import docs and
Filament's authored PBR documentation.

- Base-color RGB is sRGB, alpha linear. Metallic/roughness maps are linear;
  glTF stores roughness in green and metallic in blue. Emissive texture RGB is
  sRGB. Do not apply a generic sRGB conversion to data channels or tint geometry
  with a vertex mask intended only for secondary motion.
- Preserve actual texture/factor multiplication, normals, normal strength,
  tangent handedness, channel selectors, UV transforms, sampler repeat/filter,
  alpha mode/cutoff, culling, emission and enabled extra material features.
  Godot requires both mesh normals and tangents for normal mapping; its normal
  map expects X+/Y+/Z+. Unsupported material features need an explicit guard or
  an actual equivalent implementation, not a silent shader conversion.
- Godot's official `BaseMaterial3D.metallic_specular` documentation recommends
  leaving 0.5 in most cases; arbitrary lowering is not a universally correct
  skin fix. Roughness controls highlight breadth, metallic controls the
  conductor/dielectric mixture and specular controls reflectance strength.
  They are not interchangeable sliders.
- **The actual Forward+ mapping is quadratic:** `F0 = 0.16 * specular²` for the
  dielectric portion, mixed with albedo for metallic. Thus 0.5 → 4%, 0.35 →
  1.96%, and 2.8% → approximately 0.4183. This corrects the queried assumption
  that 0.35 meant 2.8%. The exact function was read at lines 55–59 of
  `scene_forward_lights_inc.glsl` (M04). It is not a claim that every path in a
  different engine/build has that mapping.
- Filament's table, attributed there to *Real-Time Rendering* fourth edition,
  lists illustrative normal-incidence reflectance: eyes 2.5% / parameter 0.39,
  skin 2.8% / 0.42, hair 4.6% / 0.54. This pass read that table, not the cited
  book. The table does **not** provide an eye roughness value. Use it as a
  calibration lead with the actual stylized-blue-skin art direction; do not
  present selected numbers as measured Rama anatomy or approved final art.
- A new material is not subsurface scattering merely because it has softer
  light or lower specular. Godot has explicit subsurface enable/strength and
  renderer limitations. A fake-SSS claim requires correction; a real added
  feature needs dense-scene cost and actual appearance review.
- PNG/JPEG/GLB size is not GPU memory. Godot documents that Lossy texture import
  can reduce disk bytes without reducing VRAM versus Lossless. VRAM compression
  changes residency/bandwidth and can introduce artifacts. The official RGBA8
  example with mipmaps is approximately 5.33 MiB at 1024² uncompressed versus
  1.33 MiB for its illustrated compressed mode; actual format/platform matters.
  Sum dimensions × format/block cost over all mip levels, count duplicated
  imported textures and compare with actual runtime allocation. Do not multiply
  PNG bytes by hero count and call it measured VRAM.

The secondary-motion worker independently read the renderer's skinning/custom
vertex order and records it in its own `secondary/source-reading.json` evidence.
That is the worker's named source analysis, not a duplicate desk execution.
Custom offset/mask/material preservation still requires current imported-engine
comparison and lifecycle tests.

## Deadlock complexity, game design and lawful references

The retained [Rama design study](RAMA_HERO_DESIGN_STUDY.md) studied a pinned
SteamTracking data snapshot: 68 records and 41 complete candidate four-slot kits
after stated filtering. Flags do not independently prove live selectability;
the wiki request was blocked, no footage was watched and no commercial rigs were
recovered. This desk consulted that existing study rather than re-scraping it.

Apply its bounded design lesson: complexity comes from relationships among a
stable weapon/four-action vocabulary, spatial setup, movement commitment,
objects, resources and counter windows. Adding hidden modes or spectacle without
readable timing does not create mastery. Actual current Kodanda is timed
automatic release, not the study's proposed hold-to-charge mechanic. Keep source
proposal and implemented behavior distinct in instructions, UI and tests.

Selected Nystrom, Godot animation/interpolation and Filament scopes were already
read in the earlier study. The planned Swink, Fullerton, Schell, PBRT and
*Real-Time Rendering* books are not newly read by this task. No “all books” or
Reddit-wide comprehension claim is made. Read another source only to answer a
named unresolved implementation question and produce a useful experiment.

## Desk result and next owner

This pass produced the fifteen-role plan, quality gates, staged whole-game
delivery order and source-backed answers used by lighting, performance,
secondary-motion and materials workers. Twelve official documentation/specification
responses and three further renderer/PBR responses were retrieved successfully;
only the sections named in the ledger were read. A Blender 4.3 manual request
failed with `URLError`, remains unread and was not retried through another route.
No external executable/code/assets were adopted or executed in this study.

Root integrates the new documents into the existing roadmap/README and source
pin/evidence process. The desk must not mark the new art/motion/lookdev/LOD
candidate accepted before role 14 inspects the actual integrated output. Its next
checkpoint is a concise post-integration update with exact changed source,
reports, images, unresolved defects and next owner. Hardware, human review,
native-online and full-game gates remain open.
