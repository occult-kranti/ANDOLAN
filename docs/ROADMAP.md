# ANDOLAN production roadmap

The user’s v0.3 plan defines a browser-native open-world production. The current implementation creates a condensed six-chapter development preview with a complete ending. Completion of the preview is not completion of the 22-mission production.

## Current bounded milestone

**First Edition:** a small authored district, walk/drive transitions, an authoritative shared session, the six-chapter story, readable evidence, meaningful choices, epilogue and replay. Content has 22 stages and seven decisions. Play time, device coverage and external usability remain measurements to collect.

The panel reduced map scale from the handoff’s approximately 500 × 500 metre first district to a 200 × 200 unit block set so every landmark has a purpose. It condensed selected campaign beats to test continuity and the final choice now. This does not cancel the original chapters or the multiplayer roadmap.

The six user-requested design/review rounds are closed for the preview and tracked separately from production gates below in `PANEL_LEDGER.md`. The selected physical campaign, targeted real-crew journeys and labelled replay/presentation checks passed in separate runs. Completing a review round does not complete the similarly numbered production milestone. Detailed campaign and deployment evidence must be read from `QA_REPORT.md` and release documentation rather than inferred from this roadmap; external deployment remains a separate release gate.

## Gates, in dependency order

| Gate | Work | Exit evidence |
| --- | --- | --- |
| R0 — References | Inspect REA and a permitted controller reference, pin sources, specify a narrow subsystem, record licenses. | Actual analysis artifact and implementation tests; distinguish source reading from gameplay observation. |
| R1 — Feel of play | Camera, walk/drive transitions, collision, a useful hub, route clarity and comfort settings. | Browser journey walk → car → clinic → board, screenshots and device/frame-time/load measurements. |
| R2 — Shared private session | Authoritative seats, missions, votes, reconnect and commands. | Two real browser clients plus network tests for conflicts, duplicate commands, disconnect and resume. |
| R3a — First Edition preview | Six condensed chapters, authored dialogue, documents, choices, five endings and replay. | Content integrity, exhaustive ending reachability and complete browser campaign traversal. |
| R3b — Last Delivery production slice | Expand the opening to its full staging, monsoon atmosphere, traffic, animation, audio, assisted driving and authored diversion. | Novice completion, coherent audiovisual presentation, checkpoint recovery and measured low-spec operation. |
| R4 — Public district alpha | Accounts, regional matchmaking, moderation, reports/block/mute, transactional public rewards, durable profile storage and crash recovery. | Controlled external playtest, abuse tests and measured operational cost/capacity. A development public room is not this gate. |
| R5 — City and campaign | Six districts and 22 produced missions; crew variation, interiors, side jobs, localization and animation/audio production. | District and mission acceptance records; narrative continuity and save migration pass. |
| R6 — Public production launch | Capacity, supported-device matrix, content/asset review, backups, rollback, incident ownership and service policies. | Verified release candidate, operations rehearsal and tested deployment. |

## Next production increments after the preview gate

1. **Validate the released preview with players.** Record whether first-time players find the car and clinic, distinguish the two source records, identify a decision’s cost and explain their ending. Measure supported hardware and online sessions separately. Automated traversal does not replace these observations.
2. **Produce the opening as an authored scene.** Improve character animation, acting, environmental sound, camera treatment and the in-world diversion while preserving authority and recovery. Recorded voices and a longer opening are new production work.
3. **Add a branch-specific encounter before more numerical scores.** Build a different playable consequence of one depot or sponsor decision, including save/restore and shared-room behavior. Present callbacks are text variations along a common route.
4. **Expand one original mission family at a time.** Produce The Empty Chair or the full Two Copies venue, then assess throughput and playtest evidence before expanding the next district. Keep all original titles below; compressed beats are not completed full missions.
5. **Advance public-service infrastructure independently.** Regional discovery, accounts, moderation, abuse handling, profiles and operational ownership precede unrestricted public launch. Publishing a private/solo preview does not satisfy those requirements.

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
