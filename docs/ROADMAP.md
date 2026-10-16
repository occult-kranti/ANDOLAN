# ANDOLAN production roadmap

The user's original v0.3 handoff defines a browser-native open-world production. The current **City Reform Beta 0.3** adds multiplayer city work and a bounded reform/betrayal arc alongside the earlier six-chapter Story. The handoff version and software version are separate labels. Neither the preview campaign nor the new case arc completes the original six-district, 22-mission production.

## Current bounded milestone

**City Reform Beta 0.3:** one small district, real shared rooms, five repeatable jobs and five once-only cases. City content has 41 stages, 15 physical cargo loads, 21 event receipts and six authored media cards. The opening correction unlocks energy, welfare, resources and procurement cases. A durable crew-majority mandate has two outcomes and changes future job rewards: reform adds one point to project-bearing rewards; capture adds 25% credits and contributes no further project points. Credits remain a room-owned score.

The original **First Edition** Story remains optional, with six chapters, 22 stages, seven decisions, five endings and separate saves. The public website now serves verified Beta 0.3. Release `c20e912` passed 134 tests, all thirteen CI browser cases (11.8 minutes), builds/deployment, exact public-file checks and a native live-site smoke. Local production-container migration/restart also passed on identical application/build inputs. The earlier CI failure and test-only synchronization change remain in the QA history. No public multiplayer service has been provisioned. The intervening 0.2 baseline remains separate: 97 tests and ten browser cases in 491.765 seconds.

The current source also adds explicit braking, camera recentering, clearer destination markers, server-confirmed job acceptance that closes the board, a compact mobile job selector, guarded key rebinding, consistent touch actions, sound preview/fades and restored large-text settings. Focused native-input/audio and final small-screen checks passed on 0.3; the full integrated suite and native live-site smoke also passed. Human comprehension, real-device coverage and sustained service capacity remain observations to collect.

The panel reduced map scale from the handoff’s approximately 500 × 500 metre first district to a 200 × 200 unit block set so every landmark has a purpose. It condensed selected campaign beats to test continuity and the final choice now. This does not cancel the original chapters or the multiplayer roadmap.

The six original user-requested review rounds closed for First Edition and remain historical evidence in `PANEL_LEDGER.md`; subsequent beta work has its own records. First Edition's later complete browser suite and public solo release passed, while City Jobs 0.2 has its own ten-case baseline. Completing a review round does not complete the similarly numbered production milestone. Current gates must be read from the matching QA and deployment records; an implemented feature, passed local test and operated public service are separate milestones.

## Gates, in dependency order

| Gate | Work | Exit evidence |
| --- | --- | --- |
| R0 — References | Inspect REA and a permitted controller reference, pin sources, specify a narrow subsystem, record licenses. | Actual analysis artifact and implementation tests; distinguish source reading from gameplay observation. |
| R1 — Feel of play | Camera, walk/drive transitions, collision, a useful hub, route clarity and comfort settings. | Browser journey walk → car → clinic → board, screenshots and device/frame-time/load measurements. |
| R2 — Shared private session | Authoritative seats, missions, votes, reconnect and commands. | Two real browser clients plus network tests for conflicts, duplicate commands, disconnect and resume. |
| R2b — City Jobs baseline | Five repeatable jobs, cargo/vehicle handoffs, room progression, separate Story and runtime server selection. | 0.2 baseline passed 97 tests and ten browser cases, including a physical shared Clinic Restock route. Hosted acceptance remains open. |
| R2c — City Reform beta | Five linked once-only cases, persistent sector ledger, earned event receipts, final mandate and control/settings improvements. | 134 tests, thirteen CI browser cases, builds/deployment, exact public artifact and native live-site checks passed; physical routes, labelled final-choice fixtures and migration/restart are separately evidenced. |
| R3a — First Edition preview | Six condensed chapters, authored dialogue, documents, choices, five endings and replay. | Content integrity, exhaustive ending reachability and complete browser campaign traversal. |
| R3b — Last Delivery production slice | Expand the opening to its full staging, monsoon atmosphere, traffic, animation, audio, assisted driving and authored diversion. | Novice completion, coherent audiovisual presentation, checkpoint recovery and measured low-spec operation. |
| R4 — Public district alpha | Accounts, regional matchmaking, moderation, reports/block/mute, transactional public rewards, durable profile storage and crash recovery. | Controlled external playtest, abuse tests and measured operational cost/capacity. A development public room is not this gate. |
| R5 — City and campaign | Six districts and 22 produced missions; crew variation, interiors, side jobs, localization and animation/audio production. | District and mission acceptance records; narrative continuity and save migration pass. |
| R6 — Public production launch | Capacity, supported-device matrix, content/asset review, backups, rollback, incident ownership and service policies. | Verified release candidate, operations rehearsal and tested deployment. |

## Next increments after the current beta

1. **Operate an invited online beta.** The verified 0.3 static client is published. Separately provision a reviewed persistent backend and complete its two-client/reconnect/restart checks before advertising shared online availability. The prepared Docker/Render files and hosting guide support that step; no public service has been provisioned.
2. **Observe first-time crews.** Check whether they find the starting case, understand driver/runner handoffs, recover from a split vote and explain the permanent mandate effects. Measure supported devices and online sessions separately. Automated traversal does not replace these observations.
3. **Give sectors distinct playable systems.** Current cases move records/supplies and reveal authored comparisons. Add an actual comparison task, cooperative split objective or service-repair mechanic before multiplying cases. Energy grids, extraction markets and national institutions are not yet simulated.
4. **Make both routes playable beyond reward arithmetic.** Add different reform and capture encounters with saved consequences and genuine crew tradeoffs. The present capture benefit is score, since credits cannot be spent. No balanced economy or substantial post-ending campaign is claimed.
5. **Produce the opening and original mission families.** Improve character animation, acting, environmental staging and the full Last Delivery sequence; then produce The Empty Chair or the full Two Copies venue. The current synthesized audio and media cards do not replace acting or scene production. Keep all original titles below and assess authoring throughput before expanding another district.
6. **Advance public-service infrastructure independently.** Regional discovery, accounts, moderation, abuse handling, profiles and operational ownership precede unrestricted public launch. Static publication and private-room tests do not satisfy those requirements.

## Future national transition arc — not implemented

The requested eventual regime-change endgame extends beyond the present municipal City Mandate. This authored production plan builds on the original acts and mission slate below. Its sector simulations and national endgame remain unimplemented.

1. **Earn sector service milestones.** Produce distinct energy, welfare, resource and procurement tasks with persistent capacity, operating-budget, service-quality and environmental constraints. Crews must keep a service working across several jobs, rather than receive permanent success for filing one case.
2. **Check contract and ownership outcomes independently.** Add playable comparisons of bids, disclosed ownership, delivered work and invoices; retain responses, innocent matches and unresolved findings. An independent in-world review can confirm, narrow or reject the crew's claim. A policy or ownership change requires a recorded decision and a delivered service outcome, not a shared surname or an automatic corruption score.
3. **Build district mandates.** Let crews propose a service arrangement, negotiate its visible costs and complete a public demonstration. Each district records its own mandate, opposition response, contract and later service result. A popular headline cannot substitute for a functioning service or guarantee another district's support.
4. **Convene the national assembly.** After several district arcs, the original late-game assembly missions bring their records, allies and unresolved disputes into a fictional national vote/transition. The administration can change through an authored institutional resolution. Earlier district mandates and disclosures determine which coalition agreements and transition missions are available.
5. **Play the consequences of reform or capture.** Carry the chosen path into a post-transition chapter with different allies, service obligations and missions. Neither ending erases previous records, automatically fixes the economy or ends the need for crew work.

Public, cooperative and private provision should offer defensible alternatives in those future systems. These proposed game tradeoffs need implementation and tuning:

| Service arrangement | Proposed playable advantage | Proposed cost and obligation |
| --- | --- | --- |
| Public service | Broad eligibility and predictable access; district investment can retain useful long-term capacity | Larger upfront shared-budget commitment, visible procurement steps and maintenance obligations compete with other services |
| Worker/resident cooperative | Direct local oversight and adaptable priorities; crews gain participation and repair missions | Limited starting capacity and reserve funds; member decisions take time and can conflict across neighborhoods |
| Regulated private contract | Faster initial capacity through an outside provider; specified delivery deadlines and financing | Fees and contract renewals consume later budget; enforce service standards, ownership disclosure and an exit/continuity plan |

An energy job might trade a slower permanent grid repair against a temporary contracted supply; a welfare job might trade immediate contracted coverage against local cooperative capacity. Resource concessions must expose restoration costs and revenue obligations, while procurement choices must expose price, reliability and conflict disclosures. The player needs observable service consequences and recovery options; a single ownership label must not be the always-correct answer. These systems require new mechanics, budgets, content and testing before those promises can appear in the product.

The **reform** continuation would bind the crew's own coalition to disclosures and independent checks, including cases that cost the crew a favored contract or delay an expansion. It could retain Noor and open oversight/cooperation missions. The **capture** continuation would offer privileged access and lucrative sponsor assignments while imposing donor demands, withholding records and reducing independent support. Betrayed allies would leave or oppose specific missions; concealment could later surface through another actor's investigation. Those should change playable routes and resources persistently, rather than only an ending paragraph. The existing 0.3 route effects remain exactly the documented project bonus versus credit-score bonus/zero new projects; none of these future national systems is implemented yet.

Exit evidence for the national arc must include actual playable sector systems, independent-review branches, multiple completed district mandates, an earned assembly transition, both post-transition paths and save/reconnect coverage. Human crew playtests must assess whether the choices feel understandable and consequential. A design table or scripted ending alone does not close that milestone.

## Original 22-mission slate

“Adapted in preview” identifies borrowed story beats, not a finished full-length production mission. Remaining items are authored outlines from the handoff.

| # | Act | Mission | Current content relationship |
| ---: | --- | --- | --- |
| 01 | The city owes you nothing | Last Delivery | Adapted as preview chapter 1; expanded cinematic opening pending. |
| 02 | The city owes you nothing | The Empty Chair | Outline; Meera appears in the preview, but this mission is not produced. |
| 03 | The city owes you nothing | Two Copies | Adapted as preview chapter 2; multi-approach venue pending. |
| 04 | The city owes you nothing | A Friend of a Friend | Outline. |
| 05 | The city owes you nothing | Closing Time | Outline; negotiate/retreat/arcade encounter not produced. |
| 06 | The city owes you nothing | First Edition | Adapted as preview chapter 4. |
| 07 | The city is a balance sheet | Empty Shelves | Adapted as preview chapter 3. |
| 08 | The city is a balance sheet | The Model City | Engineer interview included in preview; full development tour pending. |
| 09 | The city is a balance sheet | The Long Way Home | Outline; emergency vehicle sequence not produced. |
| 10 | The city is a balance sheet | Paid in Full | Innocent surname link included in preview; full comparison mission pending. |
| 11 | The city is a balance sheet | The Friendly Ledger | Sponsor decision included in preview chapter 4. |
| 12 | The city is a balance sheet | Split Screen | Outline; simultaneous multi-perspective scenes pending. |
| 13 | The crowd and the camera | The Listening Tour | Outline. |
| 14 | The crowd and the camera | The Broken Window | Outline. |
| 15 | The crowd and the camera | Open Microphone | Adapted as preview chapter 5; theatrical event production pending. |
| 16 | The crowd and the camera | The Missing Minute | Outline; alternate recording mission pending. |
| 17 | The crowd and the camera | The Offer | Asha’s written offer included in preview. |
| 18 | The crowd and the camera | One of Our Own | Accountability-for-allies decision included in preview; full mission pending. |
| 19 | Who owns tomorrow? | The Public Hearing | Adapted as preview chapter 6. |
| 20 | Who owns tomorrow? | Midnight Assembly | Outcome summarized by preview epilogues; constitutional-crisis mission pending. |
| 21 | Who owns tomorrow? | The Victory Party | Outline. |
| 22 | Who owns tomorrow? | Open Windows | Six-month text epilogue included in preview; multi-stop playable epilogue pending. |

## Production decisions still requiring evidence

Do not pick a concurrency limit from occupancy arithmetic. Do not estimate a launch date from the speed of generating text. The next scope revision should use observed player completion, recurring control problems, mission-authoring throughput, device performance, server load and art/audio costs. The 6–10 hour full-campaign duration remains a target, not a measured result.

Before adding content volume, make the opening reliable and the first two-client mission legible. After that, expand in mission families: delivery/interview, venue investigation, cooperative split task, authored social set piece and epilogue visit. Keep the single engine path unless a measured failure justifies changing it.
