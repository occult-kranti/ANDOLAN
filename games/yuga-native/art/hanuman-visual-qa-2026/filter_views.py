"""Create separate OIDN display copies of render_views.py outputs; retain the raw images."""

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent.parent / "tools/hanuman-art"))
from denoise import read_pfm, write_pfm  # noqa: E402


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--oidn", type=Path, required=True)
    parser.add_argument("--threads", type=int, default=2)
    args = parser.parse_args()
    source, output, oidn = args.source.resolve(), args.output.resolve(), args.oidn.resolve(strict=True)
    if source == output:
        parser.error("output must differ from the raw source directory")
    receipt = json.loads((source / "receipt.json").read_text())
    receipt["filter"] = {"tool": "Intel Open Image Denoise CLI", "binary_sha256": digest(oidn),
                         "mode": "RT, LDR sRGB", "threads": args.threads,
                         "note": "Display-referred denoising without auxiliary albedo or normal passes."}
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="yuga-hanuman-oidn-") as cache:
        raw_pfm, filtered_pfm = Path(cache) / "raw.pfm", Path(cache) / "filtered.pfm"
        for view in receipt["views"]:
            raw = source / view["image"]
            if digest(raw) != view["sha256"]:
                raise ValueError(f"Raw render does not match receipt: {raw}")
            with Image.open(raw) as image:
                pixels = np.asarray(image.convert("RGB"), dtype=np.float32) / 255
            write_pfm(raw_pfm, pixels)
            subprocess.run([str(oidn), "--device", "cpu", "--threads", str(args.threads), "--affinity", "0",
                            "--ldr", str(raw_pfm), "--srgb", "--output", str(filtered_pfm)],
                           check=True, stdout=subprocess.DEVNULL)
            result = read_pfm(filtered_pfm)
            if result.shape != pixels.shape:
                raise ValueError("Denoiser changed the output dimensions")
            dest = output / view["image"]
            Image.fromarray(np.rint(result.clip(0, 1) * 255).astype(np.uint8)).save(dest)
            view["raw_sha256"] = view["sha256"]
            view["sha256"] = digest(dest)
    (output / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"output": str(output), "views": len(receipt["views"]), "filter": receipt["filter"]}, indent=2))


if __name__ == "__main__":
    main()
