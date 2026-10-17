# Subhadra — The standard that makes a road

Stable ID: `subhadra` · Keeper · source motif `M1`. Original mythology-inspired fiction: an art/animation brief and native-practice proposal, not an accepted production model or a canonical power.

## Silhouette, materials and motion

Spear pennant, rounded shoulder guards and a strong side braid; asymmetric short command cape leaves both legs readable.

Materials: Teal woven cloth and warm ivory pennant; Brushed brass spear fittings; Dark leather armour with clean broad planes.

Forward-alert command stance; decisive spear points and heel-to-toe steps; hand signals precede allied staging without adding orders to server rules.

Body/accent: `#64bbc5` / `#ffe8a4`. Separate Sun triangle/Moon bracket; costume never identifies team.

## Current browser kit — retained

Health 315; speed 7.2 m/s. Primary is an aimed projectile: 22 damage every 0.45 s, projectile speed 38 m/s. Weapon: spear. Unupgraded starting values, not measured balance.

| Slot / name | Kind | Cooldown (s) | Power field | Range / radius (m) | Duration field (s) |
| --- | --- | --- | --- | --- | --- |
| Q · Signal Lance | `bolt` | 9 | 44 | 24 / 3 | 2 |
| E · Rally Close | `heal` | 13 | 42 | 8 / 4 | 3 |
| R · Twin Standards | `summon` | 48 | 28 | 10 / 4 | 3 |

Fields retain their simulator meanings: movement power is not landing damage; projectile radius is not an explosion; summon duration 3 produces nine-second sentinels. Only Rama/Hanuman/Sita R currently have authoritative preparation. [Timing boundary](README.md#runtime-contract).

## Primary and Q/E/R presentation

**Primary — `subhadra.primary`:** A teal lance-shaped bolt from the spear tip, with a short rectangular pennant wake. Current primary has no authored gameplay windup; show the accepted muzzle/string release immediately, then its visible collidable projectile.

**Q — Signal Lance (`subhadra.q`):** A brighter signal lance leaves two small square markers along its clear firing line.

Counter: Sidestep the aimed projectile or use solid cover; there is no homing.

**E — Rally Close (`subhadra.e`):** A compact rally circle sends outward chevrons toward nearby allies; small radius remains visible.

Counter: Force allies apart and apply pressure outside the healing radius; no resurrection.

**R — Twin Standards (`subhadra.r`):** Two miniature banner-chariot silhouettes form beside the caster, resolve into exactly two temporary sentinel standards, then march with their actual units. Their nine-second sandglass crests drain visibly. The chariot image does not summon additional vehicles.

Counter: Defeat or kite the two temporary sentinels, pressure a different route or wait out their nine-second lifetime.

## Native ultimate demonstration contract

`subhadra.r.v1` · shape `twin_banner_procession` · family `summon_pair` · anchor `caster`. **No gameplay mutation.** Browser definitions stay unchanged.

Prepare 0.85 s → travel 0 s → active appearance 9 s → recovery 0.5 s. Nominal contact/arrival: 0.85 s. Classification: `proposed_native_demo_windup`.

Presentation envelope: range 10 m, radius 4 m, width 8 m, height 4.5 m. These are composition bounds; authority defines actual collision/damage. Exactly 0 projectile form(s) and 2 summon form(s); ornamental geometry adds no hitbox.

Per-cast caps: 48 instances, 160 particles, 1 light, 3 voices, 16 draw calls, 18000 triangles and 10.45 s lifetime. Provisional engineering caps, not measured GPU performance.

Low settings: Keep exact footprint, team symbol, release and expiry. Drop loose particles, secondary contour layers, point lights and ornamental distortion.

Reduced motion: No camera shake, screen flash or full-screen overlay; replace orbiting ornaments with stationary outlines.

Audio: One short onset, one release/arrival and optional low sustain; silence never removes the visible warning.

## Review focus

No third unit, permanent reinforcement, controllable vehicle or hidden team buff is implied by the procession.

Require readable face/weapon at gameplay distance, grounded support feet, actual hand/socket contact, clean cloth and continuous start/stop/aim/cast/recovery footage. Review both teams, day/night, low effects and overlap. A valid catalogue or still concept cannot pass that gate.

## Concept generation brief

Original YUGA character concept: Subhadra, The standard that makes a road. Spear pennant, rounded shoulder guards and a strong side braid; asymmetric short command cape leaves both legs readable. Materials: Teal woven cloth and warm ivory pennant; Brushed brass spear fittings; Dark leather armour with clean broad planes. Show front, three-quarter and gameplay-distance silhouettes with relaxed hands and a readable weapon; include one action key pose. Purposeful expressive face, credible anatomy and fitted cloth. Original mythology-inspired fiction; no commercial-game assets, copied costume or claim of historical reconstruction. Separate concept painting from production mesh.

[Source/invention record](../research/CREATIVE_HERO_SOURCES.md) · [Machine-readable catalogue](../../assets/design/hero-codex.json)
