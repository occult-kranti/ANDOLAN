# Chitrangada — The crossing that becomes a promise

Stable ID: `chitrangada` · Vanguard · source motif `M1`. Original mythology-inspired fiction: an art/animation brief and native-practice proposal, not an accepted production model or a canonical power.

## Silhouette, materials and motion

Athletic spear-duelist stance, crescent spear, braided knot and a short segmented mantle that exposes purposeful leg motion.

Materials: Burnt-coral cloth with pale sand lining; Brushed copper and dark steel spear; Flexible dark leather scales at joints.

Balanced crossing steps, precise hand transfers and hips that lead the spear arc; planted foot remains stable during oath gestures.

Body/accent: `#ca785d` / `#ffe0a5`. Separate Sun triangle/Moon bracket; costume never identifies team.

## Current browser kit — retained

Health 350; speed 7.5 m/s. Primary is an aimed projectile: 24 damage every 0.46 s, projectile speed 37 m/s. Weapon: spear. Unupgraded starting values, not measured balance.

| Slot / name | Kind | Cooldown (s) | Power field | Range / radius (m) | Duration field (s) |
| --- | --- | --- | --- | --- | --- |
| Q · Crossing Step | `dash` | 9 | 25 | 12 / 3 | 2 |
| E · Spear Arc | `cone` | 12 | 44 | 11 / 4 | 2 |
| R · Defender’s Vow | `ward` | 44 | 80 | 8 / 6 | 4 |

Fields retain their simulator meanings: movement power is not landing damage; projectile radius is not an explosion; summon duration 3 produces nine-second sentinels. Only Rama/Hanuman/Sita R currently have authoritative preparation. [Timing boundary](README.md#runtime-contract).

## Primary and Q/E/R presentation

**Primary — `chitrangada.primary`:** A narrow copper spear-light projectile with a small open crescent tail. Current primary has no authored gameplay windup; show the accepted muzzle/string release immediately, then its visible collidable projectile.

**Q — Crossing Step (`chitrangada.q`):** One clean crossing ribbon marks the collision-limited dash; no afterimage damage or invulnerability.

Counter: Predict the collision-limited endpoint; the dash has no added damage or invulnerability.

**E — Spear Arc (`chitrangada.e`):** A low crescent edge clearly sweeps the actual forward cone; its rear edge is open.

Counter: Move outside the forward cone, behind the caster or behind solid cover.

**R — Defender’s Vow (`chitrangada.r`):** Six open crescent plates cross once like a woven oath, then separate around nearby allies into thin shield arcs. The centre remains clear and a receding edge marks the four-second ward.

Counter: Spread allies away from the ward radius, wait out four seconds or attack after the crossing dash is spent; this is not a parry or reflection.

## Native ultimate demonstration contract

`chitrangada.r.v1` · shape `crossing_oath` · family `protection` · anchor `caster`. **No gameplay mutation.** Browser definitions stay unchanged.

Prepare 0.65 s → travel 0 s → active appearance 4 s → recovery 0.5 s. Nominal contact/arrival: 0.65 s. Classification: `proposed_native_demo_windup`.

Presentation envelope: range 8 m, radius 6 m, width 12 m, height 4 m. These are composition bounds; authority defines actual collision/damage. Exactly 0 projectile form(s) and 0 summon form(s); ornamental geometry adds no hitbox.

Per-cast caps: 48 instances, 160 particles, 1 light, 3 voices, 16 draw calls, 18000 triangles and 5.25 s lifetime. Provisional engineering caps, not measured GPU performance.

Low settings: Keep exact footprint, team symbol, release and expiry. Drop loose particles, secondary contour layers, point lights and ornamental distortion.

Reduced motion: No camera shake, screen flash or full-screen overlay; replace orbiting ornaments with stationary outlines.

Audio: One short onset, one release/arrival and optional low sustain; silence never removes the visible warning.

## Review focus

Do not borrow literal regional armour as an unsupported historical claim; keep each spear-hand transfer anatomically credible.

Require readable face/weapon at gameplay distance, grounded support feet, actual hand/socket contact, clean cloth and continuous start/stop/aim/cast/recovery footage. Review both teams, day/night, low effects and overlap. A valid catalogue or still concept cannot pass that gate.

## Concept generation brief

Original YUGA character concept: Chitrangada, The crossing that becomes a promise. Athletic spear-duelist stance, crescent spear, braided knot and a short segmented mantle that exposes purposeful leg motion. Materials: Burnt-coral cloth with pale sand lining; Brushed copper and dark steel spear; Flexible dark leather scales at joints. Show front, three-quarter and gameplay-distance silhouettes with relaxed hands and a readable weapon; include one action key pose. Purposeful expressive face, credible anatomy and fitted cloth. Original mythology-inspired fiction; no commercial-game assets, copied costume or claim of historical reconstruction. Separate concept painting from production mesh.

[Source/invention record](../research/CREATIVE_HERO_SOURCES.md) · [Machine-readable catalogue](../../assets/design/hero-codex.json)
