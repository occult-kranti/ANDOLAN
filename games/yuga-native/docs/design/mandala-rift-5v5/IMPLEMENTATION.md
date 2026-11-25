# Mandala Rift · development notes

## Geometry and sightlines

The [route graph](map-spec.json) is a symmetric planning model. Work in metres, with Sun at negative Z and Moon at positive Z. Its 5 m/s walking estimate comes from the current Rust hero tests, while water and fold costs are proposals. Place protective spawn structures, two plant volumes, identifiable cover and all three connected lanes in an in-engine graybox. Neither the generated illustration nor the line diagram is a collision mesh.

Target at least two independent approaches to each site, a continuous dry rotation, and clear exits from every jungle pocket. Begin with the existing 8 m lane clearance as a comparison, not an unconditional rule: measure hero radius, ability footprints and team stacking in real play. Test simultaneous 5v5 movement and both directions at every doorway, slope and high/low route. List every long sightline from spawn, entrances, site corners and ramp tops; add cover only after observing the actual shoulder camera. Revisit the current 7 m Mountain Pulse radius where it can dominate an 8 m lane.

## Folded-space contract

The proposed first version is two **bidirectional topological shortcuts**, not a claim of a curved non-Euclidean physics simulation. A small temple antechamber and a visually larger stepped-sanctuary interior create the impossible-space impression. Keep the gameplay world finite. The southern and northern pairs are mirrored; any team may use either pair. The linked doors have consistent symbols, sounds and a visible destination label. A conventional corridor connects the same regions if a player chooses not to use a fold.

Proposed transit is a 24-tick (1.2 s) held channel followed by a 6-tick (0.3 s) commit at the current 20 Hz authority rate, matching the graph's 1.5 s abstract cost. Release, damage, knockout or leaving the entrance cancels the channel. A server decides completion and checks the destination capsule. If blocked, the player stays on the source side with a clear failure cue; never place two characters in the same capsule. Define same-tick contention by a stable seat or player ID ordering. Apply lethal damage before transfer on the same tick. A successful exit has a short per-player re-entry cooldown to prevent ping-pong, without disabling the alternative walking route.

Use authored transforms from entrance-local coordinates to destination-local coordinates. For a facing-door pair, the initial mathematical proposal is `T_exit · R_y(π) · inverse(T_entry)` for position and the corresponding rotation for facing, aim and horizontal velocity. Do not scale the player or alter movement speed. Verify the matrix convention in the target engine before implementation; use inverse pairs and round-trip tests, including elevated and edge positions. These are design equations, not code currently integrated with YUGA's authority.

First competitive version: opaque gates; hitscan, arrows, damaging zones, healing fields and sight queries stop at the membrane. A channel cannot start while airborne. Existing deployables remain in their origin region. A crossing ends targeting/dragging cleanly and emits one departure/arrival event with server tick and portal ID. The minimap labels the destination and only shows enemy information already authorized by the match's visibility rules. If spectator, replay or reconnect arrives mid-channel, reconstruct from the same server state. Client prediction may interpolate visuals, but authority owns collision, entry/exit and cooldown.

Possible later visual tests include bounded offscreen portal views and a separate interior scene. Camera recursion, clip planes, overlapping render layers and portal visibility can create GPU cost or visual leaks; profile and test each, and preserve an opaque fallback. Do not recursively render arbitrary portals or assume a visual portal establishes a correct physics connection.

## Water and jungle

Prototype ankle-to-knee shallow water as a floor region, initially 0.15–0.45 m deep. It does not imply swimming, drowning or buoyant combat. The graph models water movement at 85% of dry walking speed; apply any actual multiplier equally to teams in the authoritative movement system, make it legible, and test abilities, evasion, knockback, entering/leaving and packet delay. Effects, hits and targeting use the same valid gameplay surfaces; water does not secretly block projectiles. Provide a dry route with a comparable purpose and measure whether the speed penalty discourages its use.

Use readable ripples and footstep audio with subtitles. Restrict reflective effects and transparent layering until the target GPU is profiled. Vegetation frames routes but must not create one-way sightlines or conceal aim indicators. Water color, particle density and reduced-motion behavior require accessibility checks.

## Reuse without minions

The existing [world asset library](../../../art/reuse-library/README.md) and [world landmark study](../../../art/world-landmark-study/README.md) contain reusable temple, courtyard, rock and nature sources with provenance. Start with those meshes and materials for a candidate graybox/art pass, and compare collision to the map before promotion. Review the rejected shoreline layouts in the [world panel](../../research/world-panel-2026/README.md); their rock placement failed actual-camera review.

Keep soldier rigs, animation clips, armor, weapons, sound and the Rust wave implementation versioned. Candidate future reuse includes a hero's armor or a brief, non-targetable ability echo and decorative stone reliefs. Any damaging summon, independent AI or reusable character needs a new design and authority review. The current request pauses the wave-minion role; this proposal does not add autonomous jungle minions or treat recycled NPCs as combatants.

## Acceptance matrix

| Area | Required evidence before promotion |
| --- | --- |
| 5v5 baseline | Ten unique seats, five per team, no wave units, hero KO scoring and deterministic simultaneous deaths; reconnect/disconnect, input limits and a full match result. |
| Objective rounds | Plant/defuse interruption, expiration, both simultaneous-wipe cases, dropped carrier, side switch, overtime, late join, spectator visibility and a frozen resolved round. |
| Fold links | Both directions and teams; 30-tick channel, cancelled or blocked exit, simultaneous entrants, damage on the completion tick, no projectile or line-of-sight leakage, aim/velocity transform, pause, respawn and reconnect. |
| Water | All hero movement and ability boundaries at shallow-water edges, equal team timing, aim/telegraph visibility, reduced effects, dry-route accessibility and audible direction. |
| Layout | Measured spawn-to-site routes, on-screen sightlines, collision/capsule clearance, escape paths, upper/lower floor support and both-team camera captures. Graph symmetry alone is insufficient. |
| Art and performance | Provenance and notices, runtime LODs, ten visible heroes and overlapping effects, p50/p95/p99 frame time, draw calls and memory on the target laptop; human readability and player feedback. |

The current Rust world uses a ground-plane authority with limited authored collision. Raised platforms, multi-level navigation, folded interiors and water modifiers require explicit new authority and rendering work. Historical Godot and browser builds are separate and must not be relabeled as supporting these features.
