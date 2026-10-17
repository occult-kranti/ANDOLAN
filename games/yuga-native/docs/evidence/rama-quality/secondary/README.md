# Rama bounded secondary motion component

Status: component verified; actual hero binding and native rendered review remain
pending. This is a procedural motion candidate toward the hero slice, not accepted
physical cloth, hair simulation, or Deadlock-quality art.

## Contract and integration

`scripts/rama_secondary_motion.gd` is a plain `Node`; it never changes a bone,
animation, imported mesh, skin, LOD, movement, collision, resource, or combat rule.
Configure once against the complete `HeroVisual`, after the existing sole Rama
skeleton modifier is configured. The node must be retained by the player:

```gdscript
const Secondary = preload("res://scripts/rama_secondary_motion.gd")
var rama_secondary = Secondary.new()
visual.add_child(rama_secondary)
if not rama_secondary.configure(visual):
    rama_secondary.queue_free()
    rama_secondary = null
```

Call `update_secondary(delta, state)` from the existing motion update using actual
movement. State fields are `local_velocity` (visual basis inverse × world velocity),
`position` (actual global position), `yaw` (visual global yaw), `grounded`, `alive`,
`paused`, `reduced_motion` and optional `reset`. These are presentation inputs,
never authority outputs. The component has no autonomous process callback.

Call `reset(reason)` from the existing player reset path. Supply actual death state
to `alive`; the transition to death or respawn clears inherited inertia. Pause
holds positions, velocities, clock and previous-input baseline exactly. A large
teleport clears inertia; an invalid/long delta resets without catch-up. Removal
from the tree restores its own surface overrides.

The artist authors white vertex RGB and a linear alpha motion weight, preserving
opaque glTF material alpha modes. Blue trailing mantle and its gold trim share one
continuous field; fitted chest/waist panels, jewelry and fixed edges stay zero.
Hair clumps fade from fixed roots to free tips; scalp and brows stay zero. The
component rejects missing masks, colored RGB or unsupported material features.
Only `Cobalt handwoven silk`, `Cobalt lotus brocade`, `Worked warm gold` and `Swept black hair` receive
per-instance overrides. Bow leather and all other materials retain their resources.
No runtime mesh copy discards imported LODs. A small per-instance culling margin
covers the maximum shader displacement and is restored when unbound.

`shaders/rama_secondary_cloth.gdshader` samples the imported albedo, metallic,
roughness and normal textures with original factors, normal scale and channel
selectors. It uses no TIME, opacity effect, particles or lights. Unsupported
material lighting/features/UV changes are rejected rather than flattened.

Forward+ compute skinning precedes custom vertex code. The shader therefore adds
its bounded offset to the already posed local vertex, using an authored alpha
identity that persists across poses. The offset is converted from hero space into
each mesh's basis. The exact Godot 4.6.3 source URLs and read hashes are recorded in
[`source-reading.json`](source-reading.json).

## Executed verification

```sh
LP_NUM_THREADS=2 godot --headless --path games/yuga-native \
  --script res://tests/rama_secondary_motion_cases.gd -- \
  --report=/tmp/rama-secondary-component-r4.json
```

Final result: **42/42 component checks passed**, exit 0. The synthetic fixture
contains genuine ArrayMesh colors, material resources and per-instance overrides.
It checks shared-resource preservation, channel/factor/texture transfer, fixed
anchors, shared hem displacement, coordinate transforms, steady travel response,
pause/resume, death/respawn, reset, teleport, reduced motion, invalid types/numbers,
huge finite yaw and unsupported lighting-mode rejection.

Constant-target movement/turn responses at 30/60/120 Hz agree within 0.000001 m.
The maximum measured constant-turn difference was 0.0000000084 m. A three-second
varying movement/yaw study compares 90 identical sample times: maximum cloth
difference is 0.421 mm at 30 versus 120 Hz and 0.140 mm at 60 versus 120 Hz, against
a stated 2 mm tolerance. Exact equivalence is claimed only for constant targets.
The 2,400 adversarial varying-step/speed/turn/airborne samples remained finite;
maximum observed cloth/hair offset was 53.1/12.6 mm under 75/18 mm hard caps.

[`component-r4.json`](component-r4.json) pins the tested sources. Earlier r1/r2/r3
reports are preserved with their own source hashes. Independent QA read the
component and initial reports; its overflow and material-mode counterexamples
produced the two corrections above. A source-read review is distinct from an
independent engine execution or rendered approval.

The artist's actual mask validator subsequently found that a trailing gold-pattern
border uses `Cobalt lotus brocade`. The fourth material now shares the identical
cloth displacement; otherwise the border would detach from the moving mantle.

## Remaining acceptance

1. Bind the artist's actual semantic-mask candidate and inspect actual imported
   material values and alpha modes. Do not silently enable the effect on an
   unmasked historical hero.
2. Capture same-camera/light/material animation A/B. Review continuous turns,
   starts/stops, all bow/action contacts, flight, pause, death, reset and teleport.
   Verify attached edges and gold trim at actual gameplay distance and close range.
3. Rerun existing motion/contact/traversal and gameplay tests after integration.
   Component math alone cannot establish surface intersections or hand contact.

There is no collision/self-collision, wind field, strand physics, multi-segment
cloth solve, force reaction, or secondary normal/tangent recomputation. Original
normal maps and posed tangent frames remain; large bending would need a richer
normal treatment. The conservative displacement limits are deliberate. No actual
shader render, consumer-GPU profiling or production art approval is claimed here.
