This native preview concentrates on one playable Rama: a new editable, skinned 3D character, 23 authored animation clips, and one shared combat kit in bow training and three-lane Confluence practice.

- **LMB — Kodanda:** a timed bow draw and shot.
- **Q — Piercing Dawn:** a committed piercing arrow; cover stops it.
- **E — Measured Step:** a short movement with collision.
- **C — Guardian Circle:** a visible field that shields and heals eligible allies and Rama.
- **X — Dawn Volley:** three paced, telegraphed firing lanes.

R reloads, F/G fly and grapple, F3 shows the actual ability guide, F2 opens Help in the title/training scene and saved key remapping in Confluence, Escape pauses, and F5 resets practice. Hero health, siege damage, defeat and respawn use the authoritative gameplay clock; effects and HUD reflect accepted state. The title displays the actual rigged hero.

Download the Linux or Windows ZIP, extract the entire folder and run `launch.sh` or `launch.bat`. No Godot editor installation is required. Vulkan is the default; the launcher accepts `--rendering-method gl_compatibility` as a fallback. The packaged engine is Godot 4.6.3.

The animation and ability MP4s show actual software-rendered game assets. Their encoded frame rates describe sampled simulation, not measured real-time performance. The motion reel is staged; the five-ability reel uses separate deliberate takes with resets between them.

This is an **offline single-hero preview**. It does **not** meet Deadlock/Overwatch concept-quality production art. Hair, secondary cloth motion, facial expression, authored LODs, full-match balance, native multiplayer and physical-GPU profiling remain open. Windows is packaged and archive-validated but has not been executed here. The older duel film and legacy invocation studies retain their separate scope.

Packages were exported from clean release source `9eb6323ef20d8f10436a893ffcd434096686247a`. All 352 runtime files are verified against that commit. Manifests and SHA256SUMS identify the downloadable bytes.

[Build, controls and handoff](https://github.com/occult-kranti/ANDOLAN/blob/game/yuga-native-production/games/yuga-native/docs/RAMA_HERO_MILESTONE.md) · [Independent acceptance and limits](https://github.com/occult-kranti/ANDOLAN/blob/game/yuga-native-production/games/yuga-native/docs/RAMA_HERO_ACCEPTANCE.md)


Validation: [full native CI passed](https://github.com/occult-kranti/ANDOLAN/actions/runs/39036000777). Local checks include 138 actual-world integration assertions, 85 focused combat cases and 9 critical-HUD regressions, recorded continuous motion, and actual Linux mouse/keyboard screen reviews at 960 × 600 and 1280 × 720. Settings entry clipping was reproduced, corrected and reviewed at both sizes. After the final HUD/field correction, the new Linux package received a focused 960 × 600 title/world/Guardian/pause/reset smoke; the unchanged broader settings and remap flows retain their prior source-pinned reviews. Closing title Settings currently focuses Bow training.

This is a manually published prerelease backed by the linked native foundation CI run and the archived local package/render reviews. The browser game and prior native releases retain their separate scope.
