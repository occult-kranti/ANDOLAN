# TF2 source study for original YUGA Triad relays

Reviewed 17 October 2026 UTC. This study supports the next **offline native map prototype**: three lane relays, contested ownership, bounded supply and clearer troop-attack markers. It does not report those features as implemented or close a full-game production gate. The [source ledger](tf2-reuse-sources.json) records immutable revisions, retrieval times, content hashes, reading ranges and access failures.

**Decision:** retain Godot 4.6.3, Blender and original YUGA assets. Use the official TF2 gameplay source to study behavior and failure cases, then implement original rules through YUGA's existing fixed-step simulation. No upstream game code, maps, models, textures or sounds were imported. The earlier [reuse study](REUSABLE_GAME_SYSTEMS.md) inspected the Source camera; this pass inspects capture, payload, dispenser and objective presentation code at the same verified revision.

## Round 1 — verify the sources and their limits

### Official source is available; a source release is not a general asset license

The public [Valve Source SDK 2013 repository](https://github.com/ValveSoftware/source-sdk-2013/tree/be57e3d01ac7d7aa6a2cacbfef187c0b46616db0) resolved to **`be57e3d01ac7d7aa6a2cacbfef187c0b46616db0`**, commit dated 10 October 2026. Its README says, “Contains the game code for Half-Life 2, HL2: DM and TF2.” This is an official Valve publication, not a leaked-source mirror or recovered original code from a reverse-engineering tool.

The complete [Source 1 SDK license](https://github.com/ValveSoftware/source-sdk-2013/blob/be57e3d01ac7d7aa6a2cacbfef187c0b46616db0/LICENSE) was read. Its grant concerns a “modified Valve game running on Valve's Source 1 engine,” with free distribution and stated notice/Steam conditions. It is not a permissive Godot code foundation or a grant to reuse TF2 commercial artwork. Keep inspected SDK files in research scratch; no port of this code is proposed. SDK build instructions require the relevant Steam SDK/runtime, and were not executed here.

Public game source answers these selected questions more directly than disassembling a client. REA/Ghidra remains useful for a separately scoped binary-analysis question with an available input and recorded rights/provenance; neither tool was exercised in this pass. Source 1 TF2 findings do not establish Source 2, Deadlock, Dota 2 or Overwatch implementation details.

### Selected implementation evidence

All rows below refer to the immutable Valve revision above. Reading covered the stated ranges, not the complete repository. Mode flags and class-specific branches matter; these observations are not a claim that every current live TF2 mode behaves identically.

| Source and inspected range | Observed implementation | Transferable YUGA question |
| --- | --- | --- |
| [trigger_area_capture.cpp, L304–465 and L543–635](https://github.com/ValveSoftware/source-sdk-2013/blob/be57e3d01ac7d7aa6a2cacbfef187c0b46616db0/src/game/server/trigger_area_capture.cpp#L304-L465) | `CaptureThink` filters living, eligible capturers separately from players allowed to block. It counts competing teams, updates blocked/client state, and advances/reverses/decays progress under mode rules. A guard addresses repeated `StartTouch`-driven thinking when several players enter together. | Can one fixed-tick aggregate produce exactly one capture result, including simultaneous opposing arrivals and duplicate contact events? |
| [team_train_watcher.cpp, L644–694](https://github.com/ValveSoftware/source-sdk-2013/blob/be57e3d01ac7d7aa6a2cacbfef187c0b46616db0/src/game/server/team_train_watcher.cpp#L644-L694) | `InternalSetNumTrainCappers` distinguishes no capturers **and not blocked** from contested presence. It starts a recede deadline once, uses configured/overtime variants, or cancels that countdown when conditions change. | Should contest pause ownership/supply while abandonment uses its own explicit policy? Avoid treating both as the same state. |
| [tf_obj_dispenser.cpp, L552–600, L626–714 and L901–951](https://github.com/ValveSoftware/source-sdk-2013/blob/be57e3d01ac7d7aa6a2cacbfef187c0b46616db0/src/game/server/tf/tf_obj_dispenser.cpp#L626-L714) | Disabled dispensers clear healing targets. Periodic checks remove stale/dead/far targets and reevaluate eligibility; `CouldHealTarget` checks visibility unless a flag disables it, life and team/disguise rules. Metal dispensing bounds the grant by stored stock and deducts the actual accepted amount. | Recheck range, vertical band, LOS, eligibility and resource cap at service time; do not rely solely on exit events. Keep supply receipts bounded and idempotent. |
| [hud_controlpointicons.cpp, L287–322](https://github.com/ValveSoftware/source-sdk-2013/blob/be57e3d01ac7d7aa6a2cacbfef187c0b46616db0/src/game/client/hud_controlpointicons.cpp#L287-L322) | `UpdateImage` chooses owner/locked icons and a separately controlled overlay from objective state. | Can neutral, owned, contested and unavailable relays be understood through shape/text as well as team color? |
| [tf_hud_escort.cpp, L818–844 and L890–962](https://github.com/ValveSoftware/source-sdk-2013/blob/be57e3d01ac7d7aa6a2cacbfef187c0b46616db0/src/game/client/tf/tf_hud_escort.cpp#L818-L844) | The UI derives remaining time from a recede deadline, clamps it, and manages blocked/countdown/speed/player-count displays so conflicting status elements do not all show together. | Use one state-derived status, one progress value and one deadline; do not let competing labels obscure the next action. |
| [tf_objective_resource.cpp, L1–155](https://github.com/ValveSoftware/source-sdk-2013/blob/be57e3d01ac7d7aa6a2cacbfef187c0b46616db0/src/game/server/tf/tf_objective_resource.cpp#L1-L155) | This inspected TF-specific table chiefly publishes Mann vs. Machine wave/count/timing fields and initializes their arrays. It is **not** the complete generic control-point replication implementation. | Keep bounded relay summary data explicit, but do not claim this file proves YUGA networking or a complete TF2 capture protocol. |

The exact capture-rate formula between the inspected ranges, complete payload movement, all dispenser subclasses, generic objective replication, full shader pipeline, matchmaking and runtime behavior were not audited. No TF2 client, match, replay, map or executable was downloaded or run.

### Three community repositories, three different jobs

A dedicated source-review worker pinned the following repositories, inspected their licenses and selected implementation/docs, then independently recomputed the twelve downloaded file hashes. The ledger includes exact paths and reading ranges.

| Repository / immutable revision | Verified scope and code terms | Useful next step / limit |
| --- | --- | --- |
| [BSPSource](https://github.com/ata4/bspsrc/tree/eaac417f16d3a4d8ef55bb637ecd7bff28740209), `eaac417f16d3a4d8ef55bb637ecd7bff28740209` | Source 1 BSP → Hammer VMF decompiler. Explicit `TeamFortress2Def.java` identifies TF2/BSP 20 and TF2 entity names. Tool code has an Unlicense dedication; dependencies retain Apache-2.0/BSD-3-Clause notices. | A future bounded map-structure study could use appropriately licensed inputs. README excludes GoldSrc and Source 2 and notes consumed authoring entities cannot always be restored. Extractable embedded models/materials do not become licensed for reuse. No BSP decompilation was performed. |
| [mastercomfig](https://github.com/mastercomfig/mastercomfig/tree/d947673e721d686a64a3e7055f38197556a3405b), `d947673e721d686a64a3e7055f38197556a3405b` | MIT TF2 configuration/customization framework. Modules group related settings and document graphics/network tradeoffs. Hardware-impact labels are described as relative estimates, not precise measurements. | Adapt the **idea** of clear quality presets and named tradeoffs after profiling YUGA. This supplies neither portable Godot networking nor a game engine/asset pack. Upstream FPS/smoothness claims were not benchmarked. |
| [TrenchBroom](https://github.com/TrenchBroom/TrenchBroom/tree/4f9e04354d574b71e32dafecfb78ed45a456e5e5), `4f9e04354d574b71e32dafecfb78ed45a456e5e5` | Quake-oriented brush/entity editor; inspected code declares GPL-3.0-or-later. Valve 220 denotes a Half-Life-era MAP format; the `Teamfortress.fgd` reference occurs in the **Quake** configuration. | Original brush-authoring workflow is a possible separate experiment. The inspected format enum does not establish VMF/TF2 support. Do not adopt it as a direct TF2→Godot converter. README/manual and implementation disagree about Quake 3 patch support; no runtime test resolved that drift. |

Hammer is identified by BSPSource as Valve's level editor; Hammer's own installation/license and a TF2 map-editing workflow were not evaluated. A tool's software license does not license third-party input art, and a GPL editor does not automatically make every independently authored output GPL. No community code was integrated in this milestone.

### Access failures retained, not turned into research claims

The ordinary request to [`r/tf2/top.json?limit=5&t=month`](https://www.reddit.com/r/tf2/top.json?limit=5&t=month) returned **HTTP 403 HTML**, not posts. No new Reddit criticism, player consensus, mythology or art corpus was read. No retry through a bypass/proxy was attempted.

The official [Valve publications page](https://www.valvesoftware.com/en/publications) and the requested [Illustrative Rendering in Team Fortress 2 paper](https://cdn.akamai.steamstatic.com/apps/valve/2007/NPAR07_IllustrativeRenderingInTeamFortress2.pdf) were blocked by the session proxy with **403**. The paper was not downloaded or read; this study makes no claims derived from its contents. Existing retained feedback and art research remains separately indexed in [RESEARCH_BRIEF.md](RESEARCH_BRIEF.md). No new full book or video was studied in this pass.

## Round 2 — original Triad relay design recommendations

These are **YUGA-authored recommendations**, not extracted TF2 rules or proof of implementation. The map/gameplay owner owns the final versioned tuning and troop eligibility. Preserve the existing native offline/browser multiplayer boundary and [production rules](../GAME_DESIGN_MASTER.md).

### Objective, supply and presentation contract

1. Place one clearly named relay per lane using the canonical native map manifest. Keep the three lanes, cross-lane rotation routes and troop corridors readable. Relay architecture can echo a temple beacon, a transit signal and a coastal shrine through original geometry; a captured station must not silently add collision or close a route.
2. Aggregate occupants once per fixed simulation tick. Deduplicate entity IDs; require valid team, living/active status where that system exists, horizontal range and an explicit vertical band. Native flight makes XZ-only occupancy insufficient. Decide troop versus hero capture weights explicitly; do not infer TF2 class weights or allow physics callback order to decide ownership.
3. Derive capture state from ownership, eligible presence and progress: neutral, capturing, contested and owned; add disabled/locked only if the rules need them. Opposing eligible presence freezes capture. Specify separately whether abandoned partial progress holds or decays. Avoid hidden score grants from repeated boundary entry.
4. Publish an immutable summary/receipt with relay ID, simulation tick, owner, contest state, progress and accepted event sequence. HUD and presentation consume the same values. This offline contract is groundwork; it does not supply multiplayer authority, reconciliation or anti-cheat.
5. Offer bounded supply only to the current eligible owner while uncontested. Recheck team, LOS, distance, vertical band and cooldown at the actual service tick. Clamp to the receiving resource's maximum and report only the amount actually accepted. Store per-recipient/cycle cooldowns so entering/exiting cannot multiply the grant.
6. Use resources that the native runtime actually owns. Traversal energy and charge/ammunition are candidates only where the receiving API exists; do not advertise healing or hero damage while native hero health is absent. Supply must not reset flight/grapple cooldowns or permit unbounded airborne camping. Pause, overview, reset and scene disposal must freeze or clear timers consistently with the current simulation.
7. Make ownership readable with original shape plus text and team palette: a relay hexagon/three-spoke emblem, a separate supply diamond and explicit contest mark are candidates. Keep capture progress visually subordinate to imminent troop-attack warnings. No TF2 logo, icon or UI texture is required.
8. Reserve danger geometry for the actual footprint and time of an attack. Prefer segmented boundaries with a source-facing indication over several bright filled rings. Identify these as **troop-attack markers** in the current prototype. The active effects worker is exploring team-shaped ticks; only the subsequent same-camera render can establish whether that implementation improves readability.

### Bounded implementation packets and evidence

| Packet / owner | Deliverable | Pass/fail evidence |
| --- | --- | --- |
| TR-01 · simulation owner | Versioned relay definitions, eligibility/state transition table, deterministic fixed-tick capture and reset. Explicit same-tick contest and abandonment policy. | Unit/scene tests for simultaneous opposing arrivals, duplicate contacts, invalid/dead IDs, departure, capture completion, zero/large elapsed input and reset; repeated seeded run yields identical receipts. |
| TR-02 · supply/player owner | Bounded resource adapter and per-recipient supply receipt; LOS/height/cooldown checks; state cleanup. | Full resource receives zero; nearly full receives only remaining capacity; contested/opponent/occluded/airborne-outside-band recipients receive zero; repeated enter/exit, pause and reset do not duplicate service. |
| TR-03 · world/UI/art owner | Three original landmarks and coherent relay/supply HUD with current bindings, objective state text and shape cues. Keep existing walkable/collision contract. | Actual 960×600 and 1280×720 views and keyboard flow; no clipped labels, no contradictory status; route connectivity remains valid. Day/night and overlapping siege warnings remain distinguishable. |
| TR-04 · independent QA/integration | Combined relays, ordinary waves, siege drill, traversal, settings/pause/overview and resource limits. | Source-pinned stress/counterexamples plus an actual packaged play loop: enter → capture → contest → supply → reset → leave. Freeze/import once before captures; no native-online claim. |

This study supplies design inputs to supporting packets under the existing [full production roadmap](../FULL_GAME_PRODUCTION_ROADMAP.md) and [backlog](../ROADMAP_BACKLOG.json); it does not create alternative completion statuses or replace the parent agent's task IDs.

## Round 3 — counterarguments and acceptance boundaries

- **TF2 objectives serve a different game structure.** A class shooter often concentrates combat at one objective; YUGA also needs three lane fronts, economy and minion movement. Three supply stations may cause camping or turn every lane into the same fight. Test rotation time and contested uptime before increasing reward strength.
- **Supply can amplify the winning side.** Ownership already grants map control. Strong resource grants can make recapture impossible, while weak grants become noise. Begin with a small capped benefit, record actual accepted amounts and compare both teams' access. No copied TF2 number is a balance result for YUGA.
- **Flight changes capture geometry.** A flyer high above a relay must not capture through a roof or avoid all contest while collecting supply. Explicit height/LOS rules and a visible interaction boundary are required; a 2D distance check is not enough.
- **More markers can reduce clarity.** Distinct glyphs help only if there is a visual priority policy. Reserve the strongest contrast for imminent damage, reduce permanent ground decoration, and review overlap under actual moving units. Source code cannot certify accessibility or visual quality.
- **Source availability does not create finished art.** BSP decompilation cannot restore every authoring construct; tools do not provide YUGA's original materials, topology, rigging, animation, audio or complete maps. The concept-target character/world gates and real-hardware profiling remain open.
- **Documentation can drift.** Capture flags change rules; TrenchBroom source and prose disagree on one format capability; upstream performance estimates are not measurements. Record observed revision and tested behavior rather than treating repository popularity as proof.

The next acceptance decision is a small original relay loop with measured failures and readable actual views. It is not full TF2 replication, full native multiplayer, production art completion or Deadlock/Overwatch visual parity.

## Reproduction and intake record

The ledger stores exact immutable raw URLs and SHA-256 hashes for all inspected source files, plus the moving-HEAD observations used to select them. Re-fetch an individual source into scratch and compare its bytes/hash before relying on line references. HTTP error bodies are marked as failures; they are not research content. Three community filename-discovery 404s are retained as resolved path mistakes.

| Intake question | Result in this pass |
| --- | --- |
| Official source fetched and selected functions inspected? | Yes; README/license plus six selected source files, with bounded ranges. |
| Community repositories compared? | Three; twelve fetched source/doc files verified by hash, with selected ranges recorded. |
| Source code ported or dependency installed? | No. |
| Commercial client, map, replay or asset downloaded/decompiled? | No. |
| Leaked or unauthorized source adopted? | No; none fetched. |
| Runtime, rendering, audible sound or multiplayer benchmark performed? | No; implementation/capture workers own subsequent evidence. |
| New Reddit corpus or official rendering paper read? | No; 403 failures are recorded. |

Only these notes, provenance metadata and brief source excerpts belong in the repository. Downloaded source files remain in scratch. Setup, engine choices and larger production priorities remain in [BUILD_HANDBOOK.md](../BUILD_HANDBOOK.md), [BRUTAL_STACK_DECISION.md](BRUTAL_STACK_DECISION.md) and the canonical roadmap.
