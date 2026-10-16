# YUGA: Confluence

An original 3v3 third-person arena prototype in Sangam City. Fourteen epic-inspired heroes, forty-two abilities, three lanes, escort/siege minion waves, towers, vulnerable cores, match upgrades, pickups and an eight-minute finish. All heroes are unlocked. Competitive online play is the direction; bots support practice and fill team slots.

The character pipeline has exported fourteen skinned GLBs from MakeHuman's CC0 anatomical mesh, rig and weights, with authored hero proportions, costumes, hair, weapons, materials and motion. Their file sizes and hashes match the [asset manifest](art/hero-assets.json). The city and gameplay effects use original runtime geometry. Illustrated character sheets and the lobby remain concept art. Full deformation and fourteen-hero browser acceptance are separate checks in the [QA ledger](docs/QA.md); a completed export is not proof of finished visual quality. This art pass does not claim parity with the key art or a commercial game's characters.

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
npm run yuga:e2e
npm run yuga:build
npm run yuga:start
```

Deploy or serve the **entire `dist/yuga/` directory**, including its hashed GLB assets. JavaScript/CSS may be inlined, but the character files are external: copying or downloading only `index.html` is insufficient. A static HTTP host can run Practice without the arena backend; online matches need a reachable secure arena server. The production Node service serves the static bundle and `/ws` together. See [deployment](docs/DEPLOYMENT.md) for Docker, Render and GitHub Pages. Publishing the static bundle does not provision a public multiplayer backend.

## Play

Choose a hero and select **Play with bots**. For **Online team match**, enter a shared arena server and leave room blank to create a room; share its invite link with teammates. Bots occupy available seats. A match accommodates six human/bot heroes total. Reconnecting resumes the same hero while its reservation remains valid; an older tab yields ownership to the newer connection.

Move with WASD or arrows; aim by captured mouse, drag or IJKL; fire with click or F; use Q/E/R for abilities; Space jumps. B opens upgrades near spawn. Escape opens settings and releases the cursor. Touch provides movement/aim surfaces and fire/jump/ability buttons. Practice pauses in menus; online team matches continue.

Optional target lock uses **T**, right-click or the touch **LOCK** button when enabled in Settings. It acquires a visible enemy hero, minion or vulnerable structure within 32 metres and 20 degrees of the current aim. Manual mouse/drag/IJKL aim releases it, as do lost visibility/range and menu transitions. Lock assists aim; you still fire, projectiles can miss or be blocked, and the server decides hits. Its current integration requires the final native-input QA gate, alongside the new art pass.

Rama's R prepares a locked three-arrow volley; Hanuman's R commits to a timed leap whose landing damages enemies and heals allies; Sita's R establishes a fixed shielding/healing sanctuary. Their preparation locks actions and shows cast progress. The other thirty-nine abilities use the established projectile, area, movement, support and summon rules.

Push with allied minions. Destroy two defending towers to expose that team's core, then destroy its core. At eight minutes the higher score wins; core health breaks a tied score. Credits buy three ranks of power, vitality or tempo at your spawn. Credits and upgrades reset for every match.

## Design and evidence

- [Implementation contract](docs/IMPLEMENTATION_CONTRACT.md): shared interfaces and finite release gates.
- [Mythology and roster](docs/MYTHOLOGY_AND_ROSTER.md): fourteen original kits and exactly which source excerpts informed them.
- [Hero art bible](art/HERO_ART_BIBLE.md), [art direction](docs/ART_DIRECTION.md) and [pipeline evaluation](art/PIPELINE_EVALUATION.md): model/rig/effect requirements, actual asset route and remaining quality gaps.
- [Mechanics research](docs/MECHANICS_RESEARCH.md), [REA analysis](docs/REA_ANALYSIS.md), [reuse ledger](docs/REUSE_LEDGER.md): inspected sources, license boundaries and research limitations.
- [Review panel](docs/PANEL.md), [QA](docs/QA.md): observed defects, accepted changes, verification and remaining limits.
- [Audio design](docs/AUDIO_DESIGN.md): synthesized original audio, browser lifecycle and bounded voices.

The [AI balance matrix](docs/evidence/balance-matrix.json) contains 168 mirrored lane/seed matches under a fixed bot policy; it is not a human win-rate estimate. Earlier browser and container checks are labelled baseline evidence. Final exported-asset, native-browser, deployment and public WSS checks remain distinct gates. Public Deadlock footage was not accessible in this environment; the [tooling study](art/DEADLOCK_VIDEO_AND_TOOLING.md) records sources actually read without claiming video viewing or proprietary asset extraction.

The earlier ANDOLAN game remains a separate application at the site root. This branch's Pages workflow assembles both applications, with YUGA under `/yuga/`. A later deployment from `main` must include this assembly step to retain the new path.
