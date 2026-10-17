#!/usr/bin/env python3
"""Compile only the reviewed OpenMW pool header and GPLv3 research harness."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    manifest = json.loads((HERE / "input-manifest.json").read_text())
    for relative, expected in manifest["files"].items():
        path = HERE / relative
        if sha(path) != expected["sha256"] or path.stat().st_size != expected["bytes"]:
            raise ValueError("Reviewed source mismatch: " + relative)
    executable = output / "openmw-pool-check"
    command = ["g++", "-std=c++20", "-O1", "-g", "-Wall", "-Wextra", "-Werror",
               "-pedantic", "-fsanitize=address,undefined", "-fno-omit-frame-pointer",
               "-I", str(HERE / "vendor/openmw"), str(HERE / "openmw-pool-check.cpp"),
               "-o", str(executable)]
    compile_result = subprocess.run(command, capture_output=True, text=True, timeout=30)
    (output / "compile.stdout.txt").write_text(compile_result.stdout)
    (output / "compile.stderr.txt").write_text(compile_result.stderr)
    result = {"passed":False, "scope":"One unchanged GPLv3 OpenMW header in a standalone research executable; no game runtime integration or engine build.",
              "compile_command":command, "compile_exit_code":compile_result.returncode,
              "compiler":subprocess.check_output(["g++", "--version"], text=True).splitlines()[0],
              "input_manifest_sha256":sha(HERE / "input-manifest.json"),
              "script_sha256":sha(Path(__file__)),
              "cpu_affinity":sorted(os.sched_getaffinity(0)) if hasattr(os, "sched_getaffinity") else None}
    if compile_result.returncode == 0:
        env = os.environ.copy()
        env.update(ASAN_OPTIONS="detect_leaks=1:halt_on_error=1", UBSAN_OPTIONS="halt_on_error=1")
        run = subprocess.run([str(executable)], capture_output=True, text=True, env=env, timeout=10)
        (output / "run.stdout.jsonl").write_text(run.stdout)
        (output / "run.stderr.txt").write_text(run.stderr)
        records = [json.loads(line) for line in run.stdout.splitlines() if line.strip()]
        result.update(run_exit_code=run.returncode, checks=records[:-1], totals=records[-1],
                      executable_sha256=sha(executable), sanitizer_stderr_bytes=len(run.stderr.encode()))
        result["passed"] = run.returncode == 0 and not run.stderr and records[-1] == {"passed":True, "checks":9, "failures":0} and all(r.get("passed") is True for r in records[:-1])
    result["sources_unchanged"] = all(sha(HERE / path) == expected["sha256"] for path, expected in manifest["files"].items())
    result["passed"] = result["passed"] and result["sources_unchanged"]
    (output / "report.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"passed":result["passed"], "checks":len(result.get("checks", [])), "output":str(output)}))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
