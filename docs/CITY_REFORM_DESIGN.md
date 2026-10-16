# City Reform — the first shared case arc

## Scope and status

City Reform Beta 0.3 implements one opening media case, four sector cases and one persistent crew decision after the five-job City Jobs Beta 0.2 baseline. Content, simulation and UI are integrated. Local source gates (134 tests, typecheck/lint), focused browser cases and production/standalone/container checks passed. Release `c20e912` passed all thirteen CI browser cases (11.8 minutes), built and deployed successfully. Public HTML matches the standalone artifact, and the native live-site check passed. The earlier failed CI attempt and subsequent test-only synchronization change remain in the QA history. The original five repeatable jobs and optional six-chapter Story retain their definitions and saves. [Current QA](CITY_REFORM_QA.md) separates physical traversal, controlled fixtures and deployment evidence.

The user requested fictional media parody, driving tasks, subtasks/events and a later betrayal path that reaches a change of administration. The accepted scope uses the existing district, two vehicles, cargo handovers, job board and authoritative rooms. It does not add simulated national elections, a power grid, a resource market, combat, NPC traffic or an investigative document-analysis minigame. Those would need distinct mechanics and evidence.

Design judgments below are authored hypotheses, not conclusions from human playtesting. The opening media route now has actual two-client traversal evidence. The four sector routes and both post-case outcomes have source/simulation coverage; the final-choice browser checks start from explicitly prepared completed-case checkpoints and do not establish physical sector traversal.

## Fiction and cast

**Republic Times** and its host **Grnab Aoswami** are invented in-universe satirical media characters requested for this game. Their broadcasts parody sensational headlines and sponsor interruptions. Every contract, wrongdoing, company, relationship and outcome described here belongs to fictional Devnagar; the game does not present allegations about a real journalist, outlet or government.

| Character or organization | Desire and contradiction | Playable role |
| --- | --- | --- |
| Noor, The Lantern | Wants a report people will read; must resist a dramatic claim the records cannot support | Dispatches the opening case; publishes checked corrections and authored event receipts |
| Kavya, Night Clinic | Wants services delivered today and a reliable record tomorrow | Verifies the supply footage and acknowledges clinic handovers |
| Yusuf, garage owner | Wants working vehicles and paid work; knows a useful repair is less photogenic than a ribbon cutting | Loads the energy-service kit and keeps transport grounded in physical jobs |
| Meera, neighborhood organizer | Wants meals and river access; refuses to treat a headline as a completed service | Receives welfare deliveries and compares the authorized river records |
| Grnab Aoswami, Republic Times | Wants the final word and continued sponsorship; each checked receipt forces a smaller, stranger headline | Short original satirical interruptions, captions and corrections; no impersonated audio |
| Bright Meridian Services | Sells energy maintenance, event logistics and media sponsorship through disclosed fictional contracts | Common named contractor whose separate records create the four cases; shared branding alone is not evidence of misconduct |
| Samar, coalition sponsor | Wants to replace the administration; also wants discretion over his own supporters | Offers the final patronage deal after the crew has earned a complete case |

The arc is a separate City Jobs continuity using the same cast. It does not assume the player completed Story or overwrite Story's choices, evidence or ending.

## Player flow

1. The job board offers **The Nine O'Clock Correction** alongside the three existing starter jobs. A short description states the route and that completing it opens four sector cases.
2. The crew accepts one active job. The HUD shows one current action, destination, foot/vehicle requirement and cargo state. Existing driver, navigator and runner roles remain optional; one person can perform every action sequentially.
3. Each completed case stage reveals a short event receipt. Receipts separate what the fictional record establishes from the presenter's joke. A resumed or newly joined client can read the same earned receipts.
4. Completing the opening case unlocks four once-only cases, playable in any order. The board displays the exact prerequisite for a locked case and the completed status of a finished case.
5. Completing all four sectors opens **The City Mandate** at Public Hearing. With no job active, players approach on foot, review both persistent consequences and cast a crew vote. A majority of currently connected players settles the result; a split remains pending.
6. The saved outcome changes future repeat-job rewards and remains in the city journal. The five repeatable jobs continue. Rejoining, restarting the server or replaying an accepted command cannot reset the mandate or repay a completed case.

No forced timer applies to these cases. The existing District Circuit remains the timed option. Long reading does not share a timer with a drive.

## Exact geography and mechanical vocabulary

Use the existing `WORLD.landmarks` positions and radii. Content refers to IDs; it does not hard-code separate movement coordinates.

| ID | In-game location | x / z | Radius |
| --- | --- | --- | --- |
| garage | Yusuf's Garage | -60 / 48 | 8 |
| board | The Newsroom | -68 / 43 | 6 |
| clinic | Night Clinic | 52 / -48 | 9 |
| archive | City Records | 48 / -66 | 8 |
| mill | Mill Ward | -48 / -68 | 8 |
| radio | Open Frequency | 65 / 0 | 8 |
| square | Assembly Square | 0 / 66 | 8 |
| civic | Public Hearing | 0 / 82 | 8 |
| river | River Steps | 82 / 48 | 8 |

`load` means `action: interact`, driver of the indicated vehicle, stopped at at most 1.5 m/s, `grantCargo: true`. It binds the actual vehicle on the first load. `unload` means on-foot interaction beside that same stopped vehicle, `requiresCargo: true, consumeCargo: true`. A teammate may unload while the driver remains seated. An ordinary on-foot interaction has no cargo effect. Nothing here remotely spawns a completed delivery or treats a passenger as the driver.

## Five authored cases

All five have `once: true`, no time limit and a nominal zero completed cooldown because the durable completed-job ledger prevents repetition. Cancellation or failure retains the existing retry rule and gives no incomplete reward. The opening case has no prerequisite; each sector case has `requiresJobs: ['media-correction']` and adds exactly one point to its named sector on successful completion. Sector points measure this authored arc, separately from the district's repeatable project counter.

| ID / title | Ordered stages and required actions | Reward: credits / reputation / project |
| --- | --- | --- |
| `media-correction` / The Nine O'Clock Correction | `brief`: board, on foot, receive Noor's question → `archive-load`: archive, any vehicle, load authorized airtime and dispatch copies → `clinic-check`: clinic, unload for Kavya's comparison → `clinic-load`: clinic, same vehicle, load the checked correction packet → `broadcast`: radio, unload the packet for publication | 120 / 2 / 1 |
| `sector-energy` / Light, Camera, Invoice | `load-lamps`: garage, van, load service lamps and public maintenance copies → `clinic-service`: clinic, unload the lamps and obtain the service acknowledgment → `load-report`: clinic, same van, load that acknowledgment with the contract copy → `file-energy`: civic, unload the checked energy-service file | 180 / 3 / 2 |
| `sector-welfare` / The Missing Breakfast | `load-register`: archive, any vehicle, load the aggregate allocation record → `depot-check`: mill, unload for comparison with the release slip → `load-meals`: mill, same vehicle, load the authorized replacement meal crates → `square-handover`: square, unload to Meera and file the two counts | 160 / 3 / 2 |
| `sector-resources` / The River Has Receipts | `load-permit`: archive, any vehicle, load the public river-haul permit → `river-check`: river, unload for comparison with the steward's signed manifest → `load-river-file`: river, same vehicle, load the checked manifest bundle → `file-resources`: civic, unload the permit/manifest file | 170 / 3 / 1 |
| `sector-procurement` / Lowest Bid, Loudest Sponsor | `load-bids`: archive, any vehicle, load both public bid-round summaries → `sponsor-check`: radio, unload for comparison with the disclosed airtime contract → `load-dossier`: radio, same vehicle, load the checked procurement file → `file-procurement`: civic, unload the file and the response request | 190 / 3 / 1 |

Physical loads are a compact game representation of moving records or supplies. Pressing interact reveals an authored comparison; the player does not actually calculate an invoice discrepancy, test electricity or measure river extraction. The interface must not promise those mechanics.

## Stage events and satirical captions

Each `JobStage.event` is presentation content `{title, body}`, exposed with stable receipt ID `${job.id}:${stage.id}`. It has no executable condition or reward effect. The city journal derives completed receipts from all stages of jobs in `city.completedJobs` and earlier stages of the current active case. Cancellation must not imply the case completed or reveal its unearned final event. In-game events use short character dialogue and concrete findings; fiction and implementation qualifications belong in About and these design notes, not repeated in every delivery receipt.

The central facts and turning points are:

| Case | First question | Checked event | Completion changes |
| --- | --- | --- | --- |
| Media | Republic Times calls staged delivery footage proof that every clinic shelf is full | The fictional dispatch copy assigns the photographed crates to a media display; Kavya's signed note shows the clinic received fewer crates. The crew corrects that specific claim without treating all coverage as false. | Noor publishes the correction and links four distinct public files; sector cases unlock |
| Energy | Bright Meridian's invoice describes full installation while the clinic still needs portable lamps | The maintenance copy lists installed fixtures; the service acknowledgment records what the delivery actually supplied. A billing question is attached to the file. | One energy case completed; immediate lamps supplied and invoice discrepancy referred for review |
| Welfare | The broadcast's cheerful breakfast total omits an amended dispatch count | Aggregate allocation and depot release counts disagree; replacement crates are physically delivered. No private recipient records enter the journal. | One welfare case completed; service delivery and accounting question are recorded separately |
| Resources | A river renewal slogan substitutes for the permit's limits | A public permit and signed manifest name different authorized quantities. The game supplies these fictional records; it does not infer misconduct from a company name alone. | One resources case completed; the specific discrepancy and requested response enter the case |
| Procurement | The winning bid and the channel's sponsorship share a contractor | The second bid round changed a requirement after the first round closed; the disclosed sponsorship is a conflict to review, not proof that advertising itself is illegal. | One procurement case completed; the tender change and sponsorship dates are referred together, with the contractor's response request retained |

Samar's supporter annex is submitted as unpublished working material. The final mandate controls whether that annex joins the public case. The capture route therefore withholds an unpublished record; it does not erase something the player already published.

Examples of original in-world captions: **“BREAKING: tomorrow's breakfast arrives in today's headline.”** **“The lights are on. The invoice would like a standing ovation.”** **“Independent analysis, proudly interrupted by our sponsor.”** These are authored game jokes, not a fetched or current internet-trend feed. Short text cards and optional original sound cues carry them; the design does not require cloned voices, real broadcaster clips or third-party memes.

## Persistent mandate and betrayal

The final command is `city_choice`, target `city-mandate`, value `reform` or `capture`. Preconditions: City Jobs mode, opening case completed, each of four sector scores at least one, no active job, on foot within Public Hearing's radius, no prior settled decision. The server stores the final outcome. Pending ballots are pruned when their players disconnect and cleared on restart or new work; a disconnect cannot silently decide the route. An explicit eligible vote is required to settle it. The client may preview, but cannot award itself the mandate.

| Route | Player-facing decision | Authored outcome | Persistent mechanical effect |
| --- | --- | --- | --- |
| `reform` | **Publish the full case. Bind the next administration to the same rules.** | **Open Mandate.** The council releases the case, removes the administration through its recorded vote and appoints an interim coalition subject to published contracts. Noor publishes Samar's disclosures too. Meera asks the crew to keep delivering after the ceremony. | Future jobs whose base reward includes project points gain **+1 project**. Credits and reputation follow their base reward. |
| `capture` | **Take Samar's deal. Seal the sponsor annex and control the next administration.** | **A New Name on the Door.** The administration changes, but the crew gives Samar's backers a private channel. Grnab announces a fresh beginning under familiar sponsor credits. Noor refuses the sealed annex; the crew keeps the lucrative dispatches. | Future jobs gain **25% credits**, rounded down; their **project contribution is zero**. Reputation is unchanged. |

Existing earned counters remain unchanged. Credits currently have no spending system, so the capture advantage is a higher shared score, not purchasing power or a proven balanced economic temptation. The reform bonus changes future district-project progression; capture stops further contribution from jobs but does not erase already earned visual tiers.

`getEffectiveJobReward(base, route)` must be a pure exported helper used by both the authoritative completion path and displayed job rewards. The UI shows the route's actual effect before voting and on later job cards. Do not display base rewards when the server would award modified rewards. `CITY_OUTCOMES` supplies the authored result; `CITY_EXPOSE_JOB_ID` supplies the stable opening prerequisite. The scripted council result is the first district-scale political ending, not a simulated national regime change. Further institutions, opposition responses and national sectors remain later production work.

## Persistence and acceptance

Systems owns a durable `city` state with `completedJobs`, four sector totals, current votes, settled decision, authored outcome and revision. Old schema-one/two saves migrate to an empty city ledger while retaining existing active jobs, cargo, counters and identities. A bounded recent-job receipt list is not evidence that a once-only sector case was completed. Story cannot acquire city progress through an incidental join or malformed command.

| Gate | Concrete acceptance | Evidence status |
| --- | --- | --- |
| Content and prerequisites | Exactly five new once-only cases; existing five definitions unchanged; all stage IDs/targets valid; two loads consumed per case; only the opening case is initially available | Passed isolated content checks: ten total jobs, five new cases, 41 stages, 15 loads, four sector prerequisites, 21 event receipts and six media cards; isolated TypeScript and ESLint pass |
| Subtask authority | Remote, wrong-vehicle, moving-vehicle and passenger actions cannot complete a case; valid driver/runner handoff advances exactly one stage | Passed local source tests and actual media-case driver/runner handoffs; source-position fixtures labelled |
| Events and late join | Earned receipts derive from canonical progress; future stages/final receipts remain hidden; late join shares the same ledger | Actual media browser route shows five earned receipts and hides the mandate; real-WebSocket fixture tests share canonical completed ledger/outcome with late join |
| Durable arc | Opening completion unlocks four cases; each pays and increments its sector once; replay/restart cannot farm rewards or erase completion | Passed simulation/network tests, including bounded-history rollover; physical media completion and duplicate replay award 120/2/1 only once |
| Final vote | Remote/vehicle/early votes rejected; connected majority at civic settles one route; ties do not settle; reconnect retains result | Passed local simulation/real-WebSocket tests with completed-case fixtures; both UI outcomes/reloads pass labelled solo fixtures |
| Real consequences | Displayed and paid rewards share the helper; modifiers persist after checkpoint restore; prior counters and Story remain intact | Helper edge checks and route-specific restored payouts pass; UI disclosures/outcomes pass labelled fixtures; full integrated Actions gate passed |
| Physical route | Actual browsers complete the opening case through ordinary controls, see event receipts and unlocked sector cards | Passed two real clients/all five stages in 71.950 s; four sector routes were not physically traversed in this check |
| Production persistence | Real older room/identity migrates with backup; new case state survives graceful production restart | Passed actual 0.2 volume copy → schema 3 under non-root 0.3 container, two WebSocket clients and first media briefing; restarted at archive-load |
| Release claims | Published client revision, hosted backend status, source/test results and remaining limits match evidence | Release c20e912/run 38857615158 passes source checks, thirteen browser cases, builds/deployment, exact public-file comparison and native live-site smoke; public backend unprovisioned |

Evidence: [physical route](evidence/city-reform-media-route.json), [labelled mandate fixtures](evidence/city-reform-mandate-fixtures.json), [container migration/restart](evidence/city-reform-container-check.json) and [central QA record](CITY_REFORM_QA.md). The earlier 0.2 ten-case baseline remains separate historical evidence.

The next meaningful human observations are whether the opening task is understood without narration, whether driver/runner handovers feel useful, whether the satire lands without obscuring the objective, and whether the mandate feels like a consequential choice. Automated pass results cannot answer those questions.
