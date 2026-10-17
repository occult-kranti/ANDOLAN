# Final source-bound traversal render review

Bounded pass for the actual staged native traversal capture at `/workspace/scratch/yuga-next/mythic-traversal-render-r3`. This archive refreshes the prior accepted `mythic-traversal-render-r1` against the final fresh-pause layout correction. Earlier accepted and rejected archives remain unchanged.

## Capture and source evidence

The runner completed 180 consecutive 1280×720 frames at 30 simulated fps and 360 physics ticks at 60 Hz, plus five separate staging stills. The silent H.264 MP4 is exactly 6.000 seconds and 180 decoded frames. Its SHA256 is `5ed183857b027618f20494d6615bd66be55302d509342ac0d6b9f96aa26f8d00`. Runner validation and an additional full FFmpeg decode completed successfully; the actual Godot log contains no ERROR or WARNING lines.

The report pins 292 current source files, including shaders. All pins were compared with current files during archiving. The only source change from the prior capture is `scripts/confluence_world.gd`, now SHA256 `c5469ed557bba6fb3510f537b6845354631a580d0a2a738ff2b411ce3b6099b2`. All 185 PNGs and the MP4 are byte-identical to the prior actual attempt, as recorded in `source-refresh-comparison.json`. Current report SHA256: `48a52008d69d8a5c76cc9a8911b762a34933793c3f5176d66ee1171ca4fd2086`.

## Direct image observations

Frames 15, 90 and 175 and all five retained stills were inspected as actual images. The lower-left invocation and controls cards leave Rama's central body clear. Flight/grapple status, energy and the minimap are readable at the captured 1280×720 size; the recorded take includes a visible rope and finite flight/carry poses. The army still distinguishes teal and red units, bows, polearms and a banner. These are simple articulated units; the still does not qualify complete combat animation. The city overview exposes three long routes and deliberately sparse repeated architecture. The night still shows cool streets with warm lamps and lit windows, without losing the visible route or troop silhouettes. The landing-court still exposes blocklike platforms and floating traversal markers; it is a staging view, not natural environment-art acceptance.

No new obvious detached limb or centre-HUD occlusion was observed in these sampled views. Fine distant ground and building details alias, surfaces and silhouettes remain coarse, the skyline is mostly empty, and hero face/hair/cloth and many environment assets remain below the intended production quality.

## Scope and limits

Recorded outcomes confirm flight, grapple, visible rope and finite poses in this scripted take, with maximum speed 18 and minimum energy 19.4. The maximum captured scene counters are 1,138 draw calls and 595,687 rendered primitives. Forward+ ran on the software renderer; these are scene counters and simulated playback timing, not a hardware FPS benchmark.

This capture does not exercise the fresh pause menu's Continue action and therefore cannot establish that fix. The final packaged OS-input review owns that evidence. The five stills are separate staging views and are not spliced into the continuous clip. Selected still inspection and complete codec decoding do not constitute full video playback, auditory audition, Windows testing, online multiplayer qualification or AAA art acceptance. `REVIEW.md` and `TRAVERSAL-RENDER-REVIEW.md` intentionally contain identical review text for release staging and repository links.
