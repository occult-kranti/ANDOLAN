# YUGA-HERO-6R · rounds 1–2 reference panel

Product: **YUGA native desktop**, existing offline Rama. Baseline inspected:
`7162b5d0b666e4422b0bc73100e1fba947d3323f`, branch `work/yuga-studio`, with the
15 November studio changes already present. Owner: `reference_panel` (evidence,
level design, independent review). This packet supports existing FG01/FG02/FG05
production work; it does not mark those tasks complete.

**Decision:** retain Rama's current five-action kit and make commitment, release,
counters, cooldown and world utility legible in the actual game. The reference
supports deliberate tactical variety and connected urban routes. It does not
justify replacing the current engine, importing a commercial game's art, or
calling a still-image pass finished character production.

## Input identity and actual review scope

| Supplied file | Bytes | Duration / video | SHA-256 |
|---|---:|---|---|
| `gameplay.mp4` | 147,387,363 | 34:06.885; 640×360; 29.97 fps | `bed8ca9b5981a0509041b95f32392762a05358d20edb390cce1388c451b982bb` |
| `all ults.mp4` | 219,141,934 | 43:15.875; 640×360; 30 fps | `6ae05fe2bac16862b55fab347f47b8fde2f66dd693bca52695278919da66443c` |

The second file identifies itself at **00:25** as **“The basics of every Deadlock
character”**. It covers ordinary skills, passives, movement and ultimates. The
first file's result card at **33:50–33:52** identifies the played hero as **Celeste**.
These are claims about the supplied pixels, not verification of the current
public game's roster, patch, creator, release status or underlying rules.

Personally inspected all **103** timestamped samples across gameplay (first
frame then ≥20 seconds between selected source frames), all **520** samples
across the explainer (5-second spacing), and all **208** denser samples listed
below. That is **831 annotated extracted frames**, not 77 minutes of uninterrupted
normal-speed viewing. The 1-second sequences reveal order and broad movement;
they cannot resolve subsecond anticipation, continuous foot contact or frame-perfect
release timing. No audio was listened to, no transcript generated, and no
controller input into Deadlock was performed. Source files are unchanged. PNG
extracts retain 640×360 dimensions with a timestamp overlay; JPG contact sheets
reduce each frame to 320×180 for navigation. Tiny text and values remain uncertain.

| Reviewed sequence | Spacing / frames | What it resolves |
|---|---:|---|
| [Gameplay full-duration sheets](gameplay-sourcepts-20s/receipt.json) | ≥20 s / 103 | Broad progression, map contexts, HUD, result boundary |
| [Explainer full-duration sheets](ults-sourcepts-5s/receipt.json) | 5 s / 520 | All 44 visible title-card segments and ability vocabulary |
| [Gameplay 00:15–00:32](gameplay-traversal-15s-r2/receipt.json) | ≥1 s / 18 | Stairs, corner changes, airborne attacks, persistent HUD |
| [Gameplay 01:10–01:27](gameplay-cover-70s-r2/receipt.json) | ≥1 s / 18 | Elevated ledge, low lane, stairs, hard corners, re-entry |
| [Gameplay 16:30–16:47](gameplay-supply-990s-r2/receipt.json) | ≥1 s / 18 | Vertical rotation into a strikeable world utility |
| [Gameplay 19:55–20:14](gameplay-objective-1195s-r2/receipt.json) | ≥1 s / 20 | Side approach, contested chamber, large neutral-looking target |
| [Gameplay 33:40–34:04](gameplay-result-2020s-r2/receipt.json) | ≥2 s / 13 | Fight → Victory → Celeste card → scoreboard → graph |
| [Calico 03:50–04:27](ults-calico-230s-r2/receipt.json) | 1 s / 38 | Four named abilities, transformed traversal, return explosion |
| [Celeste 04:35–05:19](ults-celeste-275s-r2/receipt.json) | 1 s / 45 | Vertical movement, cone, protective prism, delayed beam, bouncing orb |
| [Grey Talon 10:31–11:08](ults-grey-talon-631s-r2/receipt.json) | 1 s / 38 | Charged line, airborne fire, armed trap, player-directed projectile |

**Retained corrections:** `gameplay-20s` and `ults-20s` are preliminary `fps`
resampling outputs. Their labels were output-grid time, not trustworthy exact
source-frame PTS. They were rejected for exact timestamp attribution and replaced
by the `sourcepts` sets. Earlier dense directories without `-r2` retain an input/
output trim-order failure: restoring absolute PTS before an output `-t` cutoff
produced zero or too few frames. The helper now uses an input duration bound.
Do not count the preliminary/failed frames as additional reviewed coverage.
An early overview impression called the green utility a shop: the dense view
shows **Sinner's Sacrifice**, repeated strikes and changing health/effect numerals;
**no shop menu appears**. The corrected interpretation below supersedes it.

## Gameplay observation → design decision

Times below are source timestamps, rounded to seconds only in prose.

| Source time | Direct observation | Inference / unresolved point | Original YUGA implementation priority |
|---|---|---|---|
| 00:15–00:32 | Hero attacks while changing steps, corners and vertical position. Ability pips, minimap and team strip stay in stable screen regions. | Exact input, stamina cost and animation latency cannot be derived from 1 s samples. | Keep aim/body/movement ownership separate; current bindings and readiness stay visible during motion. |
| 01:10–01:27 | Elevated ledge overlooks a lower street; a staircase reconnects them. Solid masses divide sightlines; player returns to combat from a different angle. | A screenshot cannot measure route distance, collision shape or fairness. | One useful gallery loop with both a ramp and a retreat exit; record actual traversal time, camera collision and shot occlusion. |
| 04:35–04:49 explainer | Celeste repeatedly traverses ledges and vertical walls before ability panels. | Exact movement command sequence remains unknown. | Rama's flight/grapple must have visible anchors/support and reliable landing feedback. Do not imply his ground-only kit works from unsupported elevation. |
| 05:01–05:10 explainer | Celeste protective prism and delayed vertical beam appear as distinct shapes. | Tooltip rules are presented by an edited explainer, not independently measured. | Guardian Circle needs a fixed readable footprint and active duration; Pierce/Volley need different warning geometry. |
| 08:20, 16:38–16:47 | A green, labelled Sinner's Sacrifice machine is struck. Health changes and luminous numeric effects appear. | Risk/reward is a reasonable hypothesis; exact exchange and cooldown were not established. This is not verified shopping. | Existing relay/supply state is the nearest useful YUGA interaction. Show eligibility, gain/cap and contest state; any new resource trade must be an explicit simulation rule. |
| 10:40 onward, several visits | Side chambers, streets, high platforms, interiors and sightline breaks recur. | Samples do not reconstruct a complete map graph or all objectives. | Build a testable connected encounter module; do not copy the source map layout or infer hidden geometry. |
| 16:34–16:38 | A tether-like line and rapid vertical traversal lead into the utility area. | Its exact originating ability/item is not confirmed. | Make original anchor locations match collision and the overview; explain unreachable/blocked anchors. |
| 19:55–20:14 | The player enters a chamber containing a large target with a large health bar; other actors/effects appear, and a STUNNED state is visible. | Target reward, respawn, team eligibility and exact stun cause are unknown. | A future neutral objective needs entry/exit, clear threat geometry, reward authority and contested timing. Do not treat an ornamental statue as implemented gameplay. |
| 21:21, 24:21, 31:21, 33:40–33:44 | Several large effects overlap and partially hide actors/ground. | Reference popularity is not proof that all visual choices are readable. | Reserve the reticle/target/feet areas. Bound light and VFX opacity; keep hostile warnings distinct from decorative gold. |
| 30:01 | Sleep text/ZZZ makes a control-loss state visible near the hero. | Duration/counter not measured. | If future crowd control is added, show cause and remaining time from simulation; don't invent it in presentation. |
| 33:46–34:04 | Explicit Victory overlay, authored character result card, detailed scoreboard, then a graph view. | Player comprehension, accuracy of every metric and end-match server behavior are untested. | Existing offline outcome should flow to truthful results and restart/leave; more charts wait for meaningful collected metrics. |

## Explainer roster and ability taxonomy

Every row has a **visible hero title card** at the listed sample time. Ability
names are transcribed from readable panels and describe this recording only.
“Unresolved” means the sampled panels did not establish that slot; it is not
filled from memory or a wiki. Inferred play roles are the panel's taxonomy,
not a promise of current official behavior. A listed tooltip is evidence that
the explainer *presents* that rule, not a reproduced gameplay test.

| # / visible title / title sample | Named ordinary abilities observed | Named ultimate / major mode observed | Tactical pattern suggested by the presentation |
|---|---|---|---|
| 1 Abrams · 00:30 | Shoulder Charge; Infernal Resilience; first slot unresolved in 5 s sweep | Seismic Impact (00:50) | Close approach, sustain, airborne area initiation |
| 2 Apollo · 00:55 | Disengaging Sigil; Riposte; Flawless Advance | Itani Lo Sahn (01:25–01:30) | Retreat mark, parry, precision thrust, committed line burst |
| 3 Baba · 01:35 | Threadsap; Granny Long Legs; Baba's Brew | Feed The Birds (02:05) | Debuff/projectile, transformed movement, curse/support, persistent multi-hit threat |
| 4 Bebop · 02:10 | Exploding Uppercut; Sticky Bomb; Grapple Arm | Hyper Beam (02:40–02:45) | Displacement combination and sustained directional beam |
| 5 Billy · 02:50 | Bashdown; Rising Ram; Blasted | Chain Gang (03:20–03:25) | Melee entry, launch, sustain/ammo interaction, delayed tether punishment |
| 6 Calico · 03:40 | Gloom Bombs; Leaping Slash; Ava | Return to Shadows (04:11–04:25) | Delayed bombs, melee sustain, cat traversal, vanish/reappear burst |
| 7 Celeste · 04:30 | Light Eater; Dazzling Trick; Radiant Daggers | Shining Wonder (05:11–05:19) | Cone debuff, protective prism, delayed ground beam, bouncing orb |
| 8 Deadman Donny · 05:25 | Strix Salvo; Chimera Mk1; Jettison Fuel | Close The Deal (06:15) | Marked missiles, movement/heat, trailing hazard, grab-and-crash commitment |
| 9 The Doorman · 06:25 | Call Bell; Doorway; Luggage Cart | Hotel Guest (06:55–07:05) | Area mark, paired portal, moving displacement, temporary relocation |
| 10 Drifter · 07:10 | Rend; Stalker's Mark; Bloodscent | Eternal Night (07:55–08:00) | Close-range precision, mark/recast chase, isolation information, restricted enemy vision |
| 11 Dynamo · 08:10 | Kinetic Pulse; Quantum Entanglement; Rejuvenating Aurora | Singularity (08:45–08:55) | Knockup, short teleport, allied healing, channeled area grouping |
| 12 Graves · 09:05 | Jar of Dead; Grasping Hands; Essence Theft | Borrowed Decree (09:45–10:05) | Stored summons, area root, stat drain, growing summon pressure |
| 13 Grey Talon · 10:25 | Charged Shot; Rain of Arrows; Spirit Snare | Guided Owl (10:54–11:08) | Charged line, airborne fire, armed trap, controllable projectile |
| 14 Haze · 11:15 | Sleep Dagger; Smoke Bomb; Fixation | Bullet Dance (11:40) | Single-target disable, stealth rotation, repeated-hit scaling, local sustained fire |
| 15 Holliday · 11:55 | Powder Keg; Bounce Pad; Crackshot | Spirit Lasso (12:35) | Delayed explosive, physical launch utility, precision hit, dragged target |
| 16 Infernus · 13:00 | Napalm; Flame Dash; Afterburn | Concussive Combustion (13:35–13:40) | Area coating, trail movement, damage over time, delayed self-centered detonation |
| 17 Ivy · 13:50 | Entangling Thorns; Kudzu Connection; Stone Form | Air Drop (14:25–14:30) | Ground denial, linked support, defensive transformation, ally transport/drop |
| 18 Kelvin · 14:40 | Frost Grenade; Ice Path; Arctic Beam | Frozen Shelter (15:10–15:15) | Heal/damage area, temporary route, beam control, enclosed defensive zone |
| 19 Lady Geist · 15:25 | Essence Bomb; Life Drain; Malice | Soul Exchange (16:20–16:30) | Health-cost offense, maintained tether, stacking debuff, health reversal |
| 20 Lash · 16:40 | Ground Strike; Grapple; Flog | Death Slam (17:10–17:25) | Height-to-ground attack, aerial reposition, close sustain, area displacement |
| 21 McGinnis · 17:35 | Mini Turret; Medicinal Specter; Spectral Wall | Heavy Barrage (17:55–18:00) | Deployables, healing location, occluding wall, targeted artillery |
| 22 Mina · 18:30 | Rake; Sanguine Retreat; Love Bites | Nox Nostra (19:15–19:25) | Close heal, escape/recast, bite buildup, seeking bat swarm |
| 23 Mirage · 19:45 | Fire Scarabs; Dust Devil; Djinn's Mark | Traveler (20:35–20:50) | Projectile utility, evasive displacement, marks, delayed map relocation |
| 24 Mo + Krill · 20:55 | Scorn (overlapping panel at 21:15); Burrow; Sand Blast | Combo (21:35–21:50) | Local sustain, underground entry, disarm, held-target channel |
| 25 Nurse Harrow · 21:55 | Leech Therapy; Wretched Vapors; Healing Needles | Lurking Terrors (22:50–23:00) | Collected heal resource, buff mode, heal ammunition, fear-area release |
| 26 Paige · 23:05 | Bookwyrm; Plot Armor; Captivating Read | Rallying Charge (23:35–23:45) | Traveling hazard, ally barrier, delayed root zone, team push |
| 27 Paradox · 23:50 | Pulse Grenade; Time Wall; Kinetic Carbine | Paradoxical Swap (24:40–24:50) | Repeated area pulses, projectile-time surface, charged shot, position exchange |
| 28 Pocket · 25:00 | Barrage; Flying Cloak; Enchanter's Satchel | Affliction (25:45–25:55) | Channeled projectiles, traveling teleport marker, timed escape, local damage over time |
| 29 Rat King · 26:15 | Scrap Grenade; Rat Swarm; Royal Pestments | Rule, Ratannia! (27:00–27:25) | Delayed area explosive, attached swarm, defensive form, empowered moving hazard |
| 30 Rem · 27:40 | Pillow Toss; Tag Along; Lil Helpers | Naptime (28:40–28:50) | Knockback, ally attachment/heal, utility assistants, delayed sleep wave |
| 31 Seven · 29:05 | Lightning Ball; Static Charge; Power Surge | Storm Cloud (29:45–30:00) | Traveling area threat, delayed target stun, chained attacks, exposed area channel |
| 32 Shiv · 30:05 | Serrated Knives; Slice and Dice; Bloodletting | Killing Blow (30:50–31:10) | Bleed buildup, dash, deferred damage, threshold finisher |
| 33 Silver · 31:15 | Slam Fire / Go For The Throat; Boot Kick / Mauling Leap; Entangling Bola / Tail Whack | Lycan Curse (31:30), shown as transformation mode | Two form-specific action vocabularies; role/motion/silhouette must change coherently |
| 34 Sinclair · 32:50 | Vexing Bolt; Spectral Assistant; Rabbit Hex | Audience Participation (33:35–33:45) | Redirectable shot, clone/swap, transform control, copied enemy ultimate |
| 35 Solomon · 33:55 | Setup Bishop; Kingside Knight; Rook Battery | Develop Queen (34:35–34:45) | Placed pieces, ally enhancement, reflected lanes, positional area command |
| 36 Venator · 34:50 | Consecrating Grenade; Gutshot; Hex-Lined Snap Trap | Ira Domini (35:25–35:35) | Delayed explosive, knockback, armed trap, limited empowered shots |
| 37 Victor · 35:45 | Pain Battery; Jumpstart; Aura of Suffering | Shocking Reanimation (36:25–36:35) | Damage-stored attack, health-cost sustain, self-cost aura, delayed recovery/area release |
| 38 Vindicta · 36:40 | Stake; Flight; Crow Familiar | Assassinate (37:00–37:05) | Tether zone, aerial fire, debuff projectile, scoped execution |
| 39 Violet · 37:20 | Living Ink; Flow State; Still Life | Abstract Landscape (38:30–38:40) | Empowered shots, traversable trail, maintained target focus, vision-blocking field |
| 40 Viscous · 38:45 | Splatter; The Cube; Puddle Punch | Goo Ball (39:20–39:30) | Slowing ground, defensive enclosure, surface displacement, rolling collision mode |
| 41 Vyper · 39:35 | Screwjab Dagger; Lethal Venom; Slither | Petrifying Bola (39:55–40:00) | Debuff shot, delayed poison, sliding passive, direct-hit/area control distinction |
| 42 Warden · 40:20 | Alchemical Flask; Willpower; Binding Word | Last Stand (40:45–40:50) | Debuff projectile, self barrier/speed, escape-or-root test, delayed pulsed sustain |
| 43 Wraith · 40:55 | Card Trick; Project Mind; Full Auto | Telekinesis (41:25–41:35) | Stored projectiles, point teleport, firing buff, lift/throw target control |
| 44 Yamato · 41:45 | Power Slash; Flying Slash; Crimson Slash | Shadow Transformation (42:15–42:30) | Charged line, target grapple, local sustain, temporary empowered survival |

This is not a universal four-button template: passives, transformed actions,
recasts, charges and channel commitments recur. Most excerpts show a stationary
training opponent; they do not prove team balance, counterplay success or netcode.
The panel should borrow **readable decisions**, not these names, effects, artwork,
values or map topology. In particular, generic bow use does not make Rama a
reskinned Grey Talon. Rama's existing lane protection and fixed three-line volley
should define a different identity.

## Rama: concrete accepted design direction for round 2

Rama is a **lane guardian and deliberate archer**. His visual anchors are the
bow curve, readable draw silhouette, draped ivory cloth, indigo/blue body-family
palette and restrained aged-brass details already present in project art. Ground
warnings use original geometric language. Avoid giving every object gold glow:
that erases the distinction between architecture, friendly protection and danger.
This is fictional epic-inspired art, not an archaeological or canonical depiction.

| Existing action | Player decision | Presentation contract | Counter/readability acceptance |
|---|---|---|---|
| Kodanda / LMB | Repeated aimed pressure while moving | Visible draw/release and a small impact; preserve 20 Hz owner | Miss, cover stop and actual receiver hit must remain distinguishable |
| Piercing Dawn / Q | Commit to a longer draw for aligned enemies | One narrow directional warning, distinct from primary | Solid cover stops it; shoulder/bow motion must not claim an early hit |
| Measured Step / E | Reposition while retaining aim | Brief displacement trail with clear landing/contact | Cover limits distance; no invulnerability is invented; supported endpoint |
| Guardian Circle / C | Hold a location for self/allied troops | Fixed footprint, entry cue, duration; not a traveling aura | Field placement respects range/cover; explain leaving its protection |
| Dawn Volley / X | Lock three lanes and punish a corridor | Three readable pending lanes; each remains until **its own** release | Lateral escape and cover remain usable; first arrow must not erase later warnings |

Panel approves root's scoped correction to pending Volley lanes and a live
cooldown/cast/active phase strip, subject to actual rendered and input evidence.
**Adverse cases:** move during windup; first/second/third arrow release; interrupt
before/after first release; pause/reset; cooldown nearly ready; insufficient ammo;
field expiry; wall between source and target; remapped controls and enlarged UI.
A new VFX piece cannot mutate damage, release timing, collision or availability.
The current ground-only cast limitation must remain explicit until shared
elevation authority is actually implemented.

## Original Indian/South Asian map interaction brief

Use the existing Sangam fiction and the research brief's precise source
associations. A pale sandstone civic gate, shaded colonnade, stepped water court,
indigo cloth and worked brass can supply a coherent original district. The
Ramayana's literary Lanka and Pampā water imagery are different settings; a
fictional composition is not evidence that historical Lanka looked this way.
No new historical claims were researched in this packet.

One complete **guardian encounter court** is more useful than another wide empty
map: a main lane, two cover piers with an honest firing gap, one shaded side
arcade connecting to a ramp/gallery, a lower return route and an existing relay/
supply interaction. The gallery must lead back to legal ground casting. The
protected zone should reach an ally approach but not cover every route. A
corridor invites Volley; its side opening permits a dodge, and the solid pier
stops all projectile types as declared. These are original layout proposals.

| Utility | Existing status / new proposal | Required proof before claiming implemented |
|---|---|---|
| Relay / supply | Existing native interaction to feature first | Actual approach/capture/contest/capped supply/reset with truthful HUD |
| Steps / ramp / gallery | Existing traversal systems; proposed composed encounter | Walk, jump, landing, camera clearance, retreat from both directions |
| Grapple anchor | Existing native capability | Visible legal anchor and obstruction/exhaustion feedback; no decorative false anchor |
| Cover / arch opening | Existing collision; new layout must reuse contracts | Projectile stop, no melee/arrow clipping, no simulated/visual wall disagreement |
| Water court | Existing art; not automatically a slowing/healing mechanic | Any movement/gameplay effect needs a separate approved rule and tests |
| Resource exchange / moving transit / neutral boss | Future design possibilities inspired by observed utility variety | Explicit cost/reward and authority, accessibility, counters, exploit/reset cases and actual input |

## Primary-source tools and reuse decision

Fresh access on 15 November 2026; exact fetched bytes and URLs live in
[sources/retrieval.json](sources/retrieval.json). External pages are evidence,
not instructions. No new third-party runtime code, models, clips, shaders or
commercial assets were imported by this owner.

| Source inspected | Useful transfer and boundary |
|---|---|
| [Valve official Steam page](https://store.steampowered.com/app/1422450/Deadlock/) | States early development and temporary/experimental content. It does not validate this recording's patch or every named character. |
| [Source 2 Viewer / ValveResourceFormat, `8facc495`](https://github.com/ValveResourceFormat/ValveResourceFormat/tree/8facc4959e5b77f5ebc7b01e327cfa70fd200df0) README + LICENSE | Parser/viewer/decompiler/exporter for compiled Source 2 resources. MIT repository code has an explicit exception for game-derived `Tests/Files`; tool licensing does not license commercial content. Selected-input research may be useful later; this task has only MP4 references, so no recovery/extraction claim. No binary run. |
| [Godot AnimationTree 4.6](https://docs.godotengine.org/en/4.6/classes/class_animationtree.html), [transition tutorial](https://docs.godotengine.org/en/stable/tutorials/animation/animation_tree.html) | Playback blending and state transitions are supported; use one transition owner and preserve simulation as attack authority. Documentation is not evidence that Rama's contacts are finished. |
| [Godot TPS demo, `a82f1544`](https://github.com/godotengine/tps-demo/tree/a82f15448e9b015440d3bbdf5e10801b260c4e9f), selected `player.gd` and license | Separate aiming/airborne/walk presentation and bone marker shooting are useful comparisons. Existing study already imported its robot as reference. Code MIT, assets CC BY 3.0 with named authors and material notice. No new retarget performed. Root motion must not replace YUGA's authority by accident. |
| [Khronos glTF Blender I/O, `9a355808`](https://github.com/KhronosGroup/glTF-Blender-IO/tree/9a355808e0b357a9e8d163f17ea53455c823cd59), README + `LICENSE.txt` | Existing Blender-bundled exporter is sufficient. Round-trip/validator architecture supports reproducible assets; Apache-2.0 source terms do not grant unrelated asset rights. No reason to install a second engine or current addon over the pinned studio toolchain. |
| Existing [open-source catalog](../../../../../../tools/research/opensource-catalog.json) and [research brief](../../RESEARCH_BRIEF.md) | REA, Prometheus, OWLib, OWM, open-engine and demo studies have distinct selected-file terms and actual execution scopes. This packet read the catalog and retained reports; it did not rebuild every repository. REA/OWLib cannot manufacture an absent Deadlock server or ready-to-ship Indian hero. |

The Blender manual web route returned 402 and the short Source 2 docs URL was
inaccessible through web; no claims are attributed to unread pages. Raw official
Khronos repository files were accessible. Two initial wrong license filenames
returned 404; the actual `LICENSE.txt` was retrieved. Live upstream HEAD pins
are research revisions, not installed-engine or Blender binary identities.

## Commands, results and handoff

All source extraction, image decode/contact creation and fresh source retrieval
commands completed on the declared inputs. Per-run receipts contain exact argv,
ffprobe output, return codes, frame counts and artifact hashes. The helper needs
only Python standard library, FFmpeg/ffprobe and the installed DejaVu font; a
missing system Pillow module was observed and did not require a dependency install.

```sh
python3 tools/studio/analyze-hero-reference.py gameplay.mp4 \
  --output games/yuga-native/docs/research/hero-six-rounds/reference/gameplay-sourcepts-20s --step 20
python3 tools/studio/analyze-hero-reference.py 'all ults.mp4' \
  --output games/yuga-native/docs/research/hero-six-rounds/reference/ults-sourcepts-5s --step 5
python3 tools/studio/analyze-hero-reference.py 'all ults.mp4' \
  --output games/yuga-native/docs/research/hero-six-rounds/reference/ults-celeste-275s-r2 \
  --start 275 --duration 45 --step 1
```

Use a **fresh** output directory when reproducing. Remaining dense exact commands
are in the table-linked receipts. No native game test/import/render or release
was run by this research owner in rounds 1–2. No CPU throughput, hardware FPS,
human listening, full gameplay comprehension or complete hero-art claim follows
from this work.

Changed files: this reference directory and `tools/studio/analyze-hero-reference.py`.
Final source/output hash inventory: [handoff.json](handoff.json). Next owners:
root integrates the design/roadmap; combat owner fixes and tests lane-warning
lifetime; UI owner qualifies live feedback; art owner supplies source-bound
in-game views; this reviewer returns for independent actual capture review in
rounds 4–5. Human visual direction, ordinary player feel, complete rig/cloth/
hair/contact acceptance, rendered online clients and physical-GPU performance
remain open.
