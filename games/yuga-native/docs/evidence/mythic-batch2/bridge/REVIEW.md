# Native presentation bridge verification

`entity-bridge.json` passes 62 owner tests against content revision 2, creating actual Node3D/MeshInstance3D presentations. It covers eight entity types, orientation, ownership, generations, death/respawn, scope and input acknowledgements, reconnect, migration, 42 reverse seeks, bounded replacement/receipt stress and teardown. Invalid records cannot partially mutate the scene. All meshes are diagnostic original primitives; no collision or gameplay authority is introduced.

`independent-axis-review.json` passes 102 peer-authored actual world-axis and finite/collider checks on the same frozen bridge source. The peer found and corrected an actual projectile pitch defect: the bolt mesh now follows pitch as well as its separate aim marker. `history/` retains the initial parser failure and a 60/61 run that incorrectly compared cumulative history-reset counters as pose state; final comparisons exclude those counters.

`physics-overlap-before.json` and `physics-overlap-after.json` preserve our independent counterexample against the separate physics experiment: a pre-overlapping actor previously moved, then correctly froze with explicit collider identity after the experiment owner repaired both implementations. That evidence does not add a movement controller to this bridge.

No sockets, live native match, browser migration, rendered art acceptance, hit validation or deterministic gameplay replay are claimed. See [the bridge API](../../../NATIVE_ENTITY_BRIDGE.md). Root owns production integration and milestone acceptance.
