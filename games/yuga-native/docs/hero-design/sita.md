# Sita — A living courtyard held in two hands

Stable ID: `sita` · Keeper · source motif `R1`. Original mythology-inspired fiction: an art/animation brief and native-practice proposal, not an accepted production model or a canonical power.

## Silhouette, materials and motion

Grounded poised silhouette, seed-shaped crest, long emerald/ivory mantle and a leaf-tipped staff with a clear curved opening.

Materials: Emerald woven cloth with ivory folded lining; Matte carved wood and warm small brass joints; Seed-like translucent jade accents, no glossy plastic leaves.

Measured planted steps and open protective palms; staff turns around a stable two-hand anchor; mantle settles without clipping wrists.

Body/accent: `#69c8a2` / `#ffe3b1`. Separate Sun triangle/Moon bracket; costume never identifies team.

## Current browser kit — retained

Health 330; speed 6.8 m/s. Primary is an aimed projectile: 19 damage every 0.45 s, projectile speed 32 m/s. Weapon: staff. Unupgraded starting values, not measured balance.

| Slot / name | Kind | Cooldown (s) | Power field | Range / radius (m) | Duration field (s) |
| --- | --- | --- | --- | --- | --- |
| Q · Grove Renewal | `heal` | 10 | 50 | 8 / 5 | 3 |
| E · Rooted Path | `slow` | 15 | 25 | 18 / 5 | 4 |
| R · Shelter of Mithila | `ward` | 46 | 70 | 8 / 8 | 6 |

Fields retain their simulator meanings: movement power is not landing damage; projectile radius is not an explosion; summon duration 3 produces nine-second sentinels. Only Rama/Hanuman/Sita R currently have authoritative preparation. [Timing boundary](README.md#runtime-contract).

## Primary and Q/E/R presentation

**Primary — `sita.primary`:** A small seed-shaped green bolt with a two-leaf wake; it remains an aimed damaging projectile. Current primary has no authored gameplay windup; show the accepted muzzle/string release immediately, then its visible collidable projectile.

**Q — Grove Renewal (`sita.q`):** Five outward leaf veins connect to the accepted nearby healing circle; no spreading forest outside the radius.

Counter: Force allies apart and apply pressure outside the healing radius; no resurrection.

**E — Rooted Path (`sita.e`):** Low root ribbons trace the slowing zone boundary; the open middle and unblocked exits show it is not a wall or immobilization.

Counter: Leave the visible zone or choose another route; the area is not a wall.

**R — Shelter of Mithila (`sita.r`):** A living court grows from four open branch arches around the sanctuary, with hanging seed lanterns and an unobstructed centre. Shield petals close once; small leaves rise during actual healing ticks. The forest fades at six seconds and never becomes terrain.

Counter: Split allied formations, pressure another lane or force defenders out of the fixed sanctuary; it is not a mobile invulnerability dome.

## Native ultimate demonstration contract

`sita.r.v1` · shape `mithila_living_court` · family `protection` · anchor `caster`. **No gameplay mutation.** Browser definitions stay unchanged.

Prepare 0.8 s → travel 0 s → active appearance 6 s → recovery 0.6 s. Nominal contact/arrival: 0.8 s. Classification: `browser_windup_preserved`.

Presentation envelope: range 8 m, radius 8 m, width 16 m, height 5.5 m. These are composition bounds; authority defines actual collision/damage. Exactly 0 projectile form(s) and 0 summon form(s); ornamental geometry adds no hitbox.

Per-cast caps: 48 instances, 160 particles, 1 light, 3 voices, 16 draw calls, 18000 triangles and 7.5 s lifetime. Provisional engineering caps, not measured GPU performance.

Low settings: Keep exact footprint, team symbol, release and expiry. Drop loose particles, secondary contour layers, point lights and ornamental distortion.

Reduced motion: No camera shake, screen flash or full-screen overlay; replace orbiting ornaments with stationary outlines.

Audio: One short onset, one release/arrival and optional low sustain; silence never removes the visible warning.

## Review focus

Branches must keep aim lanes, feet and opponents visible; her agency comes from commanding posture rather than passive ornament.

Require readable face/weapon at gameplay distance, grounded support feet, actual hand/socket contact, clean cloth and continuous start/stop/aim/cast/recovery footage. Review both teams, day/night, low effects and overlap. A valid catalogue or still concept cannot pass that gate.

## Concept generation brief

Original YUGA character concept: Sita, A living courtyard held in two hands. Grounded poised silhouette, seed-shaped crest, long emerald/ivory mantle and a leaf-tipped staff with a clear curved opening. Materials: Emerald woven cloth with ivory folded lining; Matte carved wood and warm small brass joints; Seed-like translucent jade accents, no glossy plastic leaves. Show front, three-quarter and gameplay-distance silhouettes with relaxed hands and a readable weapon; include one action key pose. Purposeful expressive face, credible anatomy and fitted cloth. Original mythology-inspired fiction; no commercial-game assets, copied costume or claim of historical reconstruction. Separate concept painting from production mesh.

[Source/invention record](../research/CREATIVE_HERO_SOURCES.md) · [Machine-readable catalogue](../../assets/design/hero-codex.json)
