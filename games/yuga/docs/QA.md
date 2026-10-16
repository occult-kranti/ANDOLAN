# YUGA: Confluence — acceptance and evidence

This is the QA ledger for the separate YUGA app on `game/yuga-confluence`. Existing ANDOLAN tests, saves, files and public root are outside this change. This ledger records what was observed; an acceptance plan is not a passing result.

## Current state

Baseline contract review and harness authoring are complete. The first exploratory desktop/mobile render reached practice but emitted a WebGL disposal error; those screenshots precede repairs and do not pass acceptance. Five focused browser checks passed after the first repair freeze (one release soak deliberately skipped). The first complete-match stress attempt then exposed a real bot-area-attack iteration crash at seed 7, tick 1223, simulated 61.15 seconds; the owner repaired the copied-actor iteration and added a regression. The complete matrix then passed. The user has requested a replacement character-art pipeline, so the current runtime art is a functional placeholder baseline; the eight-minute release soak and public acceptance remain held until that pass. Only bounded local stress is measured; public-service capacity is unmeasured.

## Acceptance gates

| ID | Gate | Required evidence | State |
| --- | --- | --- | --- |
| YQ-01 | All fourteen kits are selectable | Fourteen roster cards, correct selected name/description/three skills; simulation coverage of all 42 skills and distinct stat/weapon compositions | Historical 12-card baseline passed; 14-card/art acceptance pending |
| YQ-02 | Native practice combat | Start from roster; keyboard movement/aim/fire, real damage or authoritative hit, Q/E/R cooldowns/events, jump, no injected input/command or actor position changes | Pass: ordinary keyboard combat caused real damage; no mutation |
| YQ-03 | Upgrades explain and enforce limits | Successful spawn purchase changes credits/level once; insufficient credits and away-from-spawn rejection remain visible and do not spend | Pass: native spawn purchase, funds/base disabling; systems authority tests |
| YQ-04 | Menus preserve control and time semantics | Held movement/fire released on menu/blur/hide, no modal/typing ability casts; practice pauses, online match continues; close restores world focus | Focused menu and online-time semantics pass; extra hidden-tab paths pending |
| YQ-05 | Audio is explicitly started and stops correctly | Gesture unlock/preview, native context and post-master sample checks if diagnostics available, volume zero while running, menu/hidden silence and recovery; no listening-quality claim | Pass: native preview/nonzero +volume0 samples and mute retention; no listening claim |
| YQ-06 | Settings persist and mobile controls fit | Quality/volume/sensitivity/reduced motion through UI; reload retention; 390px touch movement/aim/fire/ability controls, no horizontal overflow or overlapping essential controls | Pass: native preferences/reload and 390px touch emulation |
| YQ-07 | Match rules produce a finish and a fresh replay | Three lane waves; two defending towers unlock that team's core; death/respawn and eight-minute tie rules verified in authoritative simulation; native finish separately recorded if actually played | Full 480s simulation matches and labelled result/replay fixture pass; native eight-minute soak held for art pass |
| YQ-08 | Two real clients share authoritative state | Real WebSockets, same room/tick progression, unique humans with bot replacement, movement/combat/objective state converges; replay/late join must not retain stale controls | Pass: two actual local browser contexts, movement/ability/purchase |
| YQ-09 | Reconnect preserves identity safely | Same hero/team/KDA/upgrades, one actor, temporary bot takeover, neutral resumed controls; replacement socket does not create reconnect contention | Pass: real browser leave/rejoin same identity/hero/team/upgrades |
| YQ-10 | Malicious or duplicate commands do not create authority | Server validation of finite bounded input and alive/cooldown/range/credits; repeated command ID casts/spends at most once; no client hits/rewards/timers | Pending, systems-owned tests |
| YQ-11 | Bounded stress is measured | Fixed simulation/loopback WS scenarios, actual client/room/actor counts, elapsed time, p50/p95 timing, CPU/RSS/loop lag and machine/cgroup limits; no extrapolated production capacity | Pass after targeted repair:6 full simulations +6/12/24 real sockets; first failure retained |
| YQ-12 | Published app is isolated and runnable | Old root intact, `/ANDOLAN/yuga/` loads expected build, production has no DEV hooks, real public UI smoke, valid server files and honest public-server availability | Pending |

## Browser execution rules

- Use `playwright.yuga.config.ts`, one worker, local Vite 5180/server 3005. Browser runs wait for the integrated source freeze; no parallel software-render browser batches.
- Read-only `__YUGA.snapshot()/playerId()/metrics()/audio()` observations are permitted in development. Gameplay gates use ordinary keyboard, pointer and touch events. Direct simulation commands, positional setup, mocked sockets and shortened clocks are labelled fixtures and never count as native combat or a physically completed match.
- A software-render scheduler may cap render dispatch to a maximum ten frames per second while preserving callbacks, timestamps and cancellation. It may not alter simulation/input/network timers. Such checks establish functionality under that test budget, not consumer hardware performance.
- Use exact state/assertion evidence. A rejected request is not a successful action; a screenshot is not a frame-rate measurement; an AudioContext or waveform is not perceptual listening.
- Preserve failed attempts and distinguish confirmed app defects, harness setup errors and unresolved causes. Do not repeatedly retry a native action to turn a failure into a pass.
- A long native match is a separate bounded release/soak observation. A completed-state fixture may verify result/replay presentation, but its provenance must remain visible in reports.

## Planned stress envelope

Simulation runs cover complete eight-minute matches at fixed 20Hz with multiple seeds and record actual entity/event counts and step timing. Actual loopback WebSocket scenarios use 6, 12 and 24 clients in 1, 2 and 4 rooms, respectively, at the normal input rate for bounded periods. The initial scope is one process containing both the authoritative server factory and synthetic socket clients; CPU and RSS therefore describe that combined harness. Report cgroup CPU/memory ceilings separately from host totals. Do not call a percentile result a service guarantee or infer national capacity.

## Evidence index

- Exploratory first look: `evidence/first-look.json` and `first-desktop-*` / `first-mobile-*` screenshots. A disposal error and near-core spawn framing were reported for repair; this is not final acceptance.
- Authored browser checks: `../tests/arena.e2e.ts`, configured by repository `playwright.yuga.config.ts`. The long native match requires `YUGA_FULL_MATCH=1`; routine result/replay coverage explicitly uses a mocked-socket fixture.
- Authored bounded load harness: `../tools/stress.ts`. Execution and measurements are pending.

Focused baseline evidence: `evidence/baseline-browser-check.json` (source hashes,5 passed, 1 skipped), full Playwright report `baseline-browser-report.json`, and `baseline-*.png`. Full-match stress failure: `evidence/baseline-stress-failure.json`. No native eight-minute finish or final character-art pass is claimed.

## Bounded baseline stress result

`evidence/baseline-stress-all.json` preserves the completed pre-art/pre-new-mechanics matrix and source hashes. All six 480-second simulations finished; the three bot seeds destroyed all six lane towers and ended by score at the time limit. Peak entity counts were42 actors and28 projectiles, within the asserted bounds. Three fixed synthetic-human repetitions also completed. This is accelerated simulation evidence, not a native browser finish.

Actual loopback WebSocket scenarios each ran20 seconds at approximately19.95 inputs/client/second. Six, 12 and 24 clients used1, 2 and 4 rooms. Snapshot interarrival p95 was101.94, 101.44 and 112.96 ms respectively. In the 24-client scenario, combined server/client process CPU used12.32% of one core and peak observed RSS was159,043,584 bytes. Machine: Linux x64, Node 24.19, AMD EPYC 7763, four CPU quota and 32 GiB cgroup memory. No WAN, multi-host, public WSS, consumer-GPU or national-capacity result is implied.

Approved replacement art and new authoritative mechanics reopen the build. The five-browser baseline and stress matrix are preserved historical evidence; final acceptance requires reruns on the new source.

## Fourteen-hero art and mechanics revision

The current revision adds Chitrangada and Ulupi, for 14 heroes and 42 abilities. The earlier browser/stress evidence remains historical. Final acceptance now requires:

| Gate | Method and explicit limit | State |
| --- | --- | --- |
| Exported assets | `tools/verify-hero-assets.ts` verifies the complete 14-ID manifest, file hashes, every accessor/skin weight/rest vertex, nine required clips, 17 sampled skinned poses per clip and 432 generic TRS crossfades per hero. Finite/bounded geometry and stationary root are hard checks; loop/floor warnings need review. | Passed on frozen14-model manifest d7a9af06: all hard checks; Sita defeat costume/prop floor warning requires visual review |
| Actual browser models | `tests/hero-assets.e2e.ts` starts fresh practice for all 14 heroes and requires real GLB requests, no fallback, actual skin/bone diagnostics, native run/fire/Q/E/R/jump transitions and measured pose change. | Authored; waiting complete exports and source freeze |
| Defeat/recovery and clone isolation | A separately labelled mocked-socket fixture places duplicate same-hero actors near the camera and verifies disjoint skeleton instances plus different active animation states. This is presentation evidence, not an earned defeat or network-authority result. | Authored; pending |
| Native counter timing | Two real browser clients and a real server without hero bots isolate the Dawn Volley windup and ordinary lateral movement. No position/health/time commands are injected; lane waves remain active. | Authored; pending |
| Full match and regression | Original native combat/settings/mobile/real-WSS/reconnect checks, all 14 selectors, full 480-second native practice, and post-revision bounded stress. | Held until final assets/source freeze |
| Balance | Systems-owned 168-match mirrored/lane/seed AI matrix, counter regressions and objective/support outcomes; results explicitly limited to the benchmark bot policy. | Separate systems evidence; no human competitive-balance claim |

Required exported clips are `idle`, `run`, `fire`, `cast`, `cast1`, `cast2`, `cast3`, `jump`, and `defeat`. A clip's existence, numeric sample validity and browser state transitions do not establish absence of every animation artifact. Front/side/rear gameplay frames, weapon grip, clothing deformation, same-hero simultaneous playback and mobile readability still require visual inspection. Public Deadlock video access was blocked; the separate tooling note does not claim footage was watched or proprietary game data inspected.

## Frozen fourteen-hero numeric gates

`evidence/hero-assets-check.json` passed all14 exported GLBs and126 required clips, including every accessor, weight and rest vertex,17 sampled skinned poses per clip and432 generic TRS crossfades per model. Sita defeat reaches12.25cm below its rest floor in combined costume/prop geometry; this remains a visual-review warning. The independent Blender check in `animation-final-authored-deformation.json` evaluated5052 frames across the final14 authored bodies. Body deformation, stationary roots and idle/run seams passed its stated thresholds; Sita defeat body minimum was-1.409mm, and the global minimum was-20.52mm during Bhima run. These numeric checks do not replace actual rendering inspection.

`evidence/final-roster-stress-all.json` preserves the revised mechanics matrix with matching start/end source hashes. Six full480-second simulations finished and remained within finite/entity bounds (peak40actors). Actual6/12/24-client loopback runs lasted20seconds each; snapshot interarrival p95 was101.38/101.51/102.45ms. The24-client combined server/client process used12.93% of one core and observed171,819,008bytes peakRSS. No browser, Blender or build competed; brief targeted lint/typecheck overlapped the final socket scenario, as recorded. This remains a local bounded measurement.

Executed REA open-shooter source study: `evidence/rea-open-shooter-aim.json` and `../art/DEADLOCK_VIDEO_AND_TOOLING.md`. MIT JavaScript files were parsed by REA; GPL Quake III C was imported as a historical reference and manually read. Neither is commercial binary analysis or watched Deadlock footage.
