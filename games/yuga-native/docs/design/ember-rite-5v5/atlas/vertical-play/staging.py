"""North-up setup diagram from the actual floorplan, curtains and supported lofts."""

from html import escape


def draw(plan, phase):
    hx, hy = 255, 268

    def point(xz):
        return (hx + xz[0] * 1.85, hy - xz[1] * 1.85)

    def label(x, y, value, size=12, fill="#354c40", weight="400", anchor="start"):
        return f'<text x="{x:.2f}" y="{y:.2f}" font-size="{size}" font-weight="{weight}" fill="{fill}" text-anchor="{anchor}">{escape(str(value))}</text>'

    rows = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 540" role="img" aria-labelledby="prep-title prep-desc"><title id="prep-title">Mandala Rift preparation floorplan</title><desc id="prep-desc">Both end rooms have a home loft and an eastern forward loft. The dotted curtains at minus and plus forty metres separate the setup floor from the two central sites.</desc><rect width="640" height="540" fill="#f2f1e5"/><g font-family="Georgia,serif">'
    ]
    nodes = plan["nodes"]
    for edge in plan["links"]:
        if edge["kind"] == "fold":
            continue
        pts = [
            nodes[edge["from"]]["xz"],
            *(edge.get("via") or []),
            nodes[edge["to"]]["xz"],
        ]
        xy = " ".join(f"{x:.2f},{y:.2f}" for x, y in map(point, pts))
        rows.append(
            f'<polyline points="{xy}" fill="none" stroke="#b8bda9" stroke-linecap="round" stroke-linejoin="round" stroke-width="{edge["width"] * 1.85:.1f}"/>'
        )
    for key, room in nodes.items():
        x, y = point(room["xz"])
        w, h = (v * 1.85 for v in room["size"])
        rows.append(
            f'<rect x="{x - w / 2:.2f}" y="{y - h / 2:.2f}" width="{w:.2f}" height="{h:.2f}" fill="#dcdfcb" stroke="#677e6c"/>'
        )
        if key in ("a", "b"):
            rows.append(label(x, y + 4, key.upper(), 15, "#294935", "700", "middle"))
        if key in ("atk", "def"):
            rows.append(label(x - w / 2 - 8, y + 3, room["label"], 12, anchor="end"))
    for barrier in phase["barriers"]:
        _, y = point((0, barrier["north_m"]))
        rows.append(
            f'<path d="M98 {y:.2f}H395" stroke="#964d32" stroke-width="2" stroke-dasharray="6 4"/>'
        )
        rows.append(label(36, y + 4, f"{barrier['north_m']:+g} m", 11, "#873f29"))
    rows.append(label(96, 30, "N ↑", 13))
    for pad in phase["pads"]:
        x, y = point(pad["center_xyz"][:2])
        rows.append(
            f'<circle cx="{x:.2f}" cy="{y:.2f}" r="5.5" fill="#326758" stroke="#fff5da" stroke-width="2"/><path d="M{x + 6:.2f} {y:.2f}H425" fill="none" stroke="#75897b" stroke-width=".8"/>'
        )
        rows.append(label(433, y - 2, pad["title"], 15, "#233f33", "700"))
        rows.append(
            label(
                433,
                y + 14,
                f"+{pad['height_m']:g} m deck · {pad['spawn_to_top_s']:g} s from spawn",
                11,
            )
        )
    rows.append('<path d="M38 495v6h37v-6" fill="none" stroke="#52634e"/>')
    rows.append(label(38, 518, "20 m", 11))
    rows.append(label(432, 260, "Two central sites", 14, "#233f33", "700"))
    rows.append(label(432, 278, "Open at tick 400.", 12))
    rows.append("</g></svg>")
    return "".join(rows) + "\n"
