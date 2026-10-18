#!/usr/bin/env python3
"""Actual two-process title settings/remap persistence, with isolated user data."""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time

PROJECT = Path(__file__).resolve().parents[1]
TEST = PROJECT / "tests/desktop_d05_preferences_cases.gd"
RUNNER = PROJECT / "tools/run-visual-checks.py"
spec = importlib.util.spec_from_file_location("catalog_sources", RUNNER)
catalog = importlib.util.module_from_spec(spec)
spec.loader.exec_module(catalog)


def write(path, data):
    path.write_text(json.dumps(data, indent=2) + "\n")


def pins():
    result = catalog.sources([])
    for path in [TEST, Path(__file__)]:
        result[str(path.relative_to(PROJECT))] = {"bytes": path.stat().st_size,
                                                "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engine", default="godot")
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    engine = shutil.which(args.engine)
    if not engine: parser.error("Engine executable missing")
    report = args.report.absolute()
    folder = report.with_name(report.stem + "-processes")
    if report.exists() or folder.exists(): parser.error("Use a fresh report and process directory")
    report.parent.mkdir(parents=True, exist_ok=True)
    folder.mkdir()
    env = os.environ.copy()
    env.update(XDG_DATA_HOME=str(folder / "data"), XDG_CONFIG_HOME=str(folder / "config"),
               XDG_CACHE_HOME=str(folder / "cache"), GODOT_SILENCE_ROOT_WARNING="1",
               LP_NUM_THREADS="1", OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1")
    before = pins()
    write(folder / "source-before.json", before)
    version = subprocess.check_output([engine, "--version"], text=True, timeout=10).strip()
    if not version.startswith("4.6.3.stable."): parser.error("Requires Godot 4.6.3 standard")
    rows, phases, checks = [], {}, []
    for phase in ["write", "read"]:
        phase_report = folder / (phase + ".json")
        command = [engine, "--headless", "--single-threaded-scene", "--audio-driver", "Dummy",
                   "--path", str(PROJECT), "--script", "res://tests/desktop_d05_preferences_cases.gd",
                   "--", "--desktop-prefs-fixture", "--phase=" + phase, "--report=" + str(phase_report)]
        start = time.monotonic()
        try:
            result = subprocess.run(command, cwd=PROJECT, env=env, capture_output=True, text=True, timeout=45)
            code, stdout, stderr = result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired as error:
            code = None
            stdout = error.stdout or b""
            stderr = error.stderr or b""
            if isinstance(stdout, bytes): stdout = stdout.decode(errors="replace")
            if isinstance(stderr, bytes): stderr = stderr.decode(errors="replace")
        (folder / (phase + ".stdout.log")).write_text(stdout)
        (folder / (phase + ".stderr.log")).write_text(stderr)
        diagnostics = re.findall(r"(?im)^.*(?:SCRIPT ERROR|ERROR:|WARNING:|ObjectDB instances leaked).*$", stdout + stderr)
        data = json.loads(phase_report.read_text()) if phase_report.is_file() else {}
        phases[phase] = data
        rows.append({"phase": phase, "command": command, "exit_code": code,
                     "elapsed_seconds": time.monotonic() - start, "diagnostics": diagnostics})
        checks.extend(dict(check, name=phase + ": " + check["name"]) for check in data.get("checks", []))
        checks.append({"name": phase + " exits clean with an actual assertion report",
                       "passed": code == 0 and data.get("passed") is True and bool(data.get("checks")) and not diagnostics})
        if code != 0: break
    after = pins()
    write(folder / "source-after.json", after)
    first, second = phases.get("write", {}), phases.get("read", {})
    for name, passed in [
        ("The two runs are distinct real processes", bool(first.get("process_id")) and bool(second.get("process_id")) and first["process_id"] != second["process_id"]),
        ("The second process reuses only the same isolated user directory", bool(first.get("user_directory")) and first.get("user_directory") == second.get("user_directory") and str(folder) in first.get("user_directory", "")),
        ("The persisted file is exact after fresh-process reload", bool(first.get("settings_sha256")) and first.get("settings_sha256") == second.get("settings_sha256")),
        ("All runtime and fixture sources remain exact", before == after),
    ]: checks.append({"name": name, "passed": bool(passed)})
    summary = {"passed": all(row["passed"] for row in checks), "count": len(checks), "checks": checks,
               "processes": rows, "engine": {"path": engine, "version": version, "sha256": hashlib.sha256(Path(engine).read_bytes()).hexdigest()},
               "source_files": len(before), "source_manifest_sha256": hashlib.sha256((folder / "source-before.json").read_bytes()).hexdigest(),
               "scope": "Separate headless processes, actual title callbacks and GUI events with isolated saves; no OS input, renderer, hardware or package acceptance."}
    write(report, summary)
    print(json.dumps({"passed": summary["passed"], "count": len(checks), "failures": [row for row in checks if not row["passed"]]}))
    return 0 if summary["passed"] else 1


if __name__ == "__main__": raise SystemExit(main())
