# Draupadi — Five standards, one unbroken voice

Stable ID: `draupadi` · Keeper · source motif `M1`. Original mythology-inspired fiction: an art/animation brief and native-practice proposal, not an accepted production model or a canonical power.

## Silhouette, materials and motion

Upright narrow staff, strong vertical crown and a five-point mantle clasp; layered wine-coloured cloth falls in five broad readable panels.

Materials: Wine-red silk with muted coral undersides; Dark gold clasp and staff fittings; Warm ivory embroidery concentrated on large edges.

Firm heel-led turns, clear speaking-hand gestures and composed shoulder carriage; cloth follows the command rather than whipping randomly.

Body/accent: `#d4759b` / `#ffe1a8`. Separate Sun triangle/Moon bracket; costume never identifies team.

## Current browser kit — retained

Health 340; speed 6.5 m/s. Primary is an aimed projectile: 20 damage every 0.48 s, projectile speed 33 m/s. Weapon: staff. Unupgraded starting values, not measured balance.

| Slot / name | Kind | Cooldown (s) | Power field | Range / radius (m) | Duration field (s) |
| --- | --- | --- | --- | --- | --- |
| Q · Circle of Resolve | `ward` | 10 | 46 | 8 / 5 | 4 |
| E · Stand Accountable | `pull` | 17 | 30 | 19 / 5 | 2 |
| R · Unbroken Assembly | `heal` | 48 | 95 | 8 / 8 | 4 |

Fields retain their simulator meanings: movement power is not landing damage; projectile radius is not an explosion; summon duration 3 produces nine-second sentinels. Only Rama/Hanuman/Sita R currently have authoritative preparation. [Timing boundary](README.md#runtime-contract).

## Primary and Q/E/R presentation

**Primary — `draupadi.primary`:** A rose-gold ember-shaped projectile with a square tail mark; flame colour does not change its damage rules. Current primary has no authored gameplay windup; show the accepted muzzle/string release immediately, then its visible collidable projectile.

**Q — Circle of Resolve (`draupadi.q`):** Five short cloth-like shield tabs unfold outward beside nearby allies and visibly expire.

Counter: Separate protected allies or wait for shield expiry; the ward is not invulnerability.

**E — Stand Accountable (`draupadi.e`):** A low five-point assembly mark pulls inward at the target; it is not a stun, interrogation or lore-based judgment mechanic.

Counter: Leave the aimed radius or use solid cover; solid obstacles constrain displacement.

**R — Unbroken Assembly (`draupadi.r`):** Five tall translucent banners arc into an open assembly around the caster, stitch a single gold seam across the floor and release one outward healing wave. The banners remain porous and non-colliding.

Counter: Spread pressure beyond the eight-metre heal radius, force separation and exploit the lack of a movement ability; no resurrection or damage immunity.

## Native ultimate demonstration contract

`draupadi.r.v1` · shape `fivefold_assembly` · family `restoration` · anchor `caster`. **No gameplay mutation.** Browser definitions stay unchanged.

Prepare 0.9 s → travel 0 s → active appearance 1.1 s → recovery 0.6 s. Nominal contact/arrival: 0.9 s. Classification: `proposed_native_demo_windup`.

Presentation envelope: range 8 m, radius 8 m, width 16 m, height 5.8 m. These are composition bounds; authority defines actual collision/damage. Exactly 0 projectile form(s) and 0 summon form(s); ornamental geometry adds no hitbox.

Per-cast caps: 48 instances, 160 particles, 1 light, 3 voices, 16 draw calls, 18000 triangles and 2.7 s lifetime. Provisional engineering caps, not measured GPU performance.

Low settings: Keep exact footprint, team symbol, release and expiry. Drop loose particles, secondary contour layers, point lights and ornamental distortion.

Reduced motion: No camera shake, screen flash or full-screen overlay; replace orbiting ornaments with stationary outlines.

Audio: One short onset, one release/arrival and optional low sustain; silence never removes the visible warning.

## Review focus

Fire should not make a friendly heal look like hostile burn; five banners must not become five opaque walls.

Require readable face/weapon at gameplay distance, grounded support feet, actual hand/socket contact, clean cloth and continuous start/stop/aim/cast/recovery footage. Review both teams, day/night, low effects and overlap. A valid catalogue or still concept cannot pass that gate.

## Concept generation brief

Original YUGA character concept: Draupadi, Five standards, one unbroken voice. Upright narrow staff, strong vertical crown and a five-point mantle clasp; layered wine-coloured cloth falls in five broad readable panels. Materials: Wine-red silk with muted coral undersides; Dark gold clasp and staff fittings; Warm ivory embroidery concentrated on large edges. Show front, three-quarter and gameplay-distance silhouettes with relaxed hands and a readable weapon; include one action key pose. Purposeful expressive face, credible anatomy and fitted cloth. Original mythology-inspired fiction; no commercial-game assets, copied costume or claim of historical reconstruction. Separate concept painting from production mesh.

[Source/invention record](../research/CREATIVE_HERO_SOURCES.md) · [Machine-readable catalogue](../../assets/design/hero-codex.json)
