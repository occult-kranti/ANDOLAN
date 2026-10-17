# Meghnad — A storm written across the skyline

Stable ID: `meghnad` · Striker · source motif `R1`. Original mythology-inspired fiction: an art/animation brief and native-practice proposal, not an accepted production model or a canonical power.

## Silhouette, materials and motion

Lean forward silhouette, forked crest, compact bow and layered cloud scarf swept to one side rather than forming an opaque cloak.

Materials: Blue-violet layered silk; Dark iridescent metal limited to crest and bow; Cold silver seams and soft grey translucent accents.

Quick oblique footwork with abrupt held aim; scarf drifts after stops but never covers the face or sightline.

Body/accent: `#857ee0` / `#bce9ff`. Separate Sun triangle/Moon bracket; costume never identifies team.

## Current browser kit — retained

Health 285; speed 7.8 m/s. Primary is an aimed projectile: 22 damage every 0.4 s, projectile speed 42 m/s. Weapon: bow. Unupgraded starting values, not measured balance.

| Slot / name | Kind | Cooldown (s) | Power field | Range / radius (m) | Duration field (s) |
| --- | --- | --- | --- | --- | --- |
| Q · Cloud Snare | `slow` | 12 | 28 | 22 / 4 | 3 |
| E · Storm Step | `dash` | 12 | 25 | 13 / 3 | 2 |
| R · Gathered Squall | `burst` | 43 | 78 | 22 / 7 | 2 |

Fields retain their simulator meanings: movement power is not landing damage; projectile radius is not an explosion; summon duration 3 produces nine-second sentinels. Only Rama/Hanuman/Sita R currently have authoritative preparation. [Timing boundary](README.md#runtime-contract).

## Primary and Q/E/R presentation

**Primary — `meghnad.primary`:** A violet dart leaves two short forked contrails; no invisible projectile phases. Current primary has no authored gameplay windup; show the accepted muzzle/string release immediately, then its visible collidable projectile.

**Q — Cloud Snare (`meghnad.q`):** A low segmented cloud basin contains thin descending threads; targets remain visible through its centre.

Counter: Leave the visible zone or choose another route; the area is not a wall.

**E — Storm Step (`meghnad.e`):** An open lightning bracket marks actual dash displacement without implying teleport immunity or stealth.

Counter: Predict the collision-limited endpoint; the dash has no added damage or invulnerability.

**R — Gathered Squall (`meghnad.r`):** Three long storm ribbons unroll into a transparent forward fan, then close like a folding monsoon scroll. Lightning runs along the boundary and only one fan payload is implied.

Counter: Leave the forward fan laterally, use solid cover or pressure the low-health caster after the dash is spent.

## Native ultimate demonstration contract

`meghnad.r.v1` · shape `storm_scroll` · family `forward_fan` · anchor `aimed_forward`. **No gameplay mutation.** Browser definitions stay unchanged.

Prepare 0.75 s → travel 0 s → active appearance 0.8 s → recovery 0.55 s. Nominal contact/arrival: 0.75 s. Classification: `proposed_native_demo_windup`.

Presentation envelope: range 22 m, radius 7 m, width 18 m, height 5 m. These are composition bounds; authority defines actual collision/damage. Exactly 0 projectile form(s) and 0 summon form(s); ornamental geometry adds no hitbox.

Per-cast caps: 48 instances, 160 particles, 1 light, 3 voices, 16 draw calls, 18000 triangles and 2.2 s lifetime. Provisional engineering caps, not measured GPU performance.

Low settings: Keep exact footprint, team symbol, release and expiry. Drop loose particles, secondary contour layers, point lights and ornamental distortion.

Reduced motion: No camera shake, screen flash or full-screen overlay; replace orbiting ornaments with stationary outlines.

Audio: One short onset, one release/arrival and optional low sustain; silence never removes the visible warning.

## Review focus

Opaque storm smoke must not conceal opponents or imply a vision-denial/stealth system.

Require readable face/weapon at gameplay distance, grounded support feet, actual hand/socket contact, clean cloth and continuous start/stop/aim/cast/recovery footage. Review both teams, day/night, low effects and overlap. A valid catalogue or still concept cannot pass that gate.

## Concept generation brief

Original YUGA character concept: Meghnad, A storm written across the skyline. Lean forward silhouette, forked crest, compact bow and layered cloud scarf swept to one side rather than forming an opaque cloak. Materials: Blue-violet layered silk; Dark iridescent metal limited to crest and bow; Cold silver seams and soft grey translucent accents. Show front, three-quarter and gameplay-distance silhouettes with relaxed hands and a readable weapon; include one action key pose. Purposeful expressive face, credible anatomy and fitted cloth. Original mythology-inspired fiction; no commercial-game assets, copied costume or claim of historical reconstruction. Separate concept painting from production mesh.

[Source/invention record](../research/CREATIVE_HERO_SOURCES.md) · [Machine-readable catalogue](../../assets/design/hero-codex.json)
