"""Create the distributable library index from its Blender-rendered asset previews."""
import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

FONT = Path("/usr/share/fonts/truetype/dejavu")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("catalog", type=Path)
    p.add_argument("thumbnails", type=Path)
    p.add_argument("output", type=Path)
    args = p.parse_args()
    rows = json.loads(args.catalog.read_text())["assets"]
    title = ImageFont.truetype(str(FONT / "DejaVuSerif.ttf"), 45)
    header = ImageFont.truetype(str(FONT / "DejaVuSans.ttf"), 26)
    label = ImageFont.truetype(str(FONT / "DejaVuSans.ttf"), 17)
    small = ImageFont.truetype(str(FONT / "DejaVuSans.ttf"), 15)
    groups = [("Architecture", 4), ("Nature", 4), ("Foundations", 4), ("Symbols", 8)]
    width, pad, gap = 1220, 44, 10
    heights = {"Symbols": 119, "Foundations": 163}
    sections = []
    y = 120
    for group, columns in groups:
        members = [r for r in rows if r["category"] == group]
        tile_height = heights.get(group, 179)
        sections.append((group, columns, members, tile_height, y))
        y += 45 + ((len(members)+columns-1)//columns)*(tile_height + gap) + 28
    bg, panel, ink, muted = "#192529", "#28373b", "#f1e8d5", "#c8d2c8"
    canvas = Image.new("RGB", (width, y+12), bg)
    draw = ImageDraw.Draw(canvas)
    draw.text((pad, 22), "YUGA   /   World elements", font=title, fill=ink)
    draw.text((pad+2, 84), f"{len(rows)} editable Blender collections", font=label, fill=muted)
    for group, columns, members, height, y in sections:
        draw.text((pad, y), group, font=header, fill=ink)
        tile_width = (width-2*pad-gap*(columns-1))//columns
        for index, row in enumerate(members):
            x = pad+(index%columns)*(tile_width+gap)
            top = y+44+(index//columns)*(height+gap)
            draw.rounded_rectangle((x,top,x+tile_width,top+height),radius=4,fill=panel)
            img = Image.open(args.thumbnails / (row["id"]+".png")).convert("RGBA")
            img.thumbnail((tile_width-12,height-26), Image.Resampling.LANCZOS)
            canvas.paste(img, (x+(tile_width-img.width)//2,top+1), img)
            caption = row["id"].removeprefix("foundation-").replace("_"," ").replace("-"," ").title()
            draw.text((x+tile_width/2,top+height-15),caption,anchor="mm",font=small if group=="Symbols" else label,fill=ink)
    canvas.save(args.output, quality=91, optimize=True)


if __name__ == "__main__":
    main()
