# R7 Rama motion evidence

The final staged take contains **539 rendered frames / 22.46 seconds**. The side
correction take contains **118 frames / 4.92 seconds**. Both use the exact R7 asset,
controller and library pinned in `selection.json` and the capture reports.

- [Full movie](rama-motion.mp4) and [capture report](motion-capture.json).
- [Both-direction side correction](side/rama-motion.mp4) and [its report](side/motion-capture.json).
- [39/39 motion checks](motion-cases.json), [34/34 migrated traversal checks](traversal-cases.json).
- [Source pins, selected-frame mappings and video counts](selection.json).
- [Detailed authoring, correction and review scope](../../../../art/hero-rama-motion/REVIEW.md).

The complete movies, all raw-frame hashes, actual render logs and runtime source
snapshots are retained. This compact archive contains 36 representative PNGs;
the full raw PNG sequences remain in `/tmp/rama-motion-render-r4` and
`/tmp/rama-motion-side-r3`. `ffprobe` independently reports 539 and 118 encoded
frames respectively. No image sequence was padded to replace missing frames.

Sequential and explicitly sampled frame-strip review covers locomotion, aiming,
bow draw/release/recovery, abilities, interruption, hand/string detail, rapid
primary repetition and reactions. Independent QA checked every frame 421–538 of
the full take, and both sideways directions plus walk/stop of the short take.
The R6 triangular cloth fan/striped self-overlap is resolved; its rejected frame
remains separately under `../qa/review-images/r6-rejected-strafe-frame-00097.png`.

The drape and high-knee movement remain stylized; the cloth is skinned. This staged
Forward+/llvmpipe render is separate from the final Confluence gameplay capture
and does not establish physical-GPU performance or simulated cloth behavior.
