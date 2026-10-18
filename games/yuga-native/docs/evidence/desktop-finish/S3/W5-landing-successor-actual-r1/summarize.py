#!/usr/bin/env python3
"""Derive compact measurements from the complete archived paired recordings."""
import gzip
import hashlib
import json
from pathlib import Path


def load_capture(path):
    return json.loads(gzip.decompress((path / "capture.json.gz").read_bytes()))


def main():
    root = Path(__file__).resolve().parent
    result = {"scope": "Recorded 8c377 baseline versus 5023 successor; measurements do not grant general smoothness or player-feel acceptance.", "cases": {}}
    for case in ("landing120", "full"):
        report_path = root / (case + "-archive-comparison.json")
        comparison = json.loads(report_path.read_text())
        paths = {"baseline": root.parent / "W5-actual-motion-r1" / case / "candidate", "candidate": root / case}
        captures = {role: load_capture(path) for role, path in paths.items()}
        item = {"comparison_sha256": hashlib.sha256(report_path.read_bytes()).hexdigest(), "controls_passed": comparison["passed"], "control_predicates": len(comparison["checks"]), "roles": {}}
        for role, metrics in comparison["metrics"].items():
            contacts = metrics["contacts"]
            shots = captures[role]["shots"]
            contact_band = sum(s["final_modifier_body"]["on_floor"] and c["ground_ray"]["hit"] and abs(c["minimum_signed_m"]) <= .005 for s in shots for c in s["sole_contacts"]["sides"].values())
            item["roles"][role] = {
                "frames": len(shots),
                "physics_hz": captures[role]["physics_hz"],
                "capture_hz": captures[role]["fixed_capture_hz"],
                "first_physics": shots[0]["final_modifier_body"]["physics_frame"],
                "last_physics": shots[-1]["final_modifier_body"]["physics_frame"],
                "all_sample_minimum_m": min(c["minimum_signed_m"] for c in contacts),
                "grounded_minimum_m": metrics["lowest_grounded_sample"]["minimum_signed_m"],
                "grounded_side_samples": sum(c["grounded"] for c in contacts),
                "boolean_locked_side_samples": sum(c["locked"] for c in contacts),
                "grounded_ray_hit_minimum_within_5mm_side_samples": contact_band,
                "grounded_side_samples_below_minus5mm": metrics["grounded_side_samples_below_minus5mm"],
                "peak_ankle_step": metrics["peak_ankle_step"],
                "first_grounded_frame": next(i for i, s in enumerate(shots) if s["final_modifier_body"]["on_floor"]),
            }
            if case == "landing120":
                item["roles"][role]["first_ground_right_step"] = next(s for s in metrics["ankle_steps"] if s["from_frame"] == 7 and s["to_frame"] == 8 and s["side"] == "R")
        item["frames_with_any_global_pose_difference"] = [i for i, (a, b) in enumerate(zip(captures["baseline"]["shots"], captures["candidate"]["shots"])) if a["rendered_pose_globals"] != b["rendered_pose_globals"]]
        item["contact_definition"] = "The ±5mm band describes minimum skinned sole distance to an actual ground-ray plane while the body is grounded. It is separate from boolean foot locks; neither alone proves physical planted support or absence of drift."
        result["cases"][case] = item
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
