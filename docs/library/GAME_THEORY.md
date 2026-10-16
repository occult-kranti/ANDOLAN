# A small game-theory model for fictional crew choices

Source basis: Sinander's primary author-hosted notes, `ch_dom.tex` “Best replies”, “Dominance” and the coordination example; exact revision/links in [SOURCE_REGISTER.md](SOURCE_REGISTER.md). Schreiber Level 7 connects this diagnostic to interesting game choices. The payoff model below is **our original design instrument**, not an empirical model of government change, real protests or player political identity.

## Model the actual decision

A depot choice has a consequence vector:

`v(choice, history) = [trust change, care change, accountability change, information gained, relationship flags]`.

The first three coordinates are currently bounded game metrics; the last two may be discrete, qualitative state. A player can reasonably prioritize them differently. A numerical projection `U = wT·trust + wC·care + wA·accountability` is useful for a diagnostic, with nonnegative weights summing to one. It leaves out role-playing, interpretation, uncertainty, future dialogue and world effects. We must not pretend it captures every player's utility.

For the initial depot implementation, the metric vectors were:

| Choice ID | Trust | Care | Accountability |
| --- | ---: | ---: | ---: |
| `supplies` | +5 | +15 | 0 |
| `interview` | 0 | +4 | +10 |
| `photo` | −10 | −12 | −4 |

Within this restricted model, both alternatives improve every coordinate over `photo`. Every strictly positive weighting therefore ranks `photo` below them. That is a componentwise comparison of authored consequence vectors, **not a proof of strict strategic dominance over a fully specified multiplayer game**. Sinander's theorem assumes the complete finite game/payoff model; ANDOLAN has authored history and different human interpretations.

It is acceptable to include a deliberately bad decision for characterization. Here, however, the label and scores made the third choice a moral quiz while the scene promised competing priorities. The panel selected three defensible actions instead. The revised vectors and an executed diagnostic are in [decision-diagnostic.json](decision-diagnostic.json) and [the panel record](RESEARCH_PANEL.md); do not treat the baseline table as current balancing.

## Test preferences rather than one universal optimum

Use several diagnostic profiles, for example care-focused `[0.15, 0.70, 0.15]`, reporting-focused `[0.20, 0.15, 0.65]`, and relationship-focused `[0.65, 0.20, 0.15]`. These weights are test inputs, not inferred user categories and not stored on player profiles.

For each focal alternative:

1. Record its real cost and benefit before the player commits.
2. Confirm the cost/benefit appears in authoritative state or later content.
3. Compare all three coordinates and list any componentwise inferior option.
4. Check whether different profiles prefer different alternatives.
5. Inspect the nonnumeric flags and later dialogue before removing an apparent loser.

No target percentage of real players is assumed. A human playtest should ask why they chose an option, not infer that reason from a score.

## Crew voting is a coordination problem

Sinander's coordination example has two matching outcomes that both beat mismatch, with different players preferring different matches. It demonstrates why individually sensible choices do not guarantee agreement. It does not derive ANDOLAN's voting rule.

Our private room uses strict majority. With two connected participants, a 1–1 split does not meet a majority. Showing a selected ballot, each option's count and the current quorum makes that unresolved state legible. A player can change a ballot; the server recomputes using connected members. If someone disconnects, the room must re-evaluate pending votes under its documented membership policy. A remaining valid majority may then resolve once.

No hidden host override or automatic “correct” story choice is required. Disagreement is allowed. A time-out/tie-break policy, if added later, must be communicated before voting and tested; it is not implied by the present model.

## History, commitment and continuation

Sinander's sequential-game introduction distinguishes histories and continuation strategies. ANDOLAN borrows the bookkeeping discipline, not an equilibrium solution: accepted choices receive stable IDs, remain in saved history, and determine later authored responses. A submitted ballot is not yet a committed choice. The journal and subsequent dialogue must read the same accepted record.

Required checks:

- Pending vote changes do not alter metrics, history or evidence.
- Resolution creates exactly one accepted record.
- Replayed commands do not apply effects twice.
- A save/restore preserves the selected consequence and its later acknowledgment.
- A disconnected voter is excluded consistently from count and quorum.
- Client labels match server semantics: “vote recorded” versus “crew decided.”

Repeated-game cooperation is relevant to later crew contracts, but no trust-mechanism equilibrium has been solved or benchmarked here. Public reputation systems, player profiling and real-world political prediction are outside this model.
