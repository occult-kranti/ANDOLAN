# Hanuman, the Returning Leap

Hanuman is a close-range rescuer in YUGA’s standalone native practice court.
His low, sweeping mace gives him room to hold a front. The ward buys time,
the vault changes the angle of approach, and the tail answers someone trying
to follow. The mountain cast asks the player to choose a landing that serves
both allies and the attack. These are original gameplay interpretations of
the figure’s courage, service, strength and mountain-bearing exploits.

The supplied *Mythic 3D Hero Design Pipeline* describes a broad silhouette,
guard gestures, grounded counterplay and a plan for readable windup, travel and
release. Its Hanuman chapter on PDF pages 12–15, turnaround direction on page 28,
and courtyard sequence on page 35 informed this slice.
The existing Godot third-person camera, native practice clock, target receivers
and input actions determined what could be exercised in this build. The PDF’s
account, model-access and third-party claims are background material.

| Input | Action | Read and response | Practice tuning |
| --- | --- | --- | --- |
| LMB | **Vajra Gada** | Mace preparation and an amber frontal arc. Step back, cross behind or use stone cover. | 0.25 s preparation, 0.30 s recovery, 0.60 s cadence. 34 enemy damage at up to 3.5 m. |
| Q | **Vajra Kavacha** | Open-palm guard and a pale green fan. Allies use the marked side of the guard and keep a clear line. | 0.35 s preparation, 0.25 s recovery, 9 s cooldown. 48 shield for 3 s on the caster and eligible allies within the 5.5 m fan. |
| E | **Maruti Udayana** | A forward path shows the planned endpoint. The actor sweeps through the physical course and may stop earlier. | 0.20 s preparation, 0.45 s movement, 0.20 s recovery, 7 s cooldown. Up to 8.5 m with a collision-aware plan and no payload damage. |
| C | **Lanka Dahan** | The rear sector lights up before the tail sweeps. Step toward either flank or behind cover to break the lingering exposure. | 0.45 s preparation, 0.40 s recovery, 11 s cooldown. 28 enemy damage and up to 16 over 2 s inside the 5 m sector. |
| X | **Mountain Pulse** | The 7 m landing mark is fixed before release. Leave it or place cover between yourself and the landing. | 0.70 s preparation, 0.45 s travel, 0.50 s recovery, 30 s cooldown. A clear aim point within 14 m receives 65 enemy damage and up to 45 allied healing. |

Q shields through the existing status receiver. The forward fan limits which
other receivers benefit. The shield itself absorbs accepted damage from any
direction. C remains active independently of Hanuman once the cast has
released, so it can cover a retreat without blocking the next action. X
projects the pulse to the mark while Hanuman stays on the ground. Position,
health, team, vertical tolerance and cover are checked by authority at receipt
time. Shields and healing use existing caps.

## A short court sequence

1. **Approach.** Establish a clear three-quarter silhouette with the gada
   against the stone and leave enough space behind the tail. Step toward the
   first target and strike once so its health change can be read against the
   windup and contact.
2. **Protect.** Face an ally and use Vajra Kavacha. Keep both the hand and the
   translucent outline readable over the stone. Let a shield amount and the
   guarded audience speak for the action.
3. **Change angle.** Set up the vault route from an unobstructed face. Show the
   lower camera following the lift, then linger long enough to see how the
   feet return to support. Land near a new angle and turn the tail sector so
   one target remains inside and another is visibly outside.
4. **Deliver and recover.** Aim Mountain Pulse between the injured ally and an
   enemy target. Keep the edge of the landing mark visible through travel.
   The landing and the health receipts share an authority beat. Close by
   returning Hanuman to the ordinary grounded stance.

## Motion and effects coverage

Frame the Blender study as a series of cuts. Each action starts from its own
neutral pose so an edit can cover repositioning. At 30 fps, use these anchors
and retime the sampled clip around its contact phase. Keep the full body in
the clear frame through release, then show where the effect goes.

| Beat | Camera and contact | Effects to review |
| --- | --- | --- |
| Gada · frames 32–48 | Front three-quarter, `fire` at phase .26. Frame the right glove and mace handle together. | Read the half arc from the ground line. Add an ivory stroke on the swung side without covering hand contact. |
| Kavacha · frames 49–66 | Front three-quarter, `cast2` at phase .50. Show the open palm above the planted lead foot. | Let the forward fan establish allies’ selection. Keep the pale green shield lattice around the recipient as a separate beat. |
| Vault · frames 67–91 | Broadside, `cast1` at phase .08. Follow the parabola and hold the final step long enough to see support. | Wind marks the route between takeoff and the destination. The collision sweep can stop short of that destination. |
| Tail · frames 92–118 | Rear three-quarter, `tail_sweep` at phase .50. Include the space behind the hips and follow the tail after contact. | Two orange sheets rise inside the rear boundary. The low warm wash stays within the marked area through the lingering exposure. |
| Mountain · frames 119–168 | Grounded wide, `mountain_pulse` at phase .55. Keep Hanuman at one side of the landing circle. | The crest falls in roughly 14 frames from release to impact. The vertical break and floor ring start together at impact. |

The [runtime effect profile](../assets/design/hanuman-presentation.json) defines
the palettes, heights and spatial audio for the actual game. Use the original
idle, travel and contact frames to verify pacing in the game renderer. The
studio cuts can frame the same mechanics more clearly, especially the tail
field. They demonstrate animation and staging independently of game input.

## Authoring and verification

The [Hanuman profile](../assets/design/hanuman-ability-kit.json) defines the
slot order, geometry, tuning, colors and animation phase hints. The tail sweep
and mountain pulse use distinct planted clips. The vault reaches its early
launch pose at release, and the actor's sweep drives its flight. The kit accepts
one action at a time and runs on the actual 20 Hz practice signal. Up to three
bounded casts may exist concurrently so the ember field can outlive recovery.
The kit emits a start, release, payload and recovery before ending the effect.
The movement receipt reports the start of an accepted sweep. CharacterBody
motion determines the final position.

The ability tests use the actual courtyard target adapter, clock, geometry and
vitals. They assert once-only release, cooldown, cover, cap, cancellation and
receiver reset behavior. The separate rig tests own visual contact and actual
keyboard entry. Values are practice tuning. Shield parries, directional
damage absorption, transformed hitboxes, progression and competitive PvP
balance need their own implementations and tests.

```sh
godot --headless --path games/yuga-native --script res://tests/hanuman_combat_cases.gd
godot --headless --path games/yuga-native --script res://tests/hanuman_presentation_cases.gd
```
