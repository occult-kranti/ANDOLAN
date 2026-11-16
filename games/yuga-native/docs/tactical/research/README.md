**Current visible-art correction:** root rejected the R1 actual map appearance.
The R2 source in `visual-r2-change-receipt.json` now adds metre-scale paving,
procedural sky/reflections/haze, contact SSAO, continuous facades, two overhead
galleries, eight awning stalls, twelve planted edges and four background
landmarks. It fixes reversed site labels and reduces barrier tint. Counts and
335 physics checks below describe the earlier layout checkpoint. The R2 pass
preserves site/route data and uses a focused actual-scene preflight only, per the
user’s priority for visible art. Root owns the next actual rendered decision.

# Sangam Crossing: original tactical map

Task YUGA-TACTICAL-CASUAL-13; native offline desktop; baseline
`7162b5d0b666e4422b0bc73100e1fba947d3323f`, dirty `work/yuga-studio` preserved.
World/evidence owner writes only tactical map source/data/tests, this research
packet and the map notice. Root owns integration, imports, visuals and exports.

The active design is the user-selected first-to-13, 5v5 tactical Casual game.
The previous Rama/Sangam MOBA-like practice remains a historical checkpoint.
This map does not create lane armies, relays, creep rewards, long-match cores or
flight routes. Round rules, weapons, abilities and bots belong to their owners.

## Implemented geometry and API

- 100×130 m enclosed arena: X[-50,50], Z[-65,65].
- A / Lotus Court: (-29,0,8); B / Indigo Yard: (29,0,8); site radius5 m.
- Attackers use South Court around Z=-54, defenders North Court around Z=54.
  Team names stay sun/moon when the attack role swaps. Five spawn slots are
  spaced3 m, with local index0 at the center.
- Two buy barriers at Z±44 are actual world-layer1 colliders for bodies and
  weapon rays. Their blue visual panels disappear when the collision opens.
- Four Sangam buildings frame main and middle routes; two divider walls split
  main from outer arcades. The central monument at(0,0,8) blocks direct shots
  between plant centers. A north rotation passes through(±6,0,15).
- Static site outlines/labels leave both centers clear for root's animated
  objective relic. Low cover at1.1 m and full-height cover have distinct shot
  behavior. Collision triangles are transformed into map space, so physics
  bodies do not inherit unsupported nonuniform scaling.
-17 immutable imported meshes use existing Sangam geometry/material inputs;
 287,076 reused triangles plus procedural boxes. Four central buildings are
 collision-bearing; six taller facade instances outside the walls provide
 skyline depth. No old asset bytes are changed. Source ledger lives in
 `assets/tactical/map.json`.

Public methods match `../CONTRACT.md`: spawn, route, callout, is_buy_zone,
set_buy_barriers and report. `route` includes the spawn as its first point and
returns explicit main/mid/flank waypoints selected by index modulo3. These are
spawn-to-site routes, not a general pathfinder from arbitrary current positions.
The combat owner currently uses a safe retrace when retargeting across sites;
that longer retake path remains a tactical AI limitation. The physical north
rotation is independently verified for human navigation.

The map owns one shadowed directional sun, one weak shadowless sky fill and
one environment. Root should not add a second environment. It reuses shared immutable meshes and private material
overrides; it does not claim draw-call batching or hardware optimization from
resource sharing alone.

## Primary research and concrete adaptation

[Riot’s beginner guide](https://playvalorant.com/en-gb/news/announcements/beginners-guide/)
explains pre-round purchases and attack/defend planting. YUGA's exact timers,
credits and firearm/ability rules come from the project contract. This source
does not replace the user’s chosen mode.

[Riot’s environment-art account](https://playvalorant.com/en-us/news/dev/the-art-of-valorant-map-environments/)
connects readable combat edges, collision, material values and elevated detail.
The Exa connector independently retrieved the official developer article.
We apply that guidance with real cover, restrained paving, short site names,
quiet materials, high eaves and skyline detail outside physical bounds. The
layout is original; no Riot map geometry, screenshots or textures are used.

[Valve’s August2023 CS2 announcement](https://store.steampowered.com/news/posts/?appgroupname=Valve&appids=730&enddate=1694127271&feed=steam_community_announcements)
is a historical primary reference for shorter round matches and12-round halves.
YUGA's first13 Casual/no-overtime rule is explicitly its own contract, not a
claim to reproduce current CS2 mode behavior or ranking.

[Blizzard’s Stadium development note](https://overwatch.blizzard.com/en-us/news/24230696/1/)
emphasizes readable ability language and understandable buying descriptions.
We reserve clear site cues, keep ornate detail away from the reticle floor and
leave actual usability/feel to later human playtests. See `primary-sources.json`
for source scope and access method; no new game assets or dependencies came
from these sources.

## Reused media evidence

Read the complete prior [reference ledger](../../research/hero-six-rounds/reference/README.md)
and [full-stream/audio addendum](../../research/hero-six-rounds/reference/full-stream/README.md).
Their source MP4 hashes remain `bed8ca9b...982bb` and `6ae05fe2...443c` in those
exact receipts. No139,216-frame decode or transcription was repeated here.
Prior coverage remains all139,216 frames machine-decoded,1,256 unique frames
personally inspected, and595 machine-transcript segments read; it is not a
claim of human watching/listening to every frame or all77 minutes of audio.

Specific carried-forward observations: gameplay01:10–01:27 connects cover with
an alternate approach;16:35–16:39 shows committed route access;29:40–29:42 shows
VFX crowding the aim region. Our FPS adaptation uses grounded main/flank paths,
actual line-of-sight cover and a quiet target floor. The earlier world’s flying
and elevated bow limitations are not inherited as tactical FPS mechanics.

## Actual checks and remaining gates

First implementation: `map-cases-r1.json` passed329 headless checks.
After the center sightline/divider correction, `map-cases-r2.json` passed335.
All40 team/attack-side/site route variants were checked with actual Godot
capsule sweeps: radius0.4 m, height1.8 m, margin0.01 m. Tests include spawn/site
clearance, floor contact, buy-barrier ray/body rejection and reopening, low/high
cover, direct plant-to-plant sightline blocking, north rotation, side swaps,
invalid/nonfinite queries and unchanged source hashes. These are physics checks,
not rendered image or hardware-performance acceptance.

```sh
XDG_DATA_HOME=/tmp/yuga-tactical-map-tests godot --headless --path games/yuga-native --script res://tests/tactical/map_cases.gd -- --report=/workspaces/ANDOLAN/games/yuga-native/docs/tactical/research/map-cases-r2.json
```

Route lengths span60.82–130.12 m because actor slots and flank commitments differ.
At an illustrative6 m/s that is10.1–21.7 s before combat or pauses; actual player
and bot movement speeds belong to root/combat and must be measured in play.
No human balance claim follows from route clearance. Current paths deliberately
trade longer outer flanks for fewer direct angles.

Unrun by this owner: new imports, actual FPS map renders, OS input, firearm/VFX
occlusion in this arena, target hardware profiling, online matches and human
balance/feel. Root serializes those next gates. No map is accepted visually from
this document or a top-down schematic alone.
