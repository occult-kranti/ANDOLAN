# ANDOLAN design library

A small working library for making the game better. These notes identify what was actually read, connect it to a specific implementation decision, and define a test. This is not a claim to have read every listed book or produced human playtest evidence.

## Start here

1. [Design notes](DESIGN_NOTES.md): eight lessons, concrete changes and acceptance gates.
2. [Game-theory model](GAME_THEORY.md): choice payoff vectors, coordination and limits.
3. [Story design](STORY_DESIGN.md): narrative panel's source-grounded study and revisions.
4. [Reference mechanics](../research/REFERENCE_MECHANICS.md): actual inspected implementations and what is useful for this game.
5. [Books](BOOKS.md): twelve curated books with publisher references and a bounded reading plan.
6. [Source register](SOURCE_REGISTER.md): access status, exact sections and uncertainty.
7. [Research panel record](RESEARCH_PANEL.md): changed artifacts, three-round status and payoff diagnostic.

## Reading levels

| Level | What it means | Current material |
| --- | --- | --- |
| Primary verified | The author's text or implementation was actually retrieved from an author/project repository and the listed sections read. This verifies inspection, not every assertion in the source. | Ludvig Sinander's game-theory notes; OpenRW/OpenLara source; DX-Ball reconstruction ledger/oracle definitions. Story notes maintain their own inspected primary sources. |
| Mirror read | The archived lesson text was read at a pinned mirror; the canonical site could not be compared in this environment. | Ian Schreiber, *Game Design Concepts*, selected sections of Levels 2, 5, 7, 10, 15 and 17. |
| Bibliography / queued | A relevant work is identified, but the full work has not been read in this session. | The twelve books; original MDA paper; *Game Balance Concepts*. |

The full book/course texts are not redistributed here. Notes are original paraphrases. Source files used during research remain outside the game checkout in `/workspace/research`; compact provenance is in [source-manifest.json](source-manifest.json).

## This panel's three bounded changes

- Give the depot decision three defensible priorities and make at least two alternatives preferable under different player priorities.
- Show the accepted consequence immediately, retain it in the journal, and acknowledge it later in a conditional scene.
- Make crew coordination legible: show votes and the required majority, allow changing a ballot, and re-evaluate when a player leaves.

Round 1 establishes these decisions. Round 2 must inspect changed source and address contradictions. Round 3 must exercise the changed behavior and record results. Repeating an opinion about an unchanged build does not count as a new round. Human comprehension and enjoyment still require novice playtests.
