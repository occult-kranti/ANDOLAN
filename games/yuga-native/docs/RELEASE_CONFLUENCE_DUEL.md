## Confluence: a duel of timing

An original 24-second Rama-versus-Ravana Sentinel combat film, built in the native YUGA project. It demonstrates a blocked solar arrow, a telegraphed spectral wave, an evade and a countershot. Two skinned actors use rig-specific libraries with nine clips each, original costume work, timeline effects and an original synthesized soundtrack.

The local milestone is verified. The [movie is publicly available](https://raw.githubusercontent.com/occult-kranti/ANDOLAN/game/yuga-native-production/games/yuga-native/docs/evidence/combat-film-r4/yuga-confluence-duel.mp4). The [r2 native release](https://github.com/occult-kranti/ANDOLAN/releases/tag/yuga-confluence-duel-2026-10-17-r2) is published from commit `58fbe631bda2efcc23563be0958c3f403e4a6361`; its [build and release workflow](https://github.com/occult-kranti/ANDOLAN/actions/runs/39002862685) reports Success. Download the native ZIPs from that release's assets. All 26 project-uploaded assets were independently downloaded and verified against their manifest/checksum inventory. The exact published Linux ZIP was extracted and exercised through a bounded actual-window review; its results are recorded separately from the earlier local package.

### Watch or run

- **Watch:** `yuga-confluence-duel.mp4`, 720p, 24 fps, 24 seconds, stereo sound.
- **Linux package:** extract the entire `yuga-native-linux-x86_64.zip`, then run `./launch.sh`. The exact published ZIP has been extracted and tested through its actual game window.
- **Windows package:** extract the entire `yuga-native-windows-x86_64.zip`, then run `launch.bat`. The published archive and packed resources validate; Windows execution remains untested.
- Choose **WATCH CONFLUENCE DUEL** from the title. Playback supports pause, seeking, replay, captions, static camera, reduced flashes and the saved game volume.
- The package also includes **EXPLORE CONFLUENCE** and the existing courtyard training mode. No editor installation is required.

### Verification and scope

The film contains 576 sequential engine-rendered frames. Independent media checks verify frame hashes/timestamps and zero measured audio offset against the source mix, including four critical cue windows. Animation checks cover finite skeleton transforms, planted-foot geometry, action boundaries and deterministic backward seeking. Revision 4 corrects the fast guard-reset transition; 20 screenplay, 42 native integration and five continuity checks pass. A later saved-volume fix passes 22 audio/focus checks and the repeated 42-case integration suite.

The earlier local-package keyboard/mouse testing covers title entry, pause, ±1-second seek, scrubbing before/after the hit, replay, three accessibility toggles, both return paths, saved mute and training movement. The Windows archive is checked but unexecuted. The movie snapshot and later viewer gain fix are separately pinned. Audio timing/encoding is checked numerically; listening quality has not been reviewed.

The published Linux repeat verifies title → film, pause, ±1-second seek, pre/post-hit scrubbing, replay, Escape return and saved mute. It does not repeat every earlier local toggle/training flow. Its final Courtyard-button click was captured during loading, so successful return from that click is not claimed in this run. The [published review](evidence/combat-film-published-r2/REVIEW.md) and [direction review](COMBAT_FILM_REVIEW.md) record exact hashes and source `58fbe631bda2efcc23563be0958c3f403e4a6361`. A decoded comparison explains the local/CI pack difference as generated node IDs and two one-step leaf-shading values; runtime scripts, animation and audio match. Windows remains unexecuted.

This is an animation and presentation prototype. Its scripted visual receipts do not implement a playable, network-authoritative fight. The full hero roster, native competitive multiplayer, production animation polish and Deadlock/Overwatch-level visual quality remain open roadmap work. Floor aliasing, simple materials and sparse scenery remain visible. Software rendering does not establish gaming-GPU performance.

Source, screenplay, review records and the full production roadmap:
https://github.com/occult-kranti/ANDOLAN/tree/game/yuga-native-production/games/yuga-native
