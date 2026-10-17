# Exported Linux siege preview — actual window review

17 October 2026. The portable ZIP built from `9520d616c88d058cc6943ddc3017303eba68c026` was extracted into a new directory and executed with its bundled Godot and PCK. The actual 960 × 600 X11 window used Forward+ on llvmpipe. Input was delivered through XTest keyboard/mouse events; no game state was injected. Engine/PCK and screenshot hashes plus event order are recorded in `input-review.json`. Native package/export manifests identify the ZIP and sources. Both fresh capture archives were decoded and matched against the actual exported source inventory in `export-capture-verification.json`.

## Observed passes

- The title rendered and mouse selection entered Confluence (01,02). Escape opened a fitting pause menu with visible Siege practice, explanation, settings, return and quit.
- Tab from Continue followed by Return entered the six-unit siege encounter. The actual HUD showed two cannons, two chariots and two enemy siege units, with the correct offline drill label (03,04). Vehicle silhouettes and minimap emphasis were visible at player distance.
- The volume slider reached muted, mouse selection restarted the drill, and gameplay continued with visible units/ground effects (05,06). `saved-settings.cfg` records volume0.0. This validates saved mute state, not listening quality; the renderer used the Dummy audio driver.
- F5 restored the ordinary arrival court, Wave1/core/gold HUD and infantry formation (07). F2 opened the keyboard-help/remapping panel and Escape dismissed it (08,09).
- Ten OS Tab presses returned focus to Continue, visible after the renderer settled (12). Frames10 and11 were captured while the software renderer was still processing the input batch; they are retained as intermediate frames, not the asserted final focus positions. Reverse focus, every target and both logical viewport layouts are additionally covered by the headless suite.
- Mouse Return to courtyard restored the title (13). No engine/script error appeared in the process log. Owned processes were then terminated by the review helper.

Movement and fire events were also delivered before F5, but the screenshots do not isolate their outcomes, so this review does not claim a new hit/damage or locomotion acceptance from those actions. The earlier native suites remain the detailed logic checks.

## Remaining issues and scope

Help's compact footer still labels F5 as `respawn`; the actual reset behavior and pause action are correct. Correct that wording in the next UI pass. Overlapping bright map/attack rings need clearer separation. Vehicle materials, facial/costume detail, contact and sophisticated combat motion remain below the concept target. This review accepts a bounded offline prototype flow, not complete visual production, online play, hardware performance or Windows execution. Windows was archive/resource-validated only.

An initial window-r1 helper invocation closed immediately because stdin was not kept interactive. It contained no reviewed screenshots or gameplay result and is preserved in scratch; this r2 used an interactive session. All raw window evidence remains under `/workspace/scratch/yuga-siege/window-r2`. Public-download verification remains a separate release gate.
