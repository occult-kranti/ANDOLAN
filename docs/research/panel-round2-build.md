# Panel round 2 — build execution review

Date: 15 November 2026. Code/build lane after the panel selected native YUGA as the hero-game baseline. The current working branch is `work/yuga-studio`, restored from production `7162b5d0`; the pre-existing package-lock diff is preserved.

## Concrete outputs already verified

- Live remote branch verification confirms all ten remote heads match the audited local tracking refs.
- Godot 4.6.3 official Linux/Windows archives and extracted payloads match repository SHA-256 pins. Linux starts/imports/exports. Windows is not executed.
- Blender 4.3.2 portable matches the native authoring baseline and its official release checksum; factory-startup Python check passes. Ubuntu Blender 4.0.2 is also installed. No game art was re-exported by this lane.
- Native initial baseline: source pins 58, native contracts 279, Rama abilities 85 and complete screen catalog 47 suites/971 assertions pass. These tests ran before root briefing/N4 resource edits and retain source hashes.
- Browser YUGA typecheck and 225 tests pass; mechanics labs 21 tests pass; city typecheck and 134 tests pass. Production/standalone city, YUGA browser and all three mechanics-lab tracks build successfully.
- Root lint initially traversed new source-only research clones and historical native evidence/minified tools. Root approved explicit `.local-tools/**` and `games/yuga-native/**` exclusions, keeping native validation with its own Godot/Python runners. Root lint then passes; scoped browser lint also passes.
- YUGA browser package includes 21 model assets matching both source manifests. Three lab ZIPs independently pass CRC and every payload SHA-256. [Artifact identities](evidence/studio/browser-artifacts.json) identify exact local files.
- Actual built-browser route capture covers five products/eight screens, including local bot play, hero viewer and settings, with zero page/request errors. [Route record](evidence/studio/browser-build-review.json) and [screens](evidence/studio/browser-yuga-practice.png) retain real presentation.

## Native runtime finding and delivery decision

Official Forward+ on current llvmpipe emits native-ready but remains on preparing-scene overlay through the recorded 53-second attempt. This matches the historical documented reason for a custom pipeline-priority runtime; the current failure is retained separately, not claimed as successful art review.

Explicit compatibility rendering opens the actual native title. The original ordinary title review exits via native Quit with code 0. Expected unsupported VSync/subsurface warnings are retained. Final compatibility captures will bind the combined source after root launcher, N4 resource and standalone map changes freeze. This is reduced-effects software execution, with no consumer-GPU performance or Forward+ art acceptance claim.

## Recommendations adopted

Retain existing engine/gameplay; reuse accepted native resources; improve one legible launcher behavior; consolidate duplicate resource allocation without changing image pixels; produce a separately labeled original map prototype; package actual game builds and retain real screenshots. Research extractor/renderer repos remain isolated tools, with per-source licenses and separate adoption decisions.

Do not claim that two expert rounds, a generated image, source downloads, headless assertions or an isolated map are a complete commercial game. Full native online matches, full roster, sustained hero art/motion, hardware qualification and human balance/listening remain production gates.

Final successor packages and exact Linux execution are now complete: [build delivery](STUDIO_BUILD_DELIVERY.md), [current identities](evidence/studio/artifacts.json) and [r2 execution](evidence/studio/final-r2/execution-review.json). The first rejected map appearance and premature title cleanup remain separately retained; the accepted successor does not relabel those attempts.
