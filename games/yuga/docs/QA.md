# YUGA: Confluence — acceptance and evidence

This is the QA ledger for the separate YUGA app on `game/yuga-confluence`. Existing ANDOLAN tests, saves, files and public root are outside this change. This ledger records what was observed; an acceptance plan is not a passing result.

## Current state

The frozen fourteen-hero revision has passed the exported-asset gate, all fourteen real-model native action checks, fourteen explicitly labelled defeat/clone fixtures, native practice/settings/audio/mobile checks, real two-browser reconnect checks, and bounded simulation/socket stress. Built production pages at both `/` and `/yuga/` loaded all fourteen GLBs in Chromium. These results precede the newly requested jungle, contested-gold and political/minion expansion; they are preserved baseline evidence, not acceptance of that new work.

The native counterplay case remains open: its first attempt hit a building after a software-rendering route overshoot; the repaired route reached combat and observed local windup, but sequential peer polling missed that transient state. Both failures are retained. The full eight-minute native soak was not started before the source reopened. Public deployment is awaiting the expanded-source CI and native gates. The earlier Pages main-only policy blocked the branch and its API update returned403; the user has since removed that restriction. Local production acceptance remains separate from actual public deployment and a hosted WebSocket service.

## Acceptance gates

| ID | Gate | Required evidence | State |
| --- | --- | --- | --- |
| YQ-01 | All fourteen kits are selectable | Fourteen roster cards, correct selected name/description/three skills; simulation coverage of all 42 skills and distinct stat/weapon compositions | Pass: all fourteen native selectors and real-model actions; 42-skill systems coverage |
| YQ-02 | Native practice combat | Start from roster; keyboard movement/aim/fire, real damage or authoritative hit, Q/E/R cooldowns/events, jump, no injected input/command or actor position changes | Pass: ordinary keyboard combat caused real damage; no mutation |
| YQ-03 | Upgrades explain and enforce limits | Successful spawn purchase changes credits/level once; insufficient credits and away-from-spawn rejection remain visible and do not spend | Pass: native spawn purchase, funds/base disabling; systems authority tests |
| YQ-04 | Menus preserve control and time semantics | Held movement/fire released on menu/blur/hide, no modal/typing ability casts; practice pauses, online match continues; close restores world focus | Focused menu and online-time semantics pass; extra hidden-tab paths pending |
| YQ-05 | Audio is explicitly started and stops correctly | Gesture unlock/preview, native context and post-master sample checks if diagnostics available, volume zero while running, menu/hidden silence and recovery; no listening-quality claim | Pass: native preview/nonzero +volume0 samples and mute retention; no listening claim |
| YQ-06 | Settings persist and mobile controls fit | Quality/volume/sensitivity/reduced motion through UI; reload retention; 390px touch movement/aim/fire/ability controls, no horizontal overflow or overlapping essential controls | Pass: native preferences/reload and 390px touch emulation |
| YQ-07 | Match rules produce a finish and a fresh replay | Three lane waves; two defending towers unlock that team's core; death/respawn and eight-minute tie rules verified in authoritative simulation; native finish separately recorded if actually played | Full 480s simulation matches and labelled result/replay fixture pass; native eight-minute soak held for new mechanics expansion |
| YQ-08 | Two real clients share authoritative state | Real WebSockets, same room/tick progression, unique humans with bot replacement, movement/combat/objective state converges; replay/late join must not retain stale controls | Pass: two actual local browser contexts, movement/ability/purchase |
| YQ-09 | Reconnect preserves identity safely | Same hero/team/KDA/upgrades, one actor, temporary bot takeover, neutral resumed controls; replacement socket does not create reconnect contention | Pass: real same-page rejoin executes a new ability; reload retains one identity/hero/team/upgrades with bot takeover |
| YQ-10 | Malicious or duplicate commands do not create authority | Server validation of finite bounded input and alive/cooldown/range/credits; repeated command ID casts/spends at most once; no client hits/rewards/timers | Pass in systems-owned input/command/clock/network tests; expansion authority needs new regressions |
| YQ-11 | Bounded stress is measured | Fixed simulation/loopback WS scenarios, actual client/room/actor counts, elapsed time, p50/p95 timing, CPU/RSS/loop lag and machine/cgroup limits; no extrapolated production capacity | Pass after targeted repair:6 full simulations +6/12/24 real sockets; first failure retained |
| YQ-12 | Published app is isolated and runnable | Old root intact, `/ANDOLAN/yuga/` loads expected build, production has no DEV hooks, real public UI smoke, valid server files and honest public-server availability | Built root/nested Chromium pass; previous branch-policy block removed by user, expanded public deployment pending |

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
- Authored bounded load harness: `../tools/stress.ts`. Both historical and revised measured runs are preserved below.

Focused baseline evidence: `evidence/baseline-browser-check.json` (source hashes,5 passed, 1 skipped), full Playwright report `baseline-browser-report.json`, and `baseline-*.png`. Full-match stress failure: `evidence/baseline-stress-failure.json`. No native eight-minute finish or final character-art pass is claimed.

## Bounded baseline stress result

`evidence/baseline-stress-all.json` preserves the completed pre-art/pre-new-mechanics matrix and source hashes. All six 480-second simulations finished; the three bot seeds destroyed all six lane towers and ended by score at the time limit. Peak entity counts were42 actors and28 projectiles, within the asserted bounds. Three fixed synthetic-human repetitions also completed. This is accelerated simulation evidence, not a native browser finish.

Actual loopback WebSocket scenarios each ran20 seconds at approximately19.95 inputs/client/second. Six, 12 and 24 clients used1, 2 and 4 rooms. Snapshot interarrival p95 was101.94, 101.44 and 112.96 ms respectively. In the 24-client scenario, combined server/client process CPU used12.32% of one core and peak observed RSS was159,043,584 bytes. Machine: Linux x64, Node 24.19, AMD EPYC 7763, four CPU quota and 32 GiB cgroup memory. No WAN, multi-host, public WSS, consumer-GPU or national-capacity result is implied.

Approved replacement art and new authoritative mechanics reopen the build. The five-browser baseline and stress matrix are preserved historical evidence; final acceptance requires reruns on the new source.

## Fourteen-hero art and mechanics revision

The current revision adds Chitrangada and Ulupi, for 14 heroes and 42 abilities. The earlier browser/stress evidence remains historical. Final acceptance now requires:

| Gate | Method and explicit limit | State |
| --- | --- | --- |
| Exported assets | `tools/verify-hero-assets.ts` verifies the complete 14-ID manifest, file hashes, every accessor/skin weight/rest vertex, nine required clips, 17 sampled skinned poses per clip and 432 generic TRS crossfades per hero. Finite/bounded geometry and stationary root are hard checks; loop/floor warnings need review. | Passed on frozen14-model manifest d7a9af06: all hard checks; visual review accepts Sita defeat cloth/prop pooling as a recorded cosmetic limitation |
| Actual browser models | `tests/hero-assets.e2e.ts` starts fresh practice for all 14 heroes and requires real GLB requests, no fallback, actual skin/bone diagnostics, native run/fire/Q/E/R/jump transitions and measured pose change. | Passed: all 14 actual-model native sequences, 282.9 seconds, no fallback or page errors |
| Defeat/recovery and clone isolation | A separately labelled mocked-socket fixture places duplicate same-hero actors near the camera and verifies disjoint skeleton instances plus different active animation states. This is presentation evidence, not an earned defeat or network-authority result. | Passed: 14 labelled fixtures, 124.7 seconds, disjoint skins and late defeat pose |
| Native counter timing | Two real browser clients and a real server without hero bots isolate the Dawn Volley windup and ordinary lateral movement. No position/health/time commands are injected; lane waves remain active. | Open: route repaired; transient peer-phase observer needs repair before a valid dodge result |
| Full match and regression | Original native combat/settings/mobile/real-WSS/reconnect checks, all 14 selectors, full 480-second native practice, and post-revision bounded stress. | Focused native regressions and revised stress pass; full soak held for new mechanics expansion |
| Balance | Systems-owned 168-match mirrored/lane/seed AI matrix, counter regressions and objective/support outcomes; results explicitly limited to the benchmark bot policy. | Separate systems evidence; no human competitive-balance claim |

Required exported clips are `idle`, `run`, `fire`, `cast`, `cast1`, `cast2`, `cast3`, `jump`, and `defeat`. A clip's existence, numeric sample validity and browser state transitions do not establish absence of every animation artifact. Front/side/rear gameplay frames, weapon grip, clothing deformation, same-hero simultaneous playback and mobile readability still require visual inspection. Public Deadlock video access was blocked; the separate tooling note does not claim footage was watched or proprietary game data inspected.

## Frozen fourteen-hero numeric gates

`evidence/hero-assets-check.json` passed all14 exported GLBs and126 required clips, including every accessor, weight and rest vertex,17 sampled skinned poses per clip and432 generic TRS crossfades per model. Sita defeat reaches12.25cm below its rest floor in combined costume/prop geometry; final rendered review found a controlled kneel without gross body deformation and retains the cloth/prop floor pooling as a cosmetic limitation. The independent Blender check in `animation-final-authored-deformation.json` evaluated5052 frames across the final14 authored bodies. Body deformation, stationary roots and idle/run seams passed its stated thresholds; Sita defeat body minimum was-1.409mm, and the global minimum was-20.52mm during Bhima run. These numeric checks do not replace actual rendering inspection.

`evidence/final-roster-stress-all.json` preserves the revised mechanics matrix with matching start/end source hashes. Six full480-second simulations finished and remained within finite/entity bounds (peak40actors). Actual6/12/24-client loopback runs lasted20seconds each; snapshot interarrival p95 was101.38/101.51/102.45ms. The24-client combined server/client process used12.93% of one core and observed171,819,008bytes peakRSS. No browser, Blender or build competed; brief targeted lint/typecheck overlapped the final socket scenario, as recorded. This remains a local bounded measurement.

Executed REA open-shooter source study: `evidence/rea-open-shooter-aim.json` and `../art/DEADLOCK_VIDEO_AND_TOOLING.md`. MIT JavaScript files were parsed by REA; GPL Quake III C was imported as a historical reference and manually read. Neither is commercial binary analysis or watched Deadlock footage.

## Fourteen-hero native revision result

`evidence/final-hero-browser-check.json` and `final-hero-browser-report.json` record two passing batches: all fourteen actual GLBs through gallery, fresh practice, native run/fire/Q/E/R/jump (282.9 seconds), and fourteen labelled defeat/recovery/private-skeleton fixtures (124.7 seconds). Fifty-six screenshots retain the final manifest and source hashes. Every imported model exposed nine clips and real skin instances; no fallback or page errors occurred. The generic `cast` clip is numerically sampled and loaded; native Q/E/R exercise `cast1`/`cast2`/`cast3`. These finite samples do not prove every possible transition is artifact-free. Fixture snapshots intentionally omit a live heartbeat and cannot substantiate network freshness.

`evidence/final-native-revision-check.json` preserves seven additional passing case records and two failed counter attempts. Native practice caused 63.18 damage using ordinary keyboard aim, lock and fire. Real two-context movement, purchase, same-page new-ability rejoin and reload identity passed in101.9 seconds; the result/replay presentation fixture passed in6.5 seconds. Native WebAudio previews, volume-zero attenuation, settings persistence and390px touch controls passed. Software rendering used the stated maximum10fps dispatch budget; this is no hardware frame-rate or listening-quality claim.

Independent file-only visual review found no new framing/deformation blocker in final Chitrangada, Ulupi, Rama, Hanuman and Ravana frames or Sita's late defeat pose. Sita's palette and cloth/prop floor pooling remain art limitations. Several action stills were captured after cooldown began, so they do not prove active bespoke VFX appearance.

## Jungle expansion acceptance plan

| Risk | Required check | Evidence boundary |
| --- | --- | --- |
| Neutral camps become free or permanent rewards | Native approach, attack, aggro; authority leash/return, regeneration/reset and respawn timers; repeated lethal/projectile updates grant once | Unit/real-socket authority plus one physical native camp encounter; any shortened setup labelled |
| Gold can be claimed remotely or twice | Visible drop and lifetime; near-range claim, rival steal semantics, expiry, duplicate command IDs and simultaneous claims serialize to one owner | Exact protocol fields pending systems contract; no client-supplied payout or hit accepted |
| Temporary power survives its intended limit | Gain from valid camp outcome, HUD countdown/description, one use or expiry per contract, death/rejoin/replay policy and stale-token rejection | Read-only native diagnostics plus authoritative tests; do not infer duration from an icon |
| New wave roles and art disagree | Court/minister, city-watch, soldier and king roles match authoritative kind/team; real models, animation states and no fallback; visible attack/death and bounded waves | Numeric model gate where applicable; actual browser snapshots and screenshots with actor IDs |
| Mouse chords leave fire/aim stuck | Left fire plus right lock, release either first, drag-release outside, Escape/modal, blur and pointer cancel; aim/lock does not start unwanted shots | Native pointer input and observed ordinary input/shot state, no injected gameplay command |
| Added entities degrade the complete loop | Repeat revised full simulations and bounded actual sockets; all14 hero regression, two-client identity, final native eight-minute finish/replay, production asset URLs | Source-hashed results after final integration freeze; capacity claims remain local and bounded |

These gates were written before implementation; execution evidence is recorded below. Earlier-revision outcomes are not silently promoted to the expanded rules.


## Jungle expansion numeric and focused gates

The final seven-unit manifest `3adc9c1be2132d5064d5ac8b4122675d88e2079ca68125eac9ed221c12491776` passed the binary gate with zero warnings: seven real GLBs,28 required clips,80 bones/model, four materials/model and7,400–10,000 triangles. Every accessor, weight and bind vertex was checked;17 poses/clip and72 generic crossfade samples/model remained finite and bounded. The earlier passing manifest is preserved separately because a city-watch supporting-hand correction changed one binary. The independent authored-body report `unit-animation-final-authored.json` records1,283 frames, stationary roots and exact loop/fire recovery, with the corrected hand/receiver gap at most0.48mm. These numeric results are not a native playthrough or whole-costume visual guarantee.

New native mouse-chord and real asset-load cancellation cases, labelled390px reward/camp HUD and recent/stale/resume event cases, a true local-server camp traversal and seven-unit animation fixtures are authored. The first focused browser batch may run alongside the deterministic168-match AI comparison by coordinator approval. Neither its wall time nor software frame rate is treated as a performance measurement. Measured stress and Docker builds wait for a separate quiet browser boundary.

Remote historical run38942766367 at d9a66889 recorded7 passed,3 failed,1 skipped. The failed practice script had died before its first shot; the old counter route timed out; one cast transition was missed. The report ZIP was Forbidden at its Azure redirect, so exact hero/receipt details were unavailable. `ci-38942766367-check.json` preserves these limits. The route, event-age handling and future failure diagnostics have changed; that failed CI is not silently replaced by earlier local passes.

### Expanded focused execution

Six new cases passed in two sequential batches. `jungle-focused-check.json` records native mouse-button chords and menu release (40.7s), cancellation/restart while actual GLB responses are delayed (13.8s), labelled mobile reward/camp HUD snapshots (12.5s), and labelled recent/stale/resume animation events (10.9s). The initial attempt remains archived: the mouse observer mistook eviction from the bounded event history for a reversed shot counter, while two final console checks caught the missing favicon. The observer now retains the highest authoritative shot ID seen; release/cooldown assertions remain unchanged. Root embedded an original icon; reruns had no recorded page or console errors.

`jungle-native-units-check.json` records an actual local WebSocket camp loop using ordinary keyboard movement, target lock and primary fire. It passed normal spawn, aggro, retreat/leash reset to full health, re-engagement and defeat, one camp reward and one secured30-credit shard, Vigor gain/expiry, physical retreat toward the friendly tower, and the normal40-second full-health respawn. Hero bots were disabled; lane waves and authority clocks remained active. No position, health, reward or time was injected. This run proves a secure claim; rival theft is covered separately by authority tests and explicitly labelled HUD fixtures.

The same batch passed seven real unit GLBs through idle, run, fire and advancing defeat animations in53.9s, with real skin/pose diagnostics and no fallback. These unit-state snapshots are explicitly synthetic, so they do not claim seven earned native kills. Thirty-one screenshots preserve the native camp and unit presentation evidence. The browser used SwiftShader with a maximum10fps render dispatch budget, and part of the batch overlapped the deterministic AI matrix; no hardware performance conclusion follows.

`jungle-native-regression-check.json` records two additional passes: normal practice movement/combat/Q/E/R/purchase/pause in27.7s and actual two-client Dawn Volley counterplay in50.3s. The peer received windup at authoritative time17.85s; its first lateral movement appeared at18.05s, before release18.80s, and no attacker-to-dodger hit was observed. A native key reacts automatically to the received packet; this proves the ordinary input/authority path can evade the attack, not human reaction speed or every VFX pixel. Actors physically walked from their spawns, with no position/health/time mutation. Prior failed counter attempts remain archived. All eight new/changed focused cases therefore pass across three sequential batches. Browsers then closed for isolated stress and production packaging; final native480-second finish and current public release remain pending.
