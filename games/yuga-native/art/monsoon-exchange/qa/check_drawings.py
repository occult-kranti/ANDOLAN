"""Verify measured SVG geometry and independently render the four-page PDF and overview PNG."""

from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess
from tempfile import TemporaryDirectory
from xml.etree import ElementTree as ET

import fitz
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
PLAN = HERE.parent / "plan"
SHEETS = ("floorplan", "sun-court", "indigo-cistern", "sections")
NS = "{http://www.w3.org/2000/svg}"


def require(ok, msg):
    if not ok:
        raise ValueError(msg)


def attr_values(element, names):
    return tuple(float(element.attrib[k]) for k in names.split())


def vertices(element):
    return [
        tuple(map(float, pair.split(","))) for pair in element.attrib["points"].split()
    ]


def same(a, b, tol=0.002):
    require(
        len(a) == len(b) and max(abs(x - y) for x, y in zip(a, b)) <= tol,
        f"Drawing coordinate differs: {a} vs {b}",
    )


def sorted_points(points):
    return sorted(tuple(round(float(x), 3) for x in pt) for pt in points)


def measure_plan(root, survey, geometry, metrics, closeup):
    scale, ox, oy = attr_values(root, "data-scale data-ox data-oy")
    require(scale > 0, "Invalid map scale")

    def projected(p):
        return (ox + p[0] * scale, oy - p[1] * scale)

    elements = {e.attrib["id"]: e for e in root.iter() if "id" in e.attrib}
    x0, y0, clip_width, clip_height = attr_values(
        elements["plan-clip"][0], "x y width height"
    )

    def visible(pt):
        return x0 <= pt[0] <= x0 + clip_width and y0 <= pt[1] <= y0 + clip_height

    counts = Counter()
    for kind, group in (("room", "rooms"), ("cover", "covers"), ("water", "water")):
        for row in survey[group]:
            el = elements[f"{kind}-{row['id']}"]
            x, y = projected(row["center"])
            width, depth = (m * scale for m in row["size"][:2])
            same(
                attr_values(el, "x y width height"),
                (x - width / 2, y - depth / 2, width, depth),
            )
            if (
                closeup is None
                or (kind == "room" and row["id"] == closeup)
                or row.get("room") == closeup
            ):
                require(
                    visible((x - width / 2, y - depth / 2))
                    and visible((x + width / 2, y + depth / 2)),
                    "Key room/cover clipped",
                )
            counts[kind] += 1
    for row in survey["links"]:
        el = elements["link-" + row["id"]]
        polys = [p for p in el if p.tag == NS + "polygon"]
        patches = [p for p in geometry["floors"] if p["owner"] == row["id"]]
        actual = sorted(sorted_points(vertices(poly)) for poly in polys)
        designed = sorted(sorted_points(map(projected, p["vertices"])) for p in patches)
        require(actual == designed, f"Solid corridor polygons disagree for {row['id']}")
        counts["links"] += 1
        counts["link_patches"] += len(patches)
    for row in survey["objectives"]:
        el = elements["objective-" + row["id"]]
        x, y = projected(row["center"])
        radius = row["radius"] * scale
        same(attr_values(el, "cx cy r"), (x, y, radius))
        if closeup is None or closeup == row["room"]:
            require(
                visible((x - radius, y - radius)) and visible((x + radius, y + radius)),
                "Objective ring clipped",
            )
        counts["objective_disks"] += 1
    for row in survey["spawns"]:
        centers = []
        for diamond in elements["spawn-" + row["id"]]:
            pts = vertices(diamond)
            require(len(pts) == 5 and pts[0] == pts[4], "Missing closed spawn diamond")
            unique = set(pts)
            require(len(unique) == 4, "Degenerate spawn marker")
            centers.append(tuple(sum(p[k] for p in unique) / 4 for k in (0, 1)))
        require(
            sorted_points(centers) == sorted_points(map(projected, row["pads"])),
            "Spawn register differs",
        )
        counts["deployment_pads"] += len(centers)
    for row in survey["entries"]:
        el = elements["entry-" + row["id"]]
        x, y = row["center"][:2]
        nx, ny = row["normal"]
        half = row["width"] / 2
        require(
            el.get("data-site") == row["site"] and el.get("data-link") == row["link"],
            "Threshold identity mismatch",
        )
        wanted = [
            projected((x - ny * half, y + nx * half)),
            projected((x + ny * half, y - nx * half)),
        ]
        a, b = attr_values(el, "x1 y1"), attr_values(el, "x2 y2")
        require(
            sorted_points((a, b)) == sorted_points(wanted),
            "Gate endpoints do not match the normals and widths",
        )
        if closeup is None or closeup == row["site"]:
            require(visible(a) and visible(b), "Named site entry clipped")
        counts["entrances"] += 1
    if closeup:
        assigned = {
            cid
            for row in survey["entries"]
            if row["site"] == closeup
            for cid in row["covers"]
        }
        pins = {
            w["cover"]: w
            for w in metrics["shelter_witnesses"]
            if w["cover"] in assigned
        }
        require(set(pins) == assigned, "A named side of an entrance has no pin")
        for ident, w in pins.items():
            el = elements["shelter-" + ident]
            at = attr_values(el, "cx cy")
            same(at, projected(w["feet"]))
            require(visible(at), "Printed shelter pin clipped")
        counts["standing_shelter_pins"] = len(pins)
    plan_group = next(e for e in root.iter() if e.get("clip-path") == "url(#plan-clip)")
    drawn = Counter(
        tuple(sorted_points((attr_values(e, "x1 y1"), attr_values(e, "x2 y2"))))
        for e in plan_group
        if e.tag == NS + "line" and e.get("stroke-linecap") == "round"
    )
    planned = Counter(
        tuple(sorted_points((projected(w["a"]), projected(w["b"]))))
        for w in geometry["walls"]
    )
    require(planned == drawn, "Wall runs differ or a doorway is visibly sealed")
    counts["exterior_runs"] = sum(drawn.values())
    return {
        "drawing_units_per_metre": scale,
        "represented": dict(sorted(counts.items())),
        "clip_focus": closeup or "entire floor",
    }


def z_at(geometry, x, y):
    values = []
    for p in geometry["floors"]:
        sw, se, ne, nw = p["vertices"]
        if sw[0] - 0.001 <= x <= ne[0] + 0.001 and sw[1] - 0.001 <= y <= ne[1] + 0.001:
            fx = (x - sw[0]) / (se[0] - sw[0])
            fy = (y - sw[1]) / (nw[1] - sw[1])
            values.append(sw[2] + (se[2] - sw[2]) * fx + (nw[2] - sw[2]) * fy)
    require(
        values and max(values) - min(values) < 0.001,
        "Section loses support or falls on an inconsistent shared seam",
    )
    return sum(values) / len(values)


def measure_sections(root, geometry):
    labels = [e for e in root.iter(NS + "text") if e.text]
    profiles = [
        vertices(e) for e in root.iter(NS + "polyline") if e.get("stroke-width") == "3"
    ]
    require(len(profiles) == 2, "Two terrain sections required")
    result = {}
    for i, (profile, axis, cut) in enumerate(zip(profiles, ("Y", "X"), (40, -11))):
        baseline = min(y for x, y in profile)
        ticks = [
            e
            for e in labels
            if re.fullmatch(r"[+-]\d+ m", e.text)
            and abs(float(e.get("y")) - baseline) < 205
        ]
        tick0 = next(e for e in ticks if e.text == "+0 m")
        tick2 = next(e for e in ticks if e.text == "+2 m")

        # Align each elevation to the nearby plotted horizontal gridline, independent of the font baseline.
        def nearest_line(e):
            candidates = [
                float(n.get("y1"))
                for n in root.iter(NS + "line")
                if n.get("y1") == n.get("y2")
                and abs(float(n.get("y1")) - float(e.get("y"))) < 10
            ]
            require(len(set(candidates)) == 1, "Ambiguous elevation grid")
            return candidates[0]

        zero, two = map(nearest_line, (tick0, tick2))
        h_labels = [e for e in labels if e.text.startswith(axis + " ")]
        anchors = sorted((float(e.text[2:]), float(e.get("x"))) for e in h_labels)
        a, x0 = anchors[0]
        b, x1 = anchors[-1]
        xp = [p[0] for p in profile]
        yp = [p[1] for p in profile]
        errors = []
        for px in sorted(set(np.linspace(xp[0], xp[-1], 85)) | set(xp)):
            u = a + (b - a) * (px - x0) / (x1 - x0)
            elevation = 2 * (np.interp(px, xp, yp) - zero) / (two - zero)
            z = z_at(geometry, cut, u) if axis == "Y" else z_at(geometry, u, cut)
            errors.append(abs(elevation - z))
        require(max(errors) < 0.001, "Terrain section differs from measured floor")
        result[("copper_arcade_to_sun_court", "weavers_gate_to_sluice")[i]] = {
            "samples": len(errors),
            "max_floor_error_m": round(max(errors), 6),
        }
    return result


def raster_compare(pdf, directory):
    measured = {}
    size = (840, 594)
    for i, sheet in enumerate(SHEETS):
        src = PLAN / (sheet + ".svg")
        dest = directory / (sheet + ".png")
        subprocess.run(
            [
                "inkscape",
                str(src),
                "--export-area-page",
                "--export-width=840",
                "--export-height=594",
                f"--export-filename={dest}",
            ],
            check=True,
            stdout=subprocess.DEVNULL,
        )
        page = pdf[i]
        physical = tuple(z * 25.4 / 72 for z in (page.rect.width, page.rect.height))
        same(physical, (420, 297), 0.1)
        require(
            len(page.get_text().split()) >= 70 and bool(page.get_drawings()),
            "PDF lost searchable annotations or vector geometry",
        )
        pix = page.get_pixmap(
            matrix=fitz.Matrix(size[0] / page.rect.width, size[1] / page.rect.height),
            alpha=False,
        )
        pdf_pixels = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        svg_pixels = Image.open(dest).convert("RGB")
        if pdf_pixels.size != size:
            pdf_pixels = pdf_pixels.resize(size, Image.Resampling.LANCZOS)

        # Compare at print-thumbnail scale. Smoothing in both independent rasterizers
        # reduces font and antialias variation without concealing misplaced geometry.
        def differences(a, b):
            sm = (420, 297)
            arrays = [
                np.asarray(v.resize(sm, Image.Resampling.LANCZOS), dtype=float)
                for v in (a, b)
            ]
            delta = np.abs(arrays[0] - arrays[1]).mean(axis=2) / 255
            return {
                "mean_rgb_fraction": round(float(delta.mean()), 6),
                "fraction_over_20_percent": round(float((delta > 0.2).mean()), 6),
            }

        fills = differences(pdf_pixels, svg_pixels)
        require(
            fills["mean_rgb_fraction"] < 0.025
            and fills["fraction_over_20_percent"] < 0.02,
            f"PDF raster mismatch on {sheet}: {fills}",
        )
        measured[sheet] = {
            "page": i + 1,
            "paper_mm": [round(z, 2) for z in physical],
            "pdf_svg": fills,
        }
        if i == 0:
            png = Image.open(PLAN / "floorplan.png").convert("RGB")
            require(png.size == (1680, 1188), "Overview PNG has unexpected size")
            png_diff = differences(png, svg_pixels)
            require(
                png_diff["mean_rgb_fraction"] < 0.01
                and png_diff["fraction_over_20_percent"] < 0.01,
                "Overview PNG differs",
            )
            measured[sheet]["png_svg"] = png_diff
    return measured


def run():
    src = json.loads((PLAN / "survey.json").read_bytes())
    geo = json.loads((PLAN / "geometry.json").read_bytes())
    metrics = json.loads((PLAN / "metrics.json").read_bytes())
    roots = [ET.parse(PLAN / (sheet + ".svg")).getroot() for sheet in SHEETS]
    for root in roots:
        require(
            root.get("viewBox") == "0 0 1680 1188"
            and root.get("width") == "420mm"
            and root.get("height") == "297mm",
            "Invalid A3 view",
        )
        ids = [e.get("id") for e in root.iter() if e.get("id")]
        require(len(ids) == len(set(ids)), "Duplicate SVG IDs")
    with fitz.open(PLAN / "floorplans.pdf") as pdf, TemporaryDirectory() as tmp:
        require(len(pdf) == 4, "Four PDF pages required")
        printed = raster_compare(pdf, Path(tmp))
    files = [
        "survey.json",
        "geometry.json",
        "metrics.json",
        "floorplans.pdf",
        "floorplan.png",
        *(s + ".svg" for s in SHEETS),
    ]
    return {
        "schema": 1,
        "result": "pass",
        "units": "metres",
        "source_sha256": {
            f: sha256((PLAN / f).read_bytes()).hexdigest() for f in files
        },
        "plan_registration": {
            k: measure_plan(root, src, geo, metrics, focus)
            for k, root, focus in zip(SHEETS[:3], roots, (None, "a", "b"))
        },
        "section_registration": measure_sections(roots[3], geo),
        "delivery_rasters": printed,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = run()
    receipt = HERE / "drawing-verification.json"
    text = json.dumps(result, indent=2) + "\n"
    if args.check:
        stored = json.loads(receipt.read_bytes())
        # Each renderer must meet the acceptance tests in raster_compare.
        # Different font rasterizers can pass while averaging slightly different pixel errors.
        raster_keys = {"pdf_svg", "png_svg"}
        for record in (stored, result):
            for page in record["delivery_rasters"].values():
                for key in raster_keys:
                    page.pop(key, None)
        require(
            stored == result, "Measured geometry, source hashes or publication changed"
        )
    else:
        receipt.write_text(text)
    print("Four sheets match their measured inputs and presentation files.")
