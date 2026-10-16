# YUGA Objective & Hero Combat Lab

This branch contains an original offline `control-point` experiment using YUGA's fourteen heroes, 42 abilities, 21 models and Sangam City arena. Overwatch is a comparative research topic; no commercial source, assets or verified full-game replica is included.

Shared foundation `b8ecd2a058b8b7e0927b841867521c50f4e74162` is merged into `reference/overwatch-mechanics`. The 21 shared lab unit tests passed locally. Focused build/browser checks run in [GitHub Actions](https://github.com/occult-kranti/ANDOLAN/actions/workflows/yuga-reference-tracks.yml); inspect that branch's current result. The complete native journey and central public deployment remain separate gates.

GitHub rejected `POST /user/repos` with HTTP403, so this uses the requested branch fallback. Public delivery uses https://occult-kranti.github.io/ANDOLAN/yuga/control-lab/ . Consult the [current deployment evidence](https://github.com/occult-kranti/ANDOLAN/blob/game/yuga-confluence/games/yuga/docs/REFERENCE_LAB_QA.md) for its status and exact verified revision.

Run `npm ci`, then `npm run yuga:lab:dev` or `npm run yuga:lab:build`. Vite consumes this [track.json](track.json) `id` and filters the mode selector through `VITE_YUGA_LAB_TRACK`; `YUGA_LAB_TRACK` optionally overrides it. Other metadata records scope, not executable enforcement. `yuga:lab:e2e` explicitly exercises the shared combined client; the branch workflow separately checks this focused production build. Deployments come from the central branch so these tracks cannot overwrite one another's Pages site.

Compact-layout fixes from `176b6f8e71fcffd3d570d96e66643d8cb9893603` are also merged. The review below was initially written before the foundation merge; its source-reading boundaries and later-scope gates remain applicable. Integration state above supersedes those historical pending-integration notes.

## Current implementation boundary

Reviewed 16 October 2026 against the in-progress shared files `games/yuga/reference/{controller,types,objective,bots}.ts` in the main ANDOLAN worktree. The baseline committed HEAD was `994a3b32b1bd35e1860f37bcc210b491e3afcb0a`; the lab files were still under development, so that commit alone does not reproduce this review. The lead is integrating the foundation under gate C1; final revision, test results and artifact identity remain pending. A subsequent source review confirmed `vite.yuga-lab.config.ts` reads track metadata (or the `YUGA_LAB_TRACK` environment override), and the frontend consumes its `VITE_YUGA_LAB_TRACK` define to select/filter the control edition.

The shared lab uses `ArenaSimulation`, `ArenaWorld`, all fourteen original heroes/42 abilities and the existing fourteen hero plus seven unit GLBs. One local player and five labeled AI participants form two teams of three. The bot policy uses original waypoints, local steering probes, visible targets and ordinary input/commands. It is not an Overwatch bot implementation or evidence of human balance. This track has not run a browser, build, match or new REA analysis.

The shared current control rules are original:

- The central point is at `(0,0)`, radius 8 m. Six uncontested seconds capture; additional teammates do not speed capture.
- Eligible occupants are connected, living heroes with no respawn delay and finite height at most 2 m, within the inclusive radius. Summons/minions do not count. The height threshold approximates low occupancy; it is **not a grounded-contact test** and can include a low airborne hero.
- Contested occupancy freezes capture and scoring. An empty point retains its owner, earns zero score, and decays unfinished capture by one-sixth of its normalized bar per second. An uncontested returning owner immediately clears hostile unfinished capture.
- An owner earns one point per second only while eligible teammates remain present and no opponent contests. The target is 60 points. There is no objective-credit payout and no overtime.
- Ordinary lanes, towers, cores, waves, camps and economy continue. An already-finished arena outcome, including core destruction, takes precedence; otherwise the point target wins, then the 240-second control deadline uses higher point score or a draw. The underlying arena retains its 480-second timer.
- The wrapper adds an original 12-round primary magazine and 1.6-second reload on X. Only confirmed primary shots consume ammo; Q/E/R do not. The updated wrapper debits via an optional synchronous accepted-primary callback emitted when the simulation successfully creates a primary projectile, replacing inference from the bounded shot-event feed. This targets projectile-cap rejection and event-overflow ambiguity; independent tests remain pending. Hero health, speed and kits remain their own authored rules.

These values describe the reviewed implementation; `objective.ts` and `controller.ts` are the authority. A change there requires updating the descriptive record and tests, not adding a second rules engine in `track.json`.

## Source and Overwatch comparison matrix

The evidence baseline is the existing [Overwatch engineering study](../games/yuga/docs/research/OVERWATCH_ENGINEERING.md), plus `games/yuga/docs/research/REFERENCE_IMPLEMENTATION_SOURCES.md`, its provenance JSON and `games/yuga/docs/REFERENCE_GAME_ROADMAP.md` in the integrating branch. Those latter files are pending foundation integration into this worktree. No commercial game source, game assets, binaries or versioned replay/video were available. No inspected source establishes the complete official Control rules; rows below preserve that uncertainty.

| Comparison question | What the pinned source actually establishes | Current original lab and difference/unknown | Next decisive evidence |
| --- | --- | --- | --- |
| How does a round begin and end? | OverPy `examples/skirmish_elim.opy` separates not-started/setup/started and handles late joining; it is the author's humans-versus-bots elimination custom mode. | The local wrapper has playing/finished plus pause and epoch reset. No copied selection countdown, map coordinates, elimination rules or roster. Official Overwatch round lifecycle remains unverified. | Cancel/load/restart/native end-to-end flow and stale-epoch rejection; future versioned official-mode observation separately. |
| How is a point captured or scored? | The OverPy example contains no official Control implementation. Prior Godot community capture logic is another author's prototype, not Overwatch source. | Fixed 6-second capture, owner-present scoring, retained empty ownership, explicit contest freeze, 60-point target. These are original hybrid rules. | Tests around each boundary, then ordinary traversal showing that the rendered point agrees. No parity label without a new official source. |
| What ends a close match? | No inspected source verifies official overtime, round series or tiebreaker rules. | Core/arena outcome first, then point target, then fixed deadline tally/draw. No overtime or best-of-series. | Simultaneous core/point/deadline cases; frozen snapshots after finish; display the actual reason. |
| What counts as point presence? | No inspected source verifies official airborne, disconnected, summon or respawn capture eligibility. | Living connected heroes at height ≤2 m; inclusive radius. Low airborne presence can count. | Exact radius/height boundary fixtures, dead/disconnect/respawn/summon cases, and native jump-through-zone evidence. |
| How do combat and support events differ? | Deltin `EventInfo.cs` has distinct names for elimination, final blow, damage, healing, join and leave. A mapping is not a combat implementation. | Original hero projectiles, committed casts, cooldowns and support rules. Wallet deltas are aggregate observations, not source-attributed event receipts. | Cast-start versus hit/result checks; useful-heal/shield contribution before considering support rewards. |
| Does a reticle mean a hit? | OverPy `crosshair.opy` lays out a HUD glyph and toggles the hero HUD. It supplies no hit authority. | Existing YUGA aim/visible-target logic and authoritative collision remain decisive. | Cover break, closest collision, accepted primary shot versus ammo decrement, and missed shot evidence. |
| How should motion/audio be organized? | Prior OWLib inspection represents skeletal tracks, selected state/layer records and event/action readers. It is not a blend evaluator or audio mix. | Original rigs, animation, effects and synthetic audio with a documented CC0 anatomy foundation. | Run/fire/cast/death rendered sequences; grip/loop/skin checks; original objective cues and muted comprehension. |
| How do roles, weapons and balance compare? | Neither Workshop compilers nor format readers establish current official hero tuning, role limits, weapon constants or matchup balance. | Fourteen YUGA kits, Vanguard/Striker/Keeper labels, original magazine/reload, 3v3 local policy. | Seeded interaction scenarios for each kit; later human tests. No copied hero catalog or tuned-value claims. |
| Is this an online replacement? | Tooling needs the commercial Workshop/runtime or existing files; no inspected project is an independent commercial server. | Local authoritative experiment only. Existing YUGA network code does not make this lab online. | Separate server-owned preset work and two real-client agreement/reconnect tests. |

Pinned references and license decisions:

- [OverPy](https://github.com/Zezombye/overpy/tree/5a7d0e294b8cad73b9701987bb584d0551d7fa4d), GPL v3 root text and inspected explicit v3 headers. This pass reread the complete custom elimination and crosshair examples as text; no compiler or Workshop execution and no source import. The elimination file SHA-256 is `a4e72e1f995c5b0aba6c937f0292ccaa03f60423dec8b1a48d11756172ceec74`; license SHA-256 is `3972dc9744f6499f0f9b2dbf76696f2ae7ad8af9b23dde66d6af86c9dfb36986`, matching the existing provenance record.
- [OWLib](https://github.com/overtools/OWLib/tree/546efa19516d7df7ba138802d221c73ad886df28), MIT tooling. Animation/audio observations reuse the prior documented bounded read; this track did not re-audit the decoder. Its license does not license commercial assets it can read. No extraction.
- [Overwatch Script To Workshop](https://github.com/ItsDeltin/Overwatch-Script-To-Workshop/tree/41b51d6dcd98c7d07e4e8f8646e088e8820ae2bd). This pass reread `Deltinteger/Deltinteger/Decompiler/TextToElement/EventInfo.cs`; the previously inspected MIT license is in the sibling extension, so compiler source reuse remains unapproved in scope. Read-only concepts only.

The existing source audit records REA 6.5.0 analyzing five selected Sketchbook locomotion files: 54 findings, zero parse failures and 2,486 explicit unknowns with partial coverage. Four mocked jump-state cases are separately reported. Those results concern an independent movement example, not Overwatch; they were not rerun here and do not validate this control track. A future REA pass must name a bounded question, selected paths, tool version, input/output hashes and unresolved relationships. More static findings alone cannot close a gameplay gate.

## Ordered implementation priorities and reusable targets

1. **Integrate and verify the foundation (C1–C2).** Systems owns rules; World owns rendering; QA independently checks scenarios; root owns build/site/publication. Freeze a reviewed revision and reconcile this record. Until then, describe behavior as source-reviewed implementation, not a passed playable mode.
2. **Verify objective state communication (C3).** The proposed bounded adapter is now implemented in `reference-client/objective-status.ts` and called by the HUD. Source review confirms pure snapshot-derived `contested`, `capturing`, `scoring`, `absent` and `unclaimed` statuses, with no gameplay mutation. A retained owner with zero occupants reads “Owner absent · No points earned.” The adapter itself has no pause/finish input; the surrounding dialog/result flow must convey those states. Independent QA of status precedence, empty decaying progress and paused/finished presentation remains pending.
3. **Close one complete native loop and art readability (C4–C5).** Reach the zone through normal movement, contest/fire/reload, finish and restart/back. Verify HUD/zone and input neutrality at keyboard/mouse/touch sizes, with fixtures labeled where shortened clocks or actor placement are used. Bot path success is separate evidence.
4. **Adapt one measured improvement to YUGA (C6).** Candidate transfer: explicit objective/finish-reason readout and reusable epoch-safe lifecycle. Record the original problem, source lesson, exact lab scenario, before/after change and affected native/simulation regressions. Do not transfer scoring rules just because the lab resembles a genre reference.

Later optional targets are a purpose-built control map, alternative scoring/overtime experiments, deeper contribution events and online mode. Each needs its own approved contract. They are not prerequisites to falsely claim the initial hybrid replicates official Overwatch Control.

## Prototype verification gaps

This review executed no gameplay tests. These are handoff gates, not reported failures or pass counts; other agents may subsequently close them with exact evidence.

| Gate | Required cases | Why the case matters |
| --- | --- | --- |
| Capture eligibility | radius just inside/on/outside; height 2 m and above; low airborne; dead; disconnected; respawning; summons; nonfinite positions | Avoid visual overlap or “grounded” copy claiming eligibility the authority does not implement. |
| Capture transitions | 5.95 versus 6 seconds; multiple teammates; contested while capturing; empty decay; return by attacker/owner; enemy capture | Prove fixed rate, ownership and progress semantics without assuming reference-game rules. |
| Scoring and ending | owner present/absent; owner plus enemy; target boundary; equal deadline; simultaneous arena result; repeated post-finish step/command | Prove exactly one terminal result and no point/wallet/action advancement after it. |
| Input and reset | stale epoch/sequence; held fire/reload; pause/blur/resume; invalid elapsed time; repeat reset with same seed | Prevent inherited action, reload, capture, receipts or catch-up time in a new run. |
| Combat accounting | missed/blocked accepted primary shot; ability shot during primary cycle; empty magazine; reload complete/death/cast; every hero | The new optional accepted-primary receipt replaces shot-feed inference. Verify that event overflow cannot lose a debit, projectile-cap rejection consumes no ammo, and abilities/minions do not debit a hero magazine; compare observer-enabled and observer-free simulation outcomes. |
| Economy evidence | source award/recipient/duplicate/expiry/reset; wallet conservation; capped balance | Current receipt records are bounded wallet deltas, without source entity IDs. They support delta reconciliation, not a complete reward-attribution ledger. |
| Bots and native flow | multiple fixed seeds and all approaches; actual collision traversal; surviving owner presence; restart/gallery/back; visible zone scale | Waypoints, collision probes and screenshots alone do not prove a playable or comprehensible match. |

## Original art and communication requirements

- Retain YUGA's epic-inspired characters and architecture. No commercial silhouette, costume, logo, map layout, voice, icon or extracted asset. Preserve existing anatomy/source notices in the [reuse ledger](../games/yuga/docs/REUSE_LEDGER.md).
- Draw the objective footprint from the actual radius and center; keep ground visibility under particles, characters and camera motion. Provide a distinct contested pattern and text, with progress and owner status independent of hue.
- Show point score separately from ordinary team score and currency. The four-minute timer and “core destruction can end this mode first” rule need readable prelaunch and result communication.
- Communicate high/low occupancy honestly: “eligible heroes within 8 m and at height ≤2 m” is the engineering contract; friendly copy must not claim a true grounded test until one exists.
- Use original capture/contest/finish cues keyed to accepted state changes, deduplicate them, and preserve mute/reduced-motion settings. Later listening and first-time player observation are still required for quality claims.
- Reuse all 21 existing GLBs with actual loading/disposal and repeated-session checks. Review upper/lower-body motion, grips, telegraph silhouette and zone occlusion in runtime; concept illustrations do not certify runtime art.

## Evidence required to close a gate

Record final source commit, exact mode/seed/hero and actor state, input schedule or labeled fixture, expected/observed outcome, command/test result and output artifact. Distinguish source read, static REA, synthetic simulation, staged native, ordinary native, real-network and public-production evidence. Record a counterexample when it changes the conclusion. Track metadata remains pending until such evidence exists; a generic control point, a green build or a public URL alone is not commercial parity or human balance validation.
