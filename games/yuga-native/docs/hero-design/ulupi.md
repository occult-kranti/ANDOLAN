# Ulupi — Two rivers tied into one clear boundary

Stable ID: `ulupi` · Keeper · source motif `M1`. Original mythology-inspired fiction: an art/animation brief and native-practice proposal, not an accepted production model or a canonical power.

## Silhouette, materials and motion

Flowing grounded silhouette, wave crest, scale-edged collar and water-ring staff; humanoid legs and face stay readable beneath layered blue-green cloth.

Materials: Petrol-blue silk with turquoise underside; Pearlescent shell-like collar trim kept below bloom; Dark polished wood and wet-looking accents only on effects.

Circular forearm gestures anchored by quiet hips and planted feet; staff rolls through a real grip rather than floating.

Body/accent: `#4cb3c0` / `#d6f6e4`. Separate Sun triangle/Moon bracket; costume never identifies team.

## Current browser kit — retained

Health 320; speed 7 m/s. Primary is an aimed projectile: 20 damage every 0.46 s, projectile speed 35 m/s. Weapon: staff. Unupgraded starting values, not measured balance.

| Slot / name | Kind | Cooldown (s) | Power field | Range / radius (m) | Duration field (s) |
| --- | --- | --- | --- | --- | --- |
| Q · River Draw | `pull` | 12 | 28 | 19 / 4 | 2 |
| E · Cooling Current | `heal` | 14 | 44 | 8 / 5 | 3 |
| R · Naga Basin | `slow` | 46 | 72 | 23 / 7 | 6 |

Fields retain their simulator meanings: movement power is not landing damage; projectile radius is not an explosion; summon duration 3 produces nine-second sentinels. Only Rama/Hanuman/Sita R currently have authoritative preparation. [Timing boundary](README.md#runtime-contract).

## Primary and Q/E/R presentation

**Primary — `ulupi.primary`:** A small water-ring bolt with an open centre and short falling droplets; no homing. Current primary has no authored gameplay windup; show the accepted muzzle/string release immediately, then its visible collidable projectile.

**Q — River Draw (`ulupi.q`):** Two inward currents trace the aimed pull area; actual displacement remains collision-limited.

Counter: Leave the aimed radius or use solid cover; solid obstacles constrain displacement.

**E — Cooling Current (`ulupi.e`):** A low outward water braid marks nearby healing; no water immunity or revival implied.

Counter: Force allies apart and apply pressure outside the healing radius; no resurrection.

**R — Naga Basin (`ulupi.r`):** Two translucent water serpents braid around the basin edge, dip through matching gaps and shed a thin inward current over the floor. Their heads face inward to mark slowdown; the middle stays transparent. Both are ornaments of one six-second zone, not summoned creatures.

Counter: Leave or avoid the seven-metre basin, use another route and keep cover between opponents; there is no drowning, wall or water invulnerability.

## Native ultimate demonstration contract

`ulupi.r.v1` · shape `naga_river_knot` · family `ground_zone` · anchor `aimed_ground`. **No gameplay mutation.** Browser definitions stay unchanged.

Prepare 0.9 s → travel 0 s → active appearance 6 s → recovery 0.65 s. Nominal contact/arrival: 0.9 s. Classification: `proposed_native_demo_windup`.

Presentation envelope: range 23 m, radius 7 m, width 14 m, height 4.5 m. These are composition bounds; authority defines actual collision/damage. Exactly 0 projectile form(s) and 0 summon form(s); ornamental geometry adds no hitbox.

Per-cast caps: 48 instances, 160 particles, 1 light, 3 voices, 16 draw calls, 18000 triangles and 7.65 s lifetime. Provisional engineering caps, not measured GPU performance.

Low settings: Keep exact footprint, team symbol, release and expiry. Drop loose particles, secondary contour layers, point lights and ornamental distortion.

Reduced motion: No camera shake, screen flash or full-screen overlay; replace orbiting ornaments with stationary outlines.

Audio: One short onset, one release/arrival and optional low sustain; silence never removes the visible warning.

## Review focus

Serpent opacity, refractive distortion and looping heads must not hide targets or imply independent hitboxes.

Require readable face/weapon at gameplay distance, grounded support feet, actual hand/socket contact, clean cloth and continuous start/stop/aim/cast/recovery footage. Review both teams, day/night, low effects and overlap. A valid catalogue or still concept cannot pass that gate.

## Concept generation brief

Original YUGA character concept: Ulupi, Two rivers tied into one clear boundary. Flowing grounded silhouette, wave crest, scale-edged collar and water-ring staff; humanoid legs and face stay readable beneath layered blue-green cloth. Materials: Petrol-blue silk with turquoise underside; Pearlescent shell-like collar trim kept below bloom; Dark polished wood and wet-looking accents only on effects. Show front, three-quarter and gameplay-distance silhouettes with relaxed hands and a readable weapon; include one action key pose. Purposeful expressive face, credible anatomy and fitted cloth. Original mythology-inspired fiction; no commercial-game assets, copied costume or claim of historical reconstruction. Separate concept painting from production mesh.

[Source/invention record](../research/CREATIVE_HERO_SOURCES.md) · [Machine-readable catalogue](../../assets/design/hero-codex.json)
