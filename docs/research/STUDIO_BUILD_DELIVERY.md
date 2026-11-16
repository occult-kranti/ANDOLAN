# Studio candidate delivery — 15 November 2026

The native YUGA successor is built from frozen runtime source digest `9a83ab6de5dbed60934de4f6288570434709af6a2c8a67405b6730592d4a2ff5`. It adds the practice briefing, preserves all footer actions at tighter logical sizes, consolidates the shared gate/garden textures, and includes a separately launched original Relay Foundry exploration blockout. It is a bounded production increment; the full competitive game remains in the production plan.

## Local artifacts

All paths are relative to the repository root. Exact SHA-256 values and byte counts are in [the current artifact manifest](evidence/studio/artifacts.json).

| Artifact | Location | Verification |
| --- | --- | --- |
| Native Linux r2 | `dist/yuga-native-linux-x86_64.zip` | 105,458,408 bytes; 50 ZIP entries; every CRC/payload hash checked; actual title and corrected map, native Quit 0 |
| Native Windows r2 | `dist/yuga-native-windows-x86_64.zip` | 153,755,332 bytes; 39 ZIP entries; every CRC/payload hash checked; Windows execution unrun |
| Browser YUGA | `dist/yuga-confluence-browser-beta.zip` | 24,855,816 bytes; 21 model assets match source manifests; actual local bot practice, hero viewer and settings |
| Combined mechanics lab | `dist/yuga-lab-studio.zip` | All 22 build payloads checked |
| Lane mechanics lab | `dist/yuga-lane-lab-studio.zip` | All 22 build payloads checked |
| Control mechanics lab | `dist/yuga-control-lab-studio.zip` | All 22 build payloads checked |
| ANDOLAN city standalone | `dist/standalone/index.html` | 2,478,963 bytes; actual title and separate city regression/build checks |

Both native packages contain the identical 568-entry, 78,220,136-byte PCK, SHA-256 `035961b81f0bd13b6e19bafa5879fbba1f88206526d3542337d1af5fb4add812`. Linux uses the verified public-source Godot 4.6.3 template with the existing one-line pipeline-priority patch; its source/build/license proof closure is bundled. The exporter and Windows runtime remain official pinned Godot builds. No performance advantage is inferred from unequal startup observations.

Extract the complete Linux ZIP. The tested software-rendered cloud launch is:

```sh
./launch.sh --rendering-method gl_compatibility
```

Launch the separate map study from the same extracted folder:

```sh
./launch.sh --rendering-method gl_compatibility res://scenes/studio_map_study.tscn
```

Map controls: WASD, Shift, Space, hold RMB to orbit, O for overview, R for spawn and Escape to quit. Its relays are landmarks without capture/combat authority. For a browser ZIP, extract all assets beside `index.html`, run `python3 -m http.server 8080 --bind 127.0.0.1`, then open `http://127.0.0.1:8080/`.

## Verification and original images

- [Exact r2 execution review](evidence/studio/final-r2/execution-review.json): title and map using the actual extracted Linux runtime/PCK, both native Quit 0, no engine/script errors, all 576 runtime source files and both archives unchanged afterward.
- [Qualified r2 title](evidence/studio/final-r2/title-retry/01-title-retry-ready.png), [map ground](evidence/studio/final-r2/map/01-r2-map-ground.png), [map overview](evidence/studio/final-r2/map/02-r2-map-overview.png).
- [Native export and package identities](evidence/studio/package/native-package-manifest.json), [embedded studio resources](evidence/studio/package/embedded-studio-resources.json), and separate independent review.
- Browser gates: YUGA typecheck/225 tests, labs 21 tests, city typecheck/134 tests, root lint and every listed build pass. [Actual five-route/eight-screen browser review](evidence/studio/browser-build-review.json) reports zero page/request errors.
- Initial native baseline: 47 screen suites/971 checks, 279 native contracts, 85 ability checks and 58 source pins. Later scoped launcher/resource/map checks bind their own final source; the baseline is not relabeled as a complete rerun of the successor.

The first native package has a broader ordinary training/world/settings/help/guide/overview journey. Its original map lighting failed visual review; those packages, manifests and images remain preserved. A separate recovered-runtime probe rendered the first candidate’s actual Forward+ title/world and exited 0. The successor’s exact title/map acceptance here is explicitly Compatibility rendering. The first r2 title cleanup ended -15 after premature tool cleanup; the separate keyboard-Quit retry passed and retains the failed observation.

Physical-GPU performance, human feel/listening, Windows execution, full native online matches, the full hero roster and commercial-game visual quality remain open. Research downloads and generated concept boards retain their separate scope from executed game builds.
