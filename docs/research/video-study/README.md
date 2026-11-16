# Video-informed native game continuation

**Delivered checkpoint:** [downloads, exact source and accepted/remaining scope](DELIVERY.md).

Task `VIDEO-NATIVE-01`, YUGA native. Baseline commit
`7162b5d0b666e4422b0bc73100e1fba947d3323f`, branch `work/yuga-studio`.
The supplied originals and pre-existing studio/other-worker changes are preserved.

The panel studied both uploaded videos, audited the two browser-game catalogs,
and implemented an original local earn/spend/result continuation. Current
native product scope remains one playable Rama in offline Confluence/training.
The [story, modes and production plan](../../../games/yuga-native/docs/STUDIO_PRODUCTION_PLAN.md)
and [video-derived implementation roadmap](IMPLEMENTATION_ROADMAP.md) describe
what follows. Full roster, native online matches, accepted commercial art/motion,
human balance and physical-GPU performance remain open.

| Work | Inspectable result |
| --- | --- |
| Gameplay evidence | [135 actual timeline/dense stills](gameplay-study.md); compact HUD, central action-block states and victory→summary→analytics observations. No opened shop/death UI was observed. |
| Ability evidence | [87 timeline +192 dense frames and final frame](ult-study.md); preparation/release/recovery, guides, destination warnings and camera behavior. The file contains all-ability examples, not only ultimates. |
| Panel research round 1 | [Blog](../browser-library-panel/play-in-browser.md), [INXANITY](../browser-library-panel/inxanity-labs.md), [actual tool/source access](../browser-library-panel/access-and-build.md). Public catalogs are discovery sources; each code/data license is reviewed separately. |
| Implementation | Native core/elapsed dashboard, F4 live field shop, four original services, separate earned/spent wallet, real purchase receipts, bounded per-round metrics and an original result/core-health chart. |
| Panel round 2 / repairs | [Independent integration QA](integration-qa/README.md): mounted siege/purchase/result counterexamples, remapping/focus/pause and related regression suites. Failed layouts, clipped Close, stale focus scroll and their successors are retained. |
| Complete objective reachability | [Normal-wave automated round](round-journey/README.md): real valid ability damage and lane arrivals reach a Sun outcome. Scripted hero origins do not establish ordinary human navigation or multiplayer. |
| Actual input and footage | [First exported checkpoint review](native-input-r1/review.json), [dashboard](native-input-r1/dashboard.png), [shop](native-input-r1/shop-purchases.png), [advancing native screen recording](native-input-r1/actual-native-input.mp4). These are source-bound revision9 evidence, not acceptance of later map/scroll changes. |
| Open-source code reused | [MIT Blender inspector](../browser-library-panel/blender-inspector.md): adapted transformed bounds/camera headings, full notice, original validation/census/receipts, three actual original-asset stills. |
| AI target | [Four-panel target board](../../concepts/video-target-2026-11-16/README.md); explicitly an art-direction concept, not an implemented build. |

`native_field_shop.gd` owns local spending and typed effect admissions. It does
not edit army earnings. Current original tuning is allowance120, heal35,
arrows15, shield40 and temporary escort90; these are hypotheses for playtesting.
Pause, death, end, distance/height, stale epochs, reused nonces, reentrancy,
no-benefit receivers and blocked placement are challenged. The host stops input
while shopping, while battle/vitals continue. The siege receiver was corrected
so inactive shopping input does not grant damage immunity. Death/respawn,
focus loss and reset retire/restore input consistently.

`combat_match_metrics.gd` only observes the real army and effective damage
receipts. It preserves match totals across a kit reset, clears on army reset,
bounds the core timeline and freezes the terminal report. Result text does not
invent teammates, ranks, account progress, damage or online service status.
The pause reading-position fix keeps both the outcome heading and focused
Restart visible after earlier modal/slider navigation.

A separate worker's concurrent original Sangam district/content10 integration
arrived during this task. Its sources were preserved. Shared-tree package
attempts rejected a temporary9/10 mismatch and a source change during export;
those failed logs remain under `/workspaces/scratch/yuga-video-build-r1/`.
A stable map check then identified stale shader/authoring provenance. The
original district was regenerated with Blender inside the isolated snapshot;
its generated specification and two new content10 pins were updated together.
Shared worker files were left intact. The [frozen-build receipts](frozen-build/)
own subsequent exact combined source, checks and artifacts. Earlier revision9 inputs keep their own identity.

Audio was not reviewed. Both source videos were sampled across their complete
timelines and selected sequences examined densely; no continuous full viewing
or transcript is claimed. Software-rendered captures are not hardware FPS
measurements. One ObjectDB exit warning in a navigation suite is retained in QA.
