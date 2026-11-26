# Mandala movement and timing study

At Ghat Mandapa a defender who takes the legal forward boundary reaches the ritual centre in 10.27 seconds after release. An attacker on the corresponding dry line takes 11.10. At Bazaar that lead is 1.44 seconds on dry ground, shrinking to 0.98 if both sides choose their audible folded thresholds. A team can use preparation to reach a roof or to line up close to the boundary. Those starts produce different first engagements. [Measured paths, curves and event timestamps](physics.json)

The study runs locally at 20 Hz over the registered Mandala floor. Coordinates below give east, north and elevation in metres. A is Ghat Mandapa at (0, 0, 0) and B is Bazaar Sanctuary at (40, 0, 0). The bell screen identifies A. The dye cabinet and weighbeam identify B. The fieldbook pairs a plan view of the trajectory with an elevation profile. [Site and movement fieldbook](fieldbook.html) · [District registration](../maps/mandala.json)

## Preparation and release

The earlier round brief reserved ten seconds to plan. With ten seconds of free walking neither duty can reach its forward ladder and finish climbing. Twenty seconds permits all ten seats to choose a rehearsal kit and move, including the 17.70-second Cloth Yard climb and the 16.60-second Scale Yard climb. Kit selection here has no price or permanent effect. A 20-second buy window is a design proposal for the 5v5 round. The existing Rust ritual clock starts at approach. [Round specification](../../ROUND_AND_TECH.md) · [Authoritative ritual experiment](../../../../../../yuga-rust/src/ritual.rs)

| Window | Walk, climb, kit and sight rules |
|---|---|
| Preparation, ticks 0–399 | Walk up to 0.25 m per tick on dry floor or 0.2125 m in the ford. Use the assigned duty's ladder. Friendlies receive each other's verified setup positions. Enemy purchases, markers, sight probes, effects and coordinates stay private. |
| South attacker limit | A body of radius 0.45 m can approach the plane at north −40 m until its centre reaches −40.45 m. |
| North defender limit | The same radius stops the centre at +40.45 m before the plane at +40 m. Both planes extend through the entire air column. |
| Opening, tick 400 | The barrier drops and each player keeps the validated position. A button held during preparation needs a release and fresh press for wind, a shot, a fold or a rite. Movement continues and kit changes close. |
| Side change | Duty owns the space. Sun attacks rounds 1–12 and Moon attacks 13–24. At 12–12 the first overtime attack goes to Sun and changes each round, with the existing three-pair draw rule. Create fresh round state and clear per-seat input, projectiles, reservations and channels. |

The study exposes only friendly positions to a preparation observer. Publishing isolated enemy obstacles or draw calls can still give away setups in a client that receives every position. A multiplayer adapter has to filter network snapshots, sound, carrier markers and spectator feeds before delivery. Riot documents how shifting map barriers changed territory control and separately describes a specific buy-phase ability exception. Those sources inform the release tests. The 20-second duration and Mandala coordinates come from this study. [Riot map barrier changes](https://playvalorant.com/en-us/news/game-updates/valorant-patch-notes-0-50/) · [Riot buy-phase exception](https://playvalorant.com/en-us/news/game-updates/valorant-patch-notes-1-07/)

### Opening pressure

Times end at the site centre and exclude combat, purchases, objectives and input latency. The dry route follows real room centres, bends and slope lengths at the surveyed movement speed. A legal pre-release stride ends on the radius-adjusted boundary. The fold column allows the 1.50-second channel after release. A defending setup reaches the boundary in 14.55 seconds and an attacking setup in 15.49. Players can spend the remaining preparation time checking a kit or choosing a different route.

| Duty and site | From spawn, dry | After 10 s setup, dry | After 20 s setup, dry | After 20 s, folds allowed |
|---|---:|---:|---:|---:|
| Attack A | 26.59 s | 16.59 s | 11.10 s | 11.10 s |
| Defend A | 24.82 s | 14.82 s | 10.27 s | 10.27 s |
| Attack B | 31.51 s | 21.51 s | 16.02 s | 12.83 s |
| Defend B | 29.13 s | 19.13 s | 14.58 s | 11.85 s |

The attacker's measured boundary position is (3.000, −40.450, 0). The defender's is (8.521, +40.450, 0). Both branches reach their local temple first. From there A has a dry approach. B has a dry route over Sluice or a shorter fold into the pyramid. If a player waits at the exit, the fold can fail and the dry bypass still works. An uninterrupted kindle adds 4.00 s to arrival. These timings provide a playtest question about the first contest and do not predict a team's win rate. [Per-duty waypoints and alternatives](physics.json) · [Measured centreline method](../audit.py)

### Four climbable starts

These four proposed platforms have registered positions inside existing rooms. They are represented by 0.20 m solid decks with an open underside, a west ladder, a usable top and an east drop. The route starts only within 0.35 m of the marked foot. Each tick checks the climber and the occupied mount. On release, walk to within 0.36 m of the marked east edge, step clear and descend under gravity. Another actor cannot serve as a step, take the reserved ladder or share the landing. Hard site cover and temple roofs are excluded from the climb registry.

| Duty · room and loft | Top centre (east, north, up) | Top dimensions | Ascent / descent | Spawn to upper entry | Release from top to A / B |
|---|---|---:|---:|---:|---:|
| Attack · Spice Gate | (5.2, −114.5, 2.4) | 3.2 × 3.2 m | 1.40 / 1.00 s | 2.20 s | 29.54 / 34.46 s |
| Attack · Cloth Yard | (52, −69.2, 3.2) | 4.2 × 3.6 m | 1.75 / 1.10 s | 17.70 s | 27.92 / 20.81 s |
| Defence · Water Gate | (−5.2, 114.5, 2.4) | 3.2 × 3.2 m | 1.40 / 1.00 s | 3.00 s | 26.98 / 31.28 s |
| Defence · Scale Yard | (52, 69.2, 3.2) | 4.2 × 3.6 m | 1.75 / 1.10 s | 16.60 s | 27.92 / 20.66 s |

The last column starts at the upper ladder entry and follows the east drop, rejoins the native room centre and uses ordinary dry lanes. A defender choosing Scale can watch the eastern court and arrive at B about six seconds later than a defender taking the fastest dry boundary opening. Each JSON pad records foot, upper entry, top edge, egress, route nodes and elapsed tick counts for reproduction. [Editable setup pads and tests](physics.py)

## Flight, visibility and interactions

Maruti Ribbon starts on the surveyed floor or a registered deck. Steer horizontally at up to 5 m/s, ascend at 4 m/s, spend at most 12 m of horizontal path in 48 ticks and rise up to 4 m above the launch support. Reversing still spends distance. Releasing thrust starts the gravity phase at 9.8 m/s². A new charge requires a supported landing and a 16 s cooldown measured from launch. The existing Maruti Udayana and Sena numbers stay in their respective game assets. [Hero profile and geometry](heroes.json) · [Hero ability detail](hero-abilities.md)

- **Open site.** Both court trajectories start 3 m south of the ritual centre. Wind covers 6 m while rising, reaches 4 m, then touches down on tick 42 (2.10 s). A player can fly over the ritual disk. A channel can start only after the feet and movement mode are grounded.
- **Pavilion.** The actual first stone cornice has a 4.23 m soffit. The 1.80 m upright capsule stops with its feet at 2.4298 m. The crown also blocks an upward arrow. A flat ray around a pillar and ascent beneath a lintel can produce different outcomes.
- **Landing.** The floor comes from the GLB triangles under each footprint. A marked pad also supports landing. If a descending capsule meets an unlandable prop or a newly occupied floor, the solo drill returns to the latest safe ground projected along the flown route. If that ground is occupied as well, it withholds landing and retries. A production controller needs a visible slide or recovery animation for this case.
- **Fold.** Hold for 30 stationary, grounded ticks. South turns one quarter clockwise toward the pyramid and north turns one quarter counterclockwise. Return negates the angle and rotates the entry offset. An occupied exit cancels the attempt. Releasing the control arms a fresh crossing. A projectile hitting the threshold face stops. A projectile physically passing above a face follows its ordinary world-space direction.

The two-site sight study casts nine zero-radius rays per posture, three heights across three shoulder offsets. All **252 ground and reciprocal rays** first hit the nominated cover. Lifting the observer eye by 4 m exposes **29 of 126** samples. From the genuinely raised Sluice observer, Bazaar's Market register exposes six of nine and Measure post one. A smooth spectator camera or an unclipped effect cannot substitute for a body or muzzle query. [Independent counts and source hashes](physics.json) · [Architect's pockets, peeks and walk paths](architecture.json)

## Casts and counters

The survey uses a finite spherical projectile and an upright receiver capsule. Each simulation segment is swept against hard cover, current terrain and moving targets. Rounded box corners and time-of-impact sort order matter. At a simultaneous contact, hard geometry wins, then stable target ID breaks an actor tie. Thin fast shots cannot step through a solid frame. Signed aim includes elevation. Climbing consumes some horizontal range because the arrow or disc has a fixed three-dimensional travel budget. Soft rushes and twine permit passage.

| Shot | Release origin and clock | Distance and collision | Registered outcome |
|---|---|---|---|
| Rama · Kodanda | 1.56093 m socket, release at tick 4 | 40 m at 60 m/s, radius 0.22 m, 28 contact | From either apron the opposing target is reached on tick 6. A bell screen or dye cabinet stops the low shot on tick 5. |
| Arjuna · Gandiva Line | 1.50 m ordinary origin, release at tick 8 | 30 m at 48 m/s, radius 0.18 m, 32 contact | An elevated 2.15 m release clears the 1.55 m trace table and 1.54 m bale bench, making contact on tick 11. The 2.60 m bell screen and dye cabinet require a higher arc. |
| Krishna · Sudarshana Return | 1.35 m socket, release at tick 5 | 12 m at 16 m/s out, 20 m/s back, radius 0.25 m, one 30 contact per recipient per cast | On both sites a shield intercepts tick 10, the disc turns at tick 20, a laterally moving enemy crosses on tick 24 and the disc returns to its recorded socket on tick 32. Reading both legs never pays for the same target twice. |

A new temporary screen in the Ghat study sits beyond the 4.5 m protected apron. The disc passes through its future location on the outward leg. The screen appears after the turn and stops the return on tick 23. The low disc also ends at tick 7 when it meets either the trace table or the bale bench. The ordinary Krishna primary and native Rama plane remain their existing game implementations. The pitched Rama volume, Arjuna shot and dedicated returning disc here are executable study cases. [Numeric hero contracts](heroes.json) · [Native Rama kit](../../../../../assets/design/rama-ability-kit.json)

Two allies can combine cover, ascent and support. An ally can body-block without adding height to another player's capsule. A shield consumes the disc's single receiver contact even if an incoming return would otherwise touch the same target. Simultaneous Vanara Sena heals follow the Rust settlement order. Positive opposing damage or a knockout settles first. Two eligible +12 heals directed at a surviving ally missing four HP receive two HP of credit each. A wall blocks the support ray, full-health allies receive zero and a lethal hit cannot be reversed by that tick's heal. [Rust simultaneous-effect test](../../../../../../yuga-rust/src/battle.rs)

### Ritual reach at an edge

Kindle while grounded within the 3 m disk for 80 ticks. Quench within 1.5 m of the **placed vessel** for 70 ticks. This permits a defender outside the disk to quench a vessel near its edge. A vessel 2.80 m east of A or B is reachable by a defender 4.20 m east and is out of reach from the centre. Positive damage, leaving valid ground, releasing the control or changing operator restarts the relevant channel. Two defenders holding together progress one tick at a time. The 100 s approach and 40 s post-kindle burn clocks, elimination precedence and winning team remain the Rust experiment's responsibility. [Existing ritual rules](../../../../../../yuga-rust/src/ritual.rs) · [Reference ground and handoff regressions](test_physics.py)

## Reproduction and integration

From this directory run the following commands.

```sh
python3 physics.py --check
python3 -m unittest discover -s . -p test_physics.py -v
```

Use `python3 physics.py` to regenerate the fixed-tick trajectories, cast receipts, 14 shelter comparisons, four elevated starts and four timed openings after changing the registered map, geometry or heroes. The standard-library implementation reads the floor triangles already used by the art studio. It uses conservative axis-aligned bounds for each piece of the pavilion, analytic swept spheres and capsules against each box, and a sampled projectile-floor check at maximum 0.10 m intervals with a bracketed refinement. It does not claim pixel-level sight or full-mesh collision on curved ornament. [Floor reader](../../../../../art/mandala-map-studio/src/catalog.py) · [Box2D shape casts and time of impact](https://box2d.org/documentation/md_collision.html) · [Fixed-step timing](https://gafferongames.com/post/fix_your_timestep/)

The generated fieldbook can replay these traces. The private 5v5 runtime, full remote rendering, purchase economy, camera collision, matchmaking and controller-feel playtests require separate integration. To port, use the fixed-step input after authoritative movement, retain the live paid charges and ability priorities, validate each candidate cast and objective observation against the registered world, then feed the trusted feet, damage and interaction observations to the existing ritual reducer. Verify latency, loss, reconnection, player visibility, input release, both duties and each of the four legal lofts before comparing competitive results. [Existing grounded room rehearsal](../rehearsal.html) · [Panel's encounter and human-test protocols](encounters.md)
