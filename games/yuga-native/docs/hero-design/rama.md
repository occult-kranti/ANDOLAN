# Rama — The horizon held in a bow

Stable ID: `rama` · Striker · source motif `R1`. Original mythology-inspired fiction: an art/animation brief and native-practice proposal, not an accepted production model or a canonical power.

## Silhouette, materials and motion

A long calm vertical silhouette; one crescent bow taller than the shoulder; split cobalt sash balanced by a narrow ivory waist.

Materials: Indigo woven silk with broad quiet folds; Warm bronze bow fittings with sparse engraved sun lines; Matte ivory armour and natural skin; restrained gold edge light.

Small economical weight transfers; relaxed string hand opens after release; planted rear foot and a clear breath before committed shots.

Body/accent: `#3cb8df` / `#ffdf85`. Separate Sun triangle/Moon bracket; costume never identifies team.

## Current browser kit — retained

Health 300; speed 7.2 m/s. Primary is an aimed projectile: 27 damage every 0.48 s, projectile speed 46 m/s. Weapon: bow. Unupgraded starting values, not measured balance.

| Slot / name | Kind | Cooldown (s) | Power field | Range / radius (m) | Duration field (s) |
| --- | --- | --- | --- | --- | --- |
| Q · Steady Arrow | `bolt` | 9 | 54 | 26 / 3 | 2 |
| E · Measured Step | `dash` | 12 | 25 | 10 / 3 | 2 |
| R · Dawn Volley | `line` | 44 | 32 | 28 / 3 | 2 |

Fields retain their simulator meanings: movement power is not landing damage; projectile radius is not an explosion; summon duration 3 produces nine-second sentinels. Only Rama/Hanuman/Sita R currently have authoritative preparation. [Timing boundary](README.md#runtime-contract).

## Primary and Q/E/R presentation

**Primary — `rama.primary`:** A thin gold shaft with a blue feather wake; one visible nock, string release and bow recoil, never a continuous laser. Current primary has no authored gameplay windup; show the accepted muzzle/string release immediately, then its visible collidable projectile.

**Q — Steady Arrow (`rama.q`):** A single broad-headed arrow draws a crisp blue centreline; its thicker head distinguishes the power shot from primary.

Counter: Sidestep the aimed projectile or use solid cover; there is no homing.

**E — Measured Step (`rama.e`):** Two folded sash ribbons trace the actual dash path and settle at the collision-limited endpoint; no damaging afterimage.

Counter: Predict the collision-limited endpoint; the dash has no added damage or invulnerability.

**R — Dawn Volley (`rama.r`):** Three mirrored bow silhouettes fold around a dark solar disc, then collapse into exactly three gold arrows along the accepted spread. The eclipse is a framing motif, never a screen blackout.

Counter: Break the locked firing lane laterally or take solid cover during the one-second preparation.

## Native ultimate demonstration contract

`rama.r.v1` · shape `mirrored_arrow_eclipse` · family `projectile` · anchor `aimed_forward`. **No gameplay mutation.** Browser definitions stay unchanged.

Prepare 1 s → travel 0.46 s → active appearance 0.6 s → recovery 0.45 s. Nominal contact/arrival: 1.46 s. Classification: `browser_windup_preserved`.

Presentation envelope: range 28 m, radius 3 m, width 7 m, height 4.2 m. These are composition bounds; authority defines actual collision/damage. Exactly 3 projectile form(s) and 0 summon form(s); ornamental geometry adds no hitbox.

Per-cast caps: 48 instances, 160 particles, 1 light, 3 voices, 16 draw calls, 18000 triangles and 2.61 s lifetime. Provisional engineering caps, not measured GPU performance.

Low settings: Keep exact footprint, team symbol, release and expiry. Drop loose particles, secondary contour layers, point lights and ornamental distortion.

Reduced motion: No camera shake, screen flash or full-screen overlay; replace orbiting ornaments with stationary outlines.

Audio: One short onset, one release/arrival and optional low sustain; silence never removes the visible warning.

## Review focus

Bow/string grip, crossed draw fingers and unbounded eclipse opacity can ruin the strongest close-up.

Require readable face/weapon at gameplay distance, grounded support feet, actual hand/socket contact, clean cloth and continuous start/stop/aim/cast/recovery footage. Review both teams, day/night, low effects and overlap. A valid catalogue or still concept cannot pass that gate.

## Concept generation brief

Original YUGA character concept: Rama, The horizon held in a bow. A long calm vertical silhouette; one crescent bow taller than the shoulder; split cobalt sash balanced by a narrow ivory waist. Materials: Indigo woven silk with broad quiet folds; Warm bronze bow fittings with sparse engraved sun lines; Matte ivory armour and natural skin; restrained gold edge light. Show front, three-quarter and gameplay-distance silhouettes with relaxed hands and a readable weapon; include one action key pose. Purposeful expressive face, credible anatomy and fitted cloth. Original mythology-inspired fiction; no commercial-game assets, copied costume or claim of historical reconstruction. Separate concept painting from production mesh.

[Source/invention record](../research/CREATIVE_HERO_SOURCES.md) · [Machine-readable catalogue](../../assets/design/hero-codex.json)
