# Grounded Rama practice decision component

Role 10 of the Rama quality squad, 17 October 2026. `scripts/rama_practice_brain.gd` is an original, deterministic decision component for a future admitted native hero actor. It emits movement, aim, reload and Rama ability **requests**. It does not spawn a hero, move a node, call a damage receiver, fill ammunition, spend a cooldown, connect a network or add a playable bot to the current world.

The current native world has one locally controlled hero. `rama_hero_runtime.gd` binds its `CharacterBody3D`, camera, ammunition, action state, vitals and one real `RamaAbilityKit`. Ordinary lane troops do not implement a second hero actor or fight a hero under complete player-equivalent rules. The component is therefore staged until the integrating owner supplies an actual second hero authority and renderer. A passing component test does not close that gate.

## Ownership and integration contract

```gdscript
const PracticeBrain = preload("res://scripts/rama_practice_brain.gd")
var brain = PracticeBrain.new()
assert(brain.configure(actor_id, session_id, actor_generation, "standard"))

# Called once for each fresh authority step. These functions are the actor/map
# owner's adapters; they are intentionally not invented production APIs here.
var intent = brain.decide(delta, simulation_time, observation,
    ground_line_clear, safe_ground_steering)

# The admitted actor owner must validate the identity, generation and tick again
# before applying this same-step request through its actual movement/reload APIs.
# Its real RamaAbilityKit alone admits and executes requested abilities:
if intent.valid and not intent.ability_id.is_empty():
    var receipt = actor_kit.request_ability(intent.ability_id, actor_position,
        intent.aim, intent.ground_target,
        {"step_direction":intent.step_direction})
```

Only `PracticeBrain.configure`, `decide`, `reset` and the existing kit API above are implemented interfaces. The observation builder, actor movement/reload admission and geometry adapters belong to the future integrating actor. Do not wire the brain into the existing human player by synthesizing `Input` events or by changing damage receivers. Do not use a browser-protocol snapshot as an unreviewed native observation.

`line_clear(from_world, to_world, horizontal_margin_m) -> bool` must read the actual accepted map/cover geometry. `steer(origin_world, desired_planar_direction, lookahead_m) -> Vector3` must return a finite planar direction with length at most one, or zero when there is no safe route. Both callbacks must be side-effect-free. The brain also checks the returned movement corridor with the actual LOS callback and a 0.65 m actor margin. The future `CharacterBody3D` still owns collision and acceleration. This component supplies no navigation graph or path search and does not guarantee route completion around concave buildings.

Existing `lane_army.gd` exposes `line_clear` and `segment_wall_fraction` for exact planar box geometry. `rama_practice_army.gd` combines that geometry with actual layer-1 courtyard raycasts. Their public points are **army-local**; a world-space adapter must call `army.to_local` for both points before forwarding a query. This distinction matters when the army has a transform. The test fixture uses identity transforms and does not establish transformed-world integration.

The incoming observation is a small detached authority sample with exactly these fields:

| Fields | Required meaning |
| --- | --- |
| `actor_id`, `session_id`, `generation` | Exact configured actor/session and explicit integer lifetime generation |
| `tick`, `time_s` | Fresh monotonically increasing integer step and finite source simulation time, at most 150 ms old and never future-dated |
| `paused`, `ended`, `alive`, `grounded` | Validated actual lifecycle/support state; `alive` agrees with health |
| `action_locked`, `movement_locked` | Actual actor admission gates. Include an active reload in `action_locked`; use the actual committed-cast lock for movement |
| `team`, `position`, `yaw` | Actual team and world feet position; shared +Z-forward yaw, not the native model/camera PI offset |
| `health`, `max_health`, `shield`, `ammo` | Actual current actor values, never values inferred from a visual or cooldown animation |
| `cooldowns` | All five finite nonnegative remaining cooldowns from the actual kit, with its exact ability IDs |
| `candidates` | At most 96 current bounded dictionaries, each exactly `id`, `team`, `position`, `alive`, `observed` |

The authority caller supplies a separate `now_s`; it must be current simulation time in the same domain as `time_s`. Delta must be positive, at most 100 ms and no greater than elapsed authority time after the first sample. Duplicate/stale ticks, nonadvancing/regressing clocks, invalid callbacks or malformed samples produce zero movement and no action. Unknown or extra fields reject so unbounded nested payloads are not deep-copied. A geometry callback cannot mutate the accepted sample by alias. A generation reset during a callback invalidates the old decision; a reentrant decision produces no action.

`reset(new_generation)` requires a strictly greater generation. It clears target, timing and old tick history so an old actor cannot replay controls after a new lifetime. A different session or actor uses a new brain instance. Every proposed turn begins from the actor's **current authority yaw**, so a previously rejected turn cannot accumulate fictional local aim. The caller must apply the accepted yaw through its real actor API and include the resulting actual yaw in the next observation.

## Behavior and fairness

The state machine has reaction, tracking, approach and retreat states, plus neutral paused/ended/dead/airborne/rejected states. It can acquire only explicitly observed, alive enemies within 40 m, within an 80-degree half-angle of the actor's actual facing, on the same ground elevation within 0.4 m, and with current cover clearance. A lost target is forgotten immediately. The brain never uses a new position behind a wall, extrapolates an unseen target or reads projectiles to dodge them.

| Difficulty | First reaction | Maximum turn speed | Bounded aim variation | Intent interval | Walk speed ceiling |
| --- | --- | --- | --- | --- | --- |
| Easy | 350 ms | 120 degrees/s | 4 degrees | 600 ms | 4.8 m/s |
| Standard | 220 ms | 180 degrees/s | 1.5 degrees | 480 ms | 5.5 m/s |
| Hard | 140 ms | 240 degrees/s | 0.5 degrees | 400 ms | 6 m/s |

First reaction delays movement, turning and firing. Aim variation and two-second lateral weaving derive from the actor identity and simulation time; the same complete inputs produce the same outputs. The brain never gains extra reaction speed from render frequency. Each authority tick may produce at most one ability or reload request. Rejected admission does not trigger a per-frame retry: the intent cadence still applies. These are initial testable tuning values, not measured human-feel or competitive balance results.

When healthy, the actor approaches outside 19 m, retreats inside 7 m and otherwise weaves conservatively. Low health also requests retreat. A ready Guardian is preferred below 65% health when the actor has no shield. A ready Measured Step can help retreat from a visible enemy inside 5 m; it grants no invulnerability. A ready Dawn Volley requires at least two distinct visible first-hit receivers across its proposed three firing lanes. Two enemies standing behind one another on a single first-hit lane instead offer a Piercing Dawn opportunity. Otherwise the brain requests Piercing Dawn at 8–38 m, or Kodanda. Cooldowns and action locks are sampled hints: the actual kit still decides whether any request is legal. Empty ammunition emits a reload request and never grants ammunition itself.

This is intentionally understandable grounded practice behavior. It does not implement lane macro strategy, farming/economy, objectives, team cooperation, tactical cover selection, advanced ability combos, target leading, airborne aiming, flight/grapple, reconnect takeover, difficulty adaptation or online opponents. It has no external model/API dependency and imports no commercial game code or assets.

## Verification and remaining gates

After coordinating the shared lightweight test slot, run:

```sh
godot --headless --path games/yuga-native \
  --script res://tests/rama_practice_brain_cases.gd \
  -- --report=/tmp/NEW-rama-practice-brain.json
```

The suite uses the actual lane slab geometry to test loss of sight through a 1 mm wall. It exercises identity/time/generation validity, delayed reaction, capped aim, steering rejection, acquisition rules, lifecycle neutralization, cooldown/cadence hints, reset/reentry and deterministic replay. One explicit caller fixture passes a proposed Kodanda request through the **actual** practice army and Rama kit, then observes one real 28-damage hit. Before that explicit call, the brain cannot alter target health or start a cast. The fixture has no second hero authority and claims no rendered bot or online match.

The final focused suite passed **52/52** on Godot 4.6.3, with clean exit 0. Independent read-only review found the first-hit Volley selection issue above after an earlier 45-case pass; the final suite includes that exact counterexample. [Owned evidence](../evidence/rama-quality/ai/REVIEW.md) pins the executed source, report, raw log and independent review. No GLB/editor import, actual render or OS-input session was executed for this module.

Before enabling practice bots, the next owner must implement and independently review an admitted second native hero with player-equivalent movement, action/ammo/reload, health/shield, target identity and damage rules; connect actual navigation/cover adapters; synchronize real kit events to the actual Rama renderer; exercise death/reset/pause while both actors are live; and review complete rendered encounters with human players. Native online adds authenticated authority, authoritative elevation, action replication and two-client stress tests described in [the replication audit](NATIVE_HERO_REPLICATION.md). Physical-GPU profiling and perceived fairness/smoothness remain separate acceptance gates.

## Source review

This pass read the local `player.gd`, `rama_hero_runtime.gd`, `rama_ability_kit.gd`, `lane_army.gd`, `rama_practice_army.gd`, `rama_practice_target.gd`, the exact current `rama-ability-kit.json`, build handbook and native hero replication audit. The design follows their existing authority/presentation boundary and current grounded rules. It did not inspect commercial binaries, fetch a new book/article, watch gameplay footage or recover a commercial game's AI. Wider game-design literature and accessible source research remain in the squad's source ledger; they are not claimed as fresh readings by this component.
