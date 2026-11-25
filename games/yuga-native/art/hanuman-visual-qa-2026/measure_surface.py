"""Measure bounded image differences for matching five-view Hanuman renders.

This is a pixel-space approximation, not a colorimetric or perceptual test.
The source views must have identical render settings and camera transforms.
"""

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont


REGIONS = {
    "face": (180, 76, 255, 153),
    "exposed_arm": (298, 194, 365, 284),
    "background_control": (0, 58, 65, 550),
}


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    dirs = [args.baseline.resolve(), args.candidate.resolve()]
    data = [json.loads((d / "receipt.json").read_text()) for d in dirs]
    for field in ("blender", "renderer", "samples", "resolution", "color_transform", "look", "seed", "lights", "filter"):
        if data[0].get(field) != data[1].get(field):
            raise ValueError("Render settings do not match: " + field)
    if data[0]["resolution"] != [480, 622]:
        raise ValueError("The measured regions require the 480x622 figure view")
    views = [next(v for v in record["views"] if v["name"] == "figure-front") for record in data]
    for field in ("action", "phase", "camera_to_world", "width_m"):
        if views[0][field] != views[1][field]:
            raise ValueError("Camera or pose does not match: " + field)
    images = []
    for folder, view in zip(dirs, views, strict=True):
        path = folder / view["image"]
        if digest(path) != view["sha256"]:
            raise ValueError("Image no longer matches receipt: " + str(path))
        with Image.open(path) as image:
            images.append(image.convert("RGB"))
    rows = {}
    scales = {"source_480x622": (480, 622), "approx_gameplay_154x199": (154, 199)}
    for label, size in scales.items():
        a, b = [np.asarray(image.resize(size, Image.Resampling.LANCZOS), dtype=np.int16) for image in images]
        diff = np.abs(a - b)
        result = {}
        for name, rect in REGIONS.items():
            x0, y0, x1, y1 = rect
            x0, x1 = round(x0 * size[0] / 480), round(x1 * size[0] / 480)
            y0, y1 = round(y0 * size[1] / 622), round(y1 * size[1] / 622)
            pixels = diff[y0:y1, x0:x1]
            if not pixels.size:
                raise ValueError("Empty measurement region: " + name)
            result[name] = {
                "region_xyxy": [x0, y0, x1, y1],
                "mean_absolute_rgb_levels": round(float(pixels.mean()), 4),
                "p95_absolute_rgb_levels": round(float(np.percentile(pixels, 95)), 4),
                "pixel_fraction_any_channel_over_2_levels": round(float((pixels.max(axis=2) > 2).mean()), 4),
            }
        rows[label] = {"resolution": size, "regions": result}
    args.output.mkdir(parents=True, exist_ok=True)
    canvas = Image.new("RGB", (346, 256), "#151b1c")
    draw = ImageDraw.Draw(canvas)
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 11)
    except OSError:
        font = ImageFont.load_default()
    draw.text((8, 8), "Approximate gameplay-scale comparison", font=font, fill="#f4e5cf")
    for x, image, label in ((8, images[0], "Facial v1"), (184, images[1], "Surface candidate")):
        canvas.paste(image.resize(scales["approx_gameplay_154x199"], Image.Resampling.LANCZOS), (x, 32))
        draw.text((x, 234), label, font=font, fill="#f4e5cf")
    sheet = args.output / "gameplay-scale-simulation.png"
    canvas.save(sheet)
    report = {
        "scope": "Display-referred RGB pixel differences for one matched Blender idle still. Not an in-game screenshot, perceptual threshold, dynamic comparison, or physical GPU benchmark.",
        "rationale": "The downsampled figure is about 175 pixels tall, approximating one observed browser practice camera; actual on-screen size and angle vary.",
        "source_sha256": [record["source_sha256"] for record in data],
        "filter": data[0].get("filter"),
        "regions_source_xyxy": REGIONS,
        "results": rows,
        "simulation_png_sha256": digest(sheet),
    }
    dest = args.output / "surface-differences.json"
    dest.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
