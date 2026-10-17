# ANDOLAN — City of Consequences

Publication status for the visual checkpoint is recorded in [the verified source/CI receipt](docs/evidence/visual-campaign-publication.json).

**Latest reuse consultation:** [selected tools, two implemented offline adapters and the next five production goals](games/yuga-native/docs/research/community-reuse/README.md). Six specialists reviewed art, animation, mythology, engine sources and community coverage. Reddit app authentication succeeds, but subreddit access returns 403; fresh tool recommendations come from pinned upstream sources. Face/skin remains the next visual round.

**Download the current Rama preview:** [Linux / Windows](https://github.com/occult-kranti/ANDOLAN/releases/tag/yuga-rama-hero-2026-10-17). Extract the entire ZIP and run `launch.sh` or `launch.bat`. [Watch the actual five-action capture](https://github.com/occult-kranti/ANDOLAN/releases/download/yuga-rama-hero-2026-10-17/rama-five-abilities.mp4). Linux input and all public download bytes were verified; Windows execution remains untested. This is offline practice, with production art quality still open.

**Active production:** [fifteen specialist roles](games/yuga-native/docs/PRODUCTION_SQUADS.md) are improving one Rama hero slice against [explicit visual, motion and full-game gates](games/yuga-native/docs/DEADLOCK_QUALITY_TARGET.md). [Current source handoff](games/yuga-native/docs/VISUAL_CAMPAIGN_HANDOFF.md) distinguishes integrated work, staged art and rejected candidates from the published preview.

**Current graphics work:** the [visual campaign](games/yuga-native/docs/VISUAL_CAMPAIGN.md)
integrates hero surface finishes, courtyard arches and cupolas, warm practical
lighting, five ability effects, motion corrections and a reviewed facial-shadow
fix into the native source. Its
[round ledger](games/yuga-native/docs/VISUAL_CAMPAIGN.json) tracks the requested
ten rounds and actual specialist work. The published download above retains its
earlier source; commercial-game visual quality remains open. One fifteen-role
implementation/review cycle is complete; nine rounds remain planned.
[Watch the new silent action recording](games/yuga-native/docs/evidence/visual-campaign/capture-action-r1/rama-five-abilities.mp4)
and read its [bounded visual review](games/yuga-native/docs/evidence/visual-campaign/art-review/FILM_REVIEW.md).

Native YUGA now focuses on **one coherent Rama hero**: a new smooth 3D model, an authored motion controller, a five-part bow/ability kit, shared courtyard and Confluence controls, health and siege-damage respawn. See the [Rama milestone](games/yuga-native/docs/RAMA_HERO_MILESTONE.md), [actual art review](games/yuga-native/art/hero-rama/REVIEW.md) and [independent acceptance checklist](games/yuga-native/docs/RAMA_HERO_ACCEPTANCE.md). LMB draws and shoots; Q/E/C/X use the four abilities; F3 opens Rama's guide. F2 opens Help in title/training and saved key remapping in Confluence.

The working native source is `game/yuga-native-production`. The [previous Mythic release](https://github.com/occult-kranti/ANDOLAN/releases/tag/yuga-traversal-armies-2026-10-17-mythic) remains an immutable historical build at `e2dc0ecd3f6903e0c8af68b2c5717ba5947108ed`; its fourteen invocation studies use the older avatar. Native online matches, a complete production roster and Deadlock-level visual/performance qualification remain open. The new character is animated 3D; concept paintings are not gameplay evidence.

**New chat, contributor or agent:** read [START_HERE](docs/START_HERE.md) for the current build, product boundaries and task routing. The active native YUGA track has a [build handbook](games/yuga-native/docs/BUILD_HANDBOOK.md), [research brief](games/yuga-native/docs/research/RESEARCH_BRIEF.md) and [workspace guide](docs/WORKSPACE_AND_CLEANUP.md). The ANDOLAN protest-game documentation below describes its separate release.

Historical release: **[Triad and siege preview](https://github.com/occult-kranti/ANDOLAN/releases/tag/yuga-traversal-armies-2026-10-17-triad-siege)** for Linux or Windows. Source `ae33db4520bd14fe7b38aed173b764de7a7424d5` adds territory capture, contested supply and original relay stations to offline three-lane practice with flight, grappling, soldiers and siege vehicles. Both CI workflows passed; all 77 public assets and three current-source six-second captures were independently verified. The exact downloaded Linux build passes the bounded relay capture/supply, reset, siege-entry and title-return flow; Windows remains unexecuted. [Triad milestone and evidence](games/yuga-native/docs/TRIAD_MILESTONE.md). The [TF2 source study](games/yuga-native/docs/research/TF2_REUSE_STUDY.md) informed original behavior; no TF2 code or assets were imported. Native online matches and the concept-quality character benchmark remain open.

**City Reform Multiplayer Beta 0.3.** Bring a crew to fictional Devnagar, share a vehicle and take city jobs. Five repeatable runs cover deliveries, vehicle recovery, a checkpoint circuit and community projects. Five linked cases begin with a media exposé, uncover four sector disputes and end in a saved crew decision: publish the full case or take Samar's deal.

The original six-chapter Story remains optional, with 22 stages, seven decisions, five endings and its own evidence journal and saves. The larger six-district/22-mission game remains in [the production roadmap](docs/ROADMAP.md).

**Play Beta 0.3:** [Open ANDOLAN](https://occult-kranti.github.io/ANDOLAN/) and choose **City practice** for the city jobs/cases or **Begin story** for the original campaign. The release passed all thirteen CI browser cases; both public URL checks return the exact verified standalone file. The native live-site check also passed, including driving/braking, settings, save restoration and an already-loaded offline tab. Online rooms require a compatible game server entered in the lobby; no public multiplayer backend has been provisioned.

## Play and develop

Node 22.12 or newer (validated with Node 24):

```sh
npm ci
npm run dev
```

Client port 5173; room server port 3001. In the beta client:

- **Bring your crew** creates or joins a private room. Choose **City jobs · free roam** or **Original story · co-op**.
- **Open city** joins a shared development room on the configured server.
- **City practice** plays the city jobs solo, with a separate browser save.
- **Begin story / Continue story** opens the original solo campaign and its existing save.

For a static/downloaded client, enter your server's HTTPS or WSS address in **Game server address**. The address is remembered in that browser; an invite includes the server, room and activity. Joining online requires an actual server connection. City practice does not create online teammates.

Start **The Nine O'Clock Correction** from the jobs board for the case arc, or choose a repeatable run. One player can load and drive while another unloads on foot. The final mandate uses the connected crew's majority: reform adds one point to future project-bearing job rewards; capture gives 25% more crew credits but zero project points. Credits are a shared score, with no spending system.

Controls: WASD or arrow keys to move/drive, Shift to sprint, E to interact, F to enter/exit, Space to brake, H for the horn, drag to look, C to recenter, J for jobs or Story evidence, Escape for settings. Touch buttons include vehicle, brake and camera controls; gamepad B brakes. Settings provide graphics, camera comfort, subtitles, larger text, driving assistance, guarded key rebinding and opt-in original procedural audio with a test sound, volume and music controls.

Solo play pauses while its tab is hidden. Its fixed-step clock catches up with short delays, clears stale controls and limits long-stall recovery.

## Build and deploy

```sh
npm run build
npm run build:standalone
npm start
```

The server serves the production client and WebSocket rooms on port 3001. `dist/standalone/index.html` contains the local City practice and Story modes; online play still requires a server. Beta 0.3 uses **protocol 2**, so deploy the matching client and server. Supported old simulation saves migrate from schema 1/2 to 3 while preserving their existing progress and identities; server migration keeps an original backup. Dockerfile and Compose configuration target `andolan:0.3`; see [deployment and rollback instructions](docs/DEPLOYMENT.md).

An unexecuted [Render Blueprint](render.yaml) and [multiplayer hosting guide](docs/MULTIPLAYER_HOSTING.md) prepare one paid service with persistent room storage. No provider account, purchase or deployment has been made. The same Node service can host both client and rooms, or the static client can connect through its runtime server-address field. Running the game inside ChatGPT has not been verified.

The GitHub Actions workflow verifies and publishes the solo build. Cloud installation and startup were tested; [the setup record](docs/CLOUD_SETUP.md) explains the saved configuration draft and activation step.

## Verify

```sh
npm run lint
npm run typecheck
npm test
npm run test:content
npm run test:network
npm run test:e2e
```

Browser tests use installed Chromium; see `playwright.config.ts`. For the software-rendered cloud, run `ANDOLAN_SOFTWARE_RENDERING=1 npm run test:e2e`; CI enables this test-only graphics budget automatically. Evidence and limits are in [QA report](docs/QA_REPORT.md), [panel ledger](docs/PANEL_LEDGER.md) and `docs/evidence`.

Beta 0.3 passed **134 tests, typecheck, lint, all thirteen CI browser cases in 11.8 minutes, production/standalone builds and deployment**. Local checks include the physical two-client media case, audio/Story isolation, controls/settings and labelled mandate fixtures. The production container migrated an actual 0.2 room from a copied volume, preserved its identity/job and original backup, then retained new case progress through restart.

Release [run 38857615158](https://github.com/occult-kranti/ANDOLAN/actions/runs/38857615158), on `c20e912`, succeeded. The 2,478,963-byte public HTML matches the verified standalone SHA-256. The earlier failed van-entry run, its unproven cause and the subsequent test-only synchronization change remain documented in [current QA](docs/CITY_REFORM_QA.md). The live-site native-browser smoke passed in 28.889 seconds with no browser or request errors.

The earlier Beta 0.2 baseline remains recorded separately: 97 tests and ten browser cases in 491.765 seconds, including a physical shared Clinic Restock route. No human playtesting, full physical traversal of every sector case or hosted multiplayer result is claimed.

## Design and research

- [Game design](docs/GAME_DESIGN.md), [product brief](docs/PRODUCT_BRIEF.md), [roadmap](docs/ROADMAP.md)
- [City Jobs design and acceptance](docs/MULTIPLAYER_DESIGN.md), [City Reform cases and mandate](docs/CITY_REFORM_DESIGN.md), [multiplayer hosting](docs/MULTIPLAYER_HOSTING.md)
- [Design library and reading notes](docs/library/README.md): exact sources, game theory, story study, twelve-book reading backlog
- [Original concept art](docs/concepts/README.md): city art direction and the first crew
- [REA research](docs/research/REA_RUNBOOK.md), [mechanics specification](docs/research/VEHICLE_TRANSITION_SPEC.md), [reuse ledger](docs/REUSE_LEDGER.md)
- [Archived supplied handoff](docs/handoff/OPEN_WORLD_PLAN-v0.3.md), treated as design input
- [Third-party notices](THIRD_PARTY_NOTICES.md)
- [Dependency audit](docs/DEPENDENCIES.md): production audit and the recorded build-tool advisory

## Current boundaries

The runtime art is stylized and procedural; concept paintings are future art targets. Open city is a development mode, with no production accounts, moderation operation or regional matchmaking. Crew credits are room-owned progress counters with no spending system or cash value. Local automated tests do not prove sustained public capacity or how enjoyable repeated jobs feel. The game uses original art, synthesized audio and fictional satirical characters.
