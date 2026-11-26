#!/usr/bin/env python3
"""Build the portable plan drill from the atlas routes and Rust objective constants."""
import argparse
import base64
import json
import math
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ATLAS = HERE.parent
sys.path.insert(0, str(ATLAS))
import audit
from footprints import project_building
from ritual_rules import rule_constants


def route_guides(plan):
    edges, _ = audit.audit_geometry(plan)
    guides = {}
    destinations = {"a", "b", "mid"}
    for link in plan["links"]:
        if link["kind"] == "fold":
            if link.get("quarter_turns") not in (-2, -1, 1, 2) or not link.get("cue"):
                raise ValueError("A fold needs a signed heading and a local cue.")
            destinations.update((link["from"], link["to"]))
    for profile in ("dry", "all"):
        graph = audit.network([e for e in edges if profile == "all" or e.kind in audit.DRY])
        for start in plan["nodes"]:
            for end in sorted(destinations - {start}):
                seconds, path, kinds = audit.shortest(graph, start, end,
                                                      {"atk", "def", "a", "b"} - {start, end})
                if not math.isfinite(seconds):
                    continue
                steps = []
                for a, b, kind in zip(path, path[1:], kinds):
                    index = next(i for i, e in enumerate(edges)
                                 if {e.start, e.end} == {a, b} and e.kind == kind)
                    steps.append([index, edges[index].start == a])
                guides[f"{profile}:{start}:{end}"] = [round(seconds, 2), steps]
    return guides


def render():
    maps = []
    for key in audit.MAPS:
        source = json.loads((ATLAS / "maps" / f"{key}.json").read_text())
        maps.append({**source, "guides": route_guides(source), "building": project_building(source)})
    payload = json.dumps({"maps": maps, "rules": rule_constants()}, ensure_ascii=False,
                         separators=(",", ":")).replace("<", "\\u003c")
    artwork = base64.b64encode((HERE / "landmarks.webp").read_bytes()).decode("ascii")
    css = (HERE / "style.css").read_text().replace("ARTWORK_URL", "data:image/webp;base64," + artwork)
    template = (HERE / "page.html").read_text()
    js = (HERE / "engine.mjs").read_text() + "\n" + (HERE / "app.js").read_text()
    return template.replace("<!--APP_STYLE-->", "<style>\n" + css + "</style>").replace(
        "<!--ATLAS_DATA-->", '<script type="application/json" id="atlas-data">' + payload + "</script>").replace(
        "<!--APP_CODE-->", '<script type="module">\n' + js + "</script>")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--check", action="store_true")
    args = p.parse_args()
    result = render().encode("utf-8")
    output = ATLAS / "rehearsal.html"
    if args.check:
        if not output.is_file() or result != output.read_bytes():
            sys.exit("Rehearsal is stale. Run rehearsal/build.py to rebuild.")
        print("Portable rehearsal matches all four map sources, Rust timings, controls and art.")
    else:
        output.write_bytes(result)
        print(f"Wrote {output.name} ({len(result):,} bytes).")
