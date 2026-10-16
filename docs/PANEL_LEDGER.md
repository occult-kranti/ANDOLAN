# ANDOLAN panel and verification ledger

This ledger tracks **the six rounds explicitly requested by the user**. Earlier bootstrap and continuity review is baseline history, not another set of numbered user rounds. A source review, a test result and a browser observation are separate evidence. Repeating a report about an unchanged artifact does not constitute another round.

Separate narrative/content, world/art, simulation/network, reference/game-theory and QA agents contributed, coordinated by the root UI/release agent. An additional independent narrative reviewer checked revised content. These are AI perspectives, not human playtest participants or professional endorsement.

## Current round status

| User round | Changed artifact / decision | Evidence and current result |
| --- | --- | --- |
| 1 — Study and diagnose | Selected readings, causal beat sheet, source comparison, visible consequences and depot tradeoff proposals. | Read scopes and pinned sources in `library/STORY_DESIGN.md`; moderator accepted bounded changes. |
| 2 — Implement and challenge | Content 0.5.0: two source cards, hearing bundle, 21 receipts, nine callbacks and genuine depot priorities. | `npm run test:content`: nine tests passed; all 2,187 choice sequences enumerate to five reachable endings. |
| 3 — Verify the story revision | Independent continuity and decision review of changed content; integration defects forwarded to UI. | Content accepted within source scope. Destination dialogue was found to play too early; a later UI gate addresses it in source. Final rendered evidence is consolidated in round 6. |
| 4 — Diagnose onboarding and crew flow | Late-join context and pending votes reviewed against actual client/server rules. | Two improvements accepted: current-story recap in Crew and pending-vote status outside the conversation. |
| 5 — Implement and review crew flow | Recap, transport roles, pending-vote HUD and destination dialogue gate implemented. | Independent source review accepted the implementation and both follow-up fixes: completed-room ending priority and state-aware voting guidance. |
| 6 — Verify release candidate | Stable browser traversal, two-client behavior and release checks on the changed build. | **Closed for the preview review.** Selected physical campaign, two targeted real-crew tests and labelled replay/completed-room regressions passed. Evidence comes from separate runs, not one all-green full-suite invocation. External deployment remains a separate root release check. |

## Baseline history — before the requested six rounds

Inputs were the full user-supplied v0.3 plan, replacement prompt and Last Delivery schema; the checkout initially contained a README. The handoff described a city-first, 22-mission production and explicitly said it was not a built game.

The team established a condensed six-chapter preview in a roughly 200 × 200 unit district with nine meaningful destinations. The full 22-mission slate remains in `ROADMAP.md`; the preview is not the proposed six-to-ten-hour production.

| Baseline finding | Impact | Implemented correction | Acceptance evidence |
| --- | --- | --- | --- |
| A score-only epilogue could contradict a limited settlement. | Explicit final agency was lost. | Saved final choice takes precedence over metric thresholds. | Regression tests cover settlement, coalition and independent-review outcomes. |
| A hearing document treated every conflict as public. | Conceal/disclose branches contradicted the archive. | Separate private dossier, disclosed consulting conflict and unopened wider donor file. | Independent narrative reviewer accepted corrected branch traces. |
| A shorter article implied hiding an earlier publication, although only a draft existed. | Careful players were accused of an action they had not taken. | Establish unpublished notes and a service-focused alternative. | Independent reviewer accepted the narrow → interview → short-article route. |
| Engineer qualification overstated what the amendment corroborated. | Evidence standards were inconsistent. | Limit corroboration to redirection; retain objection as attributed testimony. | Each claim maps to the actual authored record. |
| Depot convergence lacked dispatch explanation; aliases differed from map labels. | Causal continuity and navigation were weaker. | Add dispatch bridge and canonical arrival labels. | Independent source review and content-reference checks. |

The initial content gate passed six tests. Later rounds expanded it to nine; the earlier result is historical, not an additional current gate.

## Rounds 1–3 — study, implement, review

Selected readings included Aristotle’s *Poetics*, inkle’s branching/history documentation, Schreiber’s decision and nonlinear-narrative lessons through a pinned archive, and Sinander’s author-hosted strict-dominance definition. No complete-library reading is claimed. Emily Short’s site was blocked by the network proxy and is explicitly not claimed as read. Exact scope, links and limitations are in `library/STORY_DESIGN.md` and the source register.

| Finding / evidence | Task impact | Moderator decision and owner | Observable acceptance | Result |
| --- | --- | --- | --- | --- |
| Content 0.4 summarized both records; causal recognition lens from *Poetics*. | Player receives a conclusion before inspecting its basis. | Story/UI: distinct original order and amendment at the decision. | Two readable records before characterization, each with source and qualification. | IDs/content verified by tests; QA asserted the source cards in the physical route's comparison dialog. |
| Branches rejoined with identical scenes; Schreiber Parallel Paths and inkle labelled history. | Choices can feel disconnected from endings. | Story/systems/UI: specific receipts and later conditional responses. | Immediate receipt and later/restored response match canonical history. | All 21 receipts and nine variants implemented; prior-choice references and restoration tested. |
| Depot photo option lost every authored value without compensation. | Apparent choice functioned as a punishment button. | Story: competing dispatch, witness and authorized stock-record priorities. | Each offers a legible gain and cost; evidence and clinic response agree. | Pairwise-delta test passed; independent weighted-profile diagnostic accepted. |
| Hearing needed a bundle and current disclosure state. | Finale could be detached from what is known and public. | Story/UI: hearing documents and history-derived disclosure status. | Earlier public disclosure cannot become private through a later deal. | Tested; independent narrative reviewer accepted source semantics. |

**Scope decision:** defer a new epilogue location/mission. Retain the newsroom return and text epilogue so the 22-stage browser route stays stable. This is a deferred production item.

**Independent result:** content 0.5.0 passed bounded semantic review. Original records, qualified testimony and the depot records are consistent. Receipts describe authored consequences, not a simulated delivery timer, physical stock-counting minigame or separate branch level. `library/decision-diagnostic.json` illustrates preference sensitivity in authored values; it is not a model of real politics or universal utility.

**Integration finding carried forward:** the client originally queued destination dialogue immediately on stage change, allowing a clinic response to subtitle at the depot. Root added a destination-proximity gate while retaining travel narration. Source review accepts the gate; QA's physical route checked the reserve-van clinic callback at local arrival. The other variants have source/restoration coverage, not separate full browser traversals.

## Rounds 4–5 — inspect and revise social flow

The story/product reviewer read `main.ts`, `connection.ts`, simulation voting rules and the campaign, and inspected `docs/evidence/world-desktop-game.png` for initial task presentation. That archived screenshot is not evidence of a fresh late-join session. Detailed acceptance cases are in `rounds4-6/STORY_PRODUCT_REVIEW.md`.

| Finding / evidence | Task impact | Moderator decision and owner | Observable acceptance | Result |
| --- | --- | --- | --- | --- |
| Initial snapshot suppressed old toasts, but Crew showed no story context. | Newcomers could affect the story without understanding prior decisions. | Root UI: current task, latest three completed receipts and actual transport state in Crew; offer once on progressed join. | Past history only; no repeat interruption on reconnect; completed campaigns retain their ending. | Source accepted after the completed-room guard fix. Real late-join recap, actual on-foot role and remaining closed through later snapshots passed; completed-room presentation fixture passed. Transient reconnect suppression retains source/connection-test coverage. |
| Vote counts existed only in the encounter dialog. | Progress could appear stalled to distant or seated crew. | Root UI: persistent cast count, matching threshold, own vote and next action. | A split remains pending; guidance matches seat/location; resolution clears the status. | Source accepted after state-aware guidance fix. Real crew walked to the clinic; on-foot hint, visible 1–1 split outside the dialog, changed ballot and consensus passed. |

Content version and all 22 stage IDs remained unchanged. Root owns UI fixes; reviewers did not edit app/packages during the frozen campaign run.

## Round 6 — final verification register

A source freeze protected the real physical campaign traversal. Source edits invalidated an earlier test through a Vite reload; it was neither a pass nor a gameplay/network failure. The final campaign traversal and ending completed, but its following replay assertion dismissed the native confirmation in the test harness. Corrected, separately labelled replay and completed-room checks subsequently passed. Co-op follow-ups preserved a software-rendering travel timeout and a larger-canvas interaction timeout. The final two real-crew checks passed with fixed 400 × 500 viewports: a short movement/seat/handover test and a physical walking/vote/recap test. They retain ordinary input and the authoritative server, with no state fixtures. Driving remains covered by the separate campaign and controls checks.

**Review closure:** the six requested rounds are complete for this development preview. Passing targeted follow-ups closes the changed-feature review; it does not rewrite the earlier failed runs or claim a single all-green full browser suite. The remaining deployment row belongs to the release workstream, and full-production milestones remain open in `ROADMAP.md`.

| Gate | Evidence owner / artifact | Current status |
| --- | --- | --- |
| Source/choice integrity | Story; `tests/content.test.ts` | Nine of nine passed, including 2,187 decision sequences and five endings. |
| Independent story/decision review | Narrative reviewer and reference agent; library diagnostics | Accepted within source/diagnostic scope. |
| Two final UI corrections | Root implementation; independent story reread of `main.ts` | Accepted in source: ending keeps priority and vote action matches location/seat/key. |
| Final automated source gates | Root; four test files, lint and typecheck | Root reports 42 tests passed, with lint and typecheck passing. Content's nine tests are included, not additional tests. |
| Keyboard, menus, vehicles and save flow | QA; `QA_REPORT.md` | Desktop controls/settings/save smoke passed in 35.5 s; mobile browser layout passed in 6.5 s. These are Linux Chromium checks, not physical-device validation. |
| Two independent browser clients | QA; `evidence/round6-crew-results.json` | Both targeted tests passed with no unexpected or flaky result: movement/seats/passenger authority/Take the wheel in 19.7 s, and physical walking/voting/recap in 100.2 s. Independent real WebSocket contexts, no state fixtures. |
| Full selected campaign and ending | QA; `evidence/round6-campaign-evidence.json` and `evidence/round6-campaign-ending.png` | Passed the selected physical route: all 22 stage IDs, seven resolved choices and Open Windows. Story reviewer read the artifact and viewed the rendered ending. This is not replay proof. |
| Replay | QA; separately labelled earned-data checkpoint regression | Passed in 5.5 s with native confirmation accepted. Reconstructed checkpoint uses earned mission/player data plus default vehicles and command ledger; the real Story simulation reset to `keys` and zero history. Not another full traversal. |
| Completed-room ending priority | QA; separately labelled mocked-welcome presentation regression | Passed in 9.1 s. Establishes dialog priority for this fixture; not real room completion or multiplayer evidence. |
| Recap and pending-vote presentation | Root/QA; `evidence/round6-late-join-recap.png`, `evidence/round6-private-crew-vote-tie.png` and final real-crew assertions | Correct on-foot hint, visible 1–1 split outside dialog, ballot change/consensus, canonical late-join recap and on-foot role passed. Closing the recap kept it closed through subsequent snapshots. Story reviewer read results and viewed recap/tie screenshots. |
| Destination dialogue and source-document presentation | QA; selected physical route | Reserve-van clinic callback checked on local arrival; comparison and hearing document dialogs asserted. Other narrative paths retain source-test coverage. |
| Served container and persistent room state | Root; `evidence/container-check.json` | Root reports non-root container, real WebSocket progression and room-state persistence through volume-backed restart passed. External reachability is a separate gate. |
| Production browser and public invite | Root; `evidence/production-browser-check.json` | Passed local HTTP load, offline controls/driving, save after reload, no external requests/errors and a public invite preserving mode/room. Direct file navigation was blocked by managed Chromium policy; that path is not claimed tested. |
| Deployment reachability | Root release workstream | Root must record actual URL and limits. |

This remains a development preview. Automated completion establishes that the selected route can finish. It does not establish every branch’s emotional quality, human comprehension, mobile hardware performance, internet-scale capacity or completion of the full 22-mission production.
