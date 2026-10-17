# Triad siege warning capture — bounded still review

Reviewed 17 October 2026 by the effects implementation agent after a separate capture run owned by the root agent. This is a retained technical capture and seven-image review, not an independent player study or final graphics approval.

## Capture and provenance

- Source capture: `/workspace/scratch/yuga-relays/siege-render-r1`.
- [Silent MP4](yuga-siege-preview.mp4): 180 frames, 1280×720, six seconds, 30 simulated frames per second; 360 physics ticks. This is actual Godot Forward+ output through llvmpipe software rendering, not a physical-GPU benchmark.
- Camera: `(8,12,-28)`, looking at `(0,1,0)`, 58-degree FOV. The title overlay identifies actual software rendering and simulated playback speed.
- [Capture report](siege-render-review.json), [video metadata](siege-video.json) and [runner receipt](capture-run.json) are copied verbatim. All 235 retained source hashes matched the checkout when this review was written.
- Effects source: `res://scripts/siege_effects.gd`, SHA256 `ef39110b21b9f3d1f6ee6591d4ce0a883a86f1e98587916823cf2b95997f75c0`.
- MP4: 419006 bytes, SHA256 `4653fb4b29fd1b8463a326239f6cd26b6e3ea64853daf639273f190f962c997a`.
- Capture report SHA256: `5e13510f0565b4b5dd68da420eb6b269bc5f1f654c5d4589538c51693bf7c45c`.
- [Archive manifest](archive-manifest.json) records bytes and SHA256 for every retained file except itself. Selected PNGs are renamed for archive clarity; their content hashes still match the original frame rows in the capture report.

No new runtime changes were made during this review. The full video was not watched and no audio was heard. The MP4 has one video stream and no audio stream. The four original siege cues and their playback behavior are outside this image review.

## Images actually opened

| Frame | Reported state | Observation from the rendered image |
| --- | --- | --- |
| [35](siege-frame-00035.png) | Two cannon windups, each age 0.167 s | Separated gold and cyan dashed boundaries remain visible against the light stone floor. Moon's inner bracket forms and Sun's smaller pointed marks can be seen while troops partially cover the center. |
| [45](siege-frame-00045.png) | Two cannon windups, each age 0.500 s | Full boundaries remain in place while inner marks sit nearer the center than frame 35. The segmented outline differs clearly from the uninterrupted cyan map circle to the right. Inner marks become small at this wide view. |
| [56](siege-frame-00056.png) | Two cannon impacts, each age 0.067 s | Aftermath is visibly softer than the active warnings. The floor and units remain readable through the sparse marks; no filled disk or broad bloom covers them. |
| [65](siege-frame-00065.png) | Two cannon impacts, each age 0.367 s | Aftermath is much fainter than frame 56. Some perimeter and inner marks are barely visible. This is a still-pair fade observation, not a judgement of continuous motion quality. |
| [90](siege-frame-00090.png) | Two overlapping chariot windups, ages 0.567/0.500 s | Gold/cyan segmented boundaries remain visible around the melee, but troops hide much of the inner geometry. Team shape and source direction are difficult to identify independently of color at this scale. |
| [145](siege-frame-00145.png) | No active effects | There are no residual siege warning or impact marks around the troop group. The continuous cyan map circle is still present to the right. |
| [155](siege-frame-00155.png) | Three windups: Sun cannon, Moon cannon, Sun chariot | Multiple boundaries remain visible without a solid ground fill. Two nearby gold warnings overlap into a denser cluster; the change does not solve every same-team overlap. |

Effect types and ages in the table come from the source-pinned report. They are not inferred solely from pixel appearance. Radius/timing/cancellation correctness belongs to the separate numerical tests; these stills do not independently prove those rules.

## What this review supports

The segmented boundary is a visible improvement over the previous continuous/concentric warning rings in [the earlier siege review](../siege-render-r2/SIEGE-RENDER-REVIEW.md). It separates combat markers from the map's continuous circles and avoids a bright ground disk. Gold and cyan are visibly distinct in these daylight frames. Early isolated warnings expose some of the different inner shapes. No warning geometry crosses the camera or obscures a large part of the scene. The paired impact stills show a restrained fade, and the no-effect frame shows cleanup.

These observations accept the capture as evidence of a bounded presentation improvement. They do not close the entire readability acceptance gate.

## Remaining issues and next acceptance gate

- **Source direction is subtle.** The source-facing notch is a small floor mark. In the isolated images parts of it can be discerned, but the firing direction is not an immediate, reliable cue in the dense melee. Do not claim the pointer is fully validated for gameplay.
- **Team shape needs a stronger test.** Brackets and pointed marks can be distinguished in the earlier isolated warning. At frame 90, small size and troop occlusion defeat confident shape-only classification. This review did not inspect a desaturated capture or test color-vision accessibility.
- **Same-team overlap remains.** Frame 155 still stacks nearby gold boundaries. There is less continuous concentric decoration, but the individual attack count is not obvious from this image alone.
- **Late aftermath is deliberately faint.** This prevents impact decoration from competing with active warnings, but a still alone cannot establish whether a player notices the hit transition.
- **Gameplay context is unreviewed here.** This staged camera does not validate normal third-person distance, night contrast, the complete gameplay HUD/relay card, small-window layouts, camera motion or user comprehension. The full movie, hardware frame time and sound also remain unreviewed.

Next owner: root/integration reviewer. Keep the improved boundary as the current prototype baseline; retain these open issues in the milestone. Before calling the warnings production-ready, review continuous normal-camera play in day/night scenes, dense simultaneous attacks and reduced-color views, with the real HUD visible. Native siege attacks affect troops; this marker review does not add or imply hero damage.
