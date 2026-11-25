# Height and headroom at the Sun west wind court

Rust can now answer two questions at the Vayu landing court. From a given world-space position, what surface and overhead face would a vertical ray reach? Given a proposed landing height, would Rama's actual capsule fit there? The executable uses the canonical Godot scene's 36 detailed box colliders and its physical floor. The court is centred at `[-20, 0, -88]` metres. The live match still uses its existing planar route authority. [Rust executable and regression tests](../../../../yuga-rust/src/bin/court.rs) · [Exported colliders and native answers](../../../../yuga-rust/assets/court/native.json) · [Godot extractor](../../../../yuga-rust/tools/court/capture.gd)

## What the geometry allows

| World-space probe | Native geometry result | Player implication |
| --- | --- | --- |
| X −20, Z −88, ray from Y 12 | Roof at Y 8.00. All 25 sampled roof points have valid capsule clearance. | A descending actor can land on the rooftop court. |
| X −18.95, Z −91.73, ray from Y 3 | Upper plinth tread at Y 1.15, overhead crown face at Y 6.93. | The tread is too narrow for the player's radius. It fails the standing test. |
| X −18.95, Z −91.92, ray from Y 3 | Lower plinth tread at Y 0.48, overhead crown at Y 7.40. | The horizontal face alone would give a false landing. The capsule overlaps the next solid. |
| X −18.95, Z −92.02, feet at Y 4.80 or 6.25 | The lower capsule fits in the recessed facade bay. The higher capsule's head meets the crown. | A flying actor has lateral clearance in the bay and a bounded rise. |
| X −20, Z −88, ray starting at Y 4 | Origin is inside the closed masonry core. | The court has a solid centre. A route underneath the roof through the building would contradict the source. |
| X −18.95, Z −92.85, ray from Y 1 | Outside ground at Y 0 with clearance. | The surface is reachable at ordinary ground level. |

The artist built a pair of plinth courses and a stepped, overhanging crown. There is no continuous staircase from the ground to the roof. The native builder deliberately backs every side bay with a closed core. Its two visible meshes share the same detailed collision body. The previous 8 × 8 × 8 m full-box approximation would close the real facade recess. [Authored geometry](../../../scripts/traversal_landmarks.gd) · [Detailed replacement in the canonical scene](../../../scripts/confluence_world.gd) · [Original integration and negative control](../../../tests/wind_court_integration_cases.gd)

## How the comparison works

The exporter starts the actual Confluence scene, checks that the detailed collider replaced the original, copies the dimensions of the player's live capsule, and records the 37 world-space boxes after the physics server synchronizes. For each reference origin it records Godot's inside-solid result, downward support, upward ceiling and overlap of the capsule placed 2 cm above the support. Separate samples probe the capsule directly at supplied foot positions. That 2 cm lift keeps the fitted capsule clear of its supporting face during a standing-clearance test. The direct capsule query uses the exact supplied foot position.

The Rust ray query intersects the same boxes in height order at the selected X/Z. For a capsule it measures the closest squared distance between its vertical central line segment and each box, and compares this with radius squared. This includes rounded top, bottom and corner clearance. The current court has only axis-aligned boxes. The extractor rejects rotated, scaled or non-box shapes, and the runtime checks SHA-256 for the scene, its assembly code, the landmark builder, the player source and the map. The CLI accepts only a local 11 × 11 m patch centred on this court to avoid querying other map landmarks from incomplete geometry.

| Compared against Godot 4.6.3 | Result |
| --- | ---: |
| Distinct surface probes, each checking initial overlap, down, up and standing clearance | 120 |
| Downward rays that hit a horizontal surface | 81 |
| Surfaces where the player capsule could stand | 43 |
| Overhead faces detected | 22 |
| Direct capsule overlap queries | 66 |
| Blocked capsules | 42 |
| Maximum absolute height difference | 0.000000477 m |
| Capsule dimensions | radius 0.65 m, total height 1.80 m |

Restoring the obsolete full-box collider in memory makes the comparison fail. The test also exercises out-of-region and nonfinite coordinates. These measurements cover static vertical queries and capsule occupancy. Walking up a riser, sliding diagonally past it, jumping, grazing a convex edge, and forced movement along a network-reconciled path require swept movement tests. [Native donor hashes and cases](../../../../yuga-rust/assets/court/native.json) · [Rust acceptance output](COURT-PORT-EVIDENCE.json) · [Port-wide ground assumptions](../WORLD.md)

## Reproduce and query

Run from the repository root. The Rust executable includes the fixture and checks it against the native donor files at build time and startup. Godot is required to regenerate the independent physics answers.

```sh
game=games/yuga-rust
native=games/yuga-native
cargo test --locked --manifest-path "$game/Cargo.toml" --bin court
cargo run --locked --manifest-path "$game/Cargo.toml" --bin court -- verify
cargo run --locked --manifest-path "$game/Cargo.toml" --bin court -- surface -20 12 -88 6
cargo run --locked --manifest-path "$game/Cargo.toml" --bin court -- surface -18.95 4 -91.91 5
cargo run --locked --manifest-path "$game/Cargo.toml" --bin court -- capsule -18.95 6.25 -92.02
work=$(mktemp -d)
godot --headless --path "$native" --import
godot --headless --path "$native" --script "$PWD/$game/tools/court/capture.gd" -- "$work/native.json"
cmp "$work/native.json" "$game/assets/court/native.json"
```

## Next integration

1. Add support height, vertical velocity and a stable support ID to the match's hero state. Keep lane troops on their existing X/Z paths until a lane traversal graph explicitly connects elevations. The export uses the donor's world axes and metre scale.
2. Replace the court's coarse box for hero movement and visibility with the detailed collision collection as a single operation. Keeping both produces the blocked recess exposed by the negative control. Carry the original floor exactly once.
3. Add a swept vertical capsule and a walkable-step policy. A candidate landing should have a non-obstructed path, an upward-facing contact and room for the standing capsule. Exercise descent to the roof, stepping off the edge, upward contact at the crown, corner slides and re-entry at ground level against Godot's CharacterBody3D.
4. Feed actual height into the camera, aim ray, projectile muzzle and damage-receiver positions. Compare free flight, a shortened vault, foot placement and authoritative two-seat replay at this court before applying the change to other raised landmarks. [World and planar hero movement](../../../../yuga-rust/src/world.rs) · [Actor and ability state](../../../../yuga-rust/src/combat.rs) · [Match host](../../../../yuga-rust/src/battle.rs)
