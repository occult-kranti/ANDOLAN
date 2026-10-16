# Original city soundscape

The multiplayer beta synthesizes all sound locally with Web Audio. It contains no recordings, downloaded songs, speech imitation, or borrowed melodies. It needs no audio downloads or external service.

## Sound design

- A quiet, filtered rain/street bed and distant traffic hum give the city presence without masking cues.
- Vehicle audio combines a low engine fundamental, a filtered mechanical harmonic, and speed-sensitive tyre noise. Virtual gear changes avoid an endlessly rising electronic pitch; hysteresis prevents pitch changes from chattering when speed fluctuates around a gear threshold.
- Footsteps follow measured player movement, so a held key against a wall does not produce marching in place. Entering and exiting a vehicle produces a short body thump and latch texture.
- Distinct, short tones mark a job start, job checkpoint, successful completion, crew signal, horn, UI action, and error. Routine notifications share a short suppression window, completion has priority, and repeated signals/errors have longer cooldowns. Tonal attacks rise over 16 milliseconds rather than a sharp edge. Information must remain visible in the HUD; audio never carries exclusive gameplay instructions.
- An optional quiet, slowly changing harmonic bed is off by default. The four original voicings use common musical intervals and do not quote an existing composition.

## Integration contract

`new GameAudio()` begins muted and does not create an audio context. `configure({volume, music})` changes preferences without starting sound. The interface owns preference persistence. Call `enable()` or `toggle()` directly from an explicit user gesture; loading a stored preference alone must never start playback.

`update(vehicleSpeedMetresPerSecond, inVehicle, {walkSpeed, interior})` accepts measured on-foot speed. `cue()` accepts `ui`, `job-start`, `job-progress`, `job-complete`, `signal`, `horn`, and `error`. Vehicle state transitions create entry/exit sounds automatically. Client-local horns do not imply a network broadcast unless the interface calls the cue when receiving an authoritative signal.

`setActivity(false)` fades playback down over 70 milliseconds, then suspends it during local menus or title inactivity. A revision token cancels stale fades, so a new enable action cannot be undone by an earlier pending suspension. Resuming a suspended game starts at zero gain and rises over 160 milliseconds. Visibility changes suspend hidden tabs, discard transient sounds, and reset footstep accumulation. Resuming only reuses an already enabled context; it does not opt an initially muted player into audio. `destroy()` removes listeners, stops sources, disconnects graph nodes, and closes the context.

`preview()` is an explicit settings audition: call it from the Test sound button. It works while muted or menu-paused without changing the mute preference or activity state. Its separate, quiet bus plays an original two-note sample (with a short chord when music is selected), obeys master volume including zero, and returns to the previous desired playback state after approximately 0.8 seconds. Gameplay audio is ducked during the sample. A newer preview, activity change, visibility change, toggle, or destruction invalidates the old audition. The bounded preview/fade timers are cancelled on teardown; no recurring scheduling timer is used.

Development diagnostics include `previewing`, `outputRms`, and `outputPeak`. The last two sample a 256-sample native post-master analyser buffer only when requested. Suspended contexts can retain their last buffer; these fields do not manufacture silence from state labels. Test attenuation by setting volume zero while a context is running, then separately verify suspension.

There are at most 24 transient voices. Finished voices disconnect their nodes, cue cooldowns prevent repeated UI spam, delayed frames never replay a backlog of footsteps, and continuous automation replaces superseded ramps. A compressor and conservative gains limit summed peaks. The loop graph is fixed in size.

## Verification and remaining listening work

`tests/audio.test.ts` uses a lifecycle-focused Web Audio mock to verify explicit opt-in, visibility/menu suspension, mute persistence across focus changes, volume validation, bounded voices, disconnection, delayed-frame footsteps, rejected resumes, complete shutdown, settings audition state restoration, overlapping audition cancellation, zero-volume audition, stale fade races, notification grouping, and gear hysteresis. These tests do not establish perceived loudness, pleasantness, or a speaker/headphone mix.

The previous native browser pass recorded nonzero synthesis (RMS approximately 0.00954), attenuation at zero volume (approximately 0.00000730), explicit-gesture activation, and persisted mute/settings in `docs/evidence/multiplayer-beta-audio-and-save.json`. Those figures describe the earlier audio implementation; the newer audition and fade changes need their own native browser verification. Native browser audio state and integration checks belong to the browser QA record. No human headphone or loudspeaker listening pass has been performed by this implementation agent. The subjective balance and mobile audio behavior still require playtesting with real output hardware.
