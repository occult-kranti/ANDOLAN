#!/usr/bin/env python3
"""Read-only replay of the archived actual-world before/after reports."""
import hashlib
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent


def read(name):
    return json.loads((HERE / name).read_text())


baseline = read("baseline-r4.json")
candidate = read("candidate-r2.json")
rows = list(zip(baseline["timeline"], candidate["timeline"]))
checks = []


def check(name, passed, details=None):
    checks.append({"name": name, "passed": bool(passed), "details": details or {}})


check("Same final fixture and exactly one runtime source delta", {
    path for path in baseline["source_before"]
    if baseline["source_before"][path] != candidate["source_before"][path]
} == {"res://scripts/rama_ability_effects.gd"})
check("Same ordered observations", len(baseline["timeline"]) == len(candidate["timeline"])
      and all(a["label"] == b["label"] for a, b in rows))
check("Every complete authority event is unchanged", baseline["events"] == candidate["events"],
      {"events": len(candidate["events"])})
for field in ["army_elapsed", "kit", "vitals", "audio", "hud_note", "hud_slots"]:
    check(field + " identical at every observation", all(a[field] == b[field] for a, b in rows))
check("All reported motion state identical except native sample census", all(
    {key: value for key, value in a["motion"].items() if key != "modified_samples"}
    == {key: value for key, value in b["motion"].items() if key != "modified_samples"}
    for a, b in rows), {"excluded_field": "modified_samples",
                      "reason": "Native preroll callback census differs; no pose equivalence is inferred."})
check("All arrow positions and interpolated clocks unchanged", all(
    len(a["arrows"]) == len(b["arrows"])
    and all({key: value for key, value in x.items() if key != "visible"}
            == {key: value for key, value in y.items() if key != "visible"}
            for x, y in zip(a["arrows"], b["arrows"]))
    for a, b in rows), {"arrow_observations": sum(len(a["arrows"]) for a, _ in rows)})
for name, expected in [("baseline-r4.json", 15), ("candidate-r2.json", 17),
                       ("candidate-zero-r2.json", 17), ("effects-adversarial-r1.json", 56)]:
    report = read(name)
    check(name + " expected result retained", sum(item["passed"] for item in report["checks"]) == expected)
    if "source_before" in report:
        check(name + " stable source and import inputs", report["source_before"] == report["source_after"])
    log = HERE / name.replace(".json", ".log")
    check(name + " clean engine log", not re.search(r"(?m)^(?:SCRIPT ERROR|ERROR|WARNING):", log.read_text()))

def selected(label, report):
    return next(row for row in report["timeline"] if row["label"] == label)

early = "one authority tick after resume"
boundary = "second authority boundary before presentation advances"
result = {
    "passed": all(row["passed"] for row in checks), "checks": checks,
    "inputs": {name: hashlib.sha256((HERE / name).read_bytes()).hexdigest()
               for name in ["baseline-r4.json", "candidate-r2.json", "candidate-zero-r2.json",
                            "effects-adversarial-r1.json"]},
    "before_second_pulse": {
        variant: {"army_elapsed": selected(early, report)["army_elapsed"],
                  "arrows": selected(early, report)["arrows"],
                  "audio_played": selected(early, report)["audio"]["played"]}
        for variant, report in [("baseline", baseline), ("candidate", candidate)]},
    "same_frame_notch_boundary": {
        variant: {"before": selected(early, report)["contours"],
                  "after": selected(boundary, report)["contours"]}
        for variant, report in [("baseline", baseline), ("candidate", candidate)]},
    "scope": "Comparison of recorded headless states only; no raster, audible playback, pose or feel acceptance.",
}
print(json.dumps(result, indent=2))
raise SystemExit(0 if result["passed"] else 1)
