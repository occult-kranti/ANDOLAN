# YUGA-HERO-STUDIO3 — Rama dossier

Native tactical Casual, baseline `e59a07a4786e9ad491cfef7a4e706dbd06063adc`. The Rama page becomes an ability and loadout studio beside the root-owned native viewer. Four compact icon/key selectors show one ability's name, cost, charge capacity, duration/shape and counterplay. Selection only changes the details. Preview explicitly requests the selected gesture; Ready and Aim request those presentation states. Busy and unavailable states follow the viewer report.

Costs, charge caps and earned ultimate points come from the validated current rules configuration. Magazine, reserve, base damage and reload come from the actual firearm profiles. Existing theme descriptions supply12s/10s duration facts; E/X retain truthful grounded-dash/three-shot labels. No new balance constants or hero mechanics are introduced. ARKA is labelled the starting sidearm, SURYA a bought upgrade shown in the studio. Inspecting equipment never buys or equips a match weapon.

Home, Casual, settings, help and actual threaded loading remain in the existing frontend. ChooseCasual remains outside the scroll region. Selector arrows/Home/End apply only while that selector has focus; view rotation owns its separate focus. ScrollContainer follows keyboard focus, including at150%scale. The existing in-match ability guide still uses the unchanged `_add_abilities` helper.

## Owned source and API

- `scripts/tactical_frontend.gd`: dossier integration and scroll-to-focus.
- `scripts/tactical_hero_dossier.gd`: read-only data and controls. Public `select_ability(slot)`, `request_preview(action)`, `data_report()` and `configure(showcase, settings)`.
- `tests/tactical/hero_dossier_cases.gd`: focused data, preview routing, keyboard and layout coverage.
- `tests/tactical/ui_cases.gd`: one hero-page assertion updated for selectors rather than four simultaneous descriptions.

Root owns `tactical_hero_showcase.gd`; the combat specialist owns the new full-body pose module. Dossier calls only the approved `set_preview`, `preview_report` and `set_reduced_motion` APIs. It never calls pose code or match authority, and does not promise weapon selection.

## Actual checks

```sh
godot --headless --path games/yuga-native --script res://tests/tactical/hero_dossier_cases.gd -- --report=/workspaces/ANDOLAN/games/yuga-native/docs/tactical/studio3/ui/checks-r2/result.json
godot --headless --path games/yuga-native --script res://tests/tactical/ui_cases.gd -- --report=/workspaces/ANDOLAN/games/yuga-native/docs/tactical/studio3/ui/flow-r1/result.json
```

The focused dossier suite passed32/32; the existing native UI suite passed36/36 separately. Both exited0 with no engine warnings/errors. Dossier checks cover1280×720 and960×540 at100%/150%, selector focus, scroll-to-focus, pinned main action, unavailable/unsupported/busy/reset, no animation on selection, source-backed economy/weapon data, repeated entry/exit and no match actors. The first test-only parser failure is retained in `checks-r1`.

The preview host in the focused suite implements the agreed contract; this is not acceptance of root's actual pose system. Native originals, both view modes, ordinary input and final appearance still require root integration/capture. [Source freeze](source-freeze.json) records exact hashes and boundaries.

## Pause-state integration correction

The root viewer now reports `paused`. Dossier feedback gives it precedence over the busy/playing message: **Preview paused · Play resumes**. Ready remains available while paused, and the focused host counterexample verifies this state and subsequent reset. The updated dossier suite passed 33/33 in `checks-r3`, exit 0 with no engine warnings/errors; the earlier 36-case flow run remains separate and predates this copy-only correction. No new broad suite was run. Final dossier SHA: `0746a845396cc113d807fe26baf366a80b87ab077a4c06dd5a21c7ed0ce66168`.

## Actual native visual review

All 13 original stills in `../visual-r1` were personally inspected: full-body Ready/Aim/Q/C/E/X, back, first-person Ready/Aim/Q/X, and 960×540 at normal/150% UI scale. Their hashes match the complete capture receipt; no source changed during capture. The selected details, paused feedback, mode controls and pinned Choose Casual are readable and remain inside bounds. The source-bound native viewer renders the real model and firearm.

At 960×540 with 150% UI scale, the hero is only about 100 pixels tall and much of the dossier requires scrolling. This is a retained limitation; 1280×720 at normal scale is the primary art view. Some staged captures select C/E/X programmatically while Q retains its keyboard focus outline. Selected title and pressed state remain correct; the focused suite separately exercises actual selector navigation.

[The scoped visual receipt](visual-review-r1.json) records all image hashes, rendering source pins and film metadata. These staged originals establish appearance, not ordinary input, combat authority, anatomical polish or physical-GPU performance. [The separate studio gallery](../PREVIEW.html) keeps these 13 views and the 9-second native preview film together; the earlier full-game gallery remains unchanged.

## Local gallery receipt

The gallery source is frozen at SHA `a85b08df745136c526c841f85e4fc2488b4afde4b732b7ee75e693089ccc9968`. The final focused Chromium check passed 9/9 in [preview-r4/receipt.json](preview-r4/receipt.json): 13 decoded stills, existing local document/media links, loaded local fonts, 1280×720 / 9-second video metadata and actual frame playback, desktop bounds, one filter and lightbox/Escape return. No external network request, script error or unexpected failed resource occurred. The actual [settled desktop view](preview-r4/settled-desktop.png) was personally inspected.

The initial `preview-r1` receipt is retained: its broad failed-request check counted Chromium's normal `ERR_ABORTED` cancellation after a video metadata preload. The later check exempts only that exact MP4 cancellation when verified metadata succeeds. Intermediate `preview-r2`/`preview-r3` receipts preserve the transient spinner and pre-compositor screenshot; the final check waits for a decoded video frame. The film itself retains four initial native loading-veil frames, followed by the visible hero, as recorded by root's encoding receipt. No runtime or gallery change was needed for these capture-timing corrections.

```sh
node games/yuga-native/docs/tactical/studio3/ui/preview-r4/check.cjs
```

Next owner: root, for combined delivery and ordinary native-input acceptance. UI runtime, gallery and this scoped review are frozen.
