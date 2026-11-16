#!/usr/bin/env python3
"""Run the composed Rama packet's focused native checks with isolated settings.

No imports, exports or render jobs are started here. Import once before this
runner; freeze runtime sources while it executes. Every log/report is retained.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]
PROJECT = ROOT / "games/yuga-native"
SUITES = [
    "rama_training_journey_cases", "rama_volley_warning_cases",
    "rama_power_entry_cases", "rama_hero_feedback_cases",
    "rama_ability_cases", "rama_ability_visual_cases", "rama_motion_cases",
    "rama_practice_cases", "rama_hero_integration_cases", "rama_screen_cases",
    "rama_hud_layout_cases", "rama_hud_expiry_cases", "input_binding_cases",
    "ui_hud_reload_availability_cases", "desktop_s4_guide_scaling_cases",
    "desktop_s5_compact_hud_cases", "ui_i1_action_hud_cases",
    "sangam_district_cases", "native_field_shop_cases", "native_shop_flow_cases",
    "combat_match_metrics_cases", "native_round_journey_cases", "rama_action_audio_cases",
    "desktop_world_route_parity_cases", "ui_world_objective_cases",
    "world_scene_cases", "world_flow_cases", "world_lighting_cases", "world_presentation_cases",
]

def sources():
    files = [p for folder in ("scripts", "shaders", "scenes", "assets")
             for p in sorted((PROJECT / folder).rglob("*")) if p.is_file()]
    files += [PROJECT / "project.godot", PROJECT / "export_presets.cfg"]
    files += list((PROJECT / "tests").glob("*.gd"))
    return {str(p.relative_to(PROJECT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}

def main():
    global PROJECT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--project", type=Path, default=PROJECT)
    parser.add_argument("--engine", default="godot")
    parser.add_argument("--jobs", type=int, default=4)
    args = parser.parse_args()
    PROJECT = args.project.resolve()
    if not (PROJECT / "project.godot").is_file():
        parser.error("--project must contain the native Godot project.")
    if not args.output.is_absolute() or args.output.exists():
        parser.error("Choose a fresh absolute output directory.")
    if not 1 <= args.jobs <= 8:
        parser.error("Use 1–8 independent test workers.")
    args.output.mkdir(parents=True)
    before = sources()

    def run(name):
        folder = args.output / name
        folder.mkdir()
        env = os.environ.copy()
        for key, sub in [("XDG_DATA_HOME", "data"), ("XDG_CONFIG_HOME", "config"), ("XDG_CACHE_HOME", "cache")]:
            env[key] = str(folder / sub)
            (folder / sub).mkdir()
        command = [args.engine, "--headless", "--path", str(PROJECT),
                   "--script", f"res://tests/{name}.gd", "--", f"--report={folder / 'result.json'}"]
        start = time.monotonic()
        try:
            with (folder / "run.log").open("w") as log:
                proc = subprocess.run(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=240)
            report = json.loads((folder / "result.json").read_text())
            log_text = (folder / "run.log").read_text()
            checks = report.get("checks", report.get("cases", []))
            passed = proc.returncode == 0 and report.get("passed") is True and bool(checks) and "SCRIPT ERROR:" not in log_text and "\nERROR:" not in log_text
            row = {"suite":name, "passed":passed, "exit_code":proc.returncode, "checks":len(checks), "command":command,
                   "warnings":[line for line in log_text.splitlines() if line.startswith("WARNING:")]}
        except (subprocess.TimeoutExpired, OSError, ValueError) as exc:
            row = {"suite":name, "passed":False, "error":str(exc), "command":command}
        row["wall_seconds"] = round(time.monotonic() - start, 3)
        return row

    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        results = list(pool.map(run, SUITES))
    after = sources()
    summary = {"task":"YUGA-HERO-6R", "source_unchanged":before == after, "source_sha256":before,
               "passed":before == after and all(r["passed"] for r in results),
               "suites":results, "jobs":args.jobs,
               "scope":"Headless component/integration checks. Actual rendered input/motion, human feel and hardware remain separate."}
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({"passed":summary["passed"], "suites":len(results), "checks":sum(r.get("checks",0) for r in results),
                      "warnings":sum(len(r.get("warnings",[])) for r in results),
                      "failed":[r["suite"] for r in results if not r["passed"]], "output":str(args.output)}))
    raise SystemExit(0 if summary["passed"] else 1)

if __name__ == "__main__":
    main()
