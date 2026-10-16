# Original reference lab — QA record

Status: 16 October 2026, **local unit and initial built-client checks pass; full native acceptance, CI and public lab delivery remain pending.** This is a new lab workstream, separate from the published coastal YUGA release. It implements original lane-economy and hybrid control-point experiments; none of these checks establishes Deadlock or Overwatch parity.

## Evidence boundary

The [initial archive](evidence/reference-lab-initial-check.json) records supplied results, their SHA-256 values, exact test names and source hashes taken when archived. Repository HEAD was `994a3b32b1bd35e1860f37bcc210b491e3afcb0a`, with modified and untracked implementation files. This is **working-tree evidence**, not a claim that the code was committed cleanly or hash-frozen throughout each run. No tests or browsers were rerun for this documentation pass.

| Check | Observed result and scope |
| --- | --- |
| Lab unit suite | **21/21 pass**: eight controller cases, seven deterministic objective cases, six primary-receipt cases, across three test files. The supplied Vitest JSON reports six internal suites; that is not six files. Raw input `/tmp/yuga-reference-unit-final.json` is hashed in the archive. |
| Controller | Actual public API checks cover command/epoch validation, bounded stepping, menu pause, permitted paused base purchases, primary ammo/reload, ability exclusion, deduplication/reset, a normal bot-match wallet reconciliation and frozen result, plus preservation of the lane arena outcome. |
| Objective | Labelled actor-placement fixtures cover eligibility/radius, six-second capture, no headcount bonus, contest freeze, empty-owner/no-score, partial decay, returning-owner clearance, bounded elapsed time, 60-point finish and snapshot isolation. Eligibility is height **y ≤ 2 m**, not a grounded-only check; the raw test title using “grounded” is imprecise and is not adopted as a rule here. |
| Exact primary receipts | Labelled capacity/history fixtures verify one immutable receipt for a genuinely created hero primary, none for rejected capacity/ability/minion fire, unchanged seeded arena state with an observer, and correct ammo when the bounded visual-event history loses the shot event. The observer is trusted local adapter code, not an isolated plugin sandbox. |
| Existing regression/static checks | Coordinator reports **350 existing tests**, root typecheck and lint passing. These results are recorded as coordinator-supplied, not independently rerun here. |
| Builds | Coordinator reports main YUGA and all three lab variants built successfully. Build success alone is not functional acceptance. |
| Initial production smoke | [Archived actual result](evidence/reference-lab-built-initial.json): combined entry, **lane-economy** preset, Rama, seed 7301, low quality, 960×640, loopback HTTP serving built files. Native launch → clock advance → pause → resume → return passed after two actual engine postrenders. No development hook, state injection or frame throttle supplied the result. |
| Models and errors | That smoke fetched **13 distinct GLBs**: six participating heroes and all seven units. All **21 built model hashes** were checked against their manifests separately. Page errors, console errors, failed requests and HTTP errors were empty. The response HTML hash matched the local built file. |
| Screenshots | Four actual screenshots were produced; their original paths, sizes and hashes are archived. The coordinator reports viewing two. This documentation pass did not independently assess their appearance. |

The initial smoke did not complete a control objective, full match or replay and did not test mobile, multiplayer, public hosting or consumer performance. Its thirteen fetched models must not be described as twenty-one models rendered in that run.

## Remaining gates

| Gate | Current state / required evidence |
| --- | --- |
| Desktop native flow | **Pending**: ordinary controls, aim/fire, abilities/reload, paused forge, input neutrality and reset/back; label any diagnostic fixtures. |
| Mobile native flow | **Pending**: touch movement/aim/actions, readable objective and menu separation on the declared viewport. |
| Full normal control match | **Pending**: normal clock and bots through a real result/restart, with objective/engine precedence and no hidden accelerated-clock claim. |
| New CI | **Pending**: exact committed revision, existing regression gates plus lab suites and builds. |
| Publication | **Pending**: actual combined/lane/control routes, response/artifact hashes and production browser smoke after deployment. Coastal-release evidence cannot close this gate. |

The first lab's economy ledger records **observed net wallet changes per action or simulation step**. Its reconciliation test does not identify individual reward sources or close a source-correlated exactly-once earnings gate. That stronger ledger remains later scope in the [reference roadmap](REFERENCE_GAME_ROADMAP.md). The original lab is offline with labelled bots; human balance, WAN performance and an operated public multiplayer service remain untested.
