"""Typeset surveyed game architecture as vector drawings, printable on four A3 sheets."""

from __future__ import annotations

import argparse
import html
import json
import math
import subprocess
import tempfile
from pathlib import Path

import fitz
from geometry import HERE, extent, surface_z

PAPER = "#f6f2e8"
INK = "#193331"
MUTED = "#4b625b"
FAINT = "#d6d7c9"
RUST = "#a04e2f"
TEAL = "#1c6872"
GOLD = "#947036"
PALETTE = {
    "clay": "#dfbe9d",
    "sunstone": "#e0c48c",
    "chalk": "#dad7bc",
    "jade": "#b4c8b7",
    "basalt": "#a2bcbb",
    "stone": "#cccbb9",
}
SHEETS = ["floorplan", "sun-court", "indigo-cistern", "sections"]
W = 1680
H = 1188


def esc(s):
    return html.escape(str(s), quote=True)


def n(x):
    return format(x, ".3f").rstrip("0").rstrip(".") or "0"


def attrs(data):
    return " ".join(f'{k}="{esc(v)}"' for k, v in data.items())


def xy(points):
    return " ".join(f"{n(x)},{n(y)}" for x, y in points)


def line(x, y, u, v, stroke=INK, width=1, extra=""):
    return f'<line x1="{n(x)}" y1="{n(y)}" x2="{n(u)}" y2="{n(v)}" stroke="{stroke}" stroke-width="{n(width)}" {extra}/>'


def rect(x, y, w, h, fill, stroke="none", width=0, extra=""):
    return f'<rect x="{n(x)}" y="{n(y)}" width="{n(w)}" height="{n(h)}" fill="{fill}" stroke="{stroke}" stroke-width="{n(width)}" {extra}/>'


def text(x, y, s, size=20, color=INK, weight=400, anchor="start", extra=""):
    return f'<text x="{n(x)}" y="{n(y)}" font-family="Noto Sans,sans-serif" font-size="{size}" font-weight="{weight}" fill="{color}" text-anchor="{anchor}" {extra}>{esc(s)}</text>'


def title(x, y, s, size=47):
    return f'<text x="{x}" y="{y}" fill="{INK}" font-family="Noto Serif,serif" font-size="{size}">{esc(s)}</text>'


def circle(x, y, r, fill, stroke="none", width=0, extra=""):
    return f'<circle cx="{n(x)}" cy="{n(y)}" r="{n(r)}" fill="{fill}" stroke="{stroke}" stroke-width="{n(width)}" {extra}/>'


def path(points, color=INK, width=2, fill="none", extra=""):
    return f'<polyline points="{xy(points)}" stroke="{color}" stroke-width="{n(width)}" fill="{fill}" stroke-linejoin="round" {extra}/>'


def blurb(x, y, lines, size=18, spacing=29):
    return "".join(text(x, y + i * spacing, t, size, MUTED) for i, t in enumerate(lines))


def note(x, y, s, color=MUTED):
    return text(x, y, s, 15, color, 700, extra='letter-spacing="1.6"')


def dimension(x, y, u, v, label):
    if y == v:
        caption = text((x + u) / 2, y - 7, label, 15, INK, 600, "middle")
    else:
        cx, cy = x - 8, (y + v) / 2
        caption = text(cx, cy, label, 15, INK, 600, "middle", f'transform="rotate(-90 {n(cx)} {n(cy)})"')
    return (
        line(x, y, u, v, MUTED, 1)
        + line(x - 3, y + 4, x + 3, y - 4, MUTED, 1.4)
        + line(u - 3, v + 4, u + 3, v - 4, MUTED, 1.4)
        + caption
    )


def prologue(sheet, heading, sub, view=None):
    data = {} if not view else {"data-scale": view[0], "data-ox": view[1], "data-oy": view[2]}
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="420mm" height="297mm" viewBox="0 0 1680 1188" role="img" aria-labelledby="sheet-title sheet-desc" {attrs(data)}>',
        f'<title id="sheet-title">Monsoon Exchange · {esc(heading)}</title><desc id="sheet-desc">{esc(sub)}</desc>',
        '<defs><pattern id="cover-hatch" patternUnits="userSpaceOnUse" width="8" height="8"><rect width="8" height="8" fill="#52665d"/><path d="M-2 2 L2 -2 M0 8L8 0M6 10L10 6" fill="none" stroke="#748779" stroke-width="1.2"/></pattern><pattern id="wet-hatch" patternUnits="userSpaceOnUse" width="10" height="8"><rect width="10" height="8" fill="#80b6bc"/><path d="M0 4Q2 2 5 4T10 4" fill="none" stroke="#3c808a" stroke-width="1.2"/></pattern><pattern id="substrate" patternUnits="userSpaceOnUse" width="9" height="9"><rect width="9" height="9" fill="#c6bca1"/><path d="M0 9L9 0" fill="none" stroke="#b1a787" stroke-width=".9"/></pattern></defs>',
        rect(0, 0, W, H, PAPER),
        note(55, 40, "YUGA   /   EMBER RITE     ·     DISTRICT SURVEY", TEAL),
        title(52, 100, heading, 49),
        text(1624, 42, f"MONSOON EXCHANGE     /     {sheet} OF 4", 17, MUTED, 700, "end"),
        text(1624, 88, sub, 17, MUTED, 400, "end"),
        line(54, 123, 1626, 123, INK, 2),
    ]


def footer(sheet):
    return (
        line(54, 1119, 1626, 1119, INK, 1.3)
        + note(55, 1155, "MONSOON EXCHANGE   /   MEASURED GAME ARCHITECTURE")
        + text(
            1626, 1155, f"A3 at 100%     ·     metre survey     ·     {sheet} / 4", 16, MUTED, 500, "end"
        )
        + "</svg>\n"
    )


class PlanView:
    def __init__(self, survey, mesh, scale, ox, oy, clip):
        self.s = survey
        self.g = mesh
        self.scale = scale
        self.ox = ox
        self.oy = oy
        self.clip = clip

    def at(self, p):
        return self.ox + p[0] * self.scale, self.oy - p[1] * self.scale

    def box(self, c, size):
        x, y = self.at((c[0] - size[0] / 2, c[1] + size[1] / 2))
        return x, y, size[0] * self.scale, size[1] * self.scale

    def layer(self, detail=False):
        x, y, w, h = self.clip
        o = [
            f'<defs><clipPath id="plan-clip"><rect x="{x}" y="{y}" width="{w}" height="{h}"/></clipPath></defs>',
            '<g clip-path="url(#plan-clip)">',
        ]
        for i in range(-80, 81, 5):
            a, b = self.at((i, i))
            tone = "#d7d9cc" if i % 10 == 0 else "#e5e4d9"
            o += [line(a, y, a, y + h, tone, 0.8), line(x, b, x + w, b, tone, 0.8)]
        for r in self.s["rooms"]:
            o.append(
                rect(
                    *self.box(r["center"], r["size"]),
                    PALETTE[r["material"]],
                    extra=f'id="room-{r["id"]}" data-room="{r["id"]}"',
                )
            )
        for link in self.s["links"]:
            id = link["id"]
            o.append(f'<g id="link-{id}" data-link="{id}">')
            for p in self.g["floors"]:
                if p["owner"] != id:
                    continue
                points = [self.at(v) for v in p["vertices"]]
                o.append(
                    f'<polygon points="{xy(points)}" fill="{PALETTE[p["material"]]}" stroke="{PALETTE[p["material"]]}" stroke-width=".35"/>'
                )
                if p["kind"] == "ramp":
                    v = p["vertices"]
                    cx = (v[0][0] + v[2][0]) / 2
                    cy = (v[0][1] + v[2][1]) / 2
                    dx = v[1][2] - v[0][2]
                    dy = v[3][2] - v[0][2]
                    ux, uy = (math.copysign(1, dx), 0) if dx else (0, math.copysign(1, dy))
                    span = 1.5 if detail else 1
                    start = self.at((cx - ux * span, cy - uy * span))
                    end = self.at((cx + ux * span, cy + uy * span))
                    cross = 0.42 if detail else 0.33
                    left = self.at(
                        (cx + ux * (span - 0.65) - uy * cross, cy + uy * (span - 0.65) + ux * cross)
                    )
                    right = self.at(
                        (cx + ux * (span - 0.65) + uy * cross, cy + uy * (span - 0.65) - ux * cross)
                    )
                    o.append(path([start, end], MUTED, 1.6) + path([left, end, right], MUTED, 1.6))
            o.append("</g>")
        for w in self.s["water"]:
            o.append(
                rect(
                    *self.box(w["center"], w["size"]),
                    "url(#wet-hatch)",
                    TEAL,
                    1.5,
                    extra=f'id="water-{w["id"]}"',
                )
            )
        for wall in self.g["walls"]:
            o.append(
                line(
                    *self.at(wall["a"]),
                    *self.at(wall["b"]),
                    INK,
                    3 if detail else 2.1,
                    'stroke-linecap="round"',
                )
            )
        for c in self.s["covers"]:
            o.append(
                rect(
                    *self.box(c["center"], c["size"]),
                    "url(#cover-hatch)",
                    INK,
                    1.35,
                    extra=f'id="cover-{c["id"]}" data-cover="{c["id"]}"',
                )
            )
        for obj in self.s["objectives"]:
            a, b = self.at(obj["center"])
            rad = obj["radius"] * self.scale
            o.append(
                circle(
                    a, b, rad, "none", RUST, 2.3, f'id="objective-{obj["id"]}" data-site="{obj["room"]}"'
                )
            )
            o.append(line(a - 5, b, a + 5, b, RUST, 1.2) + line(a, b - 5, a, b + 5, RUST, 1.2))
        for sp in self.s["spawns"]:
            o.append(f'<g id="spawn-{sp["id"]}">')
            for pad in sp["pads"]:
                px, py = self.at(pad)
                rr = 0.55 * self.scale
                o.append(
                    path(
                        [(px, py - rr), (px + rr, py), (px, py + rr), (px - rr, py), (px, py - rr)],
                        TEAL,
                        1.2,
                        PAPER,
                    )
                )
            o.append("</g>")
        for e in self.s["entries"]:
            cx, cy = e["center"][:2]
            nx, ny = e["normal"]
            half = e["width"] / 2
            p = self.at((cx - ny * half, cy + nx * half))
            q = self.at((cx + ny * half, cy - nx * half))
            o.append(
                line(
                    *p,
                    *q,
                    RUST,
                    2.6 if detail else 1.9,
                    f'id="entry-{e["id"]}" data-site="{e["site"]}" data-link="{e["link"]}" stroke-dasharray="5 4"',
                )
            )
        return "".join(o) + "</g>"


def north_scale(view, x, y, metres=10):
    s = view.scale
    return (
        path([(x, y - 20), (x - 5, y - 2), (x, y - 5), (x + 5, y - 2), (x, y - 20)], INK, 1, INK)
        + text(x, y - 28, "N", 15, INK, 700, "middle")
        + rect(x + 29, y - 7, s * metres / 2, 5, INK)
        + rect(x + 29 + s * metres / 2, y - 7, s * metres / 2, 5, PAPER, INK, 1)
        + text(x + 29, y + 15, "0", 13, MUTED)
        + text(x + 29 + s * metres, y + 15, f"{metres} m", 13, MUTED, 400, "end")
    )


KEYS = {
    "atk": "01",
    "scales": "02",
    "mid": "03",
    "toll": "04",
    "copper": "05",
    "ledger": "06",
    "a": "A",
    "sail": "07",
    "dyers": "08",
    "sluice": "09",
    "b": "B",
    "well": "10",
    "def": "11",
}
REGISTER = [
    "atk",
    "scales",
    "mid",
    "toll",
    "copper",
    "ledger",
    "a",
    "sail",
    "dyers",
    "sluice",
    "b",
    "well",
    "def",
]


def overview(s, g, m):
    v = PlanView(s, g, 7.8, 500, 613, (56, 148, 887, 944))
    out = prologue(
        1, "A monsoon trading district", "North-up ground plan and round openings", (v.scale, v.ox, v.oy)
    )
    out.append(v.layer())
    rooms = {r["id"]: r for r in s["rooms"]}
    for id in REGISTER:
        r = rooms[id]
        x, y = v.at(r["center"])
        k = KEYS[id]
        color = RUST if id == "a" else (TEAL if id == "b" else INK)
        if id in ("atk", "def"):
            y += 31 if id == "atk" else -28
        if id in ("a", "b"):
            y -= 39
        if id == "mid":
            x += 14
            y += 12
        out.append(
            circle(x, y, 15 if len(k) == 1 else 13, color, PAPER, 1.15)
            + text(x, y + 5, k, 15 if len(k) == 1 else 11.8, "#fffdf4", 700, "middle")
        )
    xmin, ymin, xmax, ymax = m["floor_bounds_xy"]
    west, top = v.at((xmin, ymax))
    east, bottom = v.at((xmax, ymin))
    out.append(dimension(west, 143, east, 143, f"{xmax - xmin:.1f} m   /   overall floor width"))
    out.append(dimension(79, top, 79, bottom, f"{ymax - ymin:.1f} m   /   overall floor length"))
    out.append(north_scale(v, 123, 1057, 20))
    out.append(line(954, 152, 954, 1088, FAINT, 2))
    out.append(note(989, 177, "DISTRICT REGISTER", TEAL))
    out.append(text(992, 218, "Room / surface datum", 29, INK, 650))
    out.append(text(1608, 218, "height", 16, MUTED, 600, "end"))
    for i, id in enumerate(REGISTER):
        r = rooms[id]
        y = 253 + i * 28.5
        out.append(text(993, y, KEYS[id], 16, TEAL, 700))
        out.append(text(1040, y, r["name"], 19, INK, 550))
        out.append(
            text(
                1368,
                y,
                r["role"]
                .replace("attacker spawn", "sun muster")
                .replace("defender spawn", "moon muster")
                .replace("screened central choice", "screened middle")
                .replace("wet floor and dry ledge", "wet and dry lanes"),
                15,
                MUTED,
            )
        )
        out.append(text(1610, y, f"{r['z']:+.1f} m", 17, INK, 500, "end"))
        out.append(line(994, y + 8, 1611, y + 8, FAINT, 0.8))
    out.append(note(990, 667, "RUN TO THE SITE CENTRE", TEAL))
    out.append(text(991, 707, "Branch choice costs time", 28, INK, 650))
    out.append(text(1610, 705, "metres  /  seconds", 14, MUTED, 600, "end"))
    for i, r in enumerate(m["routes"][:6]):
        y = 742 + i * 29
        out.append(text(993, y, r["name"], 19, INK))
        out.append(text(1610, y, f"{r['length_3d_m']:.2f}   /   {r['walk_s']:.2f}", 18, INK, 550, "end"))
    out.append(line(991, 915, 1610, 915, FAINT, 1))
    out.append(
        blurb(
            992,
            942,
            [
                "Timings use 0.5 m samples and a 0.65 m body radius.",
                "A 5 m/s walker starts at the marked team centre.",
                "Fights, setup and channel durations are separate.",
            ],
            16,
            24,
        )
    )
    out.append(rect(992, 1028, 22, 15, "url(#cover-hatch)") + text(1023, 1042, "cover", 16))
    out.append(rect(1120, 1028, 22, 15, "url(#wet-hatch)") + text(1152, 1042, "wet floor", 16))
    out.append(circle(1301, 1035, 8, "none", RUST, 2) + text(1321, 1042, "3 m ritual disk", 16))
    out.append(rect(993, 1064, 22, 15, "none", INK, 2) + text(1024, 1079, "exterior wall", 16))
    out.append(
        line(1220, 1070, 1246, 1070, RUST, 2, 'stroke-dasharray="4 3"')
        + text(1256, 1079, "open threshold", 16)
    )
    out.append(footer(1))
    return "".join(out)


def site_plate(s, g, m, site):
    r = next(row for row in s["rooms"] if row["id"] == site)
    sx, sy = r["center"]
    scale = 23.4
    v = PlanView(s, g, scale, 544 - scale * sx, 592 + scale * sy, (55, 154, 1007, 870))
    idx = 2 if site == "a" else 3
    subs = {
        "a": "Raised court · east bank · four independent thresholds",
        "b": "Lower court · west bank · three independent thresholds",
    }
    out = prologue(idx, r["name"], subs[site], (v.scale, v.ox, v.oy))
    out.append(v.layer(True))
    entries = [e for e in s["entries"] if e["site"] == site]
    covers = {c["id"]: c for c in s["covers"]}
    links = {link["id"]: link for link in s["links"]}
    ex, ey = v.at(r["center"])
    out.append(text(ex, ey + 32, "RITUAL", 16, RUST, 700, "middle"))
    for i, e in enumerate(entries, 1):
        ident = f"{site.upper()}{i}"
        cx, cy = e["center"][:2]
        nx, ny = e["normal"]
        px, py = v.at((cx - 1.7 * nx, cy - 1.7 * ny))
        out.append(
            circle(px, py, 19, RUST, PAPER, 1.4) + text(px, py + 5, ident, 13, "#fffaf0", 700, "middle")
        )
        for j, cid in enumerate(e["covers"]):
            c = covers[cid]
            x, y = v.at(c["center"])
            out.append(
                text(
                    x,
                    y + 5,
                    ident + ("a" if j == 0 else "b"),
                    14,
                    "#fffdf9",
                    700,
                    "middle",
                    extra='paint-order="stroke" stroke="#405049" stroke-width="2"',
                )
            )
    for witness in m["shelter_witnesses"]:
        if witness["cover"] not in {cid for e in entries for cid in e["covers"]}:
            continue
        x, y = v.at(witness["feet"])
        out.append(circle(x, y, 6.2, "#fffbec", TEAL, 2.6, f'id="shelter-{witness["cover"]}"'))
        out.append(circle(x, y, 1.7, TEAL))
    # Dimension only the site room. Dashed gaps in its drawn perimeter are true traversable openings.
    west, south = v.at((sx - r["size"][0] / 2, sy - r["size"][1] / 2))
    east, north = v.at((sx + r["size"][0] / 2, sy + r["size"][1] / 2))
    out.append(dimension(west, south + 94, east, south + 94, f"{r['size'][0]:g} m court width"))
    out.append(dimension(west - 101, north, west - 101, south, f"{r['size'][1]:g} m court depth"))
    out.append(north_scale(v, 130, 986, 5))
    out.append(line(1085, 153, 1085, 1087, FAINT, 2))
    out.append(note(1122, 178, "RITUAL FLOOR", TEAL))
    out.append(text(1122, 224, f"{r['z']:+.1f} m  /  {r['size'][0]:g} × {r['size'][1]:g} m", 33, INK, 600))
    out.append(
        blurb(
            1122,
            263,
            [
                "A carrier can kindle within the marked circle.",
                "A defender must reach the placed vessel within",
                "1.5 m. Each gate has two separate shelters.",
            ],
            16.8,
            25,
        )
    )
    out.append(line(1122, 342, 1621, 342, FAINT, 1))
    out.append(note(1122, 381, "ENTRANCES AND SHELTERS", TEAL))
    for i, e in enumerate(entries, 1):
        y = 425 + (i - 1) * 139
        ident = f"{site.upper()}{i}"
        linked = links[e["link"]]
        out.append(text(1122, y, ident, 21, RUST, 700))
        out.append(text(1172, y, linked["name"], 23, INK, 650))
        out.append(text(1622, y, f"{e['width']:g} m", 17, MUTED, 600, "end"))
        for j, cid in enumerate(e["covers"]):
            c = covers[cid]
            code = ident + ("a" if j == 0 else "b")
            out.append(text(1124, y + 36 + j * 29, code, 15, TEAL, 700))
            out.append(text(1172, y + 36 + j * 29, c["name"], 18, INK))
            out.append(text(1622, y + 36 + j * 29, f"{c['size'][2]:.2f} m high", 16, MUTED, 400, "end"))
        out.append(line(1122, y + 98, 1622, y + 98, FAINT, 1))
    notes = {
        "a": [
            "The short route climbs in two stages. An early",
            "turn at Rain Register opens a fourth north door.",
        ],
        "b": [
            "A covered passage reaches the south threshold.",
            "The optional runnel and two dry ledges lead",
            "through a separate east entrance.",
        ],
    }
    out.append(blurb(1122, 1005, notes[site], 17, 25))
    out.append(
        text(
            56,
            1090,
            "Teal pinpoints mark the tested standing shelters. Door widths are wall-to-wall. Heights are measured above the court floor.",
            17,
            MUTED,
        )
    )
    out.append(footer(idx))
    return "".join(out)


def feature_trace(s, m, axis, fixed, way):
    coords = set(way)
    sections = []
    for f in m["floors"]:
        x0, y0, x1, y1 = extent(f)
        fr, to = (x0, x1) if axis == 0 else (y0, y1)
        along = (y0, y1) if axis == 0 else (x0, x1)
        if not along[0] <= fixed <= along[1]:
            continue
        low, high = max(fr, min(way)), min(to, max(way))
        if high <= low:
            continue
        coords.update([low, high])
        sections.append((low, high, f))
    pts = []
    for val in sorted(coords):
        row = next((f for lo, hi, f in sections if lo - 1e-8 <= val <= hi + 1e-8), None)
        if row is None:
            raise ValueError(f"section missed floor at {val}")
        x, y = (val, fixed) if axis == 0 else (fixed, val)
        pts.append((val, surface_z(row, x, y)))
    return pts


def section_panel(s, g, x, y, w, h, series):
    # The positive coordinate can run either way in the section. The axis labels report world coordinates.
    name, axis, fixed, vstart, vend, marks, explanation = series
    plot_x = x + 70
    plot_y = y + 47
    pw = w - 115
    ph = h - 87
    profile = feature_trace(s, g, axis, fixed, [vstart, vend])
    zlo, zhi = -3, 7

    def position(h, z):
        return (
            plot_x + (h - vstart) / (vend - vstart) * pw,
            plot_y + ph * (zhi - z) / (zhi - zlo),
        )

    out = [note(x, y, name, TEAL), text(x + w, y, explanation, 15, MUTED, 400, "end")]
    for z in range(zlo + 1, zhi + 1):
        start = position(vstart, z)
        end = position(vend, z)
        out.append(line(*start, *end, FAINT, 1.65 if z == 0 else 0.75))
        if z % 2 == 0:
            out.append(text(start[0] - 12, start[1] + 5, f"{z:+} m", 14, MUTED, 400, "end"))
    ordered = sorted(profile, reverse=vend < vstart)
    floor = [position(a, b) for a, b in ordered]
    poly = [(floor[0][0], y + h - 37), *floor, (floor[-1][0], y + h - 37)]
    out.append(f'<polygon points="{xy(poly)}" fill="url(#substrate)"/>')
    out.append(path(floor, INK, 3))
    for a, mark in marks:
        px, py = position(a, zhi)
        out.append(line(px, py + 14, px, y + h - 37, FAINT, 1, 'stroke-dasharray="4 4"'))
        out.append(text(px, py + 8, mark, 15, INK, 620, "middle"))
        out.append(
            text(px, y + h - 13, ("X " if axis == 0 else "Y ") + f"{a:g}", 13.5, MUTED, 400, "middle")
        )
    for c in s["covers"] + s["water"]:
        center = c["center"]
        size = c["size"]
        base = c["z"]
        wet = "depth" in c
        height = c["depth"] if wet else size[2]
        i = 1 - axis
        if abs(center[i] - fixed) > size[i] / 2 + 1e-7:
            continue
        a = max(min(vstart, vend), center[axis] - size[axis] / 2)
        b = min(max(vstart, vend), center[axis] + size[axis] / 2)
        if b <= a:
            continue
        left, t = position(a, base + height)
        r, bot = position(b, base)
        out.append(
            rect(
                min(left, r),
                t,
                abs(r - left),
                bot - t,
                "url(#wet-hatch)" if wet else "url(#cover-hatch)",
                TEAL if wet else INK,
                1.5,
            )
        )
    return "".join(out)


def sections(s, g, m):
    rooms = {r["id"]: r for r in s["rooms"]}
    route = {i["id"]: i for i in m["routes"]}
    surface = rooms["a"]["z"] - rooms["b"]["z"]
    water = m["water_lanes"]
    steep = max(m["grades"], key=lambda i: i["percent"])
    normal = route["rotation"]
    alternate = route["rotation-mid"]
    water_feature = s["water"][0]
    out = prologue(4, "Grade, water and movement", "Measured longitudinal cuts and clearance assumptions")
    out.append(
        section_panel(
            s,
            g,
            66,
            183,
            995,
            356,
            (
                "01   /   COPPER ARCADE TO SUN COURT",
                1,
                40,
                -14,
                24,
                [(-11, "Arcade"), (-1, "Ramp toe"), (11.5, "Sun threshold"), (21, "Sun Court")],
                "Cut at X +40 m  ·  northward",
            ),
        )
    )
    out.append(
        section_panel(
            s,
            g,
            66,
            603,
            995,
            356,
            (
                "02   /   WEAVERS’ GATE TO SLUICE WALK",
                0,
                -11,
                5,
                -28,
                [(3, "Weavers’ Gate"), (-8, "Spillway crest"), (-17, "Spillway toe"), (-24, "Runnel")],
                "Cut at Y −11 m  ·  westward",
            ),
        )
    )
    out.append(line(1096, 150, 1096, 1087, FAINT, 2))
    out.append(note(1126, 182, "SURFACE REGISTER", TEAL))
    out.append(text(1126, 229, f"{surface:g} m of site relief", 30, INK, 650))
    out.append(
        blurb(
            1126,
            269,
            [
                f"Sun Court stands at {rooms['a']['z']:+.1f} m. The cistern floor",
                f"sits at {rooms['b']['z']:+.1f} m. Both use the same survey datum.",
            ],
            16.8,
            26,
        )
    )
    out.append(text(1126, 385, "Steepest grade", 23, INK, 650))
    out.append(
        blurb(
            1126,
            422,
            [
                "Ledger Climb rises after a flat elbow. The",
                f"steepest panel has a {steep['percent']:.2f}% grade, or",
                f"{math.degrees(math.atan(steep['percent'] / 100)):.1f}° above horizontal.",
            ],
            16.8,
            26,
        )
    )
    out.append(text(1126, 534, "Choosing water", 23, INK, 650))
    out.append(
        blurb(
            1126,
            571,
            [
                f"The {water_feature['size'][0]:g} m-wide dye runnel carries {water_feature['depth']:g} m",
                f"of water. Walk {water[0]['straight_m']:g} m straight in it in {water[0]['straight_walk_s']:.2f} s,",
                f"or take either dry side in {water[1]['straight_walk_s']:.2f} s at {s['rules']['walk_m_s']:g} m/s.",
            ],
            16.8,
            26,
        )
    )
    out.append(text(1126, 685, "Rotation reserve", 23, INK, 650))
    out.append(
        blurb(
            1126,
            722,
            [
                "B to A through Archive Court measures",
                f"{normal['length_3d_m']:.2f} m / {normal['walk_s']:.2f} s on the sampled floor.",
                f"Via the middle switch it takes {alternate['walk_s']:.2f} s.",
                "The 40 s burn and 3.5 s quench leave",
                f"{36.5 - normal['walk_s']:.2f} s or {36.5 - alternate['walk_s']:.2f} s for other actions.",
            ],
            16.8,
            26,
        )
    )
    out.append(line(1126, 872, 1621, 872, FAINT, 1))
    out.append(
        blurb(
            1126,
            911,
            [
                "Route times follow a 0.5 m grid with a",
                "0.65 m radius. Positions are measured to",
                "site centres. Combat and acceleration",
                "need playtesting.",
            ],
            16.8,
            26,
        )
    )
    out.append(
        blurb(
            66,
            1023,
            [
                "Cuts sample the actual floor patches at the specified coordinate. The vertical axis is exaggerated for legibility.",
                "Arrows on the plan point uphill. A flat landing occupies each right-angle turn.",
            ],
            16.4,
            25,
        )
    )
    out.append(footer(4))
    return "".join(out)


def build():
    def read(name):
        return json.loads((HERE / name).read_text())

    s = read("survey.json")
    g = read("geometry.json")
    m = read("metrics.json")
    return dict(
        zip(
            SHEETS,
            [overview(s, g, m), site_plate(s, g, m, "a"), site_plate(s, g, m, "b"), sections(s, g, m)],
        )
    )


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    svgs = build()
    for name, svg in svgs.items():
        target = HERE / (name + ".svg")
        if args.check:
            if not target.exists() or target.read_text() != svg:
                raise ValueError(f"Regenerate {name}.svg")
        else:
            target.write_text(svg, encoding="utf-8")
    if args.check:
        pdf = fitz.open(HERE / "floorplans.pdf")
        assert len(pdf) == 4
        for page, required in zip(pdf, ["Branch choice", "Seal Gallery", "Dye Gate", "Rotation reserve"]):
            assert required in page.get_text(), required
        png = fitz.Pixmap(str(HERE / "floorplan.png"))
        assert png.width == 1680 and png.height == 1188
    else:
        with tempfile.TemporaryDirectory() as d:
            parts = fitz.open()
            for name in svgs:
                target = Path(d) / (name + ".pdf")
                subprocess.run(
                    [
                        "inkscape",
                        str(HERE / (name + ".svg")),
                        "--export-area-page",
                        f"--export-filename={target}",
                    ],
                    check=True,
                    stdout=subprocess.DEVNULL,
                )
                src = fitz.open(target)
                parts.insert_pdf(src)
                src.close()
            parts.set_metadata(
                {
                    "title": "Monsoon Exchange · District Survey",
                    "author": "YUGA",
                    "subject": "Measured ground plan, two site enlargements and terrain sections",
                }
            )
            parts.save(HERE / "floorplans.pdf", garbage=4, deflate=True, no_new_id=True)
            parts.close()
        subprocess.run(
            [
                "inkscape",
                str(HERE / "floorplan.svg"),
                "--export-area-page",
                "--export-width=1680",
                "--export-height=1188",
                f"--export-filename={HERE / 'floorplan.png'}",
            ],
            check=True,
            stdout=subprocess.DEVNULL,
        )
    print(
        "Verified four measured vector sheets, A3 PDF and 1,680 × 1,188 overview."
        if args.check
        else "Wrote four SVG sheets, four-page A3 PDF and floorplan PNG."
    )


if __name__ == "__main__":
    main()
