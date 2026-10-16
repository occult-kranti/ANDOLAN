# Design/game-theory panel: three-round record

This is the independent research perspective within the multi-agent panel. It is not a human design jury or human playtest. The moderator's overall panel ledger remains in `docs/PANEL_LEDGER.md`.

## Round 1 — identify three changes

**Artifact:** content 0.4.0 and the existing client/server source. **Evidence:** the exact selected readings in [SOURCE_REGISTER.md](SOURCE_REGISTER.md), plus the current authored choices and voting behavior.

| Finding | Decision accepted by moderator | Owner / check |
| --- | --- | --- |
| Depot `photo` lost every metric compared with both other options; the scene promised priorities but supplied an obvious moral answer. | Replace it with authorized stock documentation and make every depot alternative trade a benefit for a cost. | Story; content choice and ending tests |
| Outcomes mainly appeared through distant ending/score changes, weakening visible causality on converged routes. | Add immediate consequence receipts, retain them in the journal, and add later history-specific dialogue. | Story + systems + client; saved-history and rendering checks |
| Two private players could split votes without reaching majority; closing the modal and omitting the tally made the unresolved state obscure. | Show votes/quorum, selected ballot and change-vote affordance; re-evaluate active membership after disconnect. | Client + systems; split vote / changed vote / disconnect tests |

## Round 2 — inspect the changed implementation

**Artifact:** content 0.5.0; client `showDialogue`, `updateVoteFeedback`, `updateHUD`, `showJournal`; simulation `resolveVote`, `disconnectPlayer`, stage advance and restore. **Verdict:** accepted within this source-review scope, no new blocker.

Observed concrete applications:

- The three depot options now trade immediate service, witness relationship and stock documentation. The descriptions expose the costs before selection; each has a different evidence record and matching clinic response.
- All accepted choices have authored consequence receipts. The client displays the latest accepted receipt and keeps the receipts in the journal. Pending ballots do not themselves create a history entry.
- Later dialogue is selected by exact accepted history IDs, with a base fallback. The simulation reconstructs presentation from history on restore.
- Vote feedback refreshes from snapshots, marks the player's choice with `aria-pressed`, displays the current majority and tells the crew that ties wait for agreement. A changed ballot replaces the old one.
- Disconnect deletes that ballot and recalculates using connected players. Deliberate shutdown can disable resolution, preventing a pending ballot from becoming canon merely because the server is draining.

The new trade-off is still an authored outcome. There is no claim that stock counting is an implemented minigame or that dispatch delay uses a physical/time simulation. A later chapter may provide those verbs; the current descriptions and receipts must remain honest about the present interaction.

### Executed payoff diagnostic

The content module was imported through the installed `tsx` runtime. The check read the actual depot effects, receipts and clinic variants. It found no componentwise inferior alternative; three explicitly supplied weighting profiles each preferred a different action. Saved output, exact source SHA-256 and all scores: [decision-diagnostic.json](decision-diagnostic.json).

| Original diagnostic profile (trust, care, accountability) | Highest score | Choice |
| --- | ---: | --- |
| Care `(0.15, 0.70, 0.15)` | 9.50 | Put the reserve van first |
| Reporting `(0.20, 0.15, 0.65)` | 8.95 | Document the stock with the clerk |
| Relationship `(0.65, 0.20, 0.15)` | 7.90 | Hear the clerk's full account |

This establishes a narrow arithmetic design property. The weights are test inputs, not measured preferences, moral rankings or a proof of gameplay enjoyment.

## Round 3 — verify the changed behavior

Pending the moderator's final frozen-build test evidence. This section will record actual content/simulation/browser results and remaining limits; the source review and arithmetic diagnostic above do not establish novice comprehension, network presentation or human comfort.
