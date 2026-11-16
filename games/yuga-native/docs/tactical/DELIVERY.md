# YUGA · Sanctum delivery

Task **YUGA-TACTICAL-CASUAL-13**, product **YUGA native desktop**. The current
continuation prepares the original first-person tactical Casual source checkpoint
for publication and updates the production dashboard. Casual is local: one human
and nine bots, two teams of five, first to 13 wins, with sides switching after
round 12. Ranked remains visibly planned and unavailable.

Review date: 15 November 2026 (America/New_York).

Source base is `7162b5d0b666e4422b0bc73100e1fba947d3323f` on
`work/yuga-studio`, plus the preserved studio, Rama/Sangam and tactical changes.
The [publication evidence](evidence/publication-r1/README.md) records exact
commands, file identities and remaining delivery gates. **Final source push,
dashboard deployment, ordinary-input review and current tactical
packages are pending at this draft.** Earlier published executables retain their
own source identities; the older studio/video-panel ZIPs are not Sanctum builds.

Run the source with the installed Godot 4.6.3 runtime:

```sh
godot --path games/yuga-native
```

Choose **Play Casual → Deploy as Rama**. During the 20-second buy phase, press
**B** at spawn to purchase equipment. Use **WASD**, mouse aim, **LMB** to fire,
**RMB** to aim down sights, **R** to reload, and **Q/E/C/X** for the tactical kit.
Hold **F** at a sanctum to attune the Astra, or at an armed Astra to sever it.
Movement, firing and reload interrupt the hold. **Tab** shows the scoreboard;
**F1** opens the guide and **Esc** pauses. The [player guide](README.md) and
[shared contract](CONTRACT.md) specify current controls, economy and round rules.

The checkpoint contains original ARKA and SURYA firearm geometry, first-person
arms, ADS/reload/recoil, Solar veil, Measured step, physical Ward wall and an
earned Dawn volley. Sangam Crossing combines two sites and physical cover with
the project's original sandstone, limestone, indigo and brass architecture.
Native screens cover menu, Casual briefing, Rama kit, settings/help/loading,
HUD, shop, scoreboard, pause and round/match results. Thirteen original
synthesized cues accompany the implementation; listening acceptance remains open.
The generated menu portrait is decorative 2D artwork, separate from actual
native gameplay and future production hero-model work.

| Executed scope | Result and evidence |
| --- | --- |
| Current round authority | [53 checks passed](evidence/publication-r1/round_rules.json), covering phases, holds, economy, one-life rules, side swap and adverse timing/state cases. |
| Current bot behavior | [21 checks passed](evidence/publication-r1/bot.json) against a disclosed synthetic movement/visibility host. |
| Current native UI | [37 checks passed](evidence/publication-r1/ci-integration/tactical-ui.json), including actual settings, loading/cancellation, shop receipts, outcome views and compact/scaled layout. The earlier 36-check receipt is retained separately. |
| Current physical map | [335 checks passed](evidence/publication-r1/map.json), including collision, routes, sites, barriers and source associations. |
| Current integrated world | [27 assertions passed cleanly with the normal clock](evidence/publication-r1/world-realtime.txt). The accelerated fixed-FPS attempt retained audio objects at exit; its [stdout](evidence/publication-r1/world.txt) and [verbose diagnostic](evidence/publication-r1/world-verbose.txt) remain a known harness limitation. |
| Classic native screens | Three focused suites passed: [end-to-end 25](evidence/publication-r1/ci-integration/ui_end_to_end.json), [loading readiness 18](evidence/publication-r1/ci-integration/ui_s3_loading_readiness.json), and [transition lifecycle 20](evidence/publication-r1/ci-integration/ui_transition_lifecycle.json). Tactical and classic entry points retain separate expectations. |
| Classic native contract pins | [83 consistency checks passed](evidence/publication-r1/contracts.json). These retained profiles do not establish tactical online authority. |
| Source snapshot tooling | [22 checks passed](evidence/publication-r1/snapshot-tests.json). This verifies the tool's source-boundary behavior, not a new exported executable. |
| Current actual-scene match | [Six observational checks passed](evidence/publication-r1/full_match.json): the fixed-seed accelerated local run completed 24 rounds, Moon 13–Sun 11, eight plants, one defuse, 153 eliminations and one side swap without reported engine warnings/errors. This is automated scene evidence, not human balance acceptance. |
| Current native visuals | [19 Forward+ captures](evidence/publication-r1/visual-r2/review.json) show real screens and geometry on llvmpipe, with no source drift during capture. Root inspected the home menu, A approach, Ward/veil and equipment shop originals. Objective/result states were staged for art inspection; ordinary input and final art acceptance remain separate. |

The earlier [13–0 match](combat/full-match-r1.json),
[18-shot capture](evidence/visual-r1/review.json), 36-check UI run and failed
accelerated-world cleanup retain their exact original scope. A scene-init failure
recorded while a helper was being edited was resolved by that helper's owner;
it is not presented as a separate root runtime repair. Passing the normal-clock
world run does not erase the accelerated harness's audio-exit diagnostic.

Changed-source groups are `scripts/tactical_*.gd`, the two tactical scenes,
`assets/tactical/`, tactical shaders/tests, `project.godot`, the tactical notices
and the source/publishing documentation. The broader commit also preserves the
separately documented [studio](../../../../docs/research/STUDIO_DELIVERY.md),
[Rama/Sangam](../research/hero-six-rounds/README.md) and
[video-panel](../../../../docs/research/video-study/DELIVERY.md) continuation.
Their historical tests and artifact manifests retain their original scope.

Original native evidence, meaningful failed runs, editable authoring sources and
notices are retained. Supplied commercial-reference videos, bulk extracted
reference images/audio/transcripts, capture caches and user state stay local;
their analytical reports, source hashes and receipts remain available in the
source checkpoint. Those local-only bytes are not backed up by the source push.
Reference material is not a runtime asset or a grant to redistribute commercial
game content. See [art/audio notices](../../NOTICE/TACTICAL-ART.md) and
[map reuse notices](../../NOTICE/TACTICAL-MAP.md).

The [art-first roadmap](ROADMAP.md) owns the next implementation order. Remaining
work includes coherent weapon/hand/contact and effect-motion review, representative
map-encounter polish, human play/balance and audio review, Windows execution and
physical-GPU qualification. Online Casual, Ranked, a finished multi-hero roster
and commercial art acceptance remain future gates. Historical campaign counts
remain **17/78 accepted scoped packets and 0/13 complete production rounds**;
that 13-round campaign is separate from Casual's first-to-13 match rule.

Next owner: root/release closes the pending source-bound
ordinary-input/package and public-byte checks; hero/world/UI owners continue one
observed visual correction at a time after that delivery receipt is finalized.
