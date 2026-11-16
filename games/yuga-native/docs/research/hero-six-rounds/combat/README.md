# Rama combat and motion handoff

Task **YUGA-HERO-6R**, native desktop/offline. Base source
`7162b5d0b666e4422b0bc73100e1fba947d3323f`, branch `work/yuga-studio`.
This packet changes the existing playable Rama. It does not add another hero,
change damage/timing, or establish finished commercial-game graphics.

## Implemented and verified

**Dawn Volley warning rhythm:** the three locked ground lanes now retire one
at a time on their actual accepted projectile pulses, instead of all vanishing
at the first release. Two-tone strokes improve contrast on bright/dark floors;
their outer edges match the projectile sweep. The primary shot has no added
ground clutter. Reduced effects/motion retain essential warnings. No shader
clock can dismiss a pending lane.

**Power preparation:** Piercing Dawn and Dawn Volley reuse the existing
`ready_draw` arm, finger and string channels while retaining their distinct
torso and planted-leg poses. Cold powers raise the bow over 0.24 seconds;
already aimed powers begin from the outgoing nock/pose. Release and recovery
clips, the 164-bone rig, GLB, animation resource, and gameplay clock are unchanged.

The previous power clips lowered an already raised bow. Piercing's authored
local arm orientations also crossed an IK branch between 0.3833 and 0.4000
seconds; interpolating those keys produced a 180-degree wrist excursion at
120 Hz. Merely preserving the nock or lengthening the entry blend did not fix
that later excursion, so both intermediate candidates remain rejected.

The chosen candidate reuses the already authored raised-bow chains. In the
actual skin witness, the maximum warm Piercing string movement during its full
preparation falls from about 30.1 cm to 1.51 cm per 30 Hz sample; Volley falls
from 30.8 cm to 1.16 cm. At 120 Hz the corrected warm maxima are below 4 mm.
Held socket contact is within 0.13 micrometres and the nearest sampled distal
finger surface is about 1.055 mm from the nock. These are mesh/contact
measurements, not human motion-quality ratings. Cold power entry is deliberately
brisk and still requires actual camera review.

All **18 primary draw trials** are exactly equal before/after, including every
recorded row for cold, warm, retrigger, reset, cancel/reaim and respawn/reaim at
30/60/120 Hz. The existing primary respawn/reaim residual remains unchanged.

| Check | Executed result |
| --- | --- |
| Ability rules/receivers | 85/85 |
| Effects geometry/resources | 74/74 |
| Effects adverse cases | 56/56 |
| New per-pulse warning lifecycle | 24/24 |
| Existing motion/contact | 39/39 |
| Existing motion polish | 22/22 |
| Existing motion adverse cases | 40/40 |
| New actual-skin power preparation | 217/217 |

Exact commands, source hashes, all 41 replaced arm-channel names and per-suite
reports are in [round3-final-receipt.json](round3-final-receipt.json).
The authoritative final new test report is
[power-entry-runtime-commit.json](round3/power-entry-runtime-commit.json).
[Primary identity](motion-study/primary-identity.json) binds the exact unchanged
primary traces. [Rounds 1–2](rounds-1-2.md) records the prior actual images
opened, original audit, scope and contracts.

## Preserved failed evidence and scope

`motion-study/` retains the source before this change, three candidate scripts,
baseline and candidate skin traces, a local-rotation diagnosis, and original
primary comparisons. The two incomplete candidates are not runtime dependencies.

The initial focused test failed because it incorrectly required reusable pose
caches to be empty after reset, and it retained 5 m/s through power preparation.
The real runtime sets horizontal velocity to zero at Q/X commitment. The final
test instead checks stale release rejection, cold entry after reset, and the
actual moving-to-committed-stop path. It retains the original numerical bound;
the threshold was not raised to make a failure disappear. The impossible
sliding-power fixture's 2.511 cm entry residual remains in the initial report.

The baseline copy of the new suite intentionally fails the new continuity
expectations. Its source file explicitly preloads `rama_motion.before.gd`;
the original report's fixed `scripts/rama_motion.gd` source entry is not the
baseline controller identity. Use the baseline preload, its source hash and
`baseline/source-sha256.txt` for that identity.

## Round 4 panel review

The UI owner independently reviewed the pending-lane code and approved its
authority, exact sweep and accessibility behavior. Actual distant warning
readability remains a render check; widening the stroke outside its collision
radius is not an acceptable way to conceal a readability defect.

The combat owner independently reviewed the new HUD meter/guide source. Its
Volley pulse calculation uses accepted release age, receipts clear on lifecycle
boundaries, and the meter is read-only. The guide matches actual kit values and
shield lifetime. Three-pixel strips and lane marks still need actual compact
and large-scale capture to exclude text overlap. This is source review only.

## Next owner and visual input route

R5 now includes an [independent map review](round5-map-review.md), with six
actual army/physics proposal probes, and an [original-pixel hero review](round5/hero-pixel-review-r1.json).
The latter inspected every frame in Piercing 45–71 and Volley 315–323, plus
13 named stills from root's frozen Forward+ capture. It accepts the visible
cold raise, lane retirement and HUD strips at the recorded camera/lighting;
warm ordinary input, fingers at useful scale, new-map/night views and full
commercial art quality remain unaccepted. Source and original hashes are in
the review receipt. This does not imply every capture frame was inspected.

Root owns the frozen-source import, package and actual native captures. For
ordinary input, enter Bow training and fire with **LMB**, then release it and
press Q or X near the end of primary recovery while the bow remains raised.
There is no independent RMB aim binding. A Q/X press during draw is rejected;
only a fresh press in the final 0.12 seconds of recovery can queue. Review
the first 0.24 seconds, all preparation, release and
recovery; especially inspect Q at 0.35–0.42 seconds. Also capture Q from cold
carry, moving into the committed stop, hit/cancel, pause/reset and all three
Volley pulses. The silent footage cannot establish listening quality.

Final art/contact, cold raise appearance, actual native input, human game feel,
audio listening, physical-GPU frame times and online matches remain distinct
gates. This packet does not certify Deadlock-level quality.

## Round 6 frozen build checks

[Round 6 verification](round6-verification.md) records **60/60** independent
encounter checks against the final imported R6d district, with no warnings or
errors, and **22/22** temporary-source packaging provenance counterexamples.
The latter found two real failure-marker/symlink fallback defects before the
root-owned packaging fix. Original failed results remain alongside the final
passing receipts. The new freeze helper copies verified source bytes while
other authorized workers continue in the live checkout. Root owns final
snapshot/export and actual R6d/warm-input visual acceptance.

The legacy world-scene regression now explicitly selects its original geometry
and verifies the exact current pause menu, including negative action mutations:
**36/36**, no warnings or errors. Every original geometry oracle remains. The
live runtime was byte-identical to the final snapshot when this test ran.

[Input audit and correction](round6-input-audit.md) supersedes the earlier
planned RMB warm-input route. Actual source, exact-engine headless checks and
a minimal X11 window confirm LMB fire and unmapped RMB. The six allegedly
different ammo readings have identical original pixels; no ammo-drain defect
was established. Earlier RMB-held Q/X footage is a cold-cast take.

## Actual packaged primary-to-power input

[The final ordinary-input review](round6/ordinary-primary-power-review.json)
opened every consecutive distinct original screen across the relevant
162-sample interval: **31 images**, with all 400 recording hashes verified.
It confirms actual LMB → Piercing activation and a raised-arm primary-recovery
→ Volley transition in the final packaged district. Volley retains the raised
pose without an intervening carry screen; its warnings retire 3 → 2 → 1 → 0.
Piercing begins after the arms partly lower, so strict fully-raised warm Q
remains a separate gate. Rear-camera finger occlusion and sparse distinct
software-rendered screens limit fine motion acceptance. The evidence is silent
and does not establish human game feel or hardware performance.
