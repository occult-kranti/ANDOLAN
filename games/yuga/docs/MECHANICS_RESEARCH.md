# YUGA mechanics research and design decisions

Research date: 16 October 2026 UTC. This is a bounded design investigation for the original browser arena defined in [IMPLEMENTATION_CONTRACT.md](IMPLEMENTATION_CONTRACT.md). It is not a complete study of Overwatch, Deadlock or Dota 2, and no proprietary binary, commercial source, character model, map, animation or audio was obtained or reverse engineered.

## Evidence levels and access limits

- **Inspected source:** selected pinned open-source files listed below, and an actual REA static run described in [REA_ANALYSIS.md](REA_ANALYSIS.md).
- **Primary documentation read:** Valve's official GameNetworkingSockets README, P2P README and license at a pinned GitHub revision. These describe a transport library, not the current netcode configuration of a named Valve game.
- **Archived teaching text read:** the specified Schreiber lessons, from a pinned public mirror. The canonical WordPress host is blocked; fidelity to its current content/license was not independently checked.
- **Commercial gameplay background:** the comparison below uses broad, longstanding genre characteristics as design context. It is explicitly not a fresh, patch-verified measurement. No current damage values, cooldowns, roster sizes, team counts, lane counts for Deadlock, or server tick rates are asserted.
- **Blocked primary references:** all ten attempted official game/GDC web URLs returned `Tunnel connection failed: 403 Forbidden` through the managed proxy. No alternate proxy, TLS bypass or retry loop was used. [source-access.json](../tools/research/source-access.json) retains the exact URLs and outcomes. Current official rules and patch dates remain a follow-up task.

## Comparison that informs an original game

These are orientation notes, not claims that every mode or patch shares the same rules. Overwatch in particular has multiple modes; a statement about its conventional objective modes must not be generalized to every economy/progression mode.

| Dimension | Overwatch background | Deadlock background | Dota 2 background | Original YUGA decision |
| --- | --- | --- | --- | --- |
| Aim and viewpoint | First-person aiming mixed with hero-specific weapons and abilities. | Third-person aiming combined with lane combat. | Overhead command-based movement, targeted and skill-shot abilities. | Third-person, camera-relative movement, explicit yaw/pitch aim, visible projectiles. Do not combine click-to-move with WASD implicitly. |
| Roles | Team composition includes protection, damage and support functions. | Hero kits can contribute damage, control, survival and utility; current classifications unverified. | Carry/support/initiator and other functions emerge from kits, items and match context. | Twelve distinct kits grouped as Vanguard, Striker and Keeper. Explain a strength and limitation before selection; role names do not enforce hidden queue rules. |
| Lanes and objectives | Conventional modes emphasize shared map objectives rather than a persistent creep-lane economy. | Lane pressure, defensive objectives and a final base objective are central concepts. | Three-lane pressure, towers and an enemy Ancient form the familiar strategic structure. | Three lanes, waves, three defending towers per team. A team's core loses protection after two of **that team's** towers fall. HUD wording must remove any ambiguity about whose towers matter. |
| Minions and economy | Mode dependent; do not assert that every current mode lacks purchases or progression. | Lane units and match-earned progression create a farming/rotation tradeoff; current sharing/deny rules are unverified. | Creeps, last hits, denies, items and experience create resource choices; exact formulas are patch sensitive. | Match-earned credits and three readable upgrade paths at spawn. No inventory grid, deny mechanic or complex item recipes in the first release. Explain the implemented credit rule rather than borrowing an assumed one. |
| Mobility | Hero-specific movement is a major kit distinction. | Movement and map traversal are part of the shooter/lane combination; current move set unverified. | Positioning, pathing, abilities and items alter access to engagements. | Common walk/jump plus explicit kit movement. A dash input must name the mapped ability and obey its cooldown; no unexplained universal dash. |
| Counters | Range, cover, timing, protection and ability interactions. | Aim, build, positioning and ability interactions; current counter matrix unverified. | Draft, positioning, resource timing and item/ability interactions. | Soft counters visible in the kit: short range versus spacing, burst versus ward, commitment versus escape. Avoid hidden immunity chains or a claim that twelve kits are already balanced. |
| Network behavior | Current prediction, reconciliation and rewind parameters were not inspected. | Current transport/prediction/hit rules were not inspected. | Current transport/prediction/hit rules were not inspected. | Shared authoritative TypeScript simulation; clients submit intent. Presentation smoothing must not change damage, target selection, cooldowns or purchases. Measure latency before adding prediction/rewind. |
| Story and identity | Commercial characters, setting and expression belong to their creators. | Commercial setting, characters and expression belong to their creators. | Commercial setting, characters and expression belong to their creators. | Original Confluence premise and authored kits; mythology provenance belongs in the content team's research. No named commercial character remixes, copied dialogue or asset imports. |

The shared contract accepts the YUGA column as scope, not as a claim of completion. The following gates distinguish implementation from research recommendations.

## Five actionable mechanics and review gates

| Mechanic | Status and reasoning | Acceptance gate |
| --- | --- | --- |
| Readable aim → cast → result | Contract accepted. The inspected sample's state/event separation is useful; Schreiber's interface lesson requires understandable feedback. | Normal input produces an accepted cast, visible trajectory/area and acknowledged result. Cooldown/dead/purchase-location failures give distinct feedback. A local flash must not imply unconfirmed damage. Aim and collision agree at cover edges. |
| Lane pressure with an understandable end condition | Contract accepted: waves, towers, core, eight-minute limit. This is an original simplification, not recovered balance data. | Every lane receives valid minion paths; no solid blocks its required route. A protected core cannot take damage. Destroy two defending towers, then damage that core. Time expiry uses the documented tiebreak and a stable finished state. |
| Useful participation beyond the final hit | Research recommendation; moderator/systems decide the exact reward rule. Tank Battle separates team and individual scores, but that alone does not prove a fair support economy. | Record the actual credit/assist rule. Two allies contributing to an objective see consistent results; a Keeper can earn meaningful progress through the implemented support or proximity rule. No duplicate death/completion payout. A disconnected or idle player must not produce an unintended unlimited reward source. |
| Meaningful, small upgrade choices | Contract accepted: power, vitality, tempo at spawn. Schreiber distinguishes understandable tradeoffs from blind or obvious choices. | Before purchase, show current value, cost and resulting effect. Server rejects insufficient credits, invalid location and duplicate ID. Repeated purchases respect caps/costs. Each path has a testable benefit and no claimed universal optimality. |
| Recovery preserves a coherent match | Contract accepted authority/reconnect; lifecycle details need tests. The sample's automatic room reset is a counterexample for a deliberate results/replay flow. | Two clients agree on death, respawn, score and objective state. Reconnect preserves one identity, clears stale intent and never replays a purchase. A finished match cannot keep granting rewards. Replay gets a new match epoch; a late packet cannot revive the previous round. |

Candidate values such as cooldowns, range, wave cadence, upgrade price and time-to-defeat require playtesting. A deterministic test establishes a rule, not enjoyment, fairness across skill levels, or competitive balance.

## Exact open-source reading register

### O1: PlayCanvas/Colyseus Tank Battle

Repository: [endel/tank-battle-multiplayer at `6339493130b4b1d4d28f0f52d17b2fba738c7d47`](https://github.com/endel/tank-battle-multiplayer/tree/6339493130b4b1d4d28f0f52d17b2fba738c7d47). MIT, Endel Dreyer and Maksims Mihejevs; license read. The local directory is a selected source archive, not a whole game installation. No dependencies, external models or reference game server were run.

- [BattleRoom.ts](https://github.com/endel/tank-battle-multiplayer/blob/6339493130b4b1d4d28f0f52d17b2fba738c7d47/server/src/rooms/BattleRoom.ts): read message handlers/join/leave/team choice (lines 133–218), update/combat/pickups/respawn/score/reset (219–509), and projectile creation. The server owns those rules. Its numeric handlers use `typeof number` without the finite bounded contract YUGA needs. Movement increments are per callback, and several timers use wall-clock `Date.now`; these are not recommended as YUGA timing rules.
- [BattleState.ts](https://github.com/endel/tank-battle-multiplayer/blob/6339493130b4b1d4d28f0f52d17b2fba738c7d47/server/src/schema/BattleState.ts): full file read. Synchronized display state is distinguished from local simulation fields; individual/team scores are separate.
- [Network.ts](https://github.com/endel/tank-battle-multiplayer/blob/6339493130b4b1d4d28f0f52d17b2fba738c7d47/web-playcanvas/src/Network.ts): full file read. Client methods send movement/aim/shoot intent, not damage results. This small wrapper alone does not establish robust reconnect, stale-input expiry or a secure boundary.
- Earlier inspected [Tank.ts lines 406–435](https://github.com/endel/tank-battle-multiplayer/blob/6339493130b4b1d4d28f0f52d17b2fba738c7d47/web-playcanvas/src/Tank.ts#L406) uses fixed-factor interpolation. Reuse the distinction between received state and displayed transform, not its frame-rate-dependent factor. Earlier scope is recorded in [ANDOLAN's source register](../../../docs/research/MULTIPLAYER_REFERENCES.md).

The new REA pass selected the first three files only. Its ambiguous score trace is described separately; manual reading, not the trace, supports the score-flow observations above.

### O2: Valve GameNetworkingSockets

Official repository: [ValveSoftware/GameNetworkingSockets at `d534c19aa760df3fb75fd20db13ba1932b8a5463`](https://github.com/ValveSoftware/GameNetworkingSockets/tree/d534c19aa760df3fb75fd20db13ba1932b8a5463). BSD-3-Clause, Valve Corporation. Read the full [README](https://github.com/ValveSoftware/GameNetworkingSockets/blob/d534c19aa760df3fb75fd20db13ba1932b8a5463/README.md), [README_P2P](https://github.com/ValveSoftware/GameNetworkingSockets/blob/d534c19aa760df3fb75fd20db13ba1932b8a5463/README_P2P.md) and license through ordinary HTTPS on 16 October 2026. No C++ build or transport experiment was performed.

The README documents reliable/unreliable messages, fragmentation, encryption, packet-loss/latency simulation and connection lanes. It explicitly excludes higher-level entity serialization/delta encoding and compression. The P2P README separates signaling, STUN, relay fallback and host identity/matchmaking requirements from transport code. Steam-specific services are not automatically available from the open-source library. Its use of ICE is not evidence of a drop-in browser WebRTC data-channel adapter.

**Lesson:** transport choice does not implement the game or its service operations. This source does not disclose Overwatch netcode or the current Dota/Deadlock prediction, tick rate or hit compensation rules.

### O3: Earlier bounded camera/interpolation sources

Sketchbook MIT commit `62f4b7986fd1ce1e4f91daba89ef032c20a6ce55`, `CameraOperator.ts` and `SpringSimulator.ts`, and Geckos BSD-3-Clause commit `a171cefb626085bfff5241cbd60c8099bdd742bf`, selected interpolation files, were inspected in the previous ANDOLAN work. Their precise files, execution scope and observed edge cases remain in the [earlier register](../../../docs/research/MULTIPLAYER_REFERENCES.md). They are prior evidence, not newly executed YUGA reference games. No source was copied into YUGA.

## Backend recommendation

| Candidate | Decision now | Evidence and gate before changing |
| --- | --- | --- |
| Existing PlayCanvas + shared TypeScript simulator + `ws` | Keep for this release. The browser practice and server can execute the same rules; existing toolchain and deployment work are useful. | Validate finite inputs, command dedupe, same-identity reconnect, room caps, backpressure and stale-input expiry. Measure actual CPU/tick cost and traffic at stated room/actor counts. WebSocket reliable delivery can delay newer state behind old traffic; a LAN check does not establish WAN smoothness. |
| Colyseus | Consider only if room lifecycle/state serialization becomes a demonstrated maintenance bottleneck. | Tank Battle shows a working architectural pattern, not proof that migration is needed. First compare a small adapter against the same authority, reconnect and load tests. Do not maintain two divergent combat rule sets. |
| Browser WebRTC/WebTransport | Future transport experiment, not a prerequisite. | Require measured benefit under delay/loss, supported-browser matrix, signaling/relay/hosting plan and reconnect semantics. Unreliable delivery would require explicit snapshot ordering and command acknowledgments. |
| Valve GameNetworkingSockets | Reference documentation; not adopted. | Native C/C++ transport and platform/service integration would be a separate product decision. No compatible browser drop-in was established in this pass. |

A static Pages deployment can serve practice. Live multiplayer also needs a running public WSS service with TLS, allowed origin, capacity controls and an operational owner. A Dockerfile or a locally successful socket test is not evidence that such a service is deployed.

## Motivation, mastery and cooperation

This uses autonomy, competence and relatedness as a design lens, not a psychological efficacy claim. Research child `motivation_sources` read the listed archived sections; no participant study was conducted.

| Actually read segment | Lesson for YUGA | Review gate |
| --- | --- | --- |
| Ian Schreiber, [Level 7](https://gamedesignconcepts.wordpress.com/2009/07/20/level-7-decision-making-and-flow-theory/), 20 July 2009: decisions, good/bad choices, action-game choices | Let players understand competing benefits rather than choose blindly. | All twelve kits expose role, three abilities and a limitation before selection; upgrade cost/effect appears before purchase. |
| Same Level 7: flow discussion and its limitations | Clear goals and feedback support learning; flow and fun are not synonyms. | Practice teaches the actual objective rules, protected-core condition, cooldowns and respawn. Novice observation remains necessary before claiming first-time usability. |
| Schreiber, [Level 8](https://gamedesignconcepts.wordpress.com/2009/07/23/level-8-kinds-of-fun-kinds-of-players/), 23 July 2009: fellowship/expression; [Level 3](https://gamedesignconcepts.wordpress.com/2009/07/06/level-3-formal-elements-of-games/), 6 July 2009: players/player interaction | Multiplayer connectivity is not itself cooperation; useful joint actions and recognizable teammates matter. | Two actual clients identify one another and jointly contribute to an objective with consistent results. Bot-only testing does not establish this. |
| Schreiber, [Level 17](https://gamedesignconcepts.wordpress.com/2009/08/24/level-17-user-interfaces/), 24 August 2009: good UI, color and feedback | Explain outcomes promptly and use more than color alone. | Successful/rejected cast, hit, death, purchase and objective changes have readable distinct feedback; team/role identification includes labels or shapes. |

Read from [mirror commit `5c98165cb261143bda0147463acbaee922ca46c9`](https://github.com/eugenioclrc/gamedesignconcepts/tree/5c98165cb261143bda0147463acbaee922ca46c9), `lessons/03-…`, `07-…`, `08-…`, `17-…`. No whole course or its commercial-book references were read. No full lesson is copied into this game.

The contract excludes paid power, loot boxes, streak loss and mandatory login. Preserve a voluntary end-of-match exit/replay choice. These are product constraints; this pass does not establish that every streak system is harmful or that these choices guarantee retention/wellbeing.

**Bibliography only, not read this pass:** Ryan, Rigby & Przybylski (2006), *The Motivational Pull of Video Games: A Self-Determination Theory Approach*, *Motivation and Emotion* 30, 344–360, DOI [10.1007/s11031-006-9051-8](https://doi.org/10.1007/s11031-006-9051-8). Its author-hosted PDF request returned proxy 403. Schell, *The Art of Game Design*, 3rd ed. (CRC, 2019); Fullerton, *Game Design Workshop*, 4th ed. (CRC, 2018); Salen & Zimmerman, *Rules of Play* (MIT Press, 2003); Koster, *A Theory of Fun for Game Design*, 2nd ed. (O'Reilly, 2013). No book downloads, whole-book reading, effect-size claims or copied exercises are implied.

## Next bounded research work

When official hosts are accessible, record the exact patch/date/mode before comparing economy, mobility and counter rules; inspect only the mechanics that resolve a live YUGA question. Observe permissioned gameplay rather than pretending documentation reveals implementation. Test the original hypothesis in YUGA before expanding scope. Commercial binaries and asset extraction are not needed to complete the accepted first release.
