# SIEGE-02 — original lane vehicle art

Source: `scripts/lane_vehicle_art.gd`, SHA-256 `c2962a3aab0bc6b6c819ef6fbdb77cad36e85a4066f2205f32d3b9748641aa2b`. The models, materials and procedural animation in this file are original YUGA work. No commercial models, textures, code, animation data or recordings were imported. The carved wood, brass, cloth, crown and pennant vocabulary continues the existing lane infantry style. These are invented fantasy vehicles, not historically authenticated Indian weapons or a commercial game's reconstructed units.

## Round 1: silhouette and integration contract

The cannon cart is low and compact, with a brass barrel, visible dark bore, wood trunnion cradle, powder chest, open spoked wheels and a small standard. The royal chariot is taller, with a crown-framed backboard, heavy horizontal bow, loaded bolt, tension cord and higher standard. Sun uses rust cloth and warm brass; Moon uses teal cloth and cool metal. Shared wood, rope and dark iron keep both teams in one material family.

`build(team: String, role: String) -> Dictionary` accepts `cannon_cart` and `royal_chariot`. Its dictionary contains `root`, `joints`, validity, rest transforms and wheel history. Preserve that complete dictionary when invoking `pose(art, role, time, moved, attack_time, hit_time, alive, dead_age)`. The integrating minion owns root translation, heading, collision, health and damage. Art modifies child joints only. Unknown roles or teams produce an inert root before material allocation.

Agreed collider radii are 0.82 m for cannon and 0.88 m for chariot. Weapon, recoil, banner and wheel geometry are bounded inside those footprints in the sampled moving, attacking and death poses. The chariot is lane siege artillery, not a jungle boss. The visual module creates no collision, particles, audio or projectile nodes.

## Round 2: implementation

Meshes and materials are cached. Custom wheel rims and spokes share one mesh per wheel size; bow limbs and cord are fixed meshes. Pennants are thin closed geometry with separated front/back surfaces. Wheel roll integrates travel from metres per 20 Hz simulation step and elapsed presentation time, stops when paused and resets on time rewind. Suspension motion affects the carriage while wheel contact stays on the lane plane.

Cannon attack time begins at 1.20 s and recoil begins at remaining 0.40 s, matching the agreed 0.80 s windup. Chariot begins at 1.00 s, draws the cord midpoint while keeping both bow tips attached, and recoils at remaining 0.45 s, matching 0.55 s windup. Recoil returns to rest. Death uses a contained carriage slump and weapon droop rather than the infantry sideways fall. Every pose resets its animated transforms before applying the current state; nonfinite input is rejected without changing the pose.

| Role | Mesh instances | Triangles | Total art nodes | Rest radius | Rest height |
| --- | ---: | ---: | ---: | ---: | ---: |
| Cannon cart | 27 | 2,112 | 35 | 0.796 m | 1.84 m |
| Royal chariot | 32 | 2,664 | 41 | 0.874 m | 2.36 m |

These are actual instantiated source-geometry counts, not GPU draw calls or frame-rate measurements. Both teams use the same geometry.

## Round 3: numerical stress and review

`tests/lane_vehicle_art_cases.gd` passes **48/48** checks. Evidence: `tests/evidence/lane-vehicle-art-cases.json`. Checks cover all role/team combinations, finite vertices/transforms, footprint and ground bounds, stable node counts, recoil timing and recovery, nonfinite rejection, huge finite inputs, root ownership, rewind/death restoration, 30 versus 60 Hz wheel integration, paused-clock stability, fixed cord endpoints during draw, invalid-team cache protection and cache reuse across 100 builds. Each role also completed 72,000 pose calls representing 20 simulated minutes, including repeated attacks and death/recovery cycles, without node growth or sampled ground penetration.

Reproduce from the repository root:

```sh
godot --headless --path games/yuga-native --script res://tests/lane_vehicle_art_cases.gd -- --report=/tmp/yuga-lane-vehicle-art.json
```

A first death-pose test exposed a cannon axle dipping 1.6 cm below the lane plane; the carriage slump was reduced and the fresh complete suite passes. That numerical correction does not substitute for visual review.

Actual siege-unit captures and integrated combat tests are owned by the coordinator/independent QA and remain separate from this art gate. No heavy render was launched by this task. The simple cached geometry provides recognizable vehicle silhouettes and bounded animation, but materials, sculpted detail, authored handling motion, damage states and effects still need production art work to approach the requested commercial visual target. No AAA-quality or complete-animation approval is claimed.
