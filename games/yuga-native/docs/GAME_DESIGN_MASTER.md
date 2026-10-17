# YUGA: Confluence — complete game design baseline

Design baseline: 17 October 2026. **This document specifies the original game we intend to finish. It does not certify that the finished game exists.** Use the [production roadmap](FULL_GAME_PRODUCTION_ROADMAP.md) and its task backlog to implement and verify this design. Runtime code remains the authority for the current prototype until a versioned change explicitly replaces a rule.

The visual and motion target is a polished contemporary team shooter at the level of the user's Deadlock/Overwatch references, combined with three-lane strategy associated with Dota. These are quality and genre references, not a claim of recovered commercial source, assets, animation data or exact rules. YUGA uses original art, licensed reusable components and documented implementation patterns. “4D/5D” is interpreted as animated, physically coherent 3D presentation, time-varying lighting and responsive effects; it is not an additional rendering technology or a quality certification.

## 1. Product, audience and non-negotiable decisions

YUGA is an online, third-person, three-lane team game in a fictional Indian-inspired city where epic-associated heroes compete as Sun and Moon. Players aim their weapons, combine three abilities, accompany living lane armies, contest jungle resources, choose match upgrades, rotate through the city and break the opposing core. Team assignments are independent of literary allegiance. The match is a fictional contest; it does not reenact a religious event or make a historical claim.

The product pillars are:

1. **Readable skill and teamwork.** A player can identify an incoming threat, its actionable boundary, its owner and at least one response. Position, aim, cover, resource choices and coordination matter.
2. **Hero identity in actual play.** Faces, anatomy, costume, posture, weapon grips, locomotion, voice and effects distinguish heroes. A roster of differently decorated copies does not meet the target.
3. **A city that supports decisions.** Three lanes, rotations, accessible vertical routes and distinct districts create deliberate opportunities. Decorative density must not obscure enemies, exits or collision.
4. **Fair competitive ownership.** Authority decides movement outcomes, hits, rewards and match results. All fourteen heroes and all abilities are available from the start. Purchases cannot buy combat advantage.
5. **A complete journey.** Launch, practice, party, queue, selection, loading, play, disconnect/rejoin, result, replay and exit receive the same care as combat.

The primary production platform is native desktop with keyboard/mouse and controller support. Windows and Linux are the initial packaging targets. A browser companion/practice build is useful but cannot lower the native visual acceptance standard. Mobile competition, console certification, a cinematic campaign, destructible cities and commercial-client replication are outside the first complete release. This is a scope decision, not a declaration that the requested visual target has been reached.

## 2. Current implementation versus production target

| Area | Audited current baseline | Approved design default for production |
| --- | --- | --- |
| Native build | Offline Rama courtyard, training targets, local controls, original production model and render/evidence tools | Complete online and bot matches using the same authoritative rule version |
| Browser authority | Protocol 2; three heroes per team including bots; 480-second matches | **6v6**, initially two players per lane; no duplicate hero within one team, opposing mirrored picks allowed |
| Roster | Fourteen definitions, 42 abilities, five Vanguards/four Strikers/five Keepers; fourteen existing GLBs | All fourteen accepted at production art, animation, networking and gameplay gates |
| Distinct timed mechanics | Rama R, Hanuman R and Sita R; other 39 slots use shared ability kinds | Preserve all 42 kit contracts initially; distinct authored motion/effects and later mechanically distinct revisions only through tested rule changes |
| Objectives | Three towers per team; core opens after two defending towers fall | Six towers per team: outer then inner in each lane; core opens after any defending inner tower falls |
| Match duration | Eight minutes; score then core-health tiebreak | **18 minutes / 1,080 seconds**; core destruction wins immediately; at the cap compare enemy towers destroyed, then enemy core damage fraction, then draw |
| Economy | Match credits, three ranks each of Power/Vitality/Tempo; contested shards and four camps | Ship this understandable economy first; expand only through the bounded equipment experiment below |
| Spatial authority | Mixed 2.5D: x/z movement/solids, projectile height, aim pitch, jump y; ground landing at zero | Versioned collision/elevation data supporting ramps, stairs, ledges and stacked walkways; remote pitch and elevated effect positions |
| Multiplayer operations | Supplied Node/WebSocket service, process-memory room/reconnect state; public WSS not established by the static site | Operated regional authoritative service, party/match lifecycle, monitoring, reconnect and persistence proven with actual clients |
| Visual quality | Published preview and bounded render evidence; commercial-quality target remains open | Reviewed continuous motion and complete live matches on declared target hardware |

The native vertical slice is **3v3, all three lanes, Rama/Hanuman/Sita**, using the current rules first. That slice permits duplicate hero selections when necessary and must say so. The next content step is six accepted heroes: Rama, Hanuman, Sita, Ravana, Arjuna and Duryodhana. Duplicate-free 6v6 cannot begin before six accepted heroes exist. The remaining eight heroes complete the release roster. Existing browser assets are starting material, not automatically production-approved native characters.

The proposed team count, objective topology and tiebreak are a rules migration. They must not silently appear on a protocol-2 server or mix incompatible clients in one room. Keep the old eight-minute practice preset separately named while validating the new format. The restored published baseline is the last evidenced runtime; uncommitted work lost during the cloud-worker reset is not counted as delivered.

## 3. Complete player journey

| State | Player purpose and required behavior | Exit and failure contract |
| --- | --- | --- |
| First launch | Choose display/language, accessible text size, audio and input preset; explain native requirements and local/server modes accurately | No mandatory account for offline practice; settings usable before entering a 3D scene; recover from unsupported settings |
| Home | Clear Play, Practice, Heroes, Party, Settings and Exit; show server/patch state and last selected hero | Do not advertise online readiness from a static-page deployment; unavailable services have actionable status |
| Hero gallery | Inspect actual animated model, role, all three abilities, real values, counters and a short playable trial | Concept art is labelled; preview cancellation unloads resources and cannot start a delayed match |
| Practice | Free play by default; optional movement, aim, cover, ability, economy and camp drills; bot difficulty and reset | Pause genuinely stops local simulation; drills give no paid/account power or fabricated mastery score |
| Party | Invite/join by code, choose region, see party members and readiness | Full room, invalid code, canceled invite and leader departure have explicit states; no exposed reconnect token |
| Queue | Choose unranked or ranked when unlocked operationally; show elapsed wait, region and cancel | Cancel is immediate; a late assignment cannot consume input/start a match after cancellation |
| Ready check | Confirm participation, identify connection trouble, reserve the match | Failed readiness returns the party with a clear reason; no repeated punishment for a server-side failure |
| Selection | Pick any available hero, show team roles and lane intent, resolve within-team conflicts; mirrored enemy picks allowed | Initial default is blind simultaneous selection with a proposed 45-second limit; selected hero and fallback are visible before timeout |
| Loadout/briefing | Explain chosen hero, three skills, starting gold, lane, objective and teammates; cosmetics only before first purchase | All gameplay choices remain available in-match; no grind-required equipment, hidden stat advantage or mandatory tutorial |
| Loading | Show real progress, input help and connection status; finish only after actor and world presentation are ready | Cancel before commitment; reconnect path after commitment; stale asynchronous loads never start a second scene |
| Spawn | Brief noninteractive countdown, clear exit, shop and team/lane markers; give player aim/control immediately when released | Neutralize held input across transition; synchronized authority starts the clock |
| Match | Fight, rotate, upgrade, communicate and pursue core objective | Online menus release local input without pausing the server; focus loss, controller unplug and device changes are handled |
| Defeat/respawn | Show killer/assists, damage types and meaningful cause, remaining respawn time, allied spectator view and next decision | No free enemy vision through death camera; respawn restores correct camera, input and HUD exactly once |
| Reconnect | Reclaim reserved identity and state; interpolate into current world; state what happened during absence | Old connection yields ownership; no duplicated cast, reward, audio, player or control stream |
| Match end | Freeze combat authority, show winning rule, team objective contribution, personal relevant metrics and report/mute options | A draw is explicit; no misleading victory caused by a score-only HUD; result acknowledged idempotently |
| Rematch/return | Party can queue again, review hero, replay or return home | New match resets credits/upgrades/cooldowns/events; room cleanup releases sockets, scene resources and audio |

No lobby customization may trap the player in an unskippable animation. Transition, loading, hover and button states must remain legible at supported resolutions, ultrawide and UI scaling. Focus order and controller navigation must work without a mouse. Match UI must not compete visually with the reticle, crossfire or ability warnings.

## 4. Match rules and strategic decisions

### Production win condition

Each team has three outer towers, three inner towers and one core. An inner tower is protected until its own outer tower is destroyed. The core is protected until at least one inner tower is destroyed. These protections are server state and visible in the world, minimap and target HUD. Destroyed structures stay destroyed. A core defeat ends the match once, even if simultaneous damage occurs; simultaneous core destruction within one authority step produces a draw. Evaluate both cores after the same authority-tick damage batch before committing a result; the current first-core finish behavior must change for this proposed rule.

At 1,080 seconds, compare the number of enemy towers destroyed. If equal, compare the fraction of damage dealt to the enemy core against that core's maximum health; if equal, draw. Kills, minion farming, camp clears and cosmetics do not win the cap tiebreak. No sudden-death rule is implied. The clock and objective comparison are visible before the final minute. This objective-first cap is proposed and must be evaluated against stalemate and early-lead incentives before ranked release.

The intended match arc is opening lane choice → first upgrade/camp rotations → coordinated outer-tower pressure → inner-lane breakthrough → core threat or objective-cap decision. These are design intentions, not claims about measured pacing. Target an interesting choice every short encounter without forcing every player to follow one optimal script. Human tests must detect whether six players merely collapse into one permanent group.

### Combat and universal movement

Primary attacks are aimed projectiles in the current rules, including mace, staff, spear and chakram silhouettes. Do not introduce a misleading melee hitbox because a model carries a mace. Projectiles respect travel, cover and valid target collision. “Line” does not mean piercing. All heroes can deal damage; roles describe emphasis rather than exclusive permissions.

Production movement includes directional locomotion, acceleration/deceleration, jump, grounded/airborne transitions and camera-relative aiming. Sprint is a proposed universal traversal state; its speed, firing restriction and stamina policy need one explicit authority experiment before becoming a competitive rule. Dash and leap remain hero abilities. The current native training dash/sprint cannot silently become a multiplayer advantage. Crouch, wall running, sliding and vaulting are excluded until a defined mechanic and matching collision/animation contract are accepted.

Preserve visible aim direction, movement direction and action commitment as separate concepts. Manual aim is the ranked default. Current optional target lock remains a practice/accessibility experiment; competitive assistance requires a published input policy and matched controller/mouse testing before activation. Assistance never fires automatically, changes projectile collision or grants visibility through cover.

The production control proposal uses WASD/mouse for movement and aim, primary fire on left click, jump on Space, Q/E/R for the three skills, interaction on F and the menu on Escape, all remappable. Sprint is enabled only after its authority rule is accepted. Current browser primaries use firing intervals without a universal magazine; the native courtyard’s twelve-shot magazine and R-to-reload are training experiments. A production ammunition/reload rule needs its own weapon contract and a conflict-free binding before adoption. Help, icons and controller prompts must show the active ruleset’s actual controls.

### Current economy to carry into the first native match

These values are inspected prototype rules, not claimed production balance:

| Rule | Current value/meaning |
| --- | --- |
| Starting credits | 180 per hero |
| Power | Three ranks; each adds 17% of base primary damage and 12% of applicable ability payload; next-rank cost `120 × rank` |
| Vitality | Three ranks; each adds 65 maximum/current health; cost `100 × rank` |
| Tempo | Three ranks; primary interval divided by `1 + 0.12 × ranks`; cost `140 × rank`; no skill-cooldown reduction |
| Purchase location | Alive near own spawn; server validates price, range, rank and duplicate command receipt |
| Lane defeat | Nearby allies receive 10 credits each; separate 8-credit contested shard |
| Shard claim | A primary shot can secure immediately; proximity begins after one second; expires after twelve seconds; wallet contents cannot be stolen |
| Camp reward | 30 nearby-team credits, separate contested 30-credit shard, twelve-second blessing for eligible living finishing hero |
| Persistence | Credits and upgrades reset each match; no purchased account power |

Gold feedback must identify shared award, personal shard secure/steal and purchase separately. A player who secured a shard does not receive a false claim of personally killing the guardian. Simultaneous shot/proximity claims resolve exactly once. Summons award neither gold nor tiebreak points. An expired shard never lingers as collectible art.

The first complete native release may retain the three upgrade tracks if human choices are meaningful. To seek deeper build variety, run a separately versioned equipment experiment: three slots (offense, survival, utility), six alternatives per slot, three upgrade ranks, no duplicate slot and no premium options. Candidate effects are primary power/rate/range/ability power/structure pressure/weapon recovery; health/regeneration/temporary shielding/slow resistance/mitigation/mobility; skill recovery/healing/shield support/pickup reach/blessing duration/team scouting. These are **proposals, not implemented items or final numbers**. Each requires caps, stacking order, counterplay, source data and human tests. Do not ship eighteen names whose underlying effects are absent. Keep the accepted three-track release viable while this experiment is evaluated; equipment breadth is not a substitute for good combat.

## 5. Lane armies and jungle

Soldiers, watch, ministers and kings are fictional old-city court units. They are not real politicians or police likenesses. They have individual silhouettes, equipment, gait, attack anticipation, hit response and defeat. Repeated units share optimized assets without becoming miniature copies of the heroes.

| Unit | Current mechanics | Animation and information requirement |
| --- | --- | --- |
| Spear Soldier | 130 HP; 14 damage; 11 m acquisition/7 m stopping distance | Brisk march, readable spear shot, recover and collapse; projectile launch matches authority |
| City Watch | 90 HP; 10 damage; 17 m acquisition/13 m stopping distance | Square shield/baton silhouette, measured stride and shot; shield prop does not imply unimplemented protection |
| Court Minister | 100 HP; 7 damage; 13 m acquisition/9 m stopping distance; every 5 s gives 12 shield for 3 s to up to three other allied minions within 6 m | Scroll/seal gesture, visible recipient pulse, no false hero/self protection |
| King siege unit | 240 HP; 3.4 m/s; visible-structure preference; 12 projectile damage to actors/32 to structures | Deliberate weight, crown readability, heavy recoil; shot can be intercepted |
| Hero sentinel | Two temporary units per accepted summon; 105 HP; nine-second current lifetime | Owner/team identity, independent attack, readable expiry; disappear exactly with authority |

Current waves begin at one second and recur every eighteen seconds. Each lane/team receives soldier, watch and minister; every third wave adds a king, first at 37 seconds. Current admission reserves mirrored pairs under the 96-actor cap. For 6v6, wave quantity, cap and timing are retuned only after a full-population benchmark and lane pressure study; a larger team must not silently inherit an overloaded cap or asymmetric spawning.

There are four current wild courts: West Reed Court at (-54,0), Stone Grove at (-20,0), Sky Garden at (20,0), East Reed Court at (54,0). Reed Naga grants ward, Grove Yaksha grants regeneration, Cloudwing grants haste. First spawn is 30 s, respawn 40 s after defeat; aggro 8 m, leash 12 m. Returning home resets the creature without a reward. A creature's identity is inspired by motifs; its stats and combat are game inventions.

Every guardian needs idle/awareness, engage, attack, hit, return, reset, defeat and respawn communication. A leash border may be subtle until needed, but the reset must be understandable. Mythological beings are opponents/allies of an original contest, not an enslavement collectible. Temporary blessings communicate their actual effect, owner and remaining time. Add a major jungle objective only after the four-camp rotation and lane objective loop pass; a future boss must not become an untested mandatory comeback button.

## 6. Fourteen-hero production roster

Six current playable women are Sita, Draupadi, Subhadra, Hidimbi, Chitrangada and Ulupi. Their roles span protection, command, duelling and frontline control; they need the same anatomy, face, motion and gameplay budget as the male characters. Character strength and team eligibility are not assigned from moral labels in the epics.

The values below are unupgraded current definitions. HP/speed are health and metres/second. CDs are seconds; `d` is aim/placement distance and `r` is radius, both in metres. Payload numbers are unupgraded damage, healing or shielding as labelled. Full authoritative fields remain in `shared/heroes.ts`; this table is a production brief, not a second hand-edited runtime database.

| Hero / current role / HP, speed | Q → E → R, current payload and CD | Identity, motion and counterplay contract |
| --- | --- | --- |
| Rama · Striker · 300, 7.2 | Steady Arrow: 54 projectile/26 m, CD 9 → Measured Step: dash 10 m, CD 12 → Dawn Volley: 3 × 32-damage arrows/28 m after 1 s locked preparation, CD 44 | Calm clear draw and release, narrow crest, curved bow, responsive sash; idle/run must not remain permanently in full draw. Opponent can break the locked line, flank or use cover. |
| Ravana · Vanguard · 390, 6.4 | Tenfold Guard:48 shield/r4/4 s, CD11 → Commanding Circle:35+pull/d20/r5, CD16 → Crownfire:90/r7, CD48 | Ten-faceted crown, broad mantle, deliberate command and close blast. Facets read as a single character silhouette. Slower approach can be spaced; pull cannot drag through solid cover. |
| Arjuna · Striker · 275, 7.7 | Converging Volley:38 forward fan/18 m, CD8 → New Angle:dash12 m, CD11 → One Clear Line:88 projectile/28 m, CD42 | Quick weight shifts, distinct bow/scarf/quiver silhouette and recoverable agile aim. Lowest health exposes a failed flank; line does not pierce walls or multiple opponents. |
| Duryodhana · Vanguard · 410, 6.2 | Mace Shock:48 forward fan/10 m, CD10 → Hold the Ground:55 shield/r4/4 s, CD15 → Iron Crescent:92 cone/12 m, CD46 | Square grounded stance, heavy mace inertia and a visibly frontal sweep. Highest base health does not give immunity; leave the arc or pressure after ward expiry. |
| Hanuman · Keeper · 350, 7.6 | Windward Leap:14 m, CD9 → Bring Them Home:48 heal/r5, CD14 → Mountain Pulse:0.7 s prepare+0.45 s travel/up to14 m, landing65 damage/45 heal/r7, CD45 | Expressive face, coherent tail/scarf and weighted compression/landing. Landing indicator follows collision-limited authority; ordinary Q has no extra damage. Enemies can leave the marked landing. |
| Karna · Striker · 315, 6.8 | Sunshaft:62 projectile/27 m, CD11 → Borrowed Dawn:42 shield/r4/3 s, CD16 → Solar Reprisal:95/r6, CD50 | Radiant shoulder discs, deliberate heavy shots, solar accents that preserve outline. Slow missed shots and short shield create openings; close nova is not a global attack. |
| Bhima · Vanguard · 400, 6.4 | Heavy Sweep:52 cone/10 m, CD10 → Closing Stride:leap12 m, CD15 → Thunder at Your Feet:92/r8, CD48 | Broad torso, large mace, convincing force through hips/shoulders and recoveries. Enemy spacing and cover matter; ordinary leap has no hidden impact damage. |
| Meghnad · Striker · 285, 7.8 | Cloud Snare:28 over3 s/d22/r4, CD12 → Storm Step:dash13 m, CD12 → Gathered Squall:78 fan/22 m, CD43 | Forked crest, layered cloud scarf, fast angle change. Cloud visuals remain translucent and bounded; no implied stealth or invulnerability. Low health punishes failed commitment. |
| Sita · Keeper · 330, 6.8 | Grove Renewal:50 heal/r5, CD10 → Rooted Path:25 over4 s/d18/r5, CD15 → Shelter of Mithila:0.8 s prepare,70 shield+9 heal/s/r8 for6 s, CD46 | Expressive grounded protector, emerald/ivory mantle, leaf staff and measured hand gestures. Sanctuary stays fixed, allies must remain inside; roots are not a solid wall or immobilize. |
| Draupadi · Keeper · 340, 6.5 | Circle of Resolve:46 shield/r5/4 s, CD10 → Stand Accountable:30+pull/d19/r5, CD17 → Unbroken Assembly:95 heal/r8, CD48 | Upright staff, five-point clasp, restrained flame association and clear commanding gesture. No movement ability; split pressure limits grouped protection. Fire motif does not make her heal hostile damage. |
| Subhadra · Keeper · 315, 7.2 | Signal Lance:44 projectile/24 m, CD9 → Rally Close:42 heal/r4, CD13 → Twin Standards:two sentinels/28 shot/9 s, CD48 | Spear pennant, distinct side braid, commander posture and clear two-unit arrival. Small heal radius and temporary reinforcements create limits; summons are not permanent troops. |
| Hidimbi · Vanguard · 375, 6.8 | Forest Boundary:27 over4 s/d16/r5, CD12 → Canopy Guard:50 shield/r5/4 s, CD16 → Grove Watch:two sentinels/32 shot/9 s, CD52 | Broad leaf mantle, braided crest and powerful guardian stance. Forest effects preserve clear routes; pressure another lane or outlast summons. Do not present her as a generic monster skin. |
| Chitrangada · Vanguard · 350, 7.5 | Crossing Step:dash12 m, CD9 → Spear Arc:44 cone/11 m, CD12 → Defender's Vow:80 shield/r6/4 s, CD44 | Agile spear duellist, segmented mantle, balanced crossing step and clean hand transfers. More mobile but less healthy than heavier Vanguards; no hidden parry or damaging dash. |
| Ulupi · Keeper · 320, 7.0 | River Draw:28+pull/d19/r4, CD12 → Cooling Current:44 heal/r5, CD14 → Naga Basin:72 over6 s/d23/r7, CD46 | Wave crest, scale-edged collar, water-ring staff and flowing but grounded gestures. Clear water edges, alternative routes and cover remain visible; basin does not cause drowning or change map collision. |

R1/M1 literary sources in the source ledger support selected associations, not the numerical abilities. Subhadra's commander/spear kit, Chitrangada's arena spear kit and every shield/heal/damage timer are original adaptations. Indrajit/Meghnad naming follows the documented traditions; Hidimbi distinguishes the female character from her brother in the inspected older translation. Regional traditions and contemporary cultural review remain relevant; a few translated passages are not complete research into Indian mythology.

Hero completion requires one accepted kit card, actual model, rig, motion set, sound palette, ability effect set, counters and playable regression pack per ID. The art team may not change a radius, number of projectiles, shield duration or movement immunity through animation. A mechanically new signature ability requires a separate authored rule proposal, simulator test, network representation, visual warning and balance evidence before replacing a current slot.

## 7. Animation, weapons and effects contract

### Actual character deliverable

Each production hero has a continuous deformed anatomical surface; individual face and proportions; fitted costume; separated material response for skin, cloth, hair and metal; working hands/feet/weapon contact; and accepted LODs. A licensed anatomical base may be shared, but individuality cannot rely only on colour and jewellery. Face expression and eye direction must survive the gameplay camera. Crowns, tails, sleeves and weapons have collision/deformation rules appropriate to their purpose.

Required animation states are relaxed/ready idle, locomotion forward/back/strafe/diagonals, start/stop/turn, aim offsets, primary anticipation/release/recovery, each Q/E/R, takeoff/air/landing, hit response, defeat, spawn and victory/defeat presentation. Sprint is added only with its accepted movement rule. Shared base motion can be retargeted, but each weapon/hero needs authored grip, posture, timing and transition correction. The current nine exported clip names are a compatibility baseline, not proof that this production set exists.

Movement translation is authority-owned. In-place locomotion scales and blends against observed speed; root displacement from a source clip is separately recorded and cannot move the competitive actor a second time. Foot planting uses declared support intervals. Hand IK resolves actual weapon anchors, with explicit bow/string hand targets and rest-axis compensation. Cloth, hair and tails follow restrained secondary motion and must settle after stops. Ragdoll is optional presentation; it cannot alter damage, block lanes or leak protected enemy positions.

Production acceptance includes: planted-foot drift **at most 2 cm over its declared support interval**, weapon-hand contact error **at most 1.5 cm** at declared grip anchors, finite transforms, stable bone lengths, no flipped joints, no exposed garment gaps at required poses and no visible loop seam at normal play speed. These are proposed acceptance thresholds aligned to the production guide, not results of the current model. A continuous actual-engine reel must show transitions and simultaneous locomotion/aim, including looking high/low and near-camera obstruction; isolated stills or finite samples cannot pass continuity.

### Timing and effect grammar

The three existing timed Rs derive preparation/travel from authoritative cast state. Rama locks facing for one second, then launches three separately collidable arrows. Hanuman prepares for0.7 s, travels for0.45 s and applies damage/heal on actual landing. Sita prepares for0.8 s and forms a six-second fixed sanctuary. Preparation blocks movement, fire, jump and another cast. Damage alone does not cancel; death cancels unfinished casting without a refund; formed Sita sanctuary persists after her death. Reconnect seeks to current cast time once and does not replay the start event.

The other39 abilities currently apply their shared-kind rules without gameplay windup. Cosmetic anticipation must not delay their accepted effect or suggest that an opponent had a warning window that did not exist. To add a competitive windup, change authority and data first. Area footprints after an instant hit are aftermath, not a future danger telegraph.

Every effect has a preparation/boundary channel where one exists, a release/contact channel and expiry/recovery. Hostile areas use readable segmented/inward boundaries; allied protection uses outward shield/leaf shapes; healing, shields, damage and slowdown have distinct marks and sound families. Shape, direction and timing carry information alongside colour. Hero palette never replaces team identification. Bloom, particles, cloth and smoke stay below a level that hides target silhouettes. Low settings retain every actionable boundary, projectile and expiry cue.

Bow heroes need visible nock/draw/release/recovery consistent with the actual fire interval; maces and spears need weight without inventing melee hits; staffs need precise origin/aim. Summons show exactly two accepted arrivals and actual expiry. The water, root and stone debris effects are cosmetic unless a versioned terrain rule explicitly says otherwise.

### Animation acceptance matrix

For every hero, exercise neutral/aimed idle, all travel directions, start/stop, turn in place, jump/landing, fire while moving, each ability while allowed movement continues, locked cast, cast death, reconnect midcast, defeat and respawn. Repeat with minimum/maximum pitch, walls, slopes, platform edges, low/high frame rates and each quality tier. Observe grip, feet, clothing, hair/tail, silhouette and effect timing. Test both teams, multiple skins if any, all LOD switches, paused/reopened preview and twenty consecutive replay transitions. Share immutable animation resources; never share mutable actor playback state.

## 8. Sangam City map and world design

The current map is140 ×170 m with lane centres x=-40,0,40, spawns z=±69 and a flat shared collision layout. The production city uses this as a proven gameplay reference, not an obligation to stretch a courtyard into a finished arena. Establish an approved greybox before environment art hides the routes.

| District | Play purpose | Visual direction and readability |
| --- | --- | --- |
| Ghat promenade / Lanka coast | West lane, riverside rotation, outer jungle access | Warm coastal gate silhouette, stepped ghats, colonnades and distant Lanka-inspired terraces; water boundary obvious; reeds stay below critical aim lines |
| Temple avenue | Central lane, direct objective pressure, broad orientation landmark | Fictional temple precinct, courtyards, carved stone, lotus/leaf abstractions and a recognisable central tower; avoid copying a real sacred complex room-for-room |
| Metro gardens / modern city | East lane, alternate routes and city contrast | Fictional Mumbai/Delhi/Bengaluru-inspired transit forms, shaded markets and planted walkways; signs and equipment original; route colours remain legible at night |
| Reed courts / swamp | Optional contested farming and short rotations | Shallow patterned water, mud/reed transitions, roots and naga court markers; current wet ground remains walkable and does not secretly slow/swim/damage |
| Bases | Safe return, purchases, respawn and team orientation | Distinct Sun/Moon silhouette and crest plus shape-coded navigation; no spawn exit gives one side a hidden shorter route |

The target topology is three identifiable lanes joined by a circular middle rotation route and bounded outer alternatives. Looping paths need more than decorative circles: each exit must reconnect to a meaningful lane/camp decision. Foreground cover, middle-distance fight spaces and far skyline layers create depth without crowding the playable corridor. Asymmetric art can coexist with measured equivalent travel, cover and objective access; visual symmetry alone is not balance proof.

Raised routes must expose an opportunity and a cost: a flank with a visible exit, cover that blocks actual shots, and a return path that does not trap a slower hero. Bridges over roads require multiple support surfaces at one x/z position. A single heightfield cannot represent that topology. Do not build traversable rooftops, stairs, bridges or elevated camps until the authority contract below is implemented and tested.

Day/night is presentation only for the initial complete rule set. Diya and lantern placement establishes warm navigational accents, cool ambient fill and clear enemy edges. Dynamic time must not grant a hidden visibility advantage or alter target eligibility. Fixed daylight/night preferences preserve equivalent actionable contrast. Reduced motion removes flicker/shake but retains events. Fog/water/specular detail cannot erase a distant hero or cause temporal shimmer; evaluate moving cameras, not only screenshots. Decorative lamps have a bounded shadow/light budget and must not require many overlapping shadow casters.

## 9. Networking, content and spatial interfaces

The client presents authority; it does not award gold, decide a hit or infer a victory from local animation. Commands are idempotent; stale input expires; reconnect identity ownership is explicit. Offline practice runs the accepted rules locally with bots. Competitive rooms advertise a rules version, content hash, map collision hash and compatible protocol range before joining.

The existing protocol provides welcome/snapshot/result/error, sequence-numbered input, stable command receipts and authoritative actor/cast/projectile/zone/economy state. Extend it deliberately rather than launching an unrelated native simulator with similar-looking rules. The following are design requirements for the engineering roadmap:

| Contract | Required fields and invariants |
| --- | --- |
| Hero definition | Stable ID, origin note, role, base stats, primary specification, three ordered ability IDs, asset/rig/animation/VFX/audio references, valid data version |
| Ability | Stable ID, targeting, geometry, timings, payloads, valid targets, cover rules, movement/action locks, cancellation/refund, upgrade scaling, effect event IDs; no hidden decorative damage |
| Map | Version/hash, world metres/axes, layers/support surfaces, collision primitives or meshes, lane graph, nav regions, spawn/tower/core/camp transforms, trigger volumes and visual-only tags |
| Animation manifest | Source/provenance, rig/rest hashes, clip duration/sample rate, in-place/root curve policy, grip/foot anchors and intervals, transition/action masks, event binding, accepted capture/report IDs |
| Actor snapshot | Stable identity/team, position including elevation/support layer, orientation and aim pitch, health/shield, movement mode, cast phase/time, equipment and status; authority owns outcomes |
| Effect/event | Stable event identity, world position including elevation, owner/team, rule-defined shape/timing, optional surface/layer reference and expiry; no local clock restart on reconnect |
| Match result | Match/rules/map IDs, final authority tick, reason, winner/draw, objective comparison, roster and individual contribution; repeated receipt cannot grant progression twice |
| Reuse manifest | Origin URL/revision/file hash, code versus asset license, attribution, modifications, redistribution decision, tool version and actual validation evidence |

**Coordinate bridge:** current shared aim is `(sin(yaw)cos(pitch), sin(pitch), cos(yaw)cos(pitch))`, so yaw0 faces+Z. Current native camera forward is `-pivot.global_basis.z`, so yaw0 faces-Z. The proposed adapter is `shared_yaw = wrap(native_yaw + PI)`, `shared_pitch = native_pitch`, with world x/z positions unchanged; the camera inverse uses `wrap(shared_yaw - PI)`. Actor/model orientation and rig-local aim axes remain separate. Cardinal directions, high/low pitch and round trips must be tested before enabling a real network weapon. This is a required adapter test, not an assertion that the current client already implements it.

**Elevation bridge:** aim pitch already exists in input and projectile motion; projectile/solid collision already considers height. Missing pieces include continuous remote actor pitch, authoritative traversable elevation/stacked support, ground targeting beyond y=0, and elevation semantics for zones/events/structures/pickups. Implement one versioned shared collision artifact and a two-client fixture with ramp, stairs, ledge, bridge-over-road, shots above/below and elevated area effects before promoting vertical geometry into the production map. Client mesh collision cannot be the competitive ground truth while the server still assumes zero-height landing.

## 10. Sound, interface and accessibility

Audio must communicate firing direction, approaching danger, damage, low health, shield depletion, ability ready/accepted/rejected, objective pressure, shard secure/steal and match end. Give each hero a coherent weapon/material palette. Distinguish allied and hostile action through spatial position and cue shape without requiring recognition of a voice line. Minion/ambient sounds receive lower priority than nearby player threats. Bounded voices, distance falloff, occlusion and event de-duplication prevent a full twelve-player fight becoming constant loudness.

Settings include master/music/effects/voice/UI volume, mute, dynamic-range preset, subtitles/captions where speech or unique cues matter, colour-vision presets, remappable keyboard/controller bindings, hold/toggle options, sensitivity, invert pitch, camera shake/bob strength, reduced motion/flashes, HUD scale and readable text. Important cues have visible equivalents; audio-only cue recognition is not required for basic participation. Test reduced-motion/low-effects presets in live fights, including Sita's protection and contested shard events.

HUD priority is reticle and hit/cover feedback; health/shield and critical status; three ability availability/commitment states; gold/build choice; objectives/clock/minimap; contextual ally calls. Avoid stacking several unprioritized notices over aiming. Buying shows exact effect, next price, affordability and place restriction. Settings save safely; invalid/corrupt data falls back visibly without losing access to controls. Menus neutralize held movement/fire; resuming does not release an accidental shot.

Pings cover attack/defend/retreat/group/camp/need help with spam limits, team-only visibility and useful world positions. Mute/report/block and streamer/privacy options belong in the complete product. Ranked access may require completed introductory matches for rule familiarity and abuse resistance, but it cannot require payment or hero unlocks. Avoid streak-loss penalties, paid random power, deceptive scarcity and compulsive daily chores. Cosmetics must preserve silhouette, team clarity and hitbox expectations.

## 11. Balance and human validation

Current health275–410, speed6.2–7.8, and nominal primary DPS41.67–57.14 describe starting values. Shared movement radius0.65 m and current projectile-hit sphere0.95 m centred1.1 m above actor origin are implementation facts, not anatomical precision. A production hitbox redesign requires explicit data and collision tests; cosmetic model height cannot secretly change fairness.

Do not tune solely to equalize a fixed bot table. Evaluate damage landed/avoided, effective healing and shielding, objective contribution, resource access, deaths after commitment, comeback opportunities, lane rotation, match duration and player comprehension together. Mirror map sides and compositions; stratify by player skill and input method. Compare crowd-control uptime and readable escape opportunities, not only aggregate win rate.

The initial human balance packet includes matched mirror games; three-role and unconventional compositions; all14hero matchups in a controlled arena; grouped healing/shield pressure; double summon pressure; long-range lanes; close-range dives; camp steals; low-economy comeback attempts; and split-push/core races. Record sample sizes, build/rules hashes and uncertainty. A passing simulated match or technical soak does not establish fun, cultural fit, equal strength or commercial visual quality.

## 12. Acceptance scenarios for a complete game

These scenarios connect design to the production roadmap; each needs an owner, exact build and preserved result. A scenario is open until executed.

| ID | Scenario | Pass condition |
| --- | --- | --- |
| GD01 | Fresh native install → settings → practice → home | Controls/focus/audio work throughout; no network needed for practice; no stale loading completion |
| GD02 | Two real clients join, leave, reconnect and replace an older tab/session | One identity/control owner; no duplicated actor, reward, cast or audio; cleanup is bounded |
| GD03 | Three-lane3v3 native vertical slice completes with Rama/Hanuman/Sita | Actual movement/combat and the selected heroes’ nine ability slots follow authority; waves/camps/shop/objectives/end/replay work |
| GD04 | Six distinct accepted heroes per team in a6v6 production-format match | Twelve real clients or declared bot/client mix; correct slots/rules; no inherited six-player evidence claimed as twelve-player proof |
| GD05 | Outer/inner/core progression, simultaneous defeat and18-minute cap | All protections/tiebreak/draw states match declared rules and UI; no farm-score win in the proposed ranked format |
| GD06 | Fourteen heroes use primary and all42 abilities against allies, enemies, cover and structures | Payload, geometry, cooldown, locks, cancellation, scaling and descriptions agree; unsupported effects absent |
| GD07 | All14heroes animate continuously through the full matrix | Actual render review meets grip/feet/loop/deformation/transition criteria; source clips and model hashes recorded |
| GD08 | Rama/Hanuman/Sita timed casts under death, lag and reconnect | Warning/payload timing comes from authority; no late replay, through-wall leap or phantom sanctuary |
| GD09 | Wave cap, summons, ministers, siege and jungle leash/reset | Symmetric admission and correct recipients; expiry/defeat cleanup; zero duplicate or reset rewards |
| GD10 | Two players contest one shard with simultaneous shot/proximity | One award, correct secure/steal label, bounded lifetime; banked wallet untouched |
| GD11 | Ramp/stairs/stacked bridge, high/low aim and elevated zone | Native/server coordinate and support agreement; no aim reversal, floating landing, ground-level false hit or wrong-layer effect |
| GD12 | Day/night, low/high quality, colour presets, reduced motion | Actionable silhouettes, boundaries and timing remain readable without flicker/shimmer or hidden gameplay changes |
| GD13 | Controller/keyboard navigation, scaling and unusual aspect ratios | All core actions and settings accessible; no clipped controls, focus trap or menu-to-game held-input leak |
| GD14 | Full match population/effects and repeated match lifecycle | Declared hardware/performance budgets met, memory/socket/audio bounded; reported percentiles and worst cases, no synthetic hardware claims |
| GD15 | Server interruption, protocol mismatch, malformed input, packet delay/loss and reconnect timeout | Clear recovery/error UX; authority stays valid; no reward/command replay abuse; result integrity preserved |
| GD16 | Actual packaged Linux/Windows release and operated online endpoint | Each platform tested on its actual runtime; package/assets/provenance verified; public service tested separately from static hosting |
| GD17 | Human visual/readability/cultural/balance reviews | Defects triaged and repaired with evidence; unresolved major problems keep the production gate open |

## 13. Working method, sources and unresolved decisions

Implement in the production roadmap's dependency order. Each squad uses four rounds: source/baseline audit → concrete implementation → actual integration/render/play test and repair → independent review with exact evidence. A completed export, generated image, clip count or written document cannot close a visual/gameplay gate. Keep concepts, source assets, licensed references, authored Blender files, exported models, manifests, actual captures and QA reports in separate organized folders. Preserve unsuccessful evidence when it explains a repaired defect.

This design pass audited local `games/yuga/shared/heroes.ts`, `types.ts`, `map.ts`, `simulation.ts`, the browser README, implementation contract, mythology/roster, minion/jungle and roster mechanics documents, hero art bible and native source library/roadmap. It did not read every book, watch current commercial gameplay, recover Deadlock/Overwatch clients or conduct a new Reddit art study. Prior source records document selected Griffith/Ganguli passages and architecture excerpts; their translations and historical interpretations have stated limits. Prior Reddit text samples are small and cannot stand for all players or authoritative mythology.

Useful source links and responsibilities:

- [Current hero definitions](../../yuga/shared/heroes.ts), [types](../../yuga/shared/types.ts), [map](../../yuga/shared/map.ts), [simulation](../../yuga/shared/simulation.ts): current executable design values.
- [Mythology and roster](../../yuga/docs/MYTHOLOGY_AND_ROSTER.md): exact literary passages and invented-kit distinctions.
- [Minions/jungle](../../yuga/docs/MINIONS_AND_JUNGLE.md), [roster mechanics](../../yuga/docs/ROSTER_MECHANICS_REVIEW.md), [hero art bible](../../yuga/art/HERO_ART_BIBLE.md): current detailed mechanics and presentation contracts; read dated status as historical evidence, not automatic present completion.
- [Native source library](../art/production/SOURCE_LIBRARY.md): inspected literary/architecture sources, original concept provenance and asset reuse terms.
- [Reference-character import](research/REFERENCE_CHARACTER_IMPORT.md) and [character reuse audit](research/CHARACTER_REUSE_AUDIT.md): official Godot TPS reference asset/rig inspection and distinct code/art licensing. A candidate bone map is not a completed retarget.
- [Research-engineering desk](RESEARCH_ENGINEERING_DESK.md): current tool study and bounded collision/animation experiments. REA/Ghidra has analyzed an original compiled fixture; commercial binary reconstruction remains unverified.
- [Production roadmap](FULL_GAME_PRODUCTION_ROADMAP.md), [machine-readable backlog](ROADMAP_BACKLOG.json), [independent guide review](PRODUCTION_GUIDE_REVIEW.md): task ownership, dependencies, acceptance and review.

Defaults are6v6/18minutes,14heroes, simultaneous blind selection, mirrored opponent picks, six towers per team, four minor jungle courts, the existing three upgrade tracks first and native desktop first. Open experiments are universal sprint policy, equipment expansion, target-assistance policy, exact final map dimensions/vertical routes, ranked rating/placement and queue population thresholds, cultural/voice review, and final target hardware budgets. Each has a concrete owner/gate in the roadmap; none blocks writing or implementing the already-defined3v3 native slice. None is resolved by claiming the preview is the complete game.

### Three-round design review record

1. **Audit:** established3v3/480s,14heroes/42slots/three timed mechanics, four camps, current upgrade formulas and mixed2.5D authority from actual sources. Identified native courtyard versus full browser-rule mismatch and current nine-clip versus production-motion gap.
2. **Specification:** selected explicit6v6/18minute full-game rules and phased hero rollout; specified player journey, objectives, economy, all42kits, actual animation/VFX contracts, district topology, accessibility and acceptance scenarios. Kept speculative item/sprint/assistance work separately labelled.
3. **Self-critique and dependency handoff:** checked team uniqueness requires six accepted heroes, no look-only melee promise, no unsupported vertical route, no static-site multiplayer claim, no stale lost-worker art claim, no commercial-fidelity claim. Handed spatial/yaw/pitch issues to the engineering desk and production roadmap; independent review remains the final guide check.
