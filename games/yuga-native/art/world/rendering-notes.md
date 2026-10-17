# Confluence world rendering candidate

This is an original lighting and water implementation for the native map review scene. It does not reproduce commercial assets, establish final competitive visibility, or measure GPU performance. The current renderer is Godot 4.6.3 Forward+; cloud captures use CPU software Vulkan.

## Integration contract

`scripts/world_lighting.gd` extends `RefCounted`. Either keep an instance and call `configure(environment, sun, world, manifest.lights)` once, then `set_phase(value)`, or use its static `configure_practicals(world, lights)` and `apply(environment, sun, world, value, shadows)` entry points. **Phase 0 is warm daytime; phase 1 is blue nighttime.** It is a blend parameter, not a circular clock. Clamp or interpolate scene settings before calling; the controller also clamps finite values and falls back to daytime for non-finite input. `diagnostics()` reports the configured resource budget. The scene can forward its `set_review_phase(value)` to this implementation for captures.

Applying a phase changes existing sky, environment, sun, fill and practical light properties. It does not recreate the sky or append lights. Reconfiguring the practical-light list replaces only the controller-owned `WorldPracticals` children. The supplied sun remains owned by the scene.

`manifest.lights` entries use `id`, `position:[x,y,z]`, `color:[r,g,b]`, `energy`, `day_energy`, `night_energy`, `range`, and optional `priority`. Higher priority is selected first, then lexical ID for ties. The first 12 valid fixtures become actual point lights. Other authored lantern/diya meshes remain emissive scenery. This fixed selection is a review-scene budget; it is not a camera-dependent light allocator. Missing color defaults to warm amber. Colors, energies and ranges are bounded; malformed, non-finite or extreme positions are excluded.

`water_material("coast" | "swamp", reduced_motion=false)` returns a shader material. Use horizontal planes or upper surfaces at the manifest's authored water elevation. Coast is brighter turquoise with broader moving highlights; swamp is greener, rougher and slower. Reduced motion sets animation speed to zero. Unknown styles use coast. Do not call this factory every frame: retain one material per style or surface as appropriate.

## Art and cost decisions

| Element | Implemented choice | Reason and remaining check |
| --- | --- | --- |
| Directional lighting | One shadowed sun/moon source plus one low-energy unshadowed blue fill | Keeps silhouettes legible without point-shadow atlas work. The scene must not add extra competing suns. |
| Directional shadows | Four blended splits; maximum camera distance 72 m; bias 0.035, normal bias 0.8 | Reduces shadow coverage cost. Bias is a starting value: inspect actual wall edges, feet and raised ornament for acne and detached shadows. |
| Practicals | Maximum 12 unshadowed omni lights; radius at most 8 m; energy at most 3 | Warm pools support lantern/diya identity. Real fixtures and emissive meshes must align; geometry can occlude less than real point lighting because these lights intentionally have no shadows. |
| Day/night | Ivory-gold direct daylight; cool readable nighttime; ambient energy 0.32–0.34 | Night is presentation, not a vision advantage. Actual hero/background color separation still needs gameplay review. |
| Atmosphere | Low-density ordinary fog; no volumetric fog | Provides distance separation without hiding nearby routes or invoking expensive volume effects. |
| Post processing | Subtle Forward+ glow and SSAO; no SSR, SSIL or SDFGI | Emissive highlights stay bounded; this is a conservative scene configuration, not a benchmark result. |
| Water | Opaque dielectric, no transparency, refraction, scene/depth reads or vertex displacement | Avoids sorting and visual/physics mismatch. The result does not simulate a swimmable volume or physically displaced waves. |
| Waves | Three analytic world-space components; derivative attenuation of finest component | Adjacent surfaces share wave coordinates; distant fine normals are reduced. Actual motion and temporal aliasing remain visual checks. |

The water preserves imported side-face normals and changes only mostly upward-facing surfaces. It is adapted from this repository's original `shaders/production_water.gdshader`, with new color/roughness parameters and attenuation of distant detail. No third-party shader or texture was copied. Static ocean and swamp levels do not alter collision or authority movement.

The shader uses Godot's `TIME`; the engine's time rollover can cause a small wave-phase reset in an exceptionally long running session. The current match target is much shorter. A future persistent world should supply a wrapped phase pair or synchronized bounded clock, then test pause/resume and very long sessions.

## Source review

The documentation website returned HTTP 403 from this environment. The official Godot documentation repository was accessible; the following files were read and independently re-fetched at **`godotengine/godot-docs@b10b7ed373c2d15555186914b82e167169b5b87b`** (4.6 branch), with matching SHA-256 bytes:

| Source | SHA-256 | Decision supported |
| --- | --- | --- |
| [Environment and post processing](https://github.com/godotengine/godot-docs/blob/b10b7ed373c2d15555186914b82e167169b5b87b/tutorials/3d/environment_and_post_processing.rst) | `dcc799b9ed5cc222134ad12827e0a0e89285bf86876a0f2c651f30ef5733f86c` | Constant ambient color can preserve visibility in shadows; fog and tonemapping need scene-specific review. |
| [Lights and shadows](https://github.com/godotengine/godot-docs/blob/b10b7ed373c2d15555186914b82e167169b5b87b/tutorials/3d/lights_and_shadows.rst) | `0250d2db8150223ef284d6e8ba049bc8f154358ea874f94813975a80857ba392` | Too little bias causes acne; too much separates shadows from objects. Omni shadow maps require additional passes. |
| [Spatial shader reference](https://github.com/godotengine/godot-docs/blob/b10b7ed373c2d15555186914b82e167169b5b87b/tutorials/shaders/shader_reference/spatial_shader.rst) | `cceceb2b29683254372bf8afa207f2ba0d9b89b05b035fade51af92162d8153e` | Fragment normals are in view space; reading or writing alpha invokes the transparent pipeline. |

These are engineering references, not evidence of commercial game reverse engineering or permission to reuse commercial content.

## Validation and open review

`tests/world_lighting_cases.gd` currently passes **30 assertions** under Godot 4.6.3: resource reuse through five blend phases, repeat configuration without accumulation, deterministic light selection, 12-light limit, bounded range, disabled practical shadows, requested sun-shadow setting, valid day/night ambient values, phase clamping, non-finite/extreme position rejection, distinct water styles and reduced motion. The fill light uses light-only sky mode so it does not create a second sun disc. Run:

```sh
godot --headless --path games/yuga-native --script res://tests/world_lighting_cases.gd -- --report=/tmp/world-lighting-cases.json
```

The committed report is `tests/evidence/world-map/lighting-cases.json`, including source and test hashes. A failed assertion or failed requested report write produces a nonzero exit. These tests validate configuration and input handling; they do **not** compile the shader in a real renderer, establish visual quality, or establish frame rate. Integrated day/night captures, swampland/shore visibility, character silhouette checks and directional-shadow contact are the next review evidence.

## Round 2: paving and wet-ground revision

The first actual scene images (`build/world-review-r1/08-player-scale.png`, `05-reed-court.png` and `01-city-overview.png`) showed intersecting lane ribbons as distracting triangular patches and long bright lines. The swamp looked like a flat green rectangle. Those observations are specific to the saved R1 images; the source changed during that first capture, so it is a visual baseline rather than an accepted frozen-source bundle.

The R2 implementation replaces the ground material with `scripts/world_ground.gdshader`. Its shared include, `scripts/world_ground_common.gdshaderinc`, accepts at most eight lane segments and twenty rotation segments as `vec4(x1,z1,x2,z2)` arrays, with explicit `lane_count` and `rotation_count`. The scene passes exact manifest polylines to both the floor and swamp materials. At this revision there are seven lane segments and eighteen rotation segments. The surface uses a union of route distance fields, so intersections do not require overlapping planes. Avenue stones are slightly larger and darker; grout is narrow and fades at small screen scale; macro variation stays low contrast. Arrival courts have two quiet concentric stone/brass inlays centered on the existing spawn positions. Geometry and authority collision remain unchanged.

For shallow wet-ground planes, set `swamp_overlay=true`, `overlay_size=Vector2(width,depth)` and `overlay_center=Vector2(world_x,world_z)`. A softly irregular elliptical mask blends pool color, normal, roughness and specular response back to the exact shared paving function at the plane edges. A dry strip along cross-mid stays visually legible. This uses the opaque pipeline throughout and does not move vertices, create depth or enable swimming. Coast leaves `swamp_overlay=false` and does not evaluate the paving branch. Source maps and counts must be bound consistently or the shallow-water border can differ from its underlying floor.

The material evaluations have fixed upper bounds of 28 segment-distance tests per visible ground fragment and per visible shallow-water fragment. There are no texture reads, depth reads, alpha sorting, time-dependent paving, or added physics bodies. This is an implementation budget, not a measured frame-time result. Actual R2 renderer compilation, appearance and source-freeze checks are performed by the integration capture, separately from the headless resource tests.
