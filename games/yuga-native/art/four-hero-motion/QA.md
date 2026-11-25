# Four-hero motion review

The concept turnarounds set an art target. The three-panel sheets and their illustrated film show anticipation, release and recovery. The four individual films show the exported skinned models moving in the Lanka court. The Blender boards show how those meshes read from four cameras. Character detail, hair, facial acting and cloth in the concept sheets exceed the geometry and secondary movement in these rig studies.

## Results

All 619 frames of the four character films decoded at 24 fps. Eighteen fixed-camera shots showed both visible pixel change and a change in the distance between sampled joints. The separate illustrated signature reel decoded all 928 frames and its twelve action beats. [Frame, model and pose evidence](evidence/media-qa.json)

| Hero | Skinned joints | Shots | Decoded frames | Fixed-camera shots with measured articulation |
| --- | ---: | ---: | ---: | ---: |
| Hanuman | 167 | 6 | 163 | 3 |
| Rama | 164 | 11 | 162 | 9 |
| Shiva | 163 | 5 | 148 | 3 |
| Krishna | 165 | 5 | 146 | 3 |

The Chromium gallery passed all eight checks, including local video playback for every hero, keyboard navigation, a 390-pixel touch layout and chapter selection on cold media. Lanka Dahan sought to its 4.083-second cut, and Govardhan Canopy started at 29.000 seconds in the illustrated reel. All requests remained local. [Browser receipt](evidence/gallery-qa.json) · [Desktop](evidence/gallery-desktop.png) · [Mobile](evidence/gallery-mobile.png)

## Reproduce the checks

From a repository checkout with Python, Pillow, NumPy, FFmpeg, FFprobe and the project’s Playwright installation, run the following commands. The gallery check uses Chromium from `PLAYWRIGHT_CHROMIUM_EXECUTABLE` or `/usr/bin/chromium` when available.

```sh
python3 games/yuga-native/art/four-hero-motion/tools/verify_media.py
node games/yuga-native/art/four-hero-motion/tools/verify_gallery.mjs
```

The media verifier fully decodes each MP4. It pairs the motion visible in the middle of each shot with samples of the head, hands, feet and hero-specific joints. Distances between joints survive a whole-character translation and camera orbit. A measurable distance change in a fixed-camera shot demonstrates articulation. The verifier also matches the four downloaded model hashes to their render traces, reads the binary animation accessors, resolves local script references and checks each illustrated chapter against its source sheet. [Media results](evidence/media-qa.json)

The gallery check loads the production page under a nested local URL. It blocks external HTTP requests, plays videos through Chromium’s native controls, follows hero deep links and checks the 390-pixel touch layout. It operates on files in the package. Upstream reference links in scripts still require internet access. [Gallery results](evidence/gallery-qa.json)

## Production boundaries

The quartet preserves the original comparative Hanuman model, with 17 weighted surfaces. The current playable Hanuman has a separate 18-surface mesh with modeled crown, facial and tail locks. Rama’s draw and release animations here use his near-detail Confluence mesh. Shiva and Krishna use preview GLBs with newly authored action tracks. Registering their gameplay slots and balancing their proposed mechanics are future work. The gallery and video QA cover media playback and geometry. Multiplayer balance, live hit timing, physical cloth and collisions need separate match tests. [Finished Hanuman comparison](../hanuman-hero-finish/QA.md) · [Classic roster](../../../yuga-rust/assets/classic-roster.json) · [Native pose comparison](../../docs/rust-rebuild/HERO-POSE-EVIDENCE.json) · [Rama motion comparison](../../docs/rust-rebuild/deep-search/RAMA-PORT-EVIDENCE.json)

The catalog contains Hanuman, Shiva, Rama and Krishna. The only game-source match for “Andy” credits Andy Johnson as one of two artists on a ribcage reference. The 14 playable entries have distinct roster IDs. [Anatomy credit](../../docs/research/hanuman-match-sources.md)
