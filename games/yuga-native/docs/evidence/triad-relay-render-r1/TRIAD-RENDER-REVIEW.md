# Triad relay capture: bounded visual review

Reviewed 17 October 2026. This is the first accepted relay capture archive, copied from the corrected raw attempt `/workspace/scratch/yuga-relays/triad-render-r2`. Acceptance covers the technical capture and the seven explicitly inspected still images. It does not close production art acceptance.

## Evidence and source

The capture contains 180 actual Forward+ frames at 1280 × 720 across 360 native physics ticks: six seconds of simulated 30 fps playback, with time scale 1. The adapter reports llvmpipe software Vulkan and X11. One initial hero/ammo/camera fixture and 7.5 seconds of unrecorded preparation precede the take; four frozen-world station views follow it. The MP4 is silent.

`triad-render-review.json` retains the complete source hashes, per-frame image hashes, actual renderer counters, relay state and supply receipts. `capture-run.json` records execution; `triad-video.json` records encoding and probing. All 180 raw frame hashes, four still hashes, report/video cross-hashes and 235 captured source hashes matched at archival. An independent ffprobe counted 180 video frames, 1280 × 720, 30/1 fps, duration 6.000000 seconds and no audio stream. This was structural media verification, not full video playback.

The working branch was `game/yuga-native-production`, based on commit `5c538388317b8bda14b7945fa341abc1a19a8657`; the capture helper had a pending source change. The captured hash inventory, rather than an assumption that all working files equalled HEAD, pins this take. Relay art SHA256: `32e42d32a4a1e52414c2e274d076c1aac4531fd10084b052082f0cc08cd31cb6`. Capture helper SHA256: `e3a197f2a476a1a249b4ea159a7b01109f962e404c1f1d40e8658333bcda98d7`.

## Rejected attempt and correction

The [rejected first attempt](../triad-render-r1-rejected/REVIEW.md) exposed an inherited bright gold circular mid-lane inlay under the hero. It visually overwhelmed the new angular objective pad. The three superseded lane-mid-inlay nodes are now hidden while their provenance and the separate base medallions remain. A fresh capture was taken after the correction; this archive does not relabel the rejected images as accepted.

## Actual observations

Images independently opened: `triad-frame-00015.png`, `triad-frame-00090.png`, `triad-frame-00175.png`, `still-reed-day.png`, `still-lotus-day.png`, `still-sky-day.png` and `still-lotus-night.png`.

- **Gameplay hierarchy:** the removed torus no longer dominates the hero or objective. Angular corner marks and rectangular progress rows remain visible around the hero. The Sun station emblem and HUD labels are readable at the captured resolution. Frames 15 and 90 show 3/12 arrows and frame 175 shows 6/12; the separate recorded state confirms one applied +3-arrow supply receipt. The images alone do not validate supply timing or authority.
- **Station construction:** the three stepped plinths read as grounded off the pads. The raised Sun star is clear against its dark backing. Neutral grey diamonds are more subdued. No obvious detached component, gross clipping or lane overlap appeared in these seven views; physical clearance is covered by integration tests, not inferred from screenshots.
- **Site identity:** Reed stems, Lotus petals and Sky sails are visible in the closer stills. Their differences remain subtle beside the shared prominent rectangular ownership badge and stepped base. Ownership is more legible than individual site identity at gameplay distance.
- **Neutral markings:** Reed/Sky corner and progress tiles have weak contrast against beige paving and visibly stippled/dashed dark edges at grazing angles and shadow boundaries. The cause is not established by still review; closer surface/aliasing inspection remains appropriate.
- **Night:** the paired Lotus view becomes cool blue while retaining readable floor, plinth, Sun emblem and progress rows. Warm lantern windows stand out more. These are small emissive accents, not demonstrated area illumination. No critical visual disappears in this paired view.

## Limits and next review

No full video playback, continuous rotor/contact review or day/night transition review was performed. The inspected views demonstrate neutral and Sun states; Moon ownership, teal capture progress and contested flags still need actual render review. Source bounds and physics checks remain separate evidence. The take does not demonstrate human-input usability, listening quality, human balance, online authority or physical-GPU frame rate.

The corrected prototype framing is usable in these inspected views, with no major new render blocker observed. Broad primitive shapes, uniform surfaces, repeating architecture, weak neutral contrast and subtle site motifs remain visible art limits. This is not acceptance of Deadlock/Overwatch-level or other AAA visual quality. The next art review should address neutral-pad contrast, stronger site silhouettes, Moon/contested presentation and continuous motion at gameplay distance.
