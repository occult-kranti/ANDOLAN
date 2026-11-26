# Announcer timing reads

Play either announcement in English or Hindi to judge how much of a round transition it occupies. The two lines describe a confirmed change of state. Neither read plays during a player's uncompleted hold. In this release the recordings appear on the listening desk. The map exercise uses its short musical cues and captions. [Audition the four reads](../index.html) · [Transcripts, durations in samples and file hashes](lines.json) · [Recording and casting script](../../../docs/design/ember-rite-5v5/audio/hero-voice-lines.csv)

| Accepted event | English | Hindi |
| --- | --- | --- |
| Ignition | The ritual fire is lit. | यज्ञ की अग्नि जल उठी। |
| Quench | The fire is out. | अग्नि बुझ गई। |

The renderer uses eSpeak NG's generic English and Hindi formant voices. SoX resamples them to mono 24 kHz PCM16, removes low rumble, normalizes peaks to −8 dBFS and adds a short lead and tail. No performer supplied voice data for these reads. Use the original lines, their pronunciation and available mix space as the starting point for a bilingual performer and director. The original score's CC0 dedication covers the seven music files listed in its manifest. [Generator](../voice_reference.py) · [eSpeak NG](https://github.com/espeak-ng/espeak-ng) · [SoX manual](https://sox.sourceforge.net/sox.html) · [Tool and rights register](../../../docs/design/ember-rite-5v5/audio/tools-and-rights.md)

With eSpeak NG 1.52.0, its English and Hindi voice data, and SoX 14.4.2 installed, run from the repository root.

```sh
python3 games/yuga-native/art/yagna-audio/voice_reference.py --output /tmp/yuga-voice-check
cmp /tmp/yuga-voice-check/lines.json games/yuga-native/art/yagna-audio/voice-guide/lines.json
```

The manifest includes a SHA-256 for each WAV. A clean render with those tool versions reproduced the four published files byte for byte.
