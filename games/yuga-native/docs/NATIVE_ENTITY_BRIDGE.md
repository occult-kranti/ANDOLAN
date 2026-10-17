# Native entity presentation bridge — MYTH06

This packet implements an actual Godot scene bridge for the contract-v1 records defined in [NATIVE_CONTRACTS.md](NATIVE_CONTRACTS.md). It is supporting work for FG04-T02. It creates and updates native `Node3D`/`MeshInstance3D` presentations and validates their lifecycle. It does not connect the browser server, migrate protocol 2, simulate movement or award damage/gold.

The supplied meshes are explicitly **diagnostic geometry**: capsules, a structure block, bolts, ground discs and pickup/event markers. They make position, orientation, ownership and lifetime inspectable in a real scene. They are not production heroes, authored vehicle replacements or evidence of final graphics. No commercial game assets were used.

## Entry points

[entity_bridge.gd](../scripts/entity_bridge.gd) extends `Node3D`. Add it to the scene tree and supply the agreed descriptor and authority-issued session scope:

```gdscript
const EntityBridge = preload("res://scripts/entity_bridge.gd")
var bridge = EntityBridge.new()
add_child(bridge)
var expected = bridge.descriptor("native-offline-triad")
var admitted = bridge.open_session("native-offline-triad", expected,
    {"room":"PRACTICE", "epoch":1, "identity":"hero"})
```

This opens presentation validation only; `report().network_connected` remains false. `submit_input(record)` validates issued intent without sending it or moving a node. `apply_snapshot(record)` first runs the accepted contract validator, then updates the native scene. `apply_event(record)` validates a receipt and creates a bounded world marker. Invalid input leaves validator and scene state unchanged.

The bridge owns two top-level containers, `Entities` and `EventReceipts`, so changing the bridge's parent transform does not offset authority world positions. It never creates `CollisionObject3D` instances or takes over player physics. No automatic process loop, physics loop, animation timer, tween or particle simulation runs here.

## Ownership and lifetime mapping

| Authority kind | Native diagnostic presentation | Lifetime behavior |
| --- | --- | --- |
| actor | Feet-origin capsule plus pitched forward marker | Same generation updates in place; dead body/aim hide; respawn requires declared discontinuity. |
| minion, neutral | Smaller capsule plus forward marker | Same ownership and generation rules; no autonomous AI. |
| structure | Static presentation block | Transform/removal comes from authority; no local objective health or shielding. |
| projectile | Bolt whose actual mesh axis follows yaw and pitch | No local collision or inferred hit. Full-snapshot absence destroys the node. |
| zone | Thin disc at authority position | No decorative damage; rule-specific radius/shape/expiry requires a later typed payload. |
| pickup, gold_shard | Small marker | No local pickup or reward logic. |
| event | Detached world-space receipt marker | Stable sequence identity; never attaches a historical actor ID to a new generation. |

The root nodes carry entity ID, generation, kind, team, attribution owner, discontinuity, alive state and acknowledged input as metadata. A same-generation update preserves the actual node instance. A greater generation destroys the old node synchronously and creates a fresh presentation. Full-snapshot absence frees the old node and associated receipts. Old generations and undeclared resurrection reject in the contract layer.

On discontinuity, associated transient receipt presentations are cleared and Godot physics interpolation is reset **after** setting the new pose. No pose interpolation is implemented in this packet. The `history_reset_count` is diagnostic evidence of resets; it is not part of the pose fingerprint.

Receipt amount/type does not mutate an entity, health, inventory or economy. This prevents a presentation event from becoming an accidental second gameplay authority. At most 64 receipt nodes exist; excess accepted receipts evict the oldest presentation while retaining the validator's sequence watermark. Events expire after 40 authority ticks as new accepted snapshots/events advance the presentation clock. This fixed debug lifetime is not a final combat-effect duration. With no new authority tick, presentation stays frozen.

Mesh resources are cached by the bounded diagnostic kind set, and materials by Sun/Moon/neutral team. Session reset clears owned nodes, preserving only those bounded caches. Scene teardown frees the bridge and all children.

## Aim and coordinate bridge

Shared coordinates are metres, +Y up, +Z forward, feet origin. The explicit aim direction is:

```text
d = (sin(yaw) cos(pitch), sin(pitch), cos(yaw) cos(pitch))
```

Actor roots rotate around +Y by shared yaw. Their `Aim` child rotates around X by `-pitch`. Projectile cylinders rotate around X by `π/2 - pitch`, so their **actual mesh axis**, not merely an unused marker, follows the same direction.

Static helpers `aim_direction`, `native_to_shared_yaw` and `shared_to_native_yaw` enforce finite bounds. Native camera forward is −Z, so shared yaw is `wrap(native_yaw + π)` and the inverse subtracts π. Positive pitch remains upward. Tests cover 25 cardinal/high/low combinations, round trips and actual mesh/anchor world bases.

Current browser Actor snapshots do not include continuous remote aim pitch. This bridge consumes the **new contract-v1 envelope**, not unmodified protocol-2 packets. It does not fabricate pitch from a local camera or claim that the current authority transmits it. A real native online adapter must negotiate that extension or display pitch as unavailable.

## Reconnect, migration and replay

- `begin_reconnect()` freezes accepted scene entities, blocks new input/snapshot/event admission and clears transient markers. There is no extrapolation or queued held input.
- `resume_session(descriptor, scope)` requires the same authenticated room, epoch, identity and exact descriptor. It preserves acknowledged input, event/snapshot watermarks and entity instances. Duplicate old receipts stay rejected.
- `migrate_session(profile_id, descriptor, scope)` requires the contract's explicit greater epoch. It clears all presentations, replay state and old acknowledgements. It cannot silently reopen an old epoch.
- `disconnect_session()` clears all owned entity/event nodes, replay records and validator state. The external session owner remains responsible for authentication and preventing unauthorized old-room reuse.

`load_replay(header, records)` validates the **entire** bounded replay before replacing a live scene. Corruption in the final record therefore cannot clear an otherwise valid current scene. It stores detached records and enters replay mode at cursor zero. Live messages cannot inject into that mode.

`seek_replay(record_count)` constructs a fresh private guard from the epoch start and validates the requested prefix before committing it. It then reconstructs the final native nodes and surviving event presentations. There are no unchecked pose checkpoints or accumulating forward-only tweens. Repeated backward seeks reproduce the direct forward scene's actual transforms, mesh bases, visibility, generations and event positions. Gameplay simulation is not reexecuted.

`report()` exposes session/ack/sequence data, real scene poses, bounded resource counts, a `pose_digest` and cumulative diagnostic counters. Cumulative spawned/update/reset counters intentionally differ after repeated seeks; they are excluded from the pose digest. `entity_node(id)` exposes the owned node for trusted future integration, not remote resource loading.

## Physics and content handoff

The bridge has no support-surface or collision authority. The parallel FG05-T02 experiment uses matching metres/+Y/feet/+Z and tests rays, initial overlap and swept shapes against stacked decks. Its TypeScript reference and Godot queries are a bounded comparison, not an adopted multiplayer controller.

Peer review found that a cast can ignore an initially overlapping shape. The paired-stream experiment now checks overlap first: the invalid actor stays at its initial feet with fraction zero and explicit `invalid_initial_overlap`, while the valid peer proceeds. Independent failing/fixed evidence is retained under `/workspace/scratch/yuga-bridge/physics-independent-probe*.json`. Support IDs, movement mode, health/cast data and rule-specific effect geometry still need typed payload/version work before production online integration.

Batch 2 deliberately advances native-practice content to revision 2 after the army/minion/invocation sources freeze. Browser/proposal content remain revision 1 and input/event/entity/replay wire versions remain 1. The final 62-case bridge run uses the refreshed catalogue. Old descriptors reject before presentation admission. Do not reuse a previously accepted content digest after changing its sources.

## Executed verification

```sh
XDG_DATA_HOME=/tmp/yuga-bridge-check godot --headless --path games/yuga-native \
  --script res://tests/entity_bridge_cases.gd -- --report=/tmp/entity-bridge-cases.json
```

The [current 62-case owner suite](evidence/mythic-batch2/bridge/entity-bridge.json) passes with clean logs against native content revision 2. It instantiates real scene nodes and verifies all eight kinds, safe rejection without partial scene mutation, actual pitch/mesh axes, parent-transform isolation, generation replacement/freeing, death/respawn, room/epoch/ack preservation, reconnect and migration, late replay corruption, 42 reverse seeks compared with direct scene geometry, 500 lifetime replacements, 128 receipts with only 64 event nodes, expiry, 30 session cycles and teardown.

Preserved corrections: an initial test parser annotation, replay comparisons accidentally including cumulative history diagnostics, and the peer-detected projectile body pitch defect. Evidence is headless node/lifecycle evidence; no actual render, human input, online match, hit validation or production-art acceptance is claimed. [Independent axis review](evidence/mythic-batch2/bridge/independent-axis-review.json) adds 102 checks of actual actor/minion/neutral and projectile bases, finite rejection and absence of colliders. It pins the unchanged bridge source; it is not a render review. [Archived failures](evidence/mythic-batch2/bridge/history/) retain the earlier owner corrections. Root owns integration and task acceptance.
