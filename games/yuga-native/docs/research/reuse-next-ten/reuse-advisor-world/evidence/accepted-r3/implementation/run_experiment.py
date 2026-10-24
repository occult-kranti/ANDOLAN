#!/usr/bin/env python3
"""Capture actual Rama events and inspect them; preserve fresh bounded evidence."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--engine", default="godot")
    args = parser.parse_args()
    if not args.output.is_absolute():
        raise SystemExit("use a fresh absolute output directory")
    scripts = Path(__file__).resolve().parent
    native = scripts.parents[4]
    repository = native.parents[1]
    resolved = shutil.which(args.engine)
    if not resolved:
        raise SystemExit("Godot is unavailable; no download attempted")
    engine = Path(resolved).resolve()
    args.output.mkdir(parents=True, exist_ok=False)
    implementation = args.output / "implementation"
    implementation.mkdir()
    files = ["run_experiment.py", "capture_owned_events.gd", "event_window.py",
             "inspect_trace.py", "check_event_window.py"]
    for name in files:
        shutil.copy2(scripts / name, implementation / name)
    receipt = {
        "schema": 1, "source_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=repository, text=True).strip(),
        "scope": "Headless original Kit/Army event capture and offline playback inspection only",
        "engine_path": str(engine), "engine_sha256": sha(engine),
        "implementation_sha256": {name: sha(scripts / name) for name in files},
        "commands": [],
    }
    trace = str(args.output / "actual-events.json")
    commands = [
        ("capture", [str(engine), "--headless", "--path", str(native), "--script",
                     "res://docs/research/reuse-next-ten/reuse-advisor-world/experiment/capture_owned_events.gd",
                     "--", "--output=" + trace]),
        ("check", [sys.executable, str(scripts / "check_event_window.py"),
                   "--trace", trace, "--output", str(args.output / "checks.json")]),
    ]
    for hz in [30, 60, 120]:
        commands.append((f"inspect-{hz}hz", [sys.executable, str(scripts / "inspect_trace.py"),
                         "--trace", trace, "--hz", str(hz), "--output",
                         str(args.output / f"inspection-{hz}hz.json")]))
    commands.append(("inspect-hitch", [sys.executable, str(scripts / "inspect_trace.py"),
                     "--trace", trace, "--hz", "60", "--mixed-hitch", "--output",
                     str(args.output / "inspection-hitch.json")]))
    for label, argv in commands:
        start = time.monotonic()
        try:
            result = subprocess.run(argv, cwd=repository, stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT, timeout=45)
            status, output = result.returncode, result.stdout
        except subprocess.TimeoutExpired as error:
            status, output = 124, (error.stdout or b"") + b"\n45-second command timeout\n"
        log = args.output / f"{label}.log"
        log.write_bytes(output)
        receipt["commands"].append({"name": label, "argv": argv,
                                    "exit_code": status, "seconds": time.monotonic() - start,
                                    "log_sha256": sha(log)})
        print(label, "exit", status, flush=True)
        if status:
            break
    receipt["passed"] = (len(receipt["commands"]) == len(commands) and
                         all(row["exit_code"] == 0 for row in receipt["commands"]))
    receipt["artifact_sha256"] = {path.name: sha(path) for path in sorted(args.output.iterdir())
                                  if path.is_file()}
    (args.output / "run.json").write_text(json.dumps(receipt, indent=2) + "\n")
    raise SystemExit(0 if receipt["passed"] else 1)


if __name__ == "__main__":
    main()
