# Lanka courtyard: production atmosphere pass

This is original fantasy art direction. The generated Sangam City concept and
Rama/Hanuman/Sita reference are visual targets, not captured game frames. The
current native courtyard remains an early production study below those targets.

## Inspected evidence and priorities

Viewed `build/visual-initial/frame-3.png`, the generated
`games/yuga/art/production-concepts/sangam-city-direction.png`, and
`games/yuga/art/references/rama-hanuman-sita.png` before making changes. The initial
frame has weak value separation, very bright pale paving, repetitive thin brass
outlines, a large foreground motif, and little distinction between near and far
surfaces. Lighting can improve modelling and material separation; it cannot
replace hero topology, garment sculpting, richer architecture or good composition.

1. Warm side light must describe the gateway and hero against cooler recesses.
2. Stone, indigo inserts, sparse brass, and water must have distinct responses.
3. Distant silhouettes should recede without haze washing out the playable court.
4. Lamps should create small warm pools at dusk and become more visible at night.
5. Keep the clear aiming corridor; reduce repetitive paving and foreground motif
   dominance in a later authored geometry revision.

## Integration API

Preload `res://scripts/production_lighting.gd` and call:

```gdscript
ProductionLighting.apply(world_environment.environment, sun, world, night, shadows)
```

Call after the world lights exist and from the settings handler. This replaces the
old lighting assignment block in `_apply_settings`; retaining that block after
this call would overwrite the art direction. The function is idempotent, reuses
`CoolSkyFill`, and adjusts direct-child `OmniLight3D` lanterns already in the scene.
It owns lighting only and adds no collision or gameplay state.

Replace the shader used for `WATER_` meshes with
`res://shaders/production_water.gdshader`. The shader preserves the sparse joined
mesh geometry and uses world-space fragment normals for small animated ripples.
Its optional `animation_speed = 0` freezes animation for a still-art review.

## Parameter intent

| Setting | Initial dusk | New dusk | New night |
| --- | ---: | ---: | ---: |
| Ambient energy | 0.72 | 0.27 | 0.21 |
| Unshadowed fill energy | 0.45 | 0.10 | 0.06 |
| Directional key energy | 1.40 | 1.12 | 0.42 |
| Key pitch / yaw | -31 / -28° | -26 / -47° | -32 / -47° |
| Sky sun disc | 16° | 0.9° | 0.9° |
| Exposure | 1.1 | 1.0 | 1.0 |
| Glow intensity, Forward+ only | 0.65 | 0.28 | 0.28 |
| AO radius, Forward+ only | 1.4 m | 0.7 m | 0.7 m |
| Water metalness | 0.35 | 0.0 | 0.0 |

The water is an opaque dielectric approximation, not simulated fluid or refractive
water. It uses no screen/depth texture, tessellation, displacement, or particle
system. Dynamic GI, SSR, volumetric fog, and point-light shadows remain disabled.
Forward+ adds restrained AO and bloom; Compatibility keeps the same direct light,
ambient, procedural sky and shader, with those optional effects disabled.

## Acceptance and remaining work

Root integration must capture the same spawn camera and one oblique side view,
in dusk and night, and inspect them before calling this visually accepted. Check
that indigo recesses retain detail, hero limbs remain readable, warm light does
not clip the pale floor, water does not wobble like a flat board, target markers
remain distinguishable, and settings toggles do not accumulate fill lights.
Render checks must include Forward+ and Compatibility. Parse validation alone
does not prove rendered quality or shader compilation on both backends.

Godot 4.6.3 headless API check passed: apply dusk → night → dusk; toggle shadows;
assert the expected ambient/key/lantern energies; assert one fill light throughout;
load the water shader resource. The first check exposed an incorrect reflection
enum name, corrected to `Environment.REFLECTION_SOURCE_SKY` before the passing run.
The temporary check is `/tmp/yuga-world-art-check/check.gd`; rendered acceptance
remains pending integration and captures.

Geometry priorities from the art director remain: soften paving seams; reduce the
near-camera lotus motif; quiet repetitive brass trim; add asymmetric silhouette
depth and human-scale side dressing without blocking movement. These are separate
authored mesh revisions, not changes hidden in the atmosphere script.
