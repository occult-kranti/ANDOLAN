# YUGA · Sanctum — hero and map build

Task `YUGA-TACTICAL-FINISH2`, native product. First-person 5v5, first team to 13 wins, sides switch after round 12. Mythic firearms and four hero powers; local Casual with one human and nine bots. Ranked remains planned. This successor integrates the authorized shop/HUD and hero/map streams.

## Artifacts

Linux and Windows archives are built from the same frozen source; both passed CRC and payload SHA checks. The exact Linux archive passed a normal mouse/keyboard route through the default title, hero inspection, Casual deployment, purchases, movement, firing, finite reload, veil, pause, menu return and native Quit (exit 0). Windows execution is not run here.

- [Linux build](../../../../../dist/sanctum-finish2-r1/yuga-native-linux-x86_64.zip): extract and run `launch.sh`.
- [Windows build](../../../../../dist/sanctum-finish2-r1/yuga-native-windows-x86_64.zip): extract and use the included launcher.
- [Source and editable art archive](../../../../../dist/sanctum-finish2-r1/yuga-sanctum-source-art.zip).
- [Native screenshot gallery](../PREVIEW.html)
- [Native gameplay rehearsal](final-motion-r1/tactical-casual.mp4)
- [Raea CPU weapon turntable](raea/surya-cpu-orbit-r3.mp4)
- [Distributed ownership and roadmap](README.md), [continuation order](../ROADMAP.md), [user requests and decisions](../PROMPTS.md)
- [Editable SURYA source and generator](../../../art/tactical/surya-carbine/README.md), [Raea compositions](../../../art/tactical/raea/README.md)

Raea is a separate CPU rendering tool. The interactive game, hero viewer, weapons, effects and map run in Godot. The Raea video is not presented as native gameplay.

## Implemented changes

**Hero.** Original detailed SURYA carbine with separate magazine, authored recoil/reload/ADS and articulated first-person utility hand. Q throws the veil, C raises the ward, E braces the dash, and X charges/releases three solar shots. Authority accepts the cast before presentation starts. Pause freezes its clock; death and round reset clear it. The corrected hand return drops below view before the supporting grip reappears.

**Hero inspection.** Native 3D Rama holding the actual SURYA model, front/back buttons, drag rotation, wheel zoom and keyboard controls. Reuses the accepted skin, authored pose library, rig adapters, material finish and cloth resources. The old bow is hidden; merged quiver geometry is removed only from the inspection instance, preserving the canonical asset. Contact shadows and restrained fill lighting give the body and cloth more form.

**Map.** Shared sandstone, indigo glaze and brass material treatments; masonry courses, framed panels and original beveled Lotus reliefs. All 62 physics bodies retain their earlier shapes, transforms and layers. Decoration is batched into three material groups and stays within existing occupied solids or nonblocking overhead space. Existing two-site routes, buy barriers, cover and objective interaction remain functional.

**Effects and interface.** Animated veil settling keeps the authoritative sight-blocking boundary visible from onset. Thin fading dash/ward pulses and shorter solar traces improve separation. Complete existing menu, Casual selection, hero, help/settings, buy HUD, guide, scoreboard, pause and outcome flows remain integrated.

## Focused evidence

- [94 hero checks](hero/checks-r3.json): cast interruption, frame-rate sampling, finite poses and projected hand return boundaries.
- [33 world checks](world-final-r1.log): physical hits/cover, sight blocking, purchases, finite reload, pause, accepted/rejected casts, death/reset. Map relief correction afterward is presentation-only and has its own preservation check.
- [Map preservation](map/authority-preservation-r2.json): 62 identical physics signatures; 42,700 relief vertices checked, none outside the permitted envelope; 20,296 decorative triangles in three batches.
- [Hero viewer review](ui/visual-acceptance-r2.json): three actual native originals at 1280×720 and 960×540, including front/back. Focused viewer/lifecycle checks are retained under [UI](ui/README.md).
- [Raea receipt and samples](raea/): official 0.1.5, software Vulkan driver observed in process; 72 frames, six seconds, 960×540 at 12 fps, 13.379 seconds elapsed. Six extracted samples visually reviewed. These are CPU render measurements, not game FPS.

- [Final map review](map/visual-review-final-r1.json): five full-resolution originals, corrected Lotus silhouette and unchanged routes. Relief remains shallow from straight on.
- [Final UI review](ui/final-ui-review.json) and [gallery check](ui/preview-final-r1/receipt.json): all 22 native originals reviewed; 25 images and both videos load, 8/8 gallery checks.
- [Actual cast review](hero/final-motion-review-r1/review.json): all 180 advancing originals viewed on contact sheets and 33 full-resolution originals. The casting hand leaves view before the support grip returns. The support grip still restores in one frame; this is not continuous anatomical regrip.
- [Final staged combat](final-motion-r1/motion.json): 180 actual native frames, 18/18 behavior checks, unchanged sources/imports. [Encoding](final-motion-r1/encoding.json) records a silent 12-second MP4; fixtures fund purchases/ultimate and suspend bot decisions while receivers, physics and effects remain real.

- [Exact packaged Linux input](package-input-r1/review.json): 37 ordinary input/capture events, 14 originals personally reviewed, exit 0 and no engine warning/error lines. Temporary initial hero shader loading and the real match loading page are preserved. First-round ARKA was used; SURYA is reviewed in the exact package hero viewer and actual game film.

The initial casting pop, flat Lotus motif, quiver and lighting findings are preserved with their rejected probe sources and captures. Earlier full-match/input evidence stays pinned to its earlier source; it is not recounted as new finish2 coverage.

## Source and resumption

Base commit `143289f410ef17ced20d0546efc7fccafee75ba9` on `work/yuga-studio`, plus the recorded dirty changes. Runtime source SHA256 `b682eb7355b4bef4441e943fd007ecd3fc85be371a30dafe59770011f5702055`. Frozen source: `.local-tools/review/sanctum-finish2-r1`. [Snapshot](package-r1/SOURCE_SNAPSHOT.json) and [full closure](package-r1/SNAPSHOT-MANIFEST.json) distinguish this build from the older public checkpoint and [prior art build](../ART_DELIVERY.md).

Changed runtime files: `scripts/tactical_weapon.gd`, `tactical_cast_motion.gd`, `tactical_world.gd`, `tactical_effects.gd`, `tactical_frontend.gd`, `tactical_hero_showcase.gd`, `tactical_map.gd`, `tactical_architecture_details.gd`; tactical veil/pulse/architecture shaders; SURYA art and the tactical content manifest. Supporting changes cover focused checks, captures, Raea compositions/CPU runner, build manifest and notices. Exact hashes are in the snapshot and subsystem handoffs.

Package hashes: Linux ZIP `d37c45fa148dcda2f5e87ceba608784cd872b1e0e454e4f61c27a523d606289d`; Windows ZIP `3e94fa33714e0c497f15c23af0f94762a7660cf97c9ef7bd57cf263a7cd43633`. [Package manifest](package-r1/native-package-manifest.json) and [command](package-r1/build-receipt.json).

Root owns integration and delivery. The next art owner should refine full-body tactical locomotion, weapon contacts, face/hair and the simple bot wardens before expanding the roster. The next gameplay owner handles human balance/feel feedback; the online owner handles authoritative servers and two real clients before Ranked. Browser/mobile remain deferred. The first Linux hero-view capture was temporarily black while software-renderer shaders compiled; later front/back/drag views rendered correctly. This startup delay is retained in the ordinary-input record. Software-rendered visuals do not establish commercial art parity, consumer-GPU performance or listening acceptance.
