"""Lay out the six unchanged camera frames from the Blender map study as one image."""

import argparse
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

PAPER = "#f3edde"
INK = "#202f29"
MUTED = "#4d5b51"
JADE = "#28604b"


def face(family, size):
    for name in (family, "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default(size=size)


def main(folder):
    report = json.loads((folder / "cameras-and-render.json").read_text())
    margin = 48
    gutter = 20
    thumb = 670
    width = 2 * margin + 2 * thumb + gutter
    rows = [
        ("overview", "District overview", "Registered radar extent, north up"),
        ("site-a", "Site A", "View from the eastern objective"),
        ("site-b", "Site B", "View from the western objective"),
    ]
    pictures = {}
    heights = {}
    for key, _, _ in rows:
        for state in ("baseline", "jade"):
            with Image.open(folder / f"{key}-{state}.png") as src:
                source = src.convert("RGB")
            size = (thumb, round(thumb * source.height / source.width))
            pictures[(key, state)] = source.resize(size, Image.Resampling.LANCZOS)
            heights[key] = size[1]
    canvas = Image.new(
        "RGB", (width, 194 + sum(heights.values()) + len(rows) * 94 + 43), PAPER
    )
    d = ImageDraw.Draw(canvas)
    serif = face("DejaVuSerif.ttf", 51)
    section = face("DejaVuSerif.ttf", 27)
    mono = face("DejaVuSansMono.ttf", 16)
    body = face("DejaVuSans.ttf", 17)
    d.text((margin, 29), "YUGA   /   MAP MATERIAL STUDY", fill=JADE, font=mono)
    d.text((margin, 57), "Dust II", fill=INK, font=serif)
    d.text((margin, 134), "Reference ground", fill=MUTED, font=body)
    d.text((margin + thumb + gutter, 134), "Jade ground", fill=JADE, font=body)
    d.line((margin, 167, width - margin, 167), fill="#b8bbab", width=2)
    y = 178
    for key, name, detail in rows:
        cam = report["cameras"][key]
        if cam.get("nav_support"):
            proof = cam["nav_support"]
            detail = f"1.60 m eye height  /  NAV area {proof['area_id']}  /  {proof['callout'] or 'unnamed area'}"
        d.text((margin, y), name, fill=INK, font=section)
        d.text((width - margin, y + 10), detail, fill=MUTED, font=mono, anchor="rt")
        y += 47
        for i, state in enumerate(("baseline", "jade")):
            x = margin + i * (thumb + gutter)
            im = pictures[(key, state)]
            canvas.paste(im, (x, y))
            d.rectangle(
                (x, y, x + im.width - 1, y + im.height - 1), outline="#7e897a", width=1
            )
        y += heights[key] + 47
    d.text(
        (margin, y - 8),
        "CS:GO Source 1  /  matched Blender cameras and lighting",
        fill=MUTED,
        font=mono,
    )
    dest = folder / "dust2-ground-comparison.webp"
    canvas.save(dest, quality=90, method=6)
    print(dest, canvas.size)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path)
    main(parser.parse_args().folder)
