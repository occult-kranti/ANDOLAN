# Ability video study and native presentation review

Task: user video study / W1 presentation evidence. Product: native offline YUGA. Reviewer: `browser_games_research`. Baseline checkout: `work/yuga-studio`, HEAD `7162b5d0b666e4422b0bc73100e1fba947d3323f`; pre-existing uncommitted sources were preserved. Exclusive outputs are this report and [ults evidence](ults/). Root owns implementation and integration.

The supplied `all ults.mp4` demonstrates multiple heroes' ordinary abilities as well as ultimates. Its most useful transferable pattern is a visible sequence of preparation, target selection, active effect and return to ordinary movement, supported by an optional explanatory guide. This is observation of the supplied video, not verification of a current commercial game's roster, balance or release version.

## Input identity and actual visual coverage

The incoming upload had previously been growing. Analysis began only after equal size/mtime checks separated by five seconds and equality of the original-before-copy, frozen-copy and original-after-copy hashes. The incoming file was left untouched. [Intake](ults/intake.json) records the probe and checks.

| Property | Observed value |
| --- | --- |
| Input | `/workspaces/ANDOLAN/all ults.mp4` |
| Frozen analysis input | `/workspaces/scratch/yuga-ults-study-20261115/all-ults-frozen.mp4` |
| SHA-256 | `6ae05fe2bac16862b55fab347f47b8fde2f66dd693bca52695278919da66443c` |
| Bytes | 219,141,934 |
| Container duration | 2,595.874830 seconds / 43:15.875 |
| Video | H.264, 640 × 360, 30 frames/s |
| Full-timeline sampling actually viewed | 87 frames at 00:00, 00:30, …, 43:00, arranged in eight contact sheets |
| Dense sampling actually viewed | 192 half-second frames in nine windows totaling 96 requested seconds, arranged in fifteen sheets |
| Additional full-size inspection | Native-size frames at approximately 17:52.5, 41:25.0, 42:25.0 and final 43:15.0 |
| Limits | No continuous 43-minute viewing, listening, input replay, controller capture or exact simulation-clock measurement |

All 23 contact sheets were opened and visually inspected. The [timeline receipt](ults/timeline.json), [dense windows](ults/dense/windows.json) and [file manifest](ults/review-manifest.json) bind the extracted JPEGs to this input. Dense times are requested source times at 0.5-second spacing; `fps=2` frame selection and rounding mean these are approximate visual event brackets, not frame-exact balance measurements. Edited transitions and repeated examples are explicitly excluded from duration inference.

Representative timeline sheets: [00:00–05:30](ults/contact-01.jpg), [06:00–11:30](ults/contact-02.jpg), [12:00–17:30](ults/contact-03.jpg), [18:00–23:30](ults/contact-04.jpg), [24:00–29:30](ults/contact-05.jpg), [30:00–35:30](ults/contact-06.jpg), [36:00–41:30](ults/contact-07.jpg), [42:00–43:00](ults/contact-08.jpg). Sparse coverage identifies scene families throughout the file; it cannot establish every unsampled action.

## Dense observed sequences

| Demonstration and reviewed windows | Visible sequence | Boundary on the conclusion |
| --- | --- | --- |
| Apollo charged slash, 01:24–01:36 | At 01:24.5 the guide changes to the charged slash. Around 01:25–01:26.5 a red rim/ground glow accompanies a held low sword pose. By 01:27 the actor has moved a long distance and the target carries crossed red strokes. At 01:28–01:31.5 the actor returns to ordinary locomotion/stance. [Sheet 1](ults/dense/apollo-slash/contact-01.jpg), [sheet 2](ults/dense/apollo-slash/contact-02.jpg). | Opening and ending transitions are edited. Pose settling supports an observed visual recovery, not the length of an input lock or invulnerability. |
| Guided Owl, 10:48–11:08 | The first section is a different ability. At 10:53.5–10:54.5 a luminous owl forms at the actor's hands. By 10:55 the camera follows the airborne owl with a green trail; banking and changing street direction remain legible. Around 11:00.5 a green target burst appears and by 11:01.5 the actor camera returns. Another flight example follows. [Preparation](ults/dense/owl-prep/contact-01.jpg), [flight/impact](ults/dense/guided-owl/contact-01.jpg), [second flight](ults/dense/guided-owl/contact-02.jpg). | Camera tracking is visible; the exact steering inputs and server rules are not. An edited second example prevents a continuous cooldown measurement. |
| Heavy Barrage, 17:49–18:09 | A different wall ability ends before 17:52. At 17:52.5 a thin outlined destination circle is visible. From 17:53 repeated teal trails/impact volumes occupy that marked area while the actor advances. By 18:01 the guide fades and ordinary weapon use follows. At 18:06 a subsequent ability shows a translucent ground circle/pin before a green field with plus marks appears at 18:07.5–18:08. [Setup](ults/dense/barrage-prep/contact-01.jpg), [active/end](ults/dense/heavy-barrage/contact-01.jpg), [subsequent ground field](ults/dense/heavy-barrage/contact-02.jpg). | The later green field is a separate demonstration. Its healing interpretation is suggested by plus marks; no health change was measured from these frames. |
| Storm Cloud, 29:46–30:06 | A bright airborne center, radial ground outline and thin branching electricity remain visible through an active channel. Around 29:51.5 the actor settles; at 29:52–29:52.5 a bright vertical effect introduces another airborne channel. The later sequence ends around 29:59.5–30:01 before an edited hero intro. [Repeated example/entry](ults/dense/storm-prep/contact-01.jpg), [active/end](ults/dense/storm-cloud/contact-01.jpg), [return/intro](ults/dense/storm-cloud/contact-02.jpg). | Repeated examples appear within this section. Neither the shown parameter numbers nor elapsed edited footage are adopted as YUGA timings, radius or damage. |
| Telekinesis, 41:24–41:36 | At 41:24.5 the raised hand glows. At 41:25 a ground circle with a vertical destination pin is visible; the target is airborne by 41:25.5 and a purple target burst appears around 41:26. Ordinary gunfire, card symbols and target hit flashes follow. [Lift/destination/burst](ults/dense/telekinesis/contact-01.jpg), [follow-up fire](ults/dense/telekinesis/contact-02.jpg). | The guide text explains a lift/slam, while images support the displacement and destination cue. Later muzzle flashes and damage numbers cannot all be attributed to the initial cast. |
| Shadow Transformation, 42:24–42:36 | An earlier attack ends. At 42:25 a vertical red field and ground ornament surround the actor. Black smoke/silhouette builds through 42:26.5. From 42:27 the silhouette carries a persistent white body mark and attacks resume; by 42:31.5 the blue/gold appearance returns. An edited city outro follows. [Transformation](ults/dense/shadow-transform/contact-01.jpg), [active/return/outro](ults/dense/shadow-transform/contact-02.jpg). | The visible appearance change is established. Immunity, resistances, recharge changes and kill extensions are guide claims; they were not behavior-tested. |

Across the sampled file, a large translucent right-side guide card presents an icon/name, short rule description, parameter groups and three purple upgrade columns. It leaves the demonstration on the left. Whether every guide layer is native UI or an editorial overlay is not established. The pattern is suitable for YUGA's deliberate F3 learning view; keeping that much text on the combat HUD would compete with targets.

World effects and target feedback stay close to the action: ground destination circles, radius outlines, projectile trails, silhouette changes, target outlines, health labels and short hit flashes. Green restoration-like motifs, purple supernatural effects and warm weapon flashes are common, but individual examples vary. YUGA should retain its own semantic palette and provide text/shape alongside color. No commercial artwork, font, icon, audio, map, shader or balance value from this video was inserted into runtime.

## Original YUGA changes and acceptance checklist

These are presentation requirements around the existing offline combat contract, not requests to change native authority, ability tuning or the separate browser server. Root can implement the remaining changes against source-bound tests and actual native captures.

| ID | Original YUGA requirement | Acceptance / counterexample |
| --- | --- | --- |
| V-01 | Keep windup, release, recovery and cooldown understandable in each existing ability slot, with actual remapped binding. | A real accepted cast shows its own phase; blocked/reloading/dead/paused/ended states never claim readiness. Advancing presentation alone cannot release a projectile or advance gameplay. |
| V-02 | Dawn Volley shows three firing lanes as pending/launched marks, never as collectible charges or confirmed hits. | Every mark follows that projectile's authoritative release delay. Cancellation/reset clears stale marks. Missing or stale release receipts cannot light a lane. |
| V-03 | Warning geometry previews the real forthcoming hazard, with a distinct impact/release presentation. | Before release, inspect actual mapped ground corridors/radius. Unlaunched lanes retain warnings until their own authoritative event; warning stroke stays inside the true sweep. A target hull is a separate receiver. |
| V-04 | The F3 guide explains preparation, interruption/counterplay and a useful follow-up using YUGA's own kit text. | All five selections preserve exact rule descriptions and current bindings. Reading or changing selection spends no resource, changes no timer and casts nothing. Overflow is handled by deliberate vertical scrolling/follow focus. |
| V-05 | The combat HUD reserves readable live health, phase/action notice, ammo and cooldowns, with learning details available on demand. | At 960 × 540 and logical 100/150/200% scale, all keys, health and current notice stay visible. No new decorative control captures mouse/keyboard input. Actual rendered screenshots remain necessary beyond structural containment. |
| V-06 | The battle dashboard reads actual Sun/Moon core pressure, army elapsed time and the field-shop wallet. | Compare labels to current reports after damage, pause/reset, income, purchase, death and round end. Do not synthesize score, hero portraits or online player activity. |
| V-07 | The field shop explains location/eligibility/cost and that the battle continues. | Real owner alone approves spending/effect. Failed purchase shows the owner's reason, does not claim success, and refreshes the wallet. Reopen/remap/round reset must preserve truthful keys and epoch/nonce behavior. |
| V-08 | Bottom map, traversal, shop button and ability slots occupy separate readable regions. | At 1180 × 650, 1280 × 720 and compact/high-scale routes, compare global rectangles as well as actual images. No panel overlap may hide the ultimate, health or live warning. |
| V-09 | Keyboard shop open/close/pause restores the intended battle or opener focus without unintended actions. | Test real OS input with remapped keys, held/echo inputs, disabled services, round ending while open, and resize. Closing must not also cast, pause or purchase. Follow-focus must reach the close button when content scrolls. |
| V-10 | Reduced motion/effects retains essential target/warning information. | Review normal and reduced variants from the same actual cast. Reduce flourishes without erasing the pending hazard, current phase or confirmed impact. No rapid screen flash is needed to convey power. |

## Independent review of existing local implementation

The uncommitted `rama_ability_meter.gd`, `rama_hero_hud.gd`, `rama_hero_panel.gd`, `rama_ability_effects.gd` and `rama_motion.gd` were already present and were not edited by this researcher. The last committed change touching the inspected HUD/motion files is `ef5609846d88fae247d220610f6343dee557a0c6`; Git cannot establish the author of later uncommitted edits. Root remains their integration owner. Exact reviewed hashes appear in [execution](ults/native-review/execution.json) and the test report.

Source inspection found the timing strips already read the mounted kit, preserve independent cooldowns, suppress unavailable states and derive volley launch marks from release receipts/generation. The guide already adds original counterplay/follow-up text. A duplicate field-guide implementation was therefore unnecessary. Motion changes reuse the authored ready-draw arm channels during power preparation and blend from the previous pose; this source review does not prove contact, smoothness or human feel.

The existing test was executed independently, with four CPU cores and a fresh data directory:

```sh
XDG_DATA_HOME=/workspaces/scratch/yuga-ults-feedback-review-20261115/user \
  godot --headless --path games/yuga-native \
  --script res://tests/rama_hero_feedback_cases.gd -- \
  --report=/workspaces/scratch/yuga-ults-feedback-review-20261115/feedback.json
```

Result: exit 0, **25/25 checks passed**, elapsed 3.442 seconds; all six externally pinned source files were unchanged before/after. [Actual report](ults/native-review/feedback.json) covers real mounted fixed-tick releases, per-projectile delays, pause/resume, cancellation, reset, empty magazine, defeat, read-only guide and logical slot containment at 100/150/200%. It does not establish rendered readability, actual OS input, motion quality, sound or GPU performance. No additional broad suites or heavy renders were run by this researcher.

Root's new `confluence_battle_hud.gd` and `native_field_shop_panel.gd` were separately parsed with Godot `--headless --check-only --script`; both exited 0 with stable source hashes. [Parse receipt](ults/native-review/parse.json) binds those specific first-review versions. The dashboard's core/time fields match the actual army report, and its wallet/eligibility fields match the owner shop report. The panel delegates purchase/eligibility/effects to `native_field_shop` and labels the live-battle behavior.

Two first-review layout findings were returned to root for correction: (1) the 1180-pixel wide-layout threshold permits bottom traversal/map overlap with the unchanged 820-pixel centered ability HUD, including a small left overlap at 1280; (2) the shop's initially unwrapped heading/subtitle can impose an excessive minimum width on compact/scaled canvases despite horizontal scrolling being disabled. These first-review sources are not accepted as rendered UI. Successor changes require their own contained geometry and native input/image evidence; parse success alone is insufficient. Controls that show bindings only at `_ready` also need a remap/reopen check.

The independent [real-container R1 probe](ults/native-review/layout-r1.json) then confirmed root's first corrections: wide dashboard peers were contained and separate at 1180 × 650 and 1280 × 720; the shop outer panel also fitted 960 physical pixels at 150/200% scaling. It exposed a further counterexample: Close had keyboard focus and `is_visible_in_tree == true` while partially or entirely outside the scroll clip in three of four cases. At 200%, its rectangle was y414–490 while the scroll viewport ended at y324. The retained [R1 runner](ults/native-review/layout-probe-r1.gd) and [execution](ults/native-review/layout-r1-execution.json) preserve that failed state.

Root moved Close into a fixed footer outside the vertically expanding scroller. The independent [R2 probe](ults/native-review/layout-r2.json) observed all eight source hashes unchanged during its 4.375-second run. It checked 1180 × 650, 1280 × 720, 960 physical pixels at150% (853.33 × 480 logical) and200% (640 × 360 logical), then a return to1280 × 720. All five cases had no dashboard peer intersections/outside rectangles; the shop panel and focused Close were contained, with no footer/scroller overlap. Each enabled ward/escort Buy control also scrolled fully into view when focused. This accepts the measured geometry/focus correction only. The [current probe](ults/native-review/layout-probe.gd) performs no purchase and claims no rendered or OS-input review. Root's separate actual-input/render queue remains responsible for appearance and lifecycle acceptance.

## Handoff and remaining work

Changed by this worker: browser source research report/JSON, this video report, extracted source frames/contact sheets and exact receipts. No production source or authority was edited. FuncGodot remains a researched MIT authoring candidate related through Quake tooling; its isolated brush-import spike was deferred when video study became the priority, and no successful map import is claimed.

Root is the next owner for actual native capture/input review and integration, using the [implementation queue](IMPLEMENTATION_ROADMAP.md). Review remaining defects against V-01–V-10, retain failed layouts/captures, and bind successor source hashes. Full-match completeness, full roster/online gameplay, map production, hardware performance and commercial-game equivalence remain outside this bounded study.
