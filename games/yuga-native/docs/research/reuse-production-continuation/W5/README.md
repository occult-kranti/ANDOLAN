# W5: actual event/socket/receiver sidecar

Implemented the next concrete step from the [previous Source 2 inspection packet](../../reuse-next-ten/reuse-advisor-world/README.md): pair actual Rama `(generation,event_seq)` identities with real rig socket transforms and the existing receivers' actual acknowledgements. The original 20 Hz combat owner and all canonical game files are unchanged.

Source checkpoint: `8e0f7ca21638cd39198606a3301b6c90afd1bdcb`. The [executed run](evidence/accepted-r4/run.json) pins the engine and six tool scripts; the [raw trace](evidence/accepted-r4/actual.json.gz) pins 16 observed game sources/assets before and after execution. Tool entry point: [`tools/reuse-event-sync`](../../../../tools/reuse-event-sync/README.md).

The fixture uses the unchanged `RamaHeroRuntime._event` route. Its effects and audio instances are replaced only with subclasses that invoke their inherited receiver exactly once and retain the returned value, sequence/generation watermarks and counters. The real player's existing rig is used for bow-grip, draw-hand, string-nock and arrow-muzzle transforms. Both before-motion-event and after-event evaluation are retained without advancing the animation clock. The actual release projectile origin matches the sampled muzzle to less than one micrometre in these probes.

## Executed evidence

All five subprocesses exited 0 with no Godot script errors. Godot 4.6.3 uses Dummy audio and headless rendering; capture is pinned to one allowed CPU. The approximately 9.7-second aggregate tool duration is not an FPS result.

- **92/92 actual capture checks:** 15 timelines, 441 full event records and 1,848 numeric presentation samples at 30/60/120 Hz. Each timeline preserves the 20 Hz Army clock.
- **43/43 Python checks:** source identity, genuine receiver returns and state, missing acknowledgements/sockets, duplicate identities, sequence gaps, invalid/absent boundaries, stale generations, nonfinite sockets, reversed clocks, frame cadence/coverage, malformed presentation state and incomplete samples. Nine added negative cases repeat removed/shifted-frame and event-clock drift mutations at all three source cadences.
- **Nine actual receiver negative calls:** duplicate completed events and stale pre-reset events are rejected by both production receivers without additional accepted effects or audio playback.
- Three reports reusing the retained MIT Source 2 window adapter preserve every selected ordinal once in each generation at 30/60/120 Hz. These are offline inspection cadences.

Each cadence covers completed Kodanda, completed Dawn Volley, windup cancellation, reset during windup followed by a new Kodanda, and cancellation after Volley releases. Kodanda releases at 0.20 s; Volley releases at 0.95 s and records three range-expiration contacts at 1.85/1.95/2.05 s. The units and unrelated AI/waves are intentionally excluded. These are actual Kit contact events, **not damage hits**. Full timing and counts: [summary](evidence/accepted-r4/summary.json).

The accepted compressed raw trace is 908,187 bytes and decompresses byte-exactly to 10,563,549 bytes, SHA-256 `7969ad496d906628697e57b696187764ff7be72c862d8b4d41f8a73bcc7b5838`. The runner verifies all compressed copies before recording them; original files remain in `/workspace/scratch/reuse-event-sync/r4/`.

## Interpretation and limits

A receiver acknowledgement means the observed call accepted that real event. It does not imply a sound was heard, a visible effect was drawn, a hit landed, or a full match was played. Accepted ordinary ticks can legitimately select no cue. Missing fields remain missing in the report and produce specific failures; no successful acknowledgement or identity transform is invented.

The source audio uses event time for pulse/confirmation eligibility, while `AudioServer` controls voice lifetime. Both simulation and wall clocks are recorded distinctly. The earlier proposal's general reference to a real-clock audio cooldown does not describe this particular action-audio guard; no scheduler was changed to match that assumption.

No screenshots or videos were produced by this headless packet. Continuous rendered comparison, human listening, real player input, unit/wall-contact review, hardware profiling and whole-game/online acceptance remain open. The first heavy rendering lane belongs to hero authoring and gate input; this sidecar can support the later continuous-motion renderer without changing gameplay.

Initial parser-inference errors were corrected before execution; the R1 log and successful R2 capture without explicit receiver identity fields remain in scratch. [Prior R3](evidence/prior-r3/run.json) has a valid capture, but independent W1 review found five gaps in its inspector: shifted/missing frames and a mislabeled cadence could pass, backward capture time was unchecked, and a malformed frame state caused an exception. The original R3 tool bytes and receipts are retained. The revised inspector validates source cadence, complete sample coverage, clock order/offset and presentation-state types; the unchanged W1 probe then passed all 11 controls. R4 is a new full run of the repaired sources, with the additional three-cadence counterexamples. No old result was relabeled. This is one bounded implementation packet, not a completed ten-stage roadmap or new accepted hero.

Next owner: motion/render worker for continuous paired images at the same three presentation cadences, using the retained exact event/acknowledgement identities and reporting real contact/audio differences. Root owns integration and publication.
