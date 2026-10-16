# City Reform Beta 0.3 verification

## Status

The final source gate passed TypeScript, ESLint and 134 tests across 13 files. Four focused browser cases passed locally: native audio/Story isolation, mobile controls/settings, both labelled mandate fixtures, and the actual two-client media route. The full thirteen-case Actions gate and publication remain pending. The previous City Jobs baseline passed all ten browser cases in 491.765 seconds; those historical results are preserved in `evidence/multiplayer-beta-browser-results.json`. They do not establish the new content or control changes.

The current release adds ten jobs in total, five one-shot cases, four sector ledgers, two permanent mandate outcomes, native Settings audio preview, revised input handling and camera/marker improvements. Source, renderer and authority reviewers are recorded in [CITY_REFORM_PANEL.md](CITY_REFORM_PANEL.md).

## Verification boundaries

- Unit/simulation checks cover guards, duplicate commands, durable case ledger, payout policy, majority votes, invalid saves and migration. Tests that position the authoritative simulation are fixtures, not proof of physical driving.
- Browser traversal uses bounded movement/steering inputs through the real simulation. The opening media case and the repeatable van delivery have dedicated two-client routes; final-mandate browser fixtures are labelled separately.
- Native WebAudio diagnostics measure actual output, attenuation and lifecycle. They do not establish a human listening assessment or a polished mix on every device.
- Chromium mobile emulation checks controls and layout; it does not measure real-phone GPU performance. Software-rendered cloud runs do not support an FPS claim.
- Container checks establish local production packaging and persistent room recovery. An operated public backend remains unprovisioned; the Render Blueprint is a prepared paid-hosting configuration, not a deployed service.
- The static public website is a separate deployment gate. Its version and HTTP/browser evidence must be checked after Actions completes.

## Results

| Check | Result and evidence |
| --- | --- |
| Source | `npm run typecheck && npm run lint && npm test`: pass; 134 tests / 13 files, 16 October 2026. |
| Native audio and separate saves | Passed in 28.185 s. Preview produced measured RMS 0.00881 while preserving mute/preferences; gameplay RMS 0.01034; zero-volume running output attenuated to 0. Earned Story stage `clinic-drive` remained unchanged. `evidence/city-reform-audio-and-save.json`. |
| Mobile controls/settings | Passed in 21.449 s. Genuine keyboard/CDP touch input: duplicate/reserved-key rejection, Escape/close cancellation, touch after remapping, full keyboard/touch braking at zero, parked camera alignment, immediate movement after menu close, and larger text restored from 14 to 16.1 px. `evidence/city-reform-controls.json`. |
| Two mandate routes | Passed in 20.094 s from explicitly prepared completed-case checkpoints. Actual UI choices show their consequences, settle through the solo simulation, remove further choices and survive reload. This is not physical sector traversal. `evidence/city-reform-mandate-fixtures.json`. |
| Actual media case | Passed in 71.950 s with two independent browser contexts and real WebSockets. All five stages were earned through bounded movement/driving and visible interactions in the same compact. Shared reward: 120 credits / 2 reputation / 1 project. Duplicate completion did not repay; five receipts appeared and the energy case unlocked. `evidence/city-reform-media-route.json` and `city-reform-physical-results.json`. |
| Full integrated browser suite | Pending the required thirteen-case GitHub Actions gate. |
| Final production container / standalone / public HTTPS | Pending final artifacts and deployment. |

Initial failures are retained in `evidence/city-reform-focused-results.json`. The first native run exposed a real delayed-close input clear and a HUD focus problem; both were repaired and retested without timing or focus workarounds. The wrong room name in an ending fixture was correctly rejected by save validation and fixed in the harness. A screenshot timeout was corrected by reducing that fixture viewport; outcome/persistence assertions remain intact. The three-repeat native close-event proof is `evidence/multiplayer-beta-menu-close-race.json`.

The final small-screen layout refresh passed both focused controls/ending cases (22.3 s / 20.6 s); a geometric assertion confirms the speed display clears the touch buttons. Updated outcome captures show the selected mandate. A fresh nearby WALK marker capture used ordinary practice controls without a checkpoint fixture. See `city-reform-visual-final-results.json` and `city-reform-nearby-objective.json`. Final container and publication identifiers will be added after those gates. Current public First Edition evidence remains in `public-pages-*` and `github-pages-release-run.json`; do not interpret those files as Beta 0.3 results.
