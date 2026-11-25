# Ember Rite · maps, modes and progression

These are proposals, not modes or maps added to the current playable package. All standard competitive formats use 5v5 hero-only play; paused lane/jungle minions are not reintroduced. The existing practice and knockout formats remain available in the current Rust prototype until an objective mode is separately integrated.

## Modes

| Mode | Intended audience and rules | Gate before availability |
| --- | --- | --- |
| **Private Ember Rite** | Ten invited players; first to 13, with paired overtime, sides swap, no in-round respawn. Allow duplicate selections while the roster is small. | Server-owned round/objective, all-ten-seat browser capture, join/start/reset/end, reconnect and disconnect policy, visibility and anti-replay checks. |
| **Ember Practice** | Learn carry/drop, interact, interruption, quench and a fake. A solo drill can use a stationary target first; bots are a later separate feature and must obey the same authority. | Accessible tutorials and real input/receipt captures; believable bot movement is not implied by scripted dummy targets. |
| **Quick Rite** | Proposed first-to-seven variant with six-round halftime and paired overtime. It shares the same 100-second approach, 4-second ignition, 40-second burn and 3.5-second quench until independently balanced. | Playtest queue times, player comprehension and both-side balance; 6–6 must not instantly end at 7–6. |
| **Competitive Rite** | Same readable objective and counterplay as private play, with ranking introduced only after the basic match works. Matchmaking should not sell gameplay power. | Stable regional service, placement/match integrity, anti-cheat/privacy review, reporting, accessibility and real-hardware/WAN evidence. |
| **Existing knockout** | The shipped interim hero-only skirmish. It has no planting objective, rounds or Mandala Rift map. | Keep release and mode labels accurate while the new mode is developed. |

Custom exploration, a cinematic gallery and PvE story encounters may be considered later. No mode awards a result or seasonal world change from an animation alone.

## Map production

The [Ember Rite atlas](atlas/README.md) contains dimensioned floor plans, architectural sections, cover designs, times and Blender-importable models for four maps. Mandala Rift is first for a playable blockout. Its Ghat Mandapa and Bazaar Sanctuary share a raised rotation at the Sluice. A slower ford, a dry jungle bank and two optional paired folds let a squad choose what information to give away. The new plan retains both spawns and sites from the [original sketch](../mandala-rift-5v5/README.md).

The next three have different rotation decisions. [Lanka](atlas/maps/lanka.md) asks whether to reveal a crossing on the high causeway or leave early for the sheltered arcade. [Ayodhya](atlas/maps/ayodhya.md) offers a shorter, audible wash beside a viable inner-bank route to its ferry quay. [Kurukshetra](atlas/maps/kurukshetra.md) puts faster openings on the outer banks and preserves both site choices for the team that holds its central bridge.

For room and cover dimensions, use the atlas JSON. Its modeled 5 m/s route times assume clear routes. In the playable pass, verify both shoulders at the final corner, the site lip and 1.5 m reach from a legal floor, plus the path left open after a hero places an area ability. Observe both sides and include rounds where the carrier changes destination. [Route checks](atlas/measurements.md) · [Encounter script and playtests](atlas/ENCOUNTERS.md)

## Motivation and fair rewards

- Make communication, protecting the carrier, successful support, quench attempts and teamwork visible alongside eliminations. Use the server's verified event receipts and context rather than rewarding spammable or self-farmed actions. A canceled quench can still be meaningful, but an attempted-action reward needs anti-farming design.
- Give all players access to the gameplay roster in the proposed competitive mode. Earned story chapters, cosmetics, tutorials and optional player-card expressions may reward participation; purchases must not alter abilities, timing, visibility or hitboxes.
- The user's proposed ultimate points for eliminations, assists, ignition and quench are **future economy work**. Before implementation, define one credit per eligible event, assist attribution, round and match resets, duplicate/reconnect handling and limits for farming. No hero can generate charges through unlimited self-healing or by repeatedly tapping an objective.
- Optional global narrative votes or win aggregates can select pre-authored **cosmetic story variants** only after accounting for sample size, side exposure, abuse, privacy, a tie and an outage. They never give a faction a stronger map or gameplay advantage. No live global world-state service exists here.
- Test onboarding and satisfaction with real participants, including support players and players who lose rounds. Do not infer engagement, accessibility or retention from the presence of points, streaks, scarcity or a color palette.
