# Vanara Sena · release cue

[Listen to the WAV](../../assets/audio/hanuman-trial/vanara_sena.wav) · [Parameters](parameters.json) · [Generator](build.py) · [Verification](verification.json) · [Provenance notice](../../NOTICE/VANARA_SENA_AUDIO.json)

This original, short release cue combines a rising harmonic horn-like breath, a soft struck-metal overtone, a membrane pulse, a pluck and filtered wind. These are mathematical approximations made with the project's existing Hanuman and traversal synthesis helpers; they are not sampled conch, bells, drums, voices, Sanskrit chanting, a named raga or audio from another game. The cue is intended to mark the authority's accepted **release** event, not to determine ability damage or timing.

The file is mono 24 kHz PCM16, 0.82 seconds long, with peak **−13.15 dBFS**, RMS **−26.87 dBFS**, zero-valued endpoints and zero clipped PCM samples. Those are numerical measurements of the stored file, not proof of perceptual quality, true-peak headroom or the combined ten-player mix. Human listening, device balance, overlapping voices and actual browser scheduling still need review.

## Reproduce and check

From the repository root with Python 3 and NumPy installed:

```sh
python3 games/yuga-native/art/vanara-sena-audio-2026/build.py --check
python3 games/yuga-native/art/vanara-sena-audio-2026/verify_corruption.py
```

To deliberately regenerate the WAV and provenance notice after editing the parameters, run the first command without `--check`. The checker regenerates both in memory and compares bytes with the committed artifacts, including the recorded NumPy version. The corruption test uses temporary copies and confirms that altered WAV and notice data fail the check. [Result](corruption-check.json). The current WAV digest is `5775ab033f1b9571b5bb9edbbee737ae898e3fa6f8c218f9d5275f2eee9b73ca`.

The browser packager collects the WAV from the existing Hanuman audio directory, and the client looks up the `vanara_sena` cue by its ability ID. That is an integration contract to verify in the assembled game. The separate Godot native preview has not been changed or retested for this ability.
