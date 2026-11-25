# Route measurements

A map author can repeat these calculations from the checked-in drawings. Times give centre-to-centre travel along route lines at full walking input. They estimate the time budget for deploying, rotating or faking an approach. First sight of an opponent depends on the camera and cover.

- Dry travel includes walking and ramps at 5 m/s. Hanuman uses this rate in the Rust simulation. Rama advances 0.25 m per 20 Hz tick at full input. [Hanuman movement](../../../../../yuga-rust/src/combat.rs) · [Rama movement](../../../../../yuga-rust/src/rama.rs)
- Distances include every authored bend. Between room centres the model assumes a constant grade over the whole route. On each shallow-water link it applies 85% walk speed for the centre-to-centre distance, assuming a wade at every depth. The drawings show level room floors and dry thresholds. An engine blockout will have shorter sloped and submerged portions. Each fold consumes 1.5 s in either direction. Walking approaches to both mouths still count.
- Each of the four spawn-to-site openings on each map has two internally room-disjoint dry paths even with the other spawn and objective closed. Site rotations exclude both spawns. The Mid rows exclude both sites and the opposing spawn. Spawns denote the attacking and defending roles after each side swap. The alternative opening closes every interior room on the fastest dry path and measures the quickest remaining path.
- The 3 m ignition disk and 1.5 m perimeter apron fit within each site room and clear fixed cover. The 4.5 m radius is a level-design clearance target. The Rust experiment puts the vessel at the actual ignition point and tests 1.5 m quench reach. [Round rules](../ROUND_AND_TECH.md) · [Rust interaction](../../../../../yuga-rust/src/ritual.rs)
- The floor check uses room rectangles and swept corridor widths in plan. It samples cover footprints on a 3 × 3 grid, checks physical route centrelines against solid footprints and checks probe endpoints against floor and cover. Water depth, ceilings, slopes at thresholds, corridor overlap, agent radius, visibility and camera clearance need an engine blockout.

The measurements below assume immediate movement, uninterrupted channels and an empty map. Check the marked probes from both shoulders at ground and elevated eye heights. A clear line in plan may still be hidden by a lintel or floor edge. A low screen intersected in plan may hide the caster's feet while exposing the head. Use screenshots from both ends and check a real ray from eye to target and eye to reticle.

From the repository root run `python3 games/yuga-native/docs/design/ember-rite-5v5/atlas/audit.py --check`. Omit `--check` to write the report after an edit.

## Mandala Rift

[Drawing inputs](maps/mandala.json) · [Encounter notes](maps/mandala.md)

15 rooms and 26 bidirectional links. Dry corridors span 5–8 m in width. Authored floor elevations run from -0.3 to 2.4 m.

| Run | Dry (s) | All links (s) | Fastest dry callouts |
| --- | ---: | ---: | --- |
| Attack → A | 26.6 | 26.6 | Spice Gate → South Temple → Ghat Mandapa |
| Attack → B | 31.5 | 28.3 | Spice Gate → South Temple → Sluice → Bazaar Sanctuary |
| Attack → Mid | 25.4 | 25.4 | Spice Gate → South Temple → Sluice |
| Defend → A | 24.8 | 24.8 | Water Gate → North Temple → Ghat Mandapa |
| Defend → B | 29.2 | 26.4 | Water Gate → North Temple → Sluice → Bazaar Sanctuary |
| Defend → Mid | 23.0 | 23.0 | Water Gate → North Temple → Sluice |
| A → B | 11.4 | 11.4 | Ghat Mandapa → Sluice → Bazaar Sanctuary |

After ignition, a defender starting at the opposite site centre has **25.1 s** in the model for reaction, fighting and positioning after reserving the fastest dry rotation and a 3.5 s quench. The carried vessel can be kindled away from the room centre.

| Opening with the fastest dry line closed | Time (s) | Alternative dry callouts |
| --- | ---: | --- |
| Attack → A | 36.9 | Spice Gate → Reed Steps → Dry Bank → Ghat Mandapa |
| Attack → B | 33.6 | Spice Gate → Cloth Yard → South Pyramid → Bazaar Sanctuary |
| Defend → A | 35.4 | Water Gate → Jar Steps → Dry Bank → Ghat Mandapa |
| Defend → B | 32.4 | Water Gate → Scale Yard → North Pyramid → Bazaar Sanctuary |

Fastest runs that use a special crossing

- Attack → B via Spice Gate → South Temple → South Pyramid (fold) → Bazaar Sanctuary saves 3.2 s.
- Defend → B via Water Gate → North Temple → North Pyramid (fold) → Bazaar Sanctuary saves 2.8 s.

| Optional crossing | Kind | Crossing (s) | Fastest dry detour (s) |
| --- | --- | ---: | ---: |
| South Temple ↔ South Pyramid | fold | 1.5 | 7.3 |
| North Temple ↔ North Pyramid | fold | 1.5 | 7.3 |
| Dry Bank ↔ Jar Steps | water | 16.4 | 11.1 |
| Dry Bank ↔ Reed Steps | water | 16.4 | 11.1 |
| Jar Steps ↔ Reed Steps | water | 21.1 | 22.3 |

| Shoulder-camera probe | Length in plan (m) | Fixed cover intersected in plan |
| --- | ---: | --- |
| Bell screen check | 16.0 | Bell screen |
| Market near lip | 11.0 | None |

## Lanka

[Drawing inputs](maps/lanka.json) · [Encounter notes](maps/lanka.md)

13 rooms and 18 bidirectional links. Dry corridors span 6–7 m in width. Authored floor elevations run from 0 to 6 m.

| Run | Dry (s) | All links (s) | Fastest dry callouts |
| --- | ---: | ---: | --- |
| Attack → A | 24.7 | 24.7 | Ferry Gate → Salt Ramp → Jetty Gate → Signal Court |
| Attack → B | 18.9 | 18.9 | Ferry Gate → Slipway → Ashoka Garden |
| Attack → Mid | 16.6 | 16.6 | Ferry Gate → Chain Foot → Wind Arch |
| Defend → A | 19.8 | 19.8 | Upland Gate → Crown Gate → Signal Court |
| Defend → B | 21.7 | 21.7 | Upland Gate → Garden Wall → Ashoka Garden |
| Defend → Mid | 14.3 | 14.3 | Upland Gate → Bell Pier → Wind Arch |
| A → B | 21.9 | 21.9 | Signal Court → Wind Arch → Fruit Stalls → Ashoka Garden |

After ignition, a defender starting at the opposite site centre has **14.6 s** in the model for reaction, fighting and positioning after reserving the fastest dry rotation and a 3.5 s quench. The carried vessel can be kindled away from the room centre.

| Opening with the fastest dry line closed | Time (s) | Alternative dry callouts |
| --- | ---: | --- |
| Attack → A | 26.9 | Ferry Gate → Chain Foot → Wind Arch → Signal Court |
| Attack → B | 28.3 | Ferry Gate → Chain Foot → Wind Arch → Fruit Stalls → Ashoka Garden |
| Defend → A | 24.5 | Upland Gate → Bell Pier → Wind Arch → Signal Court |
| Defend → B | 25.9 | Upland Gate → Bell Pier → Wind Arch → Fruit Stalls → Ashoka Garden |

| Shoulder-camera probe | Length in plan (m) | Fixed cover intersected in plan |
| --- | ---: | --- |
| Deck crossing | 23.0 | None |
| Garden entry | 15.0 | None |

## Ayodhya

[Drawing inputs](maps/ayodhya.json) · [Encounter notes](maps/ayodhya.md)

12 rooms and 19 bidirectional links. Dry corridors span 6–7 m in width. Authored floor elevations run from 0 to 4 m.

| Run | Dry (s) | All links (s) | Fastest dry callouts |
| --- | ---: | ---: | --- |
| Attack → A | 23.3 | 23.3 | Cart Gate → Lamp Lane → Assembly Court |
| Attack → B | 17.9 | 17.9 | Cart Gate → Potters Bend → Ferry Quay |
| Attack → Mid | 24.3 | 24.3 | Cart Gate → Potters Bend → Weigh House → Ledger Court |
| Defend → A | 24.2 | 24.2 | Archive Gate → Cloth Gate → Assembly Court |
| Defend → B | 19.0 | 19.0 | Archive Gate → Gauge Steps → Ferry Quay |
| Defend → Mid | 23.3 | 23.3 | Archive Gate → Gauge Steps → Sluice Gate → Ledger Court |
| A → B | 28.0 | 24.5 | Assembly Court → Ledger Court → Sluice Gate → Wash Steps → Ferry Quay |

After ignition, a defender starting at the opposite site centre has **8.5 s** in the model for reaction, fighting and positioning after reserving the fastest dry rotation and a 3.5 s quench. The carried vessel can be kindled away from the room centre.

| Opening with the fastest dry line closed | Time (s) | Alternative dry callouts |
| --- | ---: | --- |
| Attack → A | 33.2 | Cart Gate → Potters Bend → Weigh House → Ledger Court → Assembly Court |
| Attack → B | 36.2 | Cart Gate → Lamp Lane → Weigh House → Wash Steps → Ferry Quay |
| Defend → A | 32.2 | Archive Gate → Gauge Steps → Sluice Gate → Ledger Court → Assembly Court |
| Defend → B | 32.4 | Archive Gate → Cloth Gate → Sluice Gate → Wash Steps → Ferry Quay |

Fastest runs that use a special crossing

- A → B via Assembly Court → Ledger Court → Wash Steps (water) → Ferry Quay saves 3.5 s.

| Optional crossing | Kind | Crossing (s) | Fastest dry detour (s) |
| --- | --- | ---: | ---: |
| Ledger Court ↔ Wash Steps | water | 8.6 | 12.1 |

| Shoulder-camera probe | Length in plan (m) | Fixed cover intersected in plan |
| --- | ---: | --- |
| Gauge descent | 19.0 | None |
| Wash exit | 6.0 | None |

## Kurukshetra

[Drawing inputs](maps/kurukshetra.json) · [Encounter notes](maps/kurukshetra.md)

15 rooms and 19 bidirectional links. Dry corridors span 5–7 m in width. Authored floor elevations run from 0 to 4 m.

| Run | Dry (s) | All links (s) | Fastest dry callouts |
| --- | ---: | ---: | --- |
| Attack → A | 22.8 | 22.8 | Cart Yard → Ox Gate → Stone Weir → Palace Terrace |
| Attack → B | 20.6 | 20.6 | Cart Yard → Furrow → Mill Sill → Wind Field |
| Attack → Mid | 13.2 | 13.2 | Cart Yard → Boat Yard → Gauge Bridge |
| Defend → A | 12.9 | 12.9 | Record Gate → Archive → Palace Terrace |
| Defend → B | 14.6 | 14.6 | Record Gate → Winnow Shed → Wind Field |
| Defend → Mid | 15.1 | 15.1 | Record Gate → Tally Steps → Gauge Bridge |
| A → B | 21.9 | 21.9 | Palace Terrace → Seal Porch → Gauge Bridge → Tally Steps → Wind Field |

After ignition, a defender starting at the opposite site centre has **14.6 s** in the model for reaction, fighting and positioning after reserving the fastest dry rotation and a 3.5 s quench. The carried vessel can be kindled away from the room centre.

| Opening with the fastest dry line closed | Time (s) | Alternative dry callouts |
| --- | ---: | --- |
| Attack → A | 23.7 | Cart Yard → Boat Yard → Gauge Bridge → Seal Porch → Palace Terrace |
| Attack → B | 24.6 | Cart Yard → Boat Yard → Gauge Bridge → Tally Steps → Wind Field |
| Defend → A | 25.6 | Record Gate → Tally Steps → Gauge Bridge → Seal Porch → Palace Terrace |
| Defend → B | 16.1 | Record Gate → Tally Steps → Wind Field |

| Optional crossing | Kind | Crossing (s) | Fastest dry detour (s) |
| --- | --- | ---: | ---: |
| Wind Field ↔ Reed Lip | water | 8.3 | 20.4 |

| Shoulder-camera probe | Length in plan (m) | Fixed cover intersected in plan |
| --- | ---: | --- |
| Porch reveal | 20.2 | Ledger Screen |
| Sill to ring | 23.1 | None |
