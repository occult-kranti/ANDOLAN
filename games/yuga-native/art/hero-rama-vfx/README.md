# Rama solar/quill VFX candidate

Role 05, round 1–2; source starting point `1ab1f5e330d256a6ffb6a5706a07f2ff8c3bbb0e`.
This is an original procedural geometry/shader change to the existing event-driven
Rama effects. It adds no commercial assets or dependencies. The released script
and shader are preserved in `history/released-baseline/` for source comparisons.

The accepted released gameplay windups for Piercing Dawn and Dawn Volley and the
low-angle Volley release were opened before editing. Their broad pale filaments
were generic and weak against the warm paving; the new design narrows the forms
and introduces an indigo echo against gold/ivory solar energy. The accepted
Guardian frames 270/271 were also opened to preserve their exact authority-driven
boundary/recipient retirement behavior.

Piercing Dawn gathers an incomplete three-segment solar seal and two narrow
curves at the nock. Dawn Volley gathers three separated sun-blades, with fine
detached rays that remain near the caster and never impersonate unreleased
projectiles. Existing accepted projectile geometry controls the actual arrows.
Their shaft/quill is visible in crossed orientations, and a narrow indigo wake
leaves a cleaner warm/cool silhouette. Accepted contacts use short radial
filaments and two open arcs inside the same recycled bloom mesh.

The existing mesh-node ownership and caps remain twelve casts/eighteen contact
objects. There are no added lights, particle nodes, texture dependencies, camera
shake, screen effects or sound voices. Subframe arrow transforms update smoothly;
arrow-wake mesh rebuilding now shares the existing 30 Hz geometry cadence.
Reduced effects removes the secondary wake as well as the secondary contours;
reduced motion freezes decorative rotations but preserves actual travel.

Runtime ownership is `scripts/rama_ability_effects.gd` and
`shaders/rama_ribbon.gdshader`. Authority, tuning, vitals, HUD and the capture tools
are unchanged. The new `tests/rama_vfx_quality_cases.gd` adds presentation
counterexamples to the existing combat and hero integration regressions.

Round 2 execution on Godot 4.6.3: new VFX component **33/33**, unchanged ability
suite **85/85**, and unchanged hero integration **138/138** passed, each exit 0.
The existing equal-time 30/60/120 Hz integration checks reported zero mesh-vertex
and transform disagreement. Guardian remained live through authority age 5.00 s
and removed its boundary/recipients with the normal HUD update at 5.05 s. The
source-pinned reports and full process logs are in
`docs/evidence/rama-quality/vfx/round2/`. These were headless checks, without an
asset import or a heavy renderer.

The actual post-change same-camera near/far/day/night and crowded-scene review is
pending the shared renderer slot and the current hero/face/motion integration.
Finite geometry, passing counts, or the design description do not establish
readability, visual finish, real-GPU performance or Deadlock quality.
