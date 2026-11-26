"""Survey additional cover at the six courts beyond Mandala, on their actual floors."""

import argparse
from collections import deque
import json
from itertools import combinations
from math import dist, hypot
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
ATLAS = HERE.parent
sys.path.insert(0, str(ATLAS))
from audit import audit_geometry
from balance import approach_point

# Local east/north (m) from the actual site centre. A prop is a gameplay solid.
# These district-specific screen placements preserve the working 4.5 m apron.
FURNITURE = {
    ("lanka", "a"): [
        ("Copper shutter rack", -7.5, -4.7, 2.0, 2.2, 2.65),
        ("Flag locker", 5.4, 6.4, 2.8, 1.6, 2.55),
        ("Helm screen", 8.2, 0.0, 1.6, 2.0, 2.50),
    ],
    ("lanka", "b"): [
        ("Waterjar niche", -8.5, 0.5, 2.2, 1.8, 2.55),
        ("Seed chest wall", -5.3, -5.7, 2.4, 1.7, 2.50),
        ("Arbour gatepost", 6.0, 4.8, 1.6, 2.4, 2.60),
    ],
    ("ayodhya", "a"): [
        ("Petition archive", -6.7, -4.0, 2.6, 1.9, 2.55),
        ("Herald partition", 6.0, 5.6, 2.4, 1.8, 2.60),
        ("Witness screen", 8.8, -0.8, 1.6, 2.2, 2.50),
    ],
    ("ayodhya", "b"): [
        ("Boatbuilder locker", -6.0, 1.8, 1.7, 2.3, 2.65),
        ("Ferry board", 5.4, 5.7, 2.8, 1.6, 2.50),
        ("Oar shed front", -3.7, -6.6, 2.5, 1.7, 2.55),
    ],
    ("kurukshetra", "a"): [
        ("Proclamation screen", -6.2, -4.7, 2.0, 2.0, 2.60),
        ("Inkstone cupboard", 5.8, 5.3, 2.4, 1.6, 2.50),
        ("Tally board", -8.6, 0.4, 1.5, 2, 2.55),
    ],
    ("kurukshetra", "b"): [
        ("Sieve shelter", -6.5, 4.2, 2.2, 1.7, 2.60),
        ("Winnowing screen", 5.1, -5.1, 2.5, 1.7, 2.50),
        ("Granary partition", 0.3, 6.4, 2.5, 1.5, 2.55),
    ],
}
BODY = 0.65
STEP = 0.25
APRON = 4.5


def rounded(point):
    return [round(v, 3) for v in point]


def slug(label):
    return re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-")


def add_cover(site, label, xy, size, base, height, source):
    return dict(
        id=site + "-" + slug(label),
        label=label,
        center_xz=rounded(xy),
        size_xz=list(size),
        base_y=base,
        height_m=height,
        kind="hard",
        source=source,
        site=site,
    )


def box_distance(p, c):
    return hypot(
        *(
            max(0.0, abs(a - b) - s * 0.5)
            for a, b, s in zip(p, c["center_xz"], c["size_xz"])
        )
    )


def crosses(a, b, c):
    """2D slab test on a finite ray with a constant-height standing receiver."""
    lo, hi = 0.0, 1.0
    for x, y, ctr, width in zip(a, b, c["center_xz"], c["size_xz"]):
        near, far = ctr - width / 2, ctr + width / 2
        if abs(y - x) < 1e-10:
            if not near <= x <= far:
                return False
            continue
        t, u = sorted(((near - x) / (y - x), (far - x) / (y - x)))
        lo = max(lo, t)
        hi = min(hi, u)
        if lo > hi:
            return False
    return hi > 0 and lo < 1


def reachable(site, covers, start):
    """Quarter-metre flood from a legal entrance, eroded by the body radius."""
    ctr = site["xz"]
    size = site["size"]

    def legal(p):
        return all(abs(v - x) <= w / 2 - BODY for v, x, w in zip(p, ctr, size)) and all(
            box_distance(p, c) >= BODY + 0.015 for c in covers
        )

    def node(p):
        return tuple(round(v / STEP) for v in p)

    def world(q):
        return (q[0] * STEP, q[1] * STEP)

    point = node(start)
    if not legal(world(point)):
        raise ValueError(f"Blocked start {start}")
    seen = {point}
    queue = deque([point])
    while queue:
        x, y = queue.popleft()
        for dest in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if dest not in seen and legal(world(dest)):
                seen.add(dest)
                queue.append(dest)

    def has(p):
        return legal(p) and node(p) in seen

    return has


def make_pocket(block, threat, can_reach, all_cover):
    centre = block["center_xz"]
    v = [b - a for a, b in zip(threat, centre)]
    length = hypot(*v)
    if length < 1 or block["height_m"] < 2.2:
        return None
    vx, vy = (c / length for c in v)
    normal = (-vy, vx)
    for forward in (1.0, 1.25, 1.5):
        edge = min(
            s * 0.5 / abs(k)
            for s, k in zip(block["size_xz"], (vx, vy))
            if abs(k) > 1e-6
        )
        hide = [centre[0] + vx * (edge + forward), centre[1] + vy * (edge + forward)]
        if not can_reach(hide):
            continue
        shoulders = [
            [hide[i] + sgn * BODY * normal[i] for i in range(2)] for sgn in (-1, 1)
        ]
        # The four corners enclose the entire 0.45 m receiver. On a level court,
        # every ray between the 1.60 m eye and a 0..1.80 m corner stays below
        # the hard solid's 2.20 m minimum top. Its perspective shadow is convex.
        receiver_corners = [
            [hide[0] + dx, hide[1] + dz]
            for dx in (-0.451, 0.451)
            for dz in (-0.451, 0.451)
        ]
        if not all(
            crosses(threat, p, block) for p in [hide, *shoulders, *receiver_corners]
        ):
            continue
        for width in (1.25, 1.75, 2.25, 2.75, 3.25, 3.75, 4.25):
            for sign in (-1, 1):
                peek = [hide[i] + sign * width * normal[i] for i in range(2)]
                if (
                    can_reach(peek)
                    and all(
                        can_reach(
                            [hide[j] + (peek[j] - hide[j]) * f / 12 for j in range(2)]
                        )
                        for f in range(1, 13)
                    )
                    and not any(
                        crosses(threat, peek, c)
                        for c in all_cover
                        if c["height_m"] >= 1.62
                    )
                ):
                    return dict(
                        cover_id=block["id"],
                        posture="standing",
                        body_radius_m=0.45,
                        enclosing_plan_corners=4,
                        threat_xz=rounded(threat),
                        hide_xz=rounded(hide),
                        peek_xz=rounded(peek),
                    )
    return None


def study(plan):
    edges, _ = audit_geometry(plan)
    result = {"id": plan["id"], "title": plan["title"], "covers": [], "entrances": []}
    for site in ("a", "b"):
        room = plan["nodes"][site]
        ctr = room["xz"]
        w, d = room["size"]
        covers = [
            add_cover(
                site, c["label"], c["xz"], c["size"], room["y"], c["height"], "atlas"
            )
            for c in plan["cover"]
            if abs(c["xz"][0] - ctr[0]) <= w / 2 and abs(c["xz"][1] - ctr[1]) <= d / 2
        ]
        for label, x, y, wx, wy, h in FURNITURE[(plan["id"], site)]:
            block = add_cover(
                site,
                label,
                [ctr[0] + x, ctr[1] + y],
                [wx, wy],
                room["y"],
                h,
                "vertical-play",
            )
            if box_distance(ctr, block) < APRON:
                raise ValueError(f"Apron intersects {label}")
            if any(
                all(
                    abs(a - b) < (u + v) / 2 + 0.15
                    for a, b, u, v in zip(
                        block["center_xz"],
                        c["center_xz"],
                        block["size_xz"],
                        c["size_xz"],
                    )
                )
                for c in covers
            ):
                raise ValueError(f"Overlapping solids: {label}")
            covers.append(block)
        result["covers"] += covers
        for edge in edges:
            if site not in (edge.start, edge.end) or edge.kind == "fold":
                continue
            approach = edge.end if edge.start == site else edge.start
            points = edge.points if edge.start == site else edge.points[::-1]
            mouth = approach_point(room, points)
            # Move the probe inside both the floor and capsule boundary, including corner doors.
            interior = [
                max(v - s / 2 + 0.8, min(v + s / 2 - 0.8, p))
                for p, v, s in zip(mouth, ctr, room["size"])
            ]
            reach = reachable(room, covers, interior)
            if not reach(ctr):
                raise ValueError(f"Court centre blocked from {site}/{approach}")
            options = [
                v for c in covers if (v := make_pocket(c, interior, reach, covers))
            ]
            pairs = [
                pair
                for pair in combinations(options, 2)
                if dist(pair[0]["hide_xz"], pair[1]["hide_xz"]) >= 4.5
            ]
            if not pairs:
                raise ValueError(
                    f"Fewer than two full-height hides from {plan['id']}/{site}/{approach}: {options}"
                )
            first, second = min(
                pairs, key=lambda p: sum(dist(v["hide_xz"], interior) for v in p)
            )
            result["entrances"].append(
                dict(
                    id=f"{site}-{approach}",
                    site=site,
                    approach=approach,
                    mouth_xz=rounded(mouth),
                    floor_m=room["y"],
                    width_m=edge.width,
                    travel=edge.kind,
                    pockets=[first, second],
                )
            )
    return result


def render():
    surveys = [
        study(json.loads((ATLAS / "maps" / (key + ".json")).read_text()))
        for key in ("lanka", "ayodhya", "kurukshetra")
    ]
    return (
        json.dumps(
            {
                "schema": 1,
                "body_radius_m": BODY,
                "protected_apron_m": APRON,
                "districts": surveys,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    path = HERE / "sister-courts.json"
    body = render()
    if args.check:
        if not path.exists() or path.read_text() != body:
            raise SystemExit("Regenerate sister-courts.json")
    else:
        path.write_text(body)
    print(
        "Surveyed six courts in three districts with two distinct full-height hides for every registered entrance."
    )
