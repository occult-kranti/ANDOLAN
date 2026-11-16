# Sanctum art build · 15 November 2026

Task `YUGA-TACTICAL-CASUAL-13`, native product, artifact `sanctum-art-r1`. This completed local checkpoint contains the first-person mythic-firearm Casual game: 5v5, first to 13, halftime after round 12, two Astra sites and local bots. The subsequent Raea/CPU hero-and-map finishing request continues in [the distributed roadmap](finish2/README.md). It does not change these packages.

## Delivered artifacts

- [Screenshot gallery and film](PREVIEW.html): 22 original native images and a labelled 12-second scripted rehearsal.
- [Linux package](../../../../dist/sanctum-art-r1/yuga-native-linux-x86_64.zip),119,632,289 bytes. Extract and run `launch.sh`.
- [Windows package](../../../../dist/sanctum-art-r1/yuga-native-windows-x86_64.zip),167,928,935 bytes. Extract and use the included launcher; Windows execution is unrun here.
- [SURYA authoring kit](../../../../dist/sanctum-art-r1/surya-authoring-kit.zip): editable Blender source, GLB, original reference, exact prompt, generator and notices.
- [Native motion MP4](evidence/motion-r1/tactical-casual.mp4), [controls](README.md), [prompts](PROMPTS.md), [roadmap](ROADMAP.md).

Default entry: `scenes/tactical_frontend.tscn`. The older [published tactical checkpoint](PUBLICATION_2026-11-15.md) and classic practice packages retain separate source identities.

## Implemented art and game

Root implemented first-person movement, real firearm/ammunition/reload/ADS behavior, effect/audio consumers, world integration, capture/build helpers and entry point. Combat owns round authority, economy and autonomous bots. UI owns native menu/loading/hero/settings/help/HUD/shop/scoreboard/pause/outcome flow. World/art integrated the compact Sangam map and original SURYA firearm.

Sangam reuses original civic geometry with paving, sky/reflection/haze, shadows, stalls, planted edges, overhead galleries and background architecture. The generated original menu illustration is installed. A second generated image guided a separately authored SURYA model:185 editable parts,2 runtime meshes,14 primitives,11 materials and79,804 triangles. Its separate magazine, first-person hands, recoil and corrected ADS are integrated. Generated images are reference/key art, not playable geometry.

Changed runtime families: `scripts/tactical_*.gd`, `scenes/tactical_*.tscn`, `assets/tactical/`, `shaders/tactical_*.gdshader` and `project.godot`. [Frozen source hashes](evidence/package-r1/SOURCE_SNAPSHOT.json), [packaged inventory](evidence/package-r1/native-package-manifest.json), [artifact source](../../art/tactical/surya-carbine/README.md). Generators/editable art remain in existing `tools/studio/` and `art/tactical/` paths.

## Review and focused checks

- Rules/bots:53 and21 focused checks. Prior natural full matches remain in [combat](combat/README.md) and the separate publication record, with their own source identities.
- World:27 checks of physical hits/cover, smoke sight blocking, purchases, finite reload, pause, death and reset. [Final log](evidence/checks/world-r4.log).
- Native visuals:19 R3 originals, then6 final R4 firearm views. Owners reviewed UI/map; root and artist inspected imported SURYA, ADS and reload. [Weapon review](../../art/tactical/surya-carbine/native-review-r4.json), [map review](research/map-final-review-r2.json). Rejected R1 originals remain preserved.
- Motion:all180 consecutive frames reviewed, including16 full-resolution keyframes;17/17 behavior checks and unchanged sources. Declared purchase/ultimate fixtures and disabled bot decisions; real receivers/physics/effects. Silent,15 simulation frames/second, not hardware FPS or natural gameplay. [Review](combat/motion-r1-review/review.json), [encode](evidence/motion-r1/encoding.json).
- Exact Linux ZIP extracted and run with no scene override:title→Casual→deploy→buy→move/aim→live fire→finite reload→veil→pause/settings→menu→native Quit(exit0). All15 original screenshots reviewed; no engine error/warning lines. [Ordinary input](evidence/package-input-r1/review.json).
- Both archives passed CRC/payload SHA validation. Gallery13 checks:all22 images and video load; desktop/narrow originals reviewed. [Receipt](ui/preview-final-r1/receipt.json).

## Source identity

Frozen dirty art changes atop **`d541dbcff7273fffa464660f7e46f674ed1600b5`** on `work/yuga-studio`. Runtime-source SHA256 **`79e2d0e05c31b5491fc6b950eeadb8fe9ae8781c733ba0118706ee44f85fc325`**. Snapshot `.local-tools/review/sanctum-art-r1`; later live edits do not enter these artifacts. [Exact build command](evidence/package-r1/build-receipt.json).

| Artifact | SHA256 |
| --- | --- |
| Linux ZIP | `260ad4b4a8f024e36ec6829b1da53b5d37f16865251f97e64d326569ceadef9b` |
| Windows ZIP | `bbe0205f852186e309bf3119088a3a01394eb6dd8711aaff17fe98c9c007023a` |
| SURYA authoring ZIP | `f5dabbbc138a35f72c73854b190c0e684ffd916eabe374496423a9dc5c8ad334` |
| Native MP4 | `728fcba61271f3cbc45f0427ba4b074b367a98e70d3a20fa76b435ab949c4438` |

## Remaining work and next owner

Simple third-person wardens, repeated modular facades, simpler pistol/hands and absent dedicated Q/C casting remain visible. Veil entrance, dash-ring finish and X windup need refinement. The next owned pass targets these defects with shared material/motion modules, preserving confirmed match rules.

Casual is local. Ranked, online, full-body tactical Rama and wider roster remain production work. Browser/mobile are deferred. Software rendering and archive validation establish no commercial art parity, consumer-GPU performance or human feel/listening acceptance. Root owns integration/delivery; [finish2](finish2/README.md) records distributed ownership.
