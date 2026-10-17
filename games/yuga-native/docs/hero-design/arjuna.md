# Arjuna — The arrow that finds one opening

Stable ID: `arjuna` · Striker · source motif `M1`. Original mythology-inspired fiction: an art/animation brief and native-practice proposal, not an accepted production model or a canonical power.

## Silhouette, materials and motion

Lean diagonal stance, long angular bow, high off-centre quiver and a split shoulder scarf distinct from Rama’s vertical sash.

Materials: Deep lapis cloth with pale stitched hems; Brushed silver bow laminates; Ivory leather grips and restrained amber beads.

Rapid hip-led pivots, low side steps and clear shoulder counterrotation; feet recover beneath the centre before the next shot.

Body/accent: `#6599fa` / `#f5e7bd`. Separate Sun triangle/Moon bracket; costume never identifies team.

## Current browser kit — retained

Health 275; speed 7.7 m/s. Primary is an aimed projectile: 20 damage every 0.35 s, projectile speed 48 m/s. Weapon: bow. Unupgraded starting values, not measured balance.

| Slot / name | Kind | Cooldown (s) | Power field | Range / radius (m) | Duration field (s) |
| --- | --- | --- | --- | --- | --- |
| Q · Converging Volley | `burst` | 8 | 38 | 18 / 5 | 2 |
| E · New Angle | `dash` | 11 | 25 | 12 / 3 | 2 |
| R · One Clear Line | `line` | 42 | 88 | 28 / 3 | 2 |

Fields retain their simulator meanings: movement power is not landing damage; projectile radius is not an explosion; summon duration 3 produces nine-second sentinels. Only Rama/Hanuman/Sita R currently have authoritative preparation. [Timing boundary](README.md#runtime-contract).

## Primary and Q/E/R presentation

**Primary — `arjuna.primary`:** Fine silver arrow with two short blue fletching marks; fast release and clean recoverable wrist. Current primary has no authored gameplay windup; show the accepted muzzle/string release immediately, then its visible collidable projectile.

**Q — Converging Volley (`arjuna.q`):** A comb of narrow blue wedges opens into the actual forward fan, without implying individually collidable arrows.

Counter: Leave the forward fan or use solid cover; pressure from its rear.

**E — New Angle (`arjuna.e`):** A sharp diagonal scarf slash marks the new angle; one fading starting-position silhouette carries no hitbox.

Counter: Predict the collision-limited endpoint; the dash has no added damage or invulnerability.

**R — One Clear Line (`arjuna.r`):** A row of translucent mirror gates aligns down one lane; a single silver needle punches through their visual centres and the empty frames fold away. The projectile still stops at the first accepted collision.

Counter: Move across the narrow line or use cover; the lowest base health makes an exposed firing angle costly.

## Native ultimate demonstration contract

`arjuna.r.v1` · shape `horizon_needle` · family `projectile` · anchor `aimed_forward`. **No gameplay mutation.** Browser definitions stay unchanged.

Prepare 0.75 s → travel 0.46 s → active appearance 0.35 s → recovery 0.4 s. Nominal contact/arrival: 1.21 s. Classification: `proposed_native_demo_windup`.

Presentation envelope: range 28 m, radius 0.5 m, width 1.2 m, height 3.6 m. These are composition bounds; authority defines actual collision/damage. Exactly 1 projectile form(s) and 0 summon form(s); ornamental geometry adds no hitbox.

Per-cast caps: 48 instances, 160 particles, 1 light, 3 voices, 16 draw calls, 18000 triangles and 2.06 s lifetime. Provisional engineering caps, not measured GPU performance.

Low settings: Keep exact footprint, team symbol, release and expiry. Drop loose particles, secondary contour layers, point lights and ornamental distortion.

Reduced motion: No camera shake, screen flash or full-screen overlay; replace orbiting ornaments with stationary outlines.

Audio: One short onset, one release/arrival and optional low sustain; silence never removes the visible warning.

## Review focus

Mirrors must not suggest wall piercing, homing or multiple damage beams.

Require readable face/weapon at gameplay distance, grounded support feet, actual hand/socket contact, clean cloth and continuous start/stop/aim/cast/recovery footage. Review both teams, day/night, low effects and overlap. A valid catalogue or still concept cannot pass that gate.

## Concept generation brief

Original YUGA character concept: Arjuna, The arrow that finds one opening. Lean diagonal stance, long angular bow, high off-centre quiver and a split shoulder scarf distinct from Rama’s vertical sash. Materials: Deep lapis cloth with pale stitched hems; Brushed silver bow laminates; Ivory leather grips and restrained amber beads. Show front, three-quarter and gameplay-distance silhouettes with relaxed hands and a readable weapon; include one action key pose. Purposeful expressive face, credible anatomy and fitted cloth. Original mythology-inspired fiction; no commercial-game assets, copied costume or claim of historical reconstruction. Separate concept painting from production mesh.

[Source/invention record](../research/CREATIVE_HERO_SOURCES.md) · [Machine-readable catalogue](../../assets/design/hero-codex.json)
