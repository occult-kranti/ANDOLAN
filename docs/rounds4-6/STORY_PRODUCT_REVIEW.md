# Rounds 4–6 · story, onboarding and crew flow

This is the additional three-round cycle requested after rounds 1–3. It reviews the current product and code; it adds no new mission, book list or content-semantics version. The six-chapter, 22-stage acceptance route remains stable.

## Round 4 — inspect and decide

**Artifact reviewed:** `apps/client/src/main.ts`, `apps/client/src/connection.ts`, `packages/sim/src/index.ts`, the current campaign and browser-test definitions. The archived screenshot `docs/evidence/world-desktop-game.png` was inspected for the first-session objective and interaction presentation; it is not evidence of a fresh late-join session. Current join/vote findings below are source observations until exercised in a browser.

**Existing strengths retained:** the HUD names the current objective and destination; the scene has a contextual interaction button; choices remain server-owned; the private dialog shows votes per option and explains that a tie waits. The server resolves a majority of all connected crew, requires voters to be near the target and on foot, and records the resolved choice once. Public development rooms use their own one-vote rule. These rules should be described accurately, not replaced by invented character roles or permissions.

### Accepted P1 — bring a joining player into the current story

**Evidence:** `begin` resets `lastHistoryLength` to −1, so the first snapshot correctly avoids replaying every old choice toast. However, `showCrew` only showed room instructions, player names and a ready signal. A player joining an advanced room spawned at the garage with the current objective but no concise explanation of the crew’s completed decisions.

**Impact:** a newcomer can affect the shared narrative without understanding its current premise. Reading every archived document is disproportionate to the immediate task. This is a predicted task cost, not an observed human failure rate.

**Decision:** the root/UI owner adds current chapter and objective, up to three completed decisions with their existing consequence receipts, and each player’s actual transport role to the existing Crew panel. Offer the panel once on an initial mid-story join. Roles mean **on foot**, **driver** or **passenger**, as recorded by the server; they confer no invented specialist ability. Preserve the normal automatic ending for a completed campaign.

**Acceptance:**

1. A new player joining after the first decision can see the current chapter, objective and latest resolved choice without reading future chapters.
2. The recap is derived solely from canonical completed history; it shows no pending vote as a completed outcome.
3. Three or fewer decisions appear in chronological order with the same receipts used by the journal.
4. A transient reconnect does not repeatedly reopen the panel or interrupt a conversation.
5. Driver/passenger/on-foot labels agree with the server’s seat state; joining is not presented as acquiring a special narrative role.

### Accepted P2 — keep a shared decision visible outside its dialog

**Evidence:** vote counts and the majority explanation lived inside `mission-dialog`. The dialog can be closed while the authoritative vote remains pending. A remote crew member or late joiner does not see that another player is waiting, even though every connected crew member contributes to the required majority.

**Impact:** progression can appear stalled without an obvious next action. Being told “two matching votes” only after reaching the encounter provides too little context to someone still at the garage or seated in the car.

**Decision:** the root/UI owner adds a compact pending-vote HUD status naming the destination, the number who have voted, the required matching count, the player’s own vote and the relevant next action. Keep the existing detailed per-option dialog and vote-changing behavior. Use existing snapshot state; do not create a separate client-owned vote state.

**Acceptance:**

1. After one of two private crew members votes, both can see that a shared decision is pending even with the conversation closed.
2. “Votes cast” and “matching votes required” are labelled distinctly. A 1–1 split is not presented as completion or 100% progress.
3. An unvoted player outside the location is directed to that named destination; a seated player is told to stop/exit before voting; an eligible nearby player receives the interaction action.
4. Changing a vote, joining, disconnecting or resolving the decision updates the status from the next authoritative snapshot.
5. The status clears when the stage advances. Solo play and the public development room are not incorrectly described as private-majority voting.

## Round 5 — implementation review

The moderator accepted P1 and P2. Root implemented the Crew recap and pending-vote HUD after the prior QA freeze. Story/content data is unchanged. The story reviewer then independently reread the changed `showCrew`, welcome/snapshot callbacks, `updateHUD` and dialogue gate against the server contract.

**Accepted in source:** the recap reads at most three completed history entries in chronological order; transport role derives from actual vehicle/seat state; `hasWelcomed` prevents transient reconnect from repeatedly opening it; pending-vote text distinguishes total ballots from the matching threshold; authoritative snapshots clear the status when votes reset. Destination interaction dialogue is now gated by target proximity, correcting the earlier clinic callback timing issue. Travel dialogue remains available while moving.

**Corrections reported to root before acceptance:**

1. A first join to a completed room calls `showEnding` in `updateHUD`, then the automatic recap calls `showCrew`, replacing the ending while `endingShown` remains true. The auto-recap must exclude completed campaigns so the result retains priority.
2. The unvoted-player hint always says to exit even when the player is already on foot at the destination. Derive the next action from actual transport state and distance, using the current interaction binding where relevant.

These were source observations, not browser failures. Root landed both narrow fixes; the independent reread accepts them. Automatic recap now requires an incomplete mission, preserving the ending. The unvoted hint checks distance first, then vehicle occupancy, then presents the configured interaction key. QA owns their rendered verification. The reviewer did not modify app/content files during the freeze.

## Round 6 — verify release candidate

Required evidence is a supported browser check of initial mid-story joining, a visible pending vote with the dialog closed, a split vote, state update after agreement and stable reconnect behavior. Existing simulation/network tests remain evidence for the server’s rules; they cannot by themselves establish readable UI or unobstructed input. Record actual tested results and remaining limits here or in the consolidated panel ledger. Deployment verification belongs to the parent release workstream.

**Observed artifact:** `../evidence/round6-campaign-evidence.json` contains all 22 visited stage IDs, seven canonical decisions and the completed Open Windows ending. The story reviewer also viewed `../evidence/round6-campaign-ending.png`, which renders that ending. QA reports source cards asserted at comparison and hearing, plus the reserve-van callback checked at clinic arrival. These establish a selected physically traversed campaign and its displayed outcome, not every branch or replay behavior.

**Follow-up regressions passed:** completed-room ending priority passed in a labelled mocked-welcome presentation fixture (9.1 s). Native-confirm replay passed in a reconstructed checkpoint using the physically earned mission/player data, default vehicles and a fresh command ledger (5.5 s). It reset through the real Story simulation to `keys` and zero history. These are bounded presentation/replay checks, not another campaign traversal or real multiplayer proof. The earlier physical test's dismissed native confirmation remains recorded as a harness failure.

**Real crew checks passed:** the final two targeted tests used independent browser contexts and real WebSocket rooms, with no state fixtures. Movement, distinct seats, rejected passenger driving and Take the wheel passed in 19.7 s. Physical walking to the clinic, correct on-foot voting guidance, a visible 1–1 split outside the dialog, changed ballot/consensus and canonical late-join recap with the actual on-foot role passed in 100.2 s. Closing the initial recap kept it closed through subsequent snapshots. That last assertion covers continued snapshots, not a new physical reconnect journey; reconnect suppression also has source/connection-test coverage. The story reviewer read the original `test-results/final-crew-split/results.json` and viewed its recap/tie screenshots. Stable committed evidence is `../evidence/round6-crew-results.json`, `../evidence/round6-late-join-recap.png` and `../evidence/round6-private-crew-vote-tie.png`.

**Round 6 closed for the preview review.** Earlier software-rendering travel and larger-canvas interaction timeouts remain documented in `../QA_REPORT.md`. Final real-crew checks use fixed 400 × 500 viewports and separate short seat/handover and walking/vote/recap journeys; the physical campaign separately covers driving. These passed targeted checks do not amount to one all-green full-suite invocation or a consumer-hardware performance result. The consolidated `../PANEL_LEDGER.md` records each evidence scope. External deployment remains with the parent release workstream.
