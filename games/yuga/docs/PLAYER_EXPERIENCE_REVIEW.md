# YUGA — bounded player-experience review

Prepared 16 October 2026 for the lane-unit, jungle and contested-gold expansion. This review translates concrete product risks into small acceptance checks. It does not report a user study, representative sentiment, retention change or competitive balance result.

## What was available

| ID | Material and retrieval boundary | What it supports |
| --- | --- | --- |
| E-1 | User-supplied `https://share.google/cuTYg9JGQniJ9WjYg`; parent reported CONNECT HTTP 403 on 16 October 2026. No linked post, author, date, subreddit, comments, votes or destination content was received in this review. | A missing source. No criticism is attributed to that thread; a direct reachable permalink or pasted text is needed before adding its claims. |
| E-1b | User subsequently supplied `https://www.reddit.com/r/DeadlockTheGame/`. The coordinator's ordinary managed curl request around 18:20 UTC on 16 October 2026 again returned CONNECT HTTP 403 with no response body. This is a subreddit listing address, not an inspected individual post. | No Reddit review content was read. Pasted excerpts have been requested; author/date/version and comment context remain unknown. |
| E-2 | The user's direct project requests, relayed in the working task: improve primitive-looking characters, smooth controls/settings/audio, add recognizable minion roles, neutral creatures and contested gold. | This user's preferences and requested scope. They do not establish broader player sentiment or prove the revised build meets the preference. |
| E-3 | [QA.md](QA.md), including `final-hero-browser-check.json`, `final-native-revision-check.json` and `final-roster-stress-all.json` in its evidence index. | Bounded automated baseline behavior: actual fourteen-model actions, settings/mobile/reconnect checks and local simulation/socket measurements. These precede the new expansion; open counter/soak gates remain visible there. |
| E-4 | Current [map](../shared/map.ts), [types](../shared/types.ts), and accepted [minion/jungle contract](MINIONS_AND_JUNGLE.md). | Authored mechanics, dimensions and testable expectations. Source text is not rendered readability or human comprehension evidence. |
| E-5 | [Public video/tooling register](../art/DEADLOCK_VIDEO_AND_TOOLING.md) and [mechanics research](MECHANICS_RESEARCH.md). Official/game-video requests were blocked; selected pinned open-source documentation was inspected. | Event-level measurement methods and architecture context. No watched footage, current commercial reward formula or competitor player criticism is claimed. |

There are **zero accessible external player reviews in this bounded pass**. Consequently, H-1 through H-7 below are design hypotheses informed by our rules and existing QA, not reported opinions from Reddit or any game's community. They should be challenged by observations, including positive counterexamples, rather than repeated as established complaints. Broader review research is deferred until a direct source is available; it does not block these bounded implementation checks.

## Safeguards present in the current source

Read-only inspection of [client/main.ts](../client/main.ts) and the integrated simulator found the following changes during this pass. They are implemented source behavior awaiting the expansion browser gates, not evidence that all related usability concerns are solved.

| Change | Narrow benefit and remaining check |
| --- | --- |
| Mouse buttons are handled individually, while pointer capture/loss still clears held input. | Allows fire and target-lock button chords without assuming Pointer Events report every button transition. Native press/release ordering remains to be tested. |
| Loading has Back/Escape and a request-generation guard after asynchronous asset work. | The player can cancel entry and a stale completion cannot start that abandoned session. This does not abort every network download or reduce payload size. |
| Gold feedback aggregates the local player's authoritative claim events; the opening empty event snapshot gets an explicit baseline. | A confirmed claim is not inferred from a client click, and the first later event is not silently discarded. Shared award explanation and wallet comprehension still need H-2 checks. |
| Camp health, return/respawn state and minimap marks are exposed; buff timers are named and Ward is hidden at zero shield. | Makes the accepted state inspectable without inventing separate ward layers. Actual native timing, small-screen legibility and expiry remain test gates. |
| The feed excludes distant minion/bot ability spam while retaining relevant objectives and local events. | Reduces competing text. It does not prove combat readability or human preference. |
| Summoned sentinels grant neither gold nor team points when defeated. | Removes this particular summon-fed scoring loop. It does not establish that the entire economy is balanced. |

The known first-load hero payload is approximately **44.37 MiB**, plus the forthcoming unit assets, and the current entry path preloads them before Practice. Cancelable entry helps control but does not establish an acceptable download wait, frame rate or memory budget. Incremental loading and smaller assets remain product options to evaluate against measured costs; they are not implemented claims in this review.

## Prioritized issue cards

### H-1 — A winning lane may turn every nearby resource into further power

**Evidence / mechanism:** E-4. The new wave changes two escorts into three, splits gold into shared and contested components, and adds four camps. Better lane control may make both camp access and shard aim safer. That could amplify an early lead, but shared gold and exposure while farming might also help a trailing team recover; neither direction has been demonstrated.

**Decision:** retain the agreed transparent rewards for the first measured build; do not add hidden rubber-banding or change upgrade costs from intuition. Compare total awarded gold, upgrade timing, camp clear time, objective damage and score gaps at fixed times. Separate guaranteed awards from shard claims, and separate player/bot policy from hero kit effects.

**Acceptance / owner / state:** systems records mirrored teams/seeds and exact reward accounting, root reviews the resulting economy, QA checks a complete match. Gate is no duplicate/unbounded farm source and an inspectable distribution, not a declared acceptable win-rate from a tiny AI sample. Later human sessions should include both leading and trailing perspectives. **Pending new expansion evidence.**

### H-2 — “Shared”, “secure” and “steal” can describe three different wallet events unclearly

**Evidence / mechanism:** E-4. Two allies can each receive 30 camp gold while one hero on either team claims an additional 30 shard. The last-hit hero's buff is a fourth, separate state change. A single `+60` flash would misdescribe recipients and imply the shard was guaranteed. A compact grouped receipt may still be clearer than several competing banners, so presentation needs inspection.

**Decision:** identify each event and actual amount: shared award, unclaimed shard, confirmed secure/steal and buff. “Steal” never subtracts existing wallet gold. Show primary-shot claim availability immediately and delayed proximity availability after 1 s. Use shape/text as well as color; keep combat sight lines clear.

**Acceptance / owner / state:** root/UI and systems verify exact wallet deltas with two clients, one camp and a rival claim; no local claim is celebrated before authoritative confirmation. Expiry pays nobody. QA checks desktop and touch feedback against the same shard ID. Future first-time observers should correctly explain who gained what after one encounter. **Priority integration gate; pending.**

### H-3 — A new player may leave the lane without knowing why or how to return

**Evidence / mechanism:** E-2/E-4. Heroes, upgrades, waves, towers, three new buff types and two claim routes compete for attention. Repeated mandatory tutorials could be equally disruptive, especially for players who already understand lane games.

**Decision:** keep Practice immediately available and use one short contextual camp hint rather than a forced tutorial sequence. Give an actionable objective and current controls: protect the wave, defeat two defending towers to expose that core, and optionally contest a nearby camp. Explain that a camp buff is temporary and does not replace Q/E/R. Match hints to the actual current keyboard, mouse and touch controls. Key remapping is a possible later accessibility improvement; there is no remapping UI in this build.

**Acceptance / owner / state:** root verifies the first session, returning session, current keyboard/mouse/touch hints and narrow touch layout; dismissing a hint does not block play or reopen it every snapshot. A future first-time observation should show lane entry, one understood optional interaction and return to the objective without coaching. No such comprehension session is claimed yet. **Pending.**

### H-4 — More bodies and reward effects may hide the dangerous action

**Evidence / mechanism:** E-3/E-4. Existing real-model and bounded stress checks establish a useful baseline, while the expansion increases bodies, support pulses and dropped entities. Detailed art may help identity but can also obscure projectiles and the three authored windups. A still image after a cooldown starts does not prove the telegraph was readable.

**Decision:** preserve team/neutral labels, distinct silhouettes, bounded effects, clear impact/claim cues and reduced-motion support. Minister shielding must visibly identify eligible minions. A grounded Cloudwing must not imply aerial immunity. Keep actual cover aligned with shared solids. Telegraphs take priority over celebratory gold effects.

**Acceptance / owner / state:** world/audio/QA capture a live mixed wave and camp encounter at low/high quality and a narrow touch viewport; confirm identities, incoming attacks and defeat states from their actual IDs/times. Export/animation tests remain separate. Timing and performance must be measured under the stated rendering/hardware conditions. **Pending expansion art and browser evidence.**

### H-5 — Death, camp respawn and travel can create unexplained downtime

**Evidence / mechanism:** E-4. Camps first appear at 30 s and return 40 s after defeat. Death removes temporary buffs; walking back toward a spent camp may produce frustration if its state is hidden. Some downtime is also useful for planning and prevents uninterrupted resource farming.

**Decision:** expose inactive/dead camp status and the relevant countdown when nearby, plus the player's respawn state. Keep a lane objective visible while a camp is unavailable. Do not add automatic rematches, mandatory waits in menus or permanent progression punishment. Preserve the eight-minute endpoint and explicit replay.

**Acceptance / owner / state:** systems verifies spawn/respawn/buff-death timers; root/QA verify no inactive target is presented as attackable and that replay starts a clean match. Future observations should distinguish useful planning from unclear waiting; no engagement effect is inferred from timer correctness. **Pending.**

### H-6 — A bot-filled room can be mistaken for public matchmaking, and a frozen connection for a fair loss

**Evidence / mechanism:** E-3. Existing local two-context/reconnect and loopback socket checks do not establish WAN quality, operated public matchmaking or a deployed public WebSocket service. Static hosting supplies Practice. Bots are useful for immediate learning but must not be represented as real players.

**Decision:** label Practice, bots, invited online rooms and server address explicitly. Show connection/reconnect status without fabricating active opponents or successful actions. Keep input, purchases and rewards server-owned; rejoin restores one live identity rather than a duplicate. A disconnect must not award a shard locally.

**Acceptance / owner / state:** root/systems/QA run two real clients, rejoin, stale-input cleanup and identity/reward checks on the new protocol. There is no ranked matchmaking or operated public WebSocket backend in this release. Delayed/lossy WAN, real-region latency and physical-device performance require separate measurements; local stress percentiles and software-render browser checks cannot close them. Do not add a “match found” fiction to an invitation flow. **Baseline local checks exist; expansion regression and public service remain separate gates.**

### H-7 — Character quality and identity may fall short even when models technically load

**Evidence / mechanism:** E-2/E-3. The user rejected primitive presentation. Fourteen imported, skinned and animated hero models are a concrete improvement, but the existing provenance/numeric/browser evidence does not establish generated-key-art parity or human approval. New ministers and creatures could become interchangeable humanoids if only color changes.

**Decision:** use the agreed silhouettes and original costume/weapon details: polearm, compact shield, tall scroll/collar, broad crown, serpent hood/tail, heavy woodland body and folded wings. Keep cultural associations in [source notes](MINIONS_AND_JUNGLE.md#literary-sources-and-adaptation-boundaries) and visible gameplay descriptions focused on actual behavior. Do not replace named source characters with a farmable creature or invent claims of religious/historical accuracy.

**Acceptance / owner / state:** research/world/audio verify all seven real assets, independent instances and actual idle/run/fire/defeat motion; QA inspects front/side/action frames at gameplay scale. Human identity/art feedback is a distinct future gate. Budgets and imported-asset success alone cannot establish visual quality. **Pending new asset and visual review.**

## Review loop and evidence rules

The next bounded pass first closes authority/reward correctness and integrates the readable HUD; then captures native examples for H-2/H-3/H-4/H-6 and records a complete match. It reports actual pass/fail, source revision, setup, device/rendering limits and unresolved cases. It does not turn a failed native case into an unlabelled fixture or reuse a pre-expansion pass for new mechanics.

If a direct player-review source becomes accessible, add its exact URL, platform, publication date, retrieval date, known game version/locale, selected passage and access limitations. Preserve the writer's reported experience separately from verified game rules and our inference. Include relevant positive/mixed accounts and existing settings that may address the issue. Such a purposive sample can inform hypotheses but cannot estimate prevalence or prove causation from votes or repeated search results.

No user-session study, measured physical-device performance or real-region latency result has been produced in this pass. Bot benchmarks are not human balance evidence, and this review does not claim to have fixed all Deadlock criticism. Do not expand the release into a new progression system or matchmaking service solely to answer a hypothetical complaint. The immediate deliverable is a clear, coherent version of the existing match, followed by evidence for its actual limits.
