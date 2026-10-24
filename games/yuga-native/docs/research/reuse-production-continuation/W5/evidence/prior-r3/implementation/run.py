#!/usr/bin/env python3
"""Bounded read-only event/socket/receiver capture; no downloads or asset writes."""
import argparse
import gzip
import hashlib
import json
import os
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
        raise SystemExit("Use a fresh absolute output directory")
    here = Path(__file__).resolve().parent
    native, repository = here.parents[1], here.parents[3]
    engine = shutil.which(args.engine)
    if not engine:
        raise SystemExit("Godot is unavailable; no download attempted")
    engine = Path(engine).resolve()
    args.output.mkdir(parents=True, exist_ok=False)
    implementation = args.output / "implementation"
    implementation.mkdir()
    files = [p for p in here.iterdir() if p.suffix in (".gd", ".py")]
    for path in files:
        shutil.copy2(path, implementation / path.name)
    receipt = {"schema": 1, "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repository, text=True).strip(),
               "scope": "Headless real-runtime observation and numerical offline inspection; no continuous raster/listening/player input acceptance",
               "engine": str(engine), "engine_sha256": sha(engine),
               "implementation_sha256": {p.name: sha(p) for p in files}, "commands": []}
    trace = args.output / "actual.json"
    affinity = sorted(os.sched_getaffinity(0)) if hasattr(os, "sched_getaffinity") else []
    prefix = ["taskset", "-c", str(affinity[0])] if affinity and shutil.which("taskset") else []
    receipt["capture_cpu_affinity"] = affinity[:1] if prefix else None
    commands = [("capture", prefix + [str(engine), "--headless", "--audio-driver", "Dummy", "--path", str(native),
                 "--script", "res://tools/reuse-event-sync/capture.gd", "--", "--output=" + str(trace)]),
                ("checks", [sys.executable, str(here / "check_sidecar.py"), "--trace", str(trace), "--output", str(args.output / "checks.json")])]
    for hz in (30, 60, 120):
        commands.append((f"inspect-{hz}", [sys.executable, str(here / "inspect_sidecar.py"), "--trace", str(trace), "--hz", str(hz), "--output", str(args.output / f"inspection-{hz}.json")]))
    for name, argv in commands:
        start = time.monotonic()
        try:
            result = subprocess.run(argv, cwd=repository, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                    timeout=180, env={**os.environ, "OMP_NUM_THREADS": "1"})
            status, data = result.returncode, result.stdout
        except subprocess.TimeoutExpired as error:
            status, data = 124, (error.stdout or b"") + b"\n180-second timeout\n"
        log = args.output / f"{name}.log"
        log.write_bytes(data)
        errors = b"SCRIPT ERROR:" in data or b"\nERROR:" in data
        receipt["commands"].append({"name": name, "argv": argv, "exit_code": status, "engine_errors": errors,
                                    "seconds": time.monotonic()-start, "log_sha256": sha(log)})
        print(name, status, "engine_errors", errors, flush=True)
        if status or errors:
            break
    receipt["passed"] = len(receipt["commands"]) == len(commands) and all(
        r["exit_code"] == 0 and not r["engine_errors"] for r in receipt["commands"])
    # Exact original evidence remains in scratch. Deterministic gzip provides
    # compact portable copies; decompression is byte-verified before recording.
    receipt["compressed"] = {}
    for path in sorted(args.output.glob("*.json")):
        raw = path.read_bytes()
        destination = path.with_suffix(path.suffix + ".gz")
        data = gzip.compress(raw, compresslevel=6, mtime=0)
        destination.write_bytes(data)
        assert gzip.decompress(data) == raw
        receipt["compressed"][destination.name] = {"bytes": len(data), "sha256": sha(destination),
                                                    "raw_bytes": len(raw), "raw_sha256": sha(path)}
    receipt["artifact_sha256"] = {p.name: sha(p) for p in args.output.iterdir() if p.is_file()}
    (args.output / "run.json").write_text(json.dumps(receipt, indent=2) + "\n")
    raise SystemExit(0 if receipt["passed"] else 1)


if __name__ == "__main__":
    main()
