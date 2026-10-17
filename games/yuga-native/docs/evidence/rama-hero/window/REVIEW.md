# Rama packaged native-window review

The affected-screen follow-up on package R2 is **accepted at both sizes**: see [R2 review](R2-REVIEW.md) and [exact receipt](r2-review.json). The R1 failure and broader-flow evidence below remain preserved.

17 October 2026. Original Linux package R1: source `2d9353cb6723cf89d6967994f2c773d9bd66c6e6`, PCK SHA-256 `8a7aa2efa23daf4370dee8d7b74f0583a6ea44185863d96df483de942bee98a9`. [package-r1-manifest.json](package-r1-manifest.json) pins its payloads and runtime sources. [review.json](review.json) records run hashes, owners, scope, Settings correction evidence and limits.

These are real X11/XTest keyboard and mouse interactions with the extracted package, rendered using software Vulkan llvmpipe/Forward+ and Dummy audio. Capture event hashes and actual PNG dimensions are retained in each `input-review.json`. Both helpers exited normally; their game cleanup exit of −15 is the requested termination, not a crash. Neither game log has engine errors or warnings. Local game preferences are retained only under `local-saves`; shader caches and unrelated user files are excluded.

## R1 finding: Settings entry rejected

Opening Settings before any intentional scrolling clips `YOUR PREFERENCES` at both sizes. The main Settings heading, values and actions remain visible in the OS captures. This is an unwanted initial focus/layout scroll state, not a deliberate user-scrolled view. See [960 first entry](960x600-r1/04-settings.png), [960 return from remapping](960x600-r1/07-settings-saved.png) and [1280 first entry](1280x720-r1/02-settings.png). These original runs are **rejected for Settings presentation**; they do not establish all-label visual acceptance.

The narrow correction resets Settings scroll after two container layout passes, only while the panel remains visible and Sensitivity retains focus. It changes no other screen. The expanded [screen regression before](settings-entry-fix/before.json) fails six meaningful checks: complete entry heading/eyebrow and clean reopen at 960 × 600, 1280 × 720 and 1920 × 1080. [After correction](settings-entry-fix/after.json), **36/36 pass**, exit 0, no engine errors or warnings. Before/after logs and exact source hashes are retained beside the reports. The later [fresh-package actual repeat](R2-REVIEW.md) closes this affected-screen gate; headless success alone did not establish that result.

## Other bounded R1 flow findings

The root reviewer owns [960 × 600](960x600-r1/input-review.json): 24 screenshots and 64 recorded events cover loaded title, ability guide, local settings/sliders, remapping Piercing Dawn to J, saved mapping carried into Confluence, training HUD, five-ability input across training/world, reset, pause, keyboard menu scrolling and title return. The interface reviewer also inspected its final returned-title frame. Preserve these capture qualifications:

- `01-title.png` is the actual boot splash; `02-title-loaded.png` is the loaded title.
- `11-guardian.png` follows a rejected Guardian press while Piercing Dawn was committed; it is not an accepted Guardian cast. `13-guardian-active.png` is the later valid Guardian state.
- `19-world-volley.png` is a post-cast snapshot showing 13 seconds of cooldown, not the release instant.

The interface reviewer owns [1280 × 720](1280x720-r1/input-review.json): 14 screenshots and 46 events. The loaded title frames the real hero clear of the menu; training HUD, five-slot ability bar, health, ability guide, focused training pause and title return are legible. The settled Confluence HUD leaves the hero clear. Keyboard Tab navigation scrolls to a visible, gold-focused Return to courtyard action; Enter restores the title. This subset does not repeat the 960 remapping, saved-slider, five-cast or reset checks.

Useful 1280 evidence: [loaded title](1280x720-r1/01-title-loaded.png), [training HUD](1280x720-r1/03-training-hud.png), [guide](1280x720-r1/04-training-ability-guide.png), [training pause](1280x720-r1/05-training-pause.png), [live Confluence HUD](1280x720-r1/09-confluence-hud-live.png), [pause](1280x720-r1/10-confluence-paused.png), [keyboard return focus](1280x720-r1/13-confluence-return-focused.png), [returned title](1280x720-r1/14-confluence-title-return.png).

Its filenames also retain timing observations: `07-confluence-hud.png` caught the outgoing title during scene loading; `08-entry-settled.png` is the newly loaded world paused by Escape; `11-confluence-return-focus.png` actually focuses the volume slider; `12-confluence-scroll-focus.png` shows the scrolled menu after a held Tab repeats. Only `13-confluence-return-focused.png` establishes the intended return focus.

This review does not establish physical-GPU performance, listening quality, Windows execution or continuous animation/contact quality. The software-rendered scene transition visibly takes time, and the menu can need scrolling; neither is hidden by the evidence labels.
