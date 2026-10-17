# YUGA native build handbook

Read this in 5–10 minutes before changing the native game. Start with the repository [START_HERE](../../../docs/START_HERE.md), use this handbook for execution, and read the [research brief](research/RESEARCH_BRIEF.md) only when the task needs design/source context. Do not load every historical report to begin a small change.

All commands below run from the repository root, normally `/workspace/ANDOLAN`. Paths in the file table are relative to `games/yuga-native/` unless stated otherwise. This handbook was checked against source and tool `--help` on 17 October 2026; it does not replace a fresh test result.

## 1. What exists, and what we are building

Current source work is the [Rama hero milestone](RAMA_HERO_MILESTONE.md): a new smooth-skinned `rama-hero.glb`, editable Blender source, one full-body motion controller, five fixed combat actions, real health/respawn, and shared training/world screens. Start with that document and its [acceptance record](RAMA_HERO_ACCEPTANCE.md). `rama_hero_runtime.gd` is the integration entry; `rama_ability_kit.gd` owns the 20 Hz combat timing. This is still an offline native milestone; production art, hardware performance and online matches remain separate gates.

The following Mythic and Triad releases are historical. [MYTHIC_BATCHES.md](MYTHIC_BATCHES.md) preserves their bounded scope; the old `rama-production.glb`, carry overlay and fourteen-invocation research components remain available for comparisons and the existing film. They are not the current default hero or controls.

The published [Mythic native preview](https://github.com/occult-kranti/ANDOLAN/releases/tag/yuga-traversal-armies-2026-10-17-mythic) is source `e2dc0ecd3f6903e0c8af68b2c5717ba5947108ed`. It implements fourteen **invocations through the current Rama avatar**, a selector, actual troop receivers, distinct event-driven effects, sixteen original synthesized cues, a diagnostic entity bridge and a 3D physics experiment. Both bounded batches are accepted, including final pause/focus, source-matched captures and [local Linux packaged input](evidence/mythic-window-r3/REVIEW.md). [Foundation CI](https://github.com/occult-kranti/ANDOLAN/actions/runs/39025311081) and [prerelease CI](https://github.com/occult-kranti/ANDOLAN/actions/runs/39025531829) passed. All 100 downloaded assets, 290 runtime sources, two fresh source-bound decodes and sixteen required reports are verified. The exact downloaded Linux build passes title/world entry, fully visible Continue, keyboard selector entry, a visible Sita cast with release/cooldown, pause retaining that state, F5 reset to READY and title return. The 960 × 600 software Forward+/Dummy-audio run reports no engine errors or warnings. It does not repeat remapping/settings or establish listening/GPU quality; see [public release evidence](evidence/mythic-published/REVIEW.md). Windows remains unexecuted. The quick-start is **Explore Confluence → F3 → Use invocation → X**; F2 opens remapping. [Practice rules](ULTIMATE_PRACTICE.md) and [selector UX](INVOCATION_UX.md) describe this one-avatar prototype.

Historical release: the [Triad and siege preview](https://github.com/occult-kranti/ANDOLAN/releases/tag/yuga-traversal-armies-2026-10-17-triad-siege) is source `ae33db4520bd14fe7b38aed173b764de7a7424d5`. Its [foundation CI](https://github.com/occult-kranti/ANDOLAN/actions/runs/39016682299) and [prerelease CI](https://github.com/occult-kranti/ANDOLAN/actions/runs/39016682252) passed. Independent verification checked all 77 public assets, 233 tagged runtime source files and three fully decoded, source-matched six-second captures. The exact downloaded Linux window passes forward Lotus entry, capture, capped arrow supply, pause, ordinary reset, siege entry and title return. It ran at 960 × 600 on Forward+/llvmpipe with Dummy audio; the broader local Help/overview review was not repeated. Windows is packaged/validated but unexecuted. See [public release evidence](evidence/triad-published/REVIEW.md) and the [Triad milestone](TRIAD_MILESTONE.md).

The earlier [local Linux package](evidence/triad-window-r2/REVIEW.md) is source `f87de49531b3b456198bf3cd4ebf0b088bfa9094`. All 233 runtime sources match that historical Triad tag. Of 232 PCK paths, 223 payloads match and nine generated scenes differ: three exported scenes and six imported GLB scenes. All 27 compiled scripts match. This establishes the specified source/payload identity and observed behavior, not binary or full visual equivalence. The [previous 62-asset siege release](evidence/siege-published/REVIEW.md) remains historical evidence for `35b20429`, not the new build.

The current native game retains Rama's courtyard training, a 24-second two-actor combat film, and offline Confluence practice: a 140 × 260 m three-lane city, eight landing decks, ten tether rings, finite-energy flight/grapple, five-role local armies, cannon/chariot drill, three capture/supply relays, local core outcomes, day/night lighting, original sound and persistent keyboard controls. It is a prototype with bounded verified behavior. The three six-second traversal, siege and relay videos are silent; the separate film has audio.

The Mythic public/local comparison verifies the same 290 runtime sources and engine. Nine generated/imported SCN resources differ among 288 PCK paths; this does not establish binary or visual equivalence. The exact downloaded Linux package has its own input review.

The production target remains an original **6v6, 14-hero, three-lane, 18-minute** competitive game with high-quality characters, motion and operated online services. Native online matches, the full native roster, production art, human balance/accessibility studies, Windows execution and physical-GPU profiling remain open. Software Vulkan captures and simulated FPS do not establish commercial-game parity or hardware performance.

| Product | Source boundary | Run/authority boundary |
| --- | --- | --- |
| **YUGA native** | `games/yuga-native/`; branch `game/yuga-native-production` | Godot desktop project. Current playable world is offline. |
| **YUGA browser** | `games/yuga/client`, `shared`, `server`; browser release branch `game/yuga-confluence` | PlayCanvas/Vite client plus Node/WebSocket authority: protocol 2, 3v3/480 s, 140 × 170 m. `npm run yuga:dev`; client :5180, server :3005. |
| **ANDOLAN protest game** | Repository-root `apps/`, `packages/`, `tests/` | Separate existing game. `npm run dev`; client :5173, server :3001. Root `npm test/build` are not YUGA-native gates. |
| **Reference labs** | `games/yuga/reference*` | Separate mechanics studies using `yuga:lab:*`; not the native game. |

GitHub Pages can serve websites/download links; it does not host a persistent authority server. Read [GAME_DESIGN_MASTER.md](GAME_DESIGN_MASTER.md) for production rules and [FULL_GAME_PRODUCTION_ROADMAP.md](FULL_GAME_PRODUCTION_ROADMAP.md) for gates, not for a claim that those features already exist.

## 2. Tools and fresh setup

| Tool | Version/contract |
| --- | --- |
| Engine | **Godot 4.6.3 standard**, Forward+; fixed native physics 60 Hz. The C#/.NET edition is unnecessary. |
| Art | **Blender 4.3.2** is recorded for current world kits; GLB/glTF 2.0 exports, Godot-imported scenes/materials/skins. |
| JS | Node **≥22.12**; native CI pins 22.14.0, current worker validates 24.19.0. Use `npm ci` and `package-lock.json`. |
| Python/audio | Python 3.12.14 observed on this worker. Setup pins NumPy 2.3.5 and SciPy 1.15.3 in `/workspace/tooling/yuga-native-python`. |
| Capture | FFmpeg/ffprobe, Xvfb and Mesa llvmpipe. `setup-render-runtime.py` restores its pinned external Debian runtime. |
| Research only | REA/Ghidra and BRUTAL are not runtime dependencies. See the research brief for exercised capabilities and limits. |

Check the branch and preserve other workers' changes before setup:

```sh
pwd
git status --short
git branch --show-current
node --version
godot --version
bash tools/cloud/setup-native.sh
```

The setup script installs locked npm dependencies and the audio Python environment, imports Godot assets, runs the native/browser-rule suites and prepares the renderer. It prints a new `/tmp/yuga-native-setup-*` report directory. It expects Godot 4.6.3 on PATH and the usual cloud Python/Node utilities; it does not install Blender or manufacture missing editable source art.

If Godot is missing, the checked installer downloads and verifies the official Linux and Windows engines. Put the Linux binary on PATH as `godot`, then run setup:

```sh
python3 games/yuga-native/tools/release-native.py install-engines --destination /workspace/tooling/native-engine
mkdir -p /workspace/tooling/native-engine/bin
ln -sfn ../Godot_v4.6.3-stable_linux.x86_64 /workspace/tooling/native-engine/bin/godot
export PATH="/workspace/tooling/native-engine/bin:$PATH"
```

No game API key is needed to build or play offline. Rendering cannot use a headless-only invocation; use the owned-display capture helpers below. If downloads fail, inspect the managed environment/network status instead of repeatedly rerunning a failing install. Keep credentials outside source, logs, assets and release archives.

## 3. Launch and source map

```sh
godot --headless --path games/yuga-native --editor --import --quit
godot --editor --path games/yuga-native
godot --path games/yuga-native
```

For a local machine without working Vulkan, explicitly choose `--rendering-method gl_compatibility`; it has reduced effects. Do not silently accept its output as the Forward+ art target.

`project.godot` opens `scenes/courtyard.tscn`. Its title menu opens training, `confluence_world.tscn` or `combat_film.tscn`. Courtyard/world scenes own player activation, UI pause and scene returns. Shared controls/config are installed per scene. Confluence reads the staged map, assembles geometry/collisions, creates the player, army and audio, then connects combat/traversal events to those systems. The film samples its authored timeline independently of gameplay authority.

| Change | First files to open |
| --- | --- |
| Entry scene, engine settings, exports | `project.godot`, `export_presets.cfg`, `scenes/` |
| Title/courtyard/settings/help flow | `scripts/courtyard.gd`, `scripts/input_bindings.gd`, `scripts/controls_overlay.gd` |
| World assembly, HUD, pause, scene returns | `scripts/confluence_world.gd` |
| Walking, aim, weapon, ability integration | `scripts/player.gd`, `scripts/rama_hero_runtime.gd`; current kit does not use the old `projectile.gd` fire path |
| Rama actions, damage, effects and health | `scripts/rama_ability_kit.gd`, `rama_ability_effects.gd`, `rama_vitals.gd`, `assets/design/rama-ability-kit.json`; [kit contract](RAMA_ABILITY_KIT.md) |
| Rama motion and contact | `scripts/rama_motion.gd`, `assets/animations/rama_hero_motion.tres`, `art/hero-rama-motion/` |
| Rama HUD, guide and shared theme | `scripts/rama_hero_hud.gd`, `rama_hero_panel.gd`, `hero_ui_theme.gd`; [screen design](RAMA_SCREEN_DESIGN.md) |
| Courtyard receiver adapter | `scripts/rama_practice_army.gd`, `rama_practice_target.gd`; same kit as the lane world |
| Flight, grapple, energy, LOS, collision | `scripts/player_traversal.gd`; player delegates movement/state |
| Historical additive traversal pose | `scripts/traversal_pose.gd`; current Rama uses only `rama_motion.gd` to avoid competing skeleton writers |
| Lane movement, attacks, gold, local cores | `scripts/lane_army.gd`, `scripts/lane_minion.gd` |
| Invocation tuning and real troop receivers | `assets/design/native-ultimate-rules.json`, `scripts/ultimate_rules.gd`, `scripts/ultimate_session.gd`, then the army/minion files; [practice contract](ULTIMATE_PRACTICE.md) |
| Invocation selector and modal glue | `scripts/invocation_panel.gd`, `scripts/confluence_world.gd`, `scripts/input_bindings.gd`; [UI contract](INVOCATION_UX.md) |
| Invocation ornament and cues | `scripts/ultimate_effects.gd`, `scripts/invocation_audio.gd`, `tools/audio/build-invocation-audio.py`, `assets/audio/invocations/{README.md,manifest.json}` |
| Cannon carts, royal chariots, committed blast warnings | `scripts/lane_vehicle_art.gd`, `scripts/siege_effects.gd`; [siege milestone](SIEGE_MILESTONE.md) |
| Relay capture, supply and original stations | `scripts/relay_control.gd` (pure rules), `relay_session.gd` (actual resource/LOS adapter), `relay_art.gd` (original geometry); [Triad milestone](TRIAD_MILESTONE.md) |
| Map geometry and placement | `art/world/confluence-map.json` → `assets/world/confluence-map.json` via `tools/stage-world.py` |
| Landing decks/rings | `scripts/traversal_landmarks.gd` plus manifest `traversal` section |
| Lighting, water, paving | `scripts/world_lighting.gd`, `scripts/world_water.gdshader`, `scripts/world_ground.gdshader`, `scripts/world_ground_common.gdshaderinc` |
| Music/cue scheduling and synthesis | `scripts/traversal_audio.gd`, `scripts/siege_effects.gd`, `tools/audio/build-traversal-audio.py`, `tools/audio/build-siege-audio.py`; their audio manifests |
| Current Rama / courtyard art | `art/hero-rama/{README.md,build_hero.py,rebind_dhoti.py,rama-hero.blend}`, `art/build_courtyard.py`; provenance and validators beside generators |
| Modular world art | `art/world/build-architecture.py`, `build-nature.py`, their `*-manifest.json` |
| Combat film script and director | `assets/cinematics/confluence-duel.json`, `scripts/combat_film.gd` |
| Film actors, VFX, audio | `scripts/cinematic_actor.gd`, `scripts/duel_effects.gd`, `art/cinematics/`, `tools/cinematics/` |
| Native transport/interpolation study | `scripts/arena_client.gd`, `scripts/arena_interpolator.gd`; not wired into an online rendered match |
| Version/session guards and native entity presentation | `scripts/native_contracts.gd`, `scripts/entity_bridge.gd`, `assets/contracts/native-contracts-v1.json`; [contracts](NATIVE_CONTRACTS.md), [bridge](NATIVE_ENTITY_BRIDGE.md) |
| 3D authority experiment and next-server decision | `assets/contracts/physics-fixture-v1.json`, `tools/physics/{reference.ts,run.py,compare.py}`, `tests/physics_authority_cases.gd`; [physics decision](PHYSICS_AUTHORITY_DECISION.md) |
| Authoritative browser rules | Repository `games/yuga/shared/{types,map,heroes,simulation}.ts`, `games/yuga/server/server.ts` |
| Build/publication | `tools/package-native.py`, `tools/release-native.py`; repository `.github/workflows/yuga-native*.yml` |
| Current work/status | `docs/RAMA_HERO_MILESTONE.md`, `docs/RAMA_HERO_ACCEPTANCE.md`, `docs/ROADMAP_BACKLOG.json`; historical evidence stays in its original milestone/archive |

## 4. Contracts to preserve

Native defaults: WASD/arrows move, mouse aim, LMB Kodanda, Space jump/ascent, Shift sprint, R reload, **Q Piercing Dawn, E Measured Step, C Guardian Circle, X Dawn Volley**, F flight, G tether and Ctrl descend. F1 overview, F2 controls/help, **F3 Rama guide**, F5 reset, N lighting and Escape pause are fixed. The historical invocation selector remains a separate secondary pause action in Confluence. In the courtyard, keyboard customization is also under Settings. Active labels come from `InputBindings.label()`. Version-3 settings migrate newly added actions to unused keys while preserving existing bindings; they do not overwrite an old custom C binding.

`InputBindings.install()`, `read_config()`, `merge_settings()` and `release_gameplay()` are shared. Settings live in Godot `user://courtyard-settings.cfg`. Ordinary writes preserve other sections and refuse malformed/oversized input. Explicit Reset preserves invalid bytes in a unique local backup before writing defaults. Pause, capture, focus loss, overview and scene changes must neutralize held input. Flight/tether cancellation must preserve an accepted Measured Step during pause; explicit reset, death and combat cancellation retire it. Test with an isolated XDG data directory to avoid changing another session's preferences.

Map data uses metres, +Y up, base-centred props and shared +Z-forward/yaw conventions. Native camera/model orientation is a separate bridge: preserve the tested adapters rather than copying yaw blindly. Canonical native bounds are 140 × 260 m, actor x=±68/z=±128, radius 0.65 m, spawns z=±112; local core anchors z=±120. Eight copied browser SOLIDS plus eight native platform boxes and nine matching relay plinth steps define collision. The relay stations are native-only at x−34/−6/+34,z4; the capture centres stay x−40/0/+40,z0. Preserve both lane and cross-lane rotation corridors. Decorative meshes do not imply collision. Flight ceiling is 24 m; tether range 36 m. See manifest fields and actual tests before changing a number.

Native army logic is fixed at 20 Hz, with 5 Hz target decisions, 30 s paired waves and 72-live/24-corpse/96-total caps, plus at most 72 queued attacks and 32 pending siege attacks. Its five roles are `spearman`, `bow_guard`, `commander`, `cannon_cart` and `royal_chariot`. Initial practice has thirty infantry; mirrored cannons can reinforce each lane every third wave and chariots the centre every fifth, subject to clearance and capacity. `start_siege_drill()` validates before replacing the round with six centre-lane units; `reset()`/F5 restores ordinary waves. Committed siege events carry fixed ground points and cancellation receipts; `siege_effects.gd` presents them without applying damage. Enemy siege impacts now reach Rama’s health receiver through `rama_hero_runtime.gd`; ordinary troops still target troops. The shared kit has real Guardian healing/shielding, interruption, death and a three-simulation-second respawn. Browser soldier/watch/minister/king, 18 s waves, contested shards and multiplayer economy remain separate contracts.

The retained historical invocation practice uses one army-clock cast and one **shared 12-second cooldown**. Previewing/selecting another legend cannot reset it. Effects apply only to living lane troops: damage, capped healing, max-style shields, expiring slows or two atomic temporary sentinels within existing army caps. They do not supply player health, hero model swaps, spell damage to cores or online authority. Hanuman projects a landing payload without moving Rama. Casting requires the flat street ground; aimed points and troop hits use the explicit native practice geometry/line-of-sight contract, not a new multilevel combat solver. Suspension freezes the army, session and effects; cancellation preserves recovery, while an explicit round reset changes epoch and resets practice. Presentation consumes accepted events and never awards damage or gold. `invocations.reduced_effects` and `invocations.reduced_motion` persist through shared config merges while retaining exact warnings.

Relay rules run at 10 Hz through `_step_relays`, which explicitly stops during pause, overview, siege drill and outcome. The pure module emits epoch/ID supply receipts; the session checks current actors, team, height, range and physical LOS before granting bounded troop health or hero ammunition. Relay supply does not heal the hero; Guardian Circle is the current hero-healing action. Art never grants rewards. A mixed int/String actor-ID comparison and station placement across the mid crossing were caught and fixed by independent integration tests; preserve those regressions. An actual extracted-package test also caught the Lotus visit facing away from its objective. The visit now uses the shared map heading 0 at `(0, .05, -7)`; the integration gate activates the real button and checks safe spawn, camera direction and actual forward displacement toward the relay.

Browser authority remains protocol 2, three heroes per team and 480 s. Production remains a versioned 6v6/1,080 s proposal. New elevation, objectives, hero selection or input rules require a shared contract migration; an offline movement feature must not silently appear as a competitive advantage.

Batch 2's implemented contract migration requires per-profile `content_revision`: native-practice content is now **revision 3** for the Rama kit/hero receiver, while browser and production-proposal content remain revision 1. Descriptors take `versions.content` from that profile; input/event/entity/replay envelope versions remain 1. The native ledger pins fourteen gameplay sources: the previous seven army/traversal/relay/invocation sources plus the Rama kit, runtime, vitals, practice adapter/target, player and tuning JSON. Contract, source-pin, bridge, final integration and local package evidence are accepted for the bounded batch. Publication, assets, source-bound reports and the bounded exact-public Linux input repeat are verified in the public review. Never fix a stale digest without an intentional revision. The entity bridge creates diagnostic scene nodes from admitted records and handles generations/reconnect/replay without sockets, collision or gameplay authority. The physics experiment recommends a future headless Godot authority, records TS/Godot divergence and does not adopt it into the current protocol. Follow [NATIVE_ENTITY_BRIDGE.md](NATIVE_ENTITY_BRIDGE.md) and [PHYSICS_AUTHORITY_DECISION.md](PHYSICS_AUTHORITY_DECISION.md) before attempting two-client integration.

## 5. Assets, import and provenance

`assets/` contains runtime GLBs, animation libraries, textures, audio and staged JSON. `art/` contains authored generators/manifests/reference work; `docs/` contains design and evidence. Export presets include runtime JSON and exclude source, tests, tools, docs and raw art; the package helper separately attaches notices. Generated concepts are visual targets, not game meshes or proof of completed animation.

For a world-data edit:

```sh
python3 games/yuga-native/tools/stage-world.py
python3 games/yuga-native/tools/stage-world.py --check
godot --headless --path games/yuga-native --editor --import --quit
```

World-kit rebuilds use `blender --background --threads 1 --python games/yuga-native/art/world/build-architecture.py` or `build-nature.py`. These overwrite authored outputs; give the generator, GLB, manifest and validation to one owner. The legacy `build_rama.py` path still needs the missing `/workspace/tooling/yuga-art/output/rama-authored.blend`. The historical editable reconstruction uses committed `art/production/reconstruction-source.glb`, `reconstruct_rama.py` and `reconstruction-rama.blend`; follow `reconstruction-notes.md` and revalidate skin/animation after any re-export. The committed runtime GLB can be imported without rebuilding it. The new editable hero is `art/hero-rama/rama-hero.blend`; its generator also depends on `rebind_dhoti.py`. Follow that directory’s README and provenance before rebuilding. Do not regenerate accepted art just to test a UI change.

After asset changes run the matching structural validator, pinned Khronos GLB validator (see native CI), import and actual render/animation review. Update source/output hashes and attribution together. Preserve `NOTICE/ASSET-NOTICE.md` and per-asset provenance: MakeHuman anatomy data is CC0; the separate TPS motion study has CC-BY attribution; Godot and dependency notices ship with packages. A reverse-engineered engine's license does not license an unrelated game's models/textures.

The sixteen invocation cues are original deterministic oscillator synthesis: shared windup/cancel and fourteen distinct releases, with no outside samples, melodies or voices. Their manifest pins generator/WAV hashes and PCM statistics; `invocation_audio.gd` owns at most three players and suppresses stale/paused/muted onsets. The world supplies saved volume. Run `python3 games/yuga-native/tools/audio/build-invocation-audio.py --check --report /absolute/new/invocation-audio-build.json` with standard Python; generation without `--check` rewrites the authored cues. Import new WAVs before export. Reproducibility, peak limits and Dummy-driver lifecycle checks do not establish listening quality or cultural authenticity.

## 6. Focused verification

Import first. Give each run a new absolute report directory and isolated settings. This example runs a real headless suite; change only the suite/report name for the matrix below:

```sh
YUGA_CHECKS="$(mktemp -d /tmp/yuga-checks-XXXXXX)"
mkdir -p "$YUGA_CHECKS/user"
XDG_DATA_HOME="$YUGA_CHECKS/user" godot --headless --path games/yuga-native --fixed-fps 60 --script res://tests/input_binding_cases.gd -- --report="$YUGA_CHECKS/controls.json"
python3 games/yuga-native/tools/check-roadmap.py --report "$YUGA_CHECKS/roadmap.json"
```

| Changed area | Required focused checks, then integration |
| --- | --- |
| Rama hero integration | `rama_ability_cases.gd`, `rama_motion_cases.gd`, `rama_practice_cases.gd`, `rama_hero_integration_cases.gd`, `rama_screen_cases.gd`, `rama_hud_layout_cases.gd`, Python `rama_package_cases.py`; actual continuous motion/gameplay and packaged screen/input review |
| Input/settings/UI | `input_binding_cases.gd`, `siege_ui_cases.gd`, `world_scene_cases.gd`, `world_flow_cases.gd`; `combat_film_audio_cases.gd` if shared reader/audio changes; actual small-window remap/pause/drill/return |
| Player/traversal | `traversal_cases.gd`, `traversal_pose_cases.gd`, `native_acceptance.gd`, `world_scene_cases.gd`; actual motion capture |
| Army/combat/rewards | `lane_army_cases.gd`, `siege_army_cases.gd`, `siege_pose_cases.gd`, `lane_vehicle_art_cases.gd`, `projectile_cases.gd`, `traversal_army_stress.gd`; actual engagement and close continuous vehicle review |
| Invocation gameplay/UI/FX | `ultimate_cases.gd`, `ultimate_effects_cases.gd`, `invocation_ui_cases.gd`, `mythic_integration_cases.gd`; army/siege/relay regressions; actual F3 selection, remapped casting, cooldown, pause/focus/reset and 960×600/1280×720 review |
| Invocation audio | `invocation_audio_cases.gd`; Python `tools/audio/build-invocation-audio.py --check --report /absolute/new/invocation-audio-build.json`; real listening remains a separate gate |
| Contracts and entity bridge | `native_contract_cases.gd`, `entity_bridge_cases.gd`; source-pin checker listed in [NATIVE_CONTRACTS.md](NATIVE_CONTRACTS.md); diagnostic nodes do not prove online gameplay |
| 3D authority experiment | `python3 games/yuga-native/tools/physics/run.py --output /absolute/new/physics-review` runs TS tests/typecheck, Godot queries and pinned comparison; output must not exist |
| Map/lighting | Python `world_map_cases.py`, `world_plan_cases.py`; Godot `world_scene_cases.gd`, `world_lighting_cases.gd`, `world_flow_cases.gd`; day/night/overview render |
| Audio/effects | Python `tools/audio/build-traversal-audio.py --check` using the audio venv, `tools/audio/build-siege-audio.py --check`; `traversal_audio_cases.gd` and `siege_effects_cases.gd` at ordinary and fixed clocks; listening reviewed separately |
| Film | Python `combat_script_cases.py`; Godot `combat_film_cases.gd`, `combat_film_audio_cases.gd`, `combat_motion_continuity.gd`, `duel_effects_cases.gd`; actual seek/replay and continuous render |
| Transport/shared rules | `npm run yuga:typecheck`, `npm run yuga:test`; `tools/check-native-arena.py --engine /absolute/path/to/godot --output /tmp/NEW-native-arena` |
| Package/release | Python `traversal_security_cases.py`, `release_traversal_cases.py`, `release_siege_cases.py`, `release_triad_cases.py`, `release_mythic_cases.py`; current-source capture/report validation, package inspection and actual extracted-package execution |
| Roadmap/evidence | `tools/check-roadmap.py`, `tests/roadmap_cases.py`, `tools/check-evidence.py --git-ref HEAD` |

GDScript names are under `games/yuga-native/tests/`; Python suite names also live there unless qualified. Most Python suites accept `--report /absolute/path.json`; `tests/roadmap_cases.py` prints JSON only, so use `python3 games/yuga-native/tests/roadmap_cases.py > "$YUGA_CHECKS/roadmap-cases.json"`. GDScript suites receive `-- --report=/absolute/path.json`. Run from the repository root. Source-rule/map tests need `npm ci`; imported-resource tests need the Godot import. Use a fresh process/report for each case; do not share writable user settings between concurrent tests.

For the invocation selector specifically: `godot --headless --path games/yuga-native --script res://tests/invocation_ui_cases.gd -- --report="$YUGA_CHECKS/invocation-ui.json"`. Its headless focus/layout checks are separate from actual window input. Batch 2 component evidence is under `docs/evidence/mythic-batch2/`; an individual passing report is not the final batch/release gate.

A nonzero exit, `passed:false`, missing report or script error fails the run. Archive meaningful failures and exact source hashes when repairing a defect. A 20-minute accelerated simulation is not a 20-minute wall-clock performance test. Numerical transforms do not certify contact quality, artwork or audible sound. [TRAVERSAL_ARMY_VERIFICATION.md](TRAVERSAL_ARMY_VERIFICATION.md) and the workflows list the complete gates; broaden tests when a change crosses subsystem boundaries.

## 7. Actual capture and packaged-window review

Only one heavy renderer at a time. Freeze owned source while capturing, choose a fresh absolute output name and an unused X display in 90–199. The helper owns/cleans only its processes and isolates user settings. These commands launch real software Vulkan rendering:

```sh
python3 games/yuga-native/tools/setup-render-runtime.py
python3 games/yuga-native/art/hero-rama-motion/run_capture.py --output /tmp/yuga-rama-NEW-motion --display 145 --asset=res://assets/heroes/rama-hero.glb --full
python3 games/yuga-native/tools/run-rama-gameplay.py --help
python3 games/yuga-native/tools/run-traversal-capture.py --preview --output /tmp/yuga-traversal-NEW-preview --display 117
python3 games/yuga-native/tools/run-traversal-capture.py --output /tmp/yuga-traversal-NEW-full --display 117
python3 games/yuga-native/tools/run-world-capture.py --output /tmp/yuga-world-NEW --display 110
python3 games/yuga-native/tools/run-ultimate-capture.py --output /tmp/yuga-ultimates-NEW --display 119
python3 games/yuga-native/tools/run-combat-film.py --preview --output /tmp/yuga-film-NEW-preview --display 118
```

Run only the capture relevant to the changed behavior. Replace `NEW` each time; prior evidence is not overwritten. Traversal preview is 24 frames at 960 × 540; full capture is 180 frames at 1280 × 720, 30 simulated FPS and 60 Hz physics, encoded to a silent six-second movie. Film full capture omits `--preview`; it is a separate 24-second timeline. Full video needs FFmpeg/ffprobe. The ultimate helper has no preview flag: it records fourteen warning/motif stills, three quality/overlap variants and a four-second, 120-frame staged Rama/Sita take. It applies no gameplay damage; Sita is cancelled before normal expiry. All fourteen full rendered lifecycles remain a later gate. Inspect actual images and meaningful transitions after successful capture; output existence is not visual approval.

The accepted final mythic archives are [ultimate studies](evidence/mythic-ultimates-render-r3/ULTIMATE-RENDER-REVIEW.md) in `docs/evidence/mythic-ultimates-render-r3/` and [traversal](evidence/mythic-traversal-render-r2/TRAVERSAL-RENDER-REVIEW.md) in `docs/evidence/mythic-traversal-render-r2/`. Earlier rejected attempts retain their own directories. [Batch 2 review](evidence/mythic-batch2/REVIEW.md) connects capture, gameplay and packaged-input evidence.

For actual keyboard/mouse interaction with an extracted package, the window helper needs Pillow, X11/XTest libraries and the prepared Vulkan runtime. Replace the engine/PCK arguments with real extracted files; choose an unused display:

```sh
YUGA_RUNTIME=/workspace/tooling/native-render/runtime
LD_LIBRARY_PATH="$YUGA_RUNTIME/usr/lib/x86_64-linux-gnu${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}" VK_ICD_FILENAMES="$YUGA_RUNTIME/usr/share/vulkan/icd.d/lvp_icd.json" LP_NUM_THREADS=2 python3 games/yuga-native/tools/native-window-review.py --engine /absolute/linux-engine --pack /absolute/project.pck --output /tmp/yuga-window-NEW --xvfb "$YUGA_RUNTIME/usr/bin/Xvfb" --display :107
```

Keep stdin interactive for the review session; closing it immediately terminates the helper. It accepts JSON lines, for example `{"action":"capture","name":"title"}`, `{"action":"key","key":"F2"}`, and `{"action":"quit"}`. Wait for the real screen before the next event, and let software-rendered focus updates settle before asserting a screenshot. Its exit cleanup is distinct from a crash; inspect `input-review.json` and logs. Dummy audio does not verify listening quality.

## 8. Package and release

The portable package contains the official Godot engine plus an exported PCK; no editor export templates are required. Install verified engines as above, then:

```sh
python3 games/yuga-native/tools/package-native.py --linux-engine /workspace/tooling/native-engine/Godot_v4.6.3-stable_linux.x86_64 --windows-engine /workspace/tooling/native-engine/Godot_v4.6.3-stable_win64.exe --build-dir /tmp/yuga-package-NEW
```

`--export-only` validates resource packs without needing the Windows engine; `--package-only` packages existing exports. Inspect the generated export/package manifests, notices, file inventories and checksums. Extract and run the actual package, not just the source project. Clean imports can alter generated scene IDs/tiny quantized imported values: investigate differing bytes and record limits instead of claiming byte identity or perceptual equivalence.

Branch CI is [yuga-native.yml](../../../.github/workflows/yuga-native.yml). Publication is [yuga-native-release.yml](../../../.github/workflows/yuga-native-release.yml): tags matching `yuga-traversal-armies-*` or `yuga-confluence-duel-*` trigger frozen-source validation, mandatory reports, exports, staging and a separate least-privilege publish job. The workflow's exact command order and check filenames are authoritative. Do not replace failed or missing gates with unrelated successful reports. After a runtime change, capture fresh source-matched archives and update the applicable directory constants in `tools/release-native.py`. Triad's three `triad-*-render-r2` archives are historical. The published exact `-mythic` tag requires the new `mythic-traversal-render-r2` and `mythic-ultimates-render-r3` archives, plus typed source-bound invocation/bridge/physics/audio reports. The gate validates nonempty successful checks, current source/export hashes, the actual scripted event chronology, positive warning-still ages and captured media. Inspect the tag-specific `release_checks(tag)` and capture validators before staging. Changing hashes alone cannot replace a new render, and staged ornament footage does not prove actual troop effects.

For an authorized release, commit the reviewed changes first, choose a **new** tag, and push that commit/tag; never move an existing verified tag:

```sh
YUGA_TAG=yuga-traversal-armies-YYYY-MM-DD-rN
YUGA_COMMIT="$(git rev-parse HEAD)"
git tag "$YUGA_TAG" "$YUGA_COMMIT"
git push origin HEAD
git push origin "$YUGA_TAG"
```

Replace the illustrative tag value before use. Observe the actual workflow result; then download all uploaded assets into a new directory and run `python3 games/yuga-native/tools/release-native.py verify --directory /tmp/yuga-downloaded-NEW --tag "$YUGA_TAG" --commit "$YUGA_COMMIT"`. Execute the downloaded Linux package and report Windows separately. The workflow publishes using its `GITHUB_TOKEN`; local rendering/building needs no credential. Manual `stage`/`publish` subcommands exist, but require the same complete check/archive inventory; inspect `--help` and the workflow before use.

## 9. Pick the next bounded packet

[ROADMAP_BACKLOG.json](ROADMAP_BACKLOG.json) is authoritative for dependency readiness; [the full roadmap](FULL_GAME_PRODUCTION_ROADMAP.md) defines completion. Recheck `next_packets` and [MYTHIC_BATCHES.md](MYTHIC_BATCHES.md) before assigning work. Batch 1's accepted corrections do not close production character/map quality. Batch 2 has bounded acceptance, including the final pause/focus repair, captures and local packaged input. The release is published, its assets verified, and the bounded exact-public Linux input repeat passed. The next production gates are authority/controller adoption and two actual native clients, with production character/motion work in parallel.

The critical integration sequence remains FG00-T04 → FG04-T02/FG05-T02 (scene/entity/3D authority contract) → FG04-T03 (two rendered native clients) → FG06 full three-hero match. Offline decks do not close shared elevation; local core outcomes do not close FG06. FG01 visual targets and real hardware traces run alongside this work. Existing offline army/control evidence supports FG08/FG13 but does not close their production acceptance.

For a small presentation follow-up, use the supporting packets' `next_action`: close continuous vehicle/contact/material review, crowded warning readability, neutral-pad contrast and the initial world-loading transition remain open. Triad implements segmented warnings, correct round-reset Help wording and the forward-facing Lotus approach; preserve their regressions. Keep these improvements separate from the full-game dependency graph.

Use one owner per file set. Good independent squads are player/traversal, world/UI, army/AI, art, audio and QA; reserve integration ownership for shared manifests, packaging and release. Agree API/action names/coordinates before parallel edits. Agents report after three or four rounds: inspect/contract → implement → independent test/render review → bounded correction and integration. Heavy capture/package phases use frozen source. These are bounded workers, not a permanently running swarm.

```text
Task ID and scope:
Owned files / shared interfaces:
Round and source commit or hashes:
Implemented behavior:
Exact commands and report paths; pass/fail counts:
Actual images/input inspected; unverified limits:
Remaining defect/dependency and next owner:
```

Keep reusable setup and third-party tooling under `/workspace/tooling`, runtime code/assets in their canonical folders, fresh reports/captures in unique scratch directories, and accepted source-pinned evidence in the documented archives. Push/verify the intended checkpoint before cleanup. Git status, tracked notices/manifests, accepted evidence, user saves and editable source art are not redundant caches. Cleanup ownership and retained artifacts belong in [START_HERE](../../../docs/START_HERE.md); do not delete another worker's active directories.

## Siege feature checks and capture

The current siege packet adds original cannon carts and royal chariots to offline waves. In Confluence, press Escape and choose **Siege practice**; F5 restores regular lanes. The [siege milestone](SIEGE_MILESTONE.md) records its scope, five owners and graphics forecast.

Focused Godot suites are `siege_army_cases.gd`, `lane_vehicle_art_cases.gd`, `siege_effects_cases.gd`, `siege_pose_cases.gd` and `siege_ui_cases.gd`. Use the existing `--report=/absolute/new/path.json` pattern. `python3 games/yuga-native/tools/audio/build-siege-audio.py --check` verifies four original cues with the Python standard library; no new dependency is required.

After runtime/art source freeze, `python3 games/yuga-native/tools/run-siege-capture.py --output /absolute/new/directory` records 180 actual Forward+ frames of the public drill, with a fixed camera staged before the take. It owns an isolated Xvfb/Mesa session and generates a silent six-second MP4. This is simulation/motion evidence, not human-input or hardware-performance evidence. Retain raw captures in scratch and selected reviewed frames/reports in the evidence archive.

## Triad relay verification and capture

Use `tools/test-relay-control.gd`, `tools/test-relay-art.gd` and `tools/test-relay-integration.gd` with the same headless `--script res://... -- --report=/absolute/path.json` command above. `tests/world_scene_cases.gd` retains every actual lane/rotation sweep and excludes only the known solid plinth footprints from open-floor sampling. `tests/release_triad_cases.py` challenges archive/source/state/receipt/video validation. Setup and both native workflows run these gates.

`tools/run-triad-capture.py --output /new/absolute/output --display 119 --shader-cache-seed /existing/cache/mesa` records six actual seconds across capture and first supply after one documented hero/ammo/camera fixture and 7.5 seconds of physics preparation. It then takes four frozen-world station views. Runtime sources must stay unchanged throughout. Serialize it with traversal/siege captures, imports and exports. A Triad release requires all three current-source captures. Other tags follow the explicit selection in `release-native.py`: Mythic requires current traversal and ultimate studies. Historical cinematic media retains its separate provenance.

Do not infer GPU performance, human balance, listening acceptance or native online authority from these checks. The local hero still has no health/death receiver.
