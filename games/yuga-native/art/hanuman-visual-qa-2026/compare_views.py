"""Make an inspection board from two matched render_views.py output directories."""

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


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
    records = [json.loads((folder / "receipt.json").read_text()) for folder in dirs]
    for field in ("blender", "renderer", "samples", "resolution", "color_transform", "look", "seed", "lights", "filter"):
        if records[0].get(field) != records[1].get(field):
            raise ValueError(f"Unmatched rendering field: {field}")
    a, b = (record["views"] for record in records)
    if len(a) != len(b):
        raise ValueError("View counts differ")
    for left, right in zip(a, b, strict=True):
        for field in ("name", "action", "phase", "camera_to_world", "width_m", "azimuth_degrees", "elevation_degrees", "center_world_m"):
            if left[field] != right[field]:
                raise ValueError(f"Unmatched view field {field}: {left['name']}")
    width, height = records[0]["resolution"]
    pad, gap, header, label = 16, 8, 48, 30
    sheet = Image.new("RGB", (pad * 2 + len(a) * width + max(0, len(a)-1) * gap,
                               header + 2 * (height + label) + pad), "#151b1c")
    draw = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 14)
        heading = ImageFont.truetype("DejaVuSans-Bold.ttf", 20)
    except OSError:
        font = ImageFont.load_default()
        heading = font
    draw.text((pad, 12), "HANUMAN  /  MATCHED BLENDER REVIEW", font=heading, fill="#f8e7ce")
    for row, (folder, entries) in enumerate(zip(dirs, (a, b), strict=True)):
        for index, shot in enumerate(entries):
            path = folder / shot["image"]
            if digest(path) != shot["sha256"]:
                raise ValueError(f"Image no longer matches its receipt: {path}")
            x, y = pad + index * (width + gap), header + row * (height + label)
            with Image.open(path) as image:
                sheet.paste(image.convert("RGB"), (x, y))
            label_text = ("BASELINE" if row == 0 else "CANDIDATE") + "  /  " + shot["name"]
            draw.text((x, y + height + 6), label_text, font=font, fill="#e3ddd1")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(args.output, "WEBP", quality=94, method=5)
    print(json.dumps({"output": str(args.output), "sha256": digest(args.output),
                      "baseline_sha256": records[0]["source_sha256"],
                      "candidate_sha256": records[1]["source_sha256"],
                      "views": [view["name"] for view in a]}, indent=2))


if __name__ == "__main__":
    main()
