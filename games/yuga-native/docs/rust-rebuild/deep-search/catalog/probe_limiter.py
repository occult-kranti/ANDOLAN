#!/usr/bin/env python3
"""Compile the pinned MIT openbf limiter on its own and resolve a simultaneous YUGA cue stack."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import tempfile
from urllib.request import urlopen
import wave

SOURCE = "https://raw.githubusercontent.com/sprucey149/openbf/5015e39c74361efc9e2576fea5b8346361b926de/engine/crates/audio/src/limiter.rs"
DIGEST = "ae30c287df63edba8f094e596e9ebef64eb0f6d6cabfb8d949ea4484aeea2d46"
AUDIO = Path(__file__).resolve().parents[4] / "assets/audio/hanuman-trial"
HARNESS = '''
mod limiter;
use std::{convert::TryInto, fs};
fn main() {
    let bytes = fs::read("stack.f32").unwrap();
    let samples: Vec<_> = bytes.chunks_exact(4).map(|b| f32::from_le_bytes(b.try_into().unwrap())).collect();
    let mut limiter = limiter::Limiter::new(24000);
    let delay = limiter.delay();
    let mut peak = 0.0f32;
    let mut max_stereo_error = 0.0f32;
    for input in samples.iter().copied().chain(std::iter::repeat_n(0., delay)) {
        let (left, right) = limiter.process(input, -input * 0.5);
        peak = peak.max(left.abs()).max(right.abs());
        max_stereo_error = max_stereo_error.max((right + left * 0.5).abs());
    }
    assert!(peak <= 1.000001 && peak > 0.95);
    assert!(max_stereo_error < 0.000001);
    let mut clean = limiter::Limiter::new(24000);
    let mut clean_out = Vec::new();
    for input in samples.iter().map(|v| v * 0.08).chain(std::iter::repeat_n(0., delay)) {
        clean_out.push(clean.process(input, input).0);
    }
    assert!(clean_out[..delay].iter().all(|v| *v == 0.));
    assert!(clean_out[delay..].iter().zip(&samples).all(|(out, input)| *out == *input * 0.08));
    println!("{} {} {} {}", delay, peak, max_stereo_error, clean.gain());
}
'''

def run():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, help="Offline copy of the exact pinned Rust source")
    parser.add_argument("--rustc", default="rustc")
    args = parser.parse_args()
    if args.source:
        source = args.source.read_bytes()
    else:
        with urlopen(SOURCE, timeout=30) as response:
            source = response.read()
    assert hashlib.sha256(source).hexdigest() == DIGEST, "upstream source checksum changed"
    stack, fixtures = [], []
    for file in sorted(AUDIO.glob("*.wav")):
        with wave.open(str(file)) as f:
            assert (f.getframerate(), f.getsampwidth(), f.getnchannels()) == (24000, 2, 1)
            pcm = struct.unpack(f"<{f.getnframes()}h", f.readframes(f.getnframes()))
        stack.extend([0.] * max(0, len(pcm) - len(stack)))
        for i, value in enumerate(pcm):
            stack[i] += 2 * value / 32768.
        fixtures.append({"file": file.name, "sha256": hashlib.sha256(file.read_bytes()).hexdigest()})
    assert len(fixtures) == 6 and max(map(abs, stack)) > 1.
    with tempfile.TemporaryDirectory() as tmp:
        temp = Path(tmp)
        (temp / "limiter.rs").write_bytes(source)
        (temp / "stack.f32").write_bytes(struct.pack(f"<{len(stack)}f", *stack))
        (temp / "probe.rs").write_text(HARNESS)
        def command(*cmd):
            return subprocess.check_output(cmd, cwd=temp, text=True)
        command(args.rustc, "--edition=2021", "--test", "limiter.rs", "-o", "tests")
        tests = command(str(temp / "tests"))
        assert "1 passed; 0 failed" in tests
        command(args.rustc, "--edition=2021", "-O", "probe.rs", "-o", "probe")
        delay, peak, stereo_error, quiet_gain = map(float, command(str(temp / "probe")).split())
    return {"source": SOURCE, "source_sha256": DIGEST, "compiler": subprocess.check_output(
        [args.rustc, "--version"], text=True).strip(), "upstream_tests_passed": 1, "fixtures": fixtures,
        "synchronous_copies_per_cue": 2, "stack_frames": len(stack), "sample_rate_hz": 24000, "input_peak": max(map(abs, stack)),
        "output_peak": peak, "delay_frames": int(delay), "stereo_link_max_error": stereo_error,
        "quiet_gain": quiet_gain, "quiet_after_delay_bit_exact": True}

if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
