# YUGA Lane Lab

This branch contains an original offline `lane-economy` experiment using YUGA's fourteen heroes, 42 abilities, 21 models and Sangam City arena. Deadlock is a comparative research topic; no commercial source, assets or verified full-game replica is included.

Shared foundation `b8ecd2a058b8b7e0927b841867521c50f4e74162` is merged into `reference/deadlock-mechanics`. The 21 shared lab unit tests passed locally. Focused build/browser checks run in [GitHub Actions](https://github.com/occult-kranti/ANDOLAN/actions/workflows/yuga-reference-tracks.yml); inspect that branch's current result. The complete native journey and central public deployment remain separate gates.

GitHub rejected `POST /user/repos` with HTTP403, so this uses the requested branch fallback. Planned public entry: https://occult-kranti.github.io/ANDOLAN/yuga/lane-lab/ . It is not a publication claim until central deployment and public smoke pass.

Run `npm ci`, then `npm run yuga:lab:dev` or `npm run yuga:lab:build`. Vite consumes this [track.json](track.json) `id` and filters the mode selector through `VITE_YUGA_LAB_TRACK`; `YUGA_LAB_TRACK` optionally overrides it. Other metadata records scope, not executable enforcement. Deployments come from the central branch so these tracks cannot overwrite one another's Pages site.

The review below was initially written before the foundation merge; its source-reading boundaries and later-scope gates remain applicable. Integration state above supersedes those historical pending-integration notes.

## Evidence and actual reading

Audit: 16 October 2026 UTC. The main-worktree foundation was read at `games/yuga/reference/{types,controller,bots,objective}.ts`, together with the relevant economy, wave and ending paths in `games/yuga/shared/simulation.ts`. Root integration is active; the foundation is forthcoming and has not yet been merged into this worktree. Do not treat a relative link to an absent future file as current branch execution evidence.

Existing research: [Deadlock engineering](../games/yuga/docs/research/DEADLOCK_ENGINEERING.md), [reuse ledger](../games/yuga/docs/REUSE_LEDGER.md) and [Deadlock source pins](../games/yuga/docs/research/DEADLOCK_SOURCES.json). Root's newer `games/yuga/docs/research/REFERENCE_IMPLEMENTATION_SOURCES.md`, `REFERENCE_IMPLEMENTATION_PROVENANCE.json` and `games/yuga/docs/REFERENCE_GAME_ROADMAP.md` were read from the main worktree; they must accompany foundation integration. The study below checks selected actual downloaded files, rather than treating repository descriptions as gameplay evidence.

| Pinned source | Actual scope re-read in this pass | Verified lesson and boundary |
| --- | --- | --- |
| [Deadlock API](https://github.com/deadlock-api/deadlock-api/tree/917e8537cb256cffd1417a56737adfed47370dd1), `917e8537cb256cffd1417a56737adfed47370dd1`; MIT | Full root notice and `website/src/components/features/games/economy-definitions.ts` | This analytics implementation separates direct/orb income and removes overlapping assists from one display group. Useful for original source categories and accounting. It is neither a server nor proof of current commercial share/deny formulas. |
| [Deadlock-Manager](https://github.com/Mvfm-25/Deadlock-Manager/tree/c9252f69aac9088fee7151c883d7a4f91d98f51c), `c9252f69aac9088fee7151c883d7a4f91d98f51c`; GPL v3 root text | License header plus full `deadlock-manager/scripts/{minion,onda,guardiao,ponto_controle}.gd` | An independent Godot prototype: formation anchor pauses during combat; whole-wave replacement follows the last death; guardian target priority is lower; duplicate death emission is guarded. Its control zone uses minions and resets on empty/contest. These are that author's rules. Study-only; no GPL source, constants, scene or asset is copied. |

Selected source/license bytes were hashed against the existing immutable pin ledger: all six compared files matched. Full `minion.gd` was additionally read and hashed. No upstream installers, workflows, game client or engine were run; no network retrieval was required.

| File identity | SHA-256 |
| --- | --- |
| Deadlock API `LICENSE` | `e5cda462a2591bb55fc8c8c9ecd23f938690e5c00b4c75b8f70397a9e596c2bb` |
| Deadlock API `economy-definitions.ts` | `95a22403e61f3798cb2282670fa58255b74a113261534e597384a82dd01bb302` |
| Deadlock-Manager `LICENSE` | `3972dc9744f6499f0f9b2dbf76696f2ae7ad8af9b23dde66d6af86c9dfb36986` |
| Deadlock-Manager `onda.gd` | `4a47f1565b4de6a1e635fc3f610c8e64f62d34aa90b9428539d90e1150da877e` |
| Deadlock-Manager `guardiao.gd` | `458f6d4740c04527ca54c61115d0bdbffec5ab1d009d76dcb4f4a01425d67f60` |
| Deadlock-Manager `ponto_controle.gd` | `8c37f450e61c6470e73f47f595441ab83c78c12f00cc2dd860ab147235b78019` |
| Deadlock-Manager `minion.gd` | `a42922f75a0f0bb7fa740b86e7561f20920e229698366e7299ba100fb7e99f1c` |

Prior REA evidence is reused, not rerun: [DEADLOCK_REA_EVIDENCE.json](../games/yuga/docs/research/DEADLOCK_REA_EVIDENCE.json), evidence ID `ev_bfc90a5bb7dec46cf7ad2490d702cade60ec839454647602e6ec92d600b626e8`. It selected two MIT economy TypeScript files, parsed 7,012 bytes, reported zero parse failures and **193 explicit unknowns with partial coverage**. This pass rehashed the raw external output `/workspace/research/yuga-deadlock/rea-deadlock-economy.json`: 1,130,072 bytes, SHA-256 `1d6ae179737bb449622b09feb14353749465383e07f7bb3f4f5ef12eef4d54a5`, matching the compact record. It is static analytics evidence, not a played commercial simulation. The prior three synthetic helper checks and four Sketchbook jump-state checks remain prior, separately scoped tests; this pass claims no new gameplay test execution.

## Concrete comparison matrix

“Source-read” means code inspected; “pending” means acceptance remains open. No row verifies commercial parity. Preserve missing commercial facts as unknowns rather than fill them with constants from community examples.

| Mechanic | Reference evidence and unknown | Original current foundation, source-read | Next measurable gate |
| --- | --- | --- | --- |
| Lane pressure | Godot wave anchor/combat pause and delayed whole-wave replacement are inspectable. Current Deadlock wave cadence, routes and AI remain unknown. | Three original lanes; 18-second arena waves; three escort archetypes and every-third-wave siege; actor cap 96. Reference bots follow deterministic authored routes through ordinary authority input. | Mirrored seed/teams: record actual wave spawn, first contact and tower pressure; retarget after death; no double reward on simultaneous lethal damage. Do not substitute the Godot respawn recipe. |
| Structures and ending | Prototype guardian is stationary and deprioritized by minions. No commercial objective tree has been recovered. | Two destroyed allied towers expose a core; enemy core destruction wins. At 480 seconds, team score, then core health, then draw decides lane mode. | Lane mode keeps `objective=null`; exercise shield prerequisites, core win and each timeout tiebreak; terminal state freezes once. |
| Shared income | MIT analytics distinguishes source categories and overlapping assists; exact commercial shares remain unknown. | `ArenaSimulation.award` returns actual capped amounts per eligible nearby hero/source; defeat/camp events carry `sharedAwards`. | Reconcile every actual recipient and wallet cap; dead/out-of-range cases; no shared-award/orb double classification. |
| Contested pickups | Analytics separately names directly confirmed and orb income. This does not establish commercial last-hit/deny rules. | A shard has ID/source ID/expiry; secure/steal pays one actor after authoritative removal. Projectile and proximity paths share `secureGold`. | Two claimants, same shard, duplicate attempt, expiry, reset and disconnected/dead participant cases; record source ID, epoch, amount and claimant. Real multiplayer acceptance later requires two clients. |
| Wallet observations | Upstream analytics categories motivate explicit attribution, not runtime authority. | Lab polls credits after steps/commands and records bounded **net wallet deltas** (128 receipts). Totals can reconcile, but individual same-step sources are merged. | Preserve wallet reconciliation as one gate; separately verify source-level payout. Never label net-delta receipts a complete reward event ledger. |
| Spending/builds | Analytics is evidence of categories, not commercial item logic. Full commercial catalog/build balance remains unknown. | Original power/vitality/tempo upgrades, capped ranks, base-location and affordability checks; duplicate commands return cached results. | Accepted/rejected/duplicate purchase, cap, base range, reset and simultaneous income/spend accounting. Large item catalog remains disabled. |
| Weapon commitment | Inspected analytics/prototype code does not recover commercial hitscan, recoil, falloff or reload rules. | Existing hero projectile authority plus original lab 12-round primary magazine/1.6-second reload; Q/E/R do not consume rounds. Root added an optional accepted-primary observer, which debits ammo directly when an actual primary projectile is created rather than inferring it from retained visual events. | Observer addresses event-history overflow and projectile-cap ammo attribution in source; acceptance tests remain pending. Verify accepted primary reduces ammo once, capped/rejected/ability shots do not, plus reload pause/death/duplicate/reset and cover collision. Native cue must match authority. |
| Traversal | Prior MIT controller slice isolates input edges/one impulse; no current commercial mobility constants measured. | Existing jump, collision movement, stale-input expiry and authored kit movement. Universal slide/dash/mantle is absent. | Held jump, blur/menu/restart neutrality, fixed input schedule at differing render rates, authoritative obstacle contact; any new traversal remains a separately scoped experiment. |
| Hybrid comparison | Godot point resets while empty/contested and counts minions. It is not a Deadlock objective specification. | Original hero-only radius-8 point: six-second capture, contested freeze, empty capture decay, occupied-owner scoring to 60; 240-second tally. Lanes/camps/towers remain. Arena ending takes precedence. | Eligibility/contest/owner return/tally tests plus native physical traversal. Clearly explain core-loss precedence and that no objective credits are invented. |
| Readability and learning | No firsthand match observation or first-time-user test occurred in this pass. | Existing YUGA model/kit/telegraph foundation; new lab UI owned by World. | Native launch→lane→earn/claim→base upgrade→finish→restart/back; show AI labels, actual input bindings, separate team score/wallet/control score, source-versus-net receipt labels. Later human comprehension remains untested. |
| Online authority | Parsers and independent prototypes do not establish proprietary netcode or services. | First lab is offline with one local authority and epoch-guarded intent. | Keep online claims disabled until actual two-client preset agreement, reconnect, duplicate/stale input and finish/reset tests run against hosted WSS. |

## Finite implementation priorities

1. **Close the lane loop using the shared foundation.** Root integrates the shared modules; the build-time `lane` ID filters this focused edition to lane mode and World shows its true objective, economy and AI scope. QA verifies normal inputs, lane finish/reset/back and regressions. Acceptance remains pending; source reading or a built page alone cannot close it.
2. **Add source-correlated economy observations, if accepted by root.** This is the one bounded adapter improvement proposed below. Make reward origin and actual payout auditable before adding new rewards or item depth.
3. **Measure lane pressure on the existing rules.** Compare seeded/mirrored runs with spawn/contact/tower timings and explicit player absence. Only observed problems justify one further change; bot success does not establish fairness or fun.

## Later bounded adapter improvement

**Deferred proposal; current delivery keeps the net wallet-delta ledger. No shared file changed by this track.** Extend economy observations to retain an authoritative source identity and actual recipient amount for rewards and accepted spending. Preserve the existing economy rules and payout constants. Root/Systems must choose the observation API before implementation.

Evidence → `recordEconomy` currently stores epoch, serial, time, actor, absolute net delta, direction and balance. It lacks event/source identity. Several awards in one step become one receipt; the schema cannot prove which source paid or explain all capped portions. Systems confirmed purchases are recorded immediately at dispatch and simulation steps only award income in the current wrapper, so mixed income/spend cancellation is a future-proofing test, not an observed current defect. The existing arena already emits shard IDs for claims and actual `sharedAwards` for camp/defeat events, while structure awards and upgrades need complete actual payout/cost metadata for the same treatment.

Impact → aggregate wallet equality is useful but insufficient for source-level exactly-once attribution. A future economy display or transfer to YUGA would otherwise risk describing net observations as reward history.

Later decision for root → consider a small authority observation surface (or complete existing event metadata) keyed by run/epoch, authority event/source, recipient and category. Do not infer missing sources by splitting a net delta or add nominal values that exceed capped actual payouts. Expose bounded retention/gaps explicitly.

Owner → Systems implements shared observation metadata after acceptance; QA independently verifies; World labels source-correlated and wallet-total readouts correctly. This track supplies research/rule comparison only unless root reassigns implementation ownership.

Acceptance → initial 180 + actual income − actual spend = final wallet for every tracked hero; one shard pays at most once; two same-step sources stay separate; duplicate commands/claims, expiry/reset and finished runs create no extra reward; cap reductions use actual credited amounts; bounded retention never silently presents a full-match history. No gameplay formula change is part of the proposal.

## Existing prototype tests and remaining gaps

`games/yuga/reference-tests/controller.test.ts` was read in the main worktree. It contains cases for invalid/stale input, snapshot isolation, pause/catch-up, actual primary-shot ammo, ability/ammo separation, duplicate purchase, epoch reset and a normal bot match's wallet-delta reconciliation/finished freeze. The optional accepted-primary observer is now source-inspected in root's integration and addresses the prior event-overflow/projectile-cap inference flaw; no pass is inferred from the change. Presence of test code is not a result. All track test acceptance stays pending until root provides evidence. QA owns execution and exact pass counts. The existing arena economy suite separately exercises genuine primary-shot simultaneous shard claims and expiry/payouts; the new adapter must not relabel that as source-ledger coverage.

Still open for this track until explicit evidence is attached:

- Focused build consumes track ID, filters to lane mode and is served at the planned URL only after deployment; no current public-playability claim.
- Accepted-primary observer regression coverage under event-history overflow and projectile-cap rejection; no ammo charge for Q/E/R.
- Lane-only core result and timeout/tiebreak coverage with `objective=null`; keep fixture positioning/shortened clocks distinct from native traversal.
- Source-correlated receipts, mixed sources, capped awards, reset/expiry/no-reward summons and event-retention gaps; wallet-delta reconciliation alone does not close these.
- Full native lane journey with keyboard/mouse and touch, pause/blur/reload, mode switch/restart/back, model loading/disposal and HUD authority timing.
- Mirrored lane pressure and bot stuck-route checks with stated seeds; no balance conclusion from a single bot match.
- Actual two-client online evidence, performance on named consumer devices and first-time human comprehension; these are later gates, not present readiness claims.

## Art requirements and reuse targets

Reuse existing fourteen hero GLBs, seven unit GLBs, Sangam City collision/world, authored epic-inspired costumes and existing Q/E/R telegraphs. The [reuse ledger](../games/yuga/docs/REUSE_LEDGER.md) distinguishes pinned MakeHuman CC0 anatomical data from original garments/equipment/animations; retain that provenance and required build notices. No Deadlock model, animation, environment layout, VFX, UI graphic, audio or branding is authorized by this study.

For this bounded lane lab, prioritize visible mechanic states: distinct secure/steal pickup cues; readable shard expiry and actual amount; team/role silhouette at normal camera distance; vulnerable versus shielded structure state; aim/cover clarity; reload start/completion; and a clearly separate hybrid point ring. Use shape/text as well as color and honor reduced-motion settings. Animation duration must not decide damage, pickup ownership or cooldown. Any new visual/audio artifact needs creator/license/source/hash and a measured rendering/loading budget before adoption. No new models are required to test this track's first loop.

Reusable targets for deliberate YUGA adaptation are source-attributed reward readouts, trustworthy reload/cast/result cues, deterministic input/bot scenarios, explicit finish precedence and clean epoch reset. Each transfer needs a specific observed YUGA problem, original rule, accepted lab case, affected regression/native checks and before/after evidence. The track is a mechanics laboratory; implementation, art polish, release and commercial equivalence remain distinct claims.
