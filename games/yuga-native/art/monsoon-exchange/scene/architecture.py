"""Architectural motifs for Monsoon Exchange. Dimensions are metres in a local frame."""

from math import sin, cos, pi, tau
import random


def course(p, x, y, z, w, d, h, mat, lip=0.1):
    p.box(x, y, z, w, d, h, mat)
    p.box(x, y, z + h * 0.72, w + lip * 2, d + lip * 2, max(0.05, h * 0.22), "cream")


def pillar(p, x, y, z, h, r=0.27, body="sand", accent="gold"):
    p.box(x, y, z, r * 2.9, r * 2.9, h * 0.08, "basalt")
    p.box(x, y, z + h * 0.07, r * 2.6, r * 2.6, h * 0.065, body)
    profile = [
        (r * 1.27, h * 0.12),
        (r * 1.30, h * 0.17),
        (r * 0.86, h * 0.22),
        (r * 0.78, h * 0.28),
        (r * 0.63, h * 0.70),
        (r * 0.76, h * 0.76),
        (r * 1.07, h * 0.79),
        (r * 0.83, h * 0.82),
        (r * 1.23, h * 0.87),
        (r * 1.45, h * 0.9),
    ]
    p.lathe(x, y, z, profile, body, 12, 0.07, pi / 12, False)
    for level in (0.25, 0.735, 0.825):
        p.lathe(
            x, y, z, [(r * 0.91, h * level), (r * 0.91, h * level + 0.055)], accent, 16
        )
    p.box(x, y, z + h * 0.895, r * 2.60, r * 2.65, h * 0.055, body)
    p.box(x, y, z + h * 0.945, r * 3.6, r * 3.6, h * 0.06, "cream")


def roof(p, x, y, z, w, d, rise, mat="copper"):
    # Four eaves taper to a short crown at the ridge. Fine gold rolls reveal each pitch.
    def ring(w, d, h):
        return [
            (x + a * w / 2, y + b * d / 2, z + h)
            for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1))
        ]

    levels = [
        (w, d, 0),
        (w + 0.07, d + 0.07, 0.10),
        (w * 0.66, d * 0.56, rise * 0.68),
        (w * 0.42, d * 0.18, rise * 0.92),
        (w * 0.34, d * 0.08, rise),
    ]
    v = [v for a, b, h in levels for v in ring(a, b, h)]
    f = [(3, 2, 1, 0), (16, 17, 18, 19)] + [
        (4 * k + i, 4 * k + (i + 1) % 4, 4 * (k + 1) + (i + 1) % 4, 4 * (k + 1) + i)
        for k in range(4)
        for i in range(4)
    ]
    p.solid(v, f, mat)
    for i in range(4):
        for k in range(len(levels) - 1):
            p.beam(v[4 * k + i], v[4 * (k + 1) + i], 0.065, "gold", 8)
    p.box(x, y, z - 0.08, w + 0.15, d + 0.15, 0.095, "gold")
    p.box(x, y, z + rise, w * 0.4, d * 0.09, 0.11, "patina")


def finial(p, x, y, z, s):
    pr = [
        (0.33, 0),
        (0.34, 0.09),
        (0.19, 0.19),
        (0.24, 0.28),
        (0.29, 0.38),
        (0.22, 0.50),
        (0.10, 0.60),
        (0.15, 0.66),
        (0.11, 0.73),
        (0.045, 0.94),
        (0, 1.12),
    ]
    p.lathe(x, y, z, [(r * s, h * s) for r, h in pr], "gold", 20)


def cupola(p, x, y, z, r, mat="copper"):
    # Ribbed copper dome, lotus neck and small kalasha crown.
    profile = [
        (r, 0),
        (r * 1.04, r * 0.07),
        (r * 0.98, r * 0.12),
        (r * 0.91, r * 0.17),
        (r * 0.92, r * 0.31),
        (r * 0.83, r * 0.52),
        (r * 0.64, r * 0.72),
        (r * 0.42, r * 0.87),
        (r * 0.20, r * 0.97),
        (r * 0.065, r * 1.13),
    ]
    p.lathe(x, y, z, profile, mat, 40, 0, 0, True)
    for i in range(16):
        a = tau * i / 16
        for (r0, h0), (r1, h1) in zip(profile[2:], profile[3:]):
            p.beam(
                (x + (r0 + 0.02) * cos(a), y + (r0 + 0.02) * sin(a), z + h0),
                (x + (r1 + 0.02) * cos(a), y + (r1 + 0.02) * sin(a), z + h1),
                max(0.024, r * 0.012),
                "gold",
                5,
            )
    p.lathe(x, y, z, [(r * 0.98, 0.05), (r * 0.98, 0.13)], "patina", 40)
    finial(p, x, y, z + r * 1.1, r * 0.45)


def screen(p, x, y, z, w, h):
    # Open diamond lattice bounded by a thicker frame, sized to the opening.
    p.box(x, y, z, w, 0.16, 0.105, "sand")
    p.box(x, y, z + h - 0.1, w, 0.16, 0.1, "sand")
    for direction in (-1, 1):
        start = -w / 2 - h
        step = 0.42
        while start < w / 2 + h:
            end = start + direction * h
            lo = max(-w / 2, min(start, end))
            hi = min(w / 2, max(start, end))
            if hi > lo + 0.02:
                p.beam(
                    (x + lo, y, z + (lo - start) / direction),
                    (x + hi, y, z + (hi - start) / direction),
                    0.045,
                    "sand",
                    4,
                )
            start += step
    p.box(x - w / 2, y, z, 0.10, 0.17, h, "sand")
    p.box(x + w / 2, y, z, 0.10, 0.17, h, "sand")


def window(p, x, y, z, w, h, ornate=False):
    # Front plane faces -local Y. Arched head is a recessed masonry opening with dark timber shutters.
    fill = "ink"
    p.box(x, y, z, w, 0.10, h * 0.68, fill)
    n = 12
    pts = [(x - w / 2, z + h * 0.65), (x + w / 2, z + h * 0.65)] + [
        (
            x + w * 0.5 * (1 - 2 * i / n),
            z + h * 0.66 + h * 0.26 * (1 - abs(1 - 2 * i / n)) ** 0.65,
        )
        for i in range(n + 1)
    ]
    p.section(pts, y - 0.036, 0.105, fill)
    p.arc(x, y - 0.13, z + h * 0.65, w, 0.15, h * 0.30, 0.10, "sand")
    for sign in (-1, 1):
        p.box(x + sign * (w * 0.5 + 0.05), y - 0.07, z, 0.12, 0.17, h * 0.65, "sand")
    p.box(x, y - 0.05, z - 0.1, w + 0.34, 0.35, 0.13, "cream")
    if ornate:
        screen(p, x, y - 0.10, z + 0.10, w * 0.78, h * 0.50)
    else:
        for i in (-1, 0, 1):
            p.box(x + i * w * 0.23, y - 0.075, z + 0.06, 0.06, 0.09, h * 0.55, "wood")


def awning(p, x, y, z, w, d, clr="woven-blue"):
    # A striped loom cloth with real sag, depth and scalloped hem.
    nx, ny = 16, 5
    coords = []
    for j in range(ny + 1):
        t = j / ny
        for i in range(nx + 1):
            q = i / nx
            coords.append(
                (
                    x + (q - 0.5) * w,
                    y - d * t,
                    z
                    - 0.48 * t
                    - 0.23 * sin(pi * t)
                    - 0.08 * sin(pi * q)
                    + 0.045 * cos(q * tau * 4),
                )
            )
    for j in range(ny):
        for i in range(nx):
            k = j * (nx + 1) + i
            quad = [coords[k + 1], coords[k], coords[k + nx + 1], coords[k + nx + 2]]
            p.solid(quad, [(0, 1, 2, 3)], "ivory" if i in (1, 14) else clr)
    for i in range(nx):
        a, b = coords[ny * (nx + 1) + i : ny * (nx + 1) + i + 2]
        mc = ((a[0] + b[0]) / 2, a[1], (a[2] + b[2]) / 2 - 0.20)
        p.solid([a, b, mc], [(0, 1, 2)], "ivory" if i in (1, 14) else clr)
    for sign in (-1, 1):
        p.beam(
            (x + sign * w * 0.43, y, z - 0.62),
            (x + sign * w * 0.43, y - d, z - 0.47),
            0.053,
            "wood",
        )


def urn(p, x, y, z, r, material):
    p.lathe(
        x,
        y,
        z,
        [
            (0.42 * r, 0),
            (0.65 * r, 0.10 * r),
            (0.95 * r, 0.56 * r),
            (r, 0.91 * r),
            (0.78 * r, 1.3 * r),
            (0.45 * r, 1.56 * r),
            (0.54 * r, 1.64 * r),
            (0.50 * r, 1.70 * r),
        ],
        material,
        12,
    )


def hanging_lamp(p, x, y, z, drop):
    """A small pierced brass lamp suspended from a timber roof, in metres."""
    base = z - drop
    p.beam((x, y, z), (x, y, base + 0.50), 0.025, "ferric", 7)
    p.lathe(
        x,
        y,
        base,
        [
            (0.045, 0),
            (0.20, 0.08),
            (0.25, 0.19),
            (0.14, 0.24),
            (0.16, 0.39),
            (0.05, 0.49),
        ],
        "gold",
        16,
    )
    for i in range(6):
        theta = i * tau / 6
        p.beam(
            (x + 0.23 * cos(theta), y + 0.23 * sin(theta), base + 0.16),
            (x + 0.16 * cos(theta), y + 0.16 * sin(theta), base + 0.20),
            0.04,
            "signal",
            6,
        )


def banderole(p, x, y, z, width, length, cloth, phase=0):
    """Two long pointed, wind-bowed panels hung before an upper timber gallery."""
    p.beam((x - width * 0.62, y, z), (x + width * 0.62, y, z), 0.055, "gold", 8)
    vertices = []
    for row in range(11):
        t = row / 10
        for col in range(5):
            u = col / 4
            xx = x + (u - 0.5) * width + 0.22 * t * t + 0.08 * t * sin(4 * t + phase)
            yy = (
                y
                - 0.12 * t
                - 0.17 * sin(t * 5 + u * 0.8) * t
                + 0.045 * sin(u * pi * 4 + phase)
            )
            zz = z - length * t + 0.10 * sin(u * pi * 3 + phase) * t
            if row == 10:
                zz += 0.39 * abs(2 * u - 1)
            vertices.append((xx, yy, zz))
    for row in range(10):
        for col in range(4):
            i = row * 5 + col
            quad = [vertices[k] for k in (i, i + 5, i + 6, i + 1)]
            p.solid(quad, [(0, 1, 2, 3)], "ivory" if row in (1, 8) else cloth)


def kiosk(p, x, y, z, w, d, h, body="lime", canopy="tiles"):
    p.box(x, y, z, w, d, 0.36, "basalt")
    p.box(x, y, z + 0.34, w * 0.96, d * 0.95, 0.14, "sand")
    for sx in (-1, 1):
        for sy in (-1, 1):
            pillar(
                p,
                x + sx * w * 0.36,
                y + sy * d * 0.33,
                z + 0.46,
                h - 0.5,
                0.26,
                body,
                "gold",
            )
    p.arc(x, y - d * 0.35 - 0.12, z + h - 0.85, w * 0.72, 0.27, 0.58, 0.16, body)
    p.box(x, y, z + h, w, d, 0.20, "cream")
    roof(p, x, y, z + h + 0.19, w * 1.12, d * 1.17, w * 0.22, canopy)
    finial(p, x, y, z + h + 0.17 + w * 0.22, 0.62)


def gallery(p, x, y, z, w, d, h, clr="indigo", canopy="tiles"):
    bays = max(2, int(w / 3.2))
    spacing = w / bays
    p.box(x, y + d * 0.45, z, w + 0.4, 0.45, h, clr)
    p.box(x, y, z, w + 0.4, d + 0.3, 0.35, "basalt")
    for i in range(bays + 1):
        pillar(
            p,
            x - w / 2 + i * spacing,
            y - d * 0.32,
            z + 0.33,
            h - 0.33,
            0.29,
            "sand",
            "patina" if clr == "indigo" else "gold",
        )
    for i in range(bays):
        u = x - w / 2 + (i + 0.5) * spacing
        p.arc(
            u,
            y - d * 0.32 - 0.13,
            z + h * 0.70,
            spacing - 0.55,
            0.29,
            h * 0.21,
            0.17,
            "sand",
        )
        window(p, u, y + d * 0.45 - 0.25, z + 1.1, spacing * 0.40, h * 0.48, False)
    p.box(x, y, z + h, w + 0.65, d + 0.70, 0.20, "sand")
    roof(p, x, y, z + h + 0.19, w + 0.95, d + 1, 0.95, canopy)


def ring(p, x, y, z, r, w, mat, n=48):
    for i in range(n):
        a = tau * i / n
        b = tau * (i + 1) / n
        p.solid(
            [
                (x + rad * cos(t), y + rad * sin(t), z)
                for rad, t in (
                    (r - w / 2, a),
                    (r + w / 2, a),
                    (r + w / 2, b),
                    (r - w / 2, b),
                )
            ],
            [(0, 1, 2, 3)],
            mat,
        )


def tree(p, x, y, z, r, seed):
    rng = random.Random(seed)
    h = r * 2.35
    p.beam((x, y, z), (x + 0.1 * r, y, z + 0.63 * h), r * 0.14, "wood", 9)
    for i in range(11):
        a = tau * (i * 0.618 % 1)
        rad = r * (0.29 + 0.51 * rng.random())
        cx = x + rad * cos(a)
        cy = y + rad * sin(a)
        cz = z + h * (0.66 + 0.40 * rng.random())
        kr = r * (0.35 + 0.28 * rng.random())
        p.beam((x + 0.1 * r, y, z + 0.52 * h), (cx, cy, cz), r * 0.05, "wood", 6)
        profile = [
            (0.02, -0.38),
            (0.57, -0.27),
            (0.96, -0.02),
            (0.90, 0.18),
            (0.58, 0.39),
            (0.12, 0.47),
        ]
        p.lathe(
            cx,
            cy,
            cz,
            [(r0 * kr, h0 * kr) for r0, h0 in profile],
            rng.choice(["leaf", "leaf", "leaf-dark", "leaf-light"]),
            9,
            0.09,
            a,
            True,
        )
        # Small oblong leaves break the continuous crown contour in the court views.
        for j in range(22):
            ang = rng.uniform(0, tau)
            rr = kr * rng.uniform(0.76, 1)
            lx = cx + cos(ang) * rr
            ly = cy + sin(ang) * rr
            lz = cz + rng.uniform(-0.10, 0.32) * kr
            q = 0.12 + 0.09 * rng.random()
            p.solid(
                [
                    (lx - q, ly, lz),
                    (lx, ly - q * 0.55, lz + 0.09),
                    (lx + q, ly + 0.06, lz + 0.02),
                    (lx, ly + q * 0.52, lz - 0.04),
                ],
                [(0, 1, 2, 3)],
                rng.choice(["leaf", "leaf-light", "leaf-dark"]),
            )


def sun_wheel(p, x, y, z, r):
    # A brass measuring instrument: canted celestial ring on two forked shoulders.
    course(p, x, y, z, r * 2.0, r * 0.9, 0.38, "basalt")
    p.box(x, y, z + 0.35, r * 0.8, r * 0.65, 0.5, "sand")
    cz = z + r * 1.21

    def point(rad, ang, depth=0):
        return (
            x + cos(ang) * rad,
            y + sin(ang) * rad * 0.33 + depth,
            cz + sin(ang) * rad * 0.94,
        )

    for j in (0, 1):
        rr = r * (0.79 if j else 1)
        width = 0.075 if j else 0.125
        for i in range(48):
            p.beam(
                point(rr, tau * i / 48), point(rr, tau * (i + 1) / 48), width, "gold", 8
            )
    for i in range(16):
        a = tau * i / 16
        p.beam(point(0.12 * r, a), point(0.79 * r, a), 0.042, "gold", 6)
        p.beam(point(r * 0.87, a), point(r, a), 0.04, "patina", 5)
    for v in (-1, 1):
        p.beam(
            (x + v * r * 0.60, y, z + 0.35),
            (x + v * r * 0.58, y, cz),
            0.14,
            "copper",
            8,
        )
