# Triad civic relays — original native art

The three relays present local ownership without adding another bright circular warning. Their ground markings are flat broken corners and rectangular progress inlays. The solid stations sit off the lane: Reed at x=-34, Lotus at x=-6 and Sky at x=34, all z=4. Capture centres remain x=-40/0/40 at z=0 with gameplay radius 5 supplied by the session authority.

Source: `scripts/relay_art.gd`, SHA-256 `32e42d32a4a1e52414c2e274d076c1aac4531fd10084b052082f0cc08cd31cb6`. Work began from native branch checkpoint `af9dae258936a2fc1854587736dd847ef1c0d604`; other workers own session/world integration.

## Round 1 — form and readability contract

Each station is a civic machine on a stepped sandstone base. Reed has three vertical blades and stems, Lotus has six radial brass petals, and Sky has three angular cloth vanes. A quiet rotating mechanism and warm lantern windows give a day/night presence. The forms are invented, with no sacred deity miniature or authenticated historical machinery claim.

Ownership uses colour and silhouette: neutral diamond, warm Sun star and cool Moon crescent. Raised symbols face both directions along the lane. The current owner's symbol remains stable during an enemy capture. Two rows of eight rectangular inlays show capture progress using the capturing team's colour. Contested stations reveal both warm/cool side flags; they remain steady, with slow cloth sway, rather than flashing or spawning particles.

Paving corners extend only about 4.72 m from each control centre. The decorative progress surfaces are at most 3.4 cm above the ground and have no collider. There is no torus, expanding ring or large emissive disc. Lantern windows are emissive material accents; the module adds no lights and consumes none of the world's practical-light budget.

## Round 2 — implementation and authority boundary

`relay_art.gd` extends `Node3D`. Add it to the scene tree at the world origin, then call:

```gdscript
art.setup() # idempotent; builds all three sites once
art.set_states([
    {"id":0,"owner":"neutral","contested":false,"progress":0.0,"capture_team":"neutral"},
    {"id":1,"owner":"sun","contested":false,"progress":0.5,"capture_team":"moon"},
    {"id":2,"owner":"moon","contested":true,"progress":1.0,"capture_team":"sun"}
])
var boxes = art.collision_boxes()
var diagnostics = art.report()
```

`set_states` requires three unique integer ids 0–2. Owner/capture team are `neutral`, `sun` or `moon`; progress must be a finite number 0–1; contested must be a Boolean. Invalid arrays are rejected atomically. Input ordering does not matter. State application changes existing visibility/material references only. Ownership, capture timing, rewards and damage remain session responsibilities.

`reset()` restores neutral presentation and the animation clock. Optional `set_night_blend(0..1)` adjusts the existing lantern material from day to night; nonfinite values are rejected. Processing is PAUSABLE and also checks disabled ancestors, so either disabling this module or its owning session freezes animation. No audio or particles are created.

Each of the three `relay_plinth` StaticBody3D bodies uses collision layer 1/mask 0 and three box shapes matching the visible steps exactly:

| Step | Size X/Y/Z, metres | Base Y |
| --- | --- | ---: |
| Base | 1.50 /0.28 /1.50 | 0.00 |
| Middle | 1.16 /0.15 /1.16 | 0.28 |
| Top | 0.88 /0.13 /0.88 | 0.43 |

`collision_boxes()` returns the nine actual world AABBs as `{position: Vector3, size: Vector3}`, with position at base centre. The integration owner appends them to army collision/LOS data after army configuration. The maximum station half-width is 0.75 m: the closest solid edge is 5.25 m from its lane centre, outside the lane's 4 m clear half-width. The nearest Z edge is 3.25 m from the cross-mid route at z=0, outside that route's 2 m clear half-width. All rotating decoration stays within that same horizontal footprint; the station reaches 2.45 m high. Upper ornaments are decorative and non-solid. Camera/player collision follows the layer 1 stepped plinths, rather than invisible tall columns.

## Round 3 — focused verification

Command run from the repository root, without editor/import/render/packaging:

```sh
godot --headless --path games/yuga-native --script res://tools/test-relay-art.gd -- --report=/workspace/scratch/yuga-triad/relay-art-route-correction.json
```

Result: **28/28 checks passed**. The actual instantiated module has 214 nodes, 156 mesh instances, 23 cached meshes, 13 materials, 3 StaticBody3D bodies and 9 matching collision shapes. All geometry totals 3,912 source triangles, including hidden alternative ownership symbols. These are source/scene counts, not GPU draw calls or measured frame rate.

The checks cover exact collider/visible-step correspondence, real physics rays hitting the 0.56 m top step, clear corridors for all three canonical lane polylines and both rotation routes, ground-surface heights/radius, 20 rotor phases per station, ownership/capture separation, distinct symbols, invalid-state rejection, 100 repeated setups, 10,000 state/night updates without node/mesh/material growth, reset, pause/overview gating and 72,000 animation calls representing 20 simulated minutes with finite transforms.

A world integration check caught the initial z=0 plinth placement blocking the cross-mid rotation route. All stations moved to z=4 while control paving stayed at z=0. The owner suite now reads every canonical lane/rotation route from the staged manifest, and includes a counterexample proving the former z=0 placement is rejected.

Independent full-world capsule/camera/army tests and actual day/night/TPS captures belong to the integration/QA owners. No relay image has been generated or approved by this task. Paving visibility at grazing camera angles, symbol legibility during crowded combat and the visual cost of 156 mesh instances require actual render review. Geometry and materials remain a restrained procedural prototype, below the requested commercial game's production-art target.

Provenance: `NOTICE/TRIAD-RELAYS.txt`. No imported commercial game assets or reverse-engineered asset data are used.
