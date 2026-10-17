# Recovered bow-carry motion review

This archive contains an actual 236-frame Godot Forward+ render, encoded at
24 samples per second in `carry-review.mp4`, with eight selected original PNGs.
`motion-render-review.json` records every frame hash, target/import hashes,
renderer, library, capture script and studio helper. The complete PNG sequence
was generated under ignored `build/motion-carry-restored/`; the selected frames
and video are retained here. The archive manifest hashes these saved artifacts.

Target: restored published Rama `6657f4bf2fdb41b1f8b1bbd64777b35b5b4acfe00b3e3e22e4bc793fd4df3e8e`.
Candidate library: `95ffda72b8fc5d4d41e9702ce30918cffb22e75d907545dc5ff28fb01411554f`.
Sequence: adapted idle → adapted run → original fire → adapted idle, with
0.18-second blends. Manual animation advance makes this a reproducible motion
review, not a real-time frame-rate measurement or native gameplay recording.

Root inspected the actual frames. The lowered carry removes the previous
full-body study's draw-hand-behind-head running posture. That bounded correction
does **not** accept the motion for runtime use: the carry hand remains open,
arms retain a rigid rest posture, and the run has substantial flight that needs
phase-specific contact and moving-ground review. Original fire and return
transitions are visible in the retained sequence. Finite transforms, seam
velocity and a per-foot minimum height cannot establish foot locking or grip.

The candidate remains experimental. `scripts/player.gd` still selects the nine
original clips. The next animation packet must author a closed bow grip,
natural carry posture and explicit support/flight intent, then review motion
at gameplay speed and distance before promotion. Production animation and
Deadlock/Overwatch-level visual-quality gates remain open.
