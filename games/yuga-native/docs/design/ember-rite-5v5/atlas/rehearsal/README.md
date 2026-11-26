# Ember Rite atlas rehearsal

Open [the standalone rehearsal](../rehearsal.html) to walk Mandala Rift, Lanka, Ayodhya or Kurukshetra. The SVG plan, collision geometry, district landmark art, route estimates and simulation are embedded in one file. It also runs in the packaged game's sandboxed practice frame. The solo drill rehearses where and when an objective can be completed. The native and multiplayer arenas have separate geometry.

## Practice

- Choose **Explore**, a start room and a destination to compare dry routes with routes that allow water and folds. The marked itinerary begins at the chosen room. Walk freely or use **Follow marker** to inspect corners.
- Choose **Carry and kindle**. Carry the Ember to either site and hold Interact inside its 3 m disk for four seconds. The vessel stays at the precise place you finish. **Rehearse this retake** starts you at the opposite site and keeps that placement.
- Choose **Quench** to rehearse a defender opening directly. Its practice vessel sits 2 m north of the selected site centre. Move within 1.5 m of it and hold for 3.5 seconds before the 40-second burn ends.
- At a purple diamond, read the named destination and waymark. Stand still and hold for 1.5 seconds to cross. The fold preserves the runner's local offset and turns the facing with the map. On return, it reverses the turn. Each temple also has an ordinary walking route.
- Focus the plan for WASD or arrow movement. Hold **E** to interact, **G** to drop the vessel and **P** to pause. The on-screen direction pad and Interact button accept touch, mouse and keyboard activation. Losing window focus or changing district clears held controls. Resume manually after returning to a running drill.

Use `?map=kurukshetra&exercise=retake&site=b` to link a district and exercise. Supported districts are `mandala`, `lanka`, `ayodhya` and `kurukshetra`. Exercises are `explore`, `carry` and `retake`. The sole objective-site values are `a` and `b`.

## Build and verify

Run these commands from this directory.

```sh
python3 build.py
python3 build.py --check
node --test simulation.test.mjs
node browser.test.mjs
```

The builder uses Python's standard library and [the atlas audit](../audit.py) to embed [the four map sources](../maps/) and [Rust's ritual constants](../../../../../../yuga-rust/src/ritual.rs). Change authored rooms, fixed cover, water, bypasses, fold transit or cues in the map JSON. Change authoritative channel times in Rust. Rebuild and rerun the checks after either changes. The small landmark sheet derives from [the game's four district concepts](../../../../../art/ember-rite-5v5/district-landmarks.png).

The desktop browser test uses the repository's Playwright dependency and Chromium selection. It tries the local file and records when a managed browser requires the one-response loopback fallback. It then exercises the page offline and checks the same bytes inside a scripts-only frame. A separate 375 px touch viewport tests short presses and the district deep link. Screenshots go to the system temporary directory.

## Simulation boundary

Movement runs at 20 Hz, with a 0.45 m radius, 5 m/s dry walking and 85% speed in water. The disk must fit on an authored rectangular room or swept corridor, including bends. Joins are conservative near outside corners. Low and high fixed cover both obstruct the walking disk. Each registered building uses the same [parametric mesh source as the Blender exports](../massing/architecture.py). The builder intersects its convex parts with a band 0.025 to 1.7 m above the local sill and projects that silhouette onto the plan. Nested mouldings share their outer footprint. The rendered masonry polygons are the obstacles tested by the moving disk. Beams above that band leave passages open. At Ayodhya the side basins use the water speed and the central causeway remains dry. This top-down study does not simulate step descent, head clearance or camera sweep. Elevation is marked on the plan; ramps use their projected horizontal footprint for steering. Route estimates come from the atlas graph; human steering, corners, interrupted holds and placement can change the observed time. Local checks cover all sixteen dry spawn-to-site walks, both signed fold round trips, map bounds, fixed cover, drops and recovery, eight distinct off-centre kindles and retakes, centre and shoulder crossings in both directions through all four buildings, eighteen ordinary approaches in both directions combined, and completion on the last eligible clock tick. Competitive balance and player readability require the separate ten-player encounters.
