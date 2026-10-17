# Sources used for the lane and traversal milestone

This is a bounded reading and implementation record, not a claim to have read every book or watched all game footage. Retrieval URLs, exact byte hashes and dates are in `traversal-source-register.json`.

| Source | Selected idea | Concrete use |
| --- | --- | --- |
| Robert Nystrom, [Game Loop](https://gameprogrammingpatterns.com/game-loop.html) | Separate simulation progression from rendering; avoid unstable variable-step feedback | Fixed-step movement/army tests; distinguish simulated time from wall-clock performance |
| Nystrom, [Object Pool](https://gameprogrammingpatterns.com/object-pool.html) | Define capacity and overflow; reset recycled state | Bounded audio voices, live/corpse/attack budgets and reset/flood tests |
| Nystrom, [Spatial Partition](https://gameprogrammingpatterns.com/spatial-partition.html) | Limit local searches instead of unconstrained all-pairs work | Army neighbor separation and bounded target cadence |
| [Godot 4.6 CharacterBody3D](https://github.com/godotengine/godot/blob/4.6-stable/doc/classes/CharacterBody3D.xml) | Collision-based velocity movement, floor/ceiling and margin behavior | Flight/tether use the existing capsule and move-and-slide path; thin-wall and landing tests |
| [Godot 4.6 InputMap](https://github.com/godotengine/godot/blob/4.6-stable/doc/classes/InputMap.xml) | Action-to-event mapping | Persistent remapping with conflict and stuck-input tests |

Retained player criticism is in `games/yuga/docs/research/DEADLOCK_PLAYER_FEEDBACK.md`: 40 posts and 145 comments collected earlier on 2026-10-16. It is a small, selected and partly truncated sample, not a representative survey. No new Reddit or video viewing is claimed for this milestone. Attention burden, contextual help, understandable markers, consistent routes, lifecycle reliability and movement labels inform the acceptance gates.

Art uses invented Indian-inspired stepped plinths, open canopies, lotus motifs, hanging diyas, bronze rings and cloth/weapon silhouettes. The generated reference is an original fantasy environment, not an archaeological reconstruction. Vayu/Naga naming provides myth-inspired imagery without presenting new game abilities as canonical events. Human cultural/art review remains a production task.

REA/Ghidra can support lawful native-binary analysis when relevant inputs exist. This work has no supplied commercial clients and does not report binary analysis of Deadlock, Overwatch or Dota 2. Prior public-source and original-fixture analysis remains separately documented in the repository.
