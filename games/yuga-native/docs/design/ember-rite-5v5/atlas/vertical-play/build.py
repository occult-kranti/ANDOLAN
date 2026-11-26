"""Assemble the portable fieldbook and all-district door register from measured data."""

import argparse
import base64
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ATLAS = HERE.parent
sys.path.insert(0, str(ATLAS / "rehearsal"))
from footprints import project_building
from staging import draw as draw_staging

DOC_ROOT = "https://github.com/occult-kranti/ANDOLAN/blob/game/yuga-hanuman-trial/games/yuga-native/docs/design/ember-rite-5v5/atlas/vertical-play"


def read(name):
    return json.loads(name.read_text())


def load_studies():
    primary = read(HERE / "architecture.json")
    deeper = read(HERE / "mandala-body-cover.json")
    certs = {
        (entry["id"], p["cover_id"]): p
        for entry in deeper["entrances"]
        for p in entry["pockets"]
    }
    for entry in primary["entrances"]:
        for p in entry["pockets"]:
            proof = certs[entry["id"], p["cover_id"]]
            for direction, prefix in (("forward", ""), ("reverse", "reverse_")):
                part = proof[direction]
                if (
                    part["shoulder_xz"] != p[prefix + "hide_xz"]
                    or part["peek_xz"] != p[prefix + "peek_xz"]
                ):
                    raise ValueError(
                        "Whole-body position does not match surveyed shoulder and peek"
                    )
                p[prefix + "body_hide_xz"] = part["hide_xz"]
    return {
        "mandala": primary,
        **{d["id"]: d for d in read(HERE / "sister-courts.json")["districts"]},
    }


def court_maps():
    maps = []
    for district, study in load_studies().items():
        plan = read(ATLAS / "maps" / f"{district}.json")
        added = [
            dict(
                label=c["label"],
                xz=c["center_xz"],
                size=c["size_xz"],
                height=c["height_m"],
            )
            for c in study["covers"]
            if c["source"] == "vertical-play" and c.get("collision", True)
        ]
        for entry in study["entrances"]:
            pcs = entry["pockets"]
            if len(pcs) != 2 or pcs[0]["cover_id"] == pcs[1]["cover_id"]:
                raise ValueError("Two distinct solids required at " + entry["id"])
        maps.append(
            {
                **plan,
                "building": project_building(plan),
                "cover": plan["cover"] + added,
                "studyCovers": study["covers"],
                "entrances": study["entrances"],
            }
        )
    return maps


def coords(p):
    return "(" + ", ".join(f"{v:.2f}".rstrip("0").rstrip(".") for v in p) + ")"


def door_table(maps):
    rows = [
        "# Entrance survey · all four districts",
        "",
        "This register is keyed to actual physical route thresholds. Each row gives the registered width, the mouth in metres east/north and two independently reachable hiding positions supported by different collision solids. A position protects against its named observer. Rotation, return fire, an elevated eye or another entrance may expose it. A signed fold terminates in an approach room and does not count as another doorway into the site. [Interactive floorplans](https://occult-kranti.github.io/ANDOLAN/production/ember-rite/vertical-play.html) · [Mandala survey](architecture.json) · [Three companion districts](sister-courts.json)",
        "",
        "The Mandala floor comes from the exported triangle mesh. Forward observers stand four metres back along the actual approach. At each Mandala position a convex enclosing prism certifies the 0.45 m receiver against the named ground observer. Nine samples at the neighbouring shoulder mark quantify the change under a raised observer. The reverse check moves the observer to the court centre. The alternate districts use the registered level court: the observer stands just inside the threshold, and four enclosing plan corners and both shoulder samples must be concealed by a 2.2 m or higher solid on the level floor. A 0.65 m radius clearance flood must connect the court, the entrance and both marked hide/peek positions. The two alternatives can share the first stretch of floor. The three-district survey does not certify reverse or raised witnesses.",
        "",
    ]
    total = 0
    for plan in maps:
        cov = {c["id"]: c for c in plan["studyCovers"]}
        rows += ["## " + plan["title"], ""]
        for key in ("a", "b"):
            room = plan["nodes"][key]
            rows += [
                f"### Site {key.upper()} · {room['label']}",
                "",
                f"Court {room['size'][0]} × {room['size'][1]} m. Floor datum {room['y']:+g} m. Centre {coords(room['xz'])}. The 3 m kindle disk shares its centre with the 4.5 m furniture-free apron.",
                "",
                "| Approach | Mouth and width | Hide 1 → peek | Hide 2 → peek |",
                "|---|---|---|---|",
            ]
            for e in [e for e in plan["entrances"] if e["site"] == key]:
                pockets = []
                for pos in e["pockets"]:
                    c = cov[pos["cover_id"]]
                    pockets.append(
                        f"**{c['label']}** ({c['height_m']:g} m, {pos['posture']}) {coords(pos.get('body_hide_xz', pos['hide_xz']))} → {coords(pos['peek_xz'])}"
                    )
                rows.append(
                    f"| {plan['nodes'][e['approach']]['label']} | {coords(e['mouth_xz'])} · {e['width_m']:g} m | {pockets[0]} | {pockets[1]} |"
                )
                total += 1
            rows.append("")
    if total != 27:
        raise ValueError("Expected 27 registered physical mouths")
    return "\n".join(rows)


def page(maps):
    physics = read(HERE / "physics.json")
    data = json.dumps(
        dict(maps=maps, traces=physics["traces"], rate=physics["rules"]["hz"]),
        ensure_ascii=False,
        separators=(",", ":"),
    ).replace("<", "\\u003c")
    openings = "".join(
        f"<tr><th>{o['duty'].title()} · {o['site'].upper()}</th><td>{o['baseline_s']:.2f}</td><td>{o['live_s']:.2f}</td><td>{o['fold_permitted']['live_s']:.2f}</td></tr>"
        for o in physics["openings"]
    )
    # Embed the existing environment painting at a modest gallery-derived size.
    art = (HERE / "district-banner.webp").read_bytes()
    template = (HERE / "fieldbook.html.in").read_text()
    return (
        template.replace("FIELD_STYLE", (HERE / "fieldbook.css").read_text())
        .replace(
            "FIELD_ART",
            "data:image/webp;base64," + base64.b64encode(art).decode("ascii"),
        )
        .replace("DOC_ROOT", DOC_ROOT)
        .replace("FIELD_OPENING", openings)
        .replace("STAGING_PLATE", draw_staging(maps[0], physics))
        .replace("FIELD_DATA", data)
        .replace("GROUND_ENGINE", (ATLAS / "rehearsal/engine.mjs").read_text())
        .replace("FIELD_CODE", (HERE / "fieldbook.js").read_text())
    )


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--check", action="store_true")
    args = p.parse_args()
    maps = court_maps()
    for file, content in (
        (HERE / "door-register.md", door_table(maps)),
        (
            HERE / "mandala-staging.svg",
            draw_staging(maps[0], read(HERE / "physics.json")),
        ),
        (HERE / "fieldbook.html", page(maps)),
    ):
        if args.check:
            if not file.is_file() or file.read_text() != content:
                raise SystemExit("Regenerate " + file.name)
        else:
            file.write_text(content)
    print(
        f"{len(maps)} districts, 8 sites, 27 physical entrances, 54 shelter assignments; fieldbook and registers agree."
    )


if __name__ == "__main__":
    main()
