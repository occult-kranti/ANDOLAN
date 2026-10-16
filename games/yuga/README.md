# YUGA: Confluence

An original 3v3 third-person arena prototype in Sangam City. Fourteen epic-inspired heroes, forty-two abilities, three lanes, soldier/watch/minister waves, king-led siege pushes, four neutral jungle courts, contestable gold shards, towers, vulnerable cores, match upgrades, pickups and an eight-minute finish. All heroes are unlocked. Competitive online play is the direction; bots support practice and fill team slots.

The character pipeline has exported fourteen skinned GLBs from MakeHuman's CC0 anatomical mesh, rig and weights, with authored hero proportions, costumes, hair, weapons, materials and motion. Their file sizes and hashes match the [asset manifest](art/hero-assets.json). Seven separate soldier/guardian GLBs add four animation clips each and 4.27 MiB of artwork; their provenance and actual previews are in the [unit build record](art/UNIT_ASSET_BUILD.md). The city and gameplay effects use original runtime geometry. Illustrated character sheets and the lobby remain concept art. Full deformation and fourteen-hero browser acceptance are separate checks in the [QA ledger](docs/QA.md); a completed export is not proof of finished visual quality. This art pass does not claim parity with the key art or a commercial game's characters.

## Run

From the repository root, use Node 24 and the existing lockfile:

```sh
npm ci
npm run yuga:dev
```

The development client uses port 5180; the authoritative server uses 3005. The client proxies `/ws` and `/health` to that server. These are internal development addresses, not public previews.

```sh
npm run yuga:typecheck
npm run yuga:test
npm run yuga:assets
npm run yuga:unit-assets
npm run yuga:e2e
npm run yuga:build
npm run yuga:start
```

Deploy or serve the **entire `dist/yuga/` directory**, including its hashed GLB assets. JavaScript/CSS may be inlined, but the character files are external: copying or downloading only `index.html` is insufficient. A static HTTP host can run Practice without the arena backend; online matches need a reachable secure arena server. The production Node service serves the static bundle and `/ws` together. See [deployment](docs/DEPLOYMENT.md) for Docker, Render and GitHub Pages. Publishing the static bundle does not provision a public multiplayer backend.

To create a downloadable browser package (Python 3 required):

```sh
npm run yuga:package
```

This builds first, verifies all 21 GLBs against their manifests, and writes `dist/yuga-confluence-browser-beta.zip` with `START_HERE.txt` and file hashes in `BUILD_INFO.json`. Extract the whole ZIP and serve that directory over HTTP. It includes local bot Practice; online matches still require a separately configured protocol-2 HTTPS/WSS server. The [earlier clean-worktree package check](docs/evidence/coastal-browser-package.json) verified the 24,855,707-byte `d1e7450` build, now preserved as `dist/yuga-confluence-browser-beta-d1e7450.zip`. The accepted ownership repair at `0d326b0` awaits a freshly verified replacement package. Package integrity does not establish public availability.

## Play

For a first match:

1. Choose any hero and **Play with bots**. Keep **Practice focus → Free play**, or choose one optional action to try. The hero's first-action hint and expandable guide are available before starting.
2. Follow an allied wave. Break two defending towers to expose the opposing core; at eight minutes the score decides an unfinished match. Press **B** near your spawn to spend match gold on Power, Vitality or Tempo.
3. Open **Settings → City lighting** for **Fixed night**, **Fixed daylight** or the default cycle. Low visual quality and reduced motion are separate preferences.
4. To visit the new west marsh, follow **Ghat promenade** toward the middle of the map, then head outward toward **West Reed Court**. Its shallow patterned water is walkable; the gold coastal gate beyond the western boundary is scenery. The court guardian first appears at 30 seconds. Return to the wave whenever you choose.

Optional goals cover movement, a hit, an ability, an upgrade or a camp reward. Dismiss a goal at any time, retain it through pause/settings, or start fresh on replay. Its receipt records the observed action and grants no extra currency or mastery rank.

For **Online team match**, enter a shared arena server and leave room blank to create a room; share its invite link with teammates. Bots occupy available seats. A match accommodates six human/bot heroes total. Reconnecting resumes the same hero while its reservation remains valid; an older tab yields ownership to the newer connection.

Move with WASD or arrows; aim by captured mouse, drag or IJKL; fire with click or F; use Q/E/R for abilities; Space jumps. B opens upgrades near spawn. Escape opens settings and releases the cursor. Touch provides movement/aim surfaces and fire/jump/ability buttons. Practice pauses in menus; online team matches continue.

**City lighting** follows the eight-minute match through dawn, day, dusk, night and predawn. Settings can hold Fixed daylight or Fixed night and save that choice. Lighting changes presentation only; combat and target visibility rules stay the same. Reduced motion also suppresses diya flicker.

Optional target lock uses **T**, right-click or the touch **LOCK** button when enabled in Settings. It acquires a visible enemy hero, lane unit, jungle guardian or vulnerable structure within 32 metres and 20 degrees of the current aim. Manual mouse/drag/IJKL aim releases it, as do lost visibility/range and menu transitions. Lock assists aim; you still fire, projectiles can miss or be blocked, and the server decides hits. See the QA ledger for the exact native-input checks and outstanding gates.

Rama's R prepares a locked three-arrow volley; Hanuman's R commits to a timed leap whose landing damages enemies and heals allies; Sita's R establishes a fixed shielding/healing sanctuary. Their preparation locks actions and shows cast progress. The other thirty-nine abilities use the established projectile, area, movement, support and summon rules.

Push with allied minions. Destroy two defending towers to expose that team's core, then destroy its core. At eight minutes the higher score wins; core health breaks a tied score. Credits buy three ranks of power, vitality or tempo at your spawn. Power improves primary damage and applicable ability payloads, Vitality adds health, and Tempo increases basic firing rate without changing skill cooldowns. The forge shows actual effects, current price and hero-specific tradeoffs. Credits and upgrades reset for every match.

Lane defeats give nearby allies 10 credits each and leave an 8-credit shard. A primary shot can secure a shard for either team immediately; proximity collection starts after one second. Unclaimed shards expire after twelve seconds. Banked credits cannot be stolen. Summons award neither gold nor tiebreak points.

Four wild courts awaken at 30 seconds. Reed Naga grants ward, Grove Yaksha grants regeneration, and Cloudwing grants haste. A defeated guardian provides 30 nearby-team credits, a contested 30-credit shard, and a twelve-second power for the living finishing hero. Retreating beyond the leash resets the guardian without a reward; a defeated court returns after forty seconds. Camp diamonds, shard markers and remaining-power badges make this state visible. Detailed rules and original fictional unit identities are in [Minions and jungle](docs/MINIONS_AND_JUNGLE.md).

Client and server now use **protocol 2**. Update both together; an old server cannot represent neutral combat or the contested economy. The loading screen supports **Back to heroes** and Escape, and canceled loads cannot start a late match.

## Design and evidence

- [Implementation contract](docs/IMPLEMENTATION_CONTRACT.md): shared interfaces and finite release gates.
- [Mythology and roster](docs/MYTHOLOGY_AND_ROSTER.md): fourteen original kits and exactly which source excerpts informed them.
- [All-roster mechanics review](docs/ROSTER_MECHANICS_REVIEW.md): all 42 actual skill payloads, counters, shared hit volumes and the shield/reconnect/full-body-cast repairs.
- [Hero art bible](art/HERO_ART_BIBLE.md), [art direction](docs/ART_DIRECTION.md) and [pipeline evaluation](art/PIPELINE_EVALUATION.md): model/rig/effect requirements, actual asset route and remaining quality gaps.
- [Mechanics research](docs/MECHANICS_RESEARCH.md), [REA analysis](docs/REA_ANALYSIS.md), [reuse ledger](docs/REUSE_LEDGER.md): inspected sources, license boundaries and research limitations.
- [Player-experience review](docs/PLAYER_EXPERIENCE_REVIEW.md): accessible sources, unresolved feedback and concrete safeguards.
- [Reddit research](docs/REDDIT_RESEARCH.md): official API sampling, source handling and limits; [Deadlock](docs/research/DEADLOCK_ENGINEERING.md), [Overwatch](docs/research/OVERWATCH_ENGINEERING.md) and [Dota 2](docs/research/DOTA2_ENGINEERING.md) studies distinguish available tools from commercial game source.
- [Review panel](docs/PANEL.md), [QA](docs/QA.md): observed defects, accepted changes, verification and remaining limits.
- [Next-phase three-round review](docs/NEXT_PHASE_PANEL.md), [production roadmap](docs/PRODUCTION_ROADMAP.md): optional guidance, day/night readability, source decisions and separate new acceptance gates.
- [Lanka/coast source notes](docs/LANKA_COAST_RESEARCH.md): selected literary motifs, original marsh composition and the three new community-access failures; no unread feedback is attributed to them.
- [Audio design](docs/AUDIO_DESIGN.md): synthesized original audio, browser lifecycle and bounded voices.

The [current AI balance matrix](docs/evidence/jungle-balance-matrix.json) contains 168 mirrored lane/seed matches under a fixed bot policy; it is not a human win-rate estimate, and bots do not deliberately farm jungle camps. The jungle baseline passed targeted browser tests, a native 480-second finish/replay, local stress, the 21-asset container and built root/nested checks.

Current runtime `0d326b0` fixes a reproduced gallery-to-Practice startup race and passes [all five local hero-assets cases](docs/evidence/next-phase-gallery-ownership-after-check.json), including the ownership regression, fourteen heroes' 42 actual abilities and independent skin/defeat checks. Earlier guidance, camp and recording passes retain their original source identities. The [next-phase panel](docs/NEXT_PHASE_PANEL.md) records failures, repairs and exact evidence limits; a new package, full CI and public smoke remain open. Public WSS remains unprovisioned.

The separate silent `dist/yuga-actual-render-review.zip` contains the actual-render reel, 23 chapters, contact sheets and provenance from the recorded `d1e7450` build. Its [capture summary](docs/evidence/actual-render-art-review-summary.json) and [independent encoding audit](docs/evidence/next-phase-art-encoding-independent-check.json) pass: 160 shots, 2,028 source frames, all fourteen heroes/42 abilities, seven units and six city views. Ability/unit fixtures and staged coast views are labelled; the gallery shows six clips per hero. This review archive is distinct from the playable browser ZIP and does not validate the later startup repair, performance or commercial-art quality. The [tooling study](art/DEADLOCK_VIDEO_AND_TOOLING.md) records actual source reading without claiming watched Deadlock footage or proprietary asset extraction.

The earlier ANDOLAN game remains a separate application at the site root. This branch's Pages workflow assembles both applications, with YUGA under `/yuga/`. A later deployment from `main` must include this assembly step to retain the new path.
