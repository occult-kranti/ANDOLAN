# Eight design notes that change the game

These are original, short working notes based on the exact inspected sections in [SOURCE_REGISTER.md](SOURCE_REGISTER.md). “Lesson” is a paraphrase; “application” and acceptance thresholds are our design decisions. They do not imply empirical research on ANDOLAN players.

## N1 — Choose a felt experience, then test the rules that might cause it

**Source:** Schreiber Level 5, “The Process of Design” and “The Process of Play” (S1; mirror read). It explains Hunicke/LeBlanc/Zubek's MDA framework; the original paper was unavailable this pass.

**Lesson:** A rule is directly authored; how players respond to it and how that feels need observation. A screen with a city and a large feature list does not establish curiosity, agency or fellowship.

**ANDOLAN application:** Desired experience: “I had a defensible priority, my crew understood it, and the city remembered.” Concrete rules: three legible depot priorities, a shared ballot, saved choice state and a later acknowledgment. Inspect those links before adding districts.

**Acceptance:** For every depot alternative, enumerate one changed persisted fact and one visible later response. Technical tests verify those facts. A later novice playtest asks the player what changed and why; that comprehension result remains unmeasured until a person actually plays.

## N2 — Trade-offs replace the answer that is obviously marked wrong

**Source:** Schreiber Level 7, “Things Not To Do” and “What Makes Good Decisions?” (S1; mirror read).

**Lesson:** Decisions can be weak because they do nothing, have an obvious answer or offer too little information. Scarce time, competing actions and different time horizons can make alternatives worth weighing.

**Observed baseline:** Depot `photo` penalized trust, care and accountability while supplying no compensating game benefit. `supplies` and `interview` both outperformed it on the scoring dimensions implemented in content. This is a design comparison, not a claim about every player's preferences.

**ANDOLAN application:** Replace the staged-photo choice with a defensible alternative such as documenting the public shortage while protecting private people. Keep delivery, witness time and accountable public documentation in tension. State the cost before commitment; do not reward fabricating evidence to manufacture a trade-off.

**Acceptance:** Each of three choices has a clear distinct priority and a supported downstream response. A content check ensures no focal option is componentwise worse on every implemented consequence dimension unless explicitly designed as a role-playing failure choice. All endings remain reachable.

## N3 — A converged route still needs visible memory

**Source:** Schreiber Level 10, “Branching” and “Parallel Paths” (S1; mirror read).

**Lesson:** Fully branching stories grow expensive; reconverging paths can preserve scope but weaken agency when choices only surface in a distant ending.

**ANDOLAN application:** Keep the same clinic return and river interview to preserve a finishable campaign. After the depot ballot, show an immediate specific acknowledgment, save it in the journal, and use the saved selection in a later clinic line. Common destinations may remain; spoken facts must match the chosen route.

**Acceptance:** Each branch is exercised through the later scene. The journal and dialogue agree with authoritative history after restart/reconnect. No line says the player personally delivered supplies when their chosen action was documenting the dispatch.

## N4 — A vote is a coordination interface, not a disappearing button

**Sources:** Schreiber Level 17, “What is a User Interface?” / “The Two Models of Usability” (S1; mirror read); Sinander `ch_dom.tex` coordination example (S2; primary verified).

**Lesson:** Input and feedback together form the interface. Players can prefer different coordinated outcomes; agreement is not guaranteed merely because every alternative is reasonable.

**Observed baseline:** The private server required strict majority, so two players needed agreement. The client closed the choice modal after one ballot and showed no tally/quorum, obscuring whether anything happened.

**ANDOLAN application:** Keep the current ballot visible, show each option's count and the required majority, distinguish “your vote is saved” from “the crew decided,” and permit a changed ballot. On disconnect, remove the departing ballot and re-evaluate the denominator. Do not silently invent unanimous agreement.

**Acceptance:** Two clients split 1–1: no story advance, visible disagreement. One changes vote: exactly one advance. A disconnected player does not keep a stale ballot or prevent an otherwise valid remaining majority. Repeated commands do not repeat the choice consequences.

## N5 — Payoff models are a diagnostic, not the story's moral truth

**Source:** Sinander `ch_dom.tex`, “Best replies” and “Dominance” (S2; primary verified).

**Lesson:** Dominance results rely on defined players, actions, beliefs and payoffs. They do not determine what people should value. A never-best action under one specified payoff model may be appealing under a different objective.

**ANDOLAN application:** Model care/trust/accountability changes as a vector, plus information acquired and relationship flags. Compare alternatives under several positive weighting profiles to expose redundant options. Preserve nonnumeric consequences rather than collapse the entire campaign into a “correct politics” score.

**Acceptance:** Publish the actual vectors alongside test output, not in a coercive public profile. Verify at least two focal alternatives can be preferred under plausible different weights. Identify hidden costs explicitly. The model is for authored fictional choices; it predicts neither real institutions nor actual player identities.

## N6 — Saved history is the causal record

**Sources:** Sinander `ch_osdp.tex`, introduction and “Some concepts and notation” (S2; primary verified); Schreiber Level 10 (S1; mirror read).

**Lesson:** In sequential models, an action can be evaluated through its continuation, and the terminal history matters. The analogy is useful only when the game's state actually remembers the relevant choice.

**ANDOLAN application:** Later dialogue reads stable accepted choice IDs from server history. An immediate UI acknowledgment is derived from the same record. A client toast, transient vote or numerical score alone is insufficient to establish which action occurred.

**Acceptance:** Save after the depot choice, restore and reach the clinic: the branch-specific line remains the same. Changing a pending ballot changes no history until accepted. Retransmitting an accepted command adds no duplicate event.

## N7 — Make each review round change and falsify something

**Source:** Schreiber Level 2, “Speaking of Science…”, “Iteration and Risk” (S1; mirror read).

**Lesson:** A prototype tests a hypothesis, and iteration returns from observed results to revised rules. Documentation and repeated approval cannot substitute for trying the changed design.

**ANDOLAN application:** Round 1 chooses the three bounded changes above. Round 2 inspects the changed content, server and client for contradictions; accepted findings become patches. Round 3 runs the regression checks and records both results and limits. The research lane stops expanding its bibliography when the implementation questions are sufficiently answered.

**Acceptance:** Review ledger names the artifact/version, finding, patch, validation and unresolved issue for each round. No “three rounds complete” until changed code has been reviewed and exercised.

## N8 — Automated completion is not an unaided player completing the game

**Source:** Schreiber Level 15, “Why Blindtesting?”, “When to Blindtest?”, “How to Blindtest?” (S1; mirror read).

**Lesson:** A designer can unintentionally teach missing rules or rescue a confusing experience. Testing without that help reveals different failures; it requires a complete, understandable handoff.

**ANDOLAN application:** Prepare a short first-player protocol: launch, find the garage, enter/exit, reach clinic, make a choice and explain its consequence without developer instructions. Record where they pause, their mistaken expectation and whether the journal helps. Keep browser automation for regression and human play for comprehension/comfort.

**Acceptance:** Technical release report labels scripted traversal as scripted. Human-test fields remain pending until performed. Suggested first study: three unfamiliar volunteer players; report each session rather than claiming statistical generality.
