# Ember Rite · maps, modes and progression

These are proposals, not modes or maps added to the current playable package. All standard competitive formats use 5v5 hero-only play; paused lane/jungle minions are not reintroduced. The existing practice and knockout formats remain available in the current Rust prototype until an objective mode is separately integrated.

## Modes

| Mode | Intended audience and rules | Gate before availability |
| --- | --- | --- |
| **Private Ember Rite** | Ten invited players; full 13-round/pair-overtime rules, sides swap, no in-round respawn. Allow duplicate selections while the roster is small. | Server-owned round/objective, all-ten-seat browser capture, join/start/reset/end, reconnect and disconnect policy, visibility and anti-replay checks. |
| **Ember Practice** | Learn carry/drop, interact, interruption, quench and a fake. A solo drill can use a stationary target first; bots are a later separate feature and must obey the same authority. | Accessible tutorials and real input/receipt captures; believable bot movement is not implied by scripted dummy targets. |
| **Quick Rite** | Proposed first-to-seven variant with six-round halftime and paired overtime. It shares the same 100-second approach, 4-second ignition, 40-second burn and 3.5-second quench until independently balanced. | Playtest queue times, player comprehension and both-side balance; 6–6 must not instantly end at 7–6. |
| **Competitive Rite** | Same readable objective and counterplay as private play, with ranking introduced only after the basic match works. Matchmaking should not sell gameplay power. | Stable regional service, placement/match integrity, anti-cheat/privacy review, reporting, accessibility and real-hardware/WAN evidence. |
| **Existing knockout** | The shipped interim hero-only skirmish. It has no planting objective, rounds or Mandala Rift map. | Keep release and mode labels accurate while the new mode is developed. |

Custom exploration, a cinematic gallery and PvE story encounters may be considered later. No mode awards a result or seasonal world change from an animation alone.

## First map: Mandala Rift

Reuse the [existing map sketch and route graph](../mandala-rift-5v5/README.md) as a design starting point. A first graybox should include **A: Ghat Mandapa**, **B: Bazaar Sanctuary**, a central contested crossing, water/jungle flank and a continuous dry rotation. Carry the user’s Kurukshetra, river and temple inspirations into a fictional setting rather than treating distant historical locations as one real geography.

Each site needs two distinct approaches, defensible counter-approaches and a safe but contestable quench position. Keep a 3 m candidate site radius and use actual hero speed, collision and shoulder-camera sightlines to measure walk-to-contact, spawn-to-site, rotation and exposure times from **both sides**. The numbers in the existing 2D graph are planning estimates, not a navigable 3D level. Portals/non-Euclidean rooms, ziplines, water movement penalties, dynamic night and stealth must not be assumed until server collision, visibility, escape and performance are validated.

## Later map directions

- **Kurukshetra–Hastinapura fiction:** palace terraces, a river crossing and a windswept field; separate sightline and monument research from the invented two-site layout.
- **Lanka:** a coastal citadel and Ashoka-garden route joined by a bridge, with multiple viable paths instead of one exposed choke. A nominal “attacker-favored” outcome is a hypothesis, not a shipping target.
- **Ayodhya–Sarayu fiction:** civic courtyards and river steps with clear navigable water edges and two contestable sites. A nominal “defender-favored” outcome must be tested and corrected if unfair.

For every candidate, record original or licensed references, graybox dimensions, the actual engine collision, smoke/ability interaction and per-side win and route data. Measure small samples with uncertainty; do not label a map balanced because its plan is symmetric or its colors are complementary.

## Motivation and fair rewards

- Make communication, protecting the carrier, successful support, quench attempts and teamwork visible alongside eliminations. Use the server's verified event receipts and context rather than rewarding spammable or self-farmed actions. A canceled quench can still be meaningful, but an attempted-action reward needs anti-farming design.
- Give all players access to the gameplay roster in the proposed competitive mode. Earned story chapters, cosmetics, tutorials and optional player-card expressions may reward participation; purchases must not alter abilities, timing, visibility or hitboxes.
- The user's proposed ultimate points for eliminations, assists, ignition and quench are **future economy work**. Before implementation, define one credit per eligible event, assist attribution, round and match resets, duplicate/reconnect handling and limits for farming. No hero can generate charges through unlimited self-healing or by repeatedly tapping an objective.
- Optional global narrative votes or win aggregates can select pre-authored **cosmetic story variants** only after accounting for sample size, side exposure, abuse, privacy, a tie and an outage. They never give a faction a stronger map or gameplay advantage. No live global world-state service exists here.
- Test onboarding and satisfaction with real participants, including support players and players who lose rounds. Do not infer engagement, accessibility or retention from the presence of points, streaks, scarcity or a color palette.
