# Rama in the Rust Confluence match

Rama is a second selectable player character on the same 20 Hz match clock as Hanuman and the lane army. His arrows intersect moving soldiers and the opposing hero. Guardian Circle heals and shields actual allied receivers. The browser and native room host call the same Rust code. The highest-detail model and the browser LOD both retain their original skin and textures. [Rust hero and regression cases](../../../../yuga-rust/src/rama.rs) · [Match integration](../../../../yuga-rust/src/battle.rs) · [Source character provenance](../../../NOTICE/RAMA-HERO-PROVENANCE.json) · [Build and pose evidence](RAMA-PORT-EVIDENCE.json)

## Existing code and art used

| Input | What it contributes |
| --- | --- |
| YUGA Rama rules | Original range, windup, recovery, cooldown, protection, damage, per-arrow limits and volley yaw offsets. The Rust hero deserializes the same file on startup. [Five-action kit](../../../assets/design/rama-ability-kit.json) |
| Native Godot combat and actor | Bow fire locks aim at acceptance. Kodanda resamples the body's position when the arrow releases. The player wrapper spends one arrow only after acceptance. Its magazine holds 12 and takes 1.6 seconds to reload. The native kit checks ground, cover, faction, shield ownership and per-projectile contacts. [Native kit](../../../scripts/rama_ability_kit.gd) · [Player binding](../../../scripts/rama_hero_runtime.gd) · [Magazine and reload](../../../scripts/player.gd) · [Geometry helper](../../../scripts/ultimate_rules.gd) |
| Native art and controller | The model comes from YUGA's existing 164-joint MakeHuman-derived skeleton and original modeled face, hair, bow and costume. The original motion library plus procedural contact, grip and string solving run when producing the ten new stage clips. Each baked stage drives the actual skinned model. [Production notice](../../../NOTICE/RAMA-PRODUCTION-PROVENANCE.json) · [Editable-source chain and runtime LOD revisions](../../../NOTICE/RAMA-HERO-PROVENANCE.json) · [Native motion controller](../../../scripts/rama_motion.gd) · [Authored motion](../../../assets/animations/rama_hero_motion.tres) |
| Existing Hanuman port | Reuses the existing Parry-backed world, 20 Hz host, PlayCanvas character setup, global-pose verifier and shared hero/army health receivers. Straight sweeps expose a normalized first-wall fraction. Step and vault share the endpoint solver and pass their own clearances. [World geometry](../../../../yuga-rust/src/world.rs) · [Shared receiver](../../../../yuga-rust/src/combat.rs) · [Renderer](../../../../yuga-rust/web/scene.ts) · [Previous hero study](../HERO-ANIMATION.md) |

For the ranged port we also traced the GPL-3.0 Rust RPG **Veloren**. Its basic ranged state times buildup before emitting a server shoot event. Its rapid-shot state schedules projectile releases independently of animation presentation. Its projectile system excludes the owner and previously hit receivers. Those files provide a comparison for authority, ownership and repeated contact. This port uses YUGA's native targeting, abilities and art, and the Rust binary has no Veloren dependency. [Basic ranged state](https://github.com/veloren/veloren/blob/131d1193387861d35c74655662148f303c22c5b4/common/src/states/basic_ranged.rs#L82-L135) · [Rapid ranged state](https://github.com/veloren/veloren/blob/131d1193387861d35c74655662148f303c22c5b4/common/src/states/rapid_ranged.rs#L95-L140) · [Per-projectile contact filtering](https://github.com/veloren/veloren/blob/131d1193387861d35c74655662148f303c22c5b4/common/systems/src/projectile.rs#L141-L192) · [License](https://github.com/veloren/veloren/blob/131d1193387861d35c74655662148f303c22c5b4/LICENSE)

## Play and combat contracts

| Input | What the player can do | Authoritative result |
| --- | --- | --- |
| Primary | Move while drawing Kodanda. Press or hold fire. | One arrow, 28 damage, 60 m/s, 40 m range. Release on the fourth 50 ms tick after a 0.18 s draw. The next draw is available at 0.40 s. R reloads the quiver. An empty primary request also starts reload when the actor is free. |
| Q | Commit to Piercing Dawn and line up enemies. | A 52 m/s swept arrow deals up to 70 damage per hit, in contact order, to at most six distinct enemies. A wall wins a tie with a receiver at the same location. Bodies do not shield their allies from this arrow until the six-hit limit. |
| E | Step along the last movement direction, or forward when stationary. | Locks aim, caps displacement at 4.5 m, resolves the intended endpoint against cover and sweeps the actor during the step. Its 0.1 s windup and 0.22 s movement use the same simulation as the browser. |
| C | Place a visible ground circle within 16 m. | After 0.55 s, allies and Rama within 5 m receive 55 shield on entry and up to ten HP per second for 4.5 s. An existing stronger independent shield survives cancellation. A previous longer shield is restored on expiry up to its unspent value. |
| X | Choose three fixed firing lanes for Dawn Volley. | Start after 0.95 s. Three separately simulated arrows travel at 34 m/s, at yaw offsets −0.105, 0 and +0.105 radians, staggered by 0.1 s. Each deals up to 82 damage on first contact and stops on cover. |

All projectiles sweep the full horizontal distance since the last tick. The earliest wall fraction clips the path. Each arrow keeps its own hit set, so a piercing arrow cannot damage a receiver twice on adjacent ticks. Equal contact fractions resolve by stable receiver ID. Sun or Moon can play Rama. Target filters always compare participants against the actor's actual team. A released arrow's origin and height come from the native bow muzzle captured at release and rotated into the locked aim. The guardian field can remain active while a subsequent action begins. Its server-side expiry is available as `field_end_tick`. [Simulation](../../../../yuga-rust/src/rama.rs) · [Asset-build muzzle offsets](../../../../yuga-rust/assets/rama-muzzles.json)

## Rig and animation handoff

The source GLBs already contain nine clips, including idle, run and defeat. Their embedded cast names predate the native action controller. The baker instantiates the near hero in the shipped Godot project, verifies the controller's rig bindings, warms the standing pose, requests each action, triggers its actual release and captures all joint-local translations and quaternions up to 60 times per second on level ground. The muzzle is sampled at the last draw key. The resulting compressed motion cache occupies 169,032 bytes. Five native inputs are hash-checked before packaging either LOD. [Native pose capture](../../../../yuga-rust/tools/capture_rama_motion.gd) · [Cache and GLB packer](../../../../yuga-rust/tools/pack_rama.py) · [Portable cache](../../../../yuga-rust/assets/rama-motion.json.gz)

| Action | Draw state | Release state |
| --- | --- | --- |
| Kodanda | `draw` | `release` |
| Piercing Dawn | `piercing_draw` | `piercing_release` |
| Measured Step | `dash` | `dash_release` |
| Guardian Circle | `circle_draw` | `circle_release` |
| Dawn Volley | `volley_draw` | `volley_release` |

`active.motion` names the currently playing stage clip. `active.motion_phase_normalized` is elapsed time within that clip. At release the browser starts the new stage at zero. Each live projectile carries position, height, direction and a stable cast/index pair. The renderer derives the nocked shaft from the string and bow grip while winding up. Original artifact digests and per-stage errors are in the receipt. [Renderer](../../../../yuga-rust/web/scene.ts) · [Exact asset checks](RAMA-PORT-EVIDENCE.json)

The single-file browser build uses Rama's native far LOD, with 136,228 triangles, 13 materials, 17 images and all 164 bones. Adding ten clips to the existing nine produces a 22,144,960-byte GLB. The corresponding full-detail export occupies 37,293,088 bytes. Both keep every original material, primitive, skin, texture, animation definition and original BIN prefix. Two independent captures produced byte-identical compressed data. Duplicate far exports also matched.

## Verification and remaining work

The original Godot ability suite passed 85/85 checks. Nine Rust tests cover native timing and reload, cover before an enemy, six-target piercing, both teams, moving draw origin, explicit cancel, step distance, staggered arrows, ward ownership and healing, reset, and a live lane-unit hit through the public match API. The stress fixture ran two 3,600-tick simulations with 64 receivers. Each accepted 158 casts, produced 806 events, kept at most 96 history records and finished with an identical snapshot. [Native test suite](../../../tests/rama_ability_cases.gd) · [Rust tests](../../../../yuga-rust/src/rama.rs)

PlayCanvas 2.23.3 evaluated the ten exported far-LOD stage clips at all 254 authored sampling times. An independent Godot 4.6.3 capture supplied 41,656 expected global joint transforms from the near model. Maximum joint position difference was 0.000822 mm. The largest basis-column difference was 0.00000228. These checks cover neutral, forward-facing, level-ground attacks. Dynamic moving-draw leg layering, warm chained-draw entries, slope-specific foot locks, independent facial pose and pitch-dependent grip correction still belong to the native controller. A future browser blend/IK pass should use matching captures for those situations. [Playback verifier](../../../../yuga-rust/tools/check_hero_pose.mjs) · [Per-stage evidence](RAMA-PORT-EVIDENCE.json)

### Reproduce

Ordinary packaging needs Python 3 and the checked-in cache and source assets. Regenerating the authoritative poses requires the imported native Godot project. Cross-engine validation uses the repository's npm lockfile dependencies. Run the following from the repository root with a fresh working directory.

```sh
work=$(mktemp -d)
rust_game=games/yuga-rust
native=games/yuga-native
python3 "$rust_game/tools/pack_rama.py" --lod far "$work/rama.glb"
cargo test --locked --manifest-path "$rust_game/Cargo.toml" --lib rama::tests
godot --headless --path "$native" --import
godot --headless --path "$native" --script tests/rama_ability_cases.gd
godot --headless --path "$native" --script "$PWD/$rust_game/tools/capture_rama_motion.gd" -- "$work/capture.json" "$work/reference.json"
python3 "$rust_game/tools/pack_rama.py" --capture "$work/capture.json" --muzzles "$work/muzzles.json" "$work/rama-motion.json.gz"
cmp "$work/rama-motion.json.gz" "$rust_game/assets/rama-motion.json.gz"
cmp "$work/muzzles.json" "$rust_game/assets/rama-muzzles.json"
node "$rust_game/tools/check_hero_pose.mjs" "$work/rama.glb" "$work/reference.json"
```
