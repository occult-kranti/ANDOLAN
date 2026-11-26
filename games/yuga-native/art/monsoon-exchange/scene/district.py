"""Architecture and ornament placed around the measured playable floor."""

import math
import random
from math import sin, pi
from meshkit import Batch
from architecture import (
    awning,
    banderole,
    course,
    cupola,
    finial,
    gallery,
    hanging_lamp,
    kiosk,
    pillar,
    ring,
    roof,
    screen,
    sun_wheel,
    tree,
    urn,
    window,
)


def colors(owner):
    if any(k in owner for k in ("sluice", "dyers", "sail", "-b")) or owner == "b":
        return "indigo", "basalt"
    if owner in ("def", "well", "def-a", "well-a", "well-def", "mid-well"):
        return "lime", "sand"
    if (
        owner in ("a", "copper", "toll", "ledger")
        or "copper" in owner
        or "ledger" in owner
    ):
        return "brick", "sand"
    return "sienna", "sand"


def boundaries(geom, rooms):
    for wall in geom["walls"]:
        x0, y0, z0 = wall["a"]
        x1, y1, z1 = wall["b"]
        L = math.hypot(x1 - x0, y1 - y0)
        ux = (x1 - x0) / L
        uy = (y1 - y0) / L
        n = wall["outward"]
        cx = (x1 + x0) / 2
        cy = (y1 + y0) / 2
        base = (z0 + z1) / 2
        owner = wall["owner"]
        i = int(wall["id"][1:])
        body, trim = colors(owner)
        p = Batch((cx, cy, base), (ux, uy), n)
        h = 2.85 if owner in rooms else (1.47 if i % 6 in (3, 4) else 2.35)
        if owner == "a" and n[0] > 0.9:
            h = 0.65
        elif owner == "b" and n[0] < -0.9:
            h = 0.44
        elif owner == "def" and n[1] > 0.9:
            h = 0.8
        elif owner in ("copper", "sail", "dyers"):
            h = 2.5
        # All structural faces stay on the outside of the registered boundary.
        p.box(0, 0.23, -0.65, L, 0.46, h + 0.65, body)
        p.box(0, 0.24, 0, L, 0.46, 0.43, "basalt")
        p.box(0, 0.27, h - 0.14, L, 0.52, 0.095, "cream")
        p.box(0, 0.31, h - 0.03, L, 0.60, 0.11, trim)
        if h > 2 and L > 4.8:
            bays = max(1, round(L / 4.25))
            w = L / bays
            for j in range(bays):
                x = -L / 2 + (j + 0.5) * w
                if (j + i) % 3 != 1:
                    window(
                        p,
                        x,
                        0.17,
                        0.58,
                        min(w * 0.50, 2.2),
                        min(h - 1.0, 1.65),
                        (j + i) % 4 == 0,
                    )
                if j:
                    p.box(x - w / 2, 0.18, 0.34, 0.25, 0.28, h - 0.36, trim)
            for j in range(bays + 1):
                x = max(-L / 2 + 0.16, min(L / 2 - 0.16, -L / 2 + j * w))
                p.box(x, 0.23, h + 0.05, 0.27, 0.31, 0.19, body)
        if h < 1 and L > 5:
            bays = max(1, int(L / 1.75))
            for j in range(bays):
                p.box(
                    -L / 2 + L * (j + 0.5) / bays,
                    0.24,
                    h + 0.08,
                    0.24,
                    0.30,
                    0.23,
                    "sand",
                )
        if z0 != z1:
            p.verts = [
                (x, y, z + (z1 - z0) / L * ((x - cx) * ux + (y - cy) * uy))
                for x, y, z in p.verts
            ]
        p.finish(
            "Wall." + wall["id"] + " · " + owner,
            "02 · Perimeter walls",
            "wall",
            owner,
            wall_id=wall["id"],
        )


def landmark_sun(r):
    x, y = r["center"]
    w, d = r["size"]
    z = r["z"]
    edge = x + w / 2
    # Side-on eastern loggia. The court retains its complete ritual disc and four doors.
    p = Batch((edge + 0.42, y, z), (0, -1), (1, 0))
    p.box(0, 4, -0.7, d * 0.96, 7.3, 0.9, "brick")
    p.box(0, 4, 0.19, d * 0.94, 7.1, 0.19, "sunstone")
    for s in (-1, 1):
        gallery(p, s * 7.25, 3.64, 0.35, 4.0, 4.6, 3.65, "brick", "copper")
    for sx in (-1, 1):
        for sy in (-1, 1):
            pillar(p, sx * 2.45, 3.82 + sy * 2.17, 0.35, 4.85, 0.43, "sand", "gold")
    p.arc(0, 1.44, 3.3, 4.47, 0.39, 1.26, 0.30, "sand")
    p.box(0, 3.82, 5.11, 6.65, 6.12, 0.29, "cream")
    roof(p, 0, 3.82, 5.4, 7.3, 6.75, 1.55, "copper")
    cupola(p, 0, 3.82, 6.87, 1.64)
    for sx in (-1, 1):
        for sy in (-1, 1):
            finial(p, sx * 3.05, 3.82 + sy * 2.8, 5.6, 0.62)
    # A sheltered sun calendar and dyed tags give the central opening depth from
    # a player's height. The separately legible measuring wheel sits nearer the court.
    for s in (-1, 1):
        banderole(p, s * 1.55, 3.55, 4.99, 0.60, 2.12, "woven-red", s)
        hanging_lamp(p, s * 1.83, 2.76, 5.08, 1.26)
        urn(p, s * 2.85, 1.12, 0.39, 0.39, "glaze")
    p.box(0, 6.54, 0.35, 5.65, 0.41, 4.76, "brick")
    window(p, 0, 6.27, 0.92, 2.60, 3.62, True)
    # Money-changers' houses behind the loggia. Their upper galleries form the
    # town horizon seen through the pavilion, with no footprint on the site.
    for j, (u, height, color) in enumerate(
        [
            (-10.1, 6.26, "sienna"),
            (-5.05, 8.55, "lime"),
            (0, 7.45, "brick"),
            (5.05, 9.0, "sienna"),
            (10.10, 5.92, "lime"),
        ]
    ):
        p.box(u, 9.6, -3.35, 5.15, 3.72, height + 3.35, color)
        course(p, u, 9.6, height - 0.12, 5.36, 4.02, 0.28, "sand")
        for xoff in (-1.23, 1.23):
            window(p, u + xoff, 7.66, height - 2.22, 1.37, 1.70, j % 2 == 0)
        if j % 2:
            awning(
                p,
                u,
                7.57,
                height - 1.89,
                4.4,
                0.80,
                "woven-red" if j == 1 else "woven-gold",
            )
            kiosk(p, u, 9.5, height + 0.12, 3.15, 2.80, 2.13, "sand", "tiles")
        else:
            roof(p, u, 9.58, height + 0.14, 5.60, 4.20, 0.92, "tiles")
    tree(p, -12.2, 6.2, -1.8, 2.65, 335)
    tree(p, 12.0, 7.9, -1.8, 3.06, 337)
    sun_wheel(p, 4.7, 0.92, 0.38, 1.82)
    p.finish(
        "Sun Court · copper sabha, galleries and celestial wheel",
        "04 · Landmark architecture",
        "art",
        "a",
    )


def landmark_cistern(r):
    x, y = r["center"]
    w, d = r["size"]
    z = r["z"]
    edge = x - w / 2
    # Negative external court opens toward spectator. Blue steps descend from all four retaining walls.
    p = Batch((edge - 0.22, y, z), (0, 1), (-1, 0))
    ow = d * 0.78
    od = 11
    cy = od / 2 + 0.30
    stepw = 0.72
    start_z = -0.13
    p.box(0, cy, -5.2, ow + 1, od + 1, 0.35, "basalt")
    for i in range(5):
        a = ow - 2 * stepw * i
        b = od - 2 * stepw * i
        top = start_z - i * 0.51
        for side in (-1, 1):
            p.box(
                0,
                cy + side * (b / 2 - stepw / 2),
                -4.85,
                a,
                stepw,
                top + 4.85,
                "indigo" if i % 2 == 0 else "basalt",
            )
            p.box(0, cy + side * (b / 2 - stepw / 2), top, a, stepw, 0.08, "slate")
            p.box(
                side * (a / 2 - stepw / 2),
                cy,
                -4.85,
                stepw,
                b - 2 * stepw,
                top + 4.85,
                "indigo",
            )
            p.box(
                side * (a / 2 - stepw / 2), cy, top, stepw, b - 2 * stepw, 0.08, "slate"
            )
    innerw = ow - 10 * stepw
    innerd = od - 10 * stepw
    p.box(0, cy, -2.70, innerw, innerd, 0.10, "water")
    for j in range(3):
        ring(p, -2.0 + j * 0.18, cy + 0.18, -2.59, 0.40 + j * 0.32, 0.026, "patina", 32)
    # Broken caustic glints give the recessed water its own scale in a player view.
    rng = random.Random(141)
    for j in range(32):
        u = rng.uniform(-innerw * 0.46, innerw * 0.46)
        v = cy + rng.uniform(-innerd * 0.43, innerd * 0.43)
        w = rng.uniform(0.11, 0.30)
        p.solid(
            [
                (u - w, v, -2.584),
                (u - w * 0.14, v + 0.031, -2.584),
                (u + w, v + 0.066, -2.584),
                (u + w * 0.17, v + 0.012, -2.584),
            ],
            [(0, 1, 2, 3)],
            "glaze" if j % 4 else "patina",
        )
    gallery(p, 0, od + 1.8, -0.06, ow + 2.4, 3.3, 5.05, "indigo", "tiles")
    # Water gauges and suspended trade pennants mark the five measured levels.
    for s in (-1, 1):
        for k in range(5):
            p.box(
                s * (ow / 2 - 0.57 - k * 0.71),
                cy,
                -0.24 - 0.51 * k,
                0.23,
                0.55,
                0.065,
                "gold",
            )
        banderole(p, s * 4.43, od + 0.54, 4.67, 0.68, 2.28, "woven-gold", s)
        hanging_lamp(p, s * 1.55, od + 0.77, 4.92, 1.26)
    for j in range(3):
        urn(p, -6.7 + j * 0.57, od + 0.44, 0.28, 0.29 + j * 0.045, "clay")
    for side in (-1, 1):
        kiosk(p, side * (ow / 2 + 0.78), 6.1, -0.06, 3.4, 4.0, 3.1, "sand", "tiles")
        cupola(p, side * (ow / 2 + 0.65), od + 2, 4.88, 1.49, "patina")
        tree(p, side * 8.4, od + 4.05, -1.45, 2.48, 110 + side)
    p.finish(
        "Indigo Cistern · five stepped terraces and water gallery",
        "04 · Landmark architecture",
        "art",
        "b",
    )


def central_gate(rooms):
    r = rooms["mid"]
    link_y = r["center"][1] - r["size"][1] / 2 - 1.1
    x = 2.0
    y = link_y
    z = 0.50
    p = Batch((x, y, z))
    opening = 5.1
    wing = 3.55
    half = opening / 2
    h = 6.55
    for sign in (-1, 1):
        cx = sign * (half + wing / 2 + 0.13)
        p.box(cx, 0.12, -0.56, wing, 2.8, h + 0.56, "brick")
        p.box(cx, 0.12, 0.14, wing + 0.02, 2.76, 0.43, "basalt")
        course(p, cx, 0.12, 3.72, wing + 0.14, 2.96, 0.25, "sand")
        window(p, cx, -1.15, 1.08, 1.52, 2.13, True)
        p.box(cx, -1.42, 4.02, wing * 0.72, 1.04, 0.34, "sand")
        p.box(cx, -1.40, 4.34, wing * 0.65, 0.85, 1.63, "brick")
        window(p, cx, -1.89, 4.51, 1.42, 1.34, True)
        roof(p, cx, -1.34, 6.0, wing * 0.86, 1.8, 0.66, "patina")
        p.box(cx, 0.16, h, wing + 0.35, 3.16, 0.24, "sand")
        kiosk(p, cx, 0.20, h + 0.23, 2.26, 2.20, 1.75, "sand", "tiles")
        cupola(p, cx, 0.20, h + 2.64, 0.94, "patina")
        sclr = "exchange-print" if sign < 0 else "woven-gold"
        awning(p, cx, -1.22, 3.53, wing * 0.95, 1.85, sclr)
    # Spandrel above the traversable center; stone below the arch stays empty.
    n = 28
    for i in range(n):
        aa = 2 * i / n - 1
        bb = 2 * (i + 1) / n - 1
        hh = lambda t: 3.9 + 1.88 * (1 - abs(t)) ** 0.61
        p.section(
            [(aa * half, hh(aa)), (bb * half, hh(bb)), (bb * half, h), (aa * half, h)],
            -1.03,
            2.45,
            "brick",
        )
    p.arc(0, -1.25, 3.90, opening, 0.34, 1.88, 0.27, "cream")
    for sign in (-1, 1):
        banderole(
            p,
            sign * (half + 0.61),
            -1.59,
            5.82,
            0.60,
            2.10,
            "woven-gold" if sign < 0 else "woven-blue",
            sign,
        )
        hanging_lamp(p, sign * (half - 0.44), -0.66, 4.43, 0.95)
    p.box(0, 0.12, h, opening + 0.48, 3.19, 0.26, "sand")
    p.box(0, 0.05, h + 0.24, 3.92, 2.4, 1.35, "sand")
    screen(p, 0, -1.2, h + 0.46, 2.9, 0.86)
    roof(p, 0, 0.06, h + 1.61, 4.58, 3.07, 0.79, "copper")
    cupola(p, 0, 0.06, h + 2.35, 0.80, "patina")
    p.finish(
        "Weavers’ Gate · sandstone loggia and jali oriels",
        "04 · Landmark architecture",
        "art",
        "mid",
    )


def north_archive(r):
    x, y = r["center"]
    w, d = r["size"]
    z = r["z"]
    p = Batch((x, y + d / 2 + 0.48, z))
    gallery(p, 0, 3.07, 0, 15.8, 4.75, 4.2, "lime", "patina")
    for side in (-1, 1):
        xx = side * 9.0
        course(p, xx, 2.6, -0.5, 3.65, 4.7, 4.70, "lime")
        window(p, xx, 0.15, 0.81, 1.7, 2.71, True)
        cupola(p, xx, 2.57, 4.28, 1.82, "sand")
    p.finish(
        "Archive Court · pale registry and two cupolas",
        "04 · Landmark architecture",
        "art",
        "def",
    )


def corridor_chapters(rooms):
    r = rooms["dyers"]
    x, y = r["center"]
    w, d = r["size"]
    z = r["z"]
    p = Batch((x, y, z))
    # Three ribs enter the clear volume only above player height. One luminous strip of sky stays open between vaults.
    for j in (-1, 0, 1):
        yy = j * d * 0.28
        p.arc(0, yy - 0.25, 3.55, w + 0.7, 0.38, 2.05, 0.30, "cream")
        for side in (-1, 1):
            # The eastern springer above the Loom Door lands on the door lintel.
            # Keep the whole surveyed 4 m opening free at shoulder height.
            if side == 1 and j == 0:
                continue
            pillar(p, side * (w / 2 + 0.44), yy, -0.02, 3.60, 0.27, "sand", "patina")
    for sign in (-1, 1):
        verts = []
        faces = []
        for j in range(8):
            yy = -d * 0.42 + d * 0.84 * j / 7
            for i in range(8):
                xx = sign * (w * 0.52 - i * w * 0.042)
                hh = 3.78 + 1.63 * (i / 7) ** 0.73 - 0.20 * sin(pi * j / 7)
                verts.append((xx, yy, hh))
        for j in range(7):
            for i in range(7):
                k = j * 8 + i
                faces.append((k, k + 1, k + 9, k + 8))
        p.solid(verts, faces, "exchange-print" if sign < 0 else "woven-gold")
    p.finish(
        "Dyers’ Passage · sprung ribs and indigo loom shades",
        "04 · Landmark architecture",
        "ceiling",
        "dyers",
        minimum_overhead_m=3.55,
    )
    r = rooms["copper"]
    x, y = r["center"]
    w, d = r["size"]
    z = r["z"]
    p = Batch((x + w / 2 + 0.55, y, z), (0, -1), (1, 0))
    gallery(p, 0, 1.6, 0, d * 0.76, 3.0, 3.54, "brick", "copper")
    p.finish(
        "Copper Arcade · ridge of hammered market bays",
        "04 · Landmark architecture",
        "art",
        "copper",
    )
    r = rooms["atk"]
    x, y = r["center"]
    w, d = r["size"]
    z = r["z"]
    p = Batch((x, y - d / 2 - 0.52, z), (-1, 0), (0, -1))
    for side in (-1, 1):
        gallery(p, side * 6.45, 2.22, -0.05, 6.8, 3.85, 3.42, "sienna", "tiles")
        awning(
            p,
            side * 6.45,
            0.45,
            2.98,
            5.85,
            1.14,
            "exchange-print" if side < 0 else "woven-gold",
        )
        for i in range(3):
            urn(p, side * (4.0 + i * 0.6), 1.5, 0, 0.32 + 0.07 * i, "clay")
    p.finish(
        "Caravan Yard · carriers’ porticoes", "04 · Landmark architecture", "art", "atk"
    )


def rect_hits(r, t):
    return r[0] < t[2] and t[0] < r[2] and r[1] < t[3] and t[1] < r[3]


def city(geom, rooms, seed=2417):
    # Residual blocks derived from the playable polygon union. Entire footprints, including
    # balconies, must fit in the residual area, leaving surveyed paths and thresholds empty.
    floors = []
    for floor in geom["floors"]:
        vs = floor["vertices"]
        floors.append(
            (
                min(p[0] for p in vs),
                min(p[1] for p in vs),
                max(p[0] for p in vs),
                max(p[1] for p in vs),
            )
        )
    reserve = [
        (45, 6, 62, 38),
        (-67, 2, -45, 37),
        (-14, 54, 15, 68),
        (-13, -65, 13, -55),
        (-7.3, -19.8, 10, -13.5),
        (47, -26, 54, 1),
    ]
    rng = random.Random(seed)
    count = 0
    occupied = list(reserve)
    for row, cy in enumerate(range(-54, 57, 10)):
        for col, cx0 in enumerate(range(-53, 57, 10)):
            cx = cx0 + (row % 2) * 2
            scale = rng.uniform(0.82, 1.05)
            w = rng.uniform(5.1, 7.7) * scale
            d = rng.uniform(4.8, 7.7) * scale
            bb = (
                cx - w / 2 - 1.45,
                cy - d / 2 - 1.45,
                cx + w / 2 + 1.45,
                cy + d / 2 + 1.45,
            )
            if any(rect_hits(bb, t) for t in floors + reserve):
                continue
            region = "b" if cx < -20 else "a" if cx > 20 else "mid"
            clr = rng.choice(
                [
                    "lime",
                    "sienna",
                    "brick",
                    "lime",
                    "indigo" if region == "b" else "sienna",
                    "turquoise" if region == "b" else "lime",
                ]
            )
            h = rng.choice([3.3, 4.15, 5.65, 6.7])
            z = -0.8 if cx < -22 else 0.25
            p = Batch((cx, cy, z))
            p.box(0, 0, -1.5, w, d, h + 1.5, clr)
            p.box(0, 0, -0.06, w + 0.14, d + 0.14, 0.47, "basalt")
            p.box(0, 0, h - 0.48, w + 0.22, d + 0.22, 0.14, "sand")
            p.box(0, 0, h - 0.14, w + 0.5, d + 0.5, 0.22, "cream")
            for elevation in [0.82, h * 0.57] if h > 5.4 else [0.82]:
                for x in (-w * 0.25, w * 0.25):
                    window(
                        p,
                        x,
                        -d / 2 - 0.055,
                        elevation,
                        w * 0.19,
                        1.4,
                        rng.random() < 0.18,
                    )
            if (row + col) % 3 == 0:
                roof(
                    p, 0, 0, h + 0.06, w + 0.7, d + 0.7, rng.uniform(1.25, 1.9), "tiles"
                )
            else:
                for sg in (-1, 1):
                    p.box(0, sg * (d / 2 - 0.14), h, w, 0.31, 0.52, clr)
                    p.box(sg * (w / 2 - 0.14), 0, h, 0.31, d, 0.52, clr)
                if (row + col) % 3 == 1:
                    p.box(w * 0.14, d * 0.09, h, w * 0.45, d * 0.44, 1.22, clr)
                    p.box(
                        w * 0.14, d * 0.09, h + 1.22, w * 0.50, d * 0.49, 0.14, "sand"
                    )
                    urn(p, -w * 0.26, -d * 0.12, h, 0.45, "clay")
            if (row * 3 + col) % 4 == 0:
                awning(
                    p,
                    0,
                    -d / 2 - 0.12,
                    2.71,
                    w * 0.73,
                    1.1,
                    rng.choice(["woven-gold", "woven-blue", "woven-red"]),
                )
            if (col + 2 * row) % 6 == 0:
                tree(
                    p,
                    -w * 0.29,
                    d * 0.17,
                    h if (row + col) % 3 else h + 0.7,
                    1.14,
                    seed + count,
                )
            p.finish(
                f"Block.{row:02d}.{col:02d} · occupied roofline",
                "05 · Urban fabric",
                "background",
                f"block-{row}-{col}",
            )
            occupied.append(bb)
            count += 1
    # Sub-house-sized enclosed plots retain a tree, water jar and brick planter.
    # Every crown and coping sits entirely off the surveyed player floors.
    for row, y in enumerate(range(-52, 55, 12)):
        for col, x in enumerate(range(-52, 55, 13)):
            extent = 2.18
            box = (x - extent, y - extent, x + extent, y + extent)
            if (row + 2 * col) % 3 or any(rect_hits(box, t) for t in floors + occupied):
                continue
            p = Batch((x, y, -2.13))
            course(p, 0, 0, 0, 2.9, 2.6, 0.42, "brick")
            tree(p, -0.26, 0.22, 0.39, 1.8, seed + row * 13 + col)
            urn(p, 1.28, -0.47, 0.42, 0.29, "glaze")
            p.finish(
                f"Garden.{row:02d}.{col:02d} · brick planter",
                "05 · Urban fabric",
                "background",
                f"garden-{row}-{col}",
            )
            occupied.append(box)
    # Leaf silhouettes grow in setback courtyards, with roots contained behind the architectural wall.
    for j, (x, y, z, r) in enumerate(
        [
            (-46, -34, -0.8, 1.95),
            (-45, 37, -0.5, 2.35),
            (52, 36, 0.1, 2.75),
            (49, 9, 2.4, 1.62),
            (16, 50, 0.9, 2.1),
            (-15, 52, 0.8, 2.48),
            (-18, -46, 0, 1.75),
            (20, -24, 0, 2.08),
            (-10, 3, -0.3, 1.6),
            (24, 5, 0.5, 1.65),
            (-24, 38, -0.3, 2.15),
            (-5, 57, 1.2, 1.7),
        ]
    ):
        if any(rect_hits((x - 0.35, y - 0.35, x + 0.35, y + 0.35), t) for t in floors):
            continue
        p = Batch((x, y, z))
        tree(p, 0, 0, 0, r, seed + j)
        p.finish(
            "Courtyard foliage " + str(j),
            "05 · Urban fabric",
            "background",
            "tree-" + str(j),
        )
    return count
