# YUGA: design research for the next iteration

Research date: **16 October 2026 UTC**. The practical scope is optional Practice goals, accurate hero/upgrade explanations and more readable original art. Keep the existing PlayCanvas/TypeScript/WebSocket/Blender stack. Two optional development tools merit small experiments; no new package, plugin, engine or research script was installed or executed in this pass.

This is a bounded reading brief, not a claim to have read every listed book or established a psychological benefit. [The firsthand player sample](research/DEADLOCK_PLAYER_FEEDBACK.md) supplies concrete problems and counterexamples. The sources here add design and engineering rationale. Implementation status belongs in [PLAYER_EXPERIENCE_REVIEW.md](PLAYER_EXPERIENCE_REVIEW.md), [QA.md](QA.md) and the relevant owners' change records.

## What was actually read

All retrievals used ordinary configured HTTPS. Five direct author/publisher requests still returned managed-proxy HTTP 403; their contents were not read. Accessible publisher/author GitHub repositories were read at immutable revisions. These are already-hosted sources, not relays around a blocked site. Files remain outside the product under `/workspace/research/yuga-design-next`; [DESIGN_RESEARCH_SOURCES.json](research/DESIGN_RESEARCH_SOURCES.json) records exact paths, hashes and access outcomes.

| ID | Source, version and precise reading scope | Evidence boundary |
| --- | --- | --- |
| D1 | OpenStax, *Psychology 2e*, [Motivation, module m82225](https://github.com/openstax/osbooks-psychology/blob/de7e40c91813dabdc2875df9d0709fc4f46080bb/modules/m82225/index.cnxml), publisher revision `de7e40c91813dabdc2875df9d0709fc4f46080bb` dated 9 July 2026. Read intrinsic/extrinsic motivation, mixed findings on rewards, the educational-control/belonging paragraph citing Niemiec & Ryan, self-efficacy/social motives and the surrounding cautions. | Direct publisher textbook source; **secondary synthesis of psychology studies**, not an experiment conducted here or direct reading of all cited papers. Root LICENSE and collection metadata specify **CC BY-NC-SA 4.0** at this revision. No text or images are imported into the game. |
| D2 | Robert Nystrom, *Game Programming Patterns*, [Game Loop](https://github.com/munificent/game-programming-patterns/blob/898b1f2e1818c80d7eed5eba98e9903ec13b7771/book/game-loop.markdown), author revision `898b1f2e1818c80d7eed5eba98e9903ec13b7771` dated 10 June 2021. Read “One small step, one giant step”, “Play catch up” and “Stuck in the middle” (source lines 288–493). | Primary author chapter. Separates fixed simulation from variable rendering, bounded catch-up and the risk of guessed display positions. Its prose calls some predicted rendering interpolation while explicitly describing extrapolation; preserve that distinction in YUGA. No numerical tick-rate recommendation is adopted. |
| D3 | Same author/revision, [State](https://github.com/munificent/game-programming-patterns/blob/898b1f2e1818c80d7eed5eba98e9903ec13b7771/book/state.markdown), input/flag failure example and finite-state explanation (30–148), entry/exit actions and limitations (359–423); [Object Pool](https://github.com/munificent/game-programming-patterns/blob/898b1f2e1818c80d7eed5eba98e9903ec13b7771/book/object-pool.markdown), use cases and caveats (94–235). | Author source, selected sections only. [LICENSE](https://github.com/munificent/game-programming-patterns/blob/898b1f2e1818c80d7eed5eba98e9903ec13b7771/LICENSE) distinguishes **CC BY-NC-ND 4.0 prose/site files** from **MIT code files**. No prose, examples or source code are copied into YUGA. |
| D4 | Ian Schreiber, *Game Design Concepts*: Level 7 decisions/flow (20 July 2009), Level 15 blindtesting (17 August 2009), Level 17 user interfaces (24 August 2009), previously read selected sections, with Level 17 input/output, learning/use and feedback sections revisited. [Pinned public mirror](https://github.com/eugenioclrc/gamedesignconcepts/tree/5c98165cb261143bda0147463acbaee922ca46c9). | Author-attributed text through a third-party mirror; canonical host remains inaccessible and its current fidelity/license was not independently verified. Exact prior scope is in [SOURCE_REGISTER.md](../../../docs/library/SOURCE_REGISTER.md). Do not promote this to a newly authenticated primary-host read. |
| D5 | [Deadlock firsthand feedback F1–F7](research/DEADLOCK_PLAYER_FEEDBACK.md), official sample retrieved 16 October 2026: 40 posts, 145 unique comment records, 26 requests. | Purposive qualitative evidence, with positive/mixed cases, unavailable media and uncertain game versions. Counts include non-player/automated material; no prevalence or causal inference. |

## Seven lessons with concrete gates

### 1. Autonomy is a usable choice, not a compulsory checklist

D1 discusses learner control, a reason for the task, respect and doable challenge. D4 distinguishes informed choices from blind or meaningless ones. These support offering a player one small Practice goal they can choose, change or dismiss. They do not establish that a specific UI will increase intrinsic motivation.

**Decision:** “Free practice” remains a complete route. Offer a short goal with its reason and current control; no forced completion before another hero, online invitation or exit. Keep practice separate from account power and match currency. Dismissing help must not lose rewards, trigger a guilt message or reopen the same modal every snapshot.

**Gate:** keyboard and touch users can start freely, select/dismiss a goal and leave immediately. Selecting a different goal clears only that goal's session observation; it does not reset combat or award resources. Owner: client/QA. Proposed behavior must receive its own evidence.

### 2. Record what happened; do not rename an event “mastery”

D1's self-efficacy section describes belief in one's capability, not a property a game can infer from a click. D5/F1 includes a player who knows mechanics but misses cues, and a positive response to small-goal coaching. One successful action cannot establish skill transfer or consistent competence.

**Decision:** label a goal with observable evidence, such as an accepted upgrade or an authoritative hit credited to the local actor. A pressed ability key proves neither acceptance nor impact. No damage received does not prove a dodge: the enemy might never have aimed at the player. A support action should count an actual effective heal/shield if that is what the label promises, not merely an accepted empty-area cast. If such telemetry is unavailable, use an honest narrower goal or leave it instructional.

**Gate:** event identity deduplicates snapshots; only events after goal selection in the current match count; another actor's action, rejected input, reconnect replay and old-match packet cannot complete it. Completion is a finite receipt, not a percentile, rank or psychological judgment. Owner: client/systems/QA.

### 3. Explain the first useful action and its tradeoff

D4's distinction between ease of learning and ease of use argues for concise guidance that experienced players can bypass. D5/F3 shows enjoyment of heroes alongside uncertainty about role and build logic.

**Decision:** the hero guide states positioning, a first action, a real counter/limitation and an upgrade choice. Use current simulation values rather than commercial-game advice. In the inspected YUGA code, Power scales primary base damage by 17% per rank and ability power by 12% where the ability branch consumes that value; Tempo divides primary interval by `1 + 0.12 × rank`; Vitality adds 65 maximum/current health, capped at the new maximum. Therefore “12% shorter interval” is inaccurate, and “Power improves every aspect of every ability” is also inaccurate. Summon lifetime, range, cooldown and control duration must not be implied to increase unless they actually do.

**Gate:** all fourteen guide records match all forty-two authored abilities and their actual branches. The shop shows current cost and concrete resulting effect before purchase; capped/unaffordable/out-of-range actions have accurate feedback. A later participant should explain one tradeoff without coaching. Owner: content/client, independent source review by research.

### 4. Game feel begins with the input/state/feedback contract

D2 explains why simulation cannot depend on visible frame count and why display extrapolation can be wrong. D3 shows how unrelated input flags produce invalid combinations. These are engineering foundations for feel; they do not establish subjective responsiveness or a universal latency target.

**Decision:** keep fixed-step authoritative rules, bounded elapsed-time catch-up and explicit input clearing. Distinguish local intent, accepted action, windup/release and confirmed impact. Hit feedback must not appear merely because the client played a firing animation. Menus, hidden tabs, reconnects and defeat each have defined input cleanup. Do not add an input buffer or prediction layer without deciding whether delayed execution remains desirable after context changes.

**Gate:** delayed callbacks preserve the documented bounded-time policy; no stale fire/cast after a menu, blur or reconnect; animation and audio release agree with authoritative phase/timestamps. Measure native input-to-visible-feedback under stated settings and hardware before claiming the game feels faster. Owner: systems/client/world/audio/QA.

### 5. Readability is recognition at play distance

D4 connects expected interaction to feedback; D5/F4/F7 show ambiguous signifiers and propose motion cues that preserve depth. World's existing-image review identifies weak rear-view distinction, unit images too small/occluded to certify hand contact, and competing labels/markers. These are project-specific observations, not a fresh competitor-video study.

**Decision:** prioritize danger boundary/release, aim and target eligibility, then ally/enemy/neutral identity, then reward decoration. Separate a decorative sign from a pickup/available camp. Test silhouettes from behind as well as from a gallery front view. A stationary turntable or a close-up render is not evidence of a readable team fight. Keep reduced-motion and low-quality danger cues intact; use shape/text as well as hue.

**Gate:** capture the actual priority trio and mixed unit wave at gameplay size, both teams, low/high quality and narrow touch view; verify clear contour/reticle against actual cover. Match each of the 42 ability cues to its current rule, but start with the three timed R abilities before expanding captures. Ask an observer to identify threat/escape direction; automation alone cannot certify comprehension. Owner: world/audio/QA.

### 6. Healthy progression needs stopping points and honest rewards

D1 explicitly presents mixed findings on rewards, including context and differing reinforcement types. It does **not** justify a blanket claim that every reward harms motivation, nor a recommendation to exploit unpredictable rewards. D5/F2 retains both newcomer frustration and a later positive update.

**Decision:** retain match-local credits/upgrades, all heroes available, explicit replay/leave, no paid power, streak loss or forced daily schedule. A Practice receipt acknowledges the selected action without currency pressure. If permanent history is added later, define what it records, storage/migration/reset/failure behavior and cross-device limitations first. Do not label a rolling log as lifetime mastery.

**Gate:** leaving after a goal or match is a normal outcome; no automatic rematch or punishment for absence; progression claims match stored evidence. Human sessions can assess whether help is useful or distracting. No clinical, wellbeing, retention or addiction-prevention effect is claimed. Owner: product/client/QA.

### 7. Optimize the limiting resource, not the tool list

D3 notes that pooling can waste memory and retain references, while effects can have different exhaustion policies from essential entities. YUGA already has a real asset pipeline and technical gates. A new tool should answer a measured bottleneck.

**Decision:** use the present renderer/authority/Blender/Playwright/Vitest pipeline. Retain required threat visuals under effect limits; reduce decorative effects first. For repeated match/preview lifecycles, track retained entities/textures/buffers and verify cleanup before introducing a pool. Pooling everything or hiding live threats would make the wrong tradeoff.

**Gate:** compare identical scenes/build settings before/after, including cold asset load, steady frame cost, repeat-session resources and visible results. A software-render CI pass establishes functionality under that configuration, not consumer GPU capacity.

## Open production tools: verified capability and adoption decision

These are current pinned candidates, not a benchmark-backed claim of being universally “state of the art”. Licenses and the listed source sections were read; no candidate was installed, run or added to the product.

| Tool and inspected revision | Actual capability and limitation | Decision and experiment |
| --- | --- | --- |
| [glTF Transform](https://github.com/donmccurdy/glTF-Transform/tree/8e2a94a2616d293c4b503d0fb6a4b42e6ec7c62f), 16 October 2026; MIT. Read README, LICENSE.md and selected `packages/functions/src/{simplify,texture-compress}.ts`. | Reads/edits/writes glTF; provides pruning, deduplication, resampling, texture transforms and compression workflows. The inspected simplifier passes indices and **POSITION** to meshoptimizer and then compacts attributes; it does not evaluate animated deformation, face/hand importance or grip quality. Texture conversion has encoder/extension requirements; compression is not automatically a GPU-memory improvement. | **Candidate offline experiment only.** Work on one copied unit/hero, preserve originals and compare bytes, triangle/material counts, all skins/clips/contact poses and actual PlayCanvas root/nested load. Begin with inspect/deduplicate/resample rather than a blind all-roster optimize command. New decoder requirements need explicit loader/build validation. |
| [meshoptimizer](https://github.com/zeux/meshoptimizer/tree/f0a684f11ead064e176775c9b796f82a55910e92), 14 October 2026; MIT. Read LICENSE.md and README “Basic simplification”/“Attribute-aware simplification”. | Simplifies with an error bound, may stop before the requested triangle ratio, and offers attribute-aware variants. Rest-geometry error is not a bound on final skinned motion. Attribute-aware support in this library does not imply the inspected glTF wrapper invokes it. | **Do not add separately now.** Consider through the offline experiment only if actual size/render cost justifies it. Retain deformation and silhouette gates; no promised reduction percentage. |
| [Spector.js](https://github.com/BabylonJS/Spector.js/tree/970aa97e616c4dbe309ddcecd28438961dc80a93), 12 October 2026; MIT. Read LICENSE.txt, README summary/basic capture/custom-data sections and `src/spector.ts` capture methods (309–400). | Engine-independent WebGL/WebGL2 frame commands/state capture; source supports one-frame or bounded-command capture. Can inspect draw calls, buffers/textures and named objects. This is not a commercial-game extractor, WebGPU audit or proof of GPU timing. Instrumentation has overhead. | **Candidate development-only diagnosis.** Capture one representative dense fight if existing metrics cannot locate cost, then remove instrumentation for performance measurements. No persistent browser extension, MCP integration or production diagnostic hook is required. |

An engine/transport migration, new physics dependency, AI behavior framework or generative-3D weight download has no demonstrated benefit for the current practice/clarity task. New rendering technology cannot repair a misleading upgrade description or a goal that completes on a rejected input.

## Book/paper queue and unavailable reading

Nystrom's selected chapters above were actually read. The existing [curated bibliography](../../../docs/library/BOOKS.md) remains a bibliography, not a completed reading claim. Highest-value next lawful readings are Steve Swink, *Game Feel* (2008), for response/perception; Tracy Fullerton, *Game Design Workshop*, for unaided playtesting; and Jesse Schell, *The Art of Game Design*, for experience-focused iteration. No full book was downloaded or read in this pass.

The following exact requests returned proxy 403 on 16 October 2026 and remain **unread here**:

- Ryan, Rigby & Przybylski (2006), [*The Motivational Pull of Video Games* author-hosted PDF](https://selfdeterminationtheory.org/SDT/documents/2006_RyanRigbyPrzybylski_MandE.pdf), DOI `10.1007/s11031-006-9051-8`.
- Ryan & Deci (2000), [self-determination theory paper](https://selfdeterminationtheory.org/SDT/documents/2000_RyanDeci_SDT.pdf).
- Steve Swink, [“Game Feel: The Secret Ingredient”](https://www.gamedeveloper.com/design/game-feel-the-secret-ingredient).
- Riot Games, [“Clarity in League”](https://www.leagueoflegends.com/en-us/news/dev/clarity-in-league/).
- Hunicke, LeBlanc & Zubek, [MDA paper](https://users.cs.northwestern.edu/~hunicke/MDA.pdf).

Autonomy, competence and relatedness are used as a design vocabulary. The accessible OpenStax synthesis supports a bounded rationale for choice, achievable challenge and respectful cooperation; this is not direct verification of the inaccessible SDT papers, a clinical recommendation or proof of causal effects in YUGA. Complete the small original implementation, inspect its technical behavior, then observe players before expanding the roadmap.
