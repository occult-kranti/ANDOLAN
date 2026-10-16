# ANDOLAN — City of Consequences

**First Edition 0.1: a playable browser city drama.** Explore an original fictional district of Devnagar, drive, meet the crew, compare records and make choices that return later in the story.

This release contains a condensed six-chapter campaign, 22 stages, seven decisions, five endings, an evidence journal, local story saves and real shared server rooms. The larger six-district/22-mission game remains in [the production roadmap](docs/ROADMAP.md).

**Play the solo preview:** [Open ANDOLAN](https://occult-kranti.github.io/ANDOLAN/) and choose **Story**. Progress saves in that browser. Shared rooms require a separately hosted game server.

## Play and develop

Node 22.12 or newer (validated with Node 24):

```sh
npm ci
npm run dev
```

Client port 5173; room server port 3001. Use **Story** for solo play saved in this browser, **Private crew** for invited co-op, and **City sandbox** for an explicitly limited shared test room. A static/downloaded copy needs a separately hosted server for multiplayer.

Controls: WASD or arrow keys to move/drive, Shift to sprint, E to interact, F to enter/exit a vehicle, drag to look, J for evidence, Escape for settings. Gamepad and touch controls are implemented. Settings include graphics, camera comfort, subtitles, larger dialog text, driving assistance and key rebinding.

Solo play pauses while its tab is hidden. Its fixed-step clock catches up with short delays, clears stale controls and limits long-stall recovery.

## Build and deploy

```sh
npm run build
npm run build:standalone
npm start
```

The server serves the production client and WebSocket rooms on port 3001. `dist/standalone/index.html` is a self-contained solo game. Dockerfile and Compose configuration are included; see [deployment instructions](docs/DEPLOYMENT.md). The solo preview is published on GitHub Pages. Shared rooms still require a separately hosted server; running the game inside ChatGPT has not been verified.

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

## Design and research

- [Game design](docs/GAME_DESIGN.md), [product brief](docs/PRODUCT_BRIEF.md), [roadmap](docs/ROADMAP.md)
- [Design library and reading notes](docs/library/README.md): exact sources, game theory, story study, twelve-book reading backlog
- [Original concept art](docs/concepts/README.md): city art direction and the first crew
- [REA research](docs/research/REA_RUNBOOK.md), [mechanics specification](docs/research/VEHICLE_TRANSITION_SPEC.md), [reuse ledger](docs/REUSE_LEDGER.md)
- [Archived supplied handoff](docs/handoff/OPEN_WORLD_PLAN-v0.3.md), treated as design input
- [Third-party notices](THIRD_PARTY_NOTICES.md)
- [Dependency audit](docs/DEPENDENCIES.md): production audit and the recorded build-tool advisory

## Current boundaries

The runtime art is deliberately stylized and procedural; concept paintings are future art targets. Public mode is a development sandbox, with no production accounts, moderation operation, regional matchmaking or economy. Local synthetic network tests do not prove sustained public capacity. The game does not contain commercial game assets, real-world allegations, political profiling or actual protest coordination.
