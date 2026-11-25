"""Execute an unchanged pinned doukutsu-rs module against game-simulation fixtures."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory

COMMIT = "d9a281f959eba3a4423606ec7ddf4b047a1e6ff2"
SOURCE = "src/util/rng.rs"
DIGEST = "998684f3647352066343da0a2b5c4f6641d3dcd316017baf1cdddefdedaaa79a"
MAIN = r'''
#[allow(dead_code)]
mod donor;
use donor::{RNG, XorShift, Xoroshiro32PlusPlus};

fn main() {
    let seeds = [1, 17, 0x2048, 0x8ace, 0x1cab, -7];
    let mut replay_words = 0;
    for seed in seeds {
        let mut a = XorShift::new(seed);
        let mut b = Xoroshiro32PlusPlus::new(seed as u32);
        for _ in 0..37 { a.next_u32(); b.next_u16(); }
        let a_checkpoint = a.dump_state();
        let b_checkpoint = b.dump_state();
        let stream: Vec<_> = (0..512).map(|_| (a.next_u32(), b.next_u16())).collect();
        assert!(stream.iter().any(|v| v != &stream[0]));
        a.load_state(a_checkpoint);
        b.load_state(b_checkpoint);
        for (a_expected, b_expected) in stream {
            assert_eq!(a.next_u32(), a_expected);
            assert_eq!(b.next_u16(), b_expected);
            replay_words += 2;
        }
    }
    let a = XorShift::new(0);
    let b = Xoroshiro32PlusPlus::new(0);
    assert!((0..512).all(|_| a.next_u32() == 0 && b.next_u16() == 0));
    let rng = XorShift::new(17);
    let mut counts = [0; 5];
    for _ in 0..1024 {
        let value = rng.range(0..4);
        assert!((0..=4).contains(&value));
        counts[value as usize] += 1;
    }
    assert!(counts.iter().all(|&n| n > 0));
    println!(r#"{{"seeds_checked":{},"replayed_words":{},"zero_seed_absorbing_steps_per_generator":512,"range_0_to_4_bins":{:?}}}"#, seeds.len(), replay_words, counts);
}
'''


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("checkout", type=Path, help="local checkout containing the pinned Git object")
    p.add_argument("report", type=Path)
    p.add_argument("--rustc", default="rustc")
    args = p.parse_args()
    source = subprocess.check_output(["git", "-C", args.checkout, "show", f"{COMMIT}:{SOURCE}"])
    if hashlib.sha256(source).hexdigest() != DIGEST:
        raise ValueError("unexpected donor identity")
    with TemporaryDirectory() as tmp:
        work = Path(tmp)
        (work / "donor.rs").write_bytes(source)
        (work / "main.rs").write_text(MAIN)
        exe = work / "rng-fixture"
        subprocess.run([args.rustc, "--edition=2021", work/"main.rs", "-o", exe], check=True)
        recordings = [subprocess.check_output([exe]) for _ in range(2)]
        if recordings[0] != recordings[1]:
            raise ValueError("double run diverged")
    result = {"repo": "doukutsu-rs/doukutsu-rs", "commit": COMMIT, "path": SOURCE, "source_sha256": DIGEST,
              "rustc": subprocess.check_output([args.rustc, "--version"], text=True).strip(),
              "identical_runs": 2, "receipt": json.loads(recordings[0])}
    args.report.write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
