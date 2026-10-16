# Overwatch tooling: source study and original YUGA engineering lessons

Research date: 16 October 2026 UTC. Three public repositories were inspected at immutable commits. They provide asset-format readers and independent Workshop language implementations. **None of the inspected projects is the complete Overwatch engine, authoritative multiplayer service or an independent playable replacement.**

This pass downloaded selected source text through the normal managed network connection. No reference program was installed, built or run; no Overwatch executable, replay, model, texture, sound recording or animation was supplied, downloaded or extracted. No commercial match/video was observed in this pass. The findings below describe inspected source, not verified current Overwatch behavior. No reference code, asset, constants or new runtime dependency was added to YUGA.

## Sources, pins and reuse boundaries

| Project and exact revision | License actually inspected | Capability supported by the inspected files | Reuse decision |
| --- | --- | --- | --- |
| [OverTools / OWLib](https://github.com/overtools/OWLib/tree/546efa19516d7df7ba138802d221c73ad886df28), `546efa19516d7df7ba138802d221c73ad886df28` | Root [LICENSE](https://github.com/overtools/OWLib/blob/546efa19516d7df7ba138802d221c73ad886df28/LICENSE): MIT, copyright 2016–2024 overtools | DataTool file inspection/extraction CLI; Tank animation-track decoder/exporter; generated animation configuration records; selected Wwise bank event/action readers. README requires an installed Overwatch game and separately identifies Blizzard's rights. | Read as a format/architecture reference. MIT for the tool does not license commercial files the tool can read. No extraction or copied implementation. |
| [OverPy](https://github.com/Zezombye/overpy/tree/5a7d0e294b8cad73b9701987bb584d0551d7fa4d), `5a7d0e294b8cad73b9701987bb584d0551d7fa4d` | Root [LICENSE](https://github.com/Zezombye/overpy/blob/5a7d0e294b8cad73b9701987bb584d0551d7fa4d/LICENSE): GPL v3. Inspected compiler file headers explicitly specify version 3, without an “or later” clause. `package.json` has no license field. | Python-like custom-rule compiler/decompiler targeting Overwatch Workshop, plus examples, event-context fixtures and compiler checks. It needs Workshop as the execution environment. | Study concepts and test cases; do not silently copy GPL implementation into the product. Images of game abilities in the repository tree were not fetched or treated as licensed game art. |
| [ItsDeltin / Overwatch Script To Workshop](https://github.com/ItsDeltin/Overwatch-Script-To-Workshop/tree/41b51d6dcd98c7d07e4e8f8646e088e8820ae2bd), `41b51d6dcd98c7d07e4e8f8646e088e8820ae2bd` | MIT-form text, copyright 2026 ItsDeltin, at [`overwatch-script-to-workshop/LICENSE`](https://github.com/ItsDeltin/Overwatch-Script-To-Workshop/blob/41b51d6dcd98c7d07e4e8f8646e088e8820ae2bd/overwatch-script-to-workshop/LICENSE). The recursive tree showed no root license; the inspected extension package has no license field. | Independent script-to-Workshop compiler/tooling, event-name mapping and semantic regression tests in the sibling `Deltinteger` directory. | The nested extension license is not enough to assert that every sibling compiler file has a verified reuse grant. Read-only research; resolve scope before any source import. |

Repository HEAD dates were 11 October, 6 October and 5 September 2026 respectively. Those dates identify the retrieved revisions; they do not establish support for every live game patch. Repository README setup commands and external links were reference material, not instructions adopted for this environment.

## What the source actually establishes

### Animation: inspect channels and transitions, not just clip names

OWLib's [`TankLib/teAnimation.cs`](https://github.com/overtools/OWLib/blob/546efa19516d7df7ba138802d221c73ad886df28/TankLib/teAnimation.cs) defines duration, FPS, bone identifiers, per-bone position/rotation/scale index tables and dictionaries keyed by frame. Its constructor reads those streams independently. The first 220 lines were read, including the header and decoding loop; the rest of the decoder was fetched but was not fully reviewed. [`OverwatchAnimationClip.cs`](https://github.com/overtools/OWLib/blob/546efa19516d7df7ba138802d221c73ad886df28/TankLib/ExportFormats/OverwatchAnimationClip.cs), read in full, writes only the present track types with their frames and component counts.

This is concrete evidence of an implemented skeletal-track reader/exporter. It is not a recovered animation scheduler. The source itself labels header group/priority interpretations uncertain, leaves unknown fields and marks a scale-compression variant as unimplemented.

Generated [`STUAnimNode_LayerOverride`](https://github.com/overtools/OWLib/blob/546efa19516d7df7ba138802d221c73ad886df28/TankLib/STU/Types/STUAnimNode_LayerOverride.cs), [`STUAnimNode_StateMachine`](https://github.com/overtools/OWLib/blob/546efa19516d7df7ba138802d221c73ad886df28/TankLib/STU/Types/STUAnimNode_StateMachine.cs) and [`STUAnimNode_ToTargetDirectionIK`](https://github.com/overtools/OWLib/blob/546efa19516d7df7ba138802d221c73ad886df28/TankLib/STU/Types/STUAnimNode_ToTargetDirectionIK.cs) records contain bone-weight, child-node and driver references, with many hash-named fields. These support the narrower observation that the tool represents layered/state/IK configuration. They supply no inspected blend evaluator, IK solver, aim-assist algorithm, transition constants or proof of current game usage.

**YUGA application:** preserve independent locomotion and upper-body action layers, but prove them against our own rig. Run-plus-fire should retain advancing legs, a stable held weapon and coherent hands. A named clip is insufficient: sample weighted vertex positions and real exported transitions, inspect grip contact and check finite bounds, loop seams and zero root motion. These measures already exist in the original hero/unit pipeline; this later research supports continued checks and does not claim to have caused that implementation.

### Aim and telegraphs: readable UI does not establish hit authority

OverPy's [`examples/crosshair.opy`](https://github.com/Zezombye/overpy/blob/5a7d0e294b8cad73b9701987bb584d0551d7fa4d/examples/crosshair.opy) creates a text-based HUD crosshair and toggles the hero HUD through per-player button conditions. It demonstrates a custom presentation rule, not aim accuracy, acquisition rules or a reconstructed targeting system. Its line-spacing/glyph placement is not a suitable responsive browser layout to copy.

[`examples/inputhud.opy`](https://github.com/Zezombye/overpy/blob/5a7d0e294b8cad73b9701987bb584d0551d7fa4d/examples/inputhud.opy) infers keyboard/controller use from localized button-label characters and acknowledges unbound-key limitations. That is a useful counterexample: browser control labels should follow actual bindings and input events rather than infer a device from translated text.

[`src/compiler/functions/createEffect.ts`](https://github.com/Zezombye/overpy/blob/5a7d0e294b8cad73b9701987bb584d0551d7fa4d/src/compiler/functions/createEffect.ts) validates effect identifiers and required extensions. It does not reveal commercial telegraph timing or provide a telegraph renderer. No inspected source establishes Overwatch windup values, network compensation, aim smoothing or accessibility effectiveness.

**YUGA application:** a target ring must mean an eligible, currently visible target; release it when cover/range/life eligibility changes. Use the server's accepted cast target and `releaseAt` to communicate committed attacks. Keep presentation separate from authoritative damage. Test the accepted aim, cover break, button chords, cast commitment and dodge outcome with ordinary input, then compare timestamps. Existing original casts and target lock remain their own design, not recovered Overwatch rules. Color, silhouette and concise text should reinforce one another; no player accessibility study was performed here.

### Audio: event containers are a useful boundary, not a finished mix

OWLib's [`BankObjectEvent.cs`](https://github.com/overtools/OWLib/blob/546efa19516d7df7ba138802d221c73ad886df28/DataTool/ConvertLogic/WEM/BankObjectEvent.cs) reads a list of action IDs. [`BankObjectEventAction.cs`](https://github.com/overtools/OWLib/blob/546efa19516d7df7ba138802d221c73ad886df28/DataTool/ConvertLogic/WEM/BankObjectEventAction.cs) represents scope, action type, referenced object and optional parameters; types include play/stop/pause/resume and volume/filter changes. A comment explicitly questions one parameter interpretation. [`teEffectComponentSound.cs`](https://github.com/overtools/OWLib/blob/546efa19516d7df7ba138802d221c73ad886df28/TankLib/Chunks/teEffectComponentSound.cs) links an effect chunk to a sound resource. These are read/representation code, not an audio mixer or a description of current competitive sound balance.

[`STUSoundImportanceFactor.cs`](https://github.com/overtools/OWLib/blob/546efa19516d7df7ba138802d221c73ad886df28/TankLib/STU/Types/STUSoundImportanceFactor.cs) has a named weight and another unnamed float. It is not enough to infer prioritization policy or reproduce shipped loudness. No sound banks were opened and no reference recordings were heard.

**YUGA application:** synthesize original cues from accepted event IDs; keep reward, attack and urgent local-danger semantics distinct. Coalesce a camp clear and its simultaneous buff, bound routine-fire repetition and total voices, and preserve explicit preview/mute/hidden-tab lifecycle. Current YUGA already does this with a 20-source cap and event deduplication. Native analyser RMS can prove synthesis and attenuation; it cannot prove pleasant timbre, intelligibility in a crowded fight or hardware output. Human listening across speakers/headphones and muted-play comprehension remain separate acceptance work.

### Competitive flow: model states, event context and cancellation explicitly

OverPy's [`examples/skirmish_elim.opy`](https://github.com/Zezombye/overpy/blob/5a7d0e294b8cad73b9701987bb584d0551d7fa4d/examples/skirmish_elim.opy), read through its final victory rule, separates not-started, setup and started states. It has a hero-selection countdown, distinct HUD messages, join-during-round handling and round outcome rules. It is one author's humans-versus-bots custom mode, not evidence of Overwatch matchmaking, ranked scoring or official competitive round behavior. Its settings, map coordinates, timings and hero names were not adopted.

Deltin's [`RuleTest.cs`](https://github.com/ItsDeltin/Overwatch-Script-To-Workshop/blob/41b51d6dcd98c7d07e4e8f8646e088e8820ae2bd/Deltinteger/Deltinteger.Tests/LanguageTests/RuleTest.cs) rejects unsuitable condition values. [`RestrictedCallTest.cs`](https://github.com/ItsDeltin/Overwatch-Script-To-Workshop/blob/41b51d6dcd98c7d07e4e8f8646e088e8820ae2bd/Deltinteger/Deltinteger.Tests/Semantics/RestrictedCallTest.cs) distinguishes conditions from operations that produce actions, and tests event/player values in inappropriate contexts. Its decompiler [`EventInfo.cs`](https://github.com/ItsDeltin/Overwatch-Script-To-Workshop/blob/41b51d6dcd98c7d07e4e8f8646e088e8820ae2bd/Deltinteger/Deltinteger/Decompiler/TextToElement/EventInfo.cs) separately maps elimination, final blow, damage, healing, join and leave events. These source-level tests were read, not executed.

OverPy's [`eventVars.opy`](https://github.com/Zezombye/overpy/blob/5a7d0e294b8cad73b9701987bb584d0551d7fa4d/src/tests/eventVars.opy) and its expected output provide another event-context fixture. Its [`wait.ts`](https://github.com/Zezombye/overpy/blob/5a7d0e294b8cad73b9701987bb584d0551d7fa4d/src/compiler/functions/wait.ts) handles wait-expression optimization and marks waiting subroutines; its engine-timing comments were not independently verified. We should not transfer those timing assumptions into the browser simulator.

**YUGA application:** keep lobby/loading/playing/ended/reconnecting transitions explicit; cancel stale loads and held input when a flow ends. Distinguish attacker, credited hero, victim and neutral entity instead of assuming every actor is a selectable hero. Reward receipts must be authoritative and deduplicated; current wallet changes alone are not proof of a new reward. Make late join/resume and match-finished behavior executable tests, not incidental UI behavior.

## Bounded follow-up gates

These are original YUGA checks, not claims about commercial game internals. Existing implementations and their results remain documented in the owners' evidence files; this source study does not rerun or certify them.

| Area | Useful acceptance question | Evidence needed |
| --- | --- | --- |
| Motion | Can a unit run, fire repeatedly and die without a frozen lower body, detached grip or runaway transform? | Actual GLB skin/transition samples plus native rendered sequences; distinguish body bounds from weapon/costume clipping. |
| Aim and cast | Does a lock disappear behind cover, and does a committed attack keep the accepted target until release? | Simulation interaction tests and real keyboard/mouse/touch input traces. A screenshot of a ring alone is insufficient. |
| Warning readability | Can an opponent identify the danger area and leave before the accepted release? | Authoritative timestamps, ordinary-input dodge cases, then player observation; no inferred commercial windup constants. |
| Sound | Is an earned camp reward audible once without obscuring nearby danger, and can settings preview preserve mute? | Earned authoritative events, bounded source/lifecycle tests and native signal measurements; later listening is required for mix quality. |
| Flow | Does cancelling asset loading prevent a late match, and does reconnect avoid duplicate actions/rewards? | Async cancellation and real socket tests with explicit state/command identity. |
| Competition | Do wins come from understandable objectives rather than ambiguous HUD rewards? | Finished matches with authoritative finish reasons and contribution receipts; bot matrices remain bounded policy evidence, not human balance proof. |

## Retrieval and reproducibility

The three repositories were shallow, filtered, no-checkout clones under `/workspace/tooling/overwatch-research/`. Immutable `git show COMMIT:path` reads produced 27 selected files (180,329 bytes), with a local SHA-256 ledger at `/workspace/tooling/overwatch-research/evidence/ledger.json`. This ledger is cloud-workspace evidence, not a required game asset or a portable product dependency. The pinned GitHub links above allow independent retrieval. No whole-repository audit is implied: large README/package files were read in selected sections, while the small cited implementation/example/test files were read in full except for the explicitly bounded decoder read.

License-file SHA-256 checks:

- OWLib `LICENSE`: `c9d3f0ec202d809a28ab5ec728ac23cbc7b1015566ee5cd017ed84b2b8781bff`.
- OverPy `LICENSE`: `3972dc9744f6499f0f9b2dbf76696f2ae7ad8af9b23dde66d6af86c9dfb36986`.
- OSTW extension `LICENSE`: `98d77e9658bad7a876d3b8d9a978d35a626233033f74c99bf14f3ead789e5f7a`.

The study adds this document only. It does not change the frozen game, add a commercial-game dependency, establish permission for external game assets, or claim that REA reconstructed an engine. The separate [YUGA reuse ledger](../REUSE_LEDGER.md), [audio design](../AUDIO_DESIGN.md), [unit asset record](../../art/UNIT_ASSET_BUILD.md) and [QA record](../QA.md) describe the actual implementation and verification work.
