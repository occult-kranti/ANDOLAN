# Rejected R3 guard-return excerpt

**Status: rejected and incomplete.** Root stopped this actual-render capture after independent 24 Hz pose analysis identified an excessively fast return from Ravana's guard. The source candidate used a 0.12-second return blend; root required a 0.32-second replacement and a fresh recording. This archive preserves the failure rather than presenting it as an accepted full film.

The interrupted capture produced **452 PNG frames**, indices 0–451, at requested 24 Hz, ending at sampled time 18.791667 seconds of the intended 24-second film. Its source commit is `f00b086994a3625bf5f158d365d75cf6755773c0`. All 452 existing PNG hashes were checked against the interrupted-capture record while preparing this archive. That verifies file integrity against that record; **the capture did not finish and has no end-of-capture source-stability verification**.

## Preserved excerpt

[guard-return-REJECTED.mp4](guard-return-REJECTED.mp4) contains only existing frames **124–143**, in their original order, encoded by FFmpeg at 24 fps without audio, interpolation, cropping, effects or generated replacement frames. Those source samples span **5.166667–5.958333 seconds** inclusive. Twenty displayed frames make the clip **0.833333 seconds** long. It is an H.264 review copy, not a lossless replacement for the source images.

The archive contains only five source PNGs:

| Still | Sample time | Purpose |
| --- | ---: | --- |
| [132](frame-00132.png) | 5.500000 s | Guard-return boundary; the arm is still visibly extended. |
| [133](frame-00133.png) | 5.541667 s | First sampled return step. |
| [134](frame-00134.png) | 5.583333 s | Second sampled return step. |
| [135](frame-00135.png) | 5.625000 s | Arm has returned near its ready position. |
| [386](frame-00386.png) | 16.083333 s | Shadow and impact-ring review, separate from guard timing. |

Frames 132 and 135 show a substantial arm reset over 0.125 seconds; the intervening frames and excerpt preserve the transition for inspection. Root's rejection concerns that return speed. Passing finite-pose, deterministic-seek or resource tests did not establish acceptable motion. The revised return is outside this archive and requires its own evidence.

## Bounded shadow observation

Frame 386 was visually compared with R2's `docs/evidence/combat-scene-r2/frame-00009.png` at 16.1 seconds. The R3 shadow has a more continuous dark interior; the conspicuous bright holes seen in R2 are largely absent. Fine grain remains near the shadow edges, and dotted paving joins/inlays remain unresolved. Ravana's silhouette and the restrained gold impact ring are readable in the preserved frame.

This comparison is **not an isolated causal test** of the sun-angular-distance change: R3 is 1280×720 while R2 is 960×540, and the samples differ by approximately 0.016667 seconds. R2's comparison frame SHA-256 is `46ee751af2c20c64f4fca92a3f92f50287e87334dccccd73fd4a429b62057c6c`; preserved R3 frame 386 is `d08817e4040128ab040c10ea052be0489a34c9077471be013ba53c76f59a96ab`. The observation supported retaining the bounded lighting revision for further review; it did not override the failed guard-animation gate or establish commercial art quality.

## Provenance and limits

`interrupted-capture.json` is copied byte-for-byte from the stopped capture. `godot-output.txt` is the original Godot log, renamed only to keep its contents trackable under the repository's log-ignore policy. It records Godot 4.6.3 Forward+ using software Vulkan/llvmpipe; no hardware-GPU performance claim is made.

The `source/` files were extracted with `git show` from **f00b086994a3625bf5f158d365d75cf6755773c0**, not copied from the subsequently revised working tree. They include the choreography manifest, actor/director/VFX/lighting scripts and capture helpers. Their individual repository paths and hashes are recorded in `clip-metadata.json`. This is a source reference, not a standalone runnable package; model, animation and audio dependencies remain in the named repository commit.

`clip-metadata.json` records the exact FFmpeg command, encoder version, ffprobe results and all twenty input-frame hashes. `archive-manifest.json` hashes every archived payload file. `archive-manifest.sha256` is the checksum sidecar for the manifest itself and is intentionally outside the manifest's own file list. The archive contains no audio and does not copy all 452 source PNGs. It makes no claim of a complete film, accepted guard motion, completed source-end verification or authoritative gameplay.
