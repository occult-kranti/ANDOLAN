#!/usr/bin/env python3
"""Deterministic roughness-only finish; no albedo, UV, normal or model changes."""
import hashlib
import json
import math
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
HERO = PROJECT / "assets/heroes"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mapped(source, output, low, high, variation):
    image = Image.open(source).getchannel("G")
    lower, upper = image.getextrema()
    pixels = image.load()
    result = Image.new("L", image.size)
    target = result.load()
    for y in range(image.height):
        for x in range(image.width):
            # Integer texture coordinates and fixed trigonometric frequencies
            # give deterministic broad variation; authored relief stays intact.
            authored = (pixels[x, y] - lower) / max(1, upper - lower)
            u, v = x / image.width, y / image.height
            breakup = math.sin(u * math.tau * 7) * math.sin(v * math.tau * 9)
            breakup += .45 * math.sin((u * 19 + v * 13) * math.tau)
            value = low + (high - low) * authored + variation * breakup
            target[x, y] = round(255 * min(high, max(low, value)))
    result.save(output, optimize=False, compress_level=9)
    return {"source":str(source.relative_to(PROJECT)), "source_sha256":sha(source),
            "output":output.name, "sha256":sha(output), "bytes":output.stat().st_size,
            "size":list(image.size), "channel":"red", "range":list(result.getextrema()),
            "method":{"low":low,"high":high,"variation":variation},
            "rights":"Derived from existing original YUGA material; no third-party game asset"}


def main():
    outputs = []
    for original, name, low, high, variation in [
        ("rama-warm-skin", "skin-roughness.png", .50, .66, .018),
        ("worked-warm-gold", "gold-roughness.png", .30, .44, .014),
        ("ivory-silk", "ivory-roughness.png", .61, .73, .012),
        ("swept-black-hair", "hair-roughness.png", .47, .63, .010),
    ]:
        outputs.append(mapped(HERO / f"rama-hero_{original}-roughness.png", HERE / name, low, high, variation))
    source = PROJECT / "art/open-art-wave/textures/indigo-woven-roughness.png"
    output = HERE / "woven-roughness.png"
    output.write_bytes(source.read_bytes())
    image = Image.open(output)
    outputs.append({"source":str(source.relative_to(PROJECT)), "source_sha256":sha(source),
                    "output":output.name, "sha256":sha(output), "bytes":output.stat().st_size,
                    "size":list(image.size), "channel":"red", "range":list(image.getextrema()),
                    "method":"Exact copy of previously reviewed roughness derivative",
                    "rights":"CC0-1.0; Microsoft SheenCloth, pinned source in NOTICE.md"})
    manifest = {"schema":1,"generator_sha256":sha(Path(__file__)),"maps":outputs,
                "scope":"Roughness-only maps; albedo, gold ornament, UV, normals, mesh and rig untouched."
               }
    (HERE / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"maps":len(outputs),"total_bytes":sum(m["bytes"] for m in outputs),"manifest":"manifest.json"}))


if __name__ == "__main__":
    main()
