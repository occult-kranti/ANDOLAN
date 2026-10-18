#!/usr/bin/env python3
"""Independently validate final UI original-frame receipts against their freeze.

This checks evidence identity and captured state. Pixel readability requires the
separate manual original-image review; staged authority is never called play.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def at_path(value, path):
    for key in path.split("."):
        if not isinstance(value, dict) or key not in value:
            return None
        value = value[key]
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--freeze", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    capture, freeze = args.capture.resolve(), args.freeze.resolve()
    run = json.loads((capture / "run.json").read_text())
    receipt = json.loads((freeze / "ui-source-freeze.json").read_text())
    checks, originals = [], []

    def check(name, passed, details=None):
        row = {"name": name, "passed": bool(passed)}
        if details is not None:
            row["details"] = details
        checks.append(row)

    check("Native capture completed with stable source", run.get("complete") is True and run.get("source_unchanged") is True)
    planned = [step for step in run["plan"] if "capture" in step]
    shots = run.get("shots", [])
    check("Every planned original exists exactly once", len(shots) == len(planned) and
          {s["file"] for s in shots} == {s["capture"] + ".png" for s in planned} and
          len({s["file"] for s in shots}) == len(shots), {"planned": len(planned), "actual": len(shots)})
    source_pins = run["source_sha256"]
    differences = [name for name, sha in source_pins.items()
                   if receipt["source_sha256"].get(name) != sha or not (freeze / name).is_file()
                   or digest(freeze / name) != sha]
    check("Captured runtime pins match the exact frozen source", not differences, {"files": len(source_pins), "differences": differences})
    check("All native input receipts identify an owned window", bool(run.get("events")) and
          all(type(event.get("window_id")) is int and event["window_id"] > 0 for event in run["events"]),
          {"event_records": len(run.get("events", []))})
    expected_exits = [step["expect_exit"] for step in run["plan"] if "expect_exit" in step]
    if expected_exits:
        check("Native Quit reached the planned process exit", len(expected_exits) == 1 and
              type(run.get("verified_exit_code")) is int and run["verified_exit_code"] == expected_exits[0])
    for step in planned:
        name = step["capture"]
        shot = json.loads((capture / (name + ".json")).read_text())
        png = capture / shot["file"]
        data = png.read_bytes()
        dimensions = list(struct.unpack(">II", data[16:24])) if data[:8] == b"\x89PNG\r\n\x1a\n" and len(data) >= 24 else []
        recorded = next((s for s in shots if s["file"] == shot["file"]), None)
        check(name + " original hash and receipt agree", shot.get("png_status") == 0 and digest(png) == shot["sha256"] and recorded == shot and len(dimensions) == 2 and min(dimensions) > 0)
        mismatches = {key: {"expected": value, "captured": at_path(shot, key)}
                      for key, value in step.get("expect", {}).items() if at_path(shot, key) != value}
        check(name + " expected state still holds in the captured frame", not mismatches, mismatches)
        originals.append({"file": shot["file"], "sha256": shot["sha256"], "pixels": dimensions,
                          "frame": shot["frame"], "focus": shot.get("focus", ""),
                          "window_focused": shot.get("window_focused"),
                          "authority_staging": shot.get("authority_staging", {})})
    automatic = run.get("automatic_shots", [])
    for recorded in automatic:
        png = capture / recorded["file"]
        shot = json.loads(png.with_suffix(".json").read_text())
        data = png.read_bytes()
        dimensions = list(struct.unpack(">II", data[16:24])) if data[:8] == b"\x89PNG\r\n\x1a\n" and len(data) >= 24 else []
        check(recorded["file"] + " automatic original hash and receipt agree",
              shot == recorded and shot.get("png_status") == 0 and digest(png) == shot["sha256"] and
              len(dimensions) == 2 and min(dimensions) > 0)
        originals.append({"file": shot["file"], "sha256": shot["sha256"], "pixels": dimensions,
                          "frame": shot["frame"], "automatic": True,
                          "actual_transition": shot.get("transition", {}),
                          "authority_staging": shot.get("authority_staging", {})})
    check("Original frame inventory has no unrecorded or duplicated PNGs",
          len({shot["file"] for shot in originals}) == len(originals) and
          {path.name for path in capture.glob("*.png")} == {shot["file"] for shot in originals})
    stages = run.get("authority_staging", {}).get("stages", [])
    planned_stages = [step["stage"] for step in run["plan"] if "stage" in step]
    check("Authority fixtures are explicit, successful and separate from native input", len(stages) == len(planned_stages) and
          [stage.get("action") for stage in stages] == planned_stages and
          all(stage.get("passed") is True and str(stage.get("scope", "")).startswith("STAGED AUTHORITY:") for stage in stages),
          {"staged_actions": planned_stages})
    engine_log = (capture / "godot.log").read_text()
    errors = re.findall(r"^\s*(?:(?:SCRIPT )?ERROR:|.*ObjectDB instances leaked).*", engine_log, re.M)
    check("Capture engine has no errors or leaked-object diagnostics", not errors, errors)
    report = {"passed": all(row["passed"] for row in checks), "count": len(checks), "checks": checks,
              "originals": originals, "run_sha256": digest(capture / "run.json"),
              "freeze_receipt_sha256": digest(freeze / "ui-source-freeze.json"),
              "validator_sha256": digest(Path(__file__)),
              "scope": "Independent original-frame/source/state identity validation. Native navigation and explicit staged authority are distinct. Manual pixel review, OS DPI, hardware FPS, online play and packaging remain separate."}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"passed": report["passed"], "checks": report["count"], "originals": len(originals)}))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
