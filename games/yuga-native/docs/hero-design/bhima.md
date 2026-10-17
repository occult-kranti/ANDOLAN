# Bhima — The storm that starts beneath a heel

Stable ID: `bhima` · Vanguard · source motif `M1`. Original mythology-inspired fiction: an art/animation brief and native-practice proposal, not an accepted production model or a canonical power.

## Silhouette, materials and motion

Broad powerful torso, crossed straps, asymmetric waist cloth and a long-headed mace carried low enough to keep the face clear.

Materials: Forest-green coarse cloth; Dark steel mace with bright worn impact edges; Weathered leather and limited pale brass.

Big but controlled torso compression; shoulders follow hips; stomp and weapon contact have separate readable beats.

Body/accent: `#62b88d` / `#eaf4bc`. Separate Sun triangle/Moon bracket; costume never identifies team.

## Current browser kit — retained

Health 400; speed 6.4 m/s. Primary is an aimed projectile: 28 damage every 0.55 s, projectile speed 27 m/s. Weapon: mace. Unupgraded starting values, not measured balance.

| Slot / name | Kind | Cooldown (s) | Power field | Range / radius (m) | Duration field (s) |
| --- | --- | --- | --- | --- | --- |
| Q · Heavy Sweep | `cone` | 10 | 52 | 10 / 5 | 2 |
| E · Closing Stride | `leap` | 15 | 32 | 12 / 3 | 2 |
| R · Thunder at Your Feet | `nova` | 48 | 92 | 8 / 8 | 2 |

Fields retain their simulator meanings: movement power is not landing damage; projectile radius is not an explosion; summon duration 3 produces nine-second sentinels. Only Rama/Hanuman/Sita R currently have authoritative preparation. [Timing boundary](README.md#runtime-contract).

## Primary and Q/E/R presentation

**Primary — `bhima.primary`:** A blunt green-white pressure pellet from the mace, with short particulate grit that never forms another hit volume. Current primary has no authored gameplay windup; show the accepted muzzle/string release immediately, then its visible collidable projectile.

**Q — Heavy Sweep (`bhima.q`):** A heavy forward fan of stone-coloured air wedges stays low to the floor.

Counter: Move outside the forward cone, behind the caster or behind solid cover.

**E — Closing Stride (`bhima.e`):** A short low leap with a broad cloth trail; ordinary landing does not secretly deal damage.

Counter: Pressure the collision-limited landing; ordinary leap does not add hidden landing damage.

**R — Thunder at Your Feet (`bhima.r`):** Eight low stone ribs lift like drum skins around the feet, compress together, then snap down into one broad radial pulse. The ground surface never breaks or changes collision.

Counter: Space outside the eight-metre footprint or take solid cover; the visual ground fracture is cosmetic.

## Native ultimate demonstration contract

`bhima.r.v1` · shape `fault_drum` · family `radial` · anchor `caster`. **No gameplay mutation.** Browser definitions stay unchanged.

Prepare 0.8 s → travel 0 s → active appearance 0.9 s → recovery 0.8 s. Nominal contact/arrival: 0.8 s. Classification: `proposed_native_demo_windup`.

Presentation envelope: range 8 m, radius 8 m, width 16 m, height 3.5 m. These are composition bounds; authority defines actual collision/damage. Exactly 0 projectile form(s) and 0 summon form(s); ornamental geometry adds no hitbox.

Per-cast caps: 48 instances, 160 particles, 1 light, 3 voices, 16 draw calls, 18000 triangles and 2.6 s lifetime. Provisional engineering caps, not measured GPU performance.

Low settings: Keep exact footprint, team symbol, release and expiry. Drop loose particles, secondary contour layers, point lights and ornamental distortion.

Reduced motion: No camera shake, screen flash or full-screen overlay; replace orbiting ornaments with stationary outlines.

Audio: One short onset, one release/arrival and optional low sustain; silence never removes the visible warning.

## Review focus

Camera shake, tall debris and literal terrain destruction would hurt aim/readability and overstate the mechanic.

Require readable face/weapon at gameplay distance, grounded support feet, actual hand/socket contact, clean cloth and continuous start/stop/aim/cast/recovery footage. Review both teams, day/night, low effects and overlap. A valid catalogue or still concept cannot pass that gate.

## Concept generation brief

Original YUGA character concept: Bhima, The storm that starts beneath a heel. Broad powerful torso, crossed straps, asymmetric waist cloth and a long-headed mace carried low enough to keep the face clear. Materials: Forest-green coarse cloth; Dark steel mace with bright worn impact edges; Weathered leather and limited pale brass. Show front, three-quarter and gameplay-distance silhouettes with relaxed hands and a readable weapon; include one action key pose. Purposeful expressive face, credible anatomy and fitted cloth. Original mythology-inspired fiction; no commercial-game assets, copied costume or claim of historical reconstruction. Separate concept painting from production mesh.

[Source/invention record](../research/CREATIVE_HERO_SOURCES.md) · [Machine-readable catalogue](../../assets/design/hero-codex.json)
