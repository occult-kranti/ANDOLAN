# Relay Foundry — original playable map study

A separate Blender-authored blockout for YUGA desktop map design, dated 15 November 2026. This is an exploration prototype with a scale capsule walker, not a finished combat map or a replacement for accepted Confluence authority. The foundry is an invented setting, not a reconstruction of historical architecture or a commercial game level.

## What was built

The 132 × 190 metre play space has three named lanes (Loom, Span, Kiln), four production halls, side rotation courts, low cover, mirrored sun/moon spawn and core landmarks, three relay landmarks and a six-metre elevated crossover. Two continuous wedge ramps connect the central lane to the crossover; both outer lanes pass below it. The side routes have distinct pillar/cover/chimney silhouettes. Relays are landmarks with no capture rules or rewards.

All geometry and eight flat PBR materials were authored by the checked-in Python builder using Blender primitives and its bundled text font. No external model, texture, add-on, game asset or proprietary data was used. Source/outputs are original project assets. The editable `.blend` includes the original camera and CPU render setup; the runtime GLB contains only meshes/materials.

Measured asset inventory: **163 mesh objects, 12,588 triangles, eight materials, 101 colliders**. These counts are not draw-call or hardware FPS measurements. Production art, minion navigation, sightline balance, combat, match rules and online authority are future work.

## Run and controls

From repository root after installing Godot 4.6.3:

```sh
godot --headless --editor --path games/yuga-native --import --quit
godot --path games/yuga-native --rendering-method gl_compatibility res://scenes/studio_map_study.tscn
```

WASD walks, Shift runs, Space jumps, held right mouse orbits the camera, O toggles the overview, R returns to sun spawn and Escape quits. The visible HUD states that this is a map study and that landmarks have no capture/combat authority. Default game menus and accepted worlds were not changed. The prototype does not load user settings or mutate Confluence saves.

## Rebuild and verify

```sh
blender4.3 --background --threads 8 --python tools/studio/build_relay_foundry.py
godot --headless --editor --path games/yuga-native --import --quit
godot --headless --path games/yuga-native res://scenes/studio_map_study.tscn -- --verify-map
```

The builder exports `assets/world/studio-relay-foundry.glb`, saves `relay-foundry.blend`, writes `manifest.json` and renders `blender-overview.png` with Cycles on CPU, 24 samples and eight threads. The manifest records geometry/material/collision budgets and source/output hashes. The preview was directly opened and shows the distinct routes, ramps, open underpasses and landmarks; it is a Blender render, not a native screenshot.

The native scene derives collision from the actual imported meshes: `COL_BOX_` creates a local mesh-AABB box; `COL_RAMP_` creates a convex wedge. Decorative paving, ticks and lettering remain nonblocking. The separate verification mode performs real physics queries and moves the actual capsule using the shared movement method.

**Nine of nine native checks passed**: collider/ramp inventory, deck hits in all three lanes at y=6, ground below the crossover, continuous capsule walk up/down the south ramp, jump input rising to 1.652 metres then landing, and perimeter collision. See `native-collision.json` and `native-physics.log`. The walker reached `(0,6.028,0.701)` on the deck and returned to `(0,0.017,39.871)` on the ground. This proves the scoped imported physics route, not every map route or multiplayer traversal.

The first Blender gate rejected its built-in Render Result buffer as an external image. The gate was corrected to reject file-backed external images, and all seven builder checks passed. `blender-first-rejected.log` preserves the failed run; `blender-build.log` records the corrected build/render. Review also found and corrected a jump velocity reset before adding the actual jump assertion. The final native verification binds the corrected script.

Actual native map-window screenshots and OS input are owned by the package/render worker and will be linked in the root studio report. No native art acceptance is inferred from the Blender still.

## Frozen identities

- `tools/studio/build_relay_foundry.py`: `a69881ff9e7a53f4ae130c603311881f1159c2ab1ed168ff68f7be6d599eb879`
- `games/yuga-native/scripts/studio_map_study.gd`: `c46cbc96cca9c500861b75a59ce61603135d0a51f0ba8403c679c49f0b1a10eb`
- `games/yuga-native/scenes/studio_map_study.tscn`: `cbc92deb63c3cd4cf352ffbd9a31f1002eb970e465beb571bd60aa943496aa86`
- `games/yuga-native/assets/world/studio-relay-foundry.glb`: `468448f03984fdaadc1be3563ed0ace75b3d635cc5c546bd321c364ae55e84cf`
- `games/yuga-native/art/studio-map/relay-foundry.blend`: `216224dd748a7e3be786f7d6abaa8780a941811e6239ffa43283a3446a5fc6c9`
- `games/yuga-native/art/studio-map/blender-overview.png`: `23a70da2e3b556d91477c32b37c8522e1b8b9dd9f70a4c39ef6805de6592d658`
