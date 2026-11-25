# Vanara Sena · combat and animation script

This is a design and review script for the initial 5v5 version. The parameters in the [handoff](README.md) are starting values; distinguish authored intent from effects actually captured in the packaged build. The game runs the Rust combat authority at **20 Hz**. Tick zero is the server's accepted action; a 60 fps review has three display frames per simulation tick only when the display cadence is exactly 60 fps. Rendering can interpolate or arrive late; it never decides damage.

## Tactical role

Hanuman briefly denies a small, visible patch of ground while retaining the ability to reposition after recovery. The intent is to discourage a stationary hold or protect a rotation, not to let summoned creatures track an enemy behind cover. The effect is equally usable as an entrance warning, a way to help an ally disengage or a prompt to move an opponent off a corner. Because each qualifying enemy can leave the field and multiple players can be inside it, designers must test both single-duel counterplay and crowded 5v5 readability.

The five guardian silhouettes are an art-direction target for a **single authoritative field**. They are not actors, minions, decoys, vision providers, body blockers or independently controlled attackers. Their apparent weapons and paths do not independently calculate damage. Until a separate rigged character-and-AI system exists, use language such as “spectral guardians” or “echoes.”

## Input and authoritative beats

| Time from accepted cast | Server rule | Presentation and animation intent |
| --- | --- | --- |
| Before acceptance | The player previews a finite ground point within 10 m, on allowed ground and with an unobstructed cast path. An invalid point, an unavailable or airborne caster, an action lock or cooldown rejects the cast without spending it. | Show a legible 3 m boundary, center marker and text/shape feedback for valid versus unavailable placement. Keyboard **V** quick-casts at the current valid cursor; a selected HUD button may support a deliberate click. Do not leak a hidden target. |
| Tick 0 · 0.00 s | Authority creates one cast ID, pins origin/target and starts the 20 s cooldown. | Hanuman settles his stance; an aspirational pluck-and-breath gesture is the animation brief. First runtime may instead reuse the existing `cast2` clip, in which case do not imply a bespoke pluck is already playable. Wind lines and a few petals communicate the impending zone without obscuring a defender. |
| Ticks 1–11 · before 0.60 s | The cast is committed but Hanuman is still vulnerable. A knockout clears the action; no invulnerability or damage immunity is conferred. | Draw a clear countdown/approach around the fixed target. The five guardians gather in an open crescent with enough negative space to see opponents and the edge. A separate Blender scene can study plucking hair and breath timing; it is not an integrated clip until verified. |
| Tick 12 · 0.60 s | Impact at the fixed point applies **12** damage once to each eligible enemy in range/height and with an unobstructed center-to-recipient path. Allies receive no damage. Shields can absorb damage according to existing authority. | A concise non-flashing landing pulse and five brief inward strokes mark one area impact. Trigger contact accents only from real authority receipts; a missed cast should not create false hit markers. |
| Ticks 13–52 · 0.65–2.60 s | For up to 40 ticks, eligible enemies take **0.4 damage/tick** (8/s). Eligibility is reevaluated as they move. A full uninterrupted exposure is 12 + 40 × 0.4 = **28** before shields. | Echoes orbit or strike in staggered pairs as a readability layer, but the server's field, not individual avatar contact, governs damage. Keep the boundary stable and ease out decorative effects while the authoritative field remains live. |
| Tick 20 · 1.00 s | Body recovery ends, so the actor can begin another eligible action while the field remains. | Settle the shoulder and tail without teleporting the gada or feet. A later motion or cast must not move the first field's center. |
| Tick 52 · 2.60 s | The field ends after the final active tick. A caster knockout clears that caster's remaining casts; same-tick ordering is governed by the authoritative match implementation. | Guardians and petals dissipate, leaving no invisible damage area. Fade audio and visual accents without presenting disappearance as a claim about literal liberation or death. |
| Tick 400 · 20.00 s | The cooldown begun at acceptance has elapsed. | The V button is ready again; an accessible text/icon change accompanies color. |

The exact event sequence should be checked against the implementation (`begin`, `release`, `impact`, subsequent `tick`, `recovery`, `end`) and its real frame/receipt data. Do not substitute the table for a captured run, especially around same-tick defeat, pause or delayed snapshots.

## Presentation grammar

**Art.** Begin with Hanuman's recognizable copper mane, gada and tilak. Use saffron-gold and wind as the summoning palette, with a consistent team-coded boundary and non-color shape cue. The five forms should have readable but deliberately ethereal Vanara silhouettes, not generic lane soldiers with a different label. Their crescent is an original composition for YUGA, not a reconstruction of a specific ancient military array. The short-lived effects must not conceal a target, projectile line or site interaction.

**Motion.** Preserve hand/weapon contact and a supported stance. If a purpose-built animation is integrated later, review pluck, breath, release, follow-through and recovery from front and gameplay shoulder cameras; do not translate the simulation capsule from the animation. Give each spirit a nonidentical but synchronized arc, with a defined start, landing and dissolve. The visual formation must match the accepted field's position and duration even when the caster begins another action.

**Audio and captions.** A short conch-like tone, soft bell and low hand-drum rhythm can suggest the call, provided any sounds used have provenance and fit the mix. A cast cue and field/expiry cue should be distinguishable, directional where feasible, and independently adjustable or muteable. Captions can say “Vanara Sena forms” and “Vanara Sena fades” rather than inventing a Sanskrit prayer or claiming an unsourced ritual text. Human listening and cultural review are separate gates.

**Accessibility.** Communicate the warning and end through boundary shape, icon/text and timing as well as saffron/ally/enemy colors. Keep the telegraph in reduced-effects mode; avoid flashing, excessive screen bloom or camera movement. Do not require audio for the escape cue. Keep gameplay-relevant silhouettes visually distinct from players and interactables.

## Example 5v5 beat

Hanuman's team is rotating through a narrow dry route. He marks a visible patch near the far end, 8 m away. A defender hears/sees the cast, steps behind cover or leaves the 3 m disk during the 0.60 s windup, and avoids the impact. A second defender remains in the valid area for one second after impact and receives the initial damage plus approximately 8 further damage, subject to shields. At the 1.00 s recovery point Hanuman can move again, but the accepted field stays at its original ground point until it expires or is cleared by the authority. Allies inside it receive no damage.

## Existing-kit combination studies

The following are **timing hypotheses**, not new bonuses or tested outcomes. They refer to the established Hanuman rules in the [previous combat pass](../combat-panel-2026/HANUMAN_RAMA.md) and assume each later action is ready and legally accepted.

- **Sena → protective fan.** V starts at tick 0; if Q begins at the V body-unlock tick 20, its existing shield release is tick 27. The fixed Sena zone continues until tick 52 unless cleared. The shield has its own forward fan, recipient and cover checks; an ally near a spirit is not automatically protected.
- **Sena → vault.** An E started at tick 20 normally releases at tick 24 and, on clear full travel, lands at tick 33. Terrain can shorten it and a knockout interrupts it; there is no promised invulnerability. The original Sena target must remain fixed while Hanuman moves.
- **Sena → Mountain Pulse.** X started at tick 20 reaches its existing impact at tick 43, while Sena would still be active. Both ground targets, visibility paths and recipients are independently validated. Any damage or healing comes from their normal separate rules; there is no automatic 2.5× finisher, stack consumption or stun.

For each proposed sequence, compare a defender who exits or uses cover, simulate interruption before each release, and verify that a late packet cannot move an already accepted area. Human players should be able to recognize both overlapping boundaries and respond to them.

## Pseudocode contract

```text
on cast request(seat, slot=5, target):
    reject unless seat is a living Hanuman, available, grounded,
                  target finite/allowed/visible, distance <= 10m
    cooldown_until = current_tick + 400
    create cast(id, fixed_target, start_tick=current_tick)
    emit begin(id, start_tick, fixed_target)

on each authority tick for a live cast:
    age = current_tick - start_tick
    if age == 12: emit release; apply 12 to each eligible enemy; emit impact receipts
    if 12 < age <= 52: apply 8/20 to each eligible enemy; emit accepted tick receipts
    if age == 20: emit recovery
    if age == 52: emit end and discard the cast
    on caster knockout: discard its remaining casts under existing match ordering

eligible(enemy) = alive AND enemy_team AND overlaps field height AND
                  distance(enemy, fixed_target) <= 3m AND
                  clear_line(fixed_target, enemy.position)
```

The pseudocode describes intended behavior, not a replacement for executable tests. The score system must consume actual damage/knockout state rather than visual-echo animation.

## Test and balance questions

- Verify the range/radius boundaries and epsilon, cover at placement and recipient, vertical overlap, ally immunity, cooldown start and expiry, interruption before/after release, consecutive casts, overlapping allied/opposing fields, respawn/reset and malformed slot requests.
- Replay identical ten-seat inputs through native and Wasm authority, then check local and remote 3D presentation from both teams. Test slow/delayed snapshots and repeated event IDs; a renderer must not duplicate an impact or sound on replay.
- With five Hanumans, five simultaneous full-duration fields could nominally deliver 140 damage to an enemy who remains in all of them before shields. That is a design scenario, not a measured result; assess overlap, visual clutter and escape routes in human playtests before release.
- Track cast acceptance, actual recipients, movement out of the field, damage after shields, knockouts, frame-time distribution and player comprehension. Record sample size, skill mix, network conditions and confidence instead of treating these metrics as proven balance.
