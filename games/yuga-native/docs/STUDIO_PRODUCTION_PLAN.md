# YUGA: Confluence — production design and execution plan

15 November 2026. This is the current studio continuation of the existing
[game design master](GAME_DESIGN_MASTER.md), [production roadmap](FULL_GAME_PRODUCTION_ROADMAP.md)
and [active handoff](ACTIVE_DESKTOP_HANDOFF.md). It retains their rules and
unfinished gates. The user requested original hero-action presentation, complex
maps, a complete design/story/mode plan, Blender production and credited reuse.
The new delivery is a working checkpoint toward that final game.

## Product and release contract

Build an original third-person team action game in Sangam City. Players aim,
manage resources, escort lane armies, rotate through useful city spaces and
combine distinct hero abilities. The visual reference is the readability,
character presence, responsiveness and complete player journey of a premium
hero shooter. Art, maps, interfaces, sound, story and code remain our own or
explicitly licensed; commercial game clients are not dependencies.

The first online slice is 3v3 with Rama, Hanuman and Sita, all three lanes and
one authoritative ruleset. The planned complete release is 6v6, fourteen
accepted heroes and 18-minute matches. Use the design master's tower/core and
tiebreak migration. Browser protocol 2's 3v3/eight-minute rules remain a separate
preset until the new protocol is proven. Native currently offers one Rama and
offline practice; definitions, duplicate actors and concept sheets do not
complete the native roster.

Every release must let a player launch, set controls, learn a hero, start a
real available mode, recover from loading failure, play, pause appropriately,
finish or leave, retain settings and start again. Competitive availability
requires operated services and real remote clients. Nothing in a menu may
invent an online queue, population, rank or owned item.

## Story bible: the Sangam Accord

**New narrative proposal, not a delivered campaign.** Sangam's river channels,
gardens, transit halls and old observatories share a network of luminous
conduits. The network has begun losing its stored memories. Civic stewards
convene the Confluence, a bounded contest between Sun and Moon companies, to
restore relays and decide how the city's scarce energy will be shared. The
teams are changing affiliations, not moral or literary allegiances.

Heroes are original epic-inspired interpretations participating in this
fictional city. Their personal stakes emerge through short introductions,
environmental inscriptions and nonessential post-match dialogue. A match is
understandable without reading lore. Avoid treating one regional tradition as
the only authoritative interpretation; retain the existing source register
and seek cultural review for final dialogue and character presentation.

| Beat | Playable teaching purpose | Story function / intended delivery |
| --- | --- | --- |
| 1. The held horizon | Move, aim, draw/release, reload, use cover | Rama arrives at the courtyard; the mentor asks him to protect a route rather than chase every opponent. A short optional voiced/subtitled tutorial. |
| 2. Three ways through | Follow a wave; compare lane and rotation | A sealed record reveals that no district can restore the network alone. Environmental tutorial and one brief before practice. |
| 3. A light to share | Capture/contest a relay; recognize supply | Sita questions who receives the restored power. Clear relay feedback carries the scene; no dialogue blocks a live match. |
| 4. The long crossing | Learn vertical traversal and return routes | Hanuman demonstrates a risky but readable crossing. Movement never bypasses authority or makes a decorative ledge usable. |
| 5. A borrowed victory | Spend match resources and defend a core | Rival companies discover the missing memories were deliberately separated. A bot match teaches tradeoffs, with a resettable scenario. |
| 6. The accord renewed | Complete a full match and understand results | The teams restore one channel together. Results recognize team objectives and explain why the round ended. Further seasonal story is optional after the release loop works. |

The release story is a concise frame and tutorial arc. A cinematic campaign,
dialogue branching engine and additional districts are separate later work.
Rama's current ability names/values come from the native kit JSON; the browser
hero table and generated boards must not overwrite them.

## Mode matrix

| Mode | Current status | Final player job and completion |
| --- | --- | --- |
| Bow training | Native playable | Practice bow/four abilities, remap safely, reset targets and return. Ship offline without an account. |
| Confluence offline practice | Native playable with one hero | Explore lanes, local armies, relays, siege and core outcomes. Keep truthful local labels and a reliable restart. |
| Browser bot arena | Separate playable product, fourteen browser heroes | Eight-minute local 3v3 practice; existing forge, camps, shards and outcomes. Preserve its own rules and asset package. |
| Browser lane/control labs | Separate playable experiments | Compare lane economy and hybrid control objectives. Keep experimental parameters explicit; no implied ranked queues. |
| Native 3v3 Confluence | Next complete online slice | Three accepted heroes, authoritative all-lane match, rejoin and result/rematch with actual clients. Duplicate picks explicitly allowed during this slice. |
| Native 6v6 Confluence | Planned release mode | Fourteen accepted heroes; no duplicate on one team; outer/inner towers and core, 18-minute cap, design-master tiebreak. |
| Relay Control | Future bounded variant | Symmetric approaches, a contestable relay and finite rounds. Validate in the browser lab before commissioning a separate native map and rule protocol. |
| Story prologue / custom scenarios | Later optional work | Deliver the six teaching beats above using the same production movement/combat. No separate untested combat implementation. |

Only proven modes receive normal launch actions. Future modes belong in the
roadmap, not disabled purchase tiles or fabricated matchmaking states.

## Heroes, combat and animation

Keep the [fourteen-hero roster](GAME_DESIGN_MASTER.md#6-fourteen-hero-production-roster)
and its original counters. Production order is Rama → Hanuman/Sita →
Ravana/Arjuna/Duryodhana → the remaining eight. Each accepted hero needs a
distinct silhouette, anatomy, face, costume, weapon, rig, locomotion, timed
attacks, hit/death/respawn, sound palette, ability warnings and a regression
pack. An authoring template may share a rig; its appearance cannot count as
another finished hero.

Use a single versioned combat contract for windup, release, recovery, cooldown,
ammo, collision and reward events. Animation and effects subscribe to those
events. A flourish cannot change damage, hit volume or invulnerability.
Demonstrate interruption, missed shots, solid cover, repeated release,
death/respawn and adverse latency. Preserve current keyboard remappings in
every guide, HUD and added launch hint.

Model/rig in Blender; apply metre scale and transforms; retain editable .blend,
source license, rig/bone identity and export settings. Export GLB, import in
Godot and compare near/mid/far motion with real attacks. Numerical finite poses
and a turntable do not accept foot contact, cloth penetration or readable cast
entry. Complete Rama's existing hair/contact work before duplicating defects
across the roster.

## Complex maps that serve decisions

The current offline Confluence remains the 140×260 m reference with three lanes,
local armies, traversal decks and tether routes. Preserve accepted gate/garden
geometry and collision while consolidating exact duplicate texture resources.
The new **Relay Foundry** is an original Blender-authored 132×190 m map-design
prototype with its own native walk/jump study scene. It is a blockout candidate,
not an alternate authoritative Confluence map or a production-art acceptance.

| Layer | Required design | Acceptance before a competitive map ships |
| --- | --- | --- |
| Primary routes | Three legible lanes with mirrored spawn/core access and identifiable landmarks | Trace both sides' routes, sightlines, objective access and spawn escape; no trapped restart. |
| Rotations | Side pockets, two independent cross-lane choices, retreat loops | Record travel cost and visibility; no one safe route dominates every engagement. |
| Elevation | A center crossover, climbable ramps and readable landing space | Walking/jumping/contact work; server uses the same collision/elevation version; projectile origins and remote actors agree. |
| Cover | Different short/long engagement pockets; silhouettes visible against stable backgrounds | Check projectile occlusion and camera collision from both sides; no decorative fake protection. |
| Objectives | Three distinct relay landmarks, bounded capture shapes, intelligible approach/escape | Real rule-owned contest/supply state and visible counters; no UI-owned outcomes. |
| Art and audio | Coastal sandstone, indigo banners, worked brass, water/garden accents, positional cues | Source/asset credits, material budget, mobile-inapplicable desktop LOD, actual camera/motion/listening review. |

Blender source names `COL_BOX_` and `COL_RAMP_` identify simplified collision in
the new prototype. Store dimensions, transforms, mesh/hash counts and intended
routes beside the export. Moving to the match requires collision/nav/rules
versioning, authority parity and human route playtests. Visual complexity must
not create invisible walls, unreadable telegraphs or costly unbounded props.

## Final screen and UX contract

The implemented launch refinement keeps the live Rama portrait, two practices,
one gold primary and exact utility-return focus. A compact read-only briefing
adds an explanatory schematic and five **current** bindings when space allows.
At enlarged scales the essential offline/mode description and action stay
visible; optional guidance yields its space. It does not insert a new launch step.

| Screen | Information/action that must be true | Failure / accessibility requirement |
| --- | --- | --- |
| Boot/title | Actual build, available practice, current hero, selected mode | Keyboard focus, 960×540, 100/150/200% scale, no invented online availability. |
| Hero selection/guide | Accepted roster and actual current kit/bindings | Explain range/cost/counter, accessible labels; no cast from read-only guide. |
| Party/queue | Actual membership, region/rules version and progress | Cancel, timeout, rejoin and preserved inputs; show only when service exists. |
| Loading | Actual resource/construction/ready phase | Retry/back, repeated activation guard, focus restoration; never fabricate total readiness. |
| HUD | Authoritative health/ammo/cast/cooldown/objective/teams | Stable contrast, hit/blocked/miss distinction, scale and reduced effects. |
| Map/forge | Real map state, costs, upgrades and rule effects | Pause semantics appropriate to local/online; no state change from a decorative map. |
| Settings/help | Live bindings, audio/graphics/text options | Cancel remap, validate conflicts, save/relaunch, no stuck input on close. |
| Pause/results | Actual local pause or continuing online match; reason for outcome | Restart/rematch/leave, restored focus and no stale winner after reset. |
| Credits | Creator/source/license/modification record for shipped content | Available offline with packages; include code and art/font notices separately. |

The [twenty-screen AI boards](../../../docs/concepts/studio-2026-11-15/README.md)
guide composition only. Their invented labels/mechanics are documented and
rejected. Actual native/browser originals determine implemented visual quality.

## Reuse decisions and credits

Use Godot for native runtime, Blender for editable assets, existing PlayCanvas
for separate browser products, FFmpeg/Xvfb/Playwright for recorded checks and
REA for bounded analysis of owned code. The external source catalog pins
fifteen candidates; four research checkouts are prepared. A source checkout is
not a compiled, tested or integrated game dependency.

Study Prometheus/OWLib for format/tool architecture without importing a
commercial client or its assets. Prometheus is AGPLv3, OWLib is MIT and OWM is
GPLv3; preserve the selected file's actual terms if code is ever adopted.
Do not import GDQuest art under the mistaken assumption of an
unrestricted asset grant: its pinned license says CC-BY-NC-SA. Raea currently
has FSL restrictions; ThreeRT's MIT engine and closed packaged clients have
different terms. They remain isolated studies until a concrete benchmark
justifies an integration. See [source credits](../NOTICE/STUDIO_SOURCES.md),
[catalog](../../../tools/research/opensource-catalog.json) and panel reports.

All new map geometry is original procedural Blender authoring. Existing font,
MakeHuman, CC0 source-art and engine notices remain in their current ledgers.
Record per-file source/commit, license, modifications, author, hash and
distribution scope before importing anything. Credits accompany a valid grant;
they do not replace the grant. Preserve notices in every downloadable build.

## Execution roadmap and owner contracts

These are dependency gates for the final game, not estimates or new accepted
packets in the historical 78-packet campaign. The current source/test/render
receipts and [delivery report](../../../docs/research/STUDIO_DELIVERY.md)
own the new checkpoint's completed work.

| Gate | Owner / concrete code and content | Exit evidence |
| --- | --- | --- |
| 0. Reproducible studio | Build engineer + reviewer: verified engines/Blender, packages, source catalog, logs | Fresh setup, versions, import, build, actual ordinary launch/quit and artifact hashes. |
| 1. Complete Rama presentation | Character/motion engineers: finish existing CC0 hair fit, contact, transitions, LOD, audio | Continuous near/mid/far gameplay with hit/miss/interruption/death, independent visual and listening review. |
| 2. Qualified map slice | World/level engineer: current Confluence plus reviewed Foundry candidate routes | Real traversal/contact/camera/cover, geometric and material bounds, mirrored route playtests. |
| 3. Shared spatial rules | Network/simulation engineer: versioned map, elevation, input acknowledgements/reset epoch | Two rendered native clients agree on movement, ramps, blocked shots and reconnect; malformed/stale commands rejected. |
| 4. Native match lifecycle | Simulation/network engineer: authoritative combat, armies, economy, outcomes | Join, rejoin, reset, death, backend restart and full uninterrupted match on actual clients. |
| 5. Three distinct heroes | Character + gameplay + audio: Rama/Hanuman/Sita | Each complete content pack; counters and shared rule/event contract; original full match with all three. |
| 6. Online 3v3 slice | Integrator/QA/operations | Six real seats, complete all-lane match, result/rematch, latency/packet-loss/recovery and bot fallback evidence. |
| 7. Six accepted heroes | Art/gameplay teams: add Ravana/Arjuna/Duryodhana | Distinct accepted anatomy/weapons/motion, no duplicate character-template claims. |
| 8. 6v6 rules migration | Simulation/UX: six towers, core topology, 18-minute tiebreak, protocol | Deterministic fixtures plus rendered human/bot matches; old preset isolated. |
| 9. Complete fourteen | Content team: remaining eight, final voices/effects/counters | Per-hero acceptance, accessibility/readability/balance review, complete credit ledger. |
| 10. Operated beta | Services/QA: parties, region routing, reporting, persistence, monitoring | Sustained real sessions, capacity/recovery measurements, abuse controls and rollback exercise. |
| 11. Hardware/release | Build/QA/review: Linux/Windows packages on named physical GPUs | Full-match frame-time/memory/loading data, controller/keyboard/accessibility and human feel/listening passes. |
| 12. Final distribution | Lead/reviewer | Exact accepted source, signed/checksummed artifacts, current credits/help, clean install/update/save/rejoin and public-byte verification. |

Two panel rounds in this task use two researchers plus the build engineer and
lead. Researchers challenge sources/licenses and implementation shortcuts;
engineers own disjoint code/assets; an independent reviewer challenges actual
original captures. Parallel work is bounded by the four available agent slots.
Six planned professional roles do not imply six running agents or GPUs.

This host reports sixteen CPU threads. Run independent source/build/test jobs
concurrently and let Blender use a declared worker budget; serialize engine
imports/exports and native renders against frozen sources. Keep capacity for
the input/capture owner. Maximum useful throughput is the objective; oversubscribed
software renderers and duplicate imports make builds slower. Physical-GPU
profiling stays a different release gate.

## Definition of the finished version

A new user installs a credited package, adjusts settings, learns any of the
fourteen accepted heroes, joins a party, completes an authoritative 6v6 match
on a qualified complex map, survives reconnect/backend recovery, understands
the result and plays again. Art, animation, sound, input and performance pass
their named human/device reviews. The delivered local preview, concepts and
map blockout are supporting work until those exits are met.
