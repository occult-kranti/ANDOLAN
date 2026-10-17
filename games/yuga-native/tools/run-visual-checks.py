#!/usr/bin/env python3
"""Run the native visual campaign's source-bound contracts after Godot import.

Both cloud setup and CI call this catalog. Strict process lifetime and report
validation come from the existing authoring runner. These tests do not render
pixels or qualify art, hardware performance, online play or a release.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import os
from pathlib import Path
import sys

PROJECT = Path(__file__).resolve().parents[1]
REPOSITORY = PROJECT.parents[1]
HELPER_PATH = PROJECT / "tools/run-authoring-checks.py"
spec = importlib.util.spec_from_file_location("visual_authoring_helper", HELPER_PATH)
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)
LIMITS = "Headless visual component, real resource and native identity contracts only; no rendered-art, continuous-motion, physical-GPU, online or release acceptance."
SUITES = (
    ("surface-finish", "godot", "tests/rama_surface_finish_cases.gd", ("--resources",)),
    ("surface-finish-adversarial", "godot", "tests/rama_finish_adversarial_cases.gd", ()),
    ("courtyard-atmosphere", "godot", "tests/hero_atmosphere_cases.gd", ()),
    ("courtyard-district", "godot", "tests/hero_district_cases.gd", ()),
    ("courtyard-environment-adversarial", "godot", "tests/hero_environment_adversarial_cases.gd", ()),
    ("ability-calligraphy", "godot", "tests/rama_ability_visual_cases.gd", ()),
    ("ability-event-adversarial", "godot", "tests/rama_effect_adversarial_cases.gd", ()),
    ("motion-polish", "godot", "tests/rama_motion_polish_cases.gd", ()),
    ("motion-adversarial", "godot", "tests/rama_motion_adversarial_cases.gd", ()),
    ("optional-character-accents", "godot", "tests/rama_character_accents_cases.gd", ("--resources",)),
    ("native-content-pins", "python", "tools/check-native-contracts.py", ()),
    ("native-contract-admission", "godot", "tests/native_contract_cases.gd", ()),
)


def sources(selected: list[tuple]) -> dict:
    # Complete runtime bytes, selected tests, historical identity fixtures and
    # runner dependencies are frozen. Imported cache contents are not sources.
    paths = {Path(__file__).resolve(), HELPER_PATH, PROJECT / "project.godot",
             PROJECT / "export_presets.cfg", *(PROJECT / item[2] for item in selected)}
    for folder in ("scripts", "shaders", "scenes", "assets", "tests/fixtures/contracts"):
        paths.update(path for path in (PROJECT / folder).rglob("*") if path.is_file())
    records = {str(path.relative_to(PROJECT)): {"bytes": path.stat().st_size,
               "sha256": helper.sha(path)} for path in sorted(paths)}
    return records


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engine", default="godot")
    parser.add_argument("--python", dest="python_engine", default=sys.executable)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--suite", action="append", choices=[item[0] for item in SUITES])
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--max-cpus", type=int, default=2)
    args = parser.parse_args()
    selected = [item for item in SUITES if not args.suite or item[0] in args.suite]
    if args.list:
        print(json.dumps({"suites": [{"id": i, "kind": k, "source": s, "arguments": a}
                         for i, k, s, a in selected], "scope": LIMITS}, indent=2))
        return 0
    if args.output is None or not math.isfinite(args.timeout) or not 0 < args.timeout <= 1800 or not 1 <= args.max_cpus <= 64:
        parser.error("A fresh --output, timeout in (0,1800] and max-cpus in [1,64] are required")
    try:
        engine = helper.executable(args.engine)
        python = helper.executable(args.python_engine)
        output = args.output.absolute()
        if output.exists() or output.is_symlink():
            raise ValueError("Output already exists; use a fresh directory")
        if output.resolve().is_relative_to(REPOSITORY):
            raise ValueError("Generated reports must be outside the checkout")
        output.mkdir(parents=True, exist_ok=False)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    for name in ("reports", "logs", "users"):
        (output / name).mkdir()
    if hasattr(os, "sched_getaffinity") and hasattr(os, "sched_setaffinity"):
        os.sched_setaffinity(0, sorted(os.sched_getaffinity(0))[:args.max_cpus])
    before = sources(selected)
    helper.write_json(output / "source-before.json", before)
    summary = {"schema": 1, "passed": False, "scope": LIMITS, "selected_suites": [item[0] for item in selected],
               "suites": [], "sources_before_sha256": helper.sha(output / "source-before.json")}
    helper.write_json(output / "summary.json", summary)
    env = os.environ.copy()
    env.update(LP_NUM_THREADS="2", PYTHONDONTWRITEBYTECODE="1")
    probe = helper.preparation_process("engine-version", [engine, "--version"], output, env, min(args.timeout, 10))
    summary["engine_probe"] = probe
    summary["engine_version"] = (output / probe["stdout"]).read_text(errors="replace").strip()
    if not probe["passed"] or not summary["engine_version"].startswith("4.6.3.stable."):
        summary["error"] = "Godot4.6.3_standard_required"
        helper.write_json(output / "summary.json", summary)
        return 1
    for suite_id, kind, source, arguments in selected:
        report = output / "reports" / (suite_id + ".json")
        user = output / "users" / suite_id
        user.mkdir()
        suite_env = env.copy()
        suite_env.update(XDG_DATA_HOME=str(user / "data"), XDG_CONFIG_HOME=str(user / "config"), XDG_CACHE_HOME=str(user / "cache"))
        if kind == "godot":
            command = [engine, "--headless", "--single-threaded-scene", "--audio-driver", "Dummy",
                       "--path", str(PROJECT), "--fixed-fps", "60", "--script", "res://" + source,
                       "--", "--report=" + str(report), *arguments]
        else:
            command = [python, str(PROJECT / source), "--report=" + str(report), *arguments]
        result = helper.execute_suite(suite_id, command, report, output, env=suite_env, timeout=args.timeout)
        # Positive resource flags prevent a synthetic-only invocation from
        # silently substituting for the two actual-resource modes in this catalog.
        if result["passed"] and suite_id in ("surface-finish", "optional-character-accents"):
            data, _ = helper.inspect_report(report)
            key = "real_maps" if suite_id == "surface-finish" else "resources"
            if data.get(key) is not True:
                result["passed"] = False
                result["problems"].append("actual_resource_mode_not_exercised")
        summary["suites"].append(result)
        helper.write_json(output / "summary.json", summary)
        print(json.dumps({"suite": suite_id, "passed": result["passed"], "checks": result.get("checks", 0), "exit_code": result["exit_code"]}), flush=True)
    after = sources(selected)
    helper.write_json(output / "source-after.json", after)
    summary["sources_after_sha256"] = helper.sha(output / "source-after.json")
    summary["checked_sources_unchanged"] = before == after
    summary["checks"] = sum(item.get("checks", 0) for item in summary["suites"])
    summary["passed"] = bool(summary["suites"]) and summary["checked_sources_unchanged"] and all(item["passed"] for item in summary["suites"])
    helper.write_json(output / "summary.json", summary)
    print(json.dumps({"passed": summary["passed"], "suites": len(selected), "checks": summary["checks"], "output": str(output), "scope": LIMITS}))
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
