# Original reference lab — QA record

Status: 16 October 2026, **the original lab is delivered: repaired local acceptance, main CI/deployment, exact public HTML and all three public lab browser smokes pass.** Current lab runtime is `176b6f8e71fcffd3d570d96e66643d8cb9893603`. These are original local-bot lane-economy and hybrid control-point experiments; the results establish neither commercial-game parity nor public multiplayer availability.

## Current local acceptance

The [repaired native record](evidence/reference-lab-layout-check.json) pins the committed source, test/source hashes, raw report hash and nine screenshots. All three cases passed without retries or skips, in 211.801 seconds overall. Source hashes still matched after the run. Root and World independently inspected the repaired mobile settings and initial result views; World also checked score separation and keyboard access to both result actions.

| Check | Observed result and scope |
| --- | --- |
| Lab unit suite | **21/21 pass**: eight controller, seven deterministic objective and six primary-receipt cases across three files. The [initial archive](evidence/reference-lab-initial-check.json) preserves exact names and the supplied report hash. Its six internal Vitest suites are not six test files. |
| Controller and economy | Public-API cases cover input/epoch validation, bounded stepping, pause, permitted paused base purchases, ammo/reload, ability exclusion, deduplication/reset, normal bot-match wallet reconciliation, frozen result and lane ending. Wallet receipts are observed net deltas, not individual reward-source attribution. |
| Objective and shot fixtures | Labelled deterministic placements check capture, contest, owner absence/return, decay, finish and snapshot isolation. Eligibility is **y ≤ 2 m**, not grounded-only. Labelled capacity/history fixtures check immutable exact primary-creation receipts, rejected/ability/minion exclusions and correct ammo after visual-event eviction. These are mechanical fixtures, not native traversal evidence. |
| Native desktop | **Pass, 22.651 s**: ordinary lane launch, movement, aim, primary fire/reload, paused forge and fresh restart. No actor, health or clock injection. |
| Native mobile | **Pass, 14.283 s**: touch movement/fire/ability, reachable settings, 320 px lobby reflow and settings bounds without horizontal overflow. Controls can be scrolled into view; this is not every physical device or touch-aim gesture. |
| Normal control match | **Pass, 172.807 s case duration**: actual court traversal, capture/contest/scoring, one local death, Moon 60–Sun 0 at 84.0 game seconds, normal result and replay/fire/ability. Ready-to-result wall time was 164.442 seconds. The 480×400 view and test-only maximum 10 fps RAF budget bound software-render workload; elapsed-work caps can slow game time. No shortened clock or hardware-performance claim. |
| Repaired layout | Actual rectangles show no score/menu overlap at 480×400. Initial result scroll is zero; its focused heading and reason are visible before scrolling, and both actions are reached with native Tab. See [mobile settings](evidence/reference-lab-layout-mobile-settings.png), [initial result](evidence/reference-lab-layout-control-normal-result.png) and [result actions](evidence/reference-lab-layout-control-result-actions.png). |
| Errors and interpretation | All three repaired cases report no page or console errors. Cold-load blur handling remains source-reviewed without a dedicated native delayed-asset blur case. These automated checks do not measure human comprehension, fairness or physical-device performance. |

## Built-client and source evidence

The [initial built production smoke](evidence/reference-lab-built-initial.json) used the combined entry's lane preset, Rama/seed 7301, low quality and a 960×640 view over loopback HTTP. Native launch → two actual engine postrenders → clock advance → pause → resume → return passed. It fetched **13 distinct GLBs** (six participating heroes and seven units); all **21 built model hashes** were separately checked against manifests. Response HTML matched the built file, and page/console/request/HTTP error lists were empty. No development hook, state injection or frame throttle supplied that smoke. Its four screenshot paths/hashes are archived; the coordinator viewed two.

The initial unit/build archive was taken at HEAD `994a3b3` with modified and untracked files, and is explicitly **working-tree evidence**. Its source hashes were taken at archive time, not measured as a clean start/end freeze. Coordinator-supplied initial gates were 350 existing tests, typecheck, lint, main YUGA and all three lab builds. Current remote results below are separate. This documentation pass did not rerun tests, browsers or builds.

## Preserved findings and repairs

The [first native run](evidence/reference-lab-native-check.json), source `27c3d8c`, passed three narrower functional cases in 213.657 seconds. Its screenshots then exposed three real presentation defects: mobile settings clipped Lighting/Preview, short landscape menus overlapped the rival score, and results initially opened scrolled below the heading. Those passing results and eight images remain pre-repair evidence, not final visual acceptance.

World made bounded layout/focus repairs; QA added explicit bounds, overlap, scroll/focus and native-keyboard assertions and reran all three cases on `176b6f8`. The repaired record above supersedes the earlier layout acceptance. The initial unit-fixture invalid-ID correction is retained in QA's attempt history; it did not justify a runtime rule change. No earlier failure or narrower pass is relabelled as the repaired result.

## Remote and public acceptance

| Gate | Current state / required evidence |
| --- | --- |
| Focused lane branch | **Pass:** `ba816a5`, [run 38978062491](https://github.com/occult-kranti/ANDOLAN/actions/runs/38978062491). This is branch CI, not public-route acceptance. |
| Focused control branch | **Pass:** `eee698a`, [run 38978062409](https://github.com/occult-kranti/ANDOLAN/actions/runs/38978062409). Same scope limit. |
| Main CI and deployment | **Pass:** [run 38978033104](https://github.com/occult-kranti/ANDOLAN/actions/runs/38978033104), source `176b6f8e71fcffd3d570d96e66643d8cb9893603`. Coordinator confirms build, remaining/arena/hero-assets regressions, lab-browser and deployment all succeeded. The build includes 371 unit cases and main/all-three-lab production smokes. Browser inventory is 22 existing passes plus three lab passes, with one existing opt-in soak skip; the local `--list` check confirms 23 existing and three lab cases. Remote artifact ZIP inspection remains separately blocked below. |
| Historical canceled run | [38977193630](https://github.com/occult-kranti/ANDOLAN/actions/runs/38977193630) was canceled before deployment for the layout repair. Build and lab-browser passed, existing regressions were incomplete. Earlier focused branch passes `38977320540`/`38977319766` concern pre-repair source. |
| Remote artifact inspection | CI status API worked; downloading the artifact ZIP hit managed-network HTTP 403 on its signed blob URL. Remote ZIP contents were **not inspected** in that attempt. Local built-file checks remain separately evidenced. |
| Public lab verification | **Pass:** [five-document equality check](evidence/reference-lab-public-documents.json) and [three-route native browser record](evidence/reference-lab-public-check.json), exact runtime `176b6f8`, normal TLS. The combined entry used its lane preset; focused lane/control entries each used their declared preset. Details below. |
| Main YUGA public regression | **Pass, separately recorded:** [public game/model smoke](evidence/reference-lab-parent-yuga-public.json) verifies all 21 actual GLB responses, native Rama Practice/Q → leave → Arjuna gallery → close → new Arjuna Practice/Q, and the preserved ANDOLAN root. No development hooks or errors; ordinary sequential UI does not replace the separate synchronous-disposal fixture. |

The [final CI API record](evidence/reference-lab-final-ci.json) confirms all six jobs succeeded. Five public documents returned HTTP 200 and matched exact local SHA-256 values: ANDOLAN, YUGA and the three labs. Each public lab smoke loaded **13 actual GLBs** (six participating heroes plus seven units), separately verified all **21 built model hashes**, waited for two real engine postrenders, and completed native launch → clock advance → pause → resume → back. All error lists were empty. The runs used normal TLS, no development hooks, injected state or frame throttling. They are startup/lifecycle smokes, not public full-match or performance tests.

The public summary links three raw result JSONs and six screenshots; this documentation review independently matched all nine archived file hashes. Root inspected the actual combined and control practice frames for mode/objective/HUD readability. Remote CI artifact ZIP contents remain uninspected; these exact live-document/model checks are separate evidence.

Live entries: [combined lab](https://occult-kranti.github.io/ANDOLAN/yuga/lab/), [lane economy](https://occult-kranti.github.io/ANDOLAN/yuga/lane-lab/), [hybrid control](https://occult-kranti.github.io/ANDOLAN/yuga/control-lab/). The new lab's three-round review is closed for this bounded deliverable.

The source-correlated, exactly-once earnings ledger remains later work in the [reference roadmap](REFERENCE_GAME_ROADMAP.md). The lab has labelled bots and local authority; human balance, WAN quality and an operated public multiplayer service remain outside this acceptance.
