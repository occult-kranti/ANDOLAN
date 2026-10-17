# Rama lighting calibration packet

The runtime owners are `scripts/production_lighting.gd` (courtyard/title) and
`scripts/world_lighting.gd` (Confluence). This packet changes those existing
resources and lights; it adds no scene, mesh, shader, practical or shadow caster.

## Three rounds

1. **Contract/source inspection.** Reviewed the actual package-r3 title and
   Confluence-entry PNGs in `docs/evidence/rama-hero/window/960x600-r3/` and the
   left Rama in `games/yuga/art/references/rama-hanuman-sita.png`. The title face
   is dim; the world is broadly tan/flat. Source inspection found a concrete
   bug: the general lantern loop overwrote the existing `HeroPortraitFill`
   with orange lantern colour/energy/range. These observations do not establish
   the final art quality or a numerical image-quality score.
2. **Implementation/counterexample.** Keep neutral ambient visibility, give the
   form a warm key and restrained cool fill, reduce nearby fog/glow, reduce
   shadow offsets for a contact review, and distinguish the portrait light
   from lanterns. A new headless resource suite passes 108/108; the existing
   world suite passes 30/30. Running the new suite against the old scripts in
   an isolated project fails 60/108 checks. The exact light overwrite is a
   functional regression; other new limits are art-direction contracts, not
   perceptual proof.
3. **Independent review.** QA inspected the resource-test scope and requires
   actual same-camera/exposure final-art A/B. That rendered gate is **pending**.
   Do not mark this packet visually accepted from the headless result.

## Fixed budgets and APIs

Both existing public `apply` signatures, `configure`, `set_phase`, practical
sorting/cap (12), water materials and shadow settings remain available. Exposure
stays 1.0, Filmic white stays 1.0, and no auto exposure is introduced. There is
one shadowed directional key and one unshadowed directional fill per scene.
The courtyard's fill now uses `SKY_MODE_LIGHT_ONLY` like Confluence, avoiding a
second visible sun. Existing scene-owned portrait fill is calibrated separately;
it still hides during training through the scene's existing control.

| Property | Courtyard day → night | Confluence day → night |
| --- | --- | --- |
| Ambient energy | 0.30 → 0.32 | 0.30 → 0.32 |
| Key energy | 1.35 → 0.50 | 1.25 → 0.48 |
| Unshadowed fill energy | 0.24 → 0.20 | 0.22 → 0.24 |
| Fog density | 0.0013 → 0.0016 | 0.0008 → 0.0013 |
| Directional shadow distance | 70 m | 72 m |
| Shadow bias / normal bias | 0.025 / 0.35 | 0.025 / 0.35 |
| Glow intensity / bloom / threshold | 0.16 / 0 / 1.6 | 0.16 / 0 / 1.6 |

These are Godot resource values, not measured lux, radiance or performance.
Volumetric fog, SDFGI, SSIL and SSR stay disabled. Point lights cast no shadows.
The old source snapshots beside this file are immutable A/B inputs, not another
runtime lighting implementation.

## Required same-camera capture

Root owns serialized heavy captures after final hero/secondary-motion imports.
Use the **same final GLB, textures, camera, pose, resolution, exposure and scene
time** for before/after. Freeze the actual scene between stills. Do not compare
the old published mesh against a new mesh and attribute all changes to lighting.

- Title and close frontal/three-quarter face: skin, eye whites/irises, dark hair,
  blue sash and gold must remain distinct without a bright floor obscuring them.
- Confluence fixed gameplay and low hero view at phase 0, 0.5 and 1: compare
  material separation, ground contact, alley silhouettes and far-depth haze.
- A real Piercing Dawn/Guardian release: confirm warning/effect contrast at the
  same phases. A still does not establish continuous motion or human readability.
- Inspect tight normal-bias changes for acne, leaking and detached feet. Revert
  only the bias adjustment if it worsens those; do not hide contact defects with
  stronger ambient or bloom.

For the actual Confluence scene, `set_review_phase(phase)` fixes the public
phase. Its `lighting` controller holds the environment/sun/world used by
`WorldLighting.apply`. For the courtyard, use `world_environment.environment`,
`sun`, `world` and the existing title camera. A baseline script can be loaded
from the saved text into a `GDScript` resource and invoked on those same
resources; do not swap the canonical files or mutate the shared project during
another worker's capture. Record before/after script hashes and image hashes.

## Official properties actually read

The research desk read Godot source documentation at pinned commit
`89cea143987d564363e15d207438530651d943ac`:

- [Environment.xml](https://raw.githubusercontent.com/godotengine/godot/89cea143987d564363e15d207438530651d943ac/doc/classes/Environment.xml): explicit ambient colour/energy is controlled by sky contribution; sky reflection is separate. Filmic's white/exposure guidance is not a final artistic preset. The existing white/exposure is retained to isolate this comparison.
- [DirectionalLight3D.xml](https://raw.githubusercontent.com/godotengine/godot/89cea143987d564363e15d207438530651d943ac/doc/classes/DirectionalLight3D.xml): `LIGHT_ONLY` lights scene objects without appearing in sky shaders; shadow distance trades coverage for detail.
- [Light3D.xml](https://raw.githubusercontent.com/godotengine/godot/89cea143987d564363e15d207438530651d943ac/doc/classes/Light3D.xml): bias trades acne against detached shadows; normal bias offsets along normals. A lower numeric bias alone is not evidence of improved contact.

No commercial game assets, videos, measured GPU traces or new downloaded art
were used in this lighting packet.

## Rendered finding and targeted ground correction

The first actual matched capture caught radial floor bands after the lower
shadow bias. The source-pinned eight-image isolation probe in
`docs/evidence/rama-quality/lookdev/floor-artifact/probe-r1/` confirms floor
self-shadow acne: disabling only ground casting removes the bands while the
ground continues receiving hero/building shadows. This is independent of its
unchanged textures, materials and geometry.

`ground_shadow_policy.gd` now disables casting only for the five exact courtyard
floor/foundation paths and two exact Confluence ground paths. World-space bounds
reject raised or small lookalikes. It changes no material, transform, visibility,
collision or other caster. Courtyard applies on settings; Confluence applies
once in `configure`, never in per-phase updates. The candidate bias, lighting
budgets and all existing settings remain unchanged.

All 108 previous checks remain; 38 new counterexamples and actual-scene checks
bring the clean component run to **146/146**, with the existing world suite
**30/30**. `docs/evidence/rama-quality/lookdev/ground-fix-r3/` preserves those
source-pinned results and an explicitly rejected test-teardown candidate.
Root's corrected-source R2 rendering and gameplay review remain pending.

The initial property/probe shutdown emitted an ObjectDB warning from a stopped
music WAV/playback awaiting Dummy mixer retirement. Preserve that warning in
historical capture claims. The current 146-case fixture explicitly retires audio
before quitting and has a verbose zero-warning rerun in
`docs/evidence/rama-quality/lookdev/harness-cleanup-r3/`. The editable floor probe
uses the same bounded shutdown, but was only parse-checked after this harness
change; its existing eight images were not rerendered.
