"""Draw the six companion courts as vector PDFs. Rebuild with ReportLab 4.4.9."""

import argparse
from io import BytesIO
from pathlib import Path
import json
from reportlab.lib.colors import HexColor
from reportlab.pdfgen.canvas import Canvas

HERE = Path(__file__).resolve().parent
PALETTE = {
    "ink": "#273b34",
    "green": "#295940",
    "muted": "#53675b",
    "tan": "#c9cab3",
    "paper": "#faf7ec",
    "floor": "#eef0df",
    "rust": "#97472c",
    "ring": "#9a894d",
}


def make():
    stream = BytesIO()
    doc = Canvas(stream, pagesize=(842, 595), invariant=1, pageCompression=1)
    doc.setTitle("Ember Rite | Six companion ritual courts")
    doc.setAuthor("YUGA map design panel")

    def pen(name):
        return HexColor(PALETTE.get(name, name))

    def label(x, y, s, size=11, font="Helvetica", colour="ink"):
        doc.setFont(font, size)
        doc.setFillColor(pen(colour))
        doc.drawString(x, y, str(s))

    def line(x1, y1, x2, y2, colour="muted", width=0.8):
        doc.setStrokeColor(pen(colour))
        doc.setLineWidth(width)
        doc.line(x1, y1, x2, y2)

    def rect(x, y, w, h, fill, stroke):
        doc.setFillColor(pen(fill))
        doc.setStrokeColor(pen(stroke))
        doc.rect(x, y, w, h, fill=1)

    def pt(p):
        return ", ".join(f"{v:.1f}" for v in p)

    counter = 0
    for district in json.loads((HERE / "sister-courts.json").read_text())["districts"]:
        plan = json.loads(
            (HERE.parent / "maps" / (district["id"] + ".json")).read_text()
        )
        for site in ("a", "b"):
            room = plan["nodes"][site]
            edges = [e for e in district["entrances"] if e["site"] == site]
            blocks = {c["id"]: c for c in district["covers"] if c["site"] == site}
            counter += 1
            rect(0, 0, 842, 595, "paper", "paper")
            label(
                35,
                553,
                "Y U G A     /     E M B E R   R I T E",
                11,
                "Helvetica-Bold",
                "green",
            )
            label(35, 510, room["label"], 32, "Times-Roman")
            label(
                36,
                487,
                f"{district['title']}   /   Site {site.upper()}   /   {room['size'][0]} x {room['size'][1]} m   /   Floor {room['y']:+g} m",
                11,
                "Helvetica",
                "muted",
            )
            line(35, 469, 806, 469, "tan")
            # One clear north-up plan per doorway prevents overlapping witness arrows and names.
            for idx, e in enumerate(edges):
                x = 35 + (idx % 2) * 395
                y = 260 - (idx // 2) * 193
                label(
                    x,
                    y + 185,
                    f"{idx + 1:02d}   {plan['nodes'][e['approach']]['label']}",
                    14,
                    "Times-Bold",
                )
                label(
                    x,
                    y + 168,
                    f"{e['width_m']:g} m mouth at ({pt(e['mouth_xz'])})",
                    8.7,
                    "Helvetica",
                    "muted",
                )
                cx, cz = room["xz"]
                w, h = room["size"]
                scale = min(160 / w, 112 / h)

                def xy(p):
                    return x + 88 + (p[0] - cx) * scale, y + 83 + (p[1] - cz) * scale

                ox, oy = xy(room["xz"])
                rect(
                    ox - w * scale / 2,
                    oy - h * scale / 2,
                    w * scale,
                    h * scale,
                    "floor",
                    "muted",
                )
                doc.setStrokeColor(pen("ring"))
                doc.setDash(2, 2)
                doc.circle(ox, oy, 4.5 * scale)
                doc.setDash()
                doc.circle(ox, oy, 3 * scale)
                selected = {p["cover_id"] for p in e["pockets"]}
                for b in blocks.values():
                    bx, by = xy(b["center_xz"])
                    bw, bh = b["size_xz"]
                    rect(
                        bx - bw * scale / 2,
                        by - bh * scale / 2,
                        bw * scale,
                        bh * scale,
                        "green" if b["id"] in selected else "tan",
                        "muted",
                    )
                tx, ty = xy(e["pockets"][0]["threat_xz"])
                path = doc.beginPath()
                path.moveTo(tx, ty + 4)
                path.lineTo(tx - 4, ty - 4)
                path.lineTo(tx + 4, ty - 4)
                path.close()
                doc.setFillColor(pen("rust"))
                doc.drawPath(path, fill=1, stroke=0)
                for n, p in enumerate(e["pockets"]):
                    hx, hy = xy(p["hide_xz"])
                    px, py = xy(p["peek_xz"])
                    line(hx, hy, px, py, "rust")
                    doc.setStrokeColor(pen("rust"))
                    doc.setFillColor(pen("paper"))
                    doc.circle(px, py, 2.4, fill=1)
                    doc.setFillColor(pen("ink"))
                    doc.circle(hx, hy, 5.1, fill=1, stroke=0)
                    label(hx - 1.9, hy - 2.3, str(n + 1), 7, "Helvetica-Bold", "paper")
                    block = blocks[p["cover_id"]]
                    row = y + 118 - n * 45
                    label(
                        x + 177,
                        row,
                        str(n + 1) + ". " + block["label"],
                        9.7,
                        "Helvetica-Bold",
                    )
                    label(
                        x + 177,
                        row - 13,
                        f"{block['height_m']:.2f} m  /  standing",
                        8.7,
                        "Helvetica",
                        "muted",
                    )
                    label(
                        x + 177,
                        row - 25,
                        "Hide (" + pt(p["hide_xz"]) + ")",
                        8.7,
                        "Helvetica",
                        "muted",
                    )
                line(x + 8, y + 7, x + 8 + 5 * scale, y + 7, "ink", 1.3)
                label(x + 12 + 5 * scale, y + 4, "5 m", 8)
                label(x + 154, y + 148, "N", 8, "Helvetica-Bold", "muted")
            line(35, 45, 806, 45, "tan")
            label(
                35,
                27,
                "North up. Triangle = threshold observer. Number = hide. Open circle = exposed peek. Coordinates in metres east / north.",
                8.2,
                "Helvetica",
                "muted",
            )
            label(770, 27, f"{counter} / 6", 10, "Helvetica-Bold", "green")
            doc.showPage()
    doc.save()
    return stream.getvalue()


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--check", action="store_true")
    args = p.parse_args()
    path = HERE / "companion-courts.pdf"
    data = make()
    if args.check:
        if not path.is_file() or path.read_bytes() != data:
            raise SystemExit("Regenerate companion-courts.pdf with ReportLab 4.4.9")
    else:
        path.write_bytes(data)
    print("Six north-up court sheets with one diagram per approach.")
