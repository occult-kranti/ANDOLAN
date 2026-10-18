# U4-02 shared native control states

Completed a separate U4 review and narrow theme correction. An actual opened OptionButton enters Godot draw mode 4 (`HOVER_PRESSED`), but the theme reserved only 20px for its arrow in that state and had no mirrored style. Other states reserved 40px. `_set_choice_controls` now includes `hover_pressed`, preserving the arrow gutter and its RTL counterpart.

The independent baseline retains 7/8 passing checks and the exact omitted-state failure in `rejected-theme-r2/`. Final results are **8/8 new independent checks**, **88/88 existing theme regressions**, and **10/10 native XTest checks** with **50 actual events and 12 original PNGs**. All final processes exit 0, all sources stayed stable during their runs, and engine logs contain no errors. Tests and captures used isolated settings, existing bundled-font imports and no GLBs, game scenes or 3D imports.

## Actual views

`pixels-final/` contains 1280×720 original frames for normal/focused/disabled controls, pointer hover, held secondary and selected buttons, open LTR/RTL menus, rejected disabled click, checked toggle, keyboard-operated slider, held scrollbar, and utility/selected keyboard focus. Bright and dark backgrounds appear in every frame. All 12 originals were reviewed: the first 10 match the SHA-256 hashes of the 10 directly inspected prior final-run frames; the added two keyboard-focus originals were opened directly. Text remains readable on opaque surfaces, disabled states stay distinct, and the inset focus indicators remain complete.

The generous option widths in this board did not show text-arrow collision before the repair; the defect is the verified inconsistent arrow gutter/native-state contract. These captures establish actual state rendering and operation, not a claim that a current production menu visibly overlapped. The existing theme suite checks text contrast at 4.5:1 and focus at 3:1 across the defined surfaces. Scaled production screens, localization, assistive-technology support and performance remain separate gates.

## Retained fixture corrections

The first headless fixture dispatched mouse coordinates before defining its viewport/host geometry, so its popup assertion failed independently of the theme defect. Explicit viewport geometry and native mouse dispatch reached the real popup, leaving the actual gutter counterexample. `fixture-headless-r1/` retains that run.

The first rendered board set RTL after position and mirrored its test option into the other column; it also expected ordinary held buttons to use mode 4 when native Godot correctly used mode 1 (`PRESSED`). The fixture now assigns final position after layout direction and asserts the observed native state. `fixture-pixels-r1/` retains the rejected originals/receipt/source. Product code was not changed to satisfy those fixture errors.

## Exact execution and source

Run from `/workspace/ANDOLAN`:

```sh
env XDG_DATA_HOME=/tmp/yuga-u4-theme-independent-r3/user OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 taskset -c 2,3 timeout 60s godot --headless --path games/yuga-native --script res://tests/ui_independent_theme_cases.gd -- --report=/tmp/yuga-u4-theme-independent-r3/report.json
env XDG_DATA_HOME=/tmp/yuga-u4-theme-regression-r1/user OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 taskset -c 2,3 timeout 60s godot --headless --path games/yuga-native --script res://tests/ui_theme_cases.gd -- --report=/tmp/yuga-u4-theme-regression-r1/report.json
env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 LP_NUM_THREADS=1 taskset -c 3 python3 games/yuga-native/tests/ui_independent_theme_capture.py --output /tmp/yuga-u4-theme-pixels-after-r2 --display 186
```

`execution.json` records commands, counts, zero exit statuses and hashes. Theme before: `562a6658f7a64acb11ba183904ef8e62814d913825f98f678e4a9c3eef2b883c`; after: `b1d630e9087f939ba6a68a5bbfac6f126064d417393786380c324317ac5d39a6`. Source commit: `bc1a3dceaddc11f5c0745e73ad1f25f2ca77a0fb`, plus the pinned working changes. The final headless scripts ran on CPUs 2,3; rendering used CPU 3 and one llvmpipe/BLAS/OpenMP thread after root's CPU reassignment. No shared runner, ledger, commit or publication was changed.

Changed files: `scripts/hero_ui_theme.gd`, `tests/ui_independent_theme_cases.gd`, `tests/ui_independent_theme_board.gd`, `tests/ui_independent_theme_capture.py`, and this evidence directory. Next: root's U4 integration checkpoint and this reviewer's separate U4-06 counterexamples of other owners' fixes. U3's compact Bow-heading observation is owned by U4-05 and will receive independent U4-06 pixels; it is not claimed fixed by this theme change.
