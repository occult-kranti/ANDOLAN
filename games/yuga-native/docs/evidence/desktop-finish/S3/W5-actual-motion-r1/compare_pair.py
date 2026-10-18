#!/usr/bin/env python3
"""Verify actual matched controls and retain contact/step measurements, not an art score."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct

PINS = {"baseline": "119db2e65a40c148725813137340bc109f057d98ea82ef777ab7735c999c661c",
        "candidate": "8c3771a343a0538d749147393d0c407b1fb377d774a91b4cf99734e4852520f8"}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--baseline", type=Path, required=True)
    ap.add_argument("--candidate", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    if args.output.exists():
        ap.error("Fresh output required")
    directories = {role: getattr(args, role) for role in PINS}
    reports = {role: json.loads((path / "capture.json").read_text()) for role, path in directories.items()}
    runs = {role: json.loads((path.with_name(path.name + "-logs") / "run.json").read_text())
            for role, path in directories.items()}
    checks = []

    def check(name, passed, details=None):
        checks.append({"name": name, "passed": bool(passed), "details": details or {}})

    a, b = reports["baseline"], reports["candidate"]
    count = 40 if a["case"] == "landing120" else 120
    physics_hz, capture_hz = (120, 120) if count == 40 else (60, 30)
    for role, report in reports.items():
        shots = report["shots"]
        check(role + " complete native capture", report["complete"] and runs[role]["complete"]
              and len(shots) == count and all(row["passed"] for row in report["checks"]))
        check(role + " exact motion and stable source", report["source_unchanged"]
              and report["source_sha256"] == report["source_after_sha256"]
              and report["source_sha256"]["res://scripts/rama_motion.gd"] == PINS[role])
        check(role + " actual physics and every draw consecutive", report["physics_hz"] == physics_hz
              and report["fixed_capture_hz"] == capture_hz
              and all(y["render_frame"] - x["render_frame"] == 1
                      and y["final_modifier_body"]["physics_frame"] - x["final_modifier_body"]["physics_frame"]
                      == physics_hz // capture_hz for x, y in zip(shots, shots[1:])))
        pngs = sorted(directories[role].glob("*.png"))
        image_matches = len(pngs) == count
        for index, shot in enumerate(shots):
            image = directories[role] / shot["file"]
            raw_header = image.read_bytes()[:24]
            image_matches &= shot["file"] == "frame-%03d.png" % index and sha(image) == shot["sha256"]
            image_matches &= raw_header[:8] == b"\x89PNG\r\n\x1a\n" and struct.unpack(">II", raw_header[16:24]) == (1280, 960)
        check(role + " original full-size PNG identities", image_matches, {"originals": len(pngs)})
    check("Matched engine, adapter and private seed inputs", a["godot"] == b["godot"]
          and a["adapter"] == b["adapter"] and a["renderer"] == b["renderer"] == "forward_plus"
          and all(runs["baseline"][field] == runs["candidate"][field] for field in
                  ["engine_sha256", "render_inputs_sha256", "private_godot_seed_sha256",
                   "private_mesa_seed_sha256", "affinity", "runner_affinity", "library_thread_env"]))
    delta = sorted(key for key in a["source_sha256"].keys() | b["source_sha256"].keys()
                   if a["source_sha256"].get(key) != b["source_sha256"].get(key))
    check("Only declared motion and its snapshot marker differ", delta ==
          ["res://.graphics-six-snapshot.json", "res://scripts/rama_motion.gd"], {"differences": delta})
    for field in ["case", "camera_contract", "bone_names", "sole_selection", "sequence_controls", "ability_events", "time_controls"]:
        check("Matched " + field, a[field] == b[field])
    pairs = list(zip(a["shots"], b["shots"]))
    for field in ["camera", "light", "render_settings", "face", "skin_materials", "secondary", "lod", "viewport", "action"]:
        check("Matched every " + field, all(x[field] == y[field] for x, y in pairs))
    for field in ["player_transform", "rig_transform", "velocity", "on_floor", "capsules", "kit_report",
                  "army_elapsed", "transition_age", "transition_duration", "foot_targets_rig", "jump_count",
                  "traversal_mode", "player_active", "physics_frame"]:
        check("Matched every body " + field, all(x["final_modifier_body"][field] == y["final_modifier_body"][field]
                                                for x, y in pairs))
    nonleg = [i for i, name in enumerate(a["bone_names"])
              if not name.startswith(("upperleg", "lowerleg", "foot.", "toe"))]
    check("All nonleg global transforms identical", all(x["rendered_pose_globals"][i] == y["rendered_pose_globals"][i]
                                                        for x, y in pairs for i in nonleg), {"bones": len(nonleg)})
    metrics = {}
    for role, report in reports.items():
        shots = report["shots"]
        steps = []
        contacts = []
        for index, shot in enumerate(shots):
            for side, contact in shot["sole_contacts"]["sides"].items():
                contacts.append({"frame": index, "physics": shot["final_modifier_body"]["physics_frame"],
                                 "side": side, "grounded": shot["final_modifier_body"]["on_floor"],
                                 "locked": contact["locked"], "minimum_signed_m": contact["minimum_signed_m"],
                                 "vertices_below_minus5mm": contact["vertices_below_minus5mm"],
                                 "minimum_vertex": contact["minimum_vertex"]})
                if not index:
                    continue
                previous = shots[index - 1]["sole_projection"]["sides"][side]
                current = shot["sole_projection"]["sides"][side]
                steps.append({"from_frame": index - 1, "to_frame": index, "side": side,
                              "physics_from": shots[index - 1]["final_modifier_body"]["physics_frame"],
                              "physics_to": shot["final_modifier_body"]["physics_frame"],
                              "world_step_m": math.dist(previous["ankle_world"], current["ankle_world"]),
                              "world_delta_m": [y - x for x, y in zip(previous["ankle_world"], current["ankle_world"])],
                              "screen_step_px": math.dist(previous["ankle_px"], current["ankle_px"]),
                              "screen_delta_px": [y - x for x, y in zip(previous["ankle_px"], current["ankle_px"])]})
        metrics[role] = {"peak_ankle_step": max(steps, key=lambda row: row["world_step_m"]),
                         "lowest_grounded_sample": min((row for row in contacts if row["grounded"]),
                                                       key=lambda row: row["minimum_signed_m"]),
                         "grounded_side_samples_below_minus5mm": sum(row["grounded"] and row["minimum_signed_m"] < -.005
                                                                     for row in contacts),
                         "contacts": contacts, "ankle_steps": steps}
    result = {"passed": all(row["passed"] for row in checks), "checks": checks, "case": a["case"],
              "inputs": {role: {"capture_sha256": sha(path / "capture.json"), "run_sha256": sha(path.with_name(path.name + "-logs") / "run.json")}
                         for role, path in directories.items()}, "metrics": metrics,
              "scope": "Actual original-image identities and whole-tape control comparison. Measurements retain contact/snap tradeoffs; no numerical threshold grants visual acceptance. foot_targets_rig is the inherited field name for world-space fixed anchors. Native S3 25/27 failures remain independent evidence."}
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"passed": result["passed"], "checks": len(checks), "case": a["case"],
                      "failed": [row["name"] for row in checks if not row["passed"]]}))
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
