# YUGA studio delivery — 15 November 2026

An original playable development checkpoint, built on `work/yuga-studio` from
native-production `7162b5d0`. New source is uncommitted and bound by file hashes
and export manifests; the pre-existing seven-line package-lock change is preserved.
Nothing was pushed or published. This does not replace the earlier public preview.

## Play or inspect the new work

| Deliverable | Local artifact / evidence |
| --- | --- |
| Native Linux game + separate map study | [Linux ZIP](../../dist/yuga-native-linux-x86_64.zip) |
| Native Windows package | [Windows ZIP](../../dist/yuga-native-windows-x86_64.zip); archive validated, Windows execution unrun |
| Browser YUGA arena | [Browser ZIP](../../dist/yuga-confluence-browser-beta.zip) |
| Combined mechanics lab | [Combined lab ZIP](../../dist/yuga-lab-studio.zip) |
| Lane-economy lab | [Lane lab ZIP](../../dist/yuga-lane-lab-studio.zip) |
| Hybrid control lab | [Control lab ZIP](../../dist/yuga-control-lab-studio.zip) |
| ANDOLAN City Reform | [Standalone HTML](../../dist/standalone/index.html) |
| Editable original Blender map | [relay-foundry.blend](../../games/yuga-native/art/studio-map/relay-foundry.blend) · [build/export/physics record](../../games/yuga-native/art/studio-map/README.md) |
| Implemented native launch screen | [Final extracted-package title](evidence/studio/final-r2/title-retry/01-title-retry-ready.png) · [Bow training presentation](evidence/studio/briefing-training.png) · [ability guide](evidence/studio/briefing-guide.png) |
| Corrected native map appearance | [Final package ground view](evidence/studio/final-r2/map/01-r2-map-ground.png) · [overview](evidence/studio/final-r2/map/02-r2-map-overview.png) |
| Actual browser gameplay | [YUGA practice](evidence/studio/browser-yuga-practice.png) |
| AI art-direction boards | [Twenty representative screens across three boards](../concepts/studio-2026-11-15/README.md), explicitly marked as concepts |
| Silent screen review | [40-second MP4](../../dist/studio-static-screen-review.mp4): labeled static original captures, not advancing gameplay/animation footage |
| Complete design continuation | [Game, story, modes, maps, roster, code and release roadmap](../../games/yuga-native/docs/STUDIO_PRODUCTION_PLAN.md) |

Extract the entire native ZIP. On Linux, `./launch.sh` uses the default Forward+
renderer. For this cloud's software renderer use the tested explicit fallback:

```sh
./launch.sh --rendering-method gl_compatibility
./launch.sh --rendering-method gl_compatibility res://scenes/studio_map_study.tscn
```

On Windows, extract everything and run `launch.bat`; this platform is packaged
but has not been executed here. The new map is a separate exploration scene,
not another Confluence combat mode. Browser ZIPs need all external model files
and an HTTP server. Practice runs locally; online modes require a configured
compatible server. These builds do not provision public matchmaking.

For source development:

```sh
bash tools/cloud/setup-studio.sh --help
bash tools/studio/launch-native.sh --compatibility
bash tools/studio/launch-native.sh --map --compatibility
blender4.3 --background --threads 8 --python tools/studio/build_relay_foundry.py
```

## Concrete implementation

- **Native launch guidance:** the live Rama model and original indigo/ivory/gold
  system remain. A read-only mode schematic, first-action hint and five actual
  remapped bindings occupy spare desktop space. Smaller/enlarged layouts preserve
  essential offline context, primary action, scroll and focus. Mode selection,
  loading locks, recovery and exact utility-return focus keep their existing owners.
- **Exact texture reuse:** the existing gate and garden now share twelve exact
  texture resources instead of twenty-four. Replaced originals are released;
  decoded storage falls by **9,437,184 bytes (9 MiB)**. Source assets, pixels,
  material settings, transforms, geometry and collision are preserved. This is
  not a VRAM or frame-rate measurement.
- **Original Blender map:** Relay Foundry is a 132×190 m three-lane blockout with
  side rotations, cover, mirrored bases, three relay landmarks and a six-metre
  crossover with two ramps. The standalone native walker supports movement,
  running, jump, camera orbit, overview, reset and quit. There are 163 meshes,
  12,588 triangles, eight materials and 101 colliders. It has no combat/capture
  rules or shared Confluence authority; it is a playable map-design prototype.
  Actual native review rejected the first overexposed lighting. A source-only
  lighting correction restored tan/teal/amber surfaces; clipping in the matched
  HUD-excluded view fell from 88.65% to 0.29%. The metric supports the image
  review; it is not a general art-quality score. Fine paving/shadow banding remains.
- **Reproducible tooling:** installed/qualified Godot 4.6.3, official Blender 4.3.2,
  FFmpeg, Mesa/Xvfb/XTest, Python authoring wheels, Playwright Chromium and ripgrep.
  REA 6.5.0 analyzed an owned TypeScript module. No persistent MCP integration
  was registered. [Toolchain setup and evidence](STUDIO_TOOLCHAIN.md).
- **Reviewed source preparation:** fifteen canonical repositories have pinned
  revisions and reuse decisions. REA, script-only GDQuest TPS, Rapier and
  HyperFrames sources were prepared and license-checked in an ignored tooling
  directory. This is source research, not four new game-engine integrations.
  [Catalog](../../tools/research/opensource-catalog.json) ·
  [reusable preparation CLI](../../tools/research/prepare-open-source.py).

## Two expert-panel rounds

All ten remote branch heads were checked against the live remote and audited
by tree/diff/product inventory. Critical README, handoff, design, runtime,
asset, test and recovery documentation were read. This is not a claim that every
historical binary or archived image in the 24,000-file production branch was opened.

| Round | Researcher 1 | Researcher 2 | Build / integration |
| --- | --- | --- | --- |
| 1 | [Game reimplementation and branch study](panel-round1-games.md) | [Renderer/tool/license study](panel-round1-tools.md) | [Repository architecture and baseline](panel-round1-build.md) |
| 2 | [Native design, source catalog and counterexamples](panel-round2-games.md) | [Prepared tooling and actual REA use](panel-round2-tools.md) | [Build/artifact/browser execution](panel-round2-build.md) |

The two research streams reviewed sixty Exa search-result slots, then primary
repositories/license files. Result slots include duplicates; this is not sixty
unique tools. The panel corrected Raea's current FSL classification, separated
REA/Raea/rea-video, distinguished Prometheus from a standalone game, and rejected
the assumed unrestricted GDQuest art license. Prometheus is AGPLv3, OWLib MIT
and OWM GPLv3; no commercial client or extracted proprietary art was installed.

Independent reviews cover [implementation/counterexamples](panel-round2-independent-review.md)
and [actual launch originals](panel-round2-final-review.md). N4's author-owned
[resource report](panel-round2-resource-reuse.md) is explicitly not an independent
self-certification. Root reviewed the code, material/collision evidence and originals.

## Verification and exact scope

| Check | Executed result |
| --- | --- |
| Original native baseline | 47 screen suites / 971 checks; 279 native contracts, 85 Rama-ability checks and 58 source-pin checks passed before the new edits |
| Changed launcher regressions | Final seven relevant suites / 161 checks passed, including 14 new briefing checks and the clipped-footer counterexample at tight logical sizes; eight independent earlier adverse checks also passed |
| Component recovery/native input | Six actual XTest captures: both modes, keyboard focus, real missing-scene error, retry and back; exact source pins retained |
| Resource reuse | 20 new real-resource checks and 31 existing world-integration checks passed; one mutable-image adverse precondition unrun on the headless backend |
| Blender/map | Seven build/manifest gates and nine actual Godot physics checks passed, including capsule ascent/descent, jump/landing, underpass and bounds |
| Browser code | City 134 tests, YUGA 225 tests, labs 21 tests; typechecks and root browser lint passed |
| Browser runtime | Five built routes/eight original captures; zero page/request errors; includes actual local bot play |
| Source-preparation helper | Seven original guard cases plus eight additional schema/path cases passed; all four actual source checkouts reverified |
| Native packages | Linux/Windows archive CRC, payload hashes, fonts/notices and actual PCK resources verified; common PCK has 568 entries. First candidate integrity passed but map appearance was rejected; its exact archives/manifests are preserved separately. |
| Final extracted Linux successor | Qualified actual title, keyboard focus/Quit 0 and corrected map ground/overview/Escape Quit 0 with the selected runtime. The earlier title cleanup -15 remains separate. All 576 packaged runtime source files match the final source manifest. |

The original root lint failure traversed external research sources and historical
native authoring/evidence code. Explicit exclusions now keep browser lint within
its product boundary; native code uses its own Godot/Python gates. Failed first
layout/fixture/build attempts and the corrected successful runs are retained.

[Current artifact hashes](evidence/studio/artifacts.json),
[browser artifact hashes](evidence/studio/browser-artifacts.json),
[native export/source manifest](evidence/studio/package/native-export-manifest.json),
[native package manifest](evidence/studio/package/native-package-manifest.json),
[changed-source hashes](evidence/studio/changed-source.json),
[branch audit](evidence/studio/branch-audit.json),
[final consistency check](evidence/studio/final-consistency.json) and the evidence subdirectories
bind the work. The first candidate's full ordinary journey and the final
successor's title/map checks retain separate PCK identities. See
[final extracted-package execution](evidence/studio/final-r2/execution-review.json).

The official Forward+ runtime remained on the preparing-scene overlay during a
53-second llvmpipe attempt before termination. The recovered, checksum-verified
public-source runtime subsequently reached the actual title around 90 seconds
and world around 165 seconds with the current first-candidate PCK, then exited
through native Quit. Different observation windows do not establish that the
patch is faster or universally fixes startup. Its one-line pipeline-priority
change and exact source/build/license proofs are retained in
[runtime recovery](evidence/studio/public-runtime-source.json).

Explicit Compatibility also ran the actual Linux title, settings/help/guide,
training, pause, world and overview, then native Quit. Frames that captured
loading or an unactivated choice are labeled in the frame-review receipt; they
are not counted as completed gameplay. A separate map run exercised movement,
overview and native quit. Expected reduced-feature warnings are retained.
Software-render timing does not establish physical-GPU frame rate or commercial
visual quality. Final successor-package execution is recorded separately and
passes its title/keyboard Quit and map/overview/quit scope. Windows remains unrun.

## Credits and next production exit

[Studio credits](../../games/yuga-native/NOTICE/STUDIO_SOURCES.md) accompany the
existing native asset/font/engine notices in both packages. The new map geometry
is original Blender authoring; no researched proprietary assets or GDQuest art
were imported. Prepared source references remain separate from runtime content.
The concept boards' invented controls, effects, roster/prices and server address
are documented as rejected generated details; actual kit/rule data stays authoritative.

The playable native hero remains Rama. The full roster, authoritative native
matches, final character/world art and continuous motion, operated online services,
Windows execution, listening/human balance and physical-GPU qualification are
unfinished. The [production plan](../../games/yuga-native/docs/STUDIO_PRODUCTION_PLAN.md)
defines the ordered exits to a final 6v6 game. This checkpoint does not alter the
historical 17/78 accepted-packet or 0/13 complete-production-round counts.
