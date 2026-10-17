#!/usr/bin/env python3
"""Build/check original siege cues using only the Python standard library.

The output is short mono PCM16 at 24 kHz. Synthesis is additive and uses an
explicit integer PRNG, never a recording, sample pack, or borrowed tune.
--check reconstructs all bytes and checks the provenance and lossless import
settings. Mix bounds describe six siege voices at -12 dB, not listener approval.
"""

import argparse
import hashlib
import io
import json
import math
from pathlib import Path
import struct
import sys
import wave


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "assets/audio/siege"
MANIFEST = OUT / "provenance.json"
RATE = 24_000
SEED = 2026101723
MAX_VOICES = 6
VOICE_GAIN_DB = -12
SOURCE_PEAK_BOUND = 0.120
EXISTING_SUBSYSTEM_BOUND = 0.561
SPECS = {
    "cannon_windup": {"duration": 0.58, "peak": 0.115, "attack": 0.018,
                       "description": "Rising low brass-like harmonic swell; three quiet wood pulses."},
    "cannon_impact": {"duration": 0.52, "peak": 0.120, "attack": 0.003,
                       "description": "Falling membrane-like strike, filtered air transient, low metal tail."},
    "chariot_windup": {"duration": 0.66, "peak": 0.105, "attack": 0.012,
                        "description": "Three paired wood-like strokes under a restrained rising horn."},
    "chariot_impact": {"duration": 0.60, "peak": 0.115, "attack": 0.003,
                        "description": "Lower drum-like strike with a brief offset wood knock and harmonic ring."},
}


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def fade(t, duration, attack, release):
    """Raised-cosine edges, exactly zero outside the declared event."""
    if t <= 0 or t >= duration:
        return 0.0
    leading = math.sin(math.pi * min(t / attack, 1.0) / 2) ** 2
    trailing = math.sin(math.pi * min((duration - t) / release, 1.0) / 2) ** 2
    return leading * trailing


def filtered_noise(count, seed):
    """Xorshift32 uniform noise followed by a modest one-pole low-pass."""
    state = seed & 0xFFFFFFFF
    previous = 0.0
    result = []
    for _ in range(count):
        state ^= (state << 13) & 0xFFFFFFFF
        state ^= state >> 17
        state ^= (state << 5) & 0xFFFFFFFF
        state &= 0xFFFFFFFF
        uniform = 2 * (state / 0xFFFFFFFF) - 1
        previous += 0.32 * (uniform - previous)
        result.append(previous)
    return result


def brass(t, initial_hz, slope_hz_per_second):
    phase = math.tau * (initial_hz * t + 0.5 * slope_hz_per_second * t * t)
    return sum(weight * math.sin(harmonic * phase)
               for harmonic, weight in ((1, 0.62), (2, 0.22), (3, 0.10), (4, 0.05)))


def wood(t, frequency, duration=0.15):
    if t <= 0 or t >= duration:
        return 0.0
    modes = (math.sin(math.tau * frequency * t) * math.exp(-28 * t)
             + 0.30 * math.sin(math.tau * frequency * 2.37 * t) * math.exp(-45 * t)
             + 0.12 * math.sin(math.tau * frequency * 3.91 * t) * math.exp(-65 * t))
    return modes * fade(t, duration, 0.0025, 0.025)


def drum(t, base_hz, drop_hz):
    # Integrating f(t)=base+drop*exp(-t/0.024) avoids an incorrect chirp phase.
    phase = math.tau * (base_hz * t + drop_hz * 0.024 * (1 - math.exp(-t / 0.024)))
    return (math.sin(phase) * math.exp(-10 * t)
            + 0.31 * math.sin(1.59 * phase) * math.exp(-16 * t)
            + 0.12 * math.sin(2.13 * phase) * math.exp(-24 * t))


def synthesize(name, spec, index):
    count = round(spec["duration"] * RATE)
    noise = filtered_noise(count, SEED + index)
    values = []
    for frame in range(count):
        t = frame / RATE
        u = t / spec["duration"]
        if name == "cannon_windup":
            value = brass(t, 136, 140) * (0.23 + 0.77 * u)
            value += sum(0.22 * wood(t - at, 420) for at in (0.03, 0.20, 0.37))
        elif name == "cannon_impact":
            value = drum(t, 82, 96)
            value += 0.15 * noise[frame] * math.exp(-42 * t)
            value += 0.20 * brass(t, 174, -32) * math.exp(-8 * t)
        elif name == "chariot_windup":
            value = 0.32 * brass(t, 208, 70) * (0.35 + 0.65 * u)
            for at, strength in ((0.015, 0.55), (0.205, 0.70), (0.395, 0.85)):
                value += strength * wood(t - at, 306)
                value += 0.40 * strength * wood(t - at - 0.055, 520)
        elif name == "chariot_impact":
            value = drum(t, 63, 52)
            value += 0.35 * wood(t - 0.035, 356, 0.20)
            value += 0.16 * brass(t, 245, -18) * math.exp(-9 * t)
            value += 0.10 * noise[frame] * math.exp(-50 * t)
        else:
            raise ValueError("Unknown cue: " + name)
        values.append(value * fade(t, spec["duration"], spec["attack"], 0.060))
    magnitude = max(abs(value) for value in values)
    if not math.isfinite(magnitude) or magnitude <= 0:
        raise ValueError("Invalid synthesis output: " + name)
    pcm = [round(value * spec["peak"] / magnitude * 32767) for value in values]
    pcm[0] = pcm[-1] = 0
    return pcm


def encode(pcm):
    output = io.BytesIO()
    with wave.open(output, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(RATE)
        wav.writeframes(struct.pack("<" + "h" * len(pcm), *pcm))
    return output.getvalue()


def importer(name):
    source = "res://assets/audio/siege/" + name + ".wav"
    cache = "res://.godot/imported/" + name + ".wav-" + hashlib.md5(source.encode()).hexdigest() + ".sample"
    # Twelve a-p characters fit a Godot UID and are stable across regeneration.
    uid = "".join(chr(ord("a") + int(nibble, 16)) for nibble in sha256(source.encode())[:12]).lstrip("a") or "b"
    return f'''[remap]

importer="wav"
type="AudioStreamWAV"
uid="uid://{uid}"
path="{cache}"

[deps]

source_file="{source}"
dest_files=["{cache}"]

[params]

force/8_bit=false
force/mono=false
force/max_rate=false
force/max_rate_hz=44100
edit/trim=false
edit/normalize=false
edit/loop_mode=0
edit/loop_begin=0
edit/loop_end=-1
compress/mode=0
'''


def build():
    encoded, records = {}, []
    for index, (name, spec) in enumerate(SPECS.items()):
        pcm = synthesize(name, spec, index)
        data = encode(pcm)
        encoded[name + ".wav"] = data
        encoded[name + ".wav.import"] = importer(name).encode()
        peak = max(abs(sample) for sample in pcm) / 32767
        rms = math.sqrt(sum((sample / 32767) ** 2 for sample in pcm) / len(pcm))
        if peak > SOURCE_PEAK_BOUND or not 0 < len(pcm) / RATE <= 0.7 or pcm[0] != 0 or pcm[-1] != 0:
            raise ValueError("Cue level, duration or endpoint outside contract: " + name)
        records.append({
            "asset": "assets/audio/siege/" + name + ".wav", "kind": name,
            "bytes": len(data), "sha256": sha256(data), "sample_rate": RATE,
            "channels": 1, "sample_width_bytes": 2, "format": "PCM16 little-endian",
            "sample_frames": len(pcm), "duration_seconds": len(pcm) / RATE,
            "peak_linear": round(peak, 12), "rms_linear": round(rms, 12),
            "endpoint_samples": [pcm[0], pcm[-1]], "seed": SEED + index,
            "attack_seconds": spec["attack"], "release_seconds": 0.060,
            "description": spec["description"],
            "import_settings_sha256": sha256(encoded[name + ".wav.import"]),
        })
    if len({row["sha256"] for row in records}) != len(SPECS):
        raise ValueError("Cue waveforms must be distinct")
    siege_bound = MAX_VOICES * SOURCE_PEAK_BOUND * 10 ** (VOICE_GAIN_DB / 20)
    combined_bound = siege_bound + EXISTING_SUBSYSTEM_BOUND
    if combined_bound >= 1:
        raise ValueError("Declared combined subsystem budget clips")
    manifest = {
        "schema": 1, "title": "Original cannon and chariot siege cues", "license": "CC0-1.0",
        "authorship": "Original additive synthesis authored for YUGA; no recordings, sampled instruments, borrowed tune or commercial-game audio.",
        "generator": str(Path(__file__).resolve().relative_to(ROOT)),
        "generator_sha256": sha256(Path(__file__).read_bytes()),
        "dependencies": "Python standard library only: math, wave, struct, hashlib and JSON; no external packages.",
        "synthesis": {
            "brass": "Sum of harmonics 1,2,3,4 at weights 0.62,0.22,0.10,0.05; phase=2*pi*(f0*t+0.5*slope*t^2).",
            "wood": "Damped sine modes at ratios 1,2.37,3.91, weighted 1,0.30,0.12; exponential decay rates 28,45,65 s^-1.",
            "drum": "Damped modes 1,1.59,2.13; integrated exponential frequency fall with 0.024 s time constant; no physical-instrument fidelity claim.",
            "noise": "Explicit Xorshift32 seeded per cue, normalized to [-1,1], one-pole smoothing coefficient 0.32; only short impact transients.",
            "envelope": "Raised-cosine attack/release, final sample explicitly zero; normalized to each declared peak before PCM16 rounding.",
            "culture": "Warm brass/wood-drum-inspired game cues, not an authentic raga/tala performance or historical instrument reconstruction.",
        },
        "mix_budget": {
            "max_siege_voices": MAX_VOICES, "per_voice_gain_db": VOICE_GAIN_DB,
            "per_voice_peak_upper_bound": SOURCE_PEAK_BOUND,
            "siege_amplitude_upper_bound": round(siege_bound, 12),
            "siege_headroom_db": round(-20 * math.log10(siege_bound), 12),
            "assumed_existing_traversal_subsystem_upper_bound": EXISTING_SUBSYSTEM_BOUND,
            "combined_amplitude_upper_bound": round(combined_bound, 12),
            "combined_headroom_db": round(-20 * math.log10(combined_bound), 12),
            "assumptions": "Six siege voices maximum, volume <=1, each player gain and positional max gain <=-12 dB. Existing traversal subsystem separately bounded at <=0.561. No other audio, effect gain or bus amplification included; runtime integration must enforce these conditions.",
        },
        "references": [{"path": "docs/TRAVERSAL_AUDIO_DESIGN.md", "scope": "Existing project synthesis/mix conventions reviewed; no waveform or melody copied."}],
        "limitations": "Byte, PCM level, endpoint and distinction checks only. No human listening, perception, historical authenticity or physiological-benefit approval. Distinct hashes do not establish perceptual discrimination.",
        "assets": records,
    }
    encoded[MANIFEST.name] = (json.dumps(manifest, indent=2) + "\n").encode()
    return encoded, manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Check exact committed bytes; never rewrite assets.")
    parser.add_argument("--report", type=Path, help="Optional JSON result, including a failed verification.")
    args = parser.parse_args()
    report = {"passed": False, "mode": "check" if args.check else "generate"}
    try:
        encoded, manifest = build()
        if OUT.is_symlink():
            raise ValueError("Refusing symlinked siege output directory")
        if args.check:
            if not OUT.is_dir() or {path.name for path in OUT.iterdir()} != set(encoded):
                raise ValueError("Siege file inventory differs from declared assets/imports/provenance")
            for name, data in encoded.items():
                path = OUT / name
                if path.is_symlink() or not path.is_file() or path.read_bytes() != data:
                    raise ValueError("Missing, changed or symlinked expected siege file: " + name)
        else:
            OUT.mkdir(parents=True, exist_ok=True)
            for name, data in encoded.items():
                path = OUT / name
                if path.is_symlink():
                    raise ValueError("Refusing symlinked output: " + name)
                path.write_bytes(data)
        report.update({"passed": True, "assets": len(SPECS), "verified_files": len(encoded),
                       "total_wav_bytes": sum(row["bytes"] for row in manifest["assets"]),
                       "generator_sha256": manifest["generator_sha256"], "mix_budget": manifest["mix_budget"],
                       "all_cues_zero_endpoints": True, "all_assets_distinct_and_deterministic": True,
                       "records": manifest["assets"], "limitations": manifest["limitations"]})
    except (OSError, ValueError, struct.error) as error:
        report["error"] = str(error)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
