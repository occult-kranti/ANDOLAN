# Story design library and three-round revision

This records the first three requested review rounds. The later onboarding/crew cycle is in `../rounds4-6/STORY_PRODUCT_REVIEW.md`; `../PANEL_LEDGER.md` consolidates all six rounds and the latest verification evidence.

**Reading scope:** selected sections of one public-domain book, an authoring manual, two game-design lessons and a formal game-theory definition. These are curated readings, not a claim to have read every book, reconstructed commercial games or validated a universal formula for good stories. The public-domain text and freely available articles/manual were retrieved over HTTPS. No paywall, account or rights restriction was bypassed.

## Sources actually read

| Source and exact accessible copy | Sections read | Useful principle | Limit of the transfer |
| --- | --- | --- | --- |
| Aristotle, *Poetics*, translated by S. H. Butcher. [Gutenberg text, pinned GITenberg mirror](https://github.com/GITenberg/The-Poetics-of-Aristotle_1974/blob/e995f0601890656604b168f7589d6c8c35eba1ba/1974.txt) | VI–XI and XV; contents and translator identification. | A sequence becomes a plot through causal connection. Recognition and reversal should arise from prior incidents; character is expressed through what people choose. | A theory of drama, written for a different historical audience. It does not establish game UX results or require a fixed three-act structure. We adapt causal coherence, not its historical social hierarchy or every normative judgment. |
| inkle, [*Writing with ink*](https://github.com/inkle/ink/blob/35c63e52f1d36060930dc7ed3cfba38ea224b528/Documentation/WritingWithInk.md) | Introduction; Part One §5 branching/joining and §7 conditional choices; Part Two gathers, nested flow and tracking a weave; Part Three global variables and conditional blocks. | Branches can rejoin without forgetting their consequences. Labelled history and conditional text retain local variation within a manageable common route. | This documents ink’s authoring semantics. ANDOLAN uses its own narrow declarative data and does not install ink, copy its game scenes or inherit its guarantees. We still test our branches. |
| Ian Schreiber, *Game Design Concepts*, Level 7, [Decision-Making and Flow Theory, archival copy](https://github.com/eugenioclrc/gamedesignconcepts/blob/5c98165cb261143bda0147463acbaee922ca46c9/lessons/07-decision-making-and-flow-theory.md). [Original](https://gamedesignconcepts.wordpress.com/2009/07/20/level-7-decision-making-and-flow-theory/). | “Things Not To Do,” “What Makes Good Decisions?” and adjacent context. | A choice can fail by being meaningless, obvious or blind. Tradeoffs include scarce time, competing actions and immediate versus longer-term value. | These are the author’s design categories, not measured laws of player preference. The original host returned proxy 403; the pinned mirror was read. Its fidelity was not independently compared against the unavailable original. |
| Ian Schreiber, *Game Design Concepts*, Level 10, [Nonlinear Storytelling, archival copy](https://github.com/eugenioclrc/gamedesignconcepts/blob/5c98165cb261143bda0147463acbaee922ca46c9/lessons/10-nonlinear-storytelling.md) | Branching and Parallel Paths; adjacent threaded-structure discussion. | Convergent paths contain production cost, but ending-only effects can hide the link between an earlier decision and its consequence. | The immediate receipt and later callback are our adaptation. We do not adopt the lesson’s informal complexity estimates as mathematical results. |
| Ludvig Sinander, [author-hosted game-theory notes, “Dominance”](https://github.com/ludvigsinander/Sinander_game_theory_notes/blob/eb0eabb9f53588c5651c5d5e17f0e360156c069d/ch_dom.tex#L146) | Definition of strict dominance and the following finite-game example/definition. | A formal dominance claim requires specified utility and all relevant opposing actions. | ANDOLAN’s trust/care/accountability vector is an original design instrument, not a scalar utility model of actual politics. Our test checks pairwise advantages and costs in authored deltas; it does not prove equilibrium, rationality or player enjoyment. |

The GITenberg and inkle pinned URLs returned exactly the bytes first inspected. SHA-256: Poetics `5c0ef9d0fa0479a2bbc11052f1e0a2d036698473c7b71b7a9633fda7c30f8c97`; inkle `0555b6ac648055967fd2c1b636d32e47180d6c4e69f2cb09144ecf5278fb5ecb`.

### Access limits

Direct requests to `classics.mit.edu`, `gutenberg.org`, `emshort.blog` and `emshort.wordpress.com` returned network-proxy 403. The available public-domain Gutenberg mirror supplied the Aristotle reading. Emily Short’s requested primary essay, [Beyond Branching: Quality-Based and Salience-Based Narrative Structures](https://emshort.blog/2016/04/12/beyond-branching-quality-based-and-salience-based-narrative-structures/), was **not read** and contributes no attributed claims here. The inkle documentation supplies an accessible primary choice-authoring source. These limits do not block the already authorized design work.

## From reading to this game

Aristotle’s causal test is useful as a deletion test: if the depot vanished, would the article, sponsor conflict and hearing still make the same sense? In the previous build, a player could understand most of the plot from summaries alone. The revision gives the depot its own tradeoff and preserves its consequences in a later clinic scene. It becomes a cause of the crew’s relationships rather than just another destination.

Inkle’s labelled-history technique gives a practical way to remember a branch without producing three versions of every future chapter. ANDOLAN adds exact-match `dialogueVariants` and `getStageDialogue(stage, history)`. The server derives dialogue from canonical history. It runs no uploaded expressions or arbitrary story scripts.

Schreiber’s decision lens exposes the depot’s earlier staged-photo option: it lost all three authored metrics and had no compensating capability. The new choice concerns three defensible priorities within one short visit. The player sees each cost in ordinary language before deciding, gets a specific receipt afterwards, and hears the result at the clinic. The UI does not display a morality score.

## Story spine and beat sheet

**Dramatic question:** can a crew turn a service failure into accountable change without giving its own allies an exemption?

**Player role:** Aadi’s movement and driving connect a multi-character investigation. The player chooses how the crew uses limited attention and what enters its public account. They do not control the entire city or issue instructions to real-world organizations.

| Chapter | Desire and playable task | Complication / recognition | Decision and later payoff |
| --- | --- | --- | --- |
| Last Delivery | Close the garage after one favour; walk, enter the car, drive to Night Clinic and return by River Steps. | The receiving record and paperwork disagree. A mundane explanation remains possible. | Choose explanation, authorized copy or custody. River dialogue remembers that exact choice. The board turns the favour into an investigation. |
| Two Copies | Obtain the public record and compare two actual source cards. | The original assigns twelve crates to the clinic; the late-published amendment redirects eight. Redirection is established; theft is not. | Characterize the finding, draft an unsupported accusation or prioritize the affected clinic. The choice preserves its document and a readable consequence receipt. |
| Empty Shelves | Visit the depot, resolve a practical shortage and interview the riverfront engineer. | A surname link is innocent. The stock, witness and delivery all compete for a short visit. The project can be useful while its procurement is flawed. | Dispatch first, hear the witness or document the stock. A route-specific record and later clinic scene acknowledge the concrete cost. |
| First Edition | Decide what the print shop publishes, then meet the sponsor. | Noor’s discarded assumptions test her credibility. Samar’s help exposes a conflict within the crew’s own coalition. | Publish a full fact check, service article or overclaim; then disclose, return or conceal funding. The square scene remembers the funding decision. |
| Open Microphone | Travel to Assembly Square and take the written government response to the print shop. | Meera, Tara and the garage need different things. Asha offers a useful remedy with a limited review. | Share voices, narrow the agenda or restrict the statement. The gathering cannot honestly be called unanimous. |
| The Public Hearing | Review the case bundle at Civic Hall, submit a position and return to the newsroom. | The bundle distinguishes public records, a ruled-out link and the crew’s own disclosure status. A change of leadership may preserve secrecy. | The final settlement choice is explicit; prior history changes whether an open review yields transition, fracture or unfinished work. The six-month ending names what changed and what remains unresolved. |

The route remains six chapters and 22 stages. Nine conditional dialogue variants, seven three-option decisions and five endings create variation within that shared route. The revision does not create separate levels or falsely promise that every option produces a new mission.

## Character desires, contradictions and turning points

| Character | Wants | Contradiction | Playable pressure / turning point |
| --- | --- | --- | --- |
| Aadi | Keep the garage open and be dependable. | Loyalty makes him promise more than a small workshop can give. | Prioritizing the clinic gives up verification time; returning sponsorship diverts the garage repair budget. The square recalls the unrepaired shutter. |
| Noor | Publish work that matters. | A clear, fast story is tempting when the record is complicated. | Compare sources before the first article; choose whether to show discarded assumptions or turn an unsupported draft into a public allegation. |
| Kavya | Make the record accurate enough to hold up. | Evidence alone does not keep a clinic open or make a witness feel heard. | The depot makes full verification compete with dispatch and testimony. She must state what the crew gave up. |
| Meera | Reliable care after the cameras leave. | She needs the crew’s attention but refuses to become its backdrop. | The clinic callback acknowledges which priority the crew chose. At the hearing she asks for service continuity alongside institutional change. |
| Samar | Finance a coalition capable of replacing the government. | He treats his own transparency as a cost that can wait. | His payment is either disclosed, returned or concealed. The finale distinguishes that conflict from the wider donor accounts still unopened. |
| Tara | Preserve the right to disagree with the next leadership. | She wants collective action without pretending the group has one view. | She responds to funding disclosure at the square; excluding disagreement later makes her leave. |
| Asha | Preserve stability and her administration’s authority. | Her practical offer limits who can inspect the underlying decision. | The player can accept services under a limited review or seek independent scrutiny. Her fate is an outcome of the authored campaign, not a claim about an actual politician. |

## Priority decisions accepted by the moderator

### S1 — Give the player the records before the claim

**Evidence:** the old `compare` stage summarized both documents in one line and a combined evidence entry. The player did not have distinct originals to inspect at the point of choosing a characterization.

**Change:** add `orderPublic` and `amendmentPublic`, expose them through the stage’s `documents` field, and render source/qualification beside each. Present the same pattern at the final hearing with the current disclosure status.

**Acceptance:** Two Copies displays two distinct authored records before the decision; both survive in the archive after completion. The sponsor card changes from crew-known to publicly disclosed only through an actual decision. A later coalition deal cannot erase a disclosure.

### S2 — Make a choice observable now and later

**Evidence:** original branches usually rejoined with identical dialogue, with most visible effects postponed until the final report. Schreiber’s parallel-path criticism and inkle’s labelled-history contract directly inform this finding.

**Change:** all 21 choices have a specific `consequence` receipt. Nine exact-match variants connect the clinic choice to River Steps, the depot priority to the clinic, and sponsor funding to the square. A restored snapshot resolves the same dialogue from saved history.

**Acceptance:** choose any depot priority, read a specific receipt, then encounter the matching clinic response; reconnect/restore cannot select another response. Empty or unrelated history uses the base scene.

### S3 — Replace the depot’s obvious best answer with competing priorities

**Evidence:** the former staged-photo option reduced trust, care and accountability without a compensating benefit. The arithmetic made it a punishment button rather than a practical dilemma.

**Change:** dispatch the reserve van promptly, hear the clerk’s complete account, or document the physical stock with authorization. Each creates a different evidence record and a distinct later clinic acknowledgment. Stage count and IDs remain stable for testing; `photo` is the stable internal ID for the new authorized stock documentation choice.

| Priority | What it secures | What it leaves incomplete | Authored deltas (engineering reference only) |
| --- | --- | --- | --- |
| Reserve van first | Earlier clinic supply | Full stock comparison | care +14, trust +2, accountability −4 |
| Full witness account | Relationship and testimony | Earlier dispatch | care −4, trust +12, accountability +6 |
| Authorized stock record | A checkable physical count | Personal interview time | care +3, trust −3, accountability +14 |

**Acceptance:** each option has an advantage and a cost relative to each other option in these initial deltas. The text describes the tradeoff. This check is a design sanity test; caps, prior state, ending thresholds and individual player values may change the practical preference. No equilibrium or real political model is claimed.

The moderator narrowed the proposed new epilogue visit to a hearing case bundle and existing ending/return stage. A new playable visit is deferred so the active browser acceptance route stays stable. The six-month text is still a text epilogue, not a simulated six-month city.

## Explicit new three-round cycle

This is a **new scholarship-led cycle**, separate from the earlier continuity review recorded in `PANEL_LEDGER.md`.

1. **Round 1 — study, challenge, moderate.** Selected readings above; source-derived findings S1–S3 and the depot tradeoff defect presented to the root moderator. Accepted changes bounded to the existing route. No claim of observed human preferences.
2. **Round 2 — implement and challenge the revision.** Content version **0.5.0**, comparison documents, all 21 receipts, nine callback variants, disclosure state and revised depot priorities implemented. `npm run test:content` passes **9 tests**, including all 2,187 valid choice sequences reaching all five endings. Stage IDs and count remain stable. Earlier 0.4.0 saves are intentionally incompatible with the semantic change; the current client compatibility flow governs restart.
3. **Round 3 — verify the changed build.** Independent semantic review accepted content and identified a destination-dialogue timing issue for the UI owner. Contract tests establish references, history resolution and outcome reachability. Final browser traversal and the later proximity correction are recorded separately in round 6 of the panel ledger; source correctness alone does not establish their presentation.

## What these readings do not establish

They do not establish player enjoyment, cultural authenticity, a measured campaign duration, full device compatibility or commercial readiness. Next human playtests should ask players to explain one decision’s cost, identify what the two records actually prove, and describe why their ending occurred. Record their answers and observed actions before expanding the mission count.
