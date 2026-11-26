#!/usr/bin/env python3
"""Build the portable plan drill from the atlas routes and Rust objective constants."""
import argparse
import base64
import json
import math
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
ATLAS = HERE.parent
NATIVE = ATLAS.parents[3]
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
    asset_paths = {key: NATIVE / "art" / "yagna-audio" / (key + ".flac")
                   for key in ("drone", "low-drum", "hand-drum", "reed", "expiry", "quench")}
    asset_paths["maruti-udayana"] = NATIVE / "assets" / "audio" / "hanuman-trial" / "maruti_udayana.wav"
    assets = {key: base64.b64encode(path.read_bytes()).decode("ascii") for key, path in asset_paths.items()}
    audio_json = json.dumps(assets, separators=(",", ":"))
    template = (HERE / "page.html").read_text()
    # Keep the mixer module's private helpers scoped when inlining it for file:// and srcdoc.
    exports = "{RehearsalAudio, REHEARSAL_CUE_RANGES, REHEARSAL_DEFAULT_MIX, rehearsalCueInRange}"
    audio_module = re.sub(r"^export (?=(?:const|class|function) )", "", (HERE / "audio.mjs").read_text(), flags=re.M)
    mixer = f"const {exports} = (() => {{\n{audio_module}\nreturn {exports};\n}})();"
    js = "\n".join(((HERE / "engine.mjs").read_text(), mixer, (HERE / "app.js").read_text()))
    return template.replace("<!--APP_STYLE-->", "<style>\n" + css + "</style>").replace(
        "<!--ATLAS_DATA-->", '<script type="application/json" id="atlas-data">' + payload + "</script>").replace(
        "<!--AUDIO_ASSETS-->", '<script type="application/json" id="audio-assets">' + audio_json + "</script>").replace(
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
        print("Portable rehearsal matches the four maps, Rust timings, sound assets, controls and art.")
    else:
        output.write_bytes(result)
        print(f"Wrote {output.name} ({len(result):,} bytes).")
