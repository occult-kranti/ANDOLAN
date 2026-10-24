# Native atlas CI repair — 24 October 2026

The exact foundation run [40047130748](https://github.com/occult-kranti/ANDOLAN/actions/runs/40047130748/job/120731326446) failed on source `3497197745beb8e0fd22a9b67efe505700dec469`, after the reuse continuation passed. Step 31, **Native screen and recovery contracts**, failed only `ui-atlas-layout`: its three constrained-canvas cases observed a 108-pixel-wide plot, with an 87.2-pixel height at 640×360. The unchanged legacy contract required at least 120×100. All other 46 screen suites passed. The original failure and matching local reproduction remain in this directory.

The narrow runtime repair restores a 120-pixel plot width and a 100-pixel height when the actual space above combat permits. Shorter canvases retain the available locator and the existing F1 overview. The bottom combat HUD remains 80 logical pixels, and no essential font or existing test threshold was reduced. The adaptive test retains its 41 existing cases and adds readable-width, available-height and core-caption-containment checks.

Focused validation passed: **42/42 unchanged atlas checks**, **41/41 existing adaptive cases**, and **41/41 strengthened adaptive cases**. No full suite rerun was performed. Four actual X11 Forward+ software-rendered PNGs passed the existing capture runner in 64.444 seconds, with exit 0, unchanged source/imports and no warnings or errors. This worker and the root independently opened all four originals.

| Actual 200% layout | Plot | Combat height | Map-to-combat gap | Observation |
| --- | --- | --- | --- | --- |
| Base 1280×720 → logical 640×360, idle and returning | 120×100 | 80 | 96 | Readable map captions and marks; full summary text fits. |
| Base 960×540 → logical 480×270, idle and returning | 120×94 | 80 | 12 | Dense stress layout; summary/map/combat remain contained with positive gaps. |

The tiny returning summary is 148 logical pixels tall and still obscures part of the hero's upper body. This bounded repair does not qualify that stress profile as spacious. The spawn marker still truthfully shares a location with its faction core. These arranged idle/returning captures do not repeat the earlier native-input journey, qualify a package, or establish hardware performance.

[receipt.json](receipt.json) binds commands, source hashes, original failure, checks, capture freeze, independent review and remaining limits. [actual/measurement.json](actual/measurement.json) binds the four original PNGs. Root owns the commit, push and verification of successor CI/package runs; the original failed run is preserved.
