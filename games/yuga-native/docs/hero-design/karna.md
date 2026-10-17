# Karna — A sun shield with a fracture at dawn

Stable ID: `karna` · Striker · source motif `M1`. Original mythology-inspired fiction: an art/animation brief and native-practice proposal, not an accepted production model or a canonical power.

## Silhouette, materials and motion

Heavy archer silhouette with paired shoulder discs, crescent bow and a single long amber sash; broader and slower than Arjuna.

Materials: Burnished gold with deliberately dark engraved channels; Saffron cloth over warm brown leather; Small ivory borders; bright values concentrated at the bow.

Long deliberate draw, chest opening and a visible recovery breath; shoulder discs lag slightly after abrupt stops.

Body/accent: `#e5ac35` / `#fff5cb`. Separate Sun triangle/Moon bracket; costume never identifies team.

## Current browser kit — retained

Health 315; speed 6.8 m/s. Primary is an aimed projectile: 30 damage every 0.55 s, projectile speed 43 m/s. Weapon: bow. Unupgraded starting values, not measured balance.

| Slot / name | Kind | Cooldown (s) | Power field | Range / radius (m) | Duration field (s) |
| --- | --- | --- | --- | --- | --- |
| Q · Sunshaft | `line` | 11 | 62 | 27 / 3 | 2 |
| E · Borrowed Dawn | `ward` | 16 | 42 | 8 / 4 | 3 |
| R · Solar Reprisal | `nova` | 50 | 95 | 8 / 6 | 2 |

Fields retain their simulator meanings: movement power is not landing damage; projectile radius is not an explosion; summon duration 3 produces nine-second sentinels. Only Rama/Hanuman/Sita R currently have authoritative preparation. [Timing boundary](README.md#runtime-contract).

## Primary and Q/E/R presentation

**Primary — `karna.primary`:** A dense amber shaft with a compact diamond spark at release; weight comes from timing, not excessive bloom. Current primary has no authored gameplay windup; show the accepted muzzle/string release immediately, then its visible collidable projectile.

**Q — Sunshaft (`karna.q`):** A narrow sunshaft pierces a line of decorative gold apertures; one projectile and ordinary cover rules remain.

Counter: Cross the narrow firing line or use solid cover; a line projectile does not imply piercing.

**E — Borrowed Dawn (`karna.e`):** Separated solar plates briefly overlap beside allies; a shrinking rim shows the short ward lifetime.

Counter: Separate protected allies or wait for shield expiry; the ward is not invulnerability.

**R — Solar Reprisal (`karna.r`):** A sunwheel fractures into six mirrored armour plates, turns inside out and releases one close golden blast. Reflected-looking facets are decorative and do not reflect incoming projectiles.

Counter: Stay beyond the close six-metre radius, use cover, or bait the long cooldown before recommitting.

## Native ultimate demonstration contract

`karna.r.v1` · shape `sunwheel_reversal` · family `radial` · anchor `caster`. **No gameplay mutation.** Browser definitions stay unchanged.

Prepare 1 s → travel 0 s → active appearance 0.8 s → recovery 0.7 s. Nominal contact/arrival: 1 s. Classification: `proposed_native_demo_windup`.

Presentation envelope: range 8 m, radius 6 m, width 12 m, height 4.8 m. These are composition bounds; authority defines actual collision/damage. Exactly 0 projectile form(s) and 0 summon form(s); ornamental geometry adds no hitbox.

Per-cast caps: 48 instances, 160 particles, 1 light, 3 voices, 16 draw calls, 18000 triangles and 2.6 s lifetime. Provisional engineering caps, not measured GPU performance.

Low settings: Keep exact footprint, team symbol, release and expiry. Drop loose particles, secondary contour layers, point lights and ornamental distortion.

Reduced motion: No camera shake, screen flash or full-screen overlay; replace orbiting ornaments with stationary outlines.

Audio: One short onset, one release/arrival and optional low sustain; silence never removes the visible warning.

## Review focus

Do not imply invulnerability, damage reflection or global daylight changes.

Require readable face/weapon at gameplay distance, grounded support feet, actual hand/socket contact, clean cloth and continuous start/stop/aim/cast/recovery footage. Review both teams, day/night, low effects and overlap. A valid catalogue or still concept cannot pass that gate.

## Concept generation brief

Original YUGA character concept: Karna, A sun shield with a fracture at dawn. Heavy archer silhouette with paired shoulder discs, crescent bow and a single long amber sash; broader and slower than Arjuna. Materials: Burnished gold with deliberately dark engraved channels; Saffron cloth over warm brown leather; Small ivory borders; bright values concentrated at the bow. Show front, three-quarter and gameplay-distance silhouettes with relaxed hands and a readable weapon; include one action key pose. Purposeful expressive face, credible anatomy and fitted cloth. Original mythology-inspired fiction; no commercial-game assets, copied costume or claim of historical reconstruction. Separate concept painting from production mesh.

[Source/invention record](../research/CREATIVE_HERO_SOURCES.md) · [Machine-readable catalogue](../../assets/design/hero-codex.json)
