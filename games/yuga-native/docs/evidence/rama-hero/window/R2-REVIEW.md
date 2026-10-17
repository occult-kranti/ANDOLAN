# Rama package R2 — accepted affected-screen repeat

17 October 2026. Source **`78b49fbe8b9edeb78b09c2363b878bf73c158602`**; PCK SHA-256 **`dc40798bfdc5927300eeecf6c768d006c61903dc5fcd0f8c7b3ce72ddeaa2f3a`**. [Package manifest](package-r2-manifest.json) pins all runtime sources. [Review receipt](r2-review.json) records exact commands, package/engine hashes, screenshot dimensions, event counts and limits.

**The affected repeat passes at 960 × 600 and 1280 × 720.** Real XTest mouse/keyboard input opens Settings with the complete `YOUR PREFERENCES` eyebrow and Settings heading visible. Seven Tab presses move focus to Back and scroll its entire button into view. Escape returns to title; reopening Settings restores the top and full heading. Loaded title, subsequent title return and Confluence entry/HUD are correct at both sizes. All twelve PNGs were visually inspected.

| Actual evidence | 960 × 600 | 1280 × 720 |
| --- | --- | --- |
| Loaded title | [01](960x600-r2/01-title-loaded.png) | [01](1280x720-r2/01-title-loaded.png) |
| First Settings entry | [02](960x600-r2/02-settings-first-entry.png) | [02](1280x720-r2/02-settings-first-entry.png) |
| Back focused after intentional keyboard scroll | [03](960x600-r2/03-settings-back-focused.png) | [03](1280x720-r2/03-settings-back-focused.png) |
| Settings reopened at top | [04](960x600-r2/04-settings-reopened.png) | [04](1280x720-r2/04-settings-reopened.png) |
| Title after Settings | [05](960x600-r2/05-title-after-settings.png) | [05](1280x720-r2/05-title-after-settings.png) |
| Confluence entry | [06](960x600-r2/06-confluence-entry.png) | [06](1280x720-r2/06-confluence-entry.png) |

The 960 run records 21 events; the 1280 run records 18. Both helpers closed normally with exit 0, no engine errors or warnings, and no runtime edits between checks. Their game cleanup code −15 is the helper's requested termination. At 960, title return focuses Bow training: Return briefly entered that mode, then the recorded input returned normally to title and clicked Explore Confluence. The world screenshot follows that real flow, not a direct keyboard world-entry claim.

Settings is scrollable. At its top position the bottom edge of Back lies below the scroll viewport; Tab reveals the full focused button. The eyebrow naturally leaves view during that intentional scroll, then is fully visible when Settings reopens. This differs from the rejected R1 initial state, where the eyebrow was already clipped before any scrolling.

This is the bounded follow-up for the Settings fix, not a repetition of every R1 action. The broader title/training/ability/pause/remap/reset/world flow evidence remains in [the R1 review](REVIEW.md), with its exact package and limitations. Rendering used software Vulkan llvmpipe/Forward+ and Dummy audio: no physical-GPU performance, listening-quality, Windows or continuous animation/contact claim. The heavy renderer was closed and released to the final gameplay capture owner after both repeats passed.
