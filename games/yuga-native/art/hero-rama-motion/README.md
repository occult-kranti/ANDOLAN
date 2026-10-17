# Original Rama motion library and controller

The runtime library is `assets/animations/rama_hero_motion.tres`; `scripts/rama_motion.gd`
is its single full-body `SkeletonModifier3D`. The controller replaces the two previous
carry/traversal overlays for Rama. `player.gd` and gameplay remain integration-owned.

## Rebuild

From repository root, after the original hero has a current Godot import:

```sh
godot --headless --path games/yuga-native --script res://art/hero-rama-motion/build_library.gd
godot --headless --path games/yuga-native --script res://tests/rama_motion_cases.gd -- --report=/absolute/new/motion.json
```

The fixture defaults to the new `rama-hero.glb`; use `--asset=res://assets/heroes/rama-production.glb` only for an explicitly historical comparison.

The builder reads the original production hero's exact 164-bone rest rig and the
project's authored finger-closure rotations. All body trajectories, split-limb IK,
action curves, contact correction, and runtime layering here are original code.
There is **no Godot TPS motion or external animation asset in this library**. Existing
MakeHuman/CC0 and project asset provenance still applies to the underlying anatomy;
see `NOTICE/ASSET-NOTICE.md`. The original generator in
`games/yuga/art/pipeline/animations.py` informed the rig axis and four-segment limb
contract. It is project source, not a new outside dependency.

The 23 editable, named clips are idle, walk, run, sprint, aim, draw, ready_draw, release,
piercing_draw/release, circle_draw/release, volley_draw/release, jump, fall, land,
dash, flight, grapple, hit, death, and respawn. The builder removes constant rest
channels, keeping the text AnimationLibrary readable and compact. A new rig needs
explicit rest/bind compatibility before use; a matching bone count alone is not
that compatibility proof.

## Runtime API and authority

- `configure(visual, animator) -> bool` validates the rig, attaches itself and pauses
  the old AnimationPlayer. Do not also attach `hero_pose` or `traversal_pose`.
- `update_motion(delta, state) -> bool` accepts world `velocity`, model-space
  `local_velocity`, `grounded`, `traversal` (`ground/flight/grapple`), `aim_pitch`,
  `aim_yaw`, `aiming`, `dash`, and world `floor_y`. Inputs must be finite; physics
  steps are in `(0,.1]`. Presentation never modifies CharacterBody velocity.
- `request_action(id, windup, recovery) -> bool` begins a presentation for `kodanda`,
  `piercing_dawn`, `measured_step`, `guardian_circle`, `dawn_volley`, `hit`, `death`,
  or `respawn`. End windup holds until authority responds.
- `release_action(id) -> bool` accepts precisely one matching release, starts
  followthrough, and hides the nocked arrow. It emits no projectile, damage or cue.
- `cancel_action(reason)` fades the actual interrupted pose and immediately hides
  its arrow. `cancel(reason)` resets action/phase/aim/contact state idempotently.
- `socket_global(name)` returns the last evaluated world transform for `bow_grip`,
  `string_nock`, `draw_hand`, `arrow_muzzle`, or `head`.
- `evaluate_pose()` is the immediate deterministic entry for headless fixtures;
  ordinary gameplay uses the SkeletonModifier callback.
- `diagnostics()` reports action stage/phase, finite state, foot locks, exact socket
  contact error, and release/cancel counts. These are diagnostics, not authority.

Lower-body gait continues during moving bow/circle/volley actions. Stationary
piercing, circle and volley actions use authored planted poses; step and reactions
own full-body posing. State changes blend from the last evaluated pose, rapid retriggers
start from recovery, aim smoothing is exponential, and gait phase advances by traveled
speed/stride distance. The spine aim rotation preserves both arms and string contacts.
The string meets the actual posed draw-hand socket while held. Support feet lock in
world coordinates; pelvis compression accommodates anatomical reach. Sharp turns or
teleports replant instead of dragging the gameplay root. Side motion uses a dedicated
short support arc and low-clearance shuffle, with a distance-driven 1.6 m cycle,
rather than rotating the long forward stride through the opposite leg. A steady
4 m/s side-support test also rejects mid-stance replants.

## Render validation

Only one heavy renderer is allowed at a time; obtain the coordinator's slot first.

```sh
python3 games/yuga-native/art/hero-rama-motion/run_capture.py --output /absolute/new/capture --display 145 --asset=res://assets/heroes/rama-hero.glb --full
```

The staged capture translates the hero over stationary floor ticks, samples all
major motion states, and preserves source/import/frame hashes. `--side` runs both
sideways directions, walking and stops; `--full` also includes three rapid aimed
primary draws and hit/death/respawn at runtime reaction timing. `--shader-cache`
can point to an earlier capture's XDG cache parent to reuse only Mesa shader caches. It is a real Forward+
render, not a measurement of hardware FPS or a substitute for gameplay input review.
The first old-hero capture `/tmp/rama-motion-render-r1` is rejected: native foot axes
were mistaken for sole-forward axes, leaving toes raised. The corrected controller
preserves the foot rest orientation and verifies actual skinned sole/finger vertices.
The subsequent R6 take `/tmp/rama-motion-render-r2` exposed a separate cloth defect
at frames 97 and 105: the front ivory sheet formed a broad triangular fan with
self-overlap while strafing. Its nearest-anatomy leg weights and the former crossed
side stride required separate art and motion corrections. Both failed captures
remain preserved. See `REVIEW.md` for the final correction evidence and limits.
