# Lantern Procession: traversal audio design and verification

This milestone adds an original twenty-second instrumental loop and seven short
positional gameplay cues. It uses synthesized plucked harmonics, a tonic/fifth
drone, membrane-like percussion and restrained electronic bass and pulse. No
recordings, commercial game sounds, voices or existing tune were sampled.
The generated audio is dedicated to CC0 1.0. Exact assets and generator hashes
are in [the exported provenance](../NOTICE/TRAVERSAL-AUDIO-PROVENANCE.json).

## Round 1 — sources and musical constraints

The actual retrieval record, URLs, source hashes and short excerpts are stored in
[`art/audio/research-sources.json`](../art/audio/research-sources.json). These
sources were read from their public GitHub repositories:

| Read source | Applied decision |
| --- | --- |
| [librosa pitch conversion](https://raw.githubusercontent.com/librosa/librosa/main/librosa/core/convert.py) | Twelve-tone equal temperament uses `440 × 2^((MIDI − 69)/12)`. D3 anchors the original phrase. |
| [SciPy waveform documentation](https://raw.githubusercontent.com/scipy/scipy/main/scipy/signal/_waveforms.py) | Frequency-sweep phase is the integral of `2π f(t)`. Flight and grapple sweeps are explicitly integrated rather than incorrectly multiplying a changing frequency by time. |
| [music21 scale models](https://raw.githubusercontent.com/cuthbertLab/music21/master/music21/scale/__init__.py) | Its examples expressly call RagAsawari and RagMarwa “pseudo-raga” scales. Pitch membership alone does not justify presenting this synthetic loop as an authentic raga performance. |
| [Godot audio buses](https://raw.githubusercontent.com/godotengine/godot-docs/master/tutorials/audio/audio_buses.rst) | Reserve amplitude headroom; apply logarithmic gain and stop streams for a genuine zero-volume setting. |
| [Godot pause behavior](https://raw.githubusercontent.com/godotengine/godot-docs/master/tutorials/scripting/pausing_games.rst) | Pausable scene-owned audio must also reject signal-triggered cues while paused because signals can still execute. |

Stanford's Karplus–Strong page, UNSW's tuning explanation and Britannica's tala
entry returned network-policy HTTP 403. They were **not read** and do not support
this milestone's claims. No book, video, Reddit post or traditional performance
was reviewed for this audio task. Research into broader game criticism is a
separate workstream.

The phrase uses semitone offsets `0, 2, 4, 7, 9, 12`; the rhythmic pattern is two
sixteen-beat cycles, each grouped `4+4+4+4`, at 96 BPM. This is an original modal
composition with Indian instrumental inspiration, not a named raga or a claim to
reproduce a specific tala, instrument, historical performance or tuning tradition.
There is no claim that its tones improve attention, cause psychological states or
produce a physiological benefit. Quiet music and distinct cues are testable game
mixing choices; musical enjoyment requires listening feedback.

## Round 2 — synthesis and implementation

`tools/audio/build-traversal-audio.py` uses NumPy with seed `2026101707`. The
twenty-second loop contains 480,000 stereo sample frames at 24 kHz, 16-bit PCM.
Pitch harmonics decay faster at higher frequencies, giving the plucks a bright
attack and softer tail. Membrane-like impacts combine decaying oscillators and
short deterministic noise; the bass/pulse layer remains subordinate.

Drone frequencies are rounded to integer cycles over the loop, within 0.4 cents
of their equal-tempered references. Event tails wrap around the complete loop;
there is no silence or fade-out inserted at the seam. The seam's adjacent-sample
change is measured against ordinary within-loop changes. This is a numerical
continuity check, not an auditory sign-off.

| Cue | Meaning and distinguishing sound | Duration |
| --- | --- | --- |
| `grapple_lock` | Bright rising lock tone | 0.24 s |
| `grapple_release` | Short descending rope/air texture | 0.28 s |
| `flight_start` | Broad rising air swell | 0.48 s |
| `flight_exhaust` | Lower falling, pulsing warning | 0.40 s |
| `flight_recharge` | Three ascending plucked tones | 0.56 s |
| `minion_hit` | Low, brief membrane impact | 0.16 s |
| `coin` | Two higher metal-like rings | 0.36 s |

`scripts/traversal_audio.gd` owns one music player and six reusable 3D cue players.
Cues use world positions, a 65 m maximum distance and bounded per-kind cooldowns.
Higher-priority traversal alerts can replace lower-priority cues when the pool is
full. No incoming string can create a new file path or extra player. There are no
global audio-bus changes or unowned timers.

Music starts at −20 dB before the master setting; cues are capped at −6 dB before
the master setting and spatial attenuation. Semantic cues temporarily duck music
by up to another 8 dB. With six source cue peaks and music aligned, the subsystem's
conservative amplitude bound is 0.561, leaving at least 5.03 dB of headroom at
master volume 1. Other active sound systems require their own combined budget.

The shared saved `[audio] volume` is respected. The common settings reader bounds
files to 64 KiB and rejects constructor syntax, excessive nesting and unterminated
strings before parsing variants. Rejected files are preserved. Missing or nonnumeric/nonfinite
values default to 0.35; finite values clamp to `[0,1]`. An existing saved default
from another screen is honored. At zero, all streams stop and events cannot
restart them. Focus loss and scene pause suppress cues and pause the music. Scene
return frees the players and window callbacks.

Integration API:

```gdscript
audio.configure(saved_volume)             # Optional before entering tree
audio.set_volume(value)                    # Live slider; persistence owned by UI
audio.play_event("grapple_lock", position)
audio.set_music_enabled(false)
audio.set_suspended(true)                  # Menu or explicit gameplay suspension
var state = audio.get_diagnostics()
```

## Round 3 — verification and import correction

The first native check passed state/lifecycle tests, but inspection found Godot's
default WAV importer used lossy QOA compression. The eight tracked `.wav.import`
files now explicitly select uncompressed PCM with trimming, normalization and
rate conversion disabled. The native test compares every imported stream's PCM
bytes with the generated WAV payload, so source headroom and seam measurements
apply to the loaded streams too.

The focused native suite has 39 checks: malformed and unsafe saved values, genuine mute,
pre-ready configuration, exact loop range and imported PCM, all seven cues,
10,000-event flooding, bounded players, unknown and nonfinite input rejection,
music ducking, focus and pause transitions, settings changes while paused,
music-only disable, clamped API values and repeated scene cleanup.

```bash
python3 games/yuga-native/tools/audio/build-traversal-audio.py --check
godot --headless --audio-driver Dummy --path games/yuga-native \
  --script res://tests/traversal_audio_cases.gd -- \
  --report=/tmp/traversal-audio-runtime.json
```

The same 39 checks also pass with `--fixed-fps 60`. The music-disable test waits
for the cue's real monotonic cooldown instead of a simulated SceneTree timer:
fixed-FPS testing can advance 0.45 simulated seconds before the 80 ms coin
cooldown has elapsed in real time. This test correction does not change runtime
throttling, audio bytes or playback behavior.

The generator's `--check` reconstructs every WAV in memory, compares exact bytes
and source pins, verifies distinct cues, zero cue endpoints, loop seam, PCM
headroom and the lossless import settings. Regeneration and CI checks pin
`numpy==2.3.5`; all runtime audio is prebuilt. A separate check with NumPy 2.2.6
reproduced all eight WAVs byte for byte, but version metadata differed and one RMS
reduction differed by about `1e-17`. Report metrics are rounded to twelve decimal
places to avoid treating irrelevant floating-point reduction noise as asset drift;
WAV equality and SHA-256 checks remain exact. The generated eight WAVs total
2,039,392 bytes.

Headless testing used the Dummy audio driver. Human listening, headphones/stereo
localization, hardware output latency and accessibility feedback remain unverified.
The test does not establish that any cultural tradition has been authentically
recreated or that the complete game mix is balanced.

## Workspace recovery

The cloud workspace rollback removed these uncommitted assets. The generator,
runtime and test were reconstructed byte for byte from this conversation's tool
records and their prior SHA-256 values. Regeneration reproduced all eight original
WAV hashes; fresh native and PCM checks passed after restoring lossless imports.
The subsequent fixed-FPS test-timebase correction is documented above.
The research ledger records fresh public-source retrievals after recovery; it does
not present the lost temporary files as surviving evidence.
