#!/usr/bin/env python3
"""Independent read-only package HUD and actual overview interruption audit."""
import argparse
import hashlib
import json
import struct
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--package-receipt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    root = args.capture
    run = read(root / "run.json")
    package = read(args.package_receipt)
    names = ["01-package-title-idle-a", "02-package-title-idle-b", "04-package-training", "08-package-world-live", "09-package-overview-unreleased-a", "10-package-overview-unreleased-b", "11-package-overview-resumed-release"]
    shots = {name: read(root / (name + ".json")) for name in names}
    first, second, training, live, held_a, held_b, resumed = (shots[name] for name in names)
    ap, bp, rp = (s["presentation"] for s in (held_a, held_b, resumed))
    motion_fields = ["action", "action_elapsed", "stage", "phase", "locomotion_age", "nocked", "release_count", "cancel_count", "aim_weight", "foot_locks"]
    cast_a, cast_b, cast_r = (s["kit"]["casts"][0] for s in (held_a, held_b, resumed))
    checks = {
        "completed_native_process": run["complete"] and run["verified_exit_code"] == 0 and run["cleanup_exit"] == 0,
        "immutable_package_and_instrumentation": all(run[k] for k in ["package_unchanged", "instrumentation_unchanged", "archive_unchanged", "export_manifest_unchanged", "source_unchanged"]),
        "exact_r3_archive": run["package_archive"]["sha256"] == package["package"]["sha256"],
        "exact_r3_engine_and_pck": set(run["package_sha256"].values()) == {package["package"]["engine"]["sha256"], package["package"]["pck"]["sha256"]},
        "exact_r3_source_commit": run["export_manifest"]["git"]["head"] == package["source_commit"],
        "native_route_has_no_stages": not run["authority_staging"]["enabled"] and not run["authority_staging"]["stages"],
        "all_planned_original_hashes": all(sha(root / s["file"]) == s["sha256"] for s in run["shots"]),
        "title_idle_negative_control": not first["state"]["player_active"] and not second["state"]["player_active"] and not first["presentation"]["suspended"] and not second["presentation"]["suspended"] and second["presentation"]["motion"]["locomotion_age"] > first["presentation"]["motion"]["locomotion_age"],
        "training_remapped_hud": training["hero_hud"]["health"] == 300 and training["hero_hud"]["slots"][1].startswith("J  ·  READY"),
        "live_world_unstaged_and_ready": live["state"]["player_active"] and not live["state"]["overview"] and live["kit"]["accepted_casts"] == 0 and live["hero_hud"]["notice"] == "Rama is ready",
        "held_pair_advances_render_and_physics": held_b["frame"] > held_a["frame"] and held_b["physics_frame"] - held_a["physics_frame"] >= 45,
        "overview_is_not_tree_pause": all(s["state"]["overview"] and not s["paused"] and not s["state"]["player_active"] for s in (held_a, held_b)),
        "presentation_and_kit_suspended": all(s["presentation"]["suspended"] and s["kit"]["suspended"] for s in (held_a, held_b)),
        "same_unreleased_cast": cast_a == cast_b and cast_a["cast_id"] == 1 and cast_a["ability_id"] == "piercing_dawn" and cast_a["phase"] == "windup" and not cast_a["released"] and 0 <= cast_a["age_s"] < ap["motion"]["windup"],
        "entire_kit_report_held": held_a["kit"] == held_b["kit"],
        "entire_army_report_held": held_a["army"] == held_b["army"],
        "presentation_motion_state_held": all(ap["motion"][k] == bp["motion"][k] for k in motion_fields),
        "face_report_held": ap["face"] == bp["face"],
        "secondary_report_held": ap["secondary"] == bp["secondary"],
        "held_hud_truthful": held_a["hero_hud"] == held_b["hero_hud"] and held_a["hero_hud"]["notice"] == "Practice paused" and all("—" in x and "READY" not in x for x in held_a["hero_hud"]["slots"]),
        "world_atlas_matches_player": all(s["presentation"]["atlas_position"] == s["presentation"]["player_position"] for s in (live, held_a, held_b, resumed)),
        "same_cast_generation_resumes": resumed["kit"]["generation"] == held_a["kit"]["generation"] and cast_r["cast_id"] == cast_a["cast_id"] and cast_r["released"],
        "one_authority_and_motion_release": resumed["kit"]["accepted_casts"] == 1 and resumed["kit"]["release_count"] == 1 and rp["motion"]["release_count"] == 1 and not rp["motion"]["nocked"],
        "resume_reenables_authority_and_presentation": resumed["state"]["player_active"] and not resumed["state"]["overview"] and not rp["suspended"] and not resumed["kit"]["suspended"] and resumed["kit"]["elapsed"] > held_b["kit"]["elapsed"] and resumed["army"]["elapsed"] > held_b["army"]["elapsed"],
        "resumed_hud_uses_actual_cooldown": resumed["hero_hud"]["notice"] == "Piercing Dawn · released" and ("%.1fs" % resumed["kit"]["cooldowns"]["piercing_dawn"]) in resumed["hero_hud"]["slots"][1],
    }
    originals = [{"name": n, "png_sha256": sha(root / s["file"]), "state_sha256": sha(root / (n + ".json")), "framebuffer": list(struct.unpack(">II", (root / s["file"]).read_bytes()[16:24]))} for n, s in shots.items()]
    result = {"task": "I3-04", "passed": all(checks.values()), "checks": checks, "checker_sha256": sha(Path(__file__)), "run_sha256": sha(root / "run.json"), "package_receipt_sha256": sha(args.package_receipt), "source_commit": package["source_commit"], "archive_sha256": package["package"]["sha256"], "held_interval": {"render_frames": held_b["frame"] - held_a["frame"], "physics_ticks": held_b["physics_frame"] - held_a["physics_frame"], "kit_elapsed": held_a["kit"]["elapsed"], "army_elapsed": held_a["army"]["elapsed"], "cast_age_s": cast_a["age_s"], "motion_action_elapsed_s": ap["motion"]["action_elapsed"], "face_secondary_elapsed_s": ap["face"]["elapsed"]}, "originals": originals, "scope": "Actual package native-input evidence. Modified-sample count may advance while held pose clocks stay fixed. No GPU-performance or unstaged outcome claim; pixel findings are separately reviewed."}
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"passed": result["passed"], "checks": len(checks), "failed": [k for k, v in checks.items() if not v]}))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
