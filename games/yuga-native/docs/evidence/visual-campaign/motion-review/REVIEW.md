# Independent actual-rig motion review

The corrected controller passes **58 independent checks** at 30, 60 and 120 Hz.
The review found and retained a real braking/contact regression before accepting
the correction. This is numerical pose and contact evidence; continuous rendered
motion and human feel remain open.

At 120 Hz, a braking sequence through 9, 6.75, 6.749, 2.8 and 2.799 m/s left the
right foot target 15.995 mm beyond the leg solver's reachable distance. The
historical controller already reached 10.290 mm in that sequence; the initial
hysteresis patch increased it. The 2 mm acceptance threshold was retained.

The owner corrected the float32 representation of the 2.8 m/s boundary and
increased the bounded pelvic compression allowance to 140 mm while preserving
locked targets. The final sequence's largest contact error is 0.000599 mm.
Every settled walking frame retains at least one support foot. Separate ablation
trials confirm that the compression correction alone also closes the rejected
sequence without losing its support frames. The final sequence actually uses at
most 61.627 mm of contact compression; a 140 mm code allowance is not a claim that
this full displacement was observed.

Start/stop, landing, traversal, rapid reversal at constant speed, and interrupted
attacks retain exact historical event clocks and every evaluated bone position in
the tested profiles. Threshold jitter stops repeatedly restarting transitions and
restores planted support. Neither input velocity nor combat-release authority was
changed by the patch.

An older discontinuity remains: a sharp +Z to -Z reversal at 6 m/s moves the
`toe5-2.R` joint origin 912.671 mm in one 120 Hz sample. The historical controller
does the same. This requires a separate direction-transition and continuous-motion
review; it prevents an assertion that all motion defects are resolved.

See [summary.json](summary.json) for source hashes, exact commands, correction
ablation, support counts, retained harness failures and scope. Full failed and
corrected frame traces are retained as gzip-compressed JSON; decompress them with
Python's standard `gzip` module. [diagnostic.json](diagnostic.json) measures contact
compression with a read-only override whose event clocks and bone positions match
the uninstrumented controller exactly. Source snapshots are plain text under
`source/`; runtime ownership remains with `scripts/rama_motion.gd`.

The next visual gate is a paired normal-speed jitter reel: simulate the same
60 Hz inputs, capture every fourth simulation step at 15 Hz, and inspect support,
cloth and silhouette. Fixed frames and these traces do not establish continuous
art quality, physical-GPU performance or human feel.
