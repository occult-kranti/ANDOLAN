# Playable preview QA

This report covers the condensed six-chapter browser preview. It does not certify the full proposed open-world game. Browser checks use Linux Chromium and SwiftShader software rendering; the 390 × 844 check is browser emulation, not a physical touchscreen device.

## Reproduction

```sh
npm run typecheck
npm run lint
npm test
ANDOLAN_SOFTWARE_RENDERING=1 npm run test:e2e
```

`playwright.config.ts` starts the documented client/server development workflow when needed. Tests run sequentially. Desktop uses 960 × 640, final independent crew checks use a fixed 400 × 500 viewport to reduce software GPU contention, and mobile emulation uses 390 × 844. Set `PLAYWRIGHT_CHROMIUM_EXECUTABLE` to select an installed Chromium binary; otherwise the configuration uses `/usr/bin/chromium` when available, then Playwright's installed browser.

The revised CI harness gives software rendering a maximum 10-fps budget by delivering queued animation-frame callbacks with a 100-ms cooldown after each dispatch. `ANDOLAN_SOFTWARE_RENDERING=1` enables the same setup locally. It preserves native frame timestamps and cancellation; it does not change input/network timers, simulation steps, collisions, checkpoint state or assertions. The earlier local observations below used the uncapped scheduler. Capped checks establish functional behavior, not consumer-hardware smoothness. The shipped game does not contain this test scheduler.

The campaign controller plans routes through public collision geometry and sends ordinary bounded movement intent. It does not teleport, advance mission stages, inject checkpoints, alter the clock, or mutate gameplay state. Story decisions and conversations use visible buttons. A separate smoke test exercises actual keyboard controls. The high sequence number used by the campaign controller prevents the browser's keyboard poll from replacing its input; the original simulation still processes movement and collisions.

Two explicitly labelled follow-up tests use completed-state setup. The completed-room test mocks its welcome message to isolate dialog priority. The replay test normally uses a synthetic serialized checkpoint; optional `ANDOLAN_EARNED_CAMPAIGN` reuses the recorded physical campaign's mission and player while keeping default unoccupied vehicles and a fresh command ledger. Neither fixture is counted as campaign traversal or real multiplayer evidence.

## Final integrated local results

Application commit `7cf1f27896c580f5f87d289227b817a8563275b8` passes all **51 tests in five files**, TypeScript, ESLint and client/server/standalone production builds. The complete local browser suite passes **seven of seven cases in 359.094 seconds**, with zero skipped, unexpected or flaky results, using the documented software graphics budget. This supersedes the earlier split local results as the final integrated functional gate.

The campaign case took 263.214 seconds and completed all 22 stages, seven choices, hearing evidence and the visible **Open Windows** ending, then accepted the native replay confirmation and verified reset to `keys` with empty history. Its checkpoint is the original earned save, not a reconstruction. Real crew movement/seats/handover and physical walking/split votes/consensus/late-join recap passed. Mobile remains browser emulation; the completed-room and checkpoint-only replay cases retain their explicit fixture labels.

Stable evidence: `evidence/release-browser-results.json`, `release-campaign-evidence.json`, `release-completed-checkpoint.json` and `release-campaign-ending.png`. Timing review and baseline-failing regression proof are in `evidence/solo-timing-review.md`. The rebuilt standalone also passed an uncapped offline driving/save check with zero external requests or page errors (`production-browser-final-check.json`); the final non-root container retained real WebSocket identity and story state across restart (`container-final-check.json`).

## Earlier uncapped local results

| Check | Result | Observed behavior |
| --- | --- | --- |
| TypeScript and ESLint | Passed | Latest owned test changes compile and lint. |
| Desktop controls, checkpoint and settings | Passed, 35.5 s | E dialogue, F entry/exit, W driving beyond 5 m, reverse beyond 2 m, arrow-key walking, journal, modal input blocking, and reload retaining mission, position and preferences. |
| Reverse camera with Comfort | Passed | Reverse moved opposite the vehicle's heading. Camera angular separation from vehicle heading did not increase; it did not turn to follow backwards velocity. |
| Mobile browser layout | Passed, 6.5 s | Title, garage interaction and dialogue controls were in the viewport, with no horizontal overflow or uncaught JavaScript errors. |
| Six-chapter physical traversal | Passed through ending | All 22 stage IDs were visited using ordinary movement, seven choices were recorded, hearing evidence was acquired, and the visible ending was **Open Windows**. |
| Evidence documents | Passed in campaign | Comparison and hearing dialogs rendered the expected document count and source attribution. |
| Location-dependent dialogue | Passed in campaign | The reserve-van callback stayed hidden at Mill Ward and Meera's matching response appeared on arrival at Night Clinic. |
| Real crew movement, seats and handover | Passed, 19.7 s | Independent contexts and real WebSockets replicated keyboard movement, assigned distinct seats, rejected passenger driving and accepted explicit Take the wheel after driver exit. |
| Real crew voting and late-join recap | Passed, 1.7 min | Both players physically walked to the clinic. Correct on-foot voting guidance, visible split-vote status outside the dialog, ballot change/consensus, canonical recap and on-foot role passed. Closing the recap kept it closed through subsequent snapshots. No state fixtures or checkpoint injection were used. |
| Completed-room ending priority | Passed, 9.1 s | Explicit mocked-welcome presentation fixture: ending remains visible on join; the manual Crew panel still opens afterwards. It does not establish real room completion. |
| Native-confirm replay | Passed, 5.5 s | Reconstructed checkpoint reuses earned mission/player data, with default vehicles/command ledger. Real Story restore, native confirmation and replay reset to keys with empty history all passed. |
| Production standalone build | Passed over HTTP, then offline | Root verified keyboard dialogue, vehicle entry and driving with networking disabled after initial load, save detection after reload, embedded notices, no debug hooks and no external asset requests/page errors. Direct file navigation was blocked by managed Chromium policy. |
| Public-room invite | Passed | Root verified an invite opens City sandbox with its explicit room, joins that real room, and copies both mode and room into the invitation URL. |

The original final batch is preserved under `test-results/final/`: two tests passed and two test cases failed. The multiplayer failure expected the obsolete words “River Road” while the UI correctly showed the canonical River Steps objective. The campaign case reached and asserted its ending, then failed its later replay assertion because Playwright dismissed the native confirmation dialog. These are harness failures, not hidden passes. The harness now reads the canonical objective and explicitly accepts the confirmation. Follow-up results are recorded separately in `test-results/final-followup/`. Both completed-state regressions passed there; the real crew route hit its 120-second travel limit when dual software rendering starved browser input heartbeats. The position was on clear road, and the server correctly stopped the vehicle when intent grew stale. A second crew-only run reached the clinic but timed out on a click after restoring the larger canvases; its results are in `test-results/final-crew/`. The final CI tests separate the short seat/handover gate from voting and recap, keep a fixed small viewport, and physically walk both participants to the encounter. The complete campaign separately exercises driving. Both final split tests passed; results are in `test-results/final-crew-split/`.

The physical campaign took 10.7 minutes including the final 15-second replay assertion timeout. This is automation wall time under a software renderer, not a frame-rate or consumer-hardware performance measurement.

## Clean GitHub runs

Run [38834346095](https://github.com/occult-kranti/ANDOLAN/actions/runs/38834346095), on application commit `bdda206`, passed installation, typecheck, lint and all 42 tests, but failed its browser step. The environment blocked the redirected log download, so individual outcomes from that run remain unknown. Its job metadata is retained in `evidence/github-ci-first-run.json`.

Run [38835772270](https://github.com/occult-kranti/ANDOLAN/actions/runs/38835772270), on `40c7cae`, added GitHub failure annotations and saved reports without changing game code or assertions. Its browser summary was **three passed, four failed in 12.1 minutes**: the car settle predicate exceeded 15 seconds, both real-crew cases timed out clicking their initial interaction, and the selected campaign's ordinary walking exceeded the 140-second route limit. Mobile layout and both explicitly labelled completed-state cases passed. Exact assertion output is retained in `evidence/github-ci-second-run-annotations.json`; the Actions run also retains its browser report. Builds and Pages publication were skipped after these failures.

These failures are preserved separately from the earlier local passes. A focused local run with `ANDOLAN_SOFTWARE_RENDERING=1` passed all three previously failing smoke/crew checks: desktop controls in 22.7 seconds, movement/seats/handover in 13.2 seconds, and walking/votes/recap in 46.1 seconds (three passed in 1.4 minutes). Results are in `test-results/capped-smoke/results.json`. This was an intermediate run before the production timing fix and final full-suite verification.

Source review found a real fixed-timer defect: each delayed solo callback advanced only 0.05 seconds. One capped campaign was deliberately interrupted before a result while the correction was reviewed; it is neither a pass nor a failure. Commit `7cf1f27` then introduced monotonic elapsed time with bounded 20-Hz catch-up, wall-clock stale-input expiry, advance-before-new-input ordering, hidden-tab pause/reset and cleanup. Nine timing regressions pass, including two that fail against the old implementation. Sustained stalls beyond 250 ms are deliberately bounded; no rendering-performance guarantee is implied.

Run [38837936134](https://github.com/occult-kranti/ANDOLAN/actions/runs/38837936134), on final application commit `7cf1f27`, passed fresh installation, typecheck, lint, all 51 tests, **all seven browser cases (9.3 minutes)** and both production builds. The browser report uploaded successfully. The overall workflow then failed **only at Pages configuration**, which returned `Not Found` because the repository has no enabled Pages site; the deployment job was skipped. This is passing game verification, not a public launch. Full step and annotation metadata is in `evidence/github-ci-final-run.json`.

## Evidence

- `test-results/final/results.json`: original machine-readable results, including the two harness failures.
- `test-results/final/campaign-evidence.json`: earned stage list, final mission, seven decisions and player position extracted from the original report attachment.
- `test-results/final/game.e2e.ts-complete-six-c-da47d-driving-and-visible-choices/campaign-ending.png`: visible earned Open Windows ending.
- The Story and mobile result directories contain settled title and garage screenshots captured after four animation frames. Waiting for rendering avoids mistaking the previous title overview for the newly entered game camera.
- `test-results/final-followup/`: the passed, explicitly labelled completed-state regression tests and preserved software-rendering travel timeout.
- `test-results/final-crew/`: preserved larger-canvas interaction timeout after successful clinic arrival.
- `test-results/final-crew-split/`: final independent seat/handover and walking/vote/recap checks.

Test output is ignored by Git. Selected shareable evidence is archived by the release owner under `docs/evidence/`.

Stable release evidence includes `docs/evidence/round6-campaign-evidence.json`, `round6-campaign-ending.png`, `round6-crew-results.json`, `round6-private-crew-vote-tie.png`, `round6-late-join-recap.png`, `production-browser-check.json` and `container-check.json`.

## Corrections covered

The review identified and the owning agents corrected missing replay confirmation data, an invalid HTML room-code pattern, captions overlapping the map at medium widths, remote stage dialogue playing before arrival, reverse camera heading, late-join recap priority, and context-sensitive voting guidance. The harness itself was corrected to preserve settings during reload, wait for actual movement instead of fixed wall time, settle movement before comparing peer snapshots, use stable choice IDs, and accept native replay confirmation.

Vite hot reloads during early concurrent edits invalidated two exploratory sessions. Final campaign and follow-up runs used a frozen source tree. Continuous trace screenshots were disabled to avoid repeated software GPU readback; failure traces and selected screenshots remain enabled.

## Limits

This validates one selected story branch and browser interaction path. It does not validate every ending's pacing, human comprehension, physical gamepads, physical touchscreen controls, consumer hardware performance, accessibility with assistive devices, multi-region service behavior, or internet-scale concurrency. Real server protocol/capacity/persistence checks are maintained separately in the simulation/network tests and deployment verification. A successful room on the development server is not a public service launch.
