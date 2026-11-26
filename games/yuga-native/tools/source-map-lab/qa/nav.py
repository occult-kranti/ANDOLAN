"""Trace all official NAV centre heights against the rebuilt scene, including raised props."""

import argparse
from collections import Counter, defaultdict
import csv
import json
import math
from pathlib import Path
import struct

import numpy as np

from native import Bsp, texture_chain
from scene import Glb, file_sha


def nav_rows(path):
    with path.open(newline="", encoding="utf-8") as file:
        rows = [r for r in csv.DictReader(file) if r["mapName"] == "de_dust2"]
    result = []
    for r in rows:
        x = (float(r["northWestX"]) + float(r["southEastX"])) / 2
        y = (float(r["northWestY"]) + float(r["southEastY"])) / 2
        names = ("northWestZ", "southEastZ", "northEastZ", "southWestZ")
        z = sum(float(r[key]) for key in names) / 4
        result.append(
            (int(r["areaId"]), r["areaName"], [x * 0.0254, z * 0.0254, -y * 0.0254])
        )
    return result


def collision_neighbours(bsp, source_points, tolerance):
    """Intersect vertical centre rays with original player-solid world brush planes."""
    planes = np.frombuffer(
        bsp.get(1), dtype=np.dtype([("n", "<f4", 3), ("d", "<f4"), ("t", "<i4")])
    )
    brushes = np.frombuffer(bsp.get(18), dtype="<i4").reshape(-1, 3)
    side = np.frombuffer(
        bsp.get(19),
        dtype=np.dtype(
            [
                ("plane", "<u2"),
                ("texinfo", "<i2"),
                ("dispinfo", "<i2"),
                ("bevel", "<i2"),
            ]
        ),
    )
    leafbrush = np.frombuffer(bsp.get(17), dtype="<u2")
    node, leaf = bsp.get(5), bsp.get(10)
    world_brush = set()
    queue = [bsp.models()[0][9]]
    while queue:
        entry = queue.pop()
        if entry < 0:
            first, count = struct.unpack_from("<HH", leaf, (-1 - entry) * 32 + 24)
            world_brush.update(leafbrush[first : first + count])
        else:
            queue.extend(struct.unpack_from("<ii", node, entry * 32 + 4))
    zs = np.asarray([pt[2] for pt in source_points], np.float64)
    xy = np.asarray([pt[:2] for pt in source_points], np.float64).T
    closest = [None] * len(source_points)
    names = bsp.texture_names()
    for bi in sorted(world_brush):
        first, count, contents = brushes[bi]
        if not contents & (0x1 | 0x2 | 0x8 | 0x10000):
            continue
        sides = side[first : first + count]
        # Bevels expand a swept hull for a moving box. A point ray uses the true sides.
        sides = sides[sides["bevel"] == 0]
        pv = planes[sides["plane"]]
        n = pv["n"].astype(np.float64)
        upper, lower = n[:, 2] > 1e-6, n[:, 2] < -1e-6
        if not upper.any() or not lower.any():
            continue
        remainder = pv["d"][:, None] - n[:, :2] @ xy
        inside = np.all(remainder[~(upper | lower)] >= -0.01, axis=0)
        ceiling = remainder[upper] / n[upper, 2, None]
        top_row = ceiling.argmin(axis=0)
        top = ceiling[top_row, np.arange(len(zs))]
        inside &= top >= (remainder[lower] / n[lower, 2, None]).max(axis=0) - 0.01
        span = np.asarray(top - zs)
        for i in np.nonzero(inside & (np.abs(span) <= tolerance))[0]:
            index = np.flatnonzero(upper)[top_row[i]]
            if n[index, 2] < 0.55:
                continue
            if closest[i] is not None and abs(closest[i]["delta_source_units"]) <= abs(
                span[i]
            ):
                continue
            ti = int(sides[index]["texinfo"])
            closest[i] = {
                "world_brush": int(bi),
                "contents_hex": hex(int(contents)),
                "material": names[texture_chain(bsp, ti)[1]].lower()
                if ti >= 0
                else None,
                "delta_source_units": round(float(span[i]), 3),
            }
    return closest


def run(scene, nav, bsp_path=None, radius_su=18):
    g = Glb(scene)
    rows = nav_rows(nav)
    pts = np.array([r[2] for r in rows])
    tol = radius_su * 0.0254
    maximum = 128 * 0.0254
    types = ("jade", "structure", "static", "entity")
    height = {key: np.full(len(pts), np.inf) for key in types}
    surface = {key: [""] * len(pts) for key in types}
    for node, primitive, _, positions, idx in g.groups():
        ext = primitive.get("extras", {})
        ne = node.get("extras", {})
        material = g.doc["materials"][primitive["material"]]
        if "sourceOverlayId" in ext or "sourceOverlayId" in ne:
            continue
        if material.get("extras", {}).get("yugaGround"):
            kind = "jade"
        elif "sourceStaticPropIndex" in ne:
            kind = "static"
        elif "sourceModel" in ne:
            kind = "structure"
        elif "sourceMdl" in ne:
            kind = "entity"
        else:
            continue
        minimum = positions.min(axis=0)
        maxpos = positions.max(axis=0)
        in_box = np.nonzero(
            (pts[:, 0] >= minimum[0] - 0.0001)
            & (pts[:, 0] <= maxpos[0] + 0.0001)
            & (pts[:, 2] >= minimum[2] - 0.0001)
            & (pts[:, 2] <= maxpos[2] + 0.0001)
            & (pts[:, 1] >= minimum[1] - maximum)
            & (pts[:, 1] <= maxpos[1] + maximum)
        )[0]
        if not len(in_box):
            continue
        tri = positions[idx]
        normals = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
        tri = tri[normals[:, 1] > 0.55 * np.linalg.norm(normals, axis=1)]
        if not len(tri):
            continue
        low, hi = tri.min(axis=1), tri.max(axis=1)
        name = (
            ne.get("sourceMdl")
            or material.get("extras", {}).get("sourceMaterial")
            or node.get("name", "")
        )
        for i in in_box:
            x, y, z = pts[i]
            bound = (
                (low[:, 0] - 0.0001 <= x)
                & (hi[:, 0] + 0.0001 >= x)
                & (low[:, 2] - 0.0001 <= z)
                & (hi[:, 2] + 0.0001 >= z)
                & (low[:, 1] - maximum <= y)
                & (hi[:, 1] + maximum >= y)
            )
            if not bound.any():
                continue
            part = tri[bound]
            a = part[:, 0]
            s = part[:, 1] - a
            t = part[:, 2] - a
            den = s[:, 0] * t[:, 2] - s[:, 2] * t[:, 0]
            u = ((x - a[:, 0]) * t[:, 2] - (z - a[:, 2]) * t[:, 0]) / den
            v = (s[:, 0] * (z - a[:, 2]) - s[:, 2] * (x - a[:, 0])) / den
            inside = (u >= -1.0e-5) & (v >= -1.0e-5) & (u + v <= 1 + 1.0e-5)
            if not inside.any():
                continue
            elev = (a[:, 1] + u * s[:, 1] + v * t[:, 1])[inside]
            delta = elev - y
            nearest = delta[np.argmin(np.abs(delta))]
            if abs(nearest) < abs(height[kind][i]):
                height[kind][i] = nearest
                surface[kind][i] = name
    events = []
    groups = Counter()
    place_groups = defaultdict(Counter)
    props = Counter()
    for i, (id_, area, xyz) in enumerate(rows):
        close = [k for k in types if abs(height[k][i]) <= tol + 1.0e-6]
        if "jade" in close:
            family = "registered jade ground"
        elif "structure" in close:
            family = "other fixed brush surface"
        elif "static" in close:
            family = "raised/static prop geometry"
            props[surface["static"][i]] += 1
        elif "entity" in close:
            family = "entity-held geometry"
        else:
            family = "no close upward render surface"
        groups[family] += 1
        place_groups[area or "(unnamed)"][family] += 1
        if family != "registered jade ground":
            near = {}
            for k in types:
                if math.isfinite(height[k][i]) and abs(height[k][i]) <= maximum:
                    near[k] = {
                        "delta_source_units": round(float(height[k][i] / 0.0254), 3),
                        "asset": surface[k][i],
                    }
            events.append(
                dict(area=id_, place=area, classification=family, within_128_units=near)
            )
    if bsp_path and events:
        unresolved = [
            e for e in events if e["classification"] == "no close upward render surface"
        ]
        row_by_id = {row[0]: row[2] for row in rows}
        source = []
        for event in unresolved:
            x, up, minus_y = row_by_id[event["area"]]
            source.append(np.asarray([x, -minus_y, up]) / 0.0254)
        if source:
            with Bsp(bsp_path) as bsp:
                witnesses = collision_neighbours(bsp, source, radius_su)
            for event, witness in zip(unresolved, witnesses):
                event["world_collision_brush_within_tolerance"] = witness
    return {
        "schema": "yuga.dust2.nav-surface-witnesses.v1",
        "nav_sha256": file_sha(nav),
        "scene_sha256": file_sha(scene),
        "source_areas": len(rows),
        "vertical_tolerance_source_units": radius_su,
        "minimum_up_component": 0.55,
        "support_priority": list(types),
        "counts": dict(groups),
        "per_named_place": dict(place_groups),
        "static_mesh_counts": dict(props.most_common()),
        "non_jade_witnesses": events,
        "method": "For each NAV rectangle use its physical centre and mean of all four native corner elevations. A vertical ray tests barycentric containment in every upward triangle of the actual placed structure and static meshes. Printed marks/overlays do not supply a floor. Classification credits structural jade when several surfaces are within the height tolerance. Optional BSP diagnostics trace unresolved centres against world player-solid convex brushes. Displacement collision, static prop physics and the swept player hull are outside that second point-ray test.",
    }


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("scene", type=Path)
    p.add_argument("nav", type=Path)
    p.add_argument(
        "--bsp",
        type=Path,
        help="Check unmatched centres against original world clipping brushes",
    )
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    r = run(args.scene, args.nav, args.bsp)
    if args.output:
        args.output.write_text(json.dumps(r, indent=2) + "\n")
    else:
        print(json.dumps(r, indent=2))
