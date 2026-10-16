# Fourteen-hero mechanics and animation review

Reviewed 2026-10-16 against the current protocol-2 source, all 42 ability definitions, the renderer, animation authoring code and all fourteen actual hero GLBs. All fourteen binary hashes match `art/hero-assets.json`; each contains the nine required clips, including separate Q/E/R tracks (126 tracks total). This is a source/binary consistency review, with targeted playback-policy tests. Native animation quality, perceived fairness and human competitive balance remain separate checks.

The [168-match protocol-2 matrix](BALANCE_CHECK.md) remains applicable because this pass changes presentation and input observability, not authority. Its 86 Sun / 82 Moon result and per-hero spread are bot-policy observations. No health, damage, speed or cooldown was changed to equalize that table.

## Base statistics and visible scale

Primary DPS below is damage divided by authored fire interval, before tick quantization, travel, accuracy, cover, upgrades or interruptions. It is a comparison of definitions, not measured match damage. Every hero shares a 0.65 m movement radius and a projectile-hit sphere of radius 0.95 m centred 1.1 m above the actor origin. Cosmetic body height does not silently alter the hit volume.

| Hero | Health | Speed, m/s | Nominal primary DPS | Model height, m |
|---|---:|---:|---:|---:|
| Rama | 300 | 7.2 | 56.3 | 1.85 |
| Ravana | 390 | 6.4 | 50.0 | 1.97 |
| Arjuna | 275 | 7.7 | 57.1 | 1.86 |
| Duryodhana | 410 | 6.2 | 52.7 | 1.91 |
| Hanuman | 350 | 7.6 | 50.0 | 2.02 |
| Karna | 315 | 6.8 | 54.5 | 1.90 |
| Bhima | 400 | 6.4 | 50.9 | 2.08 |
| Meghnad | 285 | 7.8 | 55.0 | 1.87 |
| Sita | 330 | 6.8 | 42.2 | 1.75 |
| Draupadi | 340 | 6.5 | 41.7 | 1.78 |
| Subhadra | 315 | 7.2 | 48.9 | 1.73 |
| Hidimbi | 375 | 6.8 | 48.0 | 1.94 |
| Chitrangada | 350 | 7.5 | 52.2 | 1.80 |
| Ulupi | 320 | 7.0 | 43.5 | 1.82 |

Three power ranks increase basic damage by 51% and ability power by 36%. Three tempo ranks increase primary firing frequency by 36%; they do not shorten ability cooldowns. Three vitality ranks add 195 maximum health. These bounded, shared formulas preserve kit differences; healing and shields also receive the power multiplier. Haste multiplies movement by 1.25, slow by 0.55; matching effects refresh their duration instead of multiplying repeatedly.

## All forty-two slots

Values are unupgraded. `d` is targeting/projectile travel range; `r` is area radius; distances are metres. `CD` is cooldown in seconds. Slow damage is the nominal full-duration budget, spread over time; a target leaving the zone or taking cover receives less. Movement abilities inflict no landing damage unless explicitly listed. Summon power is damage per sentinel projectile, not an instant hit.

| Hero | Q | E | R |
|---|---|---|---|
| Rama | Steady Arrow: 54 projectile, d26; CD9 | Measured Step: dash10; CD12 | Dawn Volley: 3 × 32 projectiles, d28, 1 s locked preparation; CD44 |
| Ravana | Tenfold Guard: 48 shield, r4, 4 s; CD11 | Commanding Circle: 35 damage + pull, d20/r5; CD16 | Crownfire: 90 damage, r7; CD48 |
| Arjuna | Converging Volley: 38 forward fan, d18; CD8 | New Angle: dash12; CD11 | One Clear Line: 88 projectile, d28; CD42 |
| Duryodhana | Mace Shock: 48 forward fan, d10; CD10 | Hold the Ground: 55 shield, r4, 4 s; CD15 | Iron Crescent: 92 forward cone, d12; CD46 |
| Hanuman | Windward Leap: leap14; CD9 | Bring Them Home: 48 heal, r5; CD14 | Mountain Pulse: 0.7 s prepare + 0.45 s travel up to14, landing65 damage/45 heal, r7; CD45 |
| Karna | Sunshaft: 62 projectile, d27; CD11 | Borrowed Dawn: 42 shield, r4, 3 s; CD16 | Solar Reprisal: 95 damage, r6; CD50 |
| Bhima | Heavy Sweep: 52 forward cone, d10; CD10 | Closing Stride: leap12; CD15 | Thunder at Your Feet: 92 damage, r8; CD48 |
| Meghnad | Cloud Snare: 28 over3 s, d22/r4 + slow; CD12 | Storm Step: dash13; CD12 | Gathered Squall: 78 forward fan, d22; CD43 |
| Sita | Grove Renewal: 50 heal, r5; CD10 | Rooted Path: 25 over4 s, d18/r5 + slow; CD15 | Shelter of Mithila: 0.8 s prepare, 70 initial shield +9 heal/s for6 s, r8; CD46 |
| Draupadi | Circle of Resolve: 46 shield, r5, 4 s; CD10 | Stand Accountable: 30 damage + pull, d19/r5; CD17 | Unbroken Assembly: 95 heal, r8; CD48 |
| Subhadra | Signal Lance: 44 projectile, d24; CD9 | Rally Close: 42 heal, r4; CD13 | Twin Standards: two105-HP sentinels, 28 per shot, 9 s; CD48 |
| Hidimbi | Forest Boundary: 27 over4 s, d16/r5 + slow; CD12 | Canopy Guard: 50 shield, r5, 4 s; CD16 | Grove Watch: two105-HP sentinels, 32 per shot, 9 s; CD52 |
| Chitrangada | Crossing Step: dash12; CD9 | Spear Arc: 44 forward cone, d11; CD12 | Defender’s Vow: 80 shield, r6, 4 s; CD44 |
| Ulupi | River Draw: 28 damage + pull, d19/r4; CD12 | Cooling Current: 44 heal, r5; CD14 | Naga Basin: 72 over6 s, d23/r7 + slow; CD46 |

All cooldowns start on acceptance. Rejected commands do not create an ability event. Replayed command IDs return the original receipt without repeating the payload. The independent content reviewer found no concrete mismatch in the 42 descriptions or associated guides.

## Readability, animation and counters

| Family | Current authoritative rule and visible cue | Counter or limit |
|---|---|---|
| Primary / bolt / line | Non-homing, non-piercing projectiles; observed shot triggers weapon animation. Bolts use speed38/radius0.75; lines speed62/radius0.5. | Aim, lateral movement, walls and intervening enemies matter. A clip is presentation; it does not decide hit timing. |
| Fan / cone | Instant forward damage at accepted cast; rendered sector uses the same yaw, range and angular threshold (fan approximately151°, cone approximately113°). | Be outside the sector or behind solid cover before acceptance. The subsequent0.7 s footprint is aftermath, not a windup warning. |
| Nova / pull | Instant circle damage; pull moves surviving actors toward its selected centre by at most6 m, collision-limited. | Leave the radius or use clear-sight-blocking cover. Ordinary damage does not cancel these already-applied effects. |
| Heal / ward | Instant self-centred allied area, clear sight required; distinct cross/shield markings. Shields use one maximum pool with expiry, not additive layers. | Spread the opposing group, force movement or consume the shield. Depleted protection must not remain visually active. |
| Dash / ordinary leap | Immediate collision-limited horizontal repositioning; leap adds an airborne arc. No extra damage, haste or invulnerability. | Walls stop travel; opponents can attack the destination. |
| Slow zone | Fixed marked zone applies damage over time and0.55 movement multiplier, with0.5 s slow refresh. | Leave the zone or break its clear sight; no immobilization or hidden stun. |
| Summon | Two temporary allied sentinels, bounded placement and9 s expiry; ordinary damage/cover apply. | Defeat them or disengage. Their defeat grants no score or gold. They can fail to appear if the global actor cap/valid placement prevents it. |
| Three timed Rs | Server-owned preparation/target metadata draws the warning. Movement, primary fire and other casts are locked; Hanuman travel remains authoritative. | Dodge the warned geometry, use cover or defeat the caster before payload. Damage alone does not interrupt. Completed Sita sanctuary persists after her death. |

Ordinary mobile casts retain an upper-body action layer so locomotion continues. The three movement-locked casts now select their authored full-body `cast3` track, including hips/knees; Hanuman retains it while travelling. Entry/rejoin seeks once using authoritative elapsed time, clamped to the real clip duration. Subsequent snapshots do not restart it. Death and finished-match state release the cast path. On release it returns to normal locomotion; this deliberately does not promise every post-release recovery frame is displayed.

## Concrete findings and bounded changes

1. **Depleted shield appearance:** the prior mesh condition also accepted a positive ward timer after the shield pool reached zero. World now follows actual remaining shield, matching the HUD.
2. **Resumed R selecting Q body motion:** cached event-derived slot could remain zero after reconnect baseline discarded the old start event. World now prefers the active authoritative cast slot.
3. **Missing planted/landing body pose:** the old upper-body mask discarded the hips/knees from locked-R clips, and airborne Hanuman selected generic jump. The new full-body path fixes that selection without rebuilding the assets or changing combat.
4. **Delayed timed-R replay:** an actual capture found that a start receipt could reach model playback after the authoritative cast ended and replay `cast3` in the upper layer. Timed abilities now animate exclusively from active cast state; their receipt counters are still consumed. This also handles a whole cast occurring between rendered observations. Ordinary abilities and fresh shot feedback remain event-driven.

Eleven playback-policy tests cover all three actual simulated casts, missing-event/rejoin seeking, repeated snapshots, Hanuman airborne continuity and landing, real lethal cancellation, match-end cancellation, bounded seek values, late/missed timed-cast receipts and all39 ordinary event-driven slots. Targeted lint, YUGA typecheck and whitespace checks pass. Independent animation-owner and QA source reviews found no blocking flow defect. The capture harness separately preserves initial snapshot-before-render boundaries and checks actual presented lower-body poses plus absence of late replay. The corrected native capture remains a separate visual acceptance gate.

The existing small bot sample flags Meghnad/Ulupi and Karna/Subhadra for mirrored human trials, not immediate stat edits. Test objective contribution, effective healing/shield use, landed and avoided damage, summon survival, upgrade decisions and camp rotations together. Most scripted games finish on score; do not infer that human match pacing or comeback opportunities are already balanced.

Sources: [hero definitions](../shared/heroes.ts), [simulation](../shared/simulation.ts), [hero guide](../shared/hero-guide.ts), [model playback](../client/hero-models.ts), [cast policy](../client/hero-cast-playback.ts), [world effects](../client/world.ts), [telegraphs](../client/cast-effects.ts), [animation authoring](../art/pipeline/animations.py), [asset manifest](../art/hero-assets.json), [playback tests](../tests/hero-cast-playback.test.ts).
