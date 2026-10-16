# ANDOLAN: City of Consequences - replacement Codex prompt
Version 0.3 | 2026-10-15

Build an original browser-native open-world action drama set in a fictional Indian city. This replaces the earlier small board-first concept. The player walks, drives, interacts with a living city, forms a crew, completes cinematic missions, investigates institutional wrongdoing and experiences consequences. The felt board is an in-world headquarters tool, not the whole interface.

Read docs/OPEN_WORLD_PLAN.md completely and preserve its distinction between planned and tested work. The user wants two modes on one website: Private Story (solo/invited crew, branching campaign) and Public City (regional online district instances with random players). Do not substitute a FiveM installation, a streamed native game, an isometric dashboard or local fake multiplayer for a browser-native game.

## Start with evidence and the repository
Inspect the existing repository and available environment. Record branch, commit, uncommitted work, tools and constraints. Preserve unrelated files. Read user instructions and AGENTS.md. No missing repo or environment should be silently invented. This is a planning handoff; no engine build or REA execution has been completed yet.

Use an initial stack spike: TypeScript, PlayCanvas Engine, Rapier, and a Node/Colyseus authoritative room service. Menus may use React, but per-frame entities should not be React state updates. Use Blender/glTF assets with an asset-license ledger and glTF Transform where appropriate. Verify compatible versions from official documentation and pin them. Compare a Three.js-based alternative only through a bounded benchmark if the primary spike fails a criterion. Do not maintain two complete engines.

## How to use REA and reference games
Read https://github.com/morluto/rea and current release/tool availability. The tool assists analysis; it does not automatically port GTA V or grant rights to target software. Setup can change agent configuration and register an MCP server. Follow required approvals before installing, registering persistent integrations or executing native targets. Do not pipe an unknown installer directly into a shell.

Use the workflow: authorized target -> version/hash -> narrow question -> evidence -> behavior SPEC.md -> original implementation or separately licensed code reuse -> held-out regression tests. Prefer direct source inspection when available. Do not use binary analysis just to make the process look sophisticated.

Selected references:
- GTA V/Online: locomotion/vehicle transitions, cinematic pacing, crew invitation and multi-stage job structure.
- Watch Dogs 2: urban crew flow and connected co-op activities; no real hacking instructions.
- Minecraft: bounded item placement, inventory feedback and constructive headquarters customization.
- HITMAN: rich authored venues and multiple approaches, not assassination instruction.
- Ghost of Tsushima: environmental navigation and reduced HUD clutter.
- OpenGOAL: documented state/compiler/reconstruction discipline.
- OpenRW/OpenLara: architectural and portability references, not automatic foundations.
- Sketchbook and eligible browser city repos: selective controller/vehicle reference spikes after per-file license, dependency and asset audit.

The supplied Minecraft/GTA anecdote is NOT verified. Do not assume REA supports standalone JAR analysis. The inspected Java request #1558 reports a missing domain, while Android analysis uses external JADX/JDK. Check the installed tool catalog and exact version. Do not claim 60 seconds confirms all item values. Do not copy example cooldowns, damage or stack limits into the game as observed facts.

## R0 deliverables
Create REUSE_LEDGER.md, REFERENCES.md and one subsystem SPEC.md. For each claim mark observed/documented/inferred/original-design/unknown. Include target commit/hash, code or evidence location, license scope, asset dependencies, intended reuse and unexecuted tests. If runtime access is missing, complete source-level work and say what is blocked; do not claim gameplay observations.

## R1: feel-of-play slice
Build one approximately 500 x 500 m fictional district greybox, but first polish a single city block. Third-person character, camera collision, one car, enter/exit, arcade handling, one interior, traffic placeholders, coherent lighting, sound controls and a complete interaction loop. Original or appropriately licensed assets only. No copied GTA city, characters, radio, UI, logos or missions.

Acceptance: walk -> enter car -> drive -> stop -> exit -> enter room works repeatedly; keyboard/controller settings and camera comfort exist; no actor duplication or stuck input; WebGL2 baseline works; lower graphics settings reduce measured load. Record build, device, frame-time distribution, memory and loading bytes. Targets are not results.

## R2: real private networking
Two independent browser clients join an authoritative server. Both see movement, vehicle occupancy and mission state. Server validates seat claims, action cooldowns, damage, inventory and rewards. Client prediction/reconciliation is allowed; client-authoritative outcomes are not. Test simultaneous seat entry, disconnect in a vehicle, duplicate commands, stale revisions, forged role, lost packets and reconnect. Add four-player support only after the two-player evidence is clean.

## R3: Last Delivery
Implement the opening script in section 09: garage, rain drive, clinic contradiction, authored diversion, return and first board pin. Provide subtitles, skip/reduced-intensity options, assisted driving and checkpoint recovery. Canonical mission state is server-owned. Convert the screenplay to a validated mission graph with allowlisted actions and explicit prerequisites. No arbitrary script execution from uploaded content.

## Later mode targets
Private Story initially 1-4 players, up to 8 only after tests. Public City initially 16 per regional instance, then evaluate 32. Never claim all users share one unlimited world. Public profiles and private campaign saves are isolated. Public stranger actions cannot overwrite private story choices. Build report/block/mute, moderation, transactional rewards, anti-grief rules and crash recovery before public matchmaking.

## Original building mechanic
Implement the section 18 headquarters placement contract only after locomotion and networking are stable. Initial values (our design choices): 0.5 m grid, 90-degree rotation, 100 objects per room, conditional undo of ten personal operations. Validate bounds, collision, doorway clearance, inventory and membership server-side. Concurrent or repeated placements must never double-spend or duplicate objects.

## Narrative and action rules
Use the original cast and 22-mission outline. Direct stylized arcade combat is permitted in fictional encounters, with non-graphic feedback and alternatives. Do not turn this into instructions for violence, sabotage, evasion or attacks on real people/institutions. No real living-person villains, personal target maps or factual allegations inferred from graph proximity. Review-pending Olympus research stays out of the public factual Archive. No political profiling, real protest coordination or targeted recruitment functionality.

## Engineering contracts
Layout: apps/client, apps/server, packages/sim, packages/protocol, packages/content, tools/asset-pipeline, content/world, content/missions, content/dialogue, content/archive, docs, tests.
Implement root commands: npm ci (after lockfile), npm run dev, lint, typecheck, test, test:content, test:network, test:e2e and build. Define commands truthfully; do not claim placeholder test scripts validate nonexistent systems.
Pin content versions, use stable entity IDs, append immutable mission events, deduplicate commands, validate payload sizes and rate limits. Never expose service credentials. No unapproved provider purchases, credential creation or public deployment.

## Website deployment
Static client/CDN plus separate HTTPS/WSS regional servers and a persistence service. GitHub Pages can serve a prototype client, not the game server. Document actual costs after measurements and current vendor quotes. No free-unlimited-hosting assumption. Include immutable asset versions, rollback and save migration tests.

## Execution style
Work in bounded milestones. Use parallel agents only when available and on disjoint modules; do not bypass model/provider limits. After R0-R1, present the actual playable evidence and unresolved decisions before expanding. Keep the open-world goal intact while delivering a small complete proof. Do not spend the first milestone generating thousands of buildings or a massive list of future tasks.

Report exactly what exists: commit, changed files, commands/results, screenshots or verified preview, observed metrics, unknowns and next milestone. A screenshot is not proof of multiplayer; a build is not proof of performance; a design PDF is not a game.
