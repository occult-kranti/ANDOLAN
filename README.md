# ANDOLAN / YUGA

This repository contains two games: **YUGA**, an original mythology-inspired native 3D game, and **ANDOLAN**, a separate browser city game.

**YUGA desktop work:** [active handoff](games/yuga-native/docs/ACTIVE_DESKTOP_HANDOFF.md) → [10 screen rounds + 3 integration rounds](games/yuga-native/docs/DESKTOP_FINISH_CAMPAIGN.md) → [six-worker task ledger](games/yuga-native/docs/DESKTOP_FINISH_CAMPAIGN.json). The campaign has **17/78 reviewed packets and 0/13 complete rounds**. Mobile is deferred. Whole-hero/world art and sustained motion remain active work.

Current runtime source is `1236db50`: it adds truthful reload/returning/terminal guidance, authored descent and clearer swamp paving to the earlier focus/resource-sharing work. Test-only successor `93ebba9f` passed [all 37 foundation CI steps](https://github.com/occult-kranti/ANDOLAN/actions/runs/39154538312); the runtime composition also passed its actual native smoke. [The current report](games/yuga-native/docs/evidence/desktop-finish/continuation-oct18b/ROOT_FINAL_REVIEW.md) separates source, candidate builds and public-package evidence. C1–C8 hair studies remain rejected; canonical descent is accepted with explicit motion limits.

**Next work:** follow [the ordered six-owner queue](games/yuga-native/docs/evidence/desktop-finish/continuation-oct18b/NEXT_SIX_OWNERS.md), starting with storage and artifact access before package qualification. Older untracked project work is preserved on [the recovery branch](https://github.com/occult-kranti/ANDOLAN/tree/backup/yuga-workspace-2026-10-18); [the backup manifest and receipt](docs/evidence/workspace-backup-2026-10-18/README.md) describe its scope.

The published `79e5` Linux package passed warm execution in **126.094 s** (7 manual + 9 natural captures) and fresh-user cold execution in **269.549 s** (3 manual + 9 natural captures), both native Quit 0 with zero runtime warnings/errors. W1 and W2 reviewed all **28 originals**: [execution](games/yuga-native/docs/evidence/desktop-finish/continuation-oct18/W1-actual-r1/package-successor-r2/receipt.json) and [independent visual review](games/yuga-native/docs/evidence/desktop-finish/continuation-oct18/W2-package-successor-r2/receipt.json). These captures retain their own scope; the earlier `96d5b9cd` release's 59-screen journey is historical.

**Download the desktop polish preview:** [Linux / Windows](https://github.com/occult-kranti/ANDOLAN/releases/tag/yuga-desktop-polish-2026-10-18), source `79e5c15d8a3657e16fda67acb277b2406120dcd1`, published 18 October 2026 at 16:02:16 UTC (release ID `416542426`). Extract the entire ZIP and run `launch.sh` or `launch.bat`. [Publication receipt](games/yuga-native/docs/evidence/desktop-finish/published/release-polish-r1/publication-receipt.json) records delivery. [Independent public-byte audit](games/yuga-native/docs/evidence/desktop-finish/continuation-oct18/W3-public-audit-r1/receipt.json) passed for all five fresh downloads, 81 ZIP members, the common 550-entry PCK and bundled runtime proofs. Linux was executed; Windows has archive validation only.

Choose **Confluence** or **Bow training**, then the primary action. LMB draws/shoots, Q/E/C/X use Rama’s four abilities, F/G fly and grapple, and F3 opens the ability guide. The native slice includes offline armies, siege vehicles, territory relays, day/night lighting and a separate 24-second combat film. Native online matches, the full hero roster, physical-GPU profiling, Windows execution and [Deadlock-level art/motion quality](games/yuga-native/docs/DEADLOCK_QUALITY_TARGET.md) remain open.

| Working on | Start here |
| --- | --- |
| New chat, contributor or worker | [Project handoff](docs/START_HERE.md) |
| Native UI context and pinned Impeccable guidance | [Product](games/yuga-native/PRODUCT.md) · [Design](games/yuga-native/DESIGN.md) · [Reference pack](games/yuga-native/docs/research/impeccable/README.md) |
| Native build, tests and art pipeline | [Build handbook](games/yuga-native/docs/BUILD_HANDBOOK.md) |
| Production game, features and milestones | [Production roadmap](games/yuga-native/docs/FULL_GAME_PRODUCTION_ROADMAP.md) |
| Mythology, game design and open-source reuse | [Research brief](games/yuga-native/docs/research/RESEARCH_BRIEF.md) |
| Production progress and actual 3D source viewer | [Public snapshot dashboard](https://occult-kranti.github.io/ANDOLAN/production/) · [interactive Rama source](https://occult-kranti.github.io/ANDOLAN/production/viewer/) · [live-worker guide](games/yuga-native/docs/PRODUCTION_OBSERVATORY.md) |
| Laptop + original PS4 Linux + cloud build workflow | [Game-build setup](games/yuga-native/docs/GAME_BUILD_FARM.md) · [research and CPU pilot](games/yuga-native/docs/research/ps4-swarm-oct23/README.md); device execution and GPU-demo output have separate evidence |
| RTX 4070 8 GB local models, Codex/Claude/Kimi and six project skills | [Laptop/squad setup](games/yuga-native/docs/LOCAL_MODEL_SWARM.md) · [skill index](.agents/skills/README.md); laptop inference and the three videos remain unverified |
| AI asset models, reconstruction tools and USA laptop plan | [Historical 21 October study and adoption gates](games/yuga-native/docs/research/ai-pipeline-oct21/README.md); use the newer setup above for current execution evidence |
| Cloud setup, storage and exact recovery | [Workspace guide](docs/WORKSPACE_AND_CLEANUP.md) |

<details>
<summary>Earlier native milestones and deferred mobile plan</summary>

The [48-assignment screen campaign](games/yuga-native/docs/SCREEN_CAMPAIGN.md) and [45-assignment visual campaign](games/yuga-native/docs/VISUAL_ROUNDS_2_4_EXECUTION.json) retain their own accepted and rejected results; they do not count as completed rounds in the active campaign. Historical releases: [Rama preview and five-action video](https://github.com/occult-kranti/ANDOLAN/releases/tag/yuga-rama-hero-2026-10-17), [Triad/siege preview](https://github.com/occult-kranti/ANDOLAN/releases/tag/yuga-traversal-armies-2026-10-17-triad-siege). The [5v5 mobile roadmap](games/yuga-native/docs/MOBILE_PRODUCTION_ROADMAP.md) is planning work; no Android/iOS release is claimed.

</details>

## ANDOLAN browser game

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
