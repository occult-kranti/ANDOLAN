# Source register and reading scope

Session date: 15 October 2026, America/New_York. Pinned file SHA-256 values and byte counts are in [source-manifest.json](source-manifest.json). A citation means the listed section was inspected; it does not mean a complete book, course or proof was reviewed.

## Actually read

### S1 — Ian Schreiber, Game Design Concepts (2009)

Canonical course: <https://gamedesignconcepts.wordpress.com/>.

Read source: [archival mirror at `5c98165…`](https://github.com/eugenioclrc/gamedesignconcepts/tree/5c98165cb261143bda0147463acbaee922ca46c9). The mirror README attributes the original author and describes Creative Commons publication. Every inspected lesson links its canonical post. The canonical HTTPS request returned proxy 403, so fidelity to the live original and its exact current license version are **not independently verified**. These are original-author lesson texts as represented by a mirror, not a claim that the mirror is maintained by Schreiber. No full course is copied into ANDOLAN.

| Section actually read | Exact mirror file | Used for |
| --- | --- | --- |
| Level 2: “Speaking of Science…”, “Iteration and Risk”, “Why This Course is Non-Digital…” | [02-game-design-iteration-and-rapid-prototyping.md](https://github.com/eugenioclrc/gamedesignconcepts/blob/5c98165cb261143bda0147463acbaee922ca46c9/lessons/02-game-design-iteration-and-rapid-prototyping.md) | Hypothesis → prototype → test; three genuine rounds |
| Level 5: “Now, About That MDA Framework Thing…”, “The Process of Design”, “The Process of Play”, spawn-camping example | [05-mechanics-and-dynamics.md](https://github.com/eugenioclrc/gamedesignconcepts/blob/5c98165cb261143bda0147463acbaee922ca46c9/lessons/05-mechanics-and-dynamics.md) | MDA **secondary exposition**, distinguish desired feeling from tested behavior |
| Level 7: “Decisions”, “Things Not To Do”, “What Makes Good Decisions?”, flow discussion | [07-decision-making-and-flow-theory.md](https://github.com/eugenioclrc/gamedesignconcepts/blob/5c98165cb261143bda0147463acbaee922ca46c9/lessons/07-decision-making-and-flow-theory.md) | Avoid obvious/blind/meaningless choices; expose trade-offs |
| Level 10: “Linear”, “Branching”, “Parallel Paths”, “Threaded” | [10-nonlinear-storytelling.md](https://github.com/eugenioclrc/gamedesignconcepts/blob/5c98165cb261143bda0147463acbaee922ca46c9/lessons/10-nonlinear-storytelling.md) | Manage branch cost while showing causal consequences |
| Level 15: “The Challenges with Blindtesting”, “Why Blindtesting?”, “When to Blindtest?”, “How to Blindtest?” | [15-blindtesting.md](https://github.com/eugenioclrc/gamedesignconcepts/blob/5c98165cb261143bda0147463acbaee922ca46c9/lessons/15-blindtesting.md) | Distinguish automation and novice unaided play |
| Level 17: “What is a User Interface?”, “User Interface Design”, “The Two Models of Usability”, “Identifying the User Model” | [17-user-interfaces.md](https://github.com/eugenioclrc/gamedesignconcepts/blob/5c98165cb261143bda0147463acbaee922ca46c9/lessons/17-user-interfaces.md) | Vote state, decision acknowledgment and novice/experienced affordances |

### S2 — Ludvig Sinander, Game theory lecture notes (2026 source)

Primary author-hosted source: [repository at `eb0eabb…`](https://github.com/ludvigsinander/Sinander_game_theory_notes/tree/eb0eabb9f53588c5651c5d5e17f0e360156c069d). The repository describes advanced first-year graduate teaching at Oxford. Selected TeX sections were read directly; the entire advanced course was not studied. COPYING is GPLv3-or-later for source. We import neither TeX source nor code into the product.

- [`ch_dom.tex`, lines 17–64](https://github.com/ludvigsinander/Sinander_game_theory_notes/blob/eb0eabb9f53588c5651c5d5e17f0e360156c069d/ch_dom.tex#L17): finite normal-form game, beliefs, expected payoffs and best replies.
- [`ch_dom.tex`, “Dominance”, lines 146–226](https://github.com/ludvigsinander/Sinander_game_theory_notes/blob/eb0eabb9f53588c5651c5d5e17f0e360156c069d/ch_dom.tex#L146): strict dominance and its relation to never-best actions. We read the definitions/examples and theorem statement, not every proof.
- [`ch_dom.tex`, coordination example, lines 438–455](https://github.com/ludvigsinander/Sinander_game_theory_notes/blob/eb0eabb9f53588c5651c5d5e17f0e360156c069d/ch_dom.tex#L438): both coordinated outcomes beat mismatch while preferences can differ.
- [`ch_osdp.tex`, introduction and concepts, lines 17–74](https://github.com/ludvigsinander/Sinander_game_theory_notes/blob/eb0eabb9f53588c5651c5d5e17f0e360156c069d/ch_osdp.tex#L17): history-dependent strategies, continuation and terminal payoffs; one-shot deviation assumptions. Used to define the boundary of the analogy, not to claim a solved equilibrium for ANDOLAN.

### S3 — Reference implementations

[REFERENCE_MECHANICS.md](../research/REFERENCE_MECHANICS.md) lists the exact pinned implementation sections read. DX-Ball oracle counts remain upstream reports, even though the documents themselves were fetched. OpenRW/OpenLara code was inspected as text; their games were not run. The previous REA Sketchbook static run remains the only REA execution performed here.

## Requested but not read directly

| Source | Canonical reference | Observed access / status |
| --- | --- | --- |
| Robin Hunicke, Marc LeBlanc, Robert Zubek, “MDA: A Formal Approach to Game Design and Game Research” (2004) | <https://users.cs.northwestern.edu/~hunicke/MDA.pdf> | HTTPS proxy 403. Original paper not read this pass; Level 5's account is explicitly secondary. |
| Ian Schreiber, Game Balance Concepts (2010) | <https://gamebalanceconcepts.wordpress.com/> | Canonical lesson request returned HTTPS proxy 403. Bibliography/queued; no lesson summaries claimed as direct reading. |
| Ben Polak, Yale ECON 159 Game Theory, Lecture 1 | <https://oyc.yale.edu/economics/econ-159/lecture-1> | HTTPS proxy 403. Replaced for current notes by accessible author-hosted Sinander material; no Yale lecture viewed. |
| Twelve design/story/theory books | [Publisher bibliography](BOOKS.md) | Curated references only. No whole-book downloads or full-reading claim. Publisher pages not accessed in this pass. |

Network policy was respected. No proxy/TLS bypass was used. Public GitHub source repositories were retrieved through the configured HTTPS path. The notes distinguish a permitted public mirror from an independently authenticated canonical original.
