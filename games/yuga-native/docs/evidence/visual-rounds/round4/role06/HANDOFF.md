# R4-06 continuous motion capture — complete

One uninterrupted 210-frame / seven-second fixed 30 Hz take is captured against
committed runtime `7087eb50be6cd1beac0db704177d17f3eaa0068a`. The motion controller
is unchanged (`4c72fd247704896bbf8b720658efff1388d850912f7aed6a916950538aa458c1`).
The separate immutable snapshot is `/workspace/scratch/visual-round4/capture-motion-project-r4`.
Its 173 imports are source-MD5 fresh; all twelve promoted asset/cache/descriptor
records match the R3 promotion receipt. No editor import was run. Source/cache
and new capture helper/contract together produce 878 exact pins.

The actual Forward+ take is archived in `originals/`: 210 untouched 1280×960 PNGs,
`capture.json`, `continuity.mp4`, exact harness/freeze sources and engine logs.
The video contains exactly 210 frames at 30 Hz / seven seconds. All 210 fullbody
framing checks and nine runtime gates pass. The independent motion audit passes
13/13 checks; the archive audit verifies all originals and 878 source pins.
The engine exited zero with no warnings. Capture took 436.070 seconds of wall
time on CPUs 0 and 1 with two llvmpipe workers; recorded cadence is not hardware FPS.
All owned Godot, Xvfb and encoder processes stopped and the heavy lane is released.

`motion_contract.json` specifies one initial reset/start followed by real left
start/stop, right start, direct left reversal, another stop, jump/landing and a
public Piercing windup cancellation. No in-take teleport/reset, pose assignment,
velocity correction or spring update is injected. The camera follows only X/Z
and keeps enough fixed vertical space for the measured 1.500840 m jump apex.
The actual jump reaches root Y=1.500840187m and lands before the cast. Velocity
reaches both −6 and +6 m/s, and both stop intervals settle to zero.

The Piercing cast at frame 150 has generation 3 / id 1; public cancellation at
frame 159 returns true at kit age 0.30 s, before the 0.65 s windup. It immediately
clears the nocked arrow, warning/effects and action locks, starts fade at zero,
and produces one matching cancel with zero release/impact events. Subsequent
frames show the normal fade complete. There is one initial reset and no reset
inside the take. Capture preserves immediate call state and later presentation.

Contact uses actual imported named binds and the role 12 semantic selector:
rest vertex y<.30m, with >.5 summed foot/toe skin weight for a named side. This
jump-wide camera selects actual mid LOD 1 throughout: 5,557 left and 5,574 right
sole vertices. The cached near selector remains 6,790 per side, matching role 12,
but near-only numerical results are not transferred to the visible midLOD.
The actual minimum signed sole clearance is −20.173656 mm at frame 48, right foot.
Seven grounded side-samples are below −5 mm. Locked, grounded minimum sole
clearances range from 0.678327 mm to 1.410683 mm. These are retained CPU measurements
of actual imported vertices, not corrected motion or proof of GPU vertex positions.
`motion-check.json` preserves all 210 contact rows.

The final modifier callback snapshots all 164 bone globals together with rig,
body/capsule/collision, foot-lock targets and selected-part visibility/offsets.
Sole contact uses this coherent state. A separate draw observation preserves
sampling phase explicitly. In the actual rendered take the two physics counters
match on all 210 samples. The headless preflight's two-tick phase lead and its
−30.009268mm minimum remain separately labeled; neither value is transferred.
Fullbody projected bounds and original camera transforms are recorded separately.

Capture engineering opened original frames 000, 029, 030, 060, 099, 119, 158, 159, 163
and 209 to inspect framing and the event boundary. This is sampled original-frame
inspection, not an ordinary-speed playback or full motion-quality verdict.
Independent motion 15, contact 12 and cancellation 11 reviews were requested with
the complete originals, video and per-frame measurements.

Preparation failures remain preserved. The first Git freeze requested an
untracked R3 contract that R4 does not use. The next snapshot omitted three
Git-ignored font import descriptors, causing the first CPU preflight to stop
before motion sampling. The corrected freeze copies those descriptors only
when committed font bytes match and validates their imported source MD5s.
The second CPU preflight exercised movement/contact but skipped intended framing
samples because JSON frame numbers were floats; it is explicitly rejected for
framing. The final helper converts them to integers and requires the exact 24
sample count. The final CPU preflight passes nine gates and all 24 required
framing samples. No failed preparation run has a framebuffer or art-acceptance claim.

Owned changes are new capture/freeze/runner/archive helpers under
`tools/visual-rounds/` and this role06 evidence. Runtime sources are untouched.
This tape retains committed 7087 identity. The subsequent I1 overview suspension
patch is excluded and is not tested by this active-input tape. Actual playback,
pixel review and motion-quality disposition remain separate gates; this capture
does not promote a motion correction or certify ground/collar clearance.

Schema clarification from independent R4-15: raw `foot_targets_rig` is a
misnamed field containing WORLD-space planted anchors from `rama_motion.foot_targets`.
The raw name/data remain unchanged; contact interpretation must use world space.
