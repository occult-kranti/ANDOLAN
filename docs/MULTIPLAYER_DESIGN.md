# City Jobs and City Reform — multiplayer beta design

City Reform Beta 0.3 makes city work and a shared case arc the main multiplayer activities. Players drive, collect vehicles, move supplies and finish district projects; a media correction opens four sector cases and a persistent reform/betrayal decision. The six-chapter First Edition Story remains optional. The ten City jobs use the existing small Devnagar district; the six-district production remains a roadmap.

**Current implementation:** five repeatable jobs plus five once-only cases, 41 stages, 15 loads, 21 event receipts, six authored media cards, four sector records and one durable majority decision with two outcomes. Local source gates (134 tests, typecheck/lint), four focused browser cases, production/standalone builds and the migration/restart container check passed. Release `c20e912` passed all thirteen CI browser cases (11.8 minutes), builds and deployment; public exact-byte and native-browser checks also passed. The earlier CI failure and test-only synchronization change remain in the QA history. [The case specification](CITY_REFORM_DESIGN.md) records routes and satire; [current QA](CITY_REFORM_QA.md) records exact evidence and limits.

**Historical Beta 0.2 baseline:** the five repeatable jobs passed 97 tests, typecheck, lint and all ten browser cases in 491.765 seconds. That included physical two-client Clinic Restock with reload/rejoin and one reward, practice/audio, Story-save isolation and mobile checks. Those results do not verify later 0.3 changes. The public Pages site now serves Beta 0.3; no public multiplayer backend has been provisioned.

## Evidence and design decisions

The current simulation already owns player positions, vehicle seats, collision, commands, shared mission choices and room persistence. It has two real shared vehicles, nine landmarks and no NPC players presented as connected humans. The original campaign advances through one fixed route, with a local or room-owned narrative state. Its arrival stages can advance when a connected player enters the target radius.

These are source observations. The following are design judgments for this beta, not conclusions from human playtests:

- Keep one clear city job active for the crew. Make its next physical action visible while moving, without requiring a long conversation.
- Keep job progress and rewards separate from campaign evidence, votes and endings. City Jobs must not silently advance the optional story through incidental travel.
- Let a single player finish every job; a real crew can divide driving, navigation and on-foot handovers. Roles are opportunities, not character classes or invented specialist abilities.
- Use ordered vehicle/cargo checks so cooperation acts on shared state. A remote teammate cannot deliver cargo that never arrived.
- Offer three repeatable starter jobs and unlock two longer repeatable jobs at four room reputation. The new opening media case is also immediately available; it opens four once-only sector cases. Initial values require later playtesting; no measured session duration or balanced economy is claimed.

The existing chapter tests and browser campaign remain regression requirements. A new beta does not turn an already authored outline into a produced mission.

## Repeatable job catalog

Rewards belong to the room's progression. Credits are a shared score without spending, cash value or a persistent account wallet. Reputation unlocks jobs; project points advance the district milestone. A job awards its reward once per completed attempt, after its last valid stage. This table lists base rewards before the final mandate's modifier.

| Job | Physical sequence | Requirements | Reward: credits / reputation / project | Repeat rule |
| --- | --- | --- | --- | --- |
| Clinic Restock | Load at Mill Ward → park at Night Clinic → unload on foot | Van; one bound load; no timer | 100 / 2 / 1 | Starter; 30 s cooldown |
| Pool Car Recall | Find actual parked compact → drive through Mill Ward → park and return at Yusuf's Garage | Claim the stopped, empty compact on foot; then drive that exact car | 120 / 2 / 0 | Starter; 60 s cooldown |
| District Circuit | Garage check-in → Mill Ward → City Records → Open Frequency → River Steps → garage finish | Same car throughout; checkpoints in order; 180 s from acceptance | 80 / 2 / 0 | Starter; 30 s cooldown |
| Print Run | Load at Open Frequency → unload at The Newsroom → load notices there → unload at Assembly Square | Car or van; same vehicle throughout; two distinct loads | 140 / 3 / 1 | Requires 4 reputation; 45 s cooldown |
| Community Build | Load at Mill Ward → unload at Assembly Square → load at Yusuf's Garage → unload at River Steps | Same van; two distinct loads | 160 / 3 / 2 | Requires 4 reputation; 60 s cooldown |

The recovery job is an authorized pool-car pickup and return, not a damaged-vehicle repair or towing simulation. Its first marker follows the real compact's location. If occupied, the crew must arrange for it to be parked and emptied before claiming it. The Mill Ward checkpoint makes repeat attempts require a journey even when the previous crew left the compact at the garage.

Clinic, print and community jobs are untimed. The circuit's three-minute limit is initial tuning; it should be revisited after first-time driving observations. The limit is disclosed before acceptance and counts from acceptance, including locating a car. Completing a job does not prove a target human playtime.

## Once-only case arc

| Case | Route | Opens or records |
| --- | --- | --- |
| The Nine O'Clock Correction | Newsroom briefing → City Records → Night Clinic comparison and reload → Open Frequency | Four sector cases; 120 credits / 2 reputation / 1 project base reward |
| Light, Camera, Invoice | Garage lamps → Night Clinic service and reload → Public Hearing | Energy; 180 / 3 / 2 |
| The Missing Breakfast | City Records → Mill Ward comparison and replacement load → Assembly Square | Welfare; 160 / 3 / 2 |
| The River Has Receipts | City Records → River Steps comparison and reload → Public Hearing | Resources; 170 / 3 / 1 |
| Lowest Bid, Loudest Sponsor | City Records → Open Frequency comparison and reload → Public Hearing | Procurement; 190 / 3 / 1 |

Every case uses the existing physical loading and on-foot delivery rules. All five are untimed and can be completed once per city save/room. Earned event receipts and media cards are authored in-world content, not a live internet feed. Republic Times and Grnab Aoswami are fictional satirical characters. The new case ledger preserves completion independently of the bounded recent-job history, so an old receipt rolling out cannot unlock another payout.

After all four sectors, the crew approaches Public Hearing on foot with no job active. A majority of connected players selects the permanent City Mandate. **Publish the full case** gives the Open Mandate outcome and adds one project point to future project-bearing job rewards. **Take Samar's deal** gives A New Name on the Door, 25% more credits rounded down and zero future job project points. Reputation and already earned totals remain unchanged. The common reward helper drives displayed and paid rewards; the capture advantage is score, not purchasing power. Repeatable jobs remain available after either ending.

## Authoritative content contract

`JobDefinition` declares an ID, title, short description, kind, ordered stages, reward, cooldown and optional reputation threshold and deadline. New cases declare `once`, `requiresJobs` and an optional `sector`. Stage `event` and `crewTips` are presentation text. There are no executable predicates, arbitrary scripts or client-provided reward expressions.

A `JobStage` declares an ID, objective, landmark ID and action (`interact` or `checkpoint`). Its permitted vehicle is `any`, `car`, `van` or `none`; `none` requires the actor to be on foot. Optional cargo flags are `grantCargo`, `requiresCargo` and `consumeCargo`. Optional `maxSpeed` is absolute simulation metres per second. Current loading, parking and unloading steps use 1.5 m/s; their objectives tell the player to stop. A recovery step can declare `targetVehicleId`, with its runtime target position resolved from the actual server vehicle rather than copied coordinates.

The agreed runtime invariants are:

1. A vehicle-constrained interaction requires the actor to drive the matching stopped vehicle at the destination. The first such step binds the job to that real vehicle. Later vehicle stages use the same ID.
2. A load is created only at a valid pickup in that bound vehicle. It is not an item that a distant crew member can manufacture by clicking.
3. An on-foot unload requires current cargo and the same stopped vehicle inside the destination radius. The runner must also be at the destination. The driver may remain seated while a teammate unloads.
4. Consuming cargo clears it. A two-load job must finish the first handover before collecting the next load. It does not silently swap vehicles between loads.
5. A recovery pickup requires the configured real vehicle to be stopped and empty, and the actor to be on foot beside it. It binds that vehicle before any drive checkpoint can count.
6. Drive checkpoints require the connected driver, matching bound vehicle, current ordered checkpoint and valid position. Passenger input cannot move the car or complete driver-only checks.
7. Credits, reputation, project points, timeout and cooldown use authoritative state. Repeated or replayed commands cannot award completion twice. The client sends intent rather than asserting a position or reward.

Job lifecycle, disconnect/reconnect, abandonment and restoration are owned by the simulation/protocol implementation. A crew must be able to leave an unfinishable attempt without erasing its optional campaign or receiving an incomplete reward. Persistence must either restore the active job consistently with its bound vehicle/cargo or explicitly reject an incompatible saved schema; silently inventing cargo or replaying rewards is not acceptable.

## Cooperation and optional story

The driver loads and moves the bound vehicle. A navigator reads the current destination and helps choose turns; the content does not promise a waypoint-ping tool that does not exist. A runner steps out for delivery while the driver waits. The same person can perform each task sequentially when playing alone. The circuit needs driving/navigation rather than an invented unloading role.

All connected avatars must correspond to actual players in the room. A playable solo fallback can be offered and labelled as such, but it cannot be described as successful multiplayer. No bot fillers or fabricated concurrent-player counts are part of this design.

The title offers City practice and the original solo Story separately. The online lobby explicitly selects City jobs or Original story. A shared room has one fixed gameplay mode; joining it with the other mode is rejected. Local Story and City practice use separate saves, and online reconnection identities are scoped to the server, activity and room. Selecting a different activity does not convert the current shared room or erase campaign history. Job travel cannot advance Story, whose original crew-voting rules remain intact.

The job board shows the active objective, vehicle requirement, remaining time when relevant, cargo state, reward and unlock reason. The current objective remains visible while moving. Cancellation is limited to the owner, or an eligible contributor after the owner disconnects; after thirty seconds without the owner, a connected player can recover an orphaned attempt. Cancellation earns no partial completion reward.

The 0.3 flow closes the job board after the server acknowledges acceptance and provides a compact job selector on mobile. Braking is an explicit server input with full-strength assisted-driving behavior; Space, touch Brake and gamepad B use the same action. Camera recentering and destination markers help return to the route. Reserved/duplicate key bindings are guarded, touch actions follow their semantic action, audio has previews and fades, and larger text is restored on reload. Focused native-input/audio and small-screen browser checks passed; the combined thirteen-case run and native live-site smoke also passed.

Protocol 2 requires a compatible client/server pair. Supported simulation schemas 1/2 migrate to schema 3 without resetting prior cargo, counters, Story or identities; the new city ledger starts empty. Server migration preserves an original room-file backup. See [deployment and rollback](DEPLOYMENT.md).

## Project progression

`PROJECT_MILESTONES` and `getProjectLevel(project)` define room totals at 0, 3, 8 and 15 contribution points: Starting Out, First Contributions, Regular Support and Neighbourhood Backbone. Counts continue beyond the top milestone. These are game progress values, not estimates of real public-service outcomes.

The renderer implements four workshop festoon bulbs at tier one, clinic supplies at tier two and two civic pennant strings at tier three, driven by authoritative project totals. The source and visual review establish their implementation; the targeted first-delivery browser route earns one project point and does not verify every tier through physical play. Job definitions leave the political campaign intact and do not award vehicle upgrades or construct a new district.

## Beta 0.2 baseline acceptance register

The following results precede the City Reform/control changes and remain historical evidence. Final 0.3 verification is listed separately below.

| Gate | Required observation | Status |
| --- | --- | --- |
| Content integrity | Five jobs reference existing landmarks/vehicles; unique stage IDs; positive bounded rewards; every cargo grant consumed in order; thresholds and timer declared | Passed source validation: 5 jobs, 20 stages, 5 loads, 3 starter/2 reputation-4 jobs and 10 project boundary cases; isolated TypeScript and ESLint pass |
| Real delivery handoff | One real client loads/drives; a second unloads beside the stopped bound van; both receive the same updated stage | Passed targeted physical two-context browser route, without position fixtures or clock changes; both share 100 credits / 2 reputation / 1 project exactly once |
| Wrong-location and wrong-vehicle rejection | A remote runner, moving vehicle, different vehicle and passenger driving attempt cannot satisfy the relevant requirement | Passed simulation tests for each rule; targeted real browser route also rejects remote/duplicate/replayed job actions |
| Recovery | Pickup marker follows actual compact state; occupied pickup rejected; same vehicle traverses Mill Ward and returns | Passed simulation tests with controlled positions, including all-job completion; full physical recovery route not separately browser-tested |
| Ordered circuit | Out-of-order visit does not advance; timeout ends attempt without reward; valid full route completes | Passed simulation tests with controlled positions/time; full physical timed circuit not separately browser-tested |
| Progression | Four reputation unlocks two advanced jobs; project tiers change at 3/8/15; duplicate completion adds no second reward | Passed source/simulation boundary and replay tests; targeted browser proves the first shared completion only |
| Restore and repeat | Reload/rejoin retains identity and cargo; checkpoints restore state; complete/abandon/retry obey lifecycle rules | Passed physical browser reload/rejoin during delivery and late join; real WebSocket restart/persistence tests use controlled position fixtures; simulation tests cover cancellation, orphan recovery, cooldowns and corrupt-checkpoint rejection |
| Optional campaign | Separate activity saves preserve history; job travel cannot advance Story; original campaign regressions remain valid | Simulation isolation/migration, browser Story-save isolation and the full campaign/replay case pass in the ten-case Beta 0.2 baseline suite |
| Practice, audio and mobile entry | Solo practice is labelled truthfully; audio controls persist; touch entry and job board fit the viewport | Targeted browser checks pass; post-master audio waveform/mute/zero-volume/lifecycle measured, with no subjective listening claim; low/high/mobile screenshots reviewed |
| Hosted beta | Two separate real browser clients join a deployed backend and complete a job | Pending: paid Render Blueprint prepared, no account/purchase/service created; Pages alone cannot satisfy this gate |

The delivery record is [multiplayer-beta-real-job.json](evidence/multiplayer-beta-real-job.json); the practice/audio and preserved Story checkpoint record is [multiplayer-beta-audio-and-save.json](evidence/multiplayer-beta-audio-and-save.json). The passed baseline browser summary is [multiplayer-beta-browser-results.json](evidence/multiplayer-beta-browser-results.json). `tests/contracts.test.ts`, `tests/contracts-network.test.ts` and `tests/connection.test.ts` cover the specified semantic and network cases. Subsequent City Reform changes require a new verification run.

## Final Beta 0.3 release gates

| Gate | Required current-build evidence | Status |
| --- | --- | --- |
| Content and authority | Ten jobs, valid cargo/event/prerequisite contracts, once-only ledger, correct sector totals and command replay handling | Passed local 134-test source gate plus typecheck/lint; simulation-position fixtures are labelled |
| Physical opening case | Ordinary walking/driving through all five media stages, earned receipts and sector unlocks | Passed focused real two-client route in 71.950 s; reward 120/2/1 once, five receipts and energy unlock; no physical sector-completion claim |
| Mandate and rewards | Majority/tie/location rules, both routes, matching displayed/paid modifiers, persistence and exactly-once completion | Passed simulation and real-WebSocket tests with controlled completed-case setup; both final UI choices/reloads pass explicitly labelled solo fixtures |
| Controls and settings | Acknowledged job closure, mobile selector, rebind/touch consistency, braking, camera, audio and larger-text restore | Focused native-input/audio and final small-screen layout checks passed; combined suite and native live-site smoke passed |
| Story and migration | Separate Story still completes; supported old schemas preserve identities/cargo/Story with server backup | Local Story isolation/source migration pass; real 0.2 volume migration preserves identity/bound job and backup in production container; complete current Story and replay passed in the Actions suite |
| Production builds/container | Exact built artifacts, non-root server, real WebSocket progress and persistent restart | Client/server/standalone builds passed; `andolan:0.3` migration, two clients, first physical briefing and new-case restart passed |
| Complete browser release gate | All thirteen cases on the release revision, plus final standalone/public smoke | Run 38857615158 on c20e912 passed thirteen cases in 11.8 minutes; public exact-byte comparison and native live-site smoke passed; earlier failed attempt preserved in QA history |
| Publication and online hosting | Matching published static revision, then separate backend two-client/reconnect checks | 0.3 Pages release and public checks passed; Render/backend not provisioned |

Current evidence is centralized in [CITY_REFORM_QA.md](CITY_REFORM_QA.md), including [physical media completion](evidence/city-reform-media-route.json), [labelled mandate fixtures](evidence/city-reform-mandate-fixtures.json), [production container migration/restart](evidence/city-reform-container-check.json) and [the subsequent test-barrier check](evidence/city-reform-walk-barrier-check.json). The original CI cause remains unproven; the published test-only follow-up has identical game/build inputs. The complete replacement Actions result and live-site checks are recorded alongside the local evidence.

Human observations remain future evidence: first-job comprehension, whether roles feel useful, route difficulty, timer fairness, repeated-job fatigue and supported-device performance. Automated completion establishes functional rules; it does not establish those qualities.

The content review also flood-filled the actual collision geometry from the vehicle spawn on a one-unit grid with a 1.3-unit vehicle radius. All nine landmark target radii had a connected car-clear point (28,654 reachable grid points). This checks map connectivity; it does not prove that a driver can negotiate every route, that a parked vehicle and runner fit comfortably at every target, or that the final rendered marker is legible.
