# Original native invocation effects — MYTH09

The native practice scene can present fourteen original invocation motifs through the current Rama avatar. `ultimate_effects.gd` consumes local session events. It never changes damage, healing, shields, slows, summons, movement, collision, gold or core health. These are invocation studies, not fourteen new character models or an online match system.

## Contract and ownership

Add the Node3D script to the active world, then connect `ultimate_session.invocation_event` to `consume_event(event)`. The node processes visual time itself using `PROCESS_MODE_PAUSABLE`; explicit `step(delta)` is also available for deterministic headless tests with processing disabled. `set_suspended(true)` freezes local time and refuses new nonterminal events. `reset()` frees every owned child synchronously while retaining the epoch/cast high-water mark, so delayed same-epoch events cannot resurrect a discarded cast. A fresh authoritative reset requires a newer epoch. `set_options({reduced_effects: bool, reduced_motion: bool})` changes presentation only; the selector owns persistence.

Events carry `schema`, `kind`, `epoch`, `cast_id`, `event_seq`, `hero_id`, `effect_id`, `team`, `time_s`, `origin`, `forward`, `target`, `timing`, `geometry` and bounded `receipts`. Accepted geometry is locked at begin. Newer attachment snapshots may change without moving the initial footprint. Duplicate, stale, malformed, nonfinite and oversized events are refused before creating children. The FX clock has a bounded safety expiry if a terminal event is lost; authoritative end/cancel/reset removes the effect immediately.

`geometry` supplies world-space origin/centre/forward, exact rule radius/range/sector cosine, indexed projectile rays, or two validated summon placements. Ground strokes are derived from those values, never from the decorative codex envelope. Disk strokes are inscribed at their supplied radius. Sector strokes use a 2 mm / 0.001 rad interior margin to avoid floating-point or tessellation vertices crossing the exact closed authority boundary. Projectile warnings show the swept capsule envelope; cover can still stop a projectile. Warnings retire at release for projectiles, at impact for one-shot effects, and at active-zone expiry for persistent zones. They are visible on low effects and reduced motion with no dependence on sound.

Indexed projectile contact events remove only the corresponding visible arrow. The visual arrow cannot continue beyond an accepted wall/unit/range contact. For shields and summons, current `geometry.attachments` snapshots contain unique living `unit_id`, world `position`, `kind`, `shield`, and `remaining_s`. The renderer stores IDs and positions, never unit object references. Missing/depleted/expired entries disappear; moving entries update one merged mesh. There are no cosmetic shields before an actual accepted attachment snapshot.

## Fourteen distinct geometric studies

| Invocation | Original visible construction |
| --- | --- |
| Rama | Three bent bow outlines and an open solar frame, resolving into three indexed arrows. |
| Ravana | Ten faceted crown petals arranged as an opening iris, with fine brass spines. |
| Arjuna | Three open mirror gates down the locked lane and one travelling silver needle. |
| Duryodhana | A broken vertical crescent gate above forward bronze wedge ribs; open rear. |
| Hanuman | Three mountain-contour processions, a descending projected payload and leaf ornaments; no avatar leap claim. |
| Karna | Six sunwheel armour facets and spoke lines turn outward around an open solar frame. |
| Bhima | Eight broad low drum/stone ribs lift and compress without changing terrain. |
| Meghnad | Three long storm-scroll ribbons unroll in a forward fan, with angular lightning ends. |
| Sita | Four open branch arches and seed/leaf ornaments surrounding an empty sanctuary centre. |
| Draupadi | Five narrow translucent banners with one floor seam assembly. |
| Subhadra | Exactly two banner-chariot formation ornaments, then accepted mobile sentinel standards with a draining crest. |
| Hidimbi | Exactly two split-seed branch formations, then sparse marks above actual summoned troops. |
| Chitrangada | Six crossing crescent plates, followed by accepted recipient shield arcs. |
| Ulupi | Two low braided river-serpent contours with inward heads around an open basin. |

All meshes are original mathematical construction in the script. No commercial-game assets, textures, extracted animation, external model download or deity miniature is used. No shader time, screen flash, camera shake, refraction, screen blackout, particle system or additional light is used. Standard material opacity and simple transforms animate bounded merged geometry. The designs follow the project's independently authored codex; they are not claims of historical reconstruction or commercial-game parity.

## Budgets and evidence

At most four visual casts may coexist for stress fixtures. The gameplay adapter allows one active invocation with its shared cooldown; a visual fixture does not bypass that rule. Per cast the limits are 48 mesh instances, 16 potential draw calls and 18,000 triangles; particles, added lights and FX-owned audio voices remain zero. The separate invocation-audio module owns its three-voice budget. Each current motif uses two merged ornament surfaces plus its warning, an optional merged attachment surface and at most three projectile surfaces. Up to 72 accepted recipient marks fit in one mesh instead of 72 nodes. Reset/expiry frees all per-cast meshes/material references; there is no unbounded scene pool or combat history.

`tests/ultimate_effects_cases.gd` passes 76 focused checks on the frozen runtime: all fourteen distinct geometries and exact warning inclusion, unchanged low/reduced warning meshes, complete finite 60 Hz lifecycle samples, corrupted input refusal, indexed contact, duplicate/reset replay handling, pause, 72 wards in one mesh, four-cast cap, and 24,000 accelerated steps representing twenty minutes with no remaining nodes. The ordinary motif maximum observed by that owner fixture is 2,136 triangles; the ward case separately checks the larger merged-recipient total stays below 18,000. These are structural and lifecycle checks, not GPU timings or visual acceptance.

`tools/capture-ultimates.gd` and `tools/run-ultimate-capture.py` capture fourteen individually staged actual Forward+ warning/motif images, three mode/overlap images, and 120 consecutive 1280×720 frames at a simulated 30 fps with 60 Hz physics. The four-second sequence includes Rama preparation, release, indexed scripted contacts and expiry, plus Sita onset and sustain. Sita is explicitly cancelled at 3.8 seconds to end the fixture; its six-second lifecycle is not falsely claimed as fully captured. The report pins runtime sources, imported hero proof, real rendering counters and event phases. The video is silent and scripted presentation, not gameplay authority evidence or realtime performance. Separate actual-world tests own accepted troop outcomes.

The source-pinned actual-image packet is accepted for bounded geometric studies at `docs/evidence/mythic-ultimates-render-r3/ULTIMATE-RENDER-REVIEW.md`. It retains all fourteen motif stills, three mode views and a four-second representative video; sparse surfaces, thin distant boundaries, Ulupi's ring-like reading and the shared Karna/Bhima facet family remain explicit art limits. Passing headless checks does not establish smooth continuous choreography for all fourteen motifs, combat legibility in a crowded match, accessibility with human players, production art, online synchronization or physical-GPU performance.

The prior accepted `mythic-ultimates-render-r1` packet is historical pre-HUD evidence. The current r2 archive refreshes all source pins after the world HUD correction; every image/video byte matches the prior study. The studio itself does not exercise the world HUD, whose behavior is verified separately through packaged input review.
