#!/usr/bin/env python3
"""Original S1 gold roughness field; offline, deterministic, no image/model input.

Retains the broad forging language of the original G1 generator, with a higher
roughness floor and quieter tool marks. This changes surface response, not relief.
"""
import argparse
import hashlib
import io
import json
import math
from pathlib import Path

from PIL import Image, ImageStat, __version__ as PILLOW_VERSION

PROJECT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = PROJECT / "assets/hero-finish/s1-hammered-gold-roughness.png"
SIZE = 512


def gold(u, v):
    turn = math.tau
    forging = .029 * math.sin(turn * (3*u + 2*v)) * math.cos(turn * (2*u - 3*v))
    forging += .021 * math.sin(turn * (7*u - 5*v))
    # Tool marks stay subordinate to the existing modeled/normal-map ornament.
    marks = .007 * math.sin(turn * (61*u + 17*v))
    marks += .005 * math.sin(turn * (23*u - 71*v))
    return min(.63, max(.48, .555 + forging + marks))


def build():
    image = Image.new("L", (SIZE, SIZE))
    image.putdata([round(255*gold(x/(SIZE-1), y/(SIZE-1)))
                   for y in range(SIZE) for x in range(SIZE)])
    return image


def encoded(image):
    data = io.BytesIO()
    image.save(data, format="PNG", compress_level=9, optimize=False)
    return data.getvalue()


def verify(path):
    image = Image.open(path)
    if image.mode != "L" or image.size != (SIZE, SIZE):
        raise ValueError("Expected one 512x512 linear scalar channel")
    lo, hi = image.getextrema()
    if not 122 <= lo < hi <= 161:
        raise ValueError("Effective roughness must remain within authored .48-.63 bounds")
    if image.crop((0, 0, 1, SIZE)).tobytes() != image.crop((SIZE-1, 0, SIZE, SIZE)).tobytes():
        raise ValueError("Horizontal repeat seam differs")
    if image.crop((0, 0, SIZE, 1)).tobytes() != image.crop((0, SIZE-1, SIZE, SIZE)).tobytes():
        raise ValueError("Vertical repeat seam differs")
    regenerated = build()
    if regenerated.tobytes() != image.tobytes() or encoded(regenerated) != path.read_bytes():
        raise ValueError("Exact original-generator reconstruction differs")
    mean = ImageStat.Stat(image).mean[0]
    mip = image.copy()
    mip_means = []
    while mip.width > 1:
        mip = mip.resize((mip.width//2, mip.height//2), Image.Resampling.BOX)
        mip_means.append(ImageStat.Stat(mip).mean[0])
    if max(abs(value-mean) for value in mip_means) >= 5:
        raise ValueError("CPU area-filter mean drift exceeds five u8 steps")
    return {"range_u8": [lo, hi], "effective_roughness_range": [lo/255, hi/255],
            "mean_u8": mean, "cpu_area_filter_mip_means_u8": mip_means}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    if not args.verify_only:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(encoded(build()))
    measurements = verify(args.output)
    record = {"schema": 1, "task": "desktop-finish/S1/W3", "passed": True,
              "generator": "art/hero-finish/build_s1_gold.py",
              "generator_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "output": str(args.output), "output_sha256": hashlib.sha256(args.output.read_bytes()).hexdigest(),
              "output_bytes": args.output.stat().st_size, "pillow_version": PILLOW_VERSION,
              "size": [SIZE, SIZE], "mode": "L", "channel": "RED", "color_space": "linear scalar",
              "roughness_multiplier": 1.0, "measurements": measurements,
              "scope": "Original scalar field, exact regeneration, wrap continuity and CPU filtering model. No actual import, visible quality, geometry or hardware-performance acceptance."}
    manifest = {"schema": 1, "generator_source": record["generator"],
                "generator_sha256": record["generator_sha256"],
                "maps": [{"path": args.output.name, "sha256": record["output_sha256"],
                          "bytes": record["output_bytes"], "size": record["size"],
                          "range_u8": measurements["range_u8"], "mode": "L",
                          "channel": "RED", "color_space": "linear scalar",
                          "source": "original analytic field in art/hero-finish/build_s1_gold.py"}],
                "scope": "Worked warm gold roughness only; original albedo, normals, UVs, geometry, rig and motion preserved."}
    manifest_path = args.manifest or args.output.with_name("s1-manifest.json")
    manifest_bytes = (json.dumps(manifest, indent=2, sort_keys=True)+"\n").encode()
    if args.verify_only:
        if manifest_path.read_bytes() != manifest_bytes:
            raise ValueError("Source manifest differs from exact generator/output identities")
    else:
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_bytes(manifest_bytes)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(record, indent=2, sort_keys=True)+"\n")
    print(json.dumps(record, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
