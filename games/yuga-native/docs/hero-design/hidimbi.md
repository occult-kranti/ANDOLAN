# Hidimbi — The forest that chooses to stand beside you

Stable ID: `hidimbi` · Vanguard · source motif `M1`. Original mythology-inspired fiction: an art/animation brief and native-practice proposal, not an accepted production model or a canonical power.

## Silhouette, materials and motion

Powerful broad leaf mantle with a clear shoulder line, braided crest and forked spear; expressive humanoid face, no generic monster replacement.

Materials: Deep moss coarse cloth and bark-textured armour; Dark copper fasteners and carved wooden spear; Pale leaf undersides used only for shape contrast.

Low stable steps with quick protective turns; spear and shoulders counterbalance; leaf layers trail then settle with minimal jitter.

Body/accent: `#7da96e` / `#f1d6a3`. Separate Sun triangle/Moon bracket; costume never identifies team.

## Current browser kit — retained

Health 375; speed 6.8 m/s. Primary is an aimed projectile: 24 damage every 0.5 s, projectile speed 31 m/s. Weapon: spear. Unupgraded starting values, not measured balance.

| Slot / name | Kind | Cooldown (s) | Power field | Range / radius (m) | Duration field (s) |
| --- | --- | --- | --- | --- | --- |
| Q · Forest Boundary | `slow` | 12 | 27 | 16 / 5 | 4 |
| E · Canopy Guard | `ward` | 16 | 50 | 8 / 5 | 4 |
| R · Grove Watch | `summon` | 52 | 32 | 10 / 4 | 3 |

Fields retain their simulator meanings: movement power is not landing damage; projectile radius is not an explosion; summon duration 3 produces nine-second sentinels. Only Rama/Hanuman/Sita R currently have authoritative preparation. [Timing boundary](README.md#runtime-contract).

## Primary and Q/E/R presentation

**Primary — `hidimbi.primary`:** A thorn-shaped aimed bolt with a small paired-leaf trail; spear silhouette does not introduce melee collision. Current primary has no authored gameplay windup; show the accepted muzzle/string release immediately, then its visible collidable projectile.

**Q — Forest Boundary (`hidimbi.q`):** Root footprints define a slow zone with obvious route gaps; no new collision blocks an exit.

Counter: Leave the visible zone or choose another route; the area is not a wall.

**E — Canopy Guard (`hidimbi.e`):** Broad leaf scales overlap beside allied silhouettes as a short shield, then curl outward at expiry.

Counter: Separate protected allies or wait for shield expiry; the ward is not invulnerability.

**R — Grove Watch (`hidimbi.r`):** Exactly two walking grove sentinels rise from split seed shells; a sparse canopy procession links them visually without filling the floor. Nine-second branch rings shrink around each actual summon. Decorative roots never add extra attackers.

Counter: Kite or defeat the two temporary units, outlast nine seconds and rotate away from her strongest held objective.

## Native ultimate demonstration contract

`hidimbi.r.v1` · shape `walking_grove_pair` · family `summon_pair` · anchor `caster`. **No gameplay mutation.** Browser definitions stay unchanged.

Prepare 1 s → travel 0 s → active appearance 9 s → recovery 0.6 s. Nominal contact/arrival: 1 s. Classification: `proposed_native_demo_windup`.

Presentation envelope: range 10 m, radius 4 m, width 8 m, height 5 m. These are composition bounds; authority defines actual collision/damage. Exactly 0 projectile form(s) and 2 summon form(s); ornamental geometry adds no hitbox.

Per-cast caps: 48 instances, 160 particles, 1 light, 3 voices, 16 draw calls, 18000 triangles and 10.7 s lifetime. Provisional engineering caps, not measured GPU performance.

Low settings: Keep exact footprint, team symbol, release and expiry. Drop loose particles, secondary contour layers, point lights and ornamental distortion.

Reduced motion: No camera shake, screen flash or full-screen overlay; replace orbiting ornaments with stationary outlines.

Audio: One short onset, one release/arrival and optional low sustain; silence never removes the visible warning.

## Review focus

Treat her as an individual guardian, not a racialized monster; forest density must never obscure players or fake a wall.

Require readable face/weapon at gameplay distance, grounded support feet, actual hand/socket contact, clean cloth and continuous start/stop/aim/cast/recovery footage. Review both teams, day/night, low effects and overlap. A valid catalogue or still concept cannot pass that gate.

## Concept generation brief

Original YUGA character concept: Hidimbi, The forest that chooses to stand beside you. Powerful broad leaf mantle with a clear shoulder line, braided crest and forked spear; expressive humanoid face, no generic monster replacement. Materials: Deep moss coarse cloth and bark-textured armour; Dark copper fasteners and carved wooden spear; Pale leaf undersides used only for shape contrast. Show front, three-quarter and gameplay-distance silhouettes with relaxed hands and a readable weapon; include one action key pose. Purposeful expressive face, credible anatomy and fitted cloth. Original mythology-inspired fiction; no commercial-game assets, copied costume or claim of historical reconstruction. Separate concept painting from production mesh.

[Source/invention record](../research/CREATIVE_HERO_SOURCES.md) · [Machine-readable catalogue](../../assets/design/hero-codex.json)
