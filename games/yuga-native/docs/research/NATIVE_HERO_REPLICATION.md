# Rama remote presentation foundation

Role 09 of the Rama quality squad, 17 October 2026. This adds a **pose-only adapter**, `scripts/rama_remote_replica.gd`, around the existing validated transport/interpolator and, separately, the existing contract/entity bridge. It is not wired into the native world, camera, matchmaking or server. The current native build remains offline. This component does not close native online, 6v6, Rama action replication or visual-quality acceptance.

## The actual missing bridge

| Existing implementation | What is already available | What it does not provide |
| --- | --- | --- |
| `arena_client.gd` | Browser protocol 2 admission, full validated snapshots, room identity, stale-packet rejection, reconnect state and command receipts | Native Confluence authority, remote pitch, actor generation, traversal/support surface, native Rama windup/release/cancel events; its commands have three ability slots |
| `arena_interpolator.gd` | Bounded 32-snapshot history; delayed finite X/Y/Z/yaw sampling; shortest yaw arc; bounded projection and discontinuity heuristics | Skeleton poses, Rama ability timing, verified lifetime generations, map alignment or real rendered match integration |
| `native_contracts.gd` and `entity_bridge.gd` | Separately validated generation/discontinuity/alive/pitch poses, full-snapshot omissions, explicit session scope and diagnostic presentation nodes | A live native transport, hero asset identity, authoritative Rama ability state or an assigned production network frequency |
| `rama_motion.gd` | Exact 164-bone rest-validated controller and authored locomotion/action clips | Network authority, attack admission or an authoritative remote action schema |

The native envelope and browser protocol are deliberately separate entry points. There is no fabricated protocol-2 pitch, guessed ability state, automatic native-envelope conversion, cooldown-driven attack or locally granted damage. The native envelope calls an entity `actor`; it does not identify a Rama asset. The integrating owner must already know the appropriate asset binding. That missing authoritative hero identity remains open.

## Component contract

Create one `Node3D` replica per actual remote Rama and add the actual hero model as its child. `configure_visual(model, animator=null)` validates the existing 164-bone Rama rest rig through the real `RamaMotion.configure` API. It creates one RamaMotion, pauses the model's AnimationPlayer and rejects an already bound visual or a visual with an existing RamaMotion. An omitted animator is found below the visual. There is no fallback mesh/avatar. Supply the current accepted hero GLB; fixture skeletons belong only in the component tests.

Then choose exactly one source:

```gdscript
const RemoteReplica = preload("res://scripts/rama_remote_replica.gd")
var replica = RemoteReplica.new()
world.add_child(replica)
var model = load("res://assets/heroes/rama-hero.glb").instantiate()
replica.add_child(model)
assert(replica.configure_visual(model))
# Existing real ArenaClient instance; remote_id must differ from client.identity.
assert(replica.bind_arena(client, remote_id))
```

This is an integration recipe, not a claim that the world executes it. Binding enables presentation `_process`. The owner must choose its pause/process mode and lifetime with the rendered session. `unbind_source()` disconnects source signals, hides the visual and clears local presentation history. `reset_replica(reason)` clears presentation while retaining the bound source, so the next poll reads its current accepted state. `advance(delta, at_seconds=-1)` supplies deterministic frame/clock inputs for tests or owner-managed presentation; normal execution uses monotonic ticks. Manual and automatic advancement must not both drive the same replica.

`bind_arena(actual_client, remote_id)` admits the exact existing ArenaClient script. Its snapshot signal sets a dirty flag; the adapter ignores the supplied signal payload and fetches the client's accepted `get_snapshot()` copy once per changed receipt. It extracts only that Rama actor into the existing interpolator, retaining at most 32 single-actor poses. It never accepts an arbitrary dictionary supplied by a caller. The default interpolator retains its 100 ms delay, at most 100 ms projection and 35 m/s continuity bound.

`bind_bridge(actual_bridge, actor_id)` admits the exact existing EntityBridge script and reads its public `report()`/`entity_node()` APIs. It consumes exact accepted envelope poses and holds unchanged ticks. It does not interpolate using an invented tick rate. This bridge path currently remains diagnostic and disconnected. Its `report()` builds a bounded full public report; production integration should provide a separately reviewed single-entity read API before making this a many-replica hot path. That API is outside this component's exclusive ownership.

The replica uses world feet coordinates independently of its parent transform. Shared +Z yaw maps through the existing shared/native conversion and model PI offset. Only finite, bounded positions and finite yaw/pitch reach the visual. Render delta below one microsecond, negative/zero/nonfinite delta, delta over ten seconds, regressing clock, nonfinite clock and clock above `1e12` seconds reject. A valid long frame advances the skeleton by at most 100 ms, without unbounded catch-up simulation.

## Lifecycle and unsupported state

- Connecting, joining, disconnecting, explicit teardown and same-room reconnect clear history. An authority omission, disconnected actor or changed hero identity hides the model. Only protocol-2 `kind=hero, heroId=rama` maps to the Rama asset.
- Actual authority health/respawn or validated `alive` controls visibility. Stale data hides after one monotonic second, while keeping the last authority alive flag; timeout never becomes a defeat or reward.
- Reappearance after timeout/pause, authority death/respawn, changed identity, explicit bridge generation/discontinuity and a new bridge scope clear motion history. Poses never sweep from the old origin across those transitions. Ordinary projection still obeys the existing interpolator's bounds.
- Protocol-2 generation is unavailable. Its reset handling is a presentation heuristic, not a recovered or invented authoritative entity lifetime.
- A final accepted protocol-2 finished pose holds exactly. It does not continue projecting indefinitely or synthesize a match outcome.
- Freed or queued source, visual or motion fails closed. The component does not own or delete the transport or bridge's diagnostic nodes. External code must not free bridge-owned children; the bridge's public report assumes its own node ownership remains intact.
- Locomotion comes from sampled displacement only. The conservative grounded animation reference uses the provided actor feet height; it is not a verified support surface. Flight, grappling, airborne state, aiming, hit reactions and casts remain unsupported. No attack is inferred from generic `ability` receipts, cooldowns or speed. Protocol-2 pitch stays zero; validated native-envelope pitch is used only as a presentation pose value.

`report()` exposes source kind, latest accepted tick, visible/present/alive state, finite pose/velocity, history bounds, reset/reject counters and the explicit unsupported fields. It states `network_connected_by_this_component=false`, `local_damage_authority=false` and `action_replication=unsupported`. No session token or credentials are retained here.

## Verification and next acceptance gates

Run the light component suite from repository root after coordinating the shared test/render slot:

```sh
godot --headless --path games/yuga-native \
  --script res://tests/rama_remote_replica_cases.gd \
  -- --report=/tmp/NEW-rama-remote-replica.json
```

The fixture reconstructs the exact 164 rest bones from the existing motion library metadata and exercises the real RamaMotion, ArenaClient and EntityBridge. It loads no GLB, mesh, editor import or renderer. Its scope is behavior and API compatibility; it cannot accept skin deformation, hair/cloth quality, perceived movement, multiplayer latency or hardware performance. See [owned evidence](../evidence/rama-quality/network/) for source hashes, executed results and the review.

Before native online can close, the integration owner still needs an authenticated native authority/bootstrap; exact map/content agreement; authoritative Rama four-ability lifecycle, target/damage and elevated traversal rules; remote hero identity; two actual rendered clients; camera/local reconciliation and input-neutralization UX; projectile/VFX presentation tied to real authority events; reconnect/loss/late-event tests; a sustained full match; and real GPU/WAN profiling. The component does not silently borrow browser rules for those missing features.

## Source basis

This is an original adapter around the repository's existing implementation, not imported commercial game code. Local source/API review covered the four scripts above, native contract catalogue, current `player.gd` visual binding, the [transport report](../NATIVE_NETWORK_ADAPTER.md), [interpolation contract](../NATIVE_INTERPOLATION.md) and [native contracts](../NATIVE_CONTRACTS.md). The older native-contract prose has stale revision/health descriptions; current catalogue/code and pinned tests control actual behavior.

The existing [Rama design study](RAMA_HERO_DESIGN_STUDY.md#focused-books-documentation-and-open-source-resources) links Godot's [physics interpolation guidance](https://github.com/godotengine/godot-docs/blob/4.6/tutorials/physics/interpolation/using_physics_interpolation.rst) and Nystrom's [Game Loop](https://github.com/munificent/game-programming-patterns/blob/898b1f2e1818c80d7eed5eba98e9903ec13b7771/book/game-loop.markdown) chapter. That prior source reading supports distinct simulation/presentation owners, bounded catch-up and resetting interpolation on discontinuity. This task did not fetch a new copy or claim to recover Deadlock's networking implementation. Perceived Deadlock-level smoothness must be reviewed on the actual integrated hero and networked game.
