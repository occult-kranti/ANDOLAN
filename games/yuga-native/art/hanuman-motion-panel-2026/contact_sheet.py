"""Make a labeled contact sheet from the rendered ability-impact stills."""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent


def sha(path):
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stills", type=Path, default=HERE / "stills")
    parser.add_argument("--output", type=Path, default=HERE / "contact-sheet.webp")
    parser.add_argument("--receipt", type=Path, default=HERE / "evidence/stills.json")
    args = parser.parse_args()
    timeline = json.loads((HERE / "timeline.json").read_text())
    font_path = HERE.parents[1] / "assets/fonts/DejaVuSans.ttf"
    title = ImageFont.truetype(font_path, 27)
    label = ImageFont.truetype(font_path, 21)
    small = ImageFont.truetype(font_path, 16)
    width, height = 1704, 722
    sheet = Image.new("RGB", (width, height), "#111c21")
    draw = ImageDraw.Draw(sheet)
    draw.text((20, 13), "Hanuman · contact and landing studies", font=title, fill="#f4e8d6")
    draw.text((20, 50), "Actual Blender poses · one 20 Hz tick after impact or nominal landing",
              font=small, fill="#a1bbc0")
    panels = []
    for i, shot in enumerate(timeline["shots"]):
        x = 20 + (i % 3) * 560
        y = 84 + (i // 3) * 319
        if i >= 3:
            x += 280
        raw = args.stills / (shot["id"] + ".png")
        clean = args.stills / (shot["id"] + "-denoised.png")
        with Image.open(clean) as image:
            image = image.convert("RGB").resize((548, 308), Image.Resampling.LANCZOS)
            sheet.paste(image, (x, y))
        draw.rectangle((x, y + 271, x + 547, y + 307), fill="#0b151a")
        beat = "landing" if shot["id"] == "maruti_udayana" else "impact"
        draw.text((x + 10, y + 278), f'{shot["label"]}  ·  {beat} +1 tick',
                  font=label, fill="#f5e6d1")
        panels.append({"id": shot["id"], "frame": min(shot["frames"]["impact"] + 2,
                                                       shot["frames"]["end"]),
                       "raw_sha256": sha(raw), "denoised_sha256": sha(clean)})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(args.output, "WEBP", quality=91, method=6)
    result = {
        "scene_sha256": sha(HERE / "hanuman-layered-abilities.blend"),
        "timeline_sha256": sha(HERE / "timeline.json"),
        "image_sha256": sha(args.output),
        "renderer": "Blender Cycles CPU, 4 samples, 720 x 405; OIDN 2.5.1 sRGB LDR",
        "panels": panels
    }
    args.receipt.write_text(json.dumps(result, indent=2) + "\n")
    print("Saved", args.output)


if __name__ == "__main__":
    main()
