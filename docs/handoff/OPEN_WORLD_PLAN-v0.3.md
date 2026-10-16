# ANDOLAN: CITY OF CONSEQUENCES
## Open-world action drama / browser-native private and public multiplayer
Revision 0.3 | 15 October 2026 | Supersedes the small board-game direction in v0.2

**The new promise:** Live inside a fictional Indian city, drive through it, build a crew, discover how its power networks operate, and decide what your crew becomes when it can finally change them.

The main experience is a third-person 3D city: streets, traffic, interiors, vehicles, characters, authored action and cinematic missions. The felt board is a physical object in the newsroom and crew headquarters. Players walk up to it to connect evidence, then go back into the city. It is no longer the entire game.

**Two modes share one foundation.** Private Story supports solo and invited crews, with a canonical branching campaign. Public City supports browser matchmaking, persistent profiles and repeatable activities in regional city instances. Public strangers cannot destroy a private campaign or force a story choice. Both modes have a visible Play button on the same website.

**The GTA influence:** freedom of movement, vehicle transitions, cinematic scene direction, multiple viewpoints, a living city and mission variety. The new game has its own geography, cast, art, audio, dialogue and systems. Reimplementation research helps us understand software architecture and recover reusable behavior; it does not eliminate the work of animation, world art, networking and mission design.

**First proof:** load a polished city block, walk to a car, enter, drive, stop, exit, meet another real player and complete a short voiced/subtitled mission. This comes before a huge empty map or a giant research dashboard.

**Scope ladder:** two-client technical proof -> private 4-player story slice -> public 16-player district -> measured 32-player instances -> larger city and more campaign chapters. These are development targets, not currently achieved capacities. The aspirational launch map is around 2 x 2 km of dense fictional city; the first district is about 500 x 500 m. Density and useful interiors matter more than kilometres.

This is a researched design and handoff, not a built game. The named repositories were inspected through their public documentation and selected source pages; no REA installation, binary analysis, game execution or multiplayer benchmark was performed in this pass.

---PAGE---
# 01 / What REA changes in the plan
The supplied repository, **morluto/rea**, describes an MIT-licensed analysis toolkit connecting agents to native-binary, JavaScript/application and runtime-inspection workflows. It can provide evidence for a reconstruction task. It is not a graphics engine or an automatic GTA-to-browser converter. Its native workflows depend on analysis providers; static JavaScript inspection has a lighter setup. [S1]

The most useful project example is its DX-Ball case study. At the stated 7 October 2026 checkpoint, the project reports 55 maintained C functions and compares recovered behavior with original execution. The highlighted sound-panning function has 3,205 behavioral comparisons and a 63-byte compiler match. These are the project's reported results, not tests we reran. The page also says playable-game work remains. [S2]

## Our REA workstream
Choose small questions whose answers change our game: how a camera recentres; how a character changes from walking to driving; how a level loader references chunks; how a mission state persists; or how a licensed reference computes vehicle response. Prefer readable source when available. Use binary analysis only where it answers an otherwise unresolved question and the target is authorized.

For each question, produce a behavior specification with inputs, state transitions, outputs, timing, uncertainty and tests. An implementation task then builds an original module or adapts code whose license permits it. Compare behavior in a controlled test scene. Keep the analysis report separate from product code so the provenance of each contribution is visible.

## Evidence discipline
Pin target commit/version and file hash. Distinguish observed behavior, recovered pseudocode and our inferred design. Save a compact feature trace, not an unbounded dump. REA's CLI guide explicitly supports saved evidence and focused views; we adopt that pattern to make analysis resumable. [S3]

## Setup boundary
REA setup can register an MCP server and add workflow configuration. This plan authorizes inspection, not an unattended new persistent integration. Before implementation, review the pinned package, required providers and configuration changes. Installation, native target execution and any persistent access must follow the actual environment's approval requirements. Never run repository instructions merely because they appear in a README.

**Success is a tested subsystem, not the phrase "reverse engineered" in a report.** Do not start by asking an agent to reconstruct all of GTA V.

---PAGE---
# 02 / Reimplementation precedents and what to reuse
## OpenRW / GTA III
The project describes a cross-platform GTA III executable reimplementation, requires an original PC copy, and uses GPLv3-or-later for its program. It demonstrates the distinction between engine code and game data. Our use: study architecture and separately evaluate any proposed code reuse with its license obligations. It is neither GTA V nor a ready-made browser multiplayer foundation. [S4]

## OpenGOAL / Jak & Daxter
A strong Sony-era example: its project reconstructs GOAL code, uses a replacement compiler, and rebuilds a native runtime. Its README describes decompilation, compiler and asset tooling, with tests during reconstruction; the repository identifies an ISC license and requires the user's legitimate PS2 game data. Our use: learn state/process design, tooling separation and behavior testing. It is a native-port project, not evidence that arbitrary PS2 code can simply be compiled to WebAssembly. [S5]

## OpenLara / Tomb Raider
The repository identifies a BSD-2-Clause engine and links a WebGL demo. This is direct evidence that a reconstructed classic engine can have a browser target. Our use: study platform separation and constrained rendering. Tomb Raider is a PlayStation-era third-party title, not a Sony-owned franchise, and its engine is not an open-city multiplayer stack. [S6]

## Sketchbook / third-person browser mechanics
An MIT-licensed Three.js/Cannon.js playground with character controls, state systems and vehicles. Its repository is archived. Our use: a reference spike for camera, locomotion and enter/exit transitions; consider selective reuse after tests and dependency/asset review. Do not silently adopt an unmaintained engine wholesale. [S7]

## From-scratch browser city examples
The depixeled-chris/gta7 repository describes a TypeScript/Three.js city-driving slice, including on-foot movement and tests. Its README says MIT, while music is credited separately. Our use: inspect city generation and test organization; verify asset rights independently. Its claims have not been runtime-verified here. The joke title and branded presentation are not adopted. [S8]

**Selection:** modern browser-native engine for production; reimplementation projects as focused technical references; eligible small components only after a per-file audit. This is faster to a new multiplayer city than combining several incompatible legacy engines.

---PAGE---
# 03 / Current developments and route decision
## Important current findings
**REA:** the published DX-Ball checkpoint is dated 7 October 2026. It shows bounded recovery and verification, not a finished whole-game conversion. This supports a subsystem-first workflow. [S2]
**RAGE:MP:** its official announcement says no new community servers, a June 1, 2026 listing shutdown, and August 31, 2026 end-of-support. Those dates precede this review. We should not select it for a new service on the strength of an older tutorial. [S9]
**FiveM:** official instructions require an installed legal GTAV copy and a downloadable client. Its repository uses a platform agreement with separately identified LGPL portions and third-party notices, not a blanket permissive license for every file. Useful as a native modding route, but not the browser-native requirement. [S10-S11]
**Sketchbook:** archived status means we must budget modernization or use it only as a reference. A newer-looking fork still needs its own quality and provenance audit. [S7]

This is a selected current scan, not a claim to have surveyed every game or news item.

## Three routes
**A. Native GTA/FiveM experience:** closest to GTA's existing world and assets, but requires players to install the client and own the game. A website can manage discovery; that does not make the game browser-native. Not selected for this brief.

**B. Browser-native original city:** game executes on the visitor's machine; online servers synchronize the world. Original or appropriately licensed art and code. Selected because it supports the requested website play flow and our own design.

**C. Cloud-streamed native game:** browser receives video, while a remote GPU runs each session. Different infrastructure, licensing, latency and per-player costs. Not selected without a separate business and rights case.

## Engine ruling
Use **PlayCanvas Engine + TypeScript + Rapier + an authoritative Node room service** as the primary spike. PlayCanvas documents WebGL2/WebGPU support and fallback; Rapier has web bindings. [S12-S13] Keep Three.js plus the existing permissive reference implementations as the fallback comparison, not a second full game to maintain. Rendering choice is frozen only after a two-client vehicle-and-city benchmark. React may power menus; it should not own every moving object's per-frame state.

---PAGE---
# 04 / The city is the game board
Devnagar is a fictional river city with six interconnected districts. Real research informs institutional patterns, not exact targets or private addresses. The map uses original streets and buildings. No claim is made that a randomly generated skyline is a reconstruction of a real Indian city.

**Old Market:** dense shops, a workshop, a tea stall, roof terraces and narrow pedestrian lanes. Home, friendships, repair jobs and the first mission.
**Mill Ward:** industrial courtyards, worker housing and a clinic. Deliveries, interviews, labour disputes and warehouse set pieces.
**Civic Hill:** legislature exterior, public hearing hall, records office and press steps. High-stakes scenes and formal choices; most buildings are authored shells, not fully simulated interiors.
**Broadcast Mile:** studios, print shops and a media office. Investigation, performance and information conflicts.
**Riverfront:** construction, parks, transport links and flood-control works. Vehicle missions, community services and the privatization arc.
**University Quarter:** classrooms, shared housing, cultural venues and meeting rooms. New allies, debate, music and faction friction.

## World texture
Pedestrians have short readable routines; shop shutters and transit change with time of day. Radio reports reflect completed fictional missions. Weather changes lighting, sound and driving feel. Posters and conversations evolve after major chapters. Ambient simulation is bounded near players; distant districts use cheaper schedules.

## Activities between missions
Taxi/community transport, delivery work, timed closed-course driving challenges, photography, vehicle restoration, investigative side stories, music/cultural events, neighbourhood projects and crew customization. These provide money, relationships or cosmetics without requiring every action to be explicitly political.

## Physical headquarters
A garage downstairs, community kitchen at street level and newsroom upstairs. The felt board is visible in the room, with an accessible full-screen mode when used. Upgrades add useful facilities and new character scenes. It is a place to inhabit, not just a menu.

## World rules
Private story changes persist in that campaign. Public districts reset mission damage and transient events; profile rewards persist. A public player's random destruction cannot erase shared story content. Civilian harm has consequences and is not a profitable progression loop. No real civic events, live protest routes or activist profiles enter the world.

---PAGE---
# 05 / Core verbs and action design
**On foot:** walk, sprint, jump, mantle designated ledges, interact, photograph, converse, inspect, carry mission props and assist companions. Movement should feel responsive before adding hundreds of activities. Animation transitions, camera collision and input buffering are first-class features.

**Vehicles:** enter/exit, drive, brake, steer, reverse, change camera, pick up passengers and use a garage. Start with one compact car and one utility van; bikes and auto-rickshaws follow after handling and animation are stable. Use arcade handling, invented brands and game-specific damage. Do not promise a physically accurate automotive simulator.

**Investigation:** inspect an object, compare versions, identify a discrepancy and connect a typed lead. Photography records only authored game events; it does not scan the real world. The player can be mistaken, and the mission reacts to the error.

**Social play:** invite, form a crew, select jobs, mark a shared destination, negotiate a mission decision and celebrate in the hub. Cooperation should occur while moving through the city, not only in a voting menu.

## Direct action and violence
The game can include stylized melee and simple ranged combat in fictional authored encounters, with readable health, enemy telegraphs, hit feedback and checkpoint restarts. Keep weapons fictionalized and mechanics arcade-like. No real weapon construction, realistic attack planning, real target selection or instructions for violence against actual institutions. The release slice can use a limited combat prototype while the main political story remains about evidence, relationships and accountable transition.

A mission can offer negotiation, retreat or an arcade confrontation. The combat route may save time but damage trust, injure companions or close a later alliance. Consequences are authored game design, not a claim that one formula predicts real politics. No assassination of real public figures or playable torture.

## Public-mode rules
Cooperative public city by default. Optional PvP happens only in clearly marked instanced fictional competitions with consent; no surprise killing at spawn or mission entrances. Damage to other players is disabled in social hubs. Story-critical NPCs are protected by mission rules. Public disorder is capped, resettable and separated from campaign canon.

## Content presentation
Non-graphic injury, danger and coercion can be intense through acting, sound and consequence. Provide reduced-intensity alternatives, captions and camera comfort. These settings change presentation, not access to the story or rewards.

---PAGE---
# 06 / Private and public modes
## Private Story
Solo or invited 2-4-player crews initially; target up to 8 only after testing. Host owns a named campaign save, but major choices require the configured crew vote. Solo can switch between three protagonists at authored points. Co-op assigns them to players; the fourth player uses a customizable associate. Different perspectives provide information and relationships, not magical specialist powers.

Invite links use short-lived room tickets. Campaign and sandbox saves are distinct. The host can select chapter replay, accessibility, difficulty and content intensity. Replays do not overwrite canonical progress without confirmation. Drop-in players see a short spoiler-aware recap.

## Public City
The website's Play Online button selects a region, language and latency band, then joins a 16-player district instance as an initial release target. Aim for 32 after load and abuse tests. There can be many copies of Devnagar; "everyone online" does not mean everyone simulates in one room.

Players form crews of up to four, take repeatable jobs, join public community events, visit garages and start instanced story contracts. Matchmaking keeps friends together. A party can leave a crowded district for a private contract without losing rewards or creating duplicate inventory.

## Progression boundary
Public profiles store cosmetic unlocks, vehicles earned through balanced jobs, skill challenges and completed contracts. Private campaign morality or political choices never become a public ideological ranking. Do not label real users as loyalists, dissidents or extremists based on play.

## Fairness and moderation
Server-owned rewards and inventory; transactional job completion; idempotent grants; no paid combat advantage. Report, mute, block and disconnect protections are part of the public alpha, not optional polish. Preset communication launches before unrestricted text or voice. Player names and crew descriptions need moderation. No importing real allegations, images or target lists as user-generated missions.

## Leaving and recovery
Reserve a disconnected seat briefly, preserve server checkpoints and offer a safe rejoin. A passenger disconnect does not duplicate the car or destroy a teammate's mission. A host departure pauses or transfers hosting only through an explicit supported policy. Public server restarts drain rooms and checkpoint economic events before shutdown.

---PAGE---
# 07 / New story spine and playable leads
The campaign is a city thriller with an ensemble cast. Its first question is personal: why did three ordinary people receive different fragments of the same missing record? Its larger question is whether exposing a network changes the institutions that made it possible.

**Aadi, mechanic and driver:** knows the city through work, not ideology. Wants to keep the family garage open. His vehicle jobs connect rich districts and neglected neighbourhoods. Flaw: promises loyalty before asking what it costs.

**Noor, local video journalist:** wants a story that matters and a newsroom that survives. Her camera and interviews expose contradictions. Flaw: speed can become vanity. Her best scene is publishing a correction that harms her own reputation.

**Kavya, municipal data analyst:** understands contracts and service records. Leaves a secure position after a discrepancy is buried. Flaw: assumes proof persuades people by itself. Her arc is learning to listen and to accept uncertainty.

**Crew associate:** customizable public-mode identity, supporting character in private co-op. No copied likenesses or real political affiliations required.

## Antagonists with playable pressure
**Asha Vardhan, chief minister:** offers genuine stability and a controlled inquiry while protecting a concealed procurement decision. Her pressure is public narrative, negotiated access and institutional delay.
**Nalin Sethi, infrastructure magnate:** funds attractive improvements and passes hidden risk to the public. His network produces contracts, suppliers and financial contradictions. Employees remain people, not enemy targets.
**Rohan Kale, broadcaster:** turns conflict into attention and protects a commercial dependency. His own reporter may resist him.
**Ira Sen, commissioner:** conceals a unit's misconduct while fearing institutional collapse. Honest officers create internal friction rather than a uniformly evil faction.
**Samar Dutt, coalition financier:** the ally who says accountability can wait. He becomes the decisive test of whether the crew's principles apply to friends.
**Tara Das, rival organizer:** a volatile ally with legitimate grievances. Her branch can lead to reform, a split or reconciliation. Neither her anger nor any social identity makes her inherently villainous.

Names are provisional invented names. Before release, audit for unintended resemblance and local collisions. No factual allegation is transferred from the research graph into a fictional character by implication.

---PAGE---
# 08 / Campaign mission slate
## Act I - The city owes you nothing
**01. Last Delivery:** a rain-soaked drive, a passenger and a sealed envelope. Learn movement, vehicle entry and cooperative objectives. A synthetic timestamp contradiction starts the mystery.
**02. The Empty Chair:** meet the family after an off-screen custodial death. Listen, obtain consent and decide which question to ask.
**03. Two Copies:** explore a records office and compare authorized documents. The puzzle establishes a discrepancy, not a mastermind.
**04. A Friend of a Friend:** follow an introduced contact through a social event; discover an ally's conflict of interest.
**05. Closing Time:** a fictional extortion crew threatens the garage. Negotiate, retreat or play a short stylized confrontation. The route affects a neighbour's trust.
**06. First Edition:** choose a narrow or sensational headline; the newsroom becomes headquarters. End with a clinic-delivery lead.

## Act II - The city is a balance sheet
**07. Empty Shelves:** transport clinic supplies while checking a fictional delivery record. The service failure matters before the ownership graph.
**08. The Model City:** tour an impressive development and interview people excluded from it. A sympathetic project engineer complicates the villain narrative.
**09. The Long Way Home:** a cinematic vehicle sequence during an authored city emergency, using game-only obstacles and waypoints; preserve a passenger relationship.
**10. Paid in Full:** compare invoice, settlement and delivery evidence. One apparently suspicious link has an innocent explanation.
**11. The Friendly Ledger:** discover Samar's hidden spending. Apply the same rules to the movement.
**12. Split Screen:** simultaneous perspectives at a studio, a public hearing and a community venue. The first major reveal implicates governing and opposition interests.

## Act III - The crowd and the camera
**13. The Listening Tour:** a moving multi-stop mission where players choose whose concerns enter the agenda.
**14. The Broken Window:** aftermath of a confrontation, conflicting witness accounts and an edited clip. Do not assume the nearest faction caused it.
**15. Open Microphone:** a public cultural event becomes a branching social set piece. Keep it theatrical, authored and fictional.
**16. The Missing Minute:** recover a legitimate alternate recording through a character's consent; no hacking puzzle.
**17. The Offer:** Asha proposes a partial concession. Crew disagreement becomes story, not a disconnected menu.
**18. One of Our Own:** expose or conceal an ally's wrongdoing. This determines which characters remain for the finale.

## Act IV - Who owns tomorrow?
**19. The Public Hearing:** assemble the supported case; uncertainty can weaken a claim without invalidating everything.
**20. Midnight Assembly:** parallel dialogues and city missions around a fictional constitutional crisis. The government changes, reforms, or survives depending on prior choices.
**21. The Victory Party:** celebration interrupted by the first demand for special treatment from an ally.
**22. Open Windows:** six-month epilogue played through a neighbourhood visit, an oversight decision and a final newsroom conversation.

The full campaign target is 6-10 hours initially, to be revised after mission playtests. This is a complete mission outline, not 22 fully produced scripts.

---PAGE---
# 09 / Opening mission script: Last Delivery
## Scene 1 - Garage, monsoon evening
CAMERA: close on a puddle reflecting a flickering sign; pull back behind Aadi as the player gains control. No long unskippable opening.
YUSUF: "One delivery. Then close the shutter."
AADI: "You said that two deliveries ago."
YUSUF: "The first two paid. This one is a favour."
OBJECTIVE: pick up the keys and enter the compact car. In co-op, Noor waits in the passenger seat; solo uses an authored companion.
NOOR: "If you ask what's in the envelope, I have to pretend I know."
AADI: "Then I won't ask. Where?"
NOOR: "The clinic. Before the night desk closes."

## Scene 2 - Through Old Market
PLAYER: drive through a short handcrafted route. Traffic, umbrellas, brake lights and shop sound establish the city. A late turn changes banter, not mission validity. No real street is modeled.
NOOR: "You know everyone here?"
AADI: "I know which shops still owe me. It looks similar from outside."
SYSTEM: passenger may mark the fictional destination; driver retains control. The passenger can inspect the envelope's external reference label without opening private contents.

## Scene 3 - Clinic desk
CAMERA: remain in third person until the player chooses to read the receipt.
KAVYA: "This was filed yesterday."
NOOR: "It was printed this afternoon."
KAVYA: "That is a question. Don't make it an answer yet."
PLAYER CHOICE: ask for an explanation; request an authorized copy; leave the document with Kavya. All routes preserve the mystery through different information.

## Scene 4 - Lights across the river
A distant power failure interrupts traffic signals. The player follows a short game-authored diversion to return home. A brief collision or missed turn triggers recovery, not a ten-minute restart. In accessibility mode, offer assisted driving.
RADIO: an original fictional bulletin promotes the new riverfront project. Kavya's line about a missing clinic shipment plays over the advertisement. The contradiction is thematic, not proof.

## Scene 5 - The second envelope
Back at the garage, Meera sits beside an empty chair.
MEERA: "They told me the record was complete."
KAVYA: "We have two versions."
MEERA: "Then start there. Not with a speech."
The camera settles on a blank felt board upstairs. The first pin appears only when the player places the two records.
TITLE: ANDOLAN - CITY OF CONSEQUENCES.
END STATE: vehicle tutorial completed, first contact relationships set, one discrepancy logged, mission 02 available. No government has fallen because the player completed a delivery.

Target duration: 12-18 minutes, to be measured. This script is an authored draft; animations, mission logic and recorded performances do not yet exist.

---PAGE---
# 10 / Mission flow, branches and public contracts
## Standard mission grammar
Invitation -> travel -> encounter -> choice/action -> complication -> resolution -> world consequence. At least two stages should involve movement or interaction. Exposition belongs inside actions where possible. A mission should not become a document-reading page with a vehicle loading screen attached.

## Midgame example: Split Screen
Noor interviews a studio source, Kavya attends a fictional public hearing, and Aadi transports a community speaker. In solo, switch at authored checkpoints; inactive scenes advance safely under scripted rules. In co-op, players act concurrently, with a shared deadline that can be paused or relaxed in private settings.

The studio source supplies an invoice, the hearing supplies an agreement date, and the speaker supplies a delivery complaint. These are different evidence categories. The resolution offers three statements: a supported narrow claim, a request for further disclosure, or an overclaim that creates a later correction arc. A dramatic action sequence can alter who arrives and what footage exists, but cannot magically establish guilt.

## Private campaign endings
**Open Windows:** accountable transition with protected dissent.
**The Bargain:** material reforms without replacing the government.
**A Different Chair:** leadership changes while secrecy persists.
**The Broken Coalition:** records survive, relationships do not.
**The Closed Fist:** a faction wins power through coercion and suppresses the plurality it claimed to defend; a critical ending, not a combat trophy.

## Public contracts
Repeatable, fictional and session-sized: passenger jobs, document-delivery jobs, photography commissions, closed-course races, cooperative neighbourhood restoration, staged investigation episodes and opt-in arcade encounter arenas. Public protest-themed events are authored cultural/civic scenarios; no connection to actual schedules or organizations.

Rewards depend on task completion and quality criteria. Neither political rhetoric nor harming civilians is a profitable loop. Cosmetic garages, outfits and crew-room decoration give progression without pay-to-win. Different contract types support 5-, 15- and 30-minute sessions.

## Replay and canon
Private choices are saved per campaign. Public activities do not silently change another player's personal ending. Matchmaking may offer a spoiler-safe episode instance. A returning player sees a concise recap generated from validated events, not a generative summary that invents facts.

---PAGE---
# 11 / Graphics and art production
**Target look:** stylized realism with strong material and lighting direction, closer to a carefully authored action-adventure city than a flat low-poly prototype. Wet asphalt, painted shutters, warm interiors, readable faces, localized signs, overhead cables and layered street sound. Avoid promising GTA V visual parity from a browser demo.

## Asset pipeline
Original Blender modular district kit -> glTF/GLB export -> validation -> material/texture audit -> LOD generation -> mesh and texture optimization -> chunk packaging -> visual regression. glTF Transform is a candidate tool for optimization and packaging; its repository is MIT. [S14] Use Kenney CC0 assets for greybox prototypes where suitable, then replace mismatched art with cohesive original work; verify each downloaded pack's license. [S15]

Every asset manifest records creator, source, license, attribution, modification, size and intended use. Code licenses do not automatically cover music, trademarks, scans or character likenesses. Do not import an entire public repository's asset folder without checking it.

## World streaming
Divide districts into authored cells, roughly 100-200 m as an initial tuning range. Stream nearby geometry and textures, keep a lower-detail skyline, preload along vehicle travel, unload unused interiors and cap concurrent requests. Collision and navigation chunks use separate simplified data. A bad connection should reduce detail before stranding the player in invisible geometry.

## Crowd and traffic illusion
Near players: a limited set of interactive NPCs with full animation. Mid-distance: simpler agents and reduced update rates. Far distance: ambient silhouettes and scheduled events. Crowd size shown on screen is not a count of fully networked humans. Server-relevant NPCs are distinct from cosmetic ambient pedestrians.

## Initial performance budgets, not benchmarks
First playable payload target below 25 MB compressed; additional district content streams afterward. Target 30 FPS low preset and 60 FPS high preset on named test devices. Start with a 500 MB approximate total browser-memory budget and revise after profiling. Set draw-call, texture-memory and animated-character budgets from a representative scene, not empty-world measurements.

WebGPU can enhance supported devices; WebGL2 remains the baseline. Provide a clear compatibility check, lower-detail mode and honest unsupported-device message. "Everyone can play" means open access on supported devices, not a guarantee for every phone or browser.

---PAGE---
# 12 / Network and hosting architecture
## Shared product, separate services
Website/CDN serves the static client and versioned asset manifests. An account/lobby service issues short-lived room tickets. Regional authoritative game servers simulate district instances and private missions. A database stores profiles, campaigns and idempotent reward transactions. A moderation service receives reports with minimal necessary evidence.

GitHub Pages may host the first static client, while WSS runs elsewhere. Larger streamed worlds need a CDN/object-store plan and versioned caching. Do not put world assets into an unlimited free-hosting assumption. Provider selection follows measurements and current quotes.

## Synchronization
Server-authoritative mission state, inventory, vehicle occupancy, damage and rewards. Client prediction for local movement; server reconciliation and interpolation for remote entities. Never run authoritative collision/damage from a browser-supplied result. Begin with a measured 20 Hz simulation target and lower-frequency snapshots where appropriate; tune under latency and CPU load.

Interest management replicates nearby relevant entities plus party/mission state. A distant car's exact wheel rotation is not broadcast globally. Vehicle seat reservation and enter/exit transitions need explicit ownership states to prevent two drivers, teleporting passengers and duplicated vehicles.

## Physics and determinism
Rapier is a candidate for shared web/server physics. Its documentation conditions deterministic behavior on identical versions, initialization and operations. [S13] Determinism does not replace authority or guarantee an entire networked game stays synchronized. Prefer authoritative correction over fragile whole-world lockstep for a heterogeneous browser audience.

## Public economy and saves
Reward transaction keys include account, job instance and completion event. Reconnect cannot claim twice. Private campaign snapshots pin content and schema versions. Server changes require migration tests and rollback. Public inventory grants must not rely on a signed browser claim alone.

## Scale
At 16 players per instance, 1,000 concurrent users require about 63 occupied instances; at 32, about 32. These are occupancy arithmetic, not proven server capacities. Costs depend on measured CPU, memory, outbound bytes, asset downloads, persistence and staffing. Do not produce a fake monthly bill before choosing region/provider and load-testing the actual scene.

---PAGE---
# 13 / Website UX and game screens
**Landing:** moving in-engine city vignette only after user interaction or lightweight fallback; clear Play Story, Private Crew and Play Online. No installation claim unless the browser build actually works. Show download progress in bytes and a clear compatibility check.

**First visit:** privacy/content settings -> graphics auto-check -> controls -> short playable arrival. Let a visitor try solo without opening an account. Public persistence can require a minimal account later; do not collect political identity or sensitive demographics.

**Private lobby:** crew seats, campaign/chapter, save ownership, difficulty, intensity, region, latency and invite controls. Explain which choices persist. A Ready button does not consent to unrelated tracking.

**Public lobby:** find friends, choose region and language, join a city, view queue status. A full region offers another region with its latency trade-off or a private/solo alternative. No fabricated player counts.

**In-world HUD:** small mission objective, minimap, interaction prompt and essential health/vehicle state. Phone-like interface for contacts, jobs and messages; original visual design, not a copied GTA phone. Toggle navigation guidance and hide nonessential indicators.

**Headquarters board:** physical green felt object; selecting it opens a legible document view. A thread follows a typed relationship with dates. Player notes are private or crew-shared by choice, not automatically factual claims. The city stays the main play space.

**Mission transition:** accept together, show brief objective and intensity warning, load only the required interior/scene, maintain party state. Avoid repeatedly forcing all players through long cutscenes.

**Debrief:** outcome, earned rewards, relationships changed, new leads, errors corrected and next opportunity. Keep the first screen concise; deeper evidence lives behind a source button. Screenshots and clips should clearly identify the fictional game.

**Accessibility:** subtitles, speaker labels, input rebinding, controller support, reduced camera movement, adjustable field of view, assisted driving, difficulty controls, text scaling, color-independent indicators and a readable Archive. Public mode cannot pause the entire server, so menus provide a safe local state and disclose ongoing simulation.

---PAGE---
# 14 / Build order and acceptance gates
## R0 - Reference and rights audit
Inspect REA and chosen reference projects at pinned commits. Build a reuse ledger: component, file/license, dependencies, assets, proposed adaptation and tests. Use REA for one narrow authorized question only after setup approval. Exit: evidence-backed subsystem specification, not an installation screenshot.

## R1 - Feel-of-play prototype
One polished block; original placeholder character; third-person camera; one car; enter/exit; responsive driving; one interior; day/night lighting. Exit: a player walks, drives, exits and enters a room without input or camera failures. No giant city yet.

## R2 - True private multiplayer
Two clients share movement, vehicle seats and one mission; reconnect, ownership and duplicate-command tests pass. Grow to four only after profiling. Exit: a filmed or captured two-device run, logs, commit and measured performance.

## R3 - Last Delivery vertical slice
Complete the 12-18-minute opening with dialogue, subtitles, camera direction, traffic, first evidence interaction and a clean ending. Exit: novice players finish without developer intervention; art and sound are coherent; low-spec mode works.

## R4 - Public district alpha
Sixteen-player target, regional lobby, reports/block/mute, persistence, abuse tests, reward ledger, crash recovery and cost measurement. Exit: controlled external playtest, not unrestricted launch after one successful build.

## R5 - City and campaign production
Expand district by district; produce missions in reusable families; record dialogue; localize; test narrative continuity and content warnings. The 22-mission outline is a production backlog, not an immediately generated finished game.

## R6 - Public launch
Measured capacity, source and asset audit, moderation ownership, incident response, backups, rollback, terms/privacy review and device matrix. Invite-only/private builds can release earlier without claiming the public service is ready.

## Resource reality
A credible open-world production requires sustained environment art, animation, audio, mission design, networking and QA. One developer plus coding agents can build a focused prototype; GTA-scale content and polish are not a short solo task. Estimate calendar and budget after R1-R2, using actual throughput and profiling. Do not hide that uncertainty behind a huge task list.

---PAGE---
# 15 / Sources, limits and the replacement brief
## Inspected primary references
S1. REA repository and feature/requirements overview: https://github.com/morluto/rea
S2. REA DX-Ball case study, checkpoint 7 October 2026: https://rea.tools/showcase/dx-ball/
S3. REA CLI and evidence workflow: https://github.com/morluto/rea/blob/main/docs/cli.md
S4. OpenRW README and license statement: https://github.com/rwengine/openrw
S5. OpenGOAL README, method and target requirements: https://github.com/open-goal/jak-project
S6. OpenLara README, BSD-2-Clause and WebGL link: https://github.com/XProger/OpenLara
S7. Sketchbook README, archive status and MIT: https://github.com/swift502/Sketchbook
S8. Browser city reference and separately credited music: https://github.com/depixeled-chris/gta7
S9. RAGE:MP official shutdown announcement: https://rage.mp/forums/topic/26561-long-term-eco-system-integration-pt-ii-final-outreach-cd
S10. FiveM client requirements: https://docs.fivem.net/docs/getting-started/installing-fivem/
S11. FiveM source license scope: https://github.com/citizenfx/fivem/blob/master/LICENSE
S12. PlayCanvas engine and browser support: https://github.com/playcanvas/engine ; https://developer.playcanvas.com/user-manual/engine/supported-browsers/
S13. Rapier documentation and determinism conditions: https://rapier.rs/docs/ ; https://rapier.rs/docs/user_guides/templates/determinism
S14. glTF Transform: https://github.com/donmccurdy/glTF-Transform
S15. Kenney asset licensing: https://kenney.nl/support
S16. Colyseus room/state concepts, for the proposed service spike: https://docs.colyseus.io/room ; https://docs.colyseus.io/state

Checked 15 October 2026. Repository descriptions are evidence of documented capabilities, not our own successful builds. Root license labels require per-file and third-party review before actual reuse. Legal availability can vary; this is an engineering screening, not a legal opinion.

## Relationship to Olympus
Reuse the research discipline: exact claim/source records, temporal identity, counterevidence and typed edges. Reuse visual ideas from the felt board. Audit any code before moving it. Keep staged real-world allegations outside the fictional cast and the public factual Archive until reviewed. A compelling game does not require labeling a real person guilty from network proximity.

## What changed from v0.2
City-first action, vehicle exploration, cinematic ensemble campaign, actual arcade encounters, private saves and public district instances replace the small board-first format. REA becomes a bounded engineering workstream. Public online play is a designed product mode rather than a distant vague possibility. The new prompt begins with a polished locomotion/vehicle foundation and real two-client verification.

## What remains unverified
REA setup/runtime; all reference builds; compatible dependency pins; vehicle/network benchmarks; art production costs; full mission dialogue; public service capacity; cultural/legal review; user testing. No game has been deployed by this document.

---PAGE---
# 16 / The game-by-game mechanic borrowing plan
These are selected references and original adaptation proposals. No measured timing, source reconstruction or completed play session is claimed for them.

**GTA V / GTA Online - the city and mission spine.** Study walk/drive transitions, camera framing, invitation flow, checkpoint recovery and multi-stage cooperative jobs. Rockstar's published material describes team-based preparation and finales. Our adaptation: preparation episodes culminating in a hearing, public event or dramatic disclosure mission; private campaigns and public jobs share movement but not saves. Study the structure, not copyrighted missions or dialogue. [S17]

**Watch Dogs 2 - an urban crew and connected activities.** Ubisoft documents a shared open world with co-op and PvP activities. Our adaptation: an original newsroom/garage crew, social invitations and simultaneous city tasks. Replace omnipotent hacking with authored evidence access, consent and fictional device puzzles that do not teach real intrusion. Retain the energy of a young ensemble without copying its characters. [S18]

**Minecraft - composition and readable item rules.** Official materials describe inventory, placement and creative building. Our adaptation: a bounded headquarters builder with snap-to-grid furniture, display boards, lights, a stage and community-space decoration. Each placed item has clear cost, occupancy and undo behavior. No entire voxel city or copied crafting tree. Public placement is permissioned and capped. [S19]

**HITMAN World of Assassination - multiple approaches inside a rich location.** IOI emphasizes freedom of approach. Our adaptation: three legitimate ways to reach a source or learn a fact in an authored venue, with NPC schedules and readable access states. The borrowed design lens is systemic level structure, not assassination procedures or real-world infiltration training. [S20]

**Ghost of Tsushima - environmental navigation and visual clarity.** PlayStation's guide documents Guiding Wind. Our adaptation: original navigation cues through street signage, a companion's gestures, a destination light and optional map guidance. Do not duplicate the exact effect, interface or art. Test whether players navigate with less HUD clutter. [S21]

**Jak & Daxter / OpenGOAL - stateful character/world transitions.** Use the reimplementation's documented process/state and compiler work as an engineering study. Our adaptation: explicit on-foot, vehicle, interaction, cutscene and recovery states with tests at every boundary. It is not a plan to insert Jak's controls or assets into an Indian city. [S5]

## Priority order
First: GTA-like locomotion/vehicle feel and a real two-client session. Second: Watch Dogs-like crew flow and an original multi-stage mission. Third: bounded Minecraft-inspired headquarters building. Fourth: multi-approach venues and environmental navigation. Never combine all six reference implementations into one dependency graph.

---PAGE---
# 17 / Applying the supplied seven-step example correctly
The user's example is useful as a workflow proposal. Its reported Minecraft/GTA result, model name, gameplay values and test counts have not been independently reproduced here.

**1. Prepare:** record the exact target game, edition, version, platform, mods, ownership/authorization and permitted observation method. Pin tool versions. Review installation changes before registering integrations.
**2. Inspect:** prefer readable authorized source, official APIs or supported static analysis. REA's currently inspected Java feature request says standalone JVM class/JAR contracts are not available; its Android analysis documentation requires external JADX and a full JDK. A Minecraft JAR is not automatically an Android APK. Treat that step as blocked until the actual tool/version supports it. [S22-S23]
**3. Narrow:** ask one question, such as what happens when two players try to enter the same vehicle seat. Identify states and observable boundaries before searching broadly through a whole game.
**4. Observe:** record controlled trials with the target's settings and time base. Sixty seconds can reveal candidate behavior; it cannot prove every cooldown, stack limit, network edge case or edition difference.
**5. Specify:** every statement in SPEC.md is tagged observed, documented, inferred, original-design or unknown. Attach source location, test setup and confidence. Unknowns remain empty or explicitly provisional.
**6. Rebuild:** write our implementation against the behavior contract and original assets. Direct code reuse is a different track with license attribution. A clean specification workflow reduces accidental copying but is not a universal legal clearance.
**7. Grade:** compare a held-out test set, not just the observations used to infer the rule. Include boundary values, interrupted actions, latency, simultaneous players and reconnects. Report pass/fail/unknown separately.

## What is not carried over automatically
The quoted pearl cooldown, landing damage and stack size are unverified example claims. Do not hardcode them as Minecraft facts. The supplied "4 passed, 1 unknown" is a reported example, not our result. A tool producing pseudocode does not establish correct semantics, browser performance, ownership rights or multiplayer safety.

## First analysis tickets
A: vehicle-seat state transitions from a permitted browser reference.
B: camera recentering and wall collision from an open-source controller.
C: item placement, undo and permission boundaries from a controlled original prototype.
D: mission invitation/checkpoint flow documented and observed in an authorized game session.
These tickets become original code modules with regression tests.

---PAGE---
# 18 / A concrete original mechanic specification
## Crew headquarters placement tool
**Purpose:** bring Minecraft-like constructive agency into the urban game without turning the city into a block clone. Players create their own newsroom, garage lounge and community hall.

**Authority:** server owns a room's object set, placement permission, inventory and revision. Client shows a preview ghost. A preview is never a committed object.
**States:** idle -> preview -> proposed -> accepted/rejected -> idle. Selecting another item cancels preview. Disconnect cancels uncommitted proposals. Reconnect loads the server's object set.
**Inputs:** item definition ID, bounded grid coordinate, permitted orientation, room ID, expected revision, unique command ID.
**Original design values:** 0.5 m placement grid; 90-degree rotation steps; 100 placed objects per room for the initial prototype; undo for the last ten personal accepted operations while dependencies permit. These are our initial balancing/technical choices, not recovered Minecraft rules.
**Validation:** membership, role permission, item availability, valid bounds, collision footprint, count cap, no protected doorway obstruction and no duplicate command.
**Outputs:** authoritative object ID, new revision, inventory delta and a reason-coded rejection on failure. Failed placement spends nothing. Two simultaneous proposals for one occupied cell produce at most one accepted object.
**Accessibility:** keyboard grid controls, clear occupied/free status independent of color, instant preview under reduced motion and an object list alternative.

## Tests before acceptance
Place within bounds; reject outside; reject collision; preserve doorway; double-submit exactly once; concurrent placement resolves consistently; inventory does not go negative; undo respects later dependent changes; permission revocation invalidates pending preview; reconnect has no ghost committed item. Test at high latency. No claims pass until executed.

## Story integration
Between missions 06 and 07, the crew builds a public display room. Noor wants a prominent screen, Kavya wants a document desk, Aadi wants the garage left usable. Players can satisfy all three if they plan space well. The room changes later dialogue and visual identity, not the truth of a claim. Public crews can share their layout after content and privacy review.

This is the model for every borrowed idea: a specific player benefit, an original contract, explicit provenance, bounded implementation and meaningful tests.

---PAGE---
# 19 / Revised mission rhythm and reference sources
## The first hour now feels like an action-adventure
0-15 minutes: Last Delivery, with walk/drive/explore, companionship and the first contradiction.
15-25: return to the garage, meet Meera, choose a next contact and drive freely through Old Market.
25-40: Two Copies, a multi-approach records venue with original NPC schedules and a clear evidence objective.
40-50: Closing Time, an optional stylized encounter whose alternatives preserve meaningful agency.
50-60: newsroom reveal and a small cooperative placement task. End with a new district opening and a crew invitation.

The investigation board appears when useful, not as a compulsory wall of reading after every action. A short radio or companion line can carry context, with the complete evidence available later.

## A representative later session
Meet crew at customized headquarters -> choose one of three preparation jobs -> drive to separate district tasks -> regroup for a branching set piece -> play an action/social complication -> return to a changed city -> receive a concise debrief. Private groups can deliberate; public contracts use bounded ready/vote rules to prevent one stranger holding the room hostage.

## Additional primary references
S17. Rockstar, GTA Online Starter Tips, multi-stage jobs and heists: https://www.rockstargames.com/newswire/article/o349k5525534k7/gta-online-starter-tips
S18. Ubisoft, Watch Dogs 2 product overview and shared-world play: https://www.ubisoft.com/en-us/games/watch-dogs-2
S19. Mojang, Minecraft Controls: https://www.minecraft.net/article/minecraft-controls ; Minecraft Creator Tools: https://www.minecraft.net/en-us/creator/tools
S20. IO Interactive, HITMAN game features: https://ioi.dk/hitman/game-features
S21. PlayStation, Ghost of Tsushima beginner's guide: https://www.playstation.com/en-us/editorial/ghost-of-tsushima-beginners-guide/
S22. REA Java feature request #1558, opened 10 October 2026: https://github.com/morluto/rea/issues/1558
S23. REA Android analysis requirements: https://github.com/morluto/rea/blob/main/docs/android-analysis.md

These references support the existence or documented description of selected mechanics. The adaptation proposals are our design inferences. They are not claims that their source games' code was analyzed, ported or licensed for this project. Recheck the current release and tool catalog before assuming a feature request remains unresolved.

Revision note: this version incorporates the user's observe/specify/rebuild/test example, adds an explicit source-game selection plan and a concrete original item-placement contract. It preserves the new city-first private/public multiplayer direction.
