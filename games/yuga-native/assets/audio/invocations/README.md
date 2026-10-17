# Original invocation cues

These sixteen short WAVs are generated entirely from mathematical oscillators by `tools/audio/build-invocation-audio.py`. No outside recordings, samples, melodies, voice or commercial-game audio are used. They are interaction cues, not a musical composition or a claim of culturally authentic sound.

- Shared windup: 0.24 seconds; shared cancel: 0.16 seconds.
- Fourteen distinct hero releases: 0.48 seconds each. Fundamental frequency, partial mix, decay and phase modulation vary; exact choices are in `manifest.json`.
- 48 kHz mono PCM16, nonlooping. Worst summed peak for three maximal cues is 0.5562 of full scale.
- Three owned `AudioStreamPlayer` nodes maximum, no per-tick voice allocation. Current practice uses one active cast and replaces its windup at release.

Rebuild from repository root:

```sh
python3 games/yuga-native/tools/audio/build-invocation-audio.py
python3 games/yuga-native/tools/audio/build-invocation-audio.py --check --report /tmp/invocation-audio-build.json
```

`invocation_audio.gd` consumes canonical session events. Only begin, release and cancel start audio. Tick/impact/end do not restart cues. Epoch, cast and event sequence checks reject stale onsets; local reset retains receipt watermarks until a greater-epoch reset. Volume zero and suspension stop voices, consume valid suppressed onsets and never replay them on resume. The world owns saved volume and focus/pause/overview suspension; this module writes no settings.

The source checkout can load raw WAVs before import. Packaged builds use Godot's imported resources. Root must import the new assets before export. [Numerical PCM reproducibility](../../../docs/evidence/mythic-batch2/audio/invocation-audio-build.json), stream structure and [48 Dummy-driver lifecycle tests](../../../docs/evidence/mythic-batch2/audio/invocation-audio.json) pass; there has been no listening/perceptual review in this packet.
