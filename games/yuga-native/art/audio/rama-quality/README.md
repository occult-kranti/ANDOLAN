# Rama action audio source

Original deterministic action/counter cues for the one-hero quality slice. The generator uses only Python's standard library: oscillators, short resonators and seeded filtered noise. There are no external recordings, commercial game sounds, voices or transcribed melodies. The plucked, modal and bell-like colors are sound-design abstractions; they do not establish historical instrument/raga authenticity or psychological effects.

`build_audio.py` owns fifteen mono 48 kHz PCM16 WAVs and their manifest in `runtime/`. All files are finite, nonlooping, 0.10–0.95 seconds, and have zero first/last samples. The manifest records duration, peak/RMS/DC, seed, byte count, file hash and generator hash. Changes must regenerate the manifest and receive fresh validation and listening review.

```sh
python3 games/yuga-native/art/audio/rama-quality/build_audio.py --check --report /absolute/new/audio-build.json
```

The source runtime directory is staged byte-for-byte to `assets/audio/rama-quality/` by the integration owner. The default module reads that runtime path; its isolated component suite explicitly reads this source directory. Source art is excluded from portable exports. Import the staged WAVs before exporting and retain this README/generator/manifest as editable provenance.

## Cue language and event timing

| Action / receipt | Sound design | Actual onset |
| --- | --- | --- |
| Kodanda | Short fibre tension; dry string snap and woody tail | Existing `begin` / authority `release` |
| Piercing Dawn | Longer rising tension; brighter descending resonance | Existing `begin` / authority `release` |
| Measured Step | Restrained friction pickup and close airy sweep | Existing `begin` / authority `release`; no invulnerability cue |
| Guardian Circle | Paired soft tones and rounded bell/pluck body | Existing `begin` / authority `release`; healing ticks stay silent |
| Dawn Volley | Long tension and three compact plucked pulses | First pulse at `release`; two more only when existing `tick.age_s` reaches `release_age_s + projectile.delay_s` |
| Real damage to troop | Woody positional contact plus short local confirmation | Existing `impact` with positive `damage_applied`; missing/zero receipt stays silent |
| Cover | Dull positional contact, no success tone | Existing `impact.reason == wall`; range expiry stays silent |
| Damage to Rama | Local low-mid impact, above confirmation priority | Existing accepted vitals receipt, consistent actual health/shield arithmetic |
| Cancel | Quiet damped tension | Explicit non-terminal cancellation; reset/defeat/scene exit stay silent |

There are no independent audio gameplay timers or delayed queues. Suppressed/muted/paused pulses are consumed; returning to play never replays them. The recorded pulse delay is the current original Rama kit's 0.10/0.20 seconds, not a copied commercial implementation.

## Pool, priority and headroom

`rama_action_audio.gd` owns exactly four reusable players: three `AudioStreamPlayer3D` action/contact voices and one local `AudioStreamPlayer` for confirmation/incoming damage. There are no runtime audio buses or effects. The isolated test temporarily adds and removes a numeric capture bus; it is not a game mix feature. Positional voices use 36 m maximum distance, 3.5 m unit size, 0.65 panning strength, 8.5 kHz attenuation filter and maximum gain −18 dB. Priorities are draw/contact/cancel 1, release/confirmation 2, incoming damage 3. A new onset may replace only the oldest voice of equal/lower priority; low-priority draws cannot evict three live releases. Local confirmation cannot evict incoming damage.

Every PCM peak is below 0.16 full scale; runtime gain is at most −18 dB at slider 1. The conservative sum of four simultaneous maximum peaks is **0.08057123**, or **21.876 dB module-only headroom**. This assumes no amplified buses/effects and that the positional maximum remains enforced. It is not a bound for traversal/music/siege/legacy invocation overlap. Integration replaces the prior four Rama invocation players; independently audit the whole live mix before accepting dense-fight intelligibility.

Pitch varies deterministically from cast/generation/cue across 0.988–1.012; no random runtime allocations, timers or unbounded variations are needed. Cast state is capped at twelve and vitals-source watermarks at sixty-four. Events validate finite bounds, generation/sequence, timing, identity, release order and receipt shape. Contact confirmation is coalesced at 70 ms of authority time.

## Integration API and lifecycle

- Create one `RamaActionAudio` child of the runtime; call `consume_event(event)` for the original kit snapshots. Do not translate snapshots to a second invented event clock.
- Pass actual vitals `damaged` receipts to `consume_damage(receipt)` even for lethal receipts. Lethal receipts silence all voices and mark the receiver dead; `set_alive(true)` is required on the actual respawn path.
- Call `set_receiver_generation(vitals.generation)` on configure, practice reset and actual respawn, beside `set_alive(vitals.alive)`. Once bound, incoming damage from older or future receiver generations is rejected; kit generation and vitals generation remain separate.
- Wire saved `set_volume(value)`, world/menu `set_suspended(value)`, focus and explicit `set_alive(false)` on defeat. The module also subscribes to window focus and stops on actual tree pause. `set_volume(0)` stops existing voices immediately.
- On practice/player reset call `reset()`. It stops voices and clears active casts while preserving anti-replay watermarks; the kit's real higher-generation reset opens a new cast identity space. Local cleanup itself is not a fabricated network generation.
- Teardown frees the four child players. All files are short nonlooping cues, so there is no music/channel surviving a scene return.

`report()` exposes actual voice metadata, counters and bounded state for tests. It does not establish audible quality.

## Acceptance boundary

The final 115-case component fixture, run through `tools/run-quality-checks.py --suite action-audio-component` with complete engine-log rejection, covers PCM reproducibility/format/peak/DC, actual Godot Dummy-driver voice/event/lifecycle behavior and unmodified actual kit/vitals receipts. A fixed four-voice Dummy capture observes 0.015943 peak at maximum slider; this is one numeric fixture, not an exhaustive whole-game mix bound. **Human listening, sound-device behavior, in-game dense-fight intelligibility, accessibility comprehension and production sound quality are UNRUN.** Numerical synthesis and a passing counterexample suite cannot establish parity with Deadlock or another commercial game's sound.
