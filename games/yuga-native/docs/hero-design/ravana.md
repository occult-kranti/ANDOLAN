# Ravana — A moving citadel of ten decisions

Stable ID: `ravana` · Vanguard · source motif `R1`. Original mythology-inspired fiction: an art/animation brief and native-practice proposal, not an accepted production model or a canonical power.

## Silhouette, materials and motion

Broad trapezoid mantle, low deliberate centre of mass and ten crown facets contained within one readable head outline.

Materials: Oxidized violet bronze plates with brass cut edges; Black plum velvet beneath layered armour; Small amber inset stones; no all-over emissive skin.

Commands begin at the fingers then carry through forearms and mantle; one heavy step precedes a planted ring-blade release.

Body/accent: `#ad71e8` / `#fbc86d`. Separate Sun triangle/Moon bracket; costume never identifies team.

## Current browser kit — retained

Health 390; speed 6.4 m/s. Primary is an aimed projectile: 26 damage every 0.52 s, projectile speed 34 m/s. Weapon: chakram. Unupgraded starting values, not measured balance.

| Slot / name | Kind | Cooldown (s) | Power field | Range / radius (m) | Duration field (s) |
| --- | --- | --- | --- | --- | --- |
| Q · Tenfold Guard | `ward` | 11 | 48 | 8 / 4 | 4 |
| E · Commanding Circle | `pull` | 16 | 35 | 20 / 5 | 2 |
| R · Crownfire | `nova` | 48 | 90 | 8 / 7 | 2 |

Fields retain their simulator meanings: movement power is not landing damage; projectile radius is not an explosion; summon duration 3 produces nine-second sentinels. Only Rama/Hanuman/Sita R currently have authoritative preparation. [Timing boundary](README.md#runtime-contract).

## Primary and Q/E/R presentation

**Primary — `ravana.primary`:** A thin asymmetric ring blade leaves a short violet crescent; the opening in its centre remains visible. Current primary has no authored gameplay windup; show the accepted muzzle/string release immediately, then its visible collidable projectile.

**Q — Tenfold Guard (`ravana.q`):** Ten small faceted plates latch into a low protective rosette around allied silhouettes, leaving faces and weapons open.

Counter: Separate protected allies or wait for shield expiry; the ward is not invulnerability.

**E — Commanding Circle (`ravana.e`):** A broken ten-point ground seal tightens toward the aimed centre; inward bars communicate pull, never a solid prison.

Counter: Leave the aimed radius or use solid cover; solid obstacles constrain displacement.

**R — Crownfire (`ravana.r`):** Ten brass crown petals rise around the caster as a low iris, fold inward in sequence, then open into one violet-gold ground blast. All ten are one attack, not ten damage pulses.

Counter: Leave the seven-metre caster-centred footprint or put solid cover between caster and target; pressure the slow approach.

## Native ultimate demonstration contract

`ravana.r.v1` · shape `ten_crown_iris` · family `radial` · anchor `caster`. **No gameplay mutation.** Browser definitions stay unchanged.

Prepare 0.9 s → travel 0 s → active appearance 0.8 s → recovery 0.7 s. Nominal contact/arrival: 0.9 s. Classification: `proposed_native_demo_windup`.

Presentation envelope: range 8 m, radius 7 m, width 14 m, height 5 m. These are composition bounds; authority defines actual collision/damage. Exactly 0 projectile form(s) and 0 summon form(s); ornamental geometry adds no hitbox.

Per-cast caps: 48 instances, 160 particles, 1 light, 3 voices, 16 draw calls, 18000 triangles and 2.5 s lifetime. Provisional engineering caps, not measured GPU performance.

Low settings: Keep exact footprint, team symbol, release and expiry. Drop loose particles, secondary contour layers, point lights and ornamental distortion.

Reduced motion: No camera shake, screen flash or full-screen overlay; replace orbiting ornaments with stationary outlines.

Audio: One short onset, one release/arrival and optional low sustain; silence never removes the visible warning.

## Review focus

Ten heads rendered literally would enlarge the target silhouette and obscure aim; use crown facets instead.

Require readable face/weapon at gameplay distance, grounded support feet, actual hand/socket contact, clean cloth and continuous start/stop/aim/cast/recovery footage. Review both teams, day/night, low effects and overlap. A valid catalogue or still concept cannot pass that gate.

## Concept generation brief

Original YUGA character concept: Ravana, A moving citadel of ten decisions. Broad trapezoid mantle, low deliberate centre of mass and ten crown facets contained within one readable head outline. Materials: Oxidized violet bronze plates with brass cut edges; Black plum velvet beneath layered armour; Small amber inset stones; no all-over emissive skin. Show front, three-quarter and gameplay-distance silhouettes with relaxed hands and a readable weapon; include one action key pose. Purposeful expressive face, credible anatomy and fitted cloth. Original mythology-inspired fiction; no commercial-game assets, copied costume or claim of historical reconstruction. Separate concept painting from production mesh.

[Source/invention record](../research/CREATIVE_HERO_SOURCES.md) · [Machine-readable catalogue](../../assets/design/hero-codex.json)
