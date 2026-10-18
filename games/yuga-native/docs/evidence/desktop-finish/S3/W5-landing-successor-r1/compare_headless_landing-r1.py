#!/usr/bin/env python3
"""Compare fresh native callback data; no image or rendering claim."""
import gzip
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PINS = {"baseline": "8c3771a343a0538d749147393d0c407b1fb377d774a91b4cf99734e4852520f8",
        "candidate": "57d0098c3d05e976229cd5f2314d5356af85429e1128688d75e39ec5fdbb3b52"}


def main():
    reports, inputs, checks = {}, {}, []
    def check(name, passed, detail=None):
        checks.append({"name": name, "passed": bool(passed), "detail": detail})
    for role, suffix in (("baseline", "r1"), ("candidate", "r3")):
        path = ROOT / f"{role}-landing-120-{suffix}" / "report.json.gz"
        compressed = path.read_bytes()
        raw = gzip.decompress(compressed)
        report = json.loads(raw)
        reports[role] = report
        inputs[role] = {"path": str(path.relative_to(ROOT)), "sha256": hashlib.sha256(compressed).hexdigest(),
                        "uncompressed_sha256": hashlib.sha256(raw).hexdigest()}
        check(role + " complete source-stable callback tape", report["complete"]
              and all(row["passed"] for row in report["checks"]) and report["source_unchanged"]
              and report["source_sha256"] == report["source_after_sha256"]
              and report["source_sha256"]["res://scripts/rama_motion.gd"] == PINS[role])
        shots = report["shots"]
        check(role + " actual 120Hz physics and forty consecutive callbacks", report["physics_hz"] == 120
              and len(shots) == 40 and all(y["final_modifier_body"]["physics_frame"]
              - x["final_modifier_body"]["physics_frame"] == 1 for x, y in zip(shots, shots[1:])))
    a, b = reports["baseline"], reports["candidate"]
    delta = sorted(k for k in a["source_sha256"].keys() | b["source_sha256"].keys()
                   if a["source_sha256"].get(k) != b["source_sha256"].get(k))
    check("only motion and its declared marker differ", delta == ["res://.graphics-six-snapshot.json", "res://scripts/rama_motion.gd"], delta)
    for field in ("case", "godot", "adapter", "renderer", "camera_contract", "bone_names", "sole_selection",
                  "sequence_controls", "ability_events", "time_controls"):
        check("matched " + field, a[field] == b[field])
    pairs = list(zip(a["shots"], b["shots"]))
    for field in ("camera", "viewport", "secondary", "action"):
        check("matched every " + field, all(x[field] == y[field] for x, y in pairs))
    for field in ("player_transform", "rig_transform", "velocity", "on_floor", "capsules", "kit_report", "army_elapsed",
                  "transition_age", "transition_duration", "foot_targets_rig", "jump_count", "traversal_mode", "player_active",
                  "physics_frame", "motion"):
        check("matched every body " + field, all(x["final_modifier_body"][field] == y["final_modifier_body"][field] for x, y in pairs))
    nonleg = [i for i, name in enumerate(a["bone_names"]) if not name.startswith(("upperleg", "lowerleg", "foot.", "toe"))]
    check("all nonleg poses identical", all(x["rendered_pose_globals"][i] == y["rendered_pose_globals"][i] for x, y in pairs for i in nonleg))
    metrics = {}
    for role, report in reports.items():
        contacts, steps = [], []
        for index, shot in enumerate(report["shots"]):
            for side, contact in shot["sole_contacts"]["sides"].items():
                contacts.append({"frame": index, "physics": shot["final_modifier_body"]["physics_frame"], "side": side,
                                 "grounded": shot["final_modifier_body"]["on_floor"], "locked": contact["locked"],
                                 "minimum_signed_m": contact["minimum_signed_m"]})
                if index:
                    previous = report["shots"][index-1]["sole_projection"]["sides"][side]["ankle_world"]
                    current = shot["sole_projection"]["sides"][side]["ankle_world"]
                    steps.append({"from": index-1, "to": index, "side": side,
                                  "world_step_m": math.dist(previous, current), "delta_xyz_m": [y-x for x, y in zip(previous, current)]})
        metrics[role] = {"all_minimum_m": min(x["minimum_signed_m"] for x in contacts),
                         "grounded_minimum_m": min(x["minimum_signed_m"] for x in contacts if x["grounded"]),
                         "locked_side_samples": sum(x["locked"] for x in contacts),
                         "actual_contact_side_samples": sum(x["grounded"] and -.005 <= x["minimum_signed_m"] <= .005 for x in contacts),
                         "peak_step": max(steps, key=lambda x: x["world_step_m"]), "contacts": contacts, "steps": steps}
    result = {"passed": all(x["passed"] for x in checks), "count": len(checks), "checks": checks, "metrics": metrics, "inputs": inputs,
              "scope": "Fresh native headless 8c377 versus isolated57d0098c comparison. No drawable frames, raster, initial-visibility or smoothness acceptance. Render counters are zero in headless mode; actual physics counters are checked separately. Prior actual render frame/counter identities are not transferred."}
    (ROOT / "headless-landing-comparison.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"passed": result["passed"], "count": result["count"], "failures": [x["name"] for x in checks if not x["passed"]]}))
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
