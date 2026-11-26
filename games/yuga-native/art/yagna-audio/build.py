#!/usr/bin/env python3
"""Render and verify the YUGA score in score.json. Requires NumPy, ffmpeg and ffprobe."""

import argparse
import hashlib
import importlib.util
import json
import math
import re
import subprocess
import tempfile
from pathlib import Path

import numpy as np


HERE = Path(__file__).resolve().parent
NATIVE = HERE.parents[1]
HELPERS = NATIVE / "tools/audio/build-hanuman-ability-audio.py"
TRAVERSAL = NATIVE / "tools/audio/build-traversal-audio.py"
SCORE = HERE / "score.json"

# Reuse YUGA's pluck, membrane, air, envelope and circular placement instruments.
spec = importlib.util.spec_from_file_location("yuga_instruments", HELPERS)
instruments = importlib.util.module_from_spec(spec)
spec.loader.exec_module(instruments)
audio = instruments.audio
RATE = audio.RATE
TAU = math.tau


def clock(seconds):
    return np.arange(round(seconds * RATE), dtype=np.float64) / RATE


def pitch(tonic, interval, cents=0):
    return 440 * 2 ** ((tonic - 69 + interval + cents / 100) / 12)


def scale_peak(signal, peak):
    amplitude = np.max(np.abs(signal))
    if not np.isfinite(amplitude) or amplitude < 1e-6 or not 0 < peak < 1:
        raise ValueError("Invalid signal or peak in score")
    return signal * (peak / amplitude)


def string_pluck(frequency, pick_position, rng):
    """A plucked string whose upper partials bloom against the bridge and then recede."""
    t = clock(5.1)
    phase = TAU * frequency * (t + 0.00032 * -np.expm1(-20 * t))
    sound = np.zeros_like(t)
    for harmonic in range(1, 24):
        hz = harmonic * frequency
        body = 0.78 + 0.60 * np.exp(-((hz - 565) / 245) ** 2)
        bridge = 0.45 + 0.55 * -np.expm1(-t * (5.2 + 9 / harmonic))
        decay = np.exp(-t * (0.57 + 0.065 * harmonic ** 1.13))
        weight = np.sin(np.pi * harmonic * pick_position) / harmonic ** 1.26
        # Tiny inharmonicity and pitch drift separate successive string attacks.
        partial = harmonic * phase * (1 + 0.0000025 * harmonic ** 2)
        sound += weight * body * bridge * decay * np.sin(partial + 0.15 * harmonic)
    sound += 0.09 * instruments.air(t, rng, 14) * np.exp(-50 * t)
    return sound * audio.envelope(len(t), 0.008, 0.23)


def bass_stroke(kind, rng):
    # Duration, resting pitch, initial downward glide, hand pressure after the attack.
    duration, hz, drop, pressure = {
        "open": (0.72, 81, 48, 0), "bend": (0.77, 79, 71, 13), "touch": (0.23, 116, 30, 0)
    }[kind]
    t = clock(duration)
    frequency = hz + drop * np.exp(-44 * t) + pressure * np.exp(-((t - 0.16) / 0.09) ** 2)
    phase = TAU * (np.cumsum(frequency) - frequency[0]) / RATE
    decay = 4.9 if kind != "touch" else 20
    body = np.sin(phase) * np.exp(-decay * t)
    body += 0.48 * np.sin(1.54 * phase + 0.12) * np.exp(-(decay + 3.7) * t)
    body += 0.27 * np.sin(2.34 * phase) * np.exp(-(decay + 8) * t)
    body += 0.14 * np.sin(3.12 * phase) * np.exp(-(decay + 13) * t)
    contact = audio.membrane(hz * 1.95, duration, rng, bright=True)
    # The short, higher head resonance carries the low stroke on a small speaker.
    edge_hz = {"open": 345, "bend": 312, "touch": 430}[kind]
    edge = instruments.modes(t, edge_hz, (1, 1.43, 2.45, 3.28), 10 if kind == "open" else 14)
    return (body + 0.16 * contact + 0.72 * edge) * audio.envelope(len(t), 0.0025, 0.07)


def treble_stroke(kind, rng):
    # Ringing syllable, short edge slap, or damped finger contact.
    hz, duration, decay, skin = {
        "ring": (285, 0.48, 8, 0.17), "edge": (415, 0.23, 20, 0.38), "closed": (325, 0.15, 34, 0.32)
    }[kind]
    t = clock(duration)
    phase = TAU * (hz * t + 0.36 * -np.expm1(-55 * t))
    body = np.zeros_like(t)
    for ratio, level in ((1, 1.0), (2.01, 0.55), (3.03, 0.36), (4.19, 0.15), (5.18, 0.09)):
        body += level * np.sin(ratio * phase) * np.exp(-(decay + 2.6 * ratio) * t)
    brush = instruments.air(t, rng, 6) * np.exp(-65 * t)
    return (body + skin * brush) * audio.envelope(len(t), 0.0018, 0.045)


def reed_note(hz, duration, rng, roundness=0.60):
    t = clock(duration)
    # Integrate the initial scoop and gently delayed vibrato to keep phases continuous.
    cents = -37 * np.exp(-18 * t) + 9 * np.sin(TAU * 4.8 * t) * -np.expm1(-3.3 * t)
    frequency = hz * 2 ** (cents / 1200)
    phase = TAU * (np.cumsum(frequency) - frequency[0]) / RATE
    sound = np.zeros_like(t)
    for harmonic in range(1, 15):
        partial_hz = harmonic * hz
        formant = np.exp(-((partial_hz - 730) / 260) ** 2) + 0.37 * np.exp(-((partial_hz - 1450) / 360) ** 2)
        weight = (0.76 + 1.4 * formant) / harmonic ** 1.28
        if harmonic % 2 == 0:
            weight *= roundness
        sound += weight * np.sin(harmonic * phase + 0.09 * harmonic)
    air = instruments.air(t, rng, 7)
    sound += air * (0.085 + 0.42 * np.exp(-18 * t))
    swell = (0.80 + 0.20 * np.sin(np.pi * t / duration)) * (1 + 0.024 * np.sin(TAU * 4.8 * t))
    return sound * swell * audio.envelope(len(t), min(0.085, duration / 6), min(0.13, duration / 3))


def room(signal, circular):
    result = signal.copy()
    for seconds, level in ((0.019, 0.12), (0.043, 0.083), (0.077, 0.060), (0.123, 0.035), (0.171, 0.020)):
        offset = round(seconds * RATE)
        if circular:
            result += level * np.roll(signal, offset, axis=0)
        else:
            result[offset:] += level * signal[:-offset]
    return result


def render_stem(name, part, score, beat_seconds, rng):
    result = np.zeros(round(score["loop_beats"] * beat_seconds * RATE))
    tonic = score["tonic_midi"]
    if name == "reed":
        for beat, length, interval, strength in part["notes"]:
            event = reed_note(pitch(tonic, interval), length * beat_seconds, rng)
            audio.add_circular(result, event * strength, beat * beat_seconds)
    else:
        for beat, stroke, strength in part["strokes"]:
            if name == "drone":
                string = part["strings"][stroke]
                hz = pitch(tonic, string["interval"], string["cents"])
                event = string_pluck(hz, string["pick"], rng)
            elif name == "low-drum":
                event = bass_stroke(stroke, rng)
            else:
                event = treble_stroke(stroke, rng)
            audio.add_circular(result, event * strength, beat * beat_seconds)
    return scale_peak(room(result, circular=True), part["peak"])


def stereo(signal, pan):
    # Web Audio StereoPannerNode uses this equal-power law for a mono input.
    angle = (pan + 1) * np.pi / 4
    return np.column_stack((signal * np.cos(angle), signal * np.sin(angle)))


def render_sting(name, part, tonic, rng):
    sound = np.zeros((round(part["seconds"] * RATE), 2))

    def add(seconds, sample, gain, pan):
        start = round(seconds * RATE)
        length = min(len(sound) - start, len(sample))
        sound[start:start + length] += gain * stereo(sample[:length], pan)

    if name == "expiry":
        add(0, bass_stroke("open", rng), 0.76, 0)
        add(0, reed_note(pitch(tonic, 7), 0.42, rng, 0.94), 0.78, -0.12)
        add(0.37, reed_note(pitch(tonic, 12), 1.12, rng, 0.94), 0.75, -0.12)
        add(0.38, audio.pluck(pitch(tonic, 19), 1.69), 0.40, 0.27)
        add(0.60, audio.pluck(pitch(tonic, 12), 1.52), 0.46, 0.12)
    else:
        t = clock(0.97)
        hush = instruments.air(t, rng, 9) * np.exp(-5.0 * t) * audio.envelope(len(t), 0.017, 0.13)
        add(0, hush, 0.57, 0)
        for onset, interval, gain, pan in ((0.014, 19, 0.76, 0.22), (0.17, 12, 0.71, 0), (0.41, 0, 0.86, -0.22)):
            add(onset, audio.pluck(pitch(tonic, interval), 1.08), gain, pan)
    sound = room(sound, circular=False) * audio.envelope(len(sound), 0.003, 0.09)[:, None]
    return scale_peak(sound, part["peak"])


def pcm16(signal):
    if not np.isfinite(signal).all() or np.max(np.abs(signal)) >= 1:
        raise ValueError("PCM must be finite and below full scale")
    return np.rint(signal * 32767).astype("<i2")


def render_mix(score, stems):
    frames = round(score["ritual_seconds"] * RATE)
    fade = round(score["entry_fade_seconds"] * RATE)
    ramp = np.linspace(0, 1, fade)
    mix = np.zeros((frames, 2))
    for name, part in score["stems"].items():
        offset = round(part["entry_seconds"] * RATE)
        signal = np.resize(stems[name], frames - offset).astype(np.float64) / 32768
        signal[:fade] *= ramp
        mix[offset:] += stereo(signal, part["pan"])
    mix[-fade:] *= ramp[::-1, None]
    return pcm16(mix)


def render(score):
    beat_seconds = 60 / score["tempo_bpm"]
    if score["sample_rate_hz"] != RATE or score["loop_beats"] * beat_seconds != 10:
        raise ValueError("Score must agree with the rehearsal's 10 s / 24 kHz stem contract")
    entries = [(name, part["entry_seconds"]) for name, part in score["stems"].items()]
    if entries != [("drone", 0), ("low-drum", 10), ("hand-drum", 20), ("reed", 30)] or score["ritual_seconds"] != 40:
        raise ValueError("Score entries must agree with the public ritual clock")
    stems = {}
    for index, (name, part) in enumerate(score["stems"].items()):
        rng = np.random.default_rng(score["seed"] + index)
        stems[name] = pcm16(render_stem(name, part, score, beat_seconds, rng))
    output = {**stems, "ritual-mix": render_mix(score, stems)}
    for index, (name, part) in enumerate(score["outcomes"].items(), start=len(stems)):
        rng = np.random.default_rng(score["seed"] + index)
        output[name] = pcm16(render_sting(name, part, score["tonic_midi"], rng))
    return output


def ffmpeg(*args, data=None):
    return subprocess.run(["ffmpeg", "-hide_banner", "-nostdin", "-nostats", "-threads", "1", *args],
                          input=data, capture_output=True, check=True)


def encode(path, pcm):
    channels = 1 if pcm.ndim == 1 else pcm.shape[1]
    ffmpeg("-v", "error", "-f", "s16le", "-ar", str(RATE), "-ac", str(channels), "-i", "pipe:0",
           "-map_metadata", "-1", "-bitexact", "-c:a", "flac", "-compression_level", "8", "-y", str(path), data=pcm.tobytes())


def decode_check(path, pcm):
    fields = "stream=codec_name,sample_rate,channels,bits_per_raw_sample,duration_ts,time_base"
    probe = subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", fields, "-of", "json", str(path)])
    channels = 1 if pcm.ndim == 1 else pcm.shape[1]
    expected = {"codec_name": "flac", "sample_rate": str(RATE), "channels": channels, "bits_per_raw_sample": "16",
                "time_base": f"1/{RATE}", "duration_ts": len(pcm)}
    if json.loads(probe)["streams"] != [expected]:
        raise ValueError(f"Unexpected audio format or length in {path}")
    result = ffmpeg("-v", "error", "-i", str(path), "-f", "s16le", "pipe:1")
    if result.stdout != pcm.tobytes():
        raise ValueError(f"Decoded {path} differs from the score")


def db(value):
    return round(20 * math.log10(value), 3)


def levels(pcm):
    samples = pcm.astype(np.float64) / 32768
    return {"sample_peak_dbfs": db(np.max(np.abs(samples))), "rms_dbfs": db(np.sqrt(np.mean(samples ** 2)))}


def mono_midband_level(pcm):
    samples = pcm.astype(np.float64) / 32768
    mono = samples if samples.ndim == 1 else samples.mean(axis=1)
    weights = np.fft.rfft(mono) / len(mono)
    frequencies = np.fft.rfftfreq(len(mono), 1 / RATE)
    band = weights[(frequencies >= 220) & (frequencies <= 5000)]
    # These bins omit DC and Nyquist, so their positive and negative powers match.
    return db(np.sqrt(2 * np.sum(np.abs(band) ** 2)))


def loudness(path):
    result = ffmpeg("-v", "info", "-i", str(path), "-filter_threads", "1", "-af", "ebur128=peak=true:framelog=verbose", "-f", "null", "-")
    report = result.stderr.decode().rsplit("Summary:", 1)[-1]
    integrated = re.search(r"\bI:\s+([-\d.]+) LUFS", report)
    peak = re.search(r"\bPeak:\s+([-\d.]+) dBFS", report)
    if not integrated or not peak:
        raise ValueError(f"Missing EBU R128 measurement for {path}")
    return {"integrated_lufs": float(integrated[1]), "true_peak_dbtp": float(peak[1])}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inspect_asset(path, pcm, is_loop):
    decode_check(path, pcm)
    stats = {"file": path.name, "sha256": sha(path), "bytes": path.stat().st_size,
             "frames": len(pcm), "seconds": len(pcm) / RATE, "channels": 1 if pcm.ndim == 1 else pcm.shape[1],
             **levels(pcm), "mono_220_to_5000_hz_rms_dbfs": mono_midband_level(pcm), **loudness(path),
             "clipped_samples": int(np.count_nonzero((pcm >= 32767) | (pcm <= -32767)))}
    if stats["clipped_samples"] or stats["true_peak_dbtp"] > -3:
        raise ValueError(f"Insufficient headroom in {path}")
    if is_loop:
        samples = pcm.astype(np.int32)
        seam = int(abs(samples[0] - samples[-1]))
        limit = float(np.percentile(np.abs(np.diff(samples)), 99.5))
        if seam > max(3, limit):
            raise ValueError(f"Loop seam exceeds normal sample steps in {path}")
        stats.update(loop_step_pcm16=seam, within_loop_step_p995_pcm16=round(limit, 1))
    elif np.any(pcm[0]) or np.any(pcm[-1]):
        raise ValueError(f"One-shot {path} must begin and end at digital zero")
    return stats


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", "--verify", action="store_true", help="Verify the stored FLACs and manifest against fresh PCM")
    parser.add_argument("--output", type=Path, default=HERE, help="Destination for generated files, or files to verify")
    args = parser.parse_args()
    score = json.loads(SCORE.read_text())
    output = render(score)
    with tempfile.TemporaryDirectory() as temp:
        folder = args.output if args.check else Path(temp)
        assets = {}
        for name, pcm in output.items():
            path = folder / f"{name}.flac"
            if not args.check:
                encode(path, pcm)
            assets[name] = inspect_asset(path, pcm, name in score["stems"])
        sources = {p.relative_to(NATIVE).as_posix(): sha(p) for p in (Path(__file__).resolve(), SCORE, HELPERS, TRAVERSAL)}
        sections = []
        for start in (0, 10, 20, 30):
            section = output["ritual-mix"][start * RATE:(start + 10) * RATE]
            sections.append({"start_seconds": start, "end_seconds": start + 10, **levels(section),
                             "mono_220_to_5000_hz_rms_dbfs": mono_midband_level(section)})
        manifest = {"title": score["title"], "asset_license": "CC0-1.0",
                    "origin": "Original score, numerical synthesis and rendered audio for YUGA.", "source_sha256": sources,
                    "sample_rate_hz": RATE, "format": "FLAC, signed 16-bit PCM", "tempo_bpm": score["tempo_bpm"],
                    "loop_beats": score["loop_beats"], "loop_seconds": 10, "ritual_seconds": score["ritual_seconds"],
                    "entry_fade_seconds": score["entry_fade_seconds"],
                    "stems": {name: {"entry_seconds": part["entry_seconds"], "pan": part["pan"], "gain": 1}
                              for name, part in score["stems"].items()}, "mix_sections": sections, "assets": assets}
        text = json.dumps(manifest, indent=2) + "\n"
        if args.check:
            if json.loads((folder / "manifest.json").read_text()) != manifest:
                raise ValueError("Manifest differs from regenerated and measured assets")
        else:
            args.output.mkdir(parents=True, exist_ok=True)
            for name in output:
                file = f"{name}.flac"
                (args.output / file).write_bytes((folder / file).read_bytes())
            (args.output / "manifest.json").write_text(text)
    demo = assets["ritual-mix"]
    print(f"Verified {len(assets)} lossless files; mix {demo['seconds']:.3f} s, "
          f"{demo['integrated_lufs']} LUFS, {demo['true_peak_dbtp']} dBTP. "
          f"Total {sum(item['bytes'] for item in assets.values()):,} bytes.")


if __name__ == "__main__":
    main()
