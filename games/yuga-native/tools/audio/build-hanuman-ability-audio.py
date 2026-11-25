"""Generate the six original action cues used by the Hanuman trial."""

import argparse
from hashlib import sha256
import importlib.util
import json
from pathlib import Path

import numpy as np


TOOLS = Path(__file__).resolve().parent
NATIVE = TOOLS.parents[1]
OUTPUT = NATIVE / "assets/audio/hanuman-trial"
NOTICE = NATIVE / "NOTICE/HANUMAN-ABILITY-AUDIO.json"
spec = importlib.util.spec_from_file_location("traversal_audio", TOOLS / "build-traversal-audio.py")
audio = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audio)
RATE = audio.RATE
TAU = 2 * np.pi


def modes(t, fundamental, ratios, decay):
    """Ring a struck object. Its higher partials decay sooner."""
    return sum(np.sin(TAU * fundamental * r * t) * np.exp(-decay * (1 + r*.23) * t) / r
               for r in ratios)


def air(t, rng, width=6):
    noise = rng.standard_normal(len(t) + width - 1)
    return np.convolve(noise, np.hanning(width) / np.hanning(width).sum(), mode="valid")


def after(seconds, signal):
    offset = round(seconds * RATE)
    result = np.zeros_like(signal)
    result[offset:] = signal[:len(signal) - offset]
    return result


def gada(t, rng):
    brush = air(t,rng) * np.exp(-32*t)
    edge = modes(t, 288, (1, 2.68, 4.11, 5.38), 12)
    return .52*brush + after(.022, .72*edge + .39*audio.membrane(106, len(t)/RATE, rng))


def ward(t, rng):
    bronze = modes(t, 440, (1, 2.01, 3, 4.16), 5)
    answer = audio.pluck(660, len(t)/RATE)
    return .72*bronze + .47*after(.066, answer) + .25*after(.145, audio.pluck(880, len(t)/RATE))


def vault(t, rng):
    breath = air(t, rng, width=10) * np.sin(np.pi * t / (len(t)/RATE))**1.3
    upward = np.sin(TAU*(177*t + 630*t*t)) * np.exp(-5*t)
    return .85*breath + .26*upward + .28*audio.membrane(140, len(t)/RATE, rng)


def embers(t, rng):
    spray = air(t,rng,width=4)
    sweep = np.sin(np.pi*t/(len(t)/RATE))**1.2
    crackles = sum(np.exp(-135*np.abs(t-at))*np.sin(TAU*hz*t)
                   for at,hz in ((.037,820),(.085,1270),(.18,620),(.285,1030)))
    return (.34 + .25*np.cos(TAU*7*t))*spray*sweep + .42*crackles


def mountain(t, rng):
    rise = (1-np.exp(-14*t))*np.exp(-4*t)
    horn = np.sin(TAU*(113*t + 30*t*t)) + .36*np.sin(TAU*(226*t + 62*t*t))
    return .65*rise*horn + .5*audio.pluck(220, len(t)/RATE) + .16*air(t,rng,14)*rise


def landing(t, rng):
    drum = audio.membrane(91, len(t)/RATE, rng, bright=True)
    stone = modes(t, 161, (1, 1.49, 2.77, 5.18), 9)
    return .92*drum + .43*after(.038,stone) + .19*after(.104,drum)


CUES = {
    "vajra_gada": (.34, .265, gada, "Short air cut into a bronze strike"),
    "vajra_kavacha": (.47, .23, ward, "Bright three-note opening ring"),
    "maruti_udayana": (.39, .235, vault, "Rising air with a light takeoff beat"),
    "lanka_dahan": (.41, .24, embers, "Sweeping breath and four scattered ember ticks"),
    "mountain_pulse": (.55, .245, mountain, "Low rising harmonic call"),
    "mountain_impact": (.48, .27, landing, "Low membrane impact and delayed stone resonance"),
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="regenerate in memory and compare published bytes")
    args = parser.parse_args()
    if not args.check:
        OUTPUT.mkdir(parents=True, exist_ok=True)
    manifest = {"source": "Original synthesized performance cues for YUGA, with no sampled recording.",
                "generator": Path(__file__).relative_to(NATIVE).as_posix(),
                "shared_synthesis": "tools/audio/build-traversal-audio.py", "files": {}}
    for i, (name, (duration, peak, synth, description)) in enumerate(CUES.items()):
        t = np.arange(round(duration * RATE)) / RATE
        signal = synth(t, np.random.default_rng(20261125+i)) * audio.envelope(len(t), .005, .045)
        samples = signal * (peak / np.max(np.abs(signal)))
        data, pcm = audio.encode(samples)
        assert pcm[0] == pcm[-1] == 0 and max(abs(pcm.astype(int))) < 9500
        path = OUTPUT/(name+".wav")
        if args.check:
            if path.read_bytes() != data:
                raise ValueError(f"Unexpected PCM bytes in {path}")
        else:
            path.write_bytes(data)
        manifest["files"][name] = {"path": path.relative_to(NATIVE).as_posix(), "sound": description,
            "frames":len(t), "rate_hz":RATE, "channels":1, "format":"PCM16", "peak_dbfs":round(20*np.log10(peak),2),
            "rms_dbfs":round(20*np.log10(np.sqrt(np.mean(samples**2))),2), "sha256":sha256(data).hexdigest()}
    metadata = json.dumps(manifest, indent=2) + "\n"
    if args.check:
        if NOTICE.read_text() != metadata:
            raise ValueError("Hanuman audio notice is out of date")
    else:
        NOTICE.write_text(metadata)
    print(f"Verified {len(CUES)} distinct cues, {sum(x['frames'] for x in manifest['files'].values())} mono samples at {RATE} Hz")


if __name__ == "__main__":
    main()
