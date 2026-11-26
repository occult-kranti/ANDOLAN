# Ember Rite map atlas

**Mandala Rift art book.** All 15 rooms and 26 connections have individual paintings, measured sections and Blender camera studies. The library also covers the six pieces of cover, three landmarks, two vessels and the pavilion down to its 62 building parts. [Browse the map art](https://occult-kranti.github.io/ANDOLAN/production/mandala-art/) · [Editable assets and production handoff](../../../../art/mandala-map-studio/README.md)

In a five-against-five round, one team carries the Ember toward either sanctum. Choosing the other site is costly once the vessel catches. A defender has forty seconds to cross the district, find the vessel where it was placed, and complete a 3.5-second pour. Use the solo rehearsal to learn those routes and the atlas to stage the first ten-player tests. [Play the four maps](https://occult-kranti.github.io/ANDOLAN/production/ember-rite/rehearsal.html) · [Round rules](../ROUND_AND_TECH.md) · [Ten-player encounter script](ENCOUNTERS.md)

**Open the 12-page atlas** for a north-up plan, an encounter sheet and a dimensioned architectural study for each district. The studies include signed fold turns, threshold coordinates, scale and a route strip. The two GLBs for each district share an origin. Import them together to see the architectural study in its intended room, or load the floors alone to inspect a route. [Printable PDF](blueprints/yuga-map-atlas.pdf) · [Source and editorial decisions](RESEARCH_ROUNDS.md) · [Three-round handoff and next milestones](PANEL_ROADMAP.md)

| District and its main decision | Plans and geometry |
| --- | --- |
| **Mandala Rift.** A carrier can take a dry bank, show a crossing in the ford, or announce a quarter-turn fold between a temple and pyramid. The pitched silhouette above South Pyramid identifies the southern exit. | [District](maps/mandala.md) · [Floorplan](blueprints/mandala.svg) · [Encounters](blueprints/mandala-encounters.svg) · [Quarter-turn Pavilion](blueprints/mandala-architecture.svg) · [Floors](massing/mandala.glb) · [Architecture](massing/mandala-architecture.glb) |
| **Lanka.** Wind Arch is faster. Rain Gallery and the sheltered salt road let a defender rotate if the arch is held. Repeated column bays give the crossing a countable callout. | [District](maps/lanka.md) · [Floorplan](blueprints/lanka.svg) · [Encounters](blueprints/lanka-encounters.svg) · [Rain Gallery](blueprints/lanka-architecture.svg) · [Floors](massing/lanka.glb) · [Architecture](massing/lanka-architecture.glb) |
| **Ayodhya.** Take the audible water shortcut toward Ferry Quay or use the dry causeway between stepped water gauges. The footway stays level even as the well terraces descend. | [District](maps/ayodhya.md) · [Floorplan](blueprints/ayodhya.svg) · [Encounters](blueprints/ayodhya-encounters.svg) · [Measure Well](blueprints/ayodhya-architecture.svg) · [Floors](massing/ayodhya.glb) · [Architecture](massing/ayodhya-architecture.glb) |
| **Kurukshetra.** Gauge Bridge keeps either site in reach. The extra turn at Register Gate gives the palace team less setup time. Flood Bench connects the two banks when mid and both spawns are closed. | [District](maps/kurukshetra.md) · [Floorplan](blueprints/kurukshetra.svg) · [Encounters](blueprints/kurukshetra-encounters.svg) · [Register Gate](blueprints/kurukshetra-architecture.svg) · [Floors](massing/kurukshetra.glb) · [Architecture](massing/kurukshetra-architecture.glb) |

![Four architectural maquettes showing the pavilion, gallery, well and gate at their designed proportions](massing/architecture-overview.jpg)

[View the four floor models together](massing/overview.jpg) · [Imported dimensions, approaches and passage checks](massing/architecture-checks.md)

## Read a sheet and play the route

North is positive Z in the authoring plan. AT and DF are the duty spawns, M is contested mid, and A and B are the two 3 m kindle disks. The dotted 4.5 m perimeter includes clearance for a teammate reaching a vessel placed at the edge. Each enlarged view carries its own scale. Dashed connections joining fold mouths represent one transition. The exit bearing changes by a signed quarter-turn and reverses on the return trip. Ordinary routes remain available.

Choose a district and a duty in the browser rehearsal. Use the route guide to practice an opening, leave the vessel at a particular lip and recover it, or play the defender's retake against the clock. The drill projects the registered masonry at walking height. The pavilion wings, eight gallery columns, gate plinths and well parapets block the marker. The two well basins slow a crossing while the central sill remains dry. The private multiplayer release runs Hanuman and Rama in the Confluence knockout arena. Its title screen and the extracted file `ember-rite.html` both open this separate solo drill. [Game and controls](../../../../../yuga-rust/README.md) · [Desktop and phone captures](evidence/README.md) · [Balance measurements](BALANCE_MATH.md) · [Player research and revisions](PANEL_ROADMAP.md)

## Authoring and verification

The [four JSON plans](maps/) own room coordinates, floors, cover, fold transitions and architectural registration. Edit the map and its district brief together. Run the following in this directory. Each mesh imports into Blender at the shared origin. Ground axes (X, Z) in the plan correspond to Blender (X, Y), with Z up. The glTF export has X east, Y up and negative Z north.

```sh
python3 audit.py
python3 balance.py
python3 rehearsal/build.py
python3 draw.py --pdf
blender -b --factory-startup -t 1 --python-exit-code 1 --python massing.py
blender -b --factory-startup -t 1 --python-exit-code 1 --python massing.py -- --check
blender -b --factory-startup -t 1 --python-exit-code 1 --python probe_massing.py
python3 audit.py --check
python3 balance.py --check
python3 test_balance.py
python3 rehearsal/build.py --check
```

The route audit tests 16 pairs of independently reachable dry entrances and four dry rotations. The balance analysis checks the actual distance between door thresholds against the live 6 m Sena diameter, and how much time a defender has after one interrupted pour. Blender samples exported floors and cover at three sightline heights. Real hero shoulder cameras, on-device frame times and human drafts have their own production gate. [Travel results](measurements.md) · [Balance math](BALANCE_MATH.md) · [Blender sightlines](massing/sightlines.md) · [Ability changes](../HERO_BALANCE.md)

## First build and acceptance gates

| Order | Owner and deliverable | Decision before proceeding |
| --- | --- | --- |
| 1 | **World and collision.** Bring Mandala’s ordinary routes, dry bank, site floors and selected solids into an isolated playable blockout with Rama and Hanuman. Add room returns, ceilings and capsule collision. | Walk both alternatives to each site. Plant at the centre and each compass edge, recover a drop and reach a quench from each entrance. Check that a shoulder peek or floor below cannot operate the vessel. Keep folds closed for this pass. |
| 2 | **Combat and network.** Connect the tested Rust round rules to authoritative movement, held interact, damage, legal floors and a ten-seat round. Add captions, interruption, side swap and reset. | Rehearse the Mandala branch with an interrupted carrier, a fake quench and a disconnect. Match event order on two rendered clients. Check which players can hear or caption a fold. |
| 3 | **Environment art and accessibility.** Place a single skyline landmark and a quiet hero-height backdrop for each flagship site. Add the local fold and ford cues after the baseline dry paths pass. | Repeat both shoulder views at dusk, in grayscale, with muted audio and reduced effects. Ask first-time players to call the landmark and find the marked site. A false door, visible hidden carrier or missing dry route returns to the designer. |
| 4 | **Encounter and playtest.** Compare the two entries, exact vessel placements and site-dependent retakes on one Mandala revision in the proposed 48-round test. | Record choices and reasons by team and side. Revise a dominant perch or unused entrance. Promote the next map only when both sites support a contested human retake. [Sampling and rejection criteria](ENCOUNTERS.md#playtest-sequence) |
