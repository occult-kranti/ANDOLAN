# Hanuman — The mountain carried home

Stable ID: `hanuman` · Keeper · source motif `R1`. Original mythology-inspired fiction: an art/animation brief and native-practice proposal, not an accepted production model or a canonical power.

## Silhouette, materials and motion

Powerful upper body with an open face, one curved tail counterbalancing the mace and a long saffron scarf with a readable split end.

Materials: Warm terracotta cloth and worn brass; Natural fur/skin with low roughness contrast at the face; Jade herb accents restricted to the aid motif.

Deep elastic compression before travel, clear airborne extension and weighted ankle/knee landing; tail settles after the torso.

Body/accent: `#e79c61` / `#fff3bd`. Separate Sun triangle/Moon bracket; costume never identifies team.

## Current browser kit — retained

Health 350; speed 7.6 m/s. Primary is an aimed projectile: 23 damage every 0.46 s, projectile speed 29 m/s. Weapon: mace. Unupgraded starting values, not measured balance.

| Slot / name | Kind | Cooldown (s) | Power field | Range / radius (m) | Duration field (s) |
| --- | --- | --- | --- | --- | --- |
| Q · Windward Leap | `leap` | 9 | 28 | 14 / 3 | 2 |
| E · Bring Them Home | `heal` | 14 | 48 | 8 / 5 | 3 |
| R · Mountain Pulse | `nova` | 45 | 65 | 14 / 7 | 2 |

Fields retain their simulator meanings: movement power is not landing damage; projectile radius is not an explosion; summon duration 3 produces nine-second sentinels. Only Rama/Hanuman/Sita R currently have authoritative preparation. [Timing boundary](README.md#runtime-contract).

## Primary and Q/E/R presentation

**Primary — `hanuman.primary`:** A warm short wake follows the mace’s aimed energy pellet; heavy wrist recovery communicates its slower rate. Current primary has no authored gameplay windup; show the accepted muzzle/string release immediately, then its visible collidable projectile.

**Q — Windward Leap (`hanuman.q`):** A wind spiral follows the actual leap arc and vanishes at collision; the landing is non-damaging for this ordinary ability.

Counter: Pressure the collision-limited landing; ordinary leap does not add hidden landing damage.

**E — Bring Them Home (`hanuman.e`):** Herb-shaped outward strokes climb toward nearby allies; a low soft pulse marks accepted restoration.

Counter: Force allies apart and apply pressure outside the healing radius; no resurrection.

**R — Mountain Pulse (`hanuman.r`):** Three translucent mountain contours process behind a single carried rocky silhouette; the landing disc stays clear beneath them. On actual landing, stone ribs fold outward while herb leaves rise to allies. Decorative peaks add no collisions or secondary hits.

Counter: Leave the marked collision-limited landing area during preparation/travel; solid cover constrains both travel and landing payload.

## Native ultimate demonstration contract

`hanuman.r.v1` · shape `mountain_procession` · family `radial` · anchor `aimed_ground`. **No gameplay mutation.** Browser definitions stay unchanged.

Prepare 0.7 s → travel 0.45 s → active appearance 1 s → recovery 0.65 s. Nominal contact/arrival: 1.15 s. Classification: `browser_windup_preserved`.

Presentation envelope: range 14 m, radius 7 m, width 14 m, height 7 m. These are composition bounds; authority defines actual collision/damage. Exactly 0 projectile form(s) and 0 summon form(s); ornamental geometry adds no hitbox.

Per-cast caps: 48 instances, 160 particles, 1 light, 3 voices, 16 draw calls, 18000 triangles and 2.9 s lifetime. Provisional engineering caps, not measured GPU performance.

Low settings: Keep exact footprint, team symbol, release and expiry. Drop loose particles, secondary contour layers, point lights and ornamental distortion.

Reduced motion: No camera shake, screen flash or full-screen overlay; replace orbiting ornaments with stationary outlines.

Audio: One short onset, one release/arrival and optional low sustain; silence never removes the visible warning.

## Review focus

The mountain cannot hide the landing marker or detach hand/weapon contact; scenery must not masquerade as new terrain.

Require readable face/weapon at gameplay distance, grounded support feet, actual hand/socket contact, clean cloth and continuous start/stop/aim/cast/recovery footage. Review both teams, day/night, low effects and overlap. A valid catalogue or still concept cannot pass that gate.

## Concept generation brief

Original YUGA character concept: Hanuman, The mountain carried home. Powerful upper body with an open face, one curved tail counterbalancing the mace and a long saffron scarf with a readable split end. Materials: Warm terracotta cloth and worn brass; Natural fur/skin with low roughness contrast at the face; Jade herb accents restricted to the aid motif. Show front, three-quarter and gameplay-distance silhouettes with relaxed hands and a readable weapon; include one action key pose. Purposeful expressive face, credible anatomy and fitted cloth. Original mythology-inspired fiction; no commercial-game assets, copied costume or claim of historical reconstruction. Separate concept painting from production mesh.

[Source/invention record](../research/CREATIVE_HERO_SOURCES.md) · [Machine-readable catalogue](../../assets/design/hero-codex.json)
