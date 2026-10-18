# Desktop continuation — final integration review

18 October 2026. This six-owner pass delivers source `79e5c15d8a3657e16fda67acb277b2406120dcd1` with accepted screen behavior, smaller idle presentation and measured map/unit resource reuse. It closes **D09-W2 and D09-W4: 16/78 accepted scoped packets, 0/13 complete rounds**. The requested ten screen rounds plus three integration rounds remain the active plan. Commercial graphics, native online, full roster, Windows execution and physical-GPU/human-feel gates remain open.

## Accepted implementation

| Change | Evidence and result |
| --- | --- |
| Shared modal focus reveal | [W2 source](W2-screens-r1/receipt.json), [actual resize review](W1-actual-r1/ui-focus-r1/receipt.json). Missing/hidden/disabled/freed owners, replacement, manual scroll and Escape tested; 23/23 native cases. Capture and selected guide row remain visible at 200%. |
| Contextual idle traversal HUD | [Source](W2-idle-hud-r1/receipt.json), [actual comparison](W1-actual-r1/idle-hud-r1/receipt.json). 232×171→232×88 logical pixels, unchanged text sizes; 18/18 cases. Active flight/tether/cooldown/drill and important feedback retain their branches. |
| Landmark geometry sharing | [Source](W4-world-r1/receipt.json), [actual comparison](W1-actual-r1/world-landmarks-r1/receipt.json). 238 distinct primitive resources→13, 23/23 cases, matched pixels identical. Mesh instances, draw count, private materials and collision remain distinct. |
| Army geometry sharing | [Source](W4-army-resources-r1/receipt.json), [actual comparison](W1-actual-r1/army-resources-r1/receipt.json). Initial 30-unit bars/bows: 102 resources→4, 21/21 cases including wave/reset/isolation. Matched pixels identical. No draw-call/FPS claim. |
| Content revision 8 | [Repair](W4-content8-r1/receipt.json), [independent review](W6-integration-r1/content8-source-review.json). Exact revision-7 fixtures retained; only army/minion pins and intentional revision/digest change. Source 58/58, native 279/279, package 21/21. Old/forged identities reject without partial state. |

The earlier title/offline context/loading refinement and accepted one-building frontage are included. [D09 route/resource review](W4-D09-review-r1/receipt.json) preserves world 29/29, route 27/27 and fifteen unchanged pins. Allocation savings establish ownership/reuse; software rendering supplies no physical-GPU performance measurement.

The first combined `85d5831` checkpoint failed stale content-source pins. [Original CI](ROOT-ci-85d-failure-r1/receipt.json) and failed export remain preserved. The intentional migration produced `79e5c15`, whose [native CI passed all 37 steps](https://github.com/occult-kranti/ANDOLAN/actions/runs/39139568524); [exact receipt](ROOT-ci-79e5-pass-r1/receipt.json). No failure is relabeled as a pass.

## Exact package, actual execution and delivery

[W6 archive qualification](W6-package-r2/qualification-receipt-uid-reviewed.json) passes 40/40 gates: 559 runtime inputs, 81 total ZIP members, identical 70,594,852-byte/550-entry PCKs. Linux ZIP SHA `781d904d2f6986f423274cf23ecdc16a35df65df755db5171a97a152a3c88aa8`; Windows `8051586f45275c0e1956749f428a8ad2643ada69582410056597ed6f5efe01c8`. PCK SHA `f2be4e20a0f3ea3915c5ab94e3896278ab4778991e80c6c8abaadc5209511a59`.

The official exporter and explicit patched Linux runtime are separately pinned. Eleven bundled source/build/license proofs identify the one public-source pipeline task-priority patch; renderer features remain unchanged. The original strict audit rejected 75 nonruntime UID-generation warnings. A separately reviewed allowlist binds exactly those warning/source/log identities; unknown, duplicate and missing warnings still fail. [Independent guard review](W5-qualification-uid-review-r1/receipt.json) and original failure remain available. Actual runtime logs have zero warnings/errors; exports are not described as warning-free.

[W1 actual owner](W1-actual-r1/package-successor-r2/receipt.json), [W6 independent raw review](W6-integration-r1/package-native-independent-r2.json), and [W2 all-original visual review](W2-package-successor-r2/receipt.json) bind the extracted sibling runtime/PCK and all 28 original images/sidecars:

- Warm: 126.094 seconds for the complete route, 7 manual + 9 natural captures, 13/13 gates, native Quit 0. Title→Confluence→controls capture at 100/200%→selected guide at 200%→world→title. Shader seeds and the external test-only scale hook are declared.
- Cold: 269.549 seconds for the complete route, 3 manual + 9 natural captures, 12/12 gates, native Quit 0. Independent fresh preferences and empty shader caches, no seeds or scale hook; title→Confluence→title.
- W1 and W2 opened all 28 originals. W6 checked raw identities, 85 native window events and source/runtime/receipt bindings; root opened eight representative originals. The prior 59-image qualification belongs to the historical 96d5 release.

An initial validator expected a nonexistent sidecar field; its failure and original code remain preserved. The corrected validator reads actual PNG dimensions and recorded Window.size without rerendering or altering the package/observer. Both `auto-loading-3` images actually show construction; visible copy and sidecar phase govern, not the filename. The guide's long details intentionally scroll at 200%. Full route durations on llvmpipe are not startup or FPS benchmarks.

The [desktop polish preview](https://github.com/occult-kranti/ANDOLAN/releases/tag/yuga-desktop-polish-2026-10-18) became public at 16:02:16 UTC, release 416542426. Direct upload returned HTTP 401 with the held draft still empty. [Actions 39142952163](https://github.com/occult-kranti/ANDOLAN/actions/runs/39142952163) transported the exact prequalified bytes without rebuilding; root then published with explicit release identity fields. [Publication receipt](../published/release-polish-r1/publication-receipt.json) and [independent public audit](W3-public-audit-r1/receipt.json) pass for all five fresh downloads, 81 ZIP members, the common 550-entry PCK and eleven Linux provenance files. Both downloaded ZIPs remain retained. The temporary transport branch was removed using its exact expected commit lease; no Git objects were pruned. Windows remains unexecuted.

## Rejected work and next goals

C5's two four-view clay takes remain rejected: helmet edge, capped narrow gather and plate-like falling masses persist. All protected head/crown/tie/camera controls remained fixed. No production GLB changed. CC0 catalog leads are research, not licensed-payload or fit admission.

The continuous landing take exposes about 100 ms of foot settling. Private candidates improved some endpoint gaps but introduced 30 Hz contact/joint failures; the time-to-contact trial failed slow-drop contact and high-speed admission continuity. All remain inactive. Canonical near hero is `db4b2ec7`, motion `5023b301`.

The [next six-owner queue](W2-next-queue-r1.md) is still useful; its initial source-repair/package dependency is now resolved. Prioritize a materially different coarse hair construction, continuous contact blending, night/water composition and actual active HUD states. Broader native journey, two-client authority, roster, physical-GPU performance and human listening/feel require their own evidence. No future background work or commercial-quality completion is implied by this checkpoint.

## Storage, backup and continuity

The earlier d199f607-backed cleanup reclaimed 1,034,743,808 allocated bytes from 182 exact inactive capture-source duplicates. The new [recovery map](W6-package-r2-duplicates/recovery-map.json) and helper were pushed and verified at `cef6d8c53b7278e9dc824299661de1b0775a4ad2` before removal. [Execution](W6-package-r2-duplicates/execution.json) removed exactly 82 ZIP-backed expanded staging/Windows raw-PCK duplicates, reclaiming 470,986,752 allocated bytes. Both qualified ZIPs, Linux raw PCK, actual extraction, originals, sources, caches and user state remain; retained files were rehashed afterward.

Recorded historical desktop reclamation totals **12,627,566,592 allocated file bytes**, not net free space. Use exact maps; no broad cleanup. The final source/evidence backup preserves this report and finite new evidence. [Active handoff](../../../ACTIVE_DESKTOP_HANDOFF.md), [campaign](../../../DESKTOP_FINISH_CAMPAIGN.md), and [workspace guidance](../../../../../../docs/WORKSPACE_AND_CLEANUP.md) are the entry points for later agents. Cloud setup preserves install/network/credential settings and pins the final backup checkout; saving its draft does not activate a snapshot.
