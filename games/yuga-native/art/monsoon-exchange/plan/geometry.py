"""Develop the measured rooms and axial ramp runs into a single walkable surface."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
TOL = 1e-6


def rounded(value):
    return round(value, 6) or 0


def as_json(value):
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def emit(path, data, check=False):
    if check:
        if not path.is_file() or path.read_bytes() != data:
            raise ValueError(f"Regenerate {path.name}")
    else:
        path.write_bytes(data)


def extent(box):
    vertices = box["vertices"]
    return vertices[0][0], vertices[0][1], vertices[2][0], vertices[2][1]


def surface_z(box, x, y):
    sw, se, ne, nw = box["vertices"]
    return (
        sw[2]
        + (se[2] - sw[2]) * (x - sw[0]) / (se[0] - sw[0])
        + (nw[2] - sw[2]) * (y - sw[1]) / (nw[1] - sw[1])
    )


def floor_box(owner, kind, finish, suffix, bounds, height):
    x1, y1, x2, y2 = bounds
    if min(x2 - x1, y2 - y1) <= TOL:
        raise ValueError(f"{owner}: degenerate floor {bounds}")
    corners = [(x1, y1), (x2, y1), (x2, y2), (x1, y2)]
    return {
        "id": owner + "-" + suffix,
        "owner": owner,
        "kind": kind,
        "material": finish,
        "vertices": [[rounded(x), rounded(y), rounded(height(x, y))] for x, y in corners],
    }


def build_floors(survey):
    floors = []
    for r in survey["rooms"]:
        x, y = r["center"]
        w, d = r["size"]
        floors.append(
            floor_box(
                r["id"],
                "room",
                r["material"],
                "floor",
                (x - w / 2, y - d / 2, x + w / 2, y + d / 2),
                lambda x, y: r["z"],
            )
        )
    for link in survey["links"]:
        path = link["points"]
        half = link["width"] / 2
        axes = []
        for a, b in zip(path, path[1:]):
            dx, dy = b[0] - a[0], b[1] - a[1]
            if bool(dx) == bool(dy):
                raise ValueError(f"{link['id']}: runs must be non-zero and axial")
            axes.append((int(math.copysign(1, dx)) if dx else 0, int(math.copysign(1, dy)) if dy else 0))
        bends = {i for i in range(1, len(path) - 1) if axes[i] != axes[i - 1]}
        for i in sorted(bends):
            x, y, z = path[i]
            floors.append(
                floor_box(
                    link["id"],
                    "landing",
                    link["material"],
                    f"turn-{i}",
                    (x - half, y - half, x + half, y + half),
                    lambda x, y: z,
                )
            )
        for i, (a, b) in enumerate(zip(path, path[1:])):
            ux, uy = axes[i]
            x1, y1 = a[0] + ux * half * (i in bends), a[1] + uy * half * (i in bends)
            x2, y2 = b[0] - ux * half * (i + 1 in bends), b[1] - uy * half * (i + 1 in bends)
            length = (x2 - x1) * ux + (y2 - y1) * uy
            if length <= TOL:
                raise ValueError(f"{link['id']}: insufficient elbow landing")
            grade = (b[2] - a[2]) / length
            if abs(grade) > 0.30:
                raise ValueError(f"{link['id']}: grade {grade:.3f} exceeds the 30% design budget")
            bounds = (
                min(x1, x2) - abs(uy) * half,
                min(y1, y2) - abs(ux) * half,
                max(x1, x2) + abs(uy) * half,
                max(y1, y2) + abs(ux) * half,
            )

            def height(x, y):
                return a[2] + ((x - x1) * ux + (y - y1) * uy) * grade

            floors.append(
                floor_box(
                    link["id"],
                    "ramp" if grade else "walk",
                    link["material"],
                    f"run-{i + 1}",
                    bounds,
                    height,
                )
            )
    return floors


def build_walls(floors):
    """Split perimeter runs at T-junctions. An edge shared across a doorway is open."""
    extents = {f["id"]: extent(f) for f in floors}
    bounds = list(extents.values())
    for j, a in enumerate(bounds):
        for k, b in enumerate(bounds[:j]):
            if min(a[2], b[2]) - max(a[0], b[0]) > TOL and min(a[3], b[3]) - max(a[1], b[1]) > TOL:
                raise ValueError(f"Plan overlaps {floors[j]['id']} and {floors[k]['id']}")
    walls = []
    seams = 0
    for floor in floors:
        poly = floor["vertices"]
        for j, p in enumerate(poly):
            q = poly[(j + 1) % 4]
            axis = 0 if p[1] == q[1] else 1
            other = 1 - axis
            lo, hi = sorted((p[axis], q[axis]))
            line = p[other]
            cut = {lo, hi}
            touch = []
            for f in floors:
                if f is floor:
                    continue
                box = extents[f["id"]]
                low, high = box[axis], box[axis + 2]
                if (
                    hi <= low + TOL
                    or lo >= high - TOL
                    or not any(abs(line - box[t]) < TOL for t in (other, other + 2))
                ):
                    continue
                left, right = max(lo, low), min(hi, high)
                cut.update((left, right))
                touch.append((left, right, f))
            cuts = sorted(cut)
            for left, right in zip(cuts, cuts[1:]):
                mid = (left + right) / 2
                shared = next((f for u, v, f in touch if u < mid < v), None)
                points = []
                for val in (left, right) if p[axis] < q[axis] else (right, left):
                    x, y = (val, line) if axis == 0 else (line, val)
                    z = surface_z(floor, x, y)
                    if shared and abs(z - surface_z(shared, x, y)) > TOL:
                        raise ValueError(f"Vertical seam: {floor['id']} and {shared['id']} at {(x, y)}")
                    points.append([rounded(x), rounded(y), rounded(z)])
                if shared:
                    seams += 1
                    continue
                a, b = points
                length = math.dist(a[:2], b[:2])
                outside = [rounded((b[1] - a[1]) / length), rounded((a[0] - b[0]) / length)]
                walls.append(
                    {
                        "id": f"w{len(walls) + 1:03}",
                        "owner": floor["owner"],
                        "a": a,
                        "b": b,
                        "outward": outside,
                    }
                )
    return walls, seams // 2


def build(survey):
    floors = build_floors(survey)
    walls, seams = build_walls(floors)
    return {
        "schema": 1,
        "id": survey["id"],
        "axes": survey["basis"],
        "floors": floors,
        "walls": walls,
        "open_flat_or_ramped_seams": seams,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    result = build(json.loads((HERE / "survey.json").read_text()))
    emit(HERE / "geometry.json", as_json(result).encode(), args.check)
    print(
        f"{len(result['floors'])} floor patches, {len(result['walls'])} exterior wall runs, {result['open_flat_or_ramped_seams']} open floor seams"
    )


if __name__ == "__main__":
    main()
