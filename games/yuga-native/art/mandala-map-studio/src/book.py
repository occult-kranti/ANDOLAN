"""Lay out the illustrated atlas and embed the dimensioned SVGs as vector drawings."""

from argparse import ArgumentParser
from collections import Counter
from io import BytesIO
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

import fitz
from PIL import Image
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas

STUDIO = Path(__file__).resolve().parents[1]
SITE = "https://occult-kranti.github.io/ANDOLAN/production/mandala-art/"
W, H = 1080, 720
INK, SUB, PAPER, GOLD, LINE = "#193633", "#425d55", "#f8f3e7", "#865025", "#c7c2b1"
SECTIONS = {
    "room": "Rooms",
    "route": "Passages",
    "cover": "Cover",
    "artifact": "Landmarks",
    "architecture": "Architecture",
    "rite": "Ritual objects",
}


def fonts():
    paths = ["/usr/share/fonts/truetype/noto", "/usr/share/fonts/truetype/dejavu"]
    for name, candidates in {
        "Headline": ("NotoSerif-Regular.ttf", "DejaVuSerif.ttf"),
        "Body": ("NotoSans-Regular.ttf", "DejaVuSans.ttf"),
        "Label": ("NotoSans-Bold.ttf", "DejaVuSans-Bold.ttf"),
    }.items():
        found = next(
            (Path(folder, f) for f in candidates for folder in paths if Path(folder, f).is_file()), None
        )
        if found is None:
            raise FileNotFoundError("Install the Noto or DejaVu fonts for the book.")
        pdfmetrics.registerFont(TTFont(name, str(found)))


def fill(c, x, y, w, h, color):
    c.setFillColor(HexColor(color))
    c.rect(x, y, w, h, stroke=0, fill=1)


def write(c, x, y, s, font="Body", size=15, color=INK):
    c.setFillColor(HexColor(color))
    c.setFont(font, size)
    c.drawString(x, y, s)


def lines(c, s, x, y, width, size=15, leading=22):
    line = ""
    for word in s.split():
        run = (line + " " + word).lstrip()
        if line and pdfmetrics.stringWidth(run, "Body", size) > width:
            write(c, x, y, line, size=size)
            y -= leading
            line = word
        else:
            line = run
    if line:
        write(c, x, y, line, size=size)
        y -= leading
    return y


def photo(c, path, x, y, w, h):
    with Image.open(path) as image:
        image = image.convert("RGB")
        scale = min(w / image.width, h / image.height)
        dw, dh = image.width * scale, image.height * scale
        image.thumbnail((round(dw * 2.45), round(dh * 2.45)), Image.Resampling.LANCZOS)
        data = BytesIO()
        image.save(data, "JPEG", quality=89, optimize=True, subsampling=0)
        data.seek(0)
        c.drawImage(ImageReader(data), x + (w - dw) / 2, y + (h - dh) / 2, dw, dh)


def footer(c, number, label, href):
    fill(c, 39, 39, W - 78, 1, LINE)
    write(c, 39, 20, "YUGA   /   MANDALA RIFT", "Label", 9, SUB)
    write(c, 388, 20, label, "Label", 9, GOLD)
    c.linkURL(href, (380, 13, 710, 37), relative=0)
    write(c, 1005, 20, f"{number:02d}", "Label", 10, SUB)


def make_book(dest):
    catalog = json.loads((STUDIO / "catalog.json").read_text())
    concepts = json.loads((STUDIO / "concepts/index.json").read_text())
    elements = catalog["elements"]
    counts = Counter(e["kind"] for e in elements)
    fonts()
    with tempfile.TemporaryDirectory() as temp:
        base = Path(temp) / "layout.pdf"
        c = Canvas(str(base), pagesize=(W, H), pageCompression=1, invariant=1)
        c.setTitle("Mandala Rift — Environment Art Book")
        c.setAuthor("YUGA Environment Studio")
        c.setSubject(
            "Measured four-angle Blender studies, original paintings and technical drawings of the river district."
        )
        fill(c, 0, 0, W, H, INK)
        photo(c, STUDIO / "concepts/hero.webp", 0, 181, W, 539)
        write(c, 40, 145, "YUGA     /     EMBER RITE", "Label", 12, "#d9b174")
        write(c, 37, 65, "Mandala Rift", "Headline", 63, PAPER)
        write(c, 650, 106, "Environment Art Book", "Headline", 26, PAPER)
        write(c, 653, 73, "The ghat, the folded temples and the river market", "Body", 15, "#eadfc5")
        c.bookmarkPage("front")
        c.addOutlineEntry("Mandala Rift", "front", 0)
        c.showPage()
        fill(c, 0, 0, W, H, PAPER)
        write(c, 39, 672, "THE DISTRICT", "Label", 12, GOLD)
        write(c, 37, 619, "Where the river routes meet", "Headline", 42)
        photo(c, STUDIO / "district.webp", 39, 221, 1002, 383)
        blocks = [
            (
                "The ghat",
                "A porter can follow the dry bank or enter through the reeds. At the platform a row of bells gives the caller a landmark.",
            ),
            (
                "The folded temples",
                "Two paired thresholds change facing by a quarter turn. Each has a signed exit and an ordinary walking alternative.",
            ),
            (
                "The bazaar",
                "An indigo stall and hanging scales identify the second site. The elevated Sluice connects the two courts.",
            ),
        ]
        for i, (title, copy) in enumerate(blocks):
            x = 39 + i * 344
            write(c, x, 184, title, "Headline", 21)
            lines(c, copy, x, 156, 309, size=13, leading=19)
        footer(c, 2, "Open the searchable art collection", SITE)
        c.bookmarkPage("district")
        c.addOutlineEntry("District overview", "district", 0)
        c.showPage()
        shown = set()
        for page, elem in enumerate(elements, start=3):
            key, kind = elem["id"], elem["kind"]
            fill(c, 0, 0, W, H, PAPER)
            write(c, 39, 678, f"{SECTIONS[kind].upper()}   /   MANDALA RIFT", "Label", 11, GOLD)
            write(c, 37, 627, elem["title"], "Headline", 37)
            fill(c, 39, 606, 1002, 1, LINE)
            write(c, 40, 579, "ENVIRONMENT PAINTING", "Label", 10, SUB)
            x, y, w, h = 39, 212, 560, 350
            fill(c, x, y, w, h, "#e6e0d0")
            photo(c, STUDIO / "concepts" / concepts["items"][key]["file"], x, y, w, h)
            write(c, 625, 579, "VIEWS FROM THE BLENDER SCENE", "Label", 10, SUB)
            photo(c, STUDIO / elem["render"], 625, 333, 416, 228)
            write(c, 625, 304, "MEASURED DRAWING", "Label", 10, SUB)
            if kind == "route":
                dimensions = f"{elem['width_m']:g} m wide"
                if elem["travel_kind"] == "fold":
                    dimensions += f"    /    {elem['time_s']:g} s threshold crossing"
                else:
                    dimensions += f"    /    {elem['length_m']:.1f} m along the route"
            else:
                dimensions = " × ".join(f"{v:g}" for v in elem.get("size_m", []))
                dimensions = (dimensions + " m") if dimensions else "Hand-carried objective"
            write(c, 39, 185, dimensions, "Label", 14, GOLD)
            lower = lines(c, elem["art_brief"], 39, 157, 554, 14, 20)
            lines(c, elem["cue"], 39, lower - 6, 554, 13, 19)
            footer(c, page, "Open the element, its model and its film", SITE + "#element=" + key)
            if kind not in shown:
                c.bookmarkPage("section-" + kind)
                c.addOutlineEntry(f"{SECTIONS[kind]} ({counts[kind]})", "section-" + kind, 0)
                shown.add(kind)
            c.bookmarkPage(key)
            c.addOutlineEntry(elem["title"], key, 1)
            c.showPage()
        c.save()
        # Inkscape preserves the clipped survey panel and turns its letterforms
        # into paths, so routes also print correctly on systems without Noto.
        plates = Path(temp) / "drawings"
        plates.mkdir()
        for elem in elements:
            shutil.copyfile(STUDIO / elem["plate"], plates / (elem["id"] + ".svg"))
        subprocess.run(
            [
                "inkscape",
                "--batch-process",
                "--export-area-page",
                "--export-text-to-path",
                "--export-type=pdf",
                *[e["id"] + ".svg" for e in elements],
            ],
            cwd=plates,
            check=True,
        )
        with fitz.open(base) as document:
            for index, elem in enumerate(elements, start=2):
                with fitz.open(plates / (elem["id"] + ".pdf")) as converted:
                    document[index].show_pdf_page(fitz.Rect(625, H - 290, 1041, H - 48), converted, 0)
            document.save(dest, garbage=4, deflate=True)
    return 2 + len(elements)


if __name__ == "__main__":
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=STUDIO / "mandala-rift-artbook.pdf")
    args = parser.parse_args()
    print(f"Wrote {make_book(args.out)} pages to {args.out}")
