# Published cinematic release verification

The [r2 preview release](https://github.com/occult-kranti/ANDOLAN/releases/tag/yuga-confluence-duel-2026-10-17-r2) is public at source commit `58fbe631bda2efcc23563be0958c3f403e4a6361`. The [release workflow](https://github.com/occult-kranti/ANDOLAN/actions/runs/39002862685) succeeded: 13 build steps and six release steps, with no failed or skipped steps. The first tag's failed prerequisite setup remains separately recorded; this release uses a new tag.

All **26 project-uploaded assets** were independently downloaded through their public URLs. Their byte lengths, SHA-256 hashes and complete checksum inventory pass verification. GitHub additionally lists its two automatic source archives. `public-download-review.json` records the downloaded assets, and `release-manifest.json` plus `SHA256SUMS` preserve the published inventory. ZIPs and the movie are linked from the release rather than duplicated in this evidence folder.

| Published asset | Bytes | SHA-256 |
| --- | ---: | --- |
| Linux ZIP | 93,699,595 | `f00459d6977ef8c56e60bc602f0689fd9647bf588b1e7f8dfeacf411209a27a6` |
| Windows ZIP | 101,700,882 | `35158a8a22b8439d14c4cbccac3347fbd67d68452f203b41b70adf26bebc093a` |
| Movie | 2,719,092 | `9bb618a6d7b8edc37f798ca05869ba5eeaac2f88fd6e0543a4ae778aaf960544` |

## Actual published Linux execution

The downloaded Linux ZIP was extracted into a fresh directory. ZIP CRCs and all 14 payload hashes passed before its bundled engine was launched with the bundled PCK. The PCK is `0671f9a6558eeac6709f1ab31c1b60d44f0e1ff448bf673a2ace7fe3ffe353c0`; this is the published build, not the earlier locally packaged build.

`input-review.json`, sixteen actual window captures, `game-log.txt` and `published-linux-window-review.json` record these bounded outcomes:

- Title opens and Watch Confluence Duel enters the film.
- Space pauses; Right seeks one second ahead; Left restores the exact same paused image.
- Seeking to 15.8 seconds shows the projectile before impact and Ravana at 100 health; 16.6 seconds shows a standing recoil and 55 health.
- Replay restarts, and Escape returns to the title.
- Settings saves volume zero; re-entry plays the visual timeline with `muted: true` and the soundtrack player stopped.

Capture names describe the intended action, not an automatic pass. Captures 01 and 02 show the cold engine splash; 03 shows the loaded title. Capture 12 precedes the settings transition; 14 confirms Settings with volume zero. Capture 16 still shows the film during the final Courtyard-button return transition; cleanup followed before a title capture, so that button return is **not claimed verified by this run**. The earlier local-package review and fresh CI callback checks remain separate evidence. The helper intentionally terminated its owned game after review; exit −15 records cleanup. No unexpected engine errors or warnings occurred.

This run used Forward+ on llvmpipe and Dummy audio. It does not measure consumer-GPU frame rate or establish sound quality by listening. Windows was archive-validated but not executed.

## Rebuild comparison and CI checks

`pack-comparison.json` independently explains the published PCK's 32-byte size difference from the earlier local package. Of 178 entries, 169 are identical. The remaining nine imported scenes differ through 57 generated node identifiers and two mangrove leaf tangent-basis angles, each one unsigned-16-bit step (at most 0.005493 degrees). Positions, topology, skinning, materials, animation curves, scripts and audio match. No decoded differences remain unexplained. The exact size change is −5 compressed payload bytes and −27 alignment-padding bytes. These are classified differences, not a claim of byte-identical art.

The downloaded CI reports pass 20 script/resource, 42 film integration, five motion-continuity, 32 VFX, 22 audio/focus, 18 native, 25 world-scene, 13 world-flow and 30 lighting checks. CI also verifies the frozen movie archive and independently decodes the movie/audio. It does not rerender the movie. `ci-public-status.json` records the independent public workflow-page inspection; two Node-version warnings are nonblocking.

This release contains a scripted two-actor film, offline world explorer and training preview. It does not complete the full roster, native multiplayer, production physics or the commercial visual target. Sparse scenery, simple character/material finish and floor aliasing remain visible.
