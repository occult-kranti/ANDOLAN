## Confluence: a duel of timing

An original 24-second Rama-versus-Ravana Sentinel combat film, built in the native YUGA project. It demonstrates a blocked solar arrow, a telegraphed spectral wave, an evade and a countershot. Two skinned actors use rig-specific libraries with nine clips each, original costume work, timeline effects and an original synthesized soundtrack.

The local milestone is verified. The [movie is publicly available](https://raw.githubusercontent.com/occult-kranti/ANDOLAN/game/yuga-native-production/games/yuga-native/docs/evidence/combat-film-r4/yuga-confluence-duel.mp4). Download the native ZIPs from this release's assets. The local execution evidence below does not automatically establish execution of a later CI rebuild; its release manifest identifies the rebuilt files separately.

### Watch or run

- **Watch:** `yuga-confluence-duel.mp4`, 720p, 24 fps, 24 seconds, stereo sound.
- **Linux package:** extract the entire `yuga-native-linux-x86_64.zip`, then run `./launch.sh`. The exact local package has been extracted and tested through its actual game window.
- **Windows package:** extract the entire `yuga-native-windows-x86_64.zip`, then run `launch.bat`. The local archive and packed resources validate; Windows execution remains untested.
- Choose **WATCH CONFLUENCE DUEL** from the title. Playback supports pause, seeking, replay, captions, static camera, reduced flashes and the saved game volume.
- The package also includes **EXPLORE CONFLUENCE** and the existing courtyard training mode. No editor installation is required.

### Verification and scope

The film contains 576 sequential engine-rendered frames. Independent media checks verify frame hashes/timestamps and zero measured audio offset against the source mix, including four critical cue windows. Animation checks cover finite skeleton transforms, planted-foot geometry, action boundaries and deterministic backward seeking. Revision 4 corrects the fast guard-reset transition; 20 screenplay, 42 native integration and five continuity checks pass. A later saved-volume fix passes 22 audio/focus checks and the repeated 42-case integration suite.

Actual Linux keyboard/mouse testing covers title entry, pause, ±1-second seek, scrubbing before/after the hit, replay, three accessibility toggles, both return paths, saved mute and training movement. The Windows archive is checked but unexecuted. The movie snapshot and later viewer gain fix are separately pinned. Audio timing/encoding is checked numerically; listening quality has not been reviewed.

The [direction review](COMBAT_FILM_REVIEW.md) records full video/archive hashes and the tested local source `f52ceffd88d9f444541d56f7a755e57af0dcd2e5`. Future CI outputs require a pack-hash comparison or fresh execution before inheriting the local runtime result.

This is an animation and presentation prototype. Its scripted visual receipts do not implement a playable, network-authoritative fight. The full hero roster, native competitive multiplayer, production animation polish and Deadlock/Overwatch-level visual quality remain open roadmap work. Floor aliasing, simple materials and sparse scenery remain visible. Software rendering does not establish gaming-GPU performance.

Source, screenplay, review records and the full production roadmap:
https://github.com/occult-kranti/ANDOLAN/tree/game/yuga-native-production/games/yuga-native


Packages were rebuilt and checked at `58fbe631bda2efcc23563be0958c3f403e4a6361`. The MP4 and archived render reports retain their original captured source hashes; later tested playback fixes can differ from captured source. CI checks decoded media/audio correspondence and native headless scenarios; it does not rerender the film, listen to its sound, run Windows or measure hardware-GPU performance.
