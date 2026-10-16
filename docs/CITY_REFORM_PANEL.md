# City Reform: three review passes

This increment responds to the user's feedback that flow, controls, sound cues and Settings did not feel smooth, and their request for fictional media satire, linked sector cases and a later betrayal route. It follows the City Jobs baseline, whose ten browser cases passed in 491.765 seconds. These are agent reviews and automated checks, not human playtesting.

## Pass 1: turn feedback into playable scope

The panel divided work among content, authoritative systems, audio, world/camera, UI/control review and browser QA, with root integrating the client. The accepted scope keeps the existing district and five repeatable jobs, adds an opening media case and four sector cases, then a permanent crew mandate. The original Story and its save remain separate.

The opening case uses the requested fictional parodies Republic Times and Grnab Aoswami. Earned event receipts and six authored press cards carry jokes and developments without interrupting play with a new forced conversation. The cases cover energy, welfare, natural resources and public procurement. The final choice either publishes the complete case or betrays allies by sealing a sponsor annex. Both routes have saved outcomes and different future job rewards. Credits remain a score rather than a spending economy.

The control review identified concrete friction: the briefing stayed open after accepting a timed job; Settings suspended the sound being adjusted; duplicate/reserved bindings were accepted; touch depended on fixed keyboard codes; larger text did not apply on reload; assistance weakened braking. The resulting implementation separates touch actions from keyboard keys, confirms a job before returning focus to play, adds an explicit audio preview, preserves full braking and introduces camera recentering and correctly sized destination markers.

## Pass 2: independent challenge and repairs

| Finding | Evidence | Repair and review |
| --- | --- | --- |
| Assistance multiplied braking by 0.55. | A real Simulation probe from 12 m/s stopped in 0.50 s / 2.70 m normally, versus 0.95 s / 5.13 m under the old assistance mapping. | Assistance now scales acceleration only. Dedicated braking is a validated server input. |
| The first dedicated-brake implementation could oscillate across zero. | The world reviewer reproduced alternating +0.6 / -0.6 m/s under ordinary simulation ticks. | Sign-preserving server deceleration reaches zero and holds there. An independent re-probe from both directions, stale inputs and release passed; regression tests cover the transition. |
| A gamepad A+Y+forward tick could open a menu, then enter a car and send motion behind it. | Source-extracted actual input functions reproduced the command and nonzero motion. | Vehicle actions guard modal state; input is rechecked after discrete actions. The same probe now sends no vehicle command and zero movement/brake/sprint. |
| A delayed native menu-close event erased a newly pressed movement key. | Three native browser probes recorded W before the asynchronous close event, then no movement for 800 ms. | Remove the redundant delayed input clear; opening a menu already releases controls synchronously. Immediate post-close driving is a regression gate. |
| Older configured servers lacked the city state required by the new client. | Previous releases emitted protocol 1 without the new snapshot fields. | Protocol 2 plus a client compatibility gate produces an actionable update-server message before accepting identity or rendering. Save schemas 1/2 still migrate to 3. |
| Early ledger copy revealed the betrayal before the crew earned the cases. | Independent systems review of the UI. | Mandate route details stay locked until all five cases are filed. |
| Job-detail replacement could lose keyboard focus on a shared stage update. | UI source review and a DOM fixture. | Preserve relevant control focus/expanded tips, or move focus to the briefing heading. |
| A fade followed by immediate suspension froze the fade; previewing Settings was impossible. | Audio source review and prior native browser observations. | Cancellable fade-before-suspend, explicit isolated preview, quieter grouped notifications and gear hysteresis. |
| Persistent case or vote state might bypass requirements after restart. | Independent authority audit, seven additional malformed-save probes and real WebSocket tests. | Invalid saves are rejected; unique case ledger, location/prerequisite guards, majority voting and permanent reward policy are server-owned. No unresolved blocker was found. |

The world, audio, authority and UI owners completed their assigned implementations. The root’s source run passed TypeScript, ESLint and 134 tests after the modal/input repairs. Native focused checks and the actual two-client media route subsequently passed. Final integrated results are recorded separately below rather than inferred from these reviews.

## Pass 3: play and release evidence

See [CITY_REFORM_QA.md](CITY_REFORM_QA.md) for final results and exact limits. Release run 38857615158 on `c20e912` passed 134 tests and all thirteen browser cases (reported 11.8 minutes), including the original campaign/replay, physical two-client van delivery, five-stage media case, touch/rebinding/braking, native Settings audio and labelled final-mandate fixtures. Both final choices are covered without claiming physical traversal of all sector routes. The earlier van-entry CI failure is retained in the QA history; a test-only server-acknowledged stop barrier and clearer diagnostics preceded the passing full run.

Final screenshot review confirmed that the small-screen speed display clears the Vehicle, Brake and Camera buttons after the layout correction. A fresh, ordinary recovery-job approach showed the destination radius around the actual compact, a readable WALK cue and the contextual recovery action, with no page errors. At close range a plaque subtitle can sit behind the top-right HUD; the primary cue and action remain readable. This is a remaining visual refinement, not a verified gameplay blocker.

The release built and deployed successfully. Both public URL variants return the exact verified standalone HTML. The native live-site check passed in 28.889 seconds with ordinary UI input, saved-state restoration, settings and already-loaded offline play; its exact scope is recorded in the QA report. Pages runs City practice and Story and can connect to a separately hosted server. No operated public backend has been provisioned; shared internet rooms require the persistent server described in [MULTIPLAYER_HOSTING.md](MULTIPLAYER_HOSTING.md).
