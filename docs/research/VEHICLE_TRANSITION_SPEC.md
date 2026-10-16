# Walk / drive transition specification

Status: **original design contract for ANDOLAN**; research observations verified, implementation tests must be cross-referenced to actual product test results. No reference-game runtime behavior or timing is claimed.

## Purpose and evidence

A player can walk to the compact car, enter one available driver seat, drive, stop and exit into clear space without losing camera/input control, spawning a second actor or taking another player's seat. The transition remains consistent for every client in the room.

Source basis: MIT Sketchbook at `62f4b7986fd1ce1e4f91daba89ef032c20a6ce55`, the seven files in [REFERENCES.md](../REFERENCES.md). The observed local implementation separates entry animation, physics activation, control transfer and occupant references. The REA occupancy trace was ambiguous/partial; it does not establish network authority. All multiplayer rules below are original requirements.

## Authoritative state

The server owns player mode, vehicle occupancy, transform, motion input and accepted revision. One player has one stable actor ID across walking and driving. One driver seat has zero or one owner. The two references must agree: `player.vehicleId === car.id` exactly when `car.driverId === player.id`. A seated character is represented by the same logical actor at the seat transform, not a second authoritative actor.

Minimum first-slice states are `onFoot` and `driving`. A future visual `entering`/`exiting` state may interpolate between them, but animation completion must not grant occupancy. If transitions become timed, reserve the seat on the server before animation and clear an expired reservation. The first slice may atomically change mode and animate only the presentation; it must not advertise cinematic entry animations if they do not exist.

## Inputs and acceptance

An enter intent contains a unique command ID and requested vehicle/seat; an exit intent contains a unique command ID. The server obtains player identity from the connected session, never from a client-selected role or occupant ID. Movement inputs are bounded finite numbers; client position, speed, reward, mission completion and occupancy assertions are not authoritative.

Original prototype tuning proposal: entry radius 3 m from a defined access point, exit speed threshold 2 m/s, and a 20 Hz server tick. These are **proposals**, not Sketchbook/GTA measurements. The implementation's shared constants are the final executable values and must be documented if different. Do not silently copy numbers from either reference.

| Current state / intent | Required server checks | Accepted effect | Rejection |
| --- | --- | --- | --- |
| On foot → enter | Known player, known vehicle, room membership, unoccupied seat, in range, allowed speed, valid movement state | Atomically bind player and seat; reset foot/throttle inputs; increment revision; emit accepted result | Invalid, occupied, too far, moving too fast or unavailable; no partial mutation |
| Driving → drive | Sender owns driver seat, finite bounded controls, current session | Advance server simulation; publish authoritative transform | Ignore/deny forged driver and malformed values |
| Driving → exit | Sender owns seat; speed allowed; safe exit position exists | Reset car input; atomically clear both references; put actor in clear space; publish mode and transform | Too fast or blocked exit; remain seated with a readable message |
| Any → duplicate command | Previously processed command within deduplication window | Return prior outcome or harmless no-op | Never perform a second transition or grant |
| Any → stale/disallowed intent | State no longer permits action | No state mutation | Current authoritative state accompanies rejection where useful |
| Driving → disconnect | Session is gone | Clear control input immediately; release seat and remove/safely park actor according to room policy | No unattended accelerating vehicle and no permanent seat lock |
| Rejoin | Server-issued room/session proof and current snapshot | Recover current state by supported room policy | A fresh connection is not automatically a persisted campaign or vehicle reclaim |

Receipt and processing order, not local animation order, decides simultaneous requests. At most one receives a driver grant. A client may predict a short visual movement, but must reconcile on rejection. Every rejected transition leaves the previous valid state intact.

## Presentation and collision

- While on foot the camera follows the actor; while driving it follows the car. Blend presentation without changing authority.
- Reset held actions on transition, tab blur, pause/open-menu and disconnect. One press should cause one entry/exit attempt; keyboard auto-repeat must not oscillate modes.
- The car and actor must not physically push each other while seated. Keep a single authoritative motion source.
- Choose the left access point if clear, otherwise right or another documented safe offset. Test candidates against static obstacles and room bounds. If none is clear, deny exit; do not place the player inside a wall.
- Recover from out-of-bounds states using the room's safe spawn/checkpoint rule. Recovery is explicit and must not duplicate cars or grant progress.
- Use a clear nearby interaction label, occupied message and stopped-car hint. Input focus inside a name field or modal must not drive the car.
- Reduced camera motion, steering assist and remappable controls are separate product requirements. Track them as implemented or pending, never infer them from this contract.

## Acceptance matrix

These are required checks, **not claimed passes**. Product tests must link command, commit/build, expected state and observed outcome.

| ID | Test | Observable result |
| --- | --- | --- |
| VT01 | Repeat walk → enter → drive → stop → exit → room ten times | One actor and car throughout; controls/camera usable after each cycle |
| VT02 | Two independent clients enter the same driver seat in the same server window | Exactly one occupant; both clients converge; loser remains on foot |
| VT03 | Replay accepted enter/exit command; resend after intervening state change | No second transition, duplicate grant or occupant corruption |
| VT04 | Request entry from outside range and forge another player/vehicle ownership | Server rejects; transforms and occupancy unchanged |
| VT05 | Disconnect driver while holding throttle | Input clears, seat becomes available by policy; surviving client sees same result |
| VT06 | Exit beside a wall; then block every exit candidate | Safe alternate used or rejection; never spawn inside collision |
| VT07 | Hold forward during transition; blur tab; reopen menu | No stuck foot motion or throttle; focus remains usable |
| VT08 | Enter/exit at speed boundaries, NaN/infinity controls and oversized payload | Defined rejection or bounded result; server remains responsive |
| VT09 | Delay snapshots and reconnect using supported flow | Authoritative occupancy converges; no duplicate actor; save continuity reported truthfully |
| VT10 | Third-person camera near walls on foot/in car; low graphics preset | No obstructed mandatory interactions; measured rendering results recorded separately |

Known limits: no reference runtime comparison, no recovered animation timing, no measured network delay budget, and no claim of passenger seats, reservation animations or durable rejoin until implemented and tested. A screenshot cannot establish VT02/05/09; use independent clients and server-observed state.
