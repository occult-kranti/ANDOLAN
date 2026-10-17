# R2-11 — Independent effect/action visibility review

**Source/event gate PASS; candidate action and blink/cancel image gate PENDING.**

Product: native YUGA. Branch `game/yuga-native-production`, source commit
`0437ea91edf6989ff78c1eeadb3661f4825b60f2`. This review adds evidence only.
No runtime/assets, shared files, imports, renders or commits were changed or run.
The capture owner R2-06 confirmed that new five-action originals and 36 adjacent
blink/draw/release/cancel frames remain queued at this checkpoint.

## Executed verification

The four existing headless Godot suites ran sequentially with `taskset -c 0,1`:
56 adversarial, 85 ability, 33 VFX quality and 72 ability-visual assertions,
**246 passed**, every exit code 0, every stderr empty. The visual suite is a
structural/event suite despite its name; it does not inspect rendered pixels.
The historical review's total of 236 is not reused: the current visual suite
contains 72 rather than 62 checks. `run.json` records complete command arrays,
durations, result hashes and before/after SHA-256 for all inspected runtime,
asset, shader and test inputs; those hashes were unchanged during execution.
Raw stdout, stderr and result JSON are retained beside this report.

Reproduction from `/workspace/ANDOLAN`:

```sh
python3 /workspace/scratch/visual-round2/role-11/run-review.py
python3 /workspace/scratch/visual-round2/role-11/audit-evidence.py
```

The independent receipt audit passes **93 checks**. It re-hashes the 11 R2-04
source pins, compares every retained event excerpt by generation/cast/event
identity against the original gameplay receipt, checks all five release,
recovery and end times, checks real damage against health/shield deltas, and
re-hashes 15 retained action stills. `source-and-event-review.json` preserves
the exact results, including damage receiver IDs and projectile indices.
These are current-source and retained-control checks, not candidate execution.

## Cancellation and timing conclusions

The effect consumer admits the existing five ability IDs; it retires owned
cast geometry immediately on accepted cancel/end. It rejects repeated release,
pre-release impact, stale sequence and older generation events. All five
`*_cancel_removes_every_owned_node` checks pass. The real ability suite also
passes cancellation before release with no projectile, ward ownership cleanup,
and retention of an existing ward when cancelling a separate windup.
The dedicated charge suite passes Piercing/Dawn Volley cancellation removal.
No new effects or alternate gameplay/cancellation path are introduced.

Source references: `scripts/rama_ability_effects.gd:92` (event consumer),
`scripts/rama_ability_kit.gd:181` (unreleased action cancellation),
`scripts/rama_motion.gd:261` (captured-pose cancel fade),
`scripts/player.gd:484` (the normal face update writer).

| Ability | Authority release | Authority recovery | End |
| --- | ---: | ---: | ---: |
| Kodanda | 0.20 s | 0.40 s | 1.15 s |
| Piercing Dawn | 0.65 s | 0.95 s | 1.70 s |
| Measured Step | 0.10 s | 0.35 s | 0.40 s |
| Guardian Circle | 0.55 s | 0.85 s | 5.35 s |
| Dawn Volley | 0.95 s | 1.50 s | 2.35 s |

These are retained 20 Hz authority receipt times; new images must be labelled
from their observed events. Kodanda's declared 0.18-second windup quantizes to
release 0.20, while ready/recovery is 0.40. Its motion recoil lasts 0.22 seconds
after release and then fades. The 0.16-second cancellation fade is presentation;
effects retire on the accepted cancel event.

Guardian's 4.5-second field expires at age **5.05**, before its 5.35 cleanup end.
Existing checks pass authoritative boundary/recipient removal, shield restoration
and stopped healing at expiry, including 30/60/120 Hz presentation update
orders. Reduced settings preserve authoritative boundaries and projectile
shafts. These CPU checks do not provide a new expiry or reduced-mode image verdict.

For the 36-frame fixture, 181 staged public face updates plus six 30 Hz samples
put nominal frame 5 at face clock 3.2166667, within the full-close plateau.
Piercing starts before frame 15 and cancels before frame 24 at local cast age
0.30, below its 0.65 release threshold. Frame 35 is 0.40 seconds after cancel,
beyond the fade. This arithmetic passes; actual ticks, clocks and events must
still be read from the capture. Staged preroll must retain `world_advanced=false`.

## Actual originals inspected

`reviewed-images.json` pins seven original PNGs inspected with `view_image`:
five retained ordinary gameplay controls (Kodanda windup; Piercing, Measured
Step, Guardian and Volley release) and R2 baseline courtyard three-quarter-left
day/night face views. The gameplay originals' hashes match their actual receipt.

The five ordinary views show distinct existing effects and clear rear head
silhouettes. Piercing's gold strokes flank the shoulders; Step's blue trails
sit mostly below the torso; Guardian's low turquoise arcs and outer boundary
are visible around the avatar; Volley's gold loop surrounds the head silhouette
and a blue ribbon crosses the upper back. The third-person rear camera and hair
hide the front face/neck. These images cannot accept candidate frontal occlusion,
blink closure, cancellation continuity, hit satisfaction or crowded-fight clarity.

The baseline closeups expose eyes, nose, mouth and neck. Day shows strong dark
nose/cheek shading and dotted edge artifacts near temple/neck. Night retains
face contour but flattens and darkens the facial planes. Neither view contains
an action/effect. They establish an available baseline, not candidate acceptance.

## Remaining image gate and next owner

R2-06 must supply five source-pinned late-windup originals (Kodanda 0.10,
Piercing 0.60, Step 0.05, Guardian 0.50, Volley 0.90 nominal authority seconds)
and the complete 36-frame sequence with the actual receipt. R2-11 then checks:

- Accepted runtime cast IDs and observed phase for each action; face/neck framing
  and effect overlap in each original, with ordinary effects on.
- All 36 adjacent originals and reported two-physics-tick spacing; actual full
  closure and reopening, recoil and neck continuity.
- Real Kodanda release; real Piercing cancel reason `round2_face_probe`; zero
  release/impact/receipts for the cancelled cast; action state empty after fade.
- Correct clock staging and sole normal face writer during the take; source
  identity matches the candidate being accepted.

R2-04's broader diagnostic-effects-off and ordinary-effects-on/ordinary-camera
comparisons remain distinct requested modes. A single closeup take, five
windup images, or retained R1 controls cannot silently close those wider gates.
The bounded take does not establish all-five temporal readability, Guardian's
full expiry, reduced/night/crowded action appearance, physical-GPU performance,
keyboard delivery, online integration or commercial graphics parity.

Next owners: R2-06 captures; R2-11 follows up on new originals/receipts; R2-14/root
integrate this PASS/PENDING split without promoting the pending image gate.
