#!/usr/bin/env python3
"""Read-only independent audit of the explicitly staged package HUD fixtures."""
import argparse
import hashlib
import json
from pathlib import Path


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--capture", type=Path, required=True)
    parser.add_argument("--package-receipt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists(), "Preserve previous receipts."
    root = args.capture
    run = read(root / "run.json")
    package = read(args.package_receipt)
    history = read(root / "stage-history.json")["stages"]
    stages = {s["action"]: s for s in history}
    shots = run["shots"]
    lane, held, contested, defeat, respawn, sun, moon, draw, restart = shots
    expected_actions = ["lane", "relay-held", "relay-contested", "defeat", "respawn", "outcome-sun", "outcome-moon", "outcome-draw", "release"]
    held_site = stages["relay-held"]["after"]["relays"]["sites"][1]
    contested_site = stages["relay-contested"]["after"]["relays"]["sites"][1]
    terminal = [("sun", sun, {"sun": 100, "moon": 0}, "Sun core victory"), ("moon", moon, {"sun": 0, "moon": 100}, "Moon core victory"), ("draw", draw, {"sun": 0, "moon": 0}, "Draw · both cores destroyed")]
    return_events = [e for e in run["events"] if e.get("key") == "Return" and e["before"].get("focus_text") == "Restart lane practice"]
    checks = {
        "completed_actual_package_process": run["complete"] and run["verified_exit_code"] == 0 and run["cleanup_exit"] == 0,
        "immutable_package_and_instrumentation": all(run[k] for k in ["package_unchanged", "instrumentation_unchanged", "archive_unchanged", "export_manifest_unchanged", "source_unchanged"]),
        "exact_r3_archive_source_engine_pck": run["package_archive"]["sha256"] == package["package"]["sha256"] and run["export_manifest"]["git"]["head"] == package["source_commit"] and set(run["package_sha256"].values()) == {package["package"]["engine"]["sha256"], package["package"]["pck"]["sha256"]},
        "nine_explicit_stages_and_originals": run["authority_staging"]["enabled"] and [s["action"] for s in history] == expected_actions and len(shots) == 9 and all(s["passed"] and "STAGED" in s["scope"] for s in history),
        "history_matches_execution_receipt": history == run["authority_staging"]["stages"],
        "all_eighteen_originals_hash_exact": len(run["automatic_shots"]) == 9 and all(sha(root / s["file"]) == s["sha256"] for s in shots + run["automatic_shots"]),
        "shot_sidecars_equal_recorded_state": all(read(root / (Path(s["file"]).stem + ".json")) == s for s in shots),
        "fixed_external_fixture": sha(root / "authority_stage.gd") == "0ad1f073701fd2815253e68eebfa1478f06432660717dc8659baf5479cc891e7" and all(s["fixture_sha256"] == sha(root / "authority_stage.gd") for s in history),
        "normal_presentation_refresh_preserves_authority": all(s["presentation_refresh"]["delta"] == .13 and all(s["presentation_refresh"][k] for k in ["army_unchanged", "relays_unchanged", "atlas_matches_player", "location_matches_player"]) for s in history[:-1]),
        "all_sampled_atlas_positions_match_player": all(s["presentation"]["atlas_position"] == s["presentation"]["player_position"] for s in shots),
        "lane_uses_manifest_lane_and_actual_population": stages["lane"]["manifest_lane_id"] == 1 and lane["world"]["lane_label"] == "Temple avenue · 10 troops · Wave 1" and lane["army"]["alive_by_lane"][1] == 10 and lane["army"]["waves"] == 1,
        "held_relay_has_actual_sun_ownership": held_site["owner"] == "sun" and not held_site["contested"] and stages["relay-held"]["rule_inputs"]["held_steps"] == 37 and stages["relay-held"]["rule_inputs"]["held_delta"] == .25,
        "held_hint_matches_supply_clock": held_site["supply_clock"] == 1.25 and "next supply in 3.8s" in held["world"]["relay_hint"] and "+3 arrows / +6 troop health" in held["world"]["relay_hint"],
        "contested_has_both_teams_and_no_supply_countdown": contested_site["contested"] and contested_site["contributors"] == {"sun": 1, "moon": 1} and contested_site["supply_clock"] == 0 and "Contested" in contested["world"]["relay_hint"] and "next supply" not in contested["world"]["relay_hint"],
        "defeat_uses_accepted_damage": stages["defeat"]["damage"]["accepted"] and stages["defeat"]["damage"]["damage_applied"] == 300 and not stages["defeat"]["after"]["vitals"]["alive"],
        "defeat_hud_disables_all_slots": defeat["hero_hud"]["health"] == 0 and defeat["hero_hud"]["notice"] == "RETURNING IN 3.0s" and all("—" in x and "READY" not in x for x in defeat["hero_hud"]["slots"]),
        "respawn_uses_real_simulation_steps": stages["respawn"]["rule_inputs"] == {"delta": .05, "steps": 60} and stages["respawn"]["after"]["vitals"]["alive"] and stages["respawn"]["after"]["player_active"],
        "respawn_hud_location_and_atlas_agree": respawn["hero_hud"]["health"] == 300 and respawn["hero_hud"]["notice"] == "Returned to the arrival court" and stages["respawn"]["presentation_refresh"]["location"] == "Surya arrival court" and respawn["presentation"]["player_position"][2] == -112,
        "terminal_inputs_emit_exact_winners": all(stages["outcome-" + winner]["rule_inputs"] == {"cores": cores, "delta": .05} and stages["outcome-" + winner]["signals"] == [winner] and shot["army"]["winner"] == winner and shot["army"]["cores"] == cores for winner, shot, cores, heading in terminal),
        "terminal_panels_match_authority": all(shot["world"]["outcome_visible"] and shot["world"]["outcome_heading"] == heading and heading in shot["world"]["objective_label"] and ("Sun %d / Moon %d" % (cores["sun"], cores["moon"])) in shot["world"]["outcome_detail"] for winner, shot, cores, heading in terminal),
        "terminal_authority_and_slots_suspended": all(shot["paused"] and not shot["state"]["player_active"] and shot["kit"]["suspended"] and "stopped" in shot["world"]["relay_hint"] and all("—" in x for x in shot["hero_hud"]["slots"]) for winner, shot, cores, heading in terminal),
        "terminal_refresh_does_not_change_winner": all(stages["outcome-" + winner]["presentation_preserves_authority"] for winner, shot, cores, heading in terminal),
        "three_native_return_events_target_restart": len(return_events) == 3 and [e["before"]["army"]["winner"] for e in return_events] == ["sun", "moon", "draw"] and all(e["before"]["focus_text"] == "Restart lane practice" for e in return_events),
        "restart_resets_each_outcome_before_next_fixture": all(stages[action]["before"]["army"]["cores"] == {"sun": 100, "moon": 100} and stages[action]["before"]["army"]["winner"] == "" and not stages[action]["before"]["outcome_visible"] and not stages[action]["before"]["tree_paused"] for action in ["outcome-moon", "outcome-draw", "release"]),
        "release_restores_original_processing_flags": stages["release"]["after"]["processing"] == stages["lane"]["before"]["processing"] and not stages["release"]["after"]["simulation_hold"],
        "final_native_restart_has_truthful_ready_hud": not restart["world"]["outcome_visible"] and not restart["paused"] and restart["state"]["player_active"] and restart["army"]["winner"] == "" and restart["army"]["cores"] == {"sun": 100, "moon": 100} and restart["hero_hud"]["notice"] == "Rama is ready" and restart["world"]["objective_label"] == "Escort Sun troops to the Moon core.",
        "no_staged_recovery": not (root / "native-recovery.json").exists() and not (root / "coordinate-recovery-analysis.json").exists(),
        "clean_engine_log": not any(x in (root / "godot.log").read_text() for x in ["ERROR:", "SCRIPT ERROR:", "WARNING:"]),
    }
    receipt = {"task": "I3-04", "passed": all(checks.values()), "checks": checks, "checker_sha256": sha(Path(__file__)), "source_commit": package["source_commit"], "package_receipt_sha256": sha(args.package_receipt), "run_sha256": sha(root / "run.json"), "history_sha256": sha(root / "stage-history.json"), "fixture_sha256": sha(root / "authority_stage.gd"), "scope": "Explicitly staged authority inputs, held simulation and normal presentation refresh in the actual immutable Linux package. Native Return restarts after each terminal fixture. These are not naturally achieved gameplay wins, death or respawn.", "manual_originals": len(shots), "automatic_originals": len(run["automatic_shots"])}
    args.output.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"passed": receipt["passed"], "checks": len(checks), "failed": [k for k, v in checks.items() if not v]}))
    return 0 if receipt["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
