# Ash at the Waterline

The listening desk shows the original carried ember vessel from Mandala Rift. It reuses the project’s DM Sans and Barlow Condensed font files under the SIL Open Font License. The four announcer reads use generic eSpeak NG voices and a separate production script. [Vessel concept and art direction](../mandala-map-studio/README.md) · [DM Sans license](../four-hero-motion/viewer/notices/DM-Sans-OFL.txt) · [Barlow Condensed license](../four-hero-motion/viewer/notices/Barlow-Condensed-OFL.txt) · [Guide voice credits](voice-guide/README.md)

Play the full forty seconds, jump to an entrance, or solo a part on the listening desk. The first sound is a plucked fifth. As the fire burns, a low hand strike supplies a walking pulse, a second player answers across it, and a reed voice carries the last phrase. [Open the listening desk](index.html) · [Download the stereo recording](ritual-mix.flac) · [Try it in the Ember Rite rehearsal](../../docs/design/ember-rite-5v5/atlas/rehearsal.html)

| Elapsed ritual time | Part | What to listen for |
| --- | --- | --- |
| 0 s · accepted ignition | [Plucked drone](drone.flac) | The strings move through A2, two slightly detuned D3 strings and D2. The higher partials bloom after each attack. The bass string has the longest gap before the pattern begins again. |
| 10 s | [Low drum](low-drum.flac) | Accents divide each eight beats into 3 + 3 + 2. A pressed stroke bends the pitch and a quieter touch anticipates the next downbeat. A short higher resonance adds definition to the impact. |
| 20 s | [Hand drum](hand-drum.flac) | Ringing strokes answer the bass. Short edge and closed-finger notes fill some of the spaces between the quarter beats. Three quicker strokes turn the last beat into the next downbeat. |
| 30 s | [Reed call](reed.flac) | An A rises through D to E. The answer reaches up to D again and holds. Breath and gaps keep the individual notes distinct across the drums. |
| Confirmed result | [Fire completed · 2.20 s](expiry.flac) · [Fire quenched · 1.60 s](quench.flac) | Expiry sounds a low stroke under a two-note ascending horn call. Quench begins with a filtered breath and three descending plucks. |

The four independent loops share beat zero and a 10-second period. Sixteen quarter beats at 96 BPM fill that period exactly. Successive entrances add density while the tempo holds steady. The recording ends at 40.000 seconds. A completed quench can end a live round earlier, including on the last eligible tick. Play a result cue once the outcome is known. [Objective timing and precedence](../../docs/design/ember-rite-5v5/ROUND_AND_TECH.md)

## Music and source

The composition belongs to YUGA’s fictional Ember Rite. A tanpura-like plucking pattern supplies tonal continuity. The two drum registers suggest hand pressure, ringing skin and rim contact. The closing wind phrase combines a reed-like harmonic edge with the rounded attack of a horn. The pitched material and rhythmic parts are original to this score. All sound comes from mathematical oscillators, seeded noise and a short set of room reflections. The score uses zero recordings, voices or performer models. [Editable score](score.json) · [Synthesis source](build.py) · [YUGA’s earlier traversal music](../../docs/TRAVERSAL_AUDIO_DESIGN.md)

In `score.json`, beat positions begin at zero. String numbers refer to the four `strings` entries. Pitched intervals use semitones above MIDI note 50, D3. Strength changes the relative level of a single stroke. Each stem’s `peak` sets its delivered level. The generator models the bridge, head resonance, reed attack and decay. It wraps the tails and room reflections through the loop boundary. The new synthesis calls the project’s existing envelope, pluck, membrane, air, modal strike and circular placement helpers. [Hanuman instruments](../../tools/audio/build-hanuman-ability-audio.py) · [Traversal helpers](../../tools/audio/build-traversal-audio.py)

For the reference mix, start each new stem at its entry using unity gain and a 12 ms attack. Keep playing the earlier stems. The stereo positions on a −1 to +1 equal-power pan are −0.12 for the drone, centre for the low drum, +0.25 for the hand drum and −0.18 for the reed. Joining a running ritual uses elapsed game time modulo ten seconds as the common source offset. The listening recording has a 12 ms release at 40 seconds. Confirmed result cues carry their own stereo image. [Levels, phase and hashes](manifest.json)

The seven FLAC files listed in the manifest, their original composition and the new synthesis authored for them are dedicated under CC0 1.0 Universal. The voice-guide recordings on the listening desk have their own source and inventory. [CC0 legal text](https://creativecommons.org/publicdomain/zero/1.0/legalcode) · [Voice-guide inventory](voice-guide/lines.json)

## Rebuild and verify

Run from the repository root with Python 3, NumPy, FFmpeg and ffprobe installed. The recorded build used Python 3.12.14, NumPy 2.3.5 and FFmpeg 7.1.5. A fresh output directory reproduced all seven encoded files and the manifest byte for byte.

```sh
python3 games/yuga-native/art/yagna-audio/build.py --check
python3 games/yuga-native/art/yagna-audio/build.py --output /tmp/yuga-score-render
```

Running the generator without an argument updates the music files beside the score. The check reconstructs the PCM, decodes each stored FLAC, compares every sample, checks stream headers and verifies the manifest. To work in a DAW, import the FLAC stems at 96 BPM or convert losslessly to PCM WAV. [Build source](build.py)

```sh
ffmpeg -i games/yuga-native/art/yagna-audio/drone.flac -c:a pcm_s16le /tmp/yuga-drone.wav
```

## Measured playback

Every file contains signed 16-bit PCM at 24 kHz. Each mono stem has 240,000 frames. The stereo audition has 960,000 frames and occupies 1,140,237 bytes. The six files used in the live score occupy 676,414 bytes together. FFmpeg measured **−21.5 LUFS integrated and −7.3 dBTP** on the audition. All seven files passed the clipped-sample check. The largest of the four loop joins spans 35 PCM counts. At that join the same hand-drum loop’s 99.5th-percentile within-loop step is 840 counts. [Per-file and per-section measurements](manifest.json)

| Elapsed section | Stereo RMS, dBFS | Mono energy from 220 Hz to 5 kHz, dBFS |
| --- | ---: | ---: |
| 0–10 s | −25.68 | −29.91 |
| 10–20 s | −24.73 | −29.30 |
| 20–30 s | −24.19 | −27.95 |
| 30–40 s | −21.13 | −22.94 |

The second mix pass addressed the bass drum on narrow-band playback. A 220 Hz to 5 kHz fourth-order Butterworth filter put its initial 150 ms at −31.53 dBFS RMS. Adding short modes centred between 312 and 430 Hz brought that attack to −24.32 dBFS at the same file peak. The table uses direct spectral energy within that band on the final mono sum. These measurements establish the level change. Recognition on phone speakers and real headphones needs player listening. [Final score and renderer](build.py)

Headless Chromium 154.0.8037.57 played all six individual assets through the listening desk and played the stereo audition from zero to its 40.000-second `ended` event at normal speed. A separate 24 kHz `OfflineAudioContext` reconstructed all 960,000 stereo frames from the four loop sources. The largest difference from the downloaded reference was 0.885 of one signed 16-bit PCM count, with an RMS difference of 0.296 count. [Listening desk](index.html) · [Rehearsal browser checks](../../docs/design/ember-rite-5v5/atlas/rehearsal/audio.browser.test.mjs)
