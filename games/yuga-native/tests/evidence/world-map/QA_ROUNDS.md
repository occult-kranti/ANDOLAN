# World map collision and route review

This package validates the flat native traversal scene and its relationship to the current TypeScript authority. It does not certify a full multiplayer match or finished art.

## Four completed rounds

1. **Contract inspection.** Read `shared/map.ts`, `shared/simulation.ts` and the world manifest independently. Identified the existing native player's 0.29 m capsule versus the authority's 0.65 m radius, and living objective circles missing from static-map data. The new world scene now adjusts its own player capsule to 0.65 m without changing the existing courtyard. The manifest explicitly records objectives as visual review anchors.
2. **Executed authority and navigation.** `world_map_cases.py` imports and executes the real TypeScript authority through the repository's installed `tsx`. The canonical revision 2 manifest matches the source data and source hashes. All 76,853 sampled walkable cells in a 0.5 m cardinal grid connect. Eighty spawn, camp, lane-waypoint and objective-perimeter positions are reachable from each base with living objective circles included. Twelve malformed/stale/shifted contract variants and a severed-world navigation fixture are rejected. **19 checks pass.**
3. **Integrated native physics.** `world_scene_cases.gd` instantiates the actual `confluence_world.tscn`, confirms that its staged runtime manifest equals the canonical source, and performs real queries inside `_physics_process`. It checks 40 exact blocker surfaces, 4,883 open-floor samples, a 0.65 m capsule sweep along every lane/rotation segment, 14 floor anchors, the scene's actual player capsule, and all four out-of-bounds corner displacements. **16 checks pass**, including the following mutation round.
4. **Live negative fixtures.** In an isolated instance, the test removes a blocker's collision layer, removes the floor's collision layer, and inserts an unexpected center-lane prop blocker. The relevant physics checks detect all three changes. The original physics state is restored and checked again. Source hashes remain unchanged throughout the run.

## Follow-up UI, input and scene-flow review

The first UI extension reproduced the offscreen atlas, crosshair and pause actions at both 1280×720 and 960×600 logical canvas sizes. It also exposed a real projectile spawn error: assigning an untyped array to `projectile.ignore: Array[RID]` failed at runtime even though the player shot counter increased. The exact pre-fix helper, failed report and runtime log are preserved as `world_scene_cases-before-layout-fix.gd.txt`, `native-ui-before-layout-fix.json` and `native-ui-before-layout-fix-log.txt`.

The scene owner corrected the control offsets, typed RID insertion, and teleporting out of overview. Final R2 scene script `fdaebe318b42d509ff96fe5752d53efb6d1098c9cc4fd8b64ca4ab91fdf7845a` passes:

- **19 authority/navigation checks** in `authority-navigation.json`.
- **25 native physics/UI/input-state checks** in `native-physics-ui-final.json`. Controls are within both logical viewports, pause actions do not overlap, Continue has keyboard focus, and actual fired projectiles contain the shooter's RID exclusion. Held movement/fire freeze during pause; resume has neutral actions; F1 interrupts a live dash and switches back safely. Both travel buttons arrive with neutral motion, including travel initiated from overview.
- **13 scene-flow checks** in `native-flow-final.json`: three complete courtyard → connected Explore button → actual Confluence scene → injected Escape → connected Return button → fresh courtyard cycles. Previous scene instances and world collision groups are removed each time.

All three final commands exit zero. Both preserved Godot logs contain zero `ERROR` or `WARNING` lines. `qa-final-manifest.json` pins the reports, logs and test helpers. Button signals and engine input events are injected; this is not a recording of operating-system clicks. Root's rendering and OS-input review remain separate evidence.

## Reproduction

Run from the repository root after dependencies, world asset staging and Godot imports are ready:

```sh
python3 games/yuga-native/tests/world_map_cases.py --report /tmp/world-authority-navigation.json
godot --headless --path games/yuga-native --script res://tests/world_scene_cases.gd -- --report=/tmp/world-native-physics.json
godot --headless --path games/yuga-native --script res://tests/world_flow_cases.gd -- --report=/tmp/world-native-flow.json
```

`authority-navigation.json` pins the canonical manifest and authority sources. `native-physics-attempt1.json` pins the scene, scene script, canonical manifest and test script actually used. A later scene edit requires a fresh native report; these files are historical evidence, not assertions about untested revisions.

## Limits retained

- Native objective markers intentionally have no blocking collision. The current authority blocks living towers and cores. The two checks validate these distinct scopes explicitly.
- Matching 0.65 m radii do not make all collision behavior identical: native capsule versus box corners differ from the authority's square-expanded X/Z boxes. Prediction/reconciliation needs a deliberate common collision contract before online integration.
- Grid reachability is sampled and is not an exhaustive continuous-space proof. Native route sweeps cover declared route centerlines; they do not prove arbitrary player trajectories or navigation AI.
- Floor samples and capsule sweeps are real physics evidence, not render, visual-quality, GPU performance, animation, competitive balance or WAN evidence.
