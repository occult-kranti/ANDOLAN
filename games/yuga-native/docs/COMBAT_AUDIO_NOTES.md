# Confluence duel audio

This is an original synthesized soundtrack for the 24 second combat film. It contains no downloaded music, sampled commercial game sounds, recorded voices, or claims of performing a traditional raga. The drone, sparse plucked tones and soft membrane-like percussion support the scene; recognizable sounds identify actions and counterplay.

## Cue plan

The authoritative timing input is `assets/cinematics/confluence-duel.json`. The audio builder validates every cue before writing files. The film's current ten events are:

| Time | Sound | Purpose |
| --- | --- | --- |
| 1.80 s | Wood friction and string tension | Opening bow draw |
| 4.15 s | Short twang and air transient | First arrow release |
| 4.75 s | Brief inharmonic metal clang | Visible guard blocks the arrow |
| 6.00 s | Rising low resonance and air | Warning before the wave fires |
| 7.25 s | Two cloth/air swells | Rama's evasive movement |
| 8.10 s | Falling resonance and broad air | Wave release |
| 12.80 s | Wood friction and string tension | Countershot draw |
| 15.20 s | Short twang and air transient | Countershot release |
| 15.85 s | Low impact and short resonant tail | Countershot connects |
| 18.00 s | Soft harmonic bloom | Resolution |

The score ducks smoothly by 48% beneath semantic cues. Actor panning is deliberately modest: Rama −0.18, Ravana +0.18. This is a mixed cinematic soundtrack, not positional gameplay audio. The shield, warning corridor, evade result and hit receipt also have captions and visible shapes, so sound is supplementary.

## Assets and playback

- `assets/cinematics/audio/confluence-duel-mix.wav`: exactly 1,152,000 stereo frames, 48 kHz, 16 bit PCM, 24 seconds, no looping metadata.
- `assets/cinematics/audio/audio-*.wav`: ten mono cues at their declared durations, suitable for later controlled reuse.
- `art/cinematics/audio-manifest.json`: source and film hashes, output hashes, sample offsets, synthesis seeds, measurements and validation results.

Use one native `AudioStreamPlayer` with the full mix. `play(absolute_seconds)` is for a seek or restart; normal playback must not call it each frame. Pause through `stream_paused`, resume the same player, stop at the film's end, and stop/mute audio during deterministic frame capture. Rewinding must not create extra cue players. The viewer owner implements this transport and its state tests.

For the exported film, mux the exact master WAV with the actual captured video. A typical command is:

```sh
ffmpeg -i captured-film.mp4 -i games/yuga-native/assets/cinematics/audio/confluence-duel-mix.wav -map 0:v:0 -map 1:a:0 -c:v copy -c:a aac -b:a 192k -shortest confluence-duel-with-audio.mp4
```

The master WAV remains the reproducible lossless source; AAC in the delivery video is a separate encoded derivative.

## Rebuild and validation

```sh
python3 games/yuga-native/tools/cinematics/build-duel-audio.py
python3 games/yuga-native/tools/cinematics/build-duel-audio.py --check
python3 -S games/yuga-native/tools/cinematics/build-duel-audio.py --check-fixtures
```

Synthesis requires NumPy and SciPy; their actual versions are recorded. The read-only `--check` and `--check-only` modes also work with standard-library-only Python. `--check` validates the saved master and cue WAV headers, exact durations, bytes/hashes, source pins, event metadata, edge silence and clipping bounds. `--check-only` validates the current film contract and eight malformed contract fixtures without writing audio.

The build checks actual decoded master PCM against each isolated cue, including overlapping cues. The correct sample alignment must beat both adjacent one-sample shifts. Contract rejection cases cover duplicate IDs, negative starts, overruns, unknown kinds/actors, nonfinite times, filename traversal and nonintegral sample timing.

Six additional temporary-copy fixtures check stale source pins, a one-sample cue offset, truncated PCM, nonzero edge samples, clipping and a wrong channel count. File-mutating fixtures update their own hash/byte fields so structural checks must reject the defect independently. This exposed and fixed a validator gap where a WAV's declared frame count was trusted without comparing the bytes actually read. Frozen source WAVs were unchanged.

The stereo master peaks at 0.72, approximately 2.85 dB below full scale, using one linear gain rather than a clipping limiter. Its first and last 10 ms are digital silence, with adjacent fades. These checks establish file integrity and timing; they do not establish perceived loudness, musical quality or comfort on every playback device.

## Review status

Round 1 established the cue contract; round 2 synthesized the original score and effects; round 3 checked saved PCM, timing and headroom. Round 4 requires human headphone/speaker audition and review against the actual rendered film. No listening review is claimed from waveform measurements. Review should compare the guard clang with the 4.75 s block, the evade/wave pair at 7.25/8.10 s, and the 15.85 s hit; check that the score stays below these cues and that pause, seek and restart do not stack playback.
