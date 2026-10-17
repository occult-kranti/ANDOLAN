# Full Confluence duel capture — revision 4

The MP4 contains 576 actual sequential Godot Forward+ renders at 1280 × 720, sampled at 24 Hz over 24 seconds. It includes the original 48 kHz stereo soundtrack. Every frame's source time, state diagnostics and PNG hash are preserved in `combat-film-render.json`; sixteen representative original PNGs are retained here. The complete raw PNG sequence remains in the local build directory. Encoding metadata and the delivered MP4 hash are in `combat-film-video.json`.

The captured runtime matches commit `ffc57081d843ab2645a20930f6deb70f2b325193`. The capture checked source hashes before and after rendering and verified freshness of imported actor/stage models. Exact director, actor adapter, effects, lighting, screenplay and capture helpers are retained with this evidence. A subsequent viewer change honors saved game volume; it does not change this film's actors, timeline, camera, effects or soundtrack. That later runtime is tested and packaged separately.

The root review inspected the opening, three successive guard-return poses, warning/evade/miss, countershot travel, close impact and resolution. Both actors' feet remain visible in those compositions; the wave corridor clearly points to the abandoned position; health changes only after the counter hit. The revised guard return has zero speed alerts in the separate 24 Hz pose-continuity check. This is a review of selected actual frames plus numerical motion checks, not a claim of complete real-time visual or auditory audition.

The continuous film is delivered for review. Remaining art work includes floor/inlay aliasing, fine shadow grain, richer surface materials, less sparse scenery and more expressive animation. Production character fidelity and complete gameplay combat are not accepted by this capture. The earlier interrupted revision 3 and its rejected guard-return excerpt are preserved in `../combat-guard-r3-rejected/`.

Rendering took 422,631 ms on llvmpipe software Vulkan. That duration is an offline capture measurement, not gaming-GPU performance. The native viewer, Linux package interaction and encoded audio correspondence have their own evidence records.
