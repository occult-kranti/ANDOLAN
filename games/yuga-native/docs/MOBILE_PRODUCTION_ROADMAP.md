# YUGA mobile: production roadmap

Prepared 18 October 2026. **This is the mobile adaptation plan, not an Android/iOS release or a claim of Mobile Legends visual parity.** The working baseline is `game/yuga-native-production`, commit `f81ee18c90547b60fdcc26fb4b1a185ac9ad2b9c`, plus the separately recorded G1/G2 graphics candidates. Read [the architecture decisions](mobile/CODE_AND_STACK_DECISIONS.md) before implementing a packet.

## Product decision

Build an original **landscape, elevated-camera, 5v5, three-lane MOBA** using YUGA's mythology-inspired characters and world. Keep the desktop third-person game as a separate rules/presentation profile. Start mobile with Rama and bots, then a real ten-player match, then the complete fourteen-hero production roster. Fourteen invocation labels in the existing build are not fourteen finished characters. The launch roster can change through a recorded design decision, not a hidden reduction of this target.

The intended visual result is detailed, animated 3D characters with readable silhouettes, expressive attacks, coherent lighting, rich original architecture and stable frame pacing on named phones. “4D/5D” is not a renderer or asset format: the deliverables are meshes, textures, rigs, animation, effects, sound and interactive simulation. Reference quality is judged in a moving ten-player match as well as a close-up hero screen.

**Recommended starting stack:** retain Godot 4.6.3 standard/GDScript, Blender and glTF. Qualify Godot's Mobile renderer on actual devices, with a separately tested Compatibility fallback. Trial a stripped headless Godot match server to preserve native rules, plus Nakama OSS/PostgreSQL for identity, parties and matchmaking. Final transport and authority choices require the M1 comparison; no online integration is claimed today. Android is the first qualification target; iOS follows with a macOS/Xcode build/signing lane. GitHub Pages can host the site, documentation and download links; it cannot run authoritative match servers.

## Local model squad amendment — 23 October 2026

[The shared laptop/squad guide](LOCAL_MODEL_SWARM.md) now targets the user's confirmed **8 GB dedicated RTX 4070 Laptop GPU**, with 16 GB shared memory kept separate. Six project skills cover QA, UI, hero, world, motion and models/builds; one qualified local model serves queued work. Exact Codex/Claude/Kimi compatibility and actual inference must pass a laptop pilot. Heavy generation/rendering is a separate session; published TRELLIS/TRELLIS.2/Hunyuan3D 2.1 configurations exceed this GPU's dedicated memory. No model is included in a game build.

Mobile remains deferred until desktop work is accepted. When it resumes, apply the same source/asset intake evidence to M1/M3 and separately qualify mobile LODs, touch screens, real 5v5 authority and physical devices. Neither laptop model tests nor desktop art acceptance closes those gates. The implementation ledger remains **0/108 across 18 planned rounds**; no Android package, device run or video analysis is claimed. The earlier US$7,000 RTX 5090 study below is an upgrade option, not this laptop's specification.

## AI-assisted authoring amendment — 21 October 2026

The [shared model/reconstruction study](research/ai-pipeline-oct21/README.md) updates both platforms. Its candidates come from pinned GitHub sources; the requested video is not yet accessible or transcribed. No model weights, GPU inference or Android binary were produced. The user's proposed workstation is a USA RTX 5090 laptop within US$7,000; qualify exact hardware and run heavy generation/render jobs serially. Desktop remains first.

Keep inference in the offline authoring pipeline. Adopt only accepted original source assets, then produce mobile-specific geometry, material, texture and animation variants. Do not include generation weights in the APK or make authoritative matches depend on a video world model. Model-license conditions, including output restrictions where applicable, follow the resulting asset workflow.

- **M1:** qualify workstation/model dependencies separately from physical Android renderer/device budgets; record exact source and weight versions, memory and disk needs.
- **M3:** one generated-assisted hero still needs artist retopology, rig/skin, complete action transitions, mobile readability and real-device play. A desktop GLB or generated turntable is insufficient.
- **M5/M6:** apply source-studied snapshot replay/correction and transport-compatibility tests to our original authority; require rendered clients and real 5v5 evidence.
- **M9/M10/M15:** evaluate shared content dependencies and camera bookmarks; create bounded hero/map bundles with original assets, LOD/collision truth and missing/offline/update checks. Study port architecture without importing unreviewed third-party packers or asset rights.
- **M11–M13/M16/M18:** roster, sustained hardware performance and release gates remain unchanged; measure accepted asset-production and rework time before forecasting fewer rounds.

The [18-round / 108-packet implementation plan](MOBILE_PRODUCTION_BACKLOG.json) remains **0 implemented**. The new research and capacity utility are supporting work, separate from its six earlier research packets. No APK, physical-device result or model-generated asset is claimed.

## Read only what your packet needs

| Owner | Document | Main output |
| --- | --- | --- |
| Lead / architecture | [Code and stack decisions](mobile/CODE_AND_STACK_DECISIONS.md) | Exact reuse boundaries, source-to-module migration and contract decisions |
| Controls / UX | [Touch UX and screens](mobile/TOUCH_UX_AND_SCREENS.md) | Camera, pointer ownership, targeting, accessibility and complete player journey |
| Renderer / map | [Rendering and map pipeline](mobile/RENDERING_AND_MAP_PIPELINE.md) | Renderer matrix, device budgets, original modular world and asset processing |
| Character / motion | [Hero and animation pipeline](mobile/HERO_ANIMATION_AND_ASSET_PIPELINE.md) | Authored model/rig/action/LOD gates and roster production |
| Rules / services | [Gameplay, network and services](mobile/GAMEPLAY_NETWORK_AND_SERVICES.md) | Versioned 5v5 authority, economy, reconnect and operating model |
| Reuse / tooling | [Open source and reverse engineering](mobile/OPEN_SOURCE_AND_REVERSE_ENGINEERING.md) | Verified candidates, licensing, bounded analysis and adoption criteria |
| Independent QA | [Device validation and release](mobile/DEVICE_VALIDATION_AND_RELEASE.md) | Device, network, security, store and evidence requirements |

Each specialist document has a sibling source ledger. A retrieved repository README establishes only its recorded contents, not working integration. Commercial publisher/store requests that returned 403 remain unavailable evidence. This work does not claim fresh Reddit/video study or commercial mobile client disassembly.

## What changes in our code

| Area | Existing implementation | Required mobile work |
| --- | --- | --- |
| Engine/export | Forward+ desktop; `gl_compatibility` mobile override; Linux/Windows presets | Explicit mobile startup/profile, Android ARM64 export, device-qualified renderer/settings; separate iOS lane |
| Movement/camera | `player.gd` polls keyboard/mouse and owns third-person movement; overview pauses the world | Hardware-independent intent, live elevated camera, world-space touch aim, safe bounds and obstruction handling |
| Combat | `rama_ability_kit.gd` commits/cancels actions on the local army's 20 Hz step | Preserve event semantics; server-owned actions, damage, costs and cooldowns; mobile-specific tuning by profile |
| World | Offline 140 × 260 m Confluence, traversal, relays and armies | Dedicated three-lane mobile topology, visibility, towers/base, jungle, pathing and match objectives |
| Hero art | One authored Rama, LODs, full-body motion and original effects | Mobile material/skin/texture variants, match-camera readability, baked secondary motion where needed, full roster |
| Units | Shared infantry/vehicle visuals; local simulation | Server entities separated from visuals; bounded LOD/animation/effect populations; coherent wave economy |
| HUD/screens | Fixed read-only five-action strip and keyboard modals | Interactive touch layout; joystick/drag-to-aim; touch-safe lobby/draft/shop/map/settings/reconnect/result flows |
| Online | Native offline; distinct browser protocol 2 / 3v3 prototype | New mobile 5v5 profile, authoritative transport, prediction/reconciliation, fog filtering, parties and persistence |
| Verification | Strong desktop/headless checks and software-render captures | Physical Adreno/Mali/iOS runs, touch/input, heat/battery/memory, backgrounding, bad-network and store artifacts |

Do not change desktop team counts or relabel the existing browser protocol as mobile 5v5. Do not use the current paused overview as a live camera. Do not convert the large desktop HUD into touch controls by making its labels bigger.

## Game and art direction to lock in M1

Use a curved outer silhouette around three strategically readable lanes. A Lanka-inspired raised citadel, river ghats, temple courts and a marsh jungle can share an original carved-stone/bronze/indigo visual language. Curves should create routes and recognizable districts without obscuring distance, sight lines or team symmetry. Towers and objective pits need stronger value/silhouette hierarchy than decorative roofs. Trim roofs or fade their presentation when they obstruct the camera; the server still uses fixed collision and visibility.

Define routes by **travel time and encounter purpose**, then select metre dimensions: spawn-to-first contest, safe retreat, cross-lane rotation and jungle detour. Keep mobile targeting surfaces predictable. Flight and grappling become explicitly bounded hero abilities or map interactions with telegraphed landing/reach rules; unrestricted desktop traversal is not inherited automatically. Lane soldiers, archers and cannon/chariot siege units retain original animation/weapon identities. Jungle creatures offer clearly telegraphed encounters and server-awarded temporary effects; their rewards, respawn and counterplay must be visible.

Day/night art uses baked variants or controlled colour/emission changes. Diyas, lanterns and spell glows do not each require a dynamic shadow light. If time of day affects vision, its timing and visibility belong to the ruleset, not local graphics settings. Decorative settings must not remove hostile telegraphs or reveal hidden enemies.

Proposed mobile match target: roughly 12–18 minutes, subject to human playtests. A target duration is not an automatic draw timer. Define win, disconnect, surrender, remake, stalemate and eventual-match-limit behavior explicitly. Every implemented playable hero is unlocked in both practice and competitive modes; competitive monetization must not sell combat strength. Cosmetic progression and mastery should explain learning goals rather than pressure daily attendance.

## Six-worker production schedule

[MOBILE_PRODUCTION_BACKLOG.json](MOBILE_PRODUCTION_BACKLOG.json) is the machine-readable packet queue. It contains **18 planned implementation rounds × 6 workers = 108 packets**, in addition to six M0 research packets. These are production gates, not 108 completed assignments, and not a promise that a fixed number of agent calls produces commercial-quality art. Roster batches and failed quality gates can require additional rounds.

The stable workers are W1 rules/authority, W2 touch/screens, W3 hero/motion, W4 world/units, W5 rendering/build/tools, W6 independent QA/security. The lead owns shared contracts, integration and acceptance. Specialist subagents may inspect bounded questions, but only the assigned owner writes a file. Six concurrent workers plus the lead fit the current seven slots; nesting agents does not create more slots or hardware.

| Round | Integrated outcome | Gate before advancing |
| --- | --- | --- |
| M1 | Reference device/renderer/server comparison and profile specification | Named physical devices; measured spikes; approved authority/camera/art benchmark; requirements still open if devices unavailable |
| M2 | Semantic input and live mobile camera | Two-thumb movement/aim, pointer capture/cancel/focus recovery, no desktop regression |
| M3 | Complete Rama mobile vertical slice | Actual device play: movement, five actions, damage/death, readable art/animation/audio and training flow |
| M4 | One complete lane and economy | Waves/tower/base/jungle fixture; server-ready gold/XP/last-hit rules and no duplicate rewards |
| M5 | Authoritative match process and transport | Two clients agree on damage/outcome; malformed/stale/spoofed commands rejected; bounded headless room |
| M6 | Actual 5v5 networking | Ten rendered clients plus bot load; latency/loss/reconnect tests; no hidden-state leakage |
| M7 | Complete match loop | Start/draft/spawn/lanes/objectives/win/result/rematch, authoritative receipts and bounded match lifetime |
| M8 | Practice bots and service resilience | Bot practice without public server; party/rejoin/background policy; idempotent persistence and failover behavior |
| M9 | All mobile screens and onboarding | Touch-only journey, safe areas, accessibility, settings persistence, consent/error/offline states |
| M10 | Complete three-lane map and unit presentation | Traversable original city/marsh/citadel; full waves, objectives, occlusion and device scene budget |
| M11 | Heroes 2–5 through the accepted pipeline | Four complete character packages; each includes counters, motion, effects, sound, LOD and match-camera review |
| M12 | Heroes 6–10 and ten-distinct-hero match | Ten usable characters; unique-selection draft and full composition stress; no invocation stand-ins |
| M13 | Heroes 11–14 and roster completion | All fourteen complete packages, localization/cultural review and full counter/ability compatibility matrix |
| M14 | Competitive balance and fair information | Human composition/lane studies, matchmaking rules, visibility/aim fairness and replayable defect reports |
| M15 | Final art, animation, sound and screen cohesion | Device footage of hero selection and worst-case battle passes art/clarity/contact review; residual defects assigned |
| M16 | Performance, security and operating cost | Sustained named-device budgets, network/server load, economy abuse tests, incident and rollback rehearsal |
| M17 | Closed alpha and correction round | External player evidence, crashes/accessibility/balance repairs, store internal-test artifacts with exact provenance |
| M18 | Regional beta and launch readiness | Independent release gate, signing/privacy/store acceptance, regional service readiness, support/rollback/live-ops ownership |

Review the roadmap after M3, M6, M10, M14 and M18. Each review uses producer, artist, gameplay, mobile engineer and independent player/QA perspectives; record disagreements, rejected proposals and the chosen experiment. M3 proves one hero, M6 proves ten-player networking, M10 proves a complete map, M13 proves roster coverage. None alone proves a finished game.

### How a round executes

1. Lead freezes interfaces and acceptance fixtures; attaches exact baseline hashes and previous findings. For M1, missing device evidence blocks a performance decision but does not block documentation or test-fixture work.
2. Six owners work in exclusive paths against those interfaces. Each packet in the JSON specifies output and a check that could fail. Shared rules/catalog/export/notice edits are serialized through the lead.
3. Each owner returns source hashes, actual commands, positive/negative results, captures where relevant, limitations and next owner. Work that depends on another packet begins only after that interface is merged.
4. Lead integrates; W6 reproduces representative counterexamples and checks evidence belongs to this source. Keep one shared import/export/render lane in this cloud. Real device runs can parallelize on separate devices.
5. Promote passed work, retain failures, update statuses and next-round dependencies. A failed art gate gets a specific revision task; adding detail or increasing test counts does not close it automatically.

Every packet follows this brief:

```text
ID / owner / mobile profile version:
Baseline source and device/tool versions:
Exclusive files; shared contracts; prerequisites:
Observable outcome; adverse cases; actual device/input/art check:
Output artifacts and provenance/attribution:
Result: passed / failed / unrun; evidence; unresolved findings; next owner:
```

## Acceptance and practical limits

Performance targets start as hypotheses: 30 fps baseline and 60 fps standard/high tiers, using device frame-time distributions over sustained representative matches, not averages from an empty scene. Exact device, resolution, skin/triangle/draw/texture/effect budgets are selected in M1. See the rendering and device documents for provisional envelopes and measurement procedures. A software Vulkan capture is useful for visual/source verification but does not qualify a phone.

High visual quality requires authored modelling, UVs/materials, rigging, expressive timing, camera composition, sound and repeated human review. Open-source tools improve this pipeline; a code license or decompiler does not provide Mobile Legends' artwork or recreate its operated services. The existing REA/Ghidra fixture proves a bounded analysis tool works on an original sample. No Mobile Legends client binary has been supplied or analysed here.

The current cloud can research, edit, run headless/native fixtures and prepare pipelines. Physical Android/iOS test devices, a macOS/Xcode signing lane, store identities and public regional server capacity are separate requirements for later gates. Do not install large SDKs merely to claim progress while these decisions are still being made. Prepare reproducible version-pinned tooling when its packet is active.

There is no defensible calendar estimate for Mobile Legends parity from the current prototype. Re-estimate after M3 using actual hero authoring time, measured device limits and observed review/rework rates; re-estimate online operation after M6. Agent-round counts are scheduling units, not a quality or duration metric.

## Relation to ongoing desktop work

The separate [G1–G6 graphics campaign](GRAPHICS_SIX_ROUNDS.md) remains active: G1 has bounded rendered review, G2 has implementation candidates and ongoing verification, and G3–G6 remain pending at this mobile planning checkpoint. M0 research does **not** count as native G3–G6 completion. Shared improvements can be adopted by both profiles only with their own source, art and regression gates. No mobile runtime, public match server, APK or iOS app is claimed by this document.
