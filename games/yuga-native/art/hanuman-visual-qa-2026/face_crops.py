"""Make enlarged, explicitly cropped face comparisons from matching render receipts."""

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


# Coordinates are in the original 480x622-pixel camera gates. Enlarging a crop
# does not add render detail; source PNGs remain available for close inspection.
CROPS = {
    "face-front": (135, 235, 355, 415),
    "face-three-quarter": (165, 235, 385, 415),
    "face-profile": (65, 235, 285, 415),
}


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sources", nargs="+", type=Path)
    parser.add_argument("--labels", nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--views", nargs="+", choices=CROPS, default=list(CROPS))
    args = parser.parse_args()
    if len(args.sources) != len(args.labels):
        parser.error("provide one label for each source directory")
    records = [json.loads((src / "receipt.json").read_text()) for src in args.sources]
    base = records[0]
    if base["resolution"] != [480, 622]:
        raise ValueError("Crop coordinates require 480x622 source images")
    for other in records[1:]:
        for field in ("blender", "renderer", "samples", "resolution", "color_transform", "look", "seed", "lights", "filter"):
            if base.get(field) != other.get(field):
                raise ValueError("Unmatched render field: " + field)
    views = [{v["name"]: v for v in record["views"]} for record in records]
    for name in args.views:
        for other in views[1:]:
            for field in ("action", "phase", "camera_to_world", "width_m"):
                if views[0][name][field] != other[name][field]:
                    raise ValueError(f"Unmatched {field} in {name}")
    image_width, image_height = 440, 360
    gap, pad, header, label_height = 8, 12, 42, 28
    sheet = Image.new("RGB", (2 * pad + len(args.views) * image_width + max(0, len(args.views)-1) * gap,
                               header + len(records) * (image_height + label_height) + pad), "#151b1c")
    draw = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 15)
        heading = ImageFont.truetype("DejaVuSans-Bold.ttf", 20)
    except OSError:
        font = heading = ImageFont.load_default()
    draw.text((pad, 10), "HANUMAN  /  ENLARGED FACE CROPS", font=heading, fill="#f5e5cc")
    for row, (directory, label, by_name) in enumerate(zip(args.sources, args.labels, views, strict=True)):
        for col, name in enumerate(args.views):
            bounds = CROPS[name]
            view = by_name[name]
            path = directory / view["image"]
            if digest(path) != view["sha256"]:
                raise ValueError("Image hash mismatch: " + str(path))
            with Image.open(path) as image:
                crop = image.convert("RGB").crop(bounds).resize((image_width, image_height), Image.Resampling.LANCZOS)
            x, y = pad + col * (image_width + gap), header + row * (image_height + label_height)
            sheet.paste(crop, (x, y))
            draw.text((x, y + image_height + 5), label + "  /  " + name, font=font, fill="#e3ddd1")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(args.output, "WEBP", quality=95, method=5)
    print(json.dumps({"output": str(args.output), "sha256": digest(args.output),
                      "original_resolution": base["resolution"], "crop_bounds": {name: CROPS[name] for name in args.views},
                      "source_sha256": [record["source_sha256"] for record in records]}, indent=2))


if __name__ == "__main__":
    main()
