# First Edition — implemented content design

Content version **0.5.0**. Original material adapted from the user-supplied ANDOLAN v0.3 handoff. Implementation source: `packages/content/src/index.ts`; world coordinates: `packages/sim/src/world.ts`. Source-led story revisions are in `library/STORY_DESIGN.md`; the six requested review rounds and current verification status are consolidated in `PANEL_LEDGER.md`.

## Scope and story

This six-chapter preview compresses selected beats from the 22-mission campaign into a complete short arc. It is a development preview, not six fully produced cinematic missions or the full six-to-ten-hour game. The primary play space is a roughly 200 × 200 unit district. Public online launch, regional matchmaking, voiced performances and the full city are separate roadmap gates.

One clinic receipt sends Aadi, Noor and Kavya from a garage to the records office, depot, riverfront, print shop and civic hall. The crate diversion is real within the fiction; a suspicious surname match is innocent. Their sponsor has a conflict of interest. The final choice tests whether accountability applies to the new leadership as well as the old one.

## Chapters and concrete actions

| Preview chapter | Play sequence | Decision and consequence |
| --- | --- | --- |
| 1. Last Delivery | Garage keys → enter car → Night Clinic → River Steps → newsroom board | Ask for an explanation, obtain an authorized copy, or entrust the original to Kavya. Changes the first document and relationship emphasis. |
| 2. Two Copies | Records office → compare two source cards → garage board | Limit the claim, write an unsupported accusation, or prioritize affected people. Establishes the correction arc. |
| 3. Empty Shelves | Mill depot → clinic → riverfront engineer | Prioritize earlier dispatch, a fuller interview or an authorized stock count. Each leaves a different part of the visit incomplete; the clinic recalls the choice. |
| 4. First Edition | Print shop → garage board | Publish a transparent fact check, focus on the service repair or make a sweeping allegation; then disclose, return or conceal Samar’s support. |
| 5. Open Microphone | Square → print shop | Share the microphone, focus on services or restrict the message. Collect Asha’s concrete but limited offer. |
| 6. The Public Hearing | Civic Hall → garage epilogue | Seek an open review, take a service settlement or protect the coalition’s future. Return for the six-month outcome. |

There are **22 stages and seven three-option decisions**. The common route remains fixed; decisions change documents, relationship scores, the recorded history, nine authored dialogue variants and the final outcome. All 21 options have an immediate consequence receipt. Decisions do not currently generate different levels, timed action scenes or fully separate mission graphs. This keeps travel and narrative coherence testable while establishing consequence handling.

## Mission contract

Every chapter contains stable `id`, `title`, `description` and ordered `stages`. A stage declares `id`, `objective`, `targetId`, `trigger`, speaker-labelled `dialogue`, optional `evidence` and optional `choices`.

`documents` optionally exposes specific case material at a decision. `dialogueVariants` optionally maps an exact prior chapter/stage/choice tuple to an authored response. `getStageDialogue` resolves this from canonical history; it accepts no arbitrary expressions. Saved-history restoration uses the same resolver. `getChoiceConsequence` supplies the persistent receipt. `getDocumentStatus` keeps the sponsor’s prior public disclosure distinct from crew-only knowledge and the unopened wider donor file.

Allowed triggers are `arrive`, `interact`, `enter_vehicle` and `choice`. Mission data cannot execute JavaScript strings or issue arbitrary commands. The simulation handles prerequisites, position, seats, choice votes, revision and completion. It runs in the browser for local Solo Story and on the Node server for shared rooms. Canonical mission state is outside the rendering loop.

Content documents expose `id`, `title`, `source`, `body` and `qualification`. Qualification appears next to the finding. “The dates differ” and “the named person committed a crime” are distinct statements. Authored evidence IDs remain stable in saves.

## Modes, shared decisions and recovery

**Solo Story** runs the same simulation locally and saves to this browser. **Private crew** uses a server-owned room and shared campaign state. Private choices require more than half of the currently connected crew to select the same option. Voters must be on foot at the active destination; a tie waits, and a player may change their vote. A disconnected player’s pending vote is removed and the remaining majority is recalculated under the server’s explicit rules.

The Crew panel summarizes the current objective and up to three completed decision receipts. Driver, passenger and on-foot labels describe actual transport state; they do not assign specialist narrative powers. Pending-vote status distinguishes how many players have voted from how many matching votes are required. Targeted real-crew browser checks passed late-join recap, actual on-foot role, split-vote visibility and changed-ballot consensus; the ledger records their scope and the separate source, fixture and campaign evidence.

The **City sandbox** is a capped development room, with a one-vote resolution rule and separate state. It does not provide regional matchmaking, permanent public profiles, a production economy or moderation operations. A running reachable game server is required for online play.

Reconnect loads canonical room state; it does not invent missed events. Content 0.5.0 changes the depot choices, so old 0.4.0 saves are incompatible and the client reports that a new story has started. This is an explicit restart policy, not a tested save migration. Replay requires campaign completion, deliberate confirmation and a private room with one connected player; it does not let one crew member erase an active group’s campaign.

## Consequence model

Three bounded 0–100 values begin at 50: **trust**, **care** and **accountability**. Changes are authored narrative rules. These values do not label a real player’s political beliefs and do not predict how actual governments change.

The depot now offers three practical priorities. Earlier dispatch benefits care but leaves verification incomplete; a full interview strengthens the witness relationship but delays dispatch; an authorized physical count strengthens documentation but leaves less personal interview time. Each has a pairwise advantage and cost in the initial deltas. The player sees these tradeoffs and their consequences in words; the interface does not turn them into visible morality meters.

The final decision takes precedence over score thresholds:

- **The Bargain:** explicitly accept Asha’s service settlement. She stays in office; the clinic receives funding while the review remains limited.
- **A Different Chair:** explicitly protect the coalition’s future. Leadership changes while the donor file stays sealed.
- **The Broken Coalition:** seek an open review with trust below 45. The records survive; the crew separates.
- **Open Windows:** seek an open review with accountability at least 75, trust at least 65 and care at least 60. The review produces an accountable transition and a public challenge to the new council.
- **An Unfinished City:** seek an open review without meeting those conditions. Further disclosure proceeds without a complete resolution.

Explicit choices are read from saved history, not guessed from a score. Exhaustive enumeration of all 2,187 choice sequences checks reachability. This is narrative regression testing; it is not proof of balance, emotional impact or human usability.

Samar’s disclosed consulting conflict is distinct from the coalition’s unopened donor accounts. A later decision cannot make an earlier disclosure private again. The hearing dossier is the crew’s working file; the final decision controls its submission and the requested scope of review. Noor’s mistaken surname connection begins in unpublished notes, so a shorter service article does not imply concealing a previously published error.

## Navigation and interactions

| ID | Place | X | Z |
| --- | --- | ---: | ---: |
| garage | Yusuf’s Garage | -60 | 48 |
| board | The Newsroom | -68 | 43 |
| clinic | Night Clinic | 52 | -48 |
| archive | City Records | 48 | -66 |
| mill | Mill Ward | -48 | -68 |
| radio | Open Frequency / print shop | 65 | 0 |
| square | Assembly Square | 0 | 66 |
| civic | Public Hearing | 0 | 82 |
| river | River Steps | 82 | 48 |

Road axes run at -48, 0 and 48 on both coordinates. Missions use IDs, not copies of the positions. The renderer and simulation own map geometry. Display names can evolve without invalidating mission IDs.

The next task should identify both action and place. Conversation requires a deliberate interaction at its destination. Arrival objectives advance upon reaching the place. The first car stage teaches the vehicle transition explicitly. Driving is an option for later travel; the narrative does not require car chases, evasion or violence.

Arrival dialogue can accompany travel; destination interaction/choice subtitles are gated by proximity. The full conversation remains available through the interaction panel without a reading timer. Time spent in an automated driving/choice run is a test duration, not a claimed human campaign length.

## Presentation and accessibility

All scenes have text with speaker labels. No voice recording is claimed. Dialogue is short enough for a panel and can be read without an expiring timer. Choices have distinct text descriptions and no correct answer encoded only by color. Evidence is readable as text and available after discovery. Keep destination names consistent between the HUD, minimap and document board.

Audio, subtitles, camera comfort, control hints and recovery are engine/UI acceptance tasks. Automated content checks cannot establish that keyboard focus, text layout or camera comfort work; those need a rendered session. Neither skipped audio nor reduced visual effects should remove story or rewards.

## Boundaries for expansion

Retain the original 22-mission titles and act structure in `ROADMAP.md`. Promote a chapter from outline to produced only after its level, interactions, dialogue, recovery, state migration and replay have passed their gates. Add branch-specific events before expanding the score system. Gather human playtest observations before claiming duration or comprehension targets.
