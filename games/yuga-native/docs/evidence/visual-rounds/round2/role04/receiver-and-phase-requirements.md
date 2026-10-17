# R2-04 · Facial action-context fixture handoff

Native YUGA, branch `game/yuga-native-production`, frozen source
`0437ea91edf6989ff78c1eeadb3661f4825b60f2`. The source-checked fixture is complete;
new Round 2 capture and deformation review belong to R2-06/R2-05. No runtime or
asset was edited, no import/render was run, and no new pixels were reviewed here.

`face-action-fixtures.json` is the consumable contract. `source-checks.json`
records 38 passing static checks, including nine exact runtime/asset matches to
the accepted action film, all five real release/receiver/end event streams and
15 original accepted still hashes. The scalar timing checks establish a valid
schedule; they do not establish that the new harness executed it.

## Bounded capture request

Capture one late-windup face/neck original for each of `kodanda`,
`piercing_dawn`, `measured_step`, `guardian_circle`, and `dawn_volley`, then the
36 adjacent-frame blink/draw/release/cancel sequence. Use the JSON
`minimal_round2_capture_request`. Its other event/reduced/expiry entries are
available as sparse follow-on probes; a new 363-frame film is not required.

Use `scene.rama_runtime.cast_ability(id)` and its returned accepted cast ID;
subscribe to `scene.rama_runtime.combat_event`. This is an actual world-runtime
request, not proof of physical keyboard/mouse delivery. `request_action()` or a
manually sampled clip alone is pose evidence and must not be called a cast.

| Ability | Late draw authority age | Release age | Authority ready/recovery | Normal end | Existing motion clips |
| --- | ---: | ---: | ---: | ---: | --- |
| Kodanda | 0.10 | 0.20 | 0.40 | 1.15 | draw / release; ready_draw only if warm bow |
| Piercing Dawn | 0.60 | 0.65 | 0.95 | 1.70 | piercing_draw / piercing_release |
| Measured Step | 0.05 | 0.10 | 0.35 | 0.40 | dash / dash |
| Guardian Circle | 0.50 | 0.55 | 0.85 | 5.35 | circle_draw / circle_release |
| Dawn Volley | 0.90 | 0.95 | 1.50 | 2.35 | volley_draw / volley_release |

These are seconds on the 20 Hz authority clock, not image timestamps. The
60 Hz motion controller begins recoil at the actual release event and fades
for 0.16 seconds after its declared recovery duration. Kodanda's ready event
at age 0.40 and its presentation recovery ending about release + 0.22 are
intentionally distinct. Select each image from the event/report state.

The compact 30 Hz sequence naturally prerolls 181 physics ticks after face
reset: blink clock 3.0166667. Issue Kodanda before capture frame 0; issue
Piercing Dawn before frame 15; cancel its real windup before frame 24 via
`kit.cancel_windup("round2_face_probe")`. After each pair of physics ticks,
record the next framebuffer. Frame 5 then samples blink clock 3.2166667,
inside the full-close plateau 3.205–3.230. Verify the actual report: async
startup or clock alignment must not be assumed. Frame 35 is at local 1.2 s,
well after the 0.16 s cancel fade. The renderer may instead stage the181 updates through the same public
`update_facial(1.0/60.0,{alive:true,paused:false,effort:0.0})` while the world
is paused, with `world_advanced=false`, count and before/after face reports
explicitly recorded. That preparation is a staged facial clock, not naturally
elapsed gameplay. All36 captured frames then use normal player updates only.
This direct cancellation probe exercises
the existing authority API; it is not a newly assigned player cancel key.

## Receiver truth and ordinary context

A projectile hit requires `kind=impact`, `reason=unit`, and a damage receipt
with the same generation/cast/event identity, unit ID, positive damage and
matching health/shield delta. An impact on `wall` or `range` has empty receipts
and never establishes a target hit. The accepted control has Kodanda damage28
at age0.30; Piercing damage70 at0.80/0.85/0.90; and Dawn Volley damage82 on
projectile indices0/1/2 at1.20/1.30/1.40. New positions may change hit ages:
match the observed receipt, not a historical timestamp.

Measured Step has `reason=movement_accepted`, an accepted destination, and
subsequent CharacterBody displacement; it has no damage receipt. Guardian
Circle uses `kind=guardian` receipts for shield entry/healing, including
`receiver_kind=hero, unit_id=0` for Rama. Its field expires at authority age
5.05; the `end` at5.35 is a presentation cleanup tail. Observe5.00/5.05/5.10
for field/boundary/HUD expiry claims.

Retain the existing real commander receiver staging and begin-geometry
alignment in `tools/capture-rama-gameplay.gd`. Do not fabricate impacts or
manually reduce receiver health to establish an arrow hit. Record receiver
snapshots and `generation, cast_id, event_seq` with any hit claim.

Diagnostic effects-off means only hiding the existing `rama_effects` Node3D
in the isolated capture harness while its event/update lifecycle continues.
Restore its previous visibility before ordinary views. Do not suspend effects,
disconnect authority, or modify warning geometry/timing. Reduced effects are
an existing distinct mode: `set_options({reduced_effects:true,
reduced_motion:true})` keeps the effect root visible; restore both prior flags.

The ordinary view uses `scene.player.camera`, visible UI and normal effects,
with no added portrait light. Review face/neck detail in the JSON head-anchored
32-degree cameras; a closeup alone does not establish normal gameplay or
crowded-fight readability. The five ordinary accepted film anchors are retained
controls, not candidate acceptance. Exact source equality is recorded for their
ability, runtime, motion, face, player, effect, hero and motion-library inputs.

## Deformation handoff

R2-05 and R2-10 should read `player.rama_face.report()` alongside
`player.rama_motion.diagnostics()`, and inspect `head`, `neck01`, `neck02`,
`neck03`, and the aimed shoulder frame `spine03`. Runtime aim is supplied by
normal player update with pitch -0.25 (Guardian -0.55) and existing yaw PI;
never author a second skeleton/face writer to manufacture an aimed frame.

The existing combined expression is blink plus smoothed exertion:
`max(blink, effort*0.14)`, equal on both lids. Windup/hold requests effort1,
recovery0.35, and other stages0. It has no authored brow/jaw/gaze expression.
If half-correctives exist, closure weight w maps to full `max(0,2w-1)` and
half `1-abs(2w-1)`; preserve all four names and ordering. Inspect adjacent
closing, closed, reopening, recoil and cancellation frames for eye penetration,
boundary gaps and neck pops. Separate numerical pause/reset/teleport checks
must retain a unique face writer and deterministic clock/weight resets.

The existing rapid-reversal body defect remains outside these facial fixtures.
The mythology reference MY-02 supports controlled draw/readable release as an
art brief; exact powers, timelines and native effects remain game inventions.

Reproduction command for this packet:
`python3 /workspace/scratch/visual-round2/role-04/build-fixtures.py`.
Scratch contains identical JSON copies and the packet generator; durable
fixture/check/requirement artifacts live beside this file. Next owners are
R2-06 for actual capture and R2-05/R2-10/R2-11 for their scoped review.
