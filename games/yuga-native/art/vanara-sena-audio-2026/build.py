#!/usr/bin/env python3
"""Build/check one original, deterministic Vanara Sena release cue.

The synthesized timbres reuse this repository's Hanuman/traversal DSP helpers;
they are not recordings of conch, bells, drums, chanting or music.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import wave
import io

import numpy as np

HERE = Path(__file__).resolve().parent
NATIVE = HERE.parents[1]
TOOLS = NATIVE / "tools/audio"
OUTPUT = NATIVE / "assets/audio/hanuman-trial/vanara_sena.wav"
NOTICE = NATIVE / "NOTICE/VANARA_SENA_AUDIO.json"
PARAMETERS = HERE / "parameters.json"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def load_helpers():
    spec = importlib.util.spec_from_file_location("yuga_hanuman_audio", TOOLS / "build-hanuman-ability-audio.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def produce():
    cfg = json.loads(PARAMETERS.read_text())
    if cfg["schema_version"] != 1 or cfg["id"] != "vanara_sena":
        raise ValueError("Unsupported cue parameters")
    hanuman = load_helpers()
    audio = hanuman.audio
    rate = cfg["sample_rate_hz"]
    if rate != audio.RATE:
        raise ValueError("Parameters must use the existing 24 kHz synthesis contract")
    duration = cfg["duration_seconds"]
    if not 0.1 <= duration <= 2 or not 0 < cfg["peak_linear"] <= 0.25:
        raise ValueError("Cue duration or peak is outside the authored budget")
    t = np.arange(round(duration * rate), dtype=np.float64) / rate
    rng = np.random.default_rng(cfg["seed"])

    # A rising harmonic breath. The integrated frequency keeps phase continuous.
    phase = np.pi * 2 * (cfg["horn_base_hz"] * t + cfg["horn_pitch_rise_hz"] * t * t / (2 * duration))
    horn_envelope = (1 - np.exp(-23 * t)) * np.exp(-3.7 * t)
    horn = (np.sin(phase) + .32 * np.sin(phase * 2) + .12 * np.sin(phase * 3)) * horn_envelope

    # Reuse the project's additive struck-body, membrane and pluck functions.
    bronze = hanuman.after(cfg["bell_delay_seconds"], hanuman.modes(t, cfg["bell_hz"], (1, 2.01, 3.18), 7.5))
    drum = hanuman.after(cfg["membrane_delay_seconds"], audio.membrane(cfg["membrane_hz"], duration, rng))
    pluck = hanuman.after(cfg["pluck_delay_seconds"], audio.pluck(cfg["pluck_hz"], duration, .5))
    air = hanuman.air(t, rng, width=cfg["wind_filter_width"]) * np.sin(np.pi * t / duration) ** 2
    raw = .64 * horn + .19 * bronze + .16 * drum + .12 * pluck + .16 * air
    raw *= audio.envelope(len(t), cfg["fade_in_seconds"], cfg["fade_out_seconds"])
    if not np.isfinite(raw).all() or np.max(np.abs(raw)) < 1e-9:
        raise ValueError("Cue is silent or non-finite")
    raw *= cfg["peak_linear"] / np.max(np.abs(raw))
    data, pcm = audio.encode(raw)
    if pcm[0] != 0 or pcm[-1] != 0 or np.max(np.abs(pcm.astype(np.int32))) >= 32767:
        raise ValueError("Cue endpoint or PCM headroom check failed")
    with wave.open(io.BytesIO(data), "rb") as wav:
        if (wav.getnchannels(), wav.getsampwidth(), wav.getframerate(), wav.getnframes()) != (1, 2, rate, len(t)):
            raise ValueError("Unexpected WAV format")

    peak = float(np.max(np.abs(pcm.astype(np.float64))) / 32767)
    rms = float(np.sqrt(np.mean((pcm.astype(np.float64) / 32767) ** 2)))
    stats = {
        "path": "assets/audio/hanuman-trial/vanara_sena.wav",
        "sha256": digest(data),
        "bytes": len(data),
        "frames": len(pcm),
        "sample_rate_hz": rate,
        "duration_seconds": len(pcm) / rate,
        "channels": 1,
        "format": "PCM16",
        "peak_linear": round(peak, 8),
        "peak_dbfs": round(20 * np.log10(peak), 2),
        "rms_dbfs": round(20 * np.log10(rms), 2),
        "max_sample_step": round(float(np.max(np.abs(np.diff(pcm.astype(np.int32)))) / 32767), 8),
        "zero_first_and_last_sample": bool(pcm[0] == 0 and pcm[-1] == 0),
        "clipped_samples": int(np.count_nonzero(np.abs(pcm.astype(np.int32)) >= 32767)),
    }
    notice = {
        "schema_version": 1,
        "source": "Original deterministic mathematical synthesis for YUGA; no recordings, voices, sampled instruments or borrowed melodies.",
        "cue": "Soft harmonic horn-like breath, struck-metal overtone, wooden/membrane pulse and wind.",
        "generator": "art/vanara-sena-audio-2026/build.py",
        "generator_sha256": digest(Path(__file__).read_bytes()),
        "parameters": "art/vanara-sena-audio-2026/parameters.json",
        "parameters_sha256": digest(PARAMETERS.read_bytes()),
        "reused_project_helpers": ["tools/audio/build-hanuman-ability-audio.py", "tools/audio/build-traversal-audio.py"],
        "numpy_version": np.__version__,
        "file": stats,
        "limitations": "Instrument timbres are synthesized approximations, not claims of sacred vocal performance or a named raga. Numerical checks do not replace human listening or runtime mix review.",
    }
    return data, notice


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Compare regenerated bytes and provenance with the repository files")
    parser.add_argument("--report", type=Path, help="Optional path for a compact check report")
    args = parser.parse_args()
    data, notice = produce()
    text = json.dumps(notice, indent=2) + "\n"
    if args.check:
        if OUTPUT.read_bytes() != data or NOTICE.read_text() != text:
            raise ValueError("Cue or notice differs from deterministic regeneration")
    else:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        NOTICE.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_bytes(data)
        NOTICE.write_text(text)
    result = {"passed": True, "mode": "check" if args.check else "generate", **notice["file"],
              "listening_review": "not performed", "runtime_mix_review": "not performed"}
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
