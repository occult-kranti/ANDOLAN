# Duryodhana — The bronze gate that refuses to move

Stable ID: `duryodhana` · Vanguard · source motif `M1`. Original mythology-inspired fiction: an art/animation brief and native-practice proposal, not an accepted production model or a canonical power.

## Silhouette, materials and motion

Square shoulder silhouette, compact crown, thick forearms and a mace head wider than the hero’s head; clear air between weapon and torso.

Materials: Hammered bronze with dark wear in recesses; Deep rust quilted cloth; Dark leather straps with quiet iron fasteners.

Low rooted stance; force travels from heel through hips to mace; every swing has a heavy recoverable follow-through.

Body/accent: `#c58b48` / `#ffe2a5`. Separate Sun triangle/Moon bracket; costume never identifies team.

## Current browser kit — retained

Health 410; speed 6.2 m/s. Primary is an aimed projectile: 29 damage every 0.55 s, projectile speed 26 m/s. Weapon: mace. Unupgraded starting values, not measured balance.

| Slot / name | Kind | Cooldown (s) | Power field | Range / radius (m) | Duration field (s) |
| --- | --- | --- | --- | --- | --- |
| Q · Mace Shock | `burst` | 10 | 48 | 10 / 5 | 2 |
| E · Hold the Ground | `ward` | 15 | 55 | 8 / 4 | 4 |
| R · Iron Crescent | `cone` | 46 | 92 | 12 / 8 | 2 |

Fields retain their simulator meanings: movement power is not landing damage; projectile radius is not an explosion; summon duration 3 produces nine-second sentinels. Only Rama/Hanuman/Sita R currently have authoritative preparation. [Timing boundary](README.md#runtime-contract).

## Primary and Q/E/R presentation

**Primary — `duryodhana.primary`:** A compressed bronze shock dart leaves the mace head; it remains the current aimed projectile, not a hidden melee sweep. Current primary has no authored gameplay windup; show the accepted muzzle/string release immediately, then its visible collidable projectile.

**Q — Mace Shock (`duryodhana.q`):** Short tooth-like ground cuts open only in the forward fan; the mace has one contact accent.

Counter: Leave the forward fan or use solid cover; pressure from its rear.

**E — Hold the Ground (`duryodhana.e`):** Four square guard plates settle close to allied silhouettes, with a visible expiry seam.

Counter: Separate protected allies or wait for shield expiry; the ward is not invulnerability.

**R — Iron Crescent (`duryodhana.r`):** An enormous broken crescent gate rises in front of the mace and is struck into a forward wedge of bronze ribs. The rear remains visibly open; no damage is implied behind the caster.

Counter: Step behind the frontal arc, back outside its range or use solid cover; punish the recovery after the defensive ward expires.

## Native ultimate demonstration contract

`duryodhana.r.v1` · shape `iron_crescent_gate` · family `forward_cone` · anchor `aimed_forward`. **No gameplay mutation.** Browser definitions stay unchanged.

Prepare 0.85 s → travel 0 s → active appearance 0.65 s → recovery 0.8 s. Nominal contact/arrival: 0.85 s. Classification: `proposed_native_demo_windup`.

Presentation envelope: range 12 m, radius 8 m, width 16 m, height 4 m. These are composition bounds; authority defines actual collision/damage. Exactly 0 projectile form(s) and 0 summon form(s); ornamental geometry adds no hitbox.

Per-cast caps: 48 instances, 160 particles, 1 light, 3 voices, 16 draw calls, 18000 triangles and 2.4 s lifetime. Provisional engineering caps, not measured GPU performance.

Low settings: Keep exact footprint, team symbol, release and expiry. Drop loose particles, secondary contour layers, point lights and ornamental distortion.

Reduced motion: No camera shake, screen flash or full-screen overlay; replace orbiting ornaments with stationary outlines.

Audio: One short onset, one release/arrival and optional low sustain; silence never removes the visible warning.

## Review focus

A full circular shockwave would falsely advertise nova coverage; keep the silhouette visibly frontal.

Require readable face/weapon at gameplay distance, grounded support feet, actual hand/socket contact, clean cloth and continuous start/stop/aim/cast/recovery footage. Review both teams, day/night, low effects and overlap. A valid catalogue or still concept cannot pass that gate.

## Concept generation brief

Original YUGA character concept: Duryodhana, The bronze gate that refuses to move. Square shoulder silhouette, compact crown, thick forearms and a mace head wider than the hero’s head; clear air between weapon and torso. Materials: Hammered bronze with dark wear in recesses; Deep rust quilted cloth; Dark leather straps with quiet iron fasteners. Show front, three-quarter and gameplay-distance silhouettes with relaxed hands and a readable weapon; include one action key pose. Purposeful expressive face, credible anatomy and fitted cloth. Original mythology-inspired fiction; no commercial-game assets, copied costume or claim of historical reconstruction. Separate concept painting from production mesh.

[Source/invention record](../research/CREATIVE_HERO_SOURCES.md) · [Machine-readable catalogue](../../assets/design/hero-codex.json)
