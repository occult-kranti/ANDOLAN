# Hanuman native import and trial

Hanuman Trial opens from the native title screen. Choose **Hanuman**, then
**Begin Hanuman Trial**. The stage uses the existing Lanka courtyard,
practice target adapter, controls, vitals, scene loader and UI theme.
Hanuman has his own imported skinned model and mace animations.
The catalogue supplies the names, clip IDs, onset poses and timing used by
the runtime, so an ability tuning change needs no stage script edit.

Move and aim with the usual controls. The HUD shows the keys from the
shared saved bindings. The defaults are LMB, Q, E, C and X. The blue targets
receive attacks, and the gold target receives allied effects in range.
Esc pauses the trial, and F5 resets the hero, targets and cooldowns.
The pause menu returns to the title.

The capsule owns collision and movement. The attack clock supplies the
release edge, so an authored pose or animation callback cannot apply damage.
Maruti Udayana sends a swept character body through one measured arc.
Static or dynamic obstructions can end it early. The cast marker remains
the intended endpoint, and the actor report records its swept result.
The hero rig samples its mapped clip through release and recovery.

Run from the repository root with Godot 4.6.3:

    godot --headless --path games/yuga-native --editor --import --quit
    godot --headless --path games/yuga-native --fixed-fps 60 --script tools/hanuman-rig/probe.gd
    godot --headless --path games/yuga-native --fixed-fps 60 --script tools/hanuman-rig/probe_tail.gd

The probe qualifies the exact imported GLB through the real scene.
It checks skin bindings, normalized weights, in-place motion over 99 poses,
the three attachment landmarks, an ordinary grounded run, actual
target damage, pause, reset, clear takeoff and landing, and a blocked sweep.
It prints a SHA-256 and machine-readable results. Audio is muted in this
probe to isolate geometry and avoid asynchronous dummy-driver teardown.
The release path and visual judgement require separate captures.

The tail probe drives the actual weighted four-link chain through idle,
directional movement, sprint, vault, landing, pause, cancellation, reset,
and both protected authored actions. The idle stance retains its authored
motion. A JSON profile controls bounds, damping and authored clip influence.
The modifier samples swept travel and facing after body movement and writes
only four local rotations after animation. Landing recoil needs actual
descent above the threshold, excluding the shallow spawn drop. The probe
includes malformed joint-role admission and records measured applied angles.
The protection weights fade at clip entry over about 110 ms. The sampled
secondary angle remains zero through the authored sweep and pulse contacts.
This layer does not perform cloth or body collision.

At R5 the imported asset has 167 bones, eleven clips, 64,955 vertices, 105,848 triangles,
seventeen material surfaces and at most four influences
per vertex. These counts describe the full-detail single hero and do not
establish a crowd or consumer GPU frame-rate budget.
