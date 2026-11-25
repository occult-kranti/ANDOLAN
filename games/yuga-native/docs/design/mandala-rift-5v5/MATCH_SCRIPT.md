# Rift Seal · proposed 5v5 match script

**Superseded objective proposal.** The newer [Ember Rite round contract](../ember-rite-5v5/ROUND_AND_TECH.md) uses a carried fire vessel, revised 4 s/3.5 s/40 s interactions, first-to-13 regulation and paired overtime. The route and map study remain useful. This older script is retained as a historical design, not the current objective specification or a playable mode.

This is a design for a future objective mode on Mandala Rift. The current playable Rust build is a hero-only knockout skirmish on the old map; it has no round, plant, defuse, portal or water-status logic yet. The proposed numbers are starting points for playtesting, not measured balance.

## Player-facing flow

1. **Assemble.** Ten players enter a private room, five Sun and five Moon. A hero select shows the two currently supported heroes until the roster grows. Duplicates can be allowed in early tests; competitive roster restrictions need a separate decision.
2. **Prepare.** A 10-second protected planning phase identifies attacking and defending sides, the carrier and sites A/B. There are no autonomous soldier, police, royal-vehicle or jungle-creature waves. Hero abilities start with the agreed round loadout; equipment economy is not yet specified.
3. **Approach.** A 90-second round clock starts. Attackers can use the river jungle, central Mandapa or eastern Bazaar. Defenders choose where to hold and can rotate. Both folded links are available to either team and have matched audiovisual cues. No portal grants hidden vision or damage through its surface.
4. **Carry and place.** One attacker holds the Rift Seal. On defeat it drops at the last valid floor point and can be recovered by an attacker after a one-second hold. At site A or B, the carrier holds interact for three seconds within the marked plant zone. Releasing, taking damage, being defeated or leaving the zone cancels progress. Plant must complete before the round clock expires.
5. **Defend or disarm.** A completed plant starts a 35-second visible timer. Defenders hold interact for five uninterrupted seconds to disarm; additional defenders do not accelerate it. Damage, release, defeat or leaving range cancels progress. Elimination does not erase a planted objective: if all attackers fall, defenders still need to disarm. If all defenders fall after planting, attackers win the round. If all attackers fall before planting, defenders win. A simultaneous pre-plant team wipe favors defenders; a simultaneous post-plant wipe favors attackers because no defender remains to disarm.
6. **Resolve and reset.** A completed disarm gives defenders the round. An armed timer reaching zero gives attackers the round. Before a plant, expiration gives defenders the round. Freeze the objective once resolved, show the reason and score, clear temporary effects and reset all heroes and world interactions for the next round. There are no in-round respawns in this proposed mode.
7. **Switch sides.** First to seven rounds wins, with attack/defence switched after six rounds. At 6–6, play paired overtime rounds with sides swapped after each round. Win a pair by two; after three tied pairs the beta match is a draw. These numbers require human playtest.

## Example tactical beat

At round start, Sun attacks from the south. Two players take the dry edge of Ghat Jungle, one watches the Mandapa, and two pressure Bazaar. Moon hears a channel begin at the southern fold door and can challenge the doorway or hold the opposite exit. Sun releases the channel early, using the cue as a feint; the two Bazaar players rotate by the ordinary corridor. The carrier crosses A behind a protective ability and begins the three-second plant. A hit cancels it and announces the interruption to both sides. On the second attempt, the plant completes; a distinct site cue and 35-second timer replace the pre-plant clock. Moon retakes from the jungle, but must hold the disarm for five seconds while Sun contests.

This is a possible sequence, not a scripted outcome. Teams must be able to refuse the portal, change routes, win through aim and coordination, or resolve an engagement without a specific hero.

## Presentation and accessibility

- Use icons and text as well as team colors for carriers, sites, portal pairs, danger and interaction states. Avoid relying on red/green differences.
- Separate footsteps in shallow water from portal windup and the final interaction tone; expose volume controls and captions with direction and distance where appropriate.
- Offer reduced camera motion, optional portal fade, high-contrast exits and a persistent destination marker. Do not force flashing lights, rotating horizons or involuntary camera rolls.
- Keep the current team's target, objective state, match clock, score and spectating state visible. Show network interruption and input rejection rather than claiming an action succeeded.
- First version of practice bots should use the same server-authorized movement, visibility and objective rules as players, with difficulty-limited reaction and aim. No bots are implemented by this design.

## Match events to specify before implementation

Use server-owned identifiers and monotonic round and tick numbers for `round_started`, `seal_dropped`, `seal_recovered`, `plant_started`, `plant_cancelled`, `seal_armed`, `disarm_started`, `disarm_cancelled`, `round_resolved` and `match_resolved`. A single authoritative tick orders simultaneous damage, interaction cancellation, plant/disarm completion and timer expiry. Define and test that ordering before network release; do not use client animation or audio as the source of a score.
